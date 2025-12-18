from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.contrib.auth import login, logout
import logging

from usuarios.models import Usuario
from usuarios.serializers import (
    CadastroSerializer,
    UsuarioSerializer,
    UsuarioPerfilSerializer,
    RecuperarSenhaSerializer,
    ResetarSenhaSerializer,
    UsuarioUpdateSerializer
)

logger = logging.getLogger(__name__)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer customizado para adicionar dados do usuário"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Adicionar dados do usuário à resposta
        data['usuario'] = UsuarioPerfilSerializer(self.user).data
        data['mensagem'] = 'Login realizado com sucesso'
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View de login que usa token JWT nativo E cria sessão Django.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        # Primeiro, validar com o serializer padrão do Simple JWT
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            
            # Atualizar último login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Criar sessão Django também
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            
            logger.info(f'Login realizado com sessão: {user.email}')
            
            # Retornar resposta padrão do JWT com dados extras
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Erro no login: {str(e)}')
            
            # Verificar se é erro de credenciais
            error_detail = str(e)
            if 'No active account found' in error_detail or 'credenciais' in error_detail.lower():
                return Response(
                    {'detail': 'Credenciais inválidas'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            return Response(
                {'detail': 'Erro no login'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.filter(deleted=False, is_active=True)
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_permissions(self):
        if self.action in ['cadastro', 'recuperar_senha', 'resetar_senha']:
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'perfil':
            return UsuarioPerfilSerializer
        elif self.action == 'atualizar_perfil':
            return UsuarioUpdateSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['post'], url_path='cadastro')
    def cadastro(self, request):
        """Registro de novo usuário"""
        serializer = CadastroSerializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            
            with transaction.atomic():
                usuario = serializer.save()
            
            logger.info(f'Novo usuário cadastrado: {usuario.email}')
            
            return Response({
                'mensagem': 'Usuário cadastrado com sucesso',
                'usuario': UsuarioSerializer(usuario).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f'Erro no cadastro: {str(e)}')
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], url_path='recuperar-senha')
    def recuperar_senha(self, request):
        """Inicia processo de recuperação de senha"""
        serializer = RecuperarSenhaSerializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data['email'].lower()
            
            try:
                usuario = Usuario.objects.get(
                    email=email, 
                    is_active=True, 
                    deleted=False
                )
                
                # Gerar token de recuperação
                reset_token = usuario.gerar_reset_token()
                
                # Em produção, enviar email
                if not settings.DEBUG:
                    reset_url = f"{settings.FRONTEND_URL}/resetar-senha?token={reset_token}"
                    
                    send_mail(
                        subject='Recuperação de Senha - Sistema Gestão',
                        message=f'Olá {usuario.nome},\n\n'
                               f'Para resetar sua senha, clique no link abaixo:\n'
                               f'{reset_url}\n\n'
                               f'Este link expira em 1 hora.\n\n'
                               f'Se você não solicitou esta recuperação, ignore este email.\n\n'
                               f'Atenciosamente,\n'
                               f'Equipe Sistema Gestão',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )
                
                logger.info(f'Solicitação de recuperação de senha para: {email}')
                
                return Response({
                    'mensagem': 'Instruções de recuperação enviadas para o e-mail',
                    'token': reset_token if settings.DEBUG else None
                }, status=status.HTTP_200_OK)
                
            except Usuario.DoesNotExist:
                # Por segurança, não informamos se o email existe
                logger.warning(f'Tentativa de recuperação para email não cadastrado: {email}')
                return Response({
                    'mensagem': 'Se o email existir em nossa base, enviaremos instruções'
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f'Erro na recuperação de senha: {str(e)}')
            return Response(
                {'erro': str(e) if settings.DEBUG else 'Erro na solicitação'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], url_path='resetar-senha')
    def resetar_senha(self, request):
        """Reseta a senha usando token de recuperação"""
        serializer = ResetarSenhaSerializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            token = serializer.validated_data['token']
            nova_senha = serializer.validated_data['nova_senha']
            
            try:
                usuario = Usuario.objects.get(
                    reset_token=token,
                    is_active=True,
                    deleted=False
                )
                
                # Verificar se token ainda é válido
                if not usuario.reset_token_valido():
                    return Response({
                        'erro': 'Token expirado'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Atualizar senha
                usuario.set_password(nova_senha)
                usuario.reset_token = None
                usuario.reset_token_expires = None
                usuario.save()
                
                logger.info(f'Senha resetada para usuário: {usuario.email}')
                
                return Response({
                    'mensagem': 'Senha alterada com sucesso'
                }, status=status.HTTP_200_OK)
                
            except Usuario.DoesNotExist:
                return Response({
                    'erro': 'Token inválido ou expirado'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f'Erro no reset de senha: {str(e)}')
            return Response(
                {'erro': str(e) if settings.DEBUG else 'Erro no reset de senha'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='perfil')
    def perfil(self, request):
        """Retorna perfil do usuário autenticado"""
        try:
            serializer = UsuarioPerfilSerializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f'Erro ao buscar perfil: {str(e)}')
            return Response(
                {'erro': 'Erro ao buscar perfil'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['put', 'patch'], url_path='atualizar-perfil')
    def atualizar_perfil(self, request):
        """Atualiza perfil do usuário"""
        usuario = request.user
        serializer = UsuarioUpdateSerializer(
            usuario, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        try:
            serializer.is_valid(raise_exception=True)
            
            with transaction.atomic():
                serializer.save()
            
            logger.info(f'Perfil atualizado: {usuario.email}')
            
            return Response({
                'mensagem': 'Perfil atualizado com sucesso',
                'usuario': UsuarioSerializer(usuario).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Erro ao atualizar perfil: {str(e)}')
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        """Logout do usuário (sessão Django)"""
        try:
            logout(request)
            
            logger.info(f'Logout realizado: {request.user.email if request.user.is_authenticated else "usuário não autenticado"}')
            
            return Response({
                'mensagem': 'Logout realizado com sucesso'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Erro no logout: {str(e)}')
            return Response(
                {'erro': 'Erro ao fazer logout'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['delete'], url_path='deletar-conta')
    def deletar_conta(self, request):
        """Soft delete da conta do usuário"""
        usuario = request.user
        
        try:
            with transaction.atomic():
                usuario.soft_delete()
                logout(request)
            
            logger.info(f'Conta deletada: {usuario.email}')
            
            return Response({
                'mensagem': 'Conta deletada com sucesso'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Erro ao deletar conta: {str(e)}')
            return Response(
                {'erro': 'Erro ao deletar conta'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Override do delete padrão para usar soft delete"""
        instance = self.get_object()
        
        # Verificar permissões
        if instance != request.user and not request.user.is_superuser:
            return Response({
                'erro': 'Você só pode deletar seu próprio perfil'
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance.soft_delete()
        
        return Response({
            'mensagem': 'Usuário deletado com sucesso'
        }, status=status.HTTP_200_OK)


class UsuarioMeView(generics.RetrieveAPIView):
    """View para obter dados do usuário autenticado"""
    serializer_class = UsuarioPerfilSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class SessionAuthView(generics.GenericAPIView):
    """View para verificar sessão Django"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Verifica se há sessão ativa"""
        if request.user.is_authenticated:
            return Response({
                'autenticado': True,
                'usuario': UsuarioPerfilSerializer(request.user).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'autenticado': False,
            'mensagem': 'Nenhuma sessão ativa'
        }, status=status.HTTP_200_OK)