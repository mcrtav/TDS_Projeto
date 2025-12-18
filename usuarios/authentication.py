from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    """
    Autenticação JWT customizada que sincroniza com sessão Django.
    """
    
    def authenticate(self, request):
        """
        Tenta autenticar via JWT e sincroniza com sessão Django.
        """
        # Primeiro tenta a autenticação JWT padrão
        auth_result = super().authenticate(request)
        
        if auth_result:
            user, validated_token = auth_result
            
            # Sincronizar com sessão Django
            self.sync_with_django_session(request, user, validated_token)
            
            return user, validated_token
        
        # Se JWT falhou, tentar sessão Django
        return self.authenticate_via_session(request)
    
    def sync_with_django_session(self, request, user, validated_token):
        """
        Sincroniza autenticação JWT com sessão Django.
        """
        try:
            # Criar sessão se não existir
            if not request.session.session_key:
                request.session.create()
            
            # Armazenar informações na sessão
            request.session['jwt_access'] = str(validated_token)
            request.session['user_id'] = str(user.id)
            request.session['is_authenticated'] = True
            
            # Manter sessão ativa
            request.session.save()
            
            logger.debug(f'Sessão Django sincronizada para usuário JWT: {user.email}')
            
        except Exception as e:
            logger.error(f'Erro ao sincronizar sessão Django: {str(e)}')
    
    def authenticate_via_session(self, request):
        """
        Tenta autenticar via sessão Django.
        """
        user_id = request.session.get('user_id')
        
        if not user_id:
            return None
        
        try:
            user = User.objects.get(
                id=user_id,
                is_active=True,
                deleted=False
            )
            
            # Verificar se há token JWT válido na sessão
            jwt_token = request.session.get('jwt_access')
            if jwt_token:
                try:
                    validated_token = self.get_validated_token(jwt_token)
                    return user, validated_token
                except AuthenticationFailed:
                    # Token JWT expirado, mas sessão ainda válida
                    pass
            
            # Retornar apenas o usuário (sem token) para sessão pura
            return user, None
            
        except User.DoesNotExist:
            # Limpar sessão inválida
            if 'user_id' in request.session:
                del request.session['user_id']
                request.session.save()
            return None
    
    def get_user(self, validated_token):
        """
        Retorna o usuário autenticado correspondente ao token.
        """
        try:
            user_id = validated_token.get('user_id')
            
            if not user_id:
                raise AuthenticationFailed(
                    _('Token inválido: user_id não encontrado'),
                    code='token_invalid'
                )
            
            # Buscar usuário na tabela customizada
            usuario = User.objects.get(
                id=user_id,
                is_active=True,
                deleted=False
            )
            
            logger.debug(f'Usuário autenticado via JWT: {usuario.email}')
            
            return usuario
            
        except User.DoesNotExist:
            logger.warning(f'Tentativa de autenticação com usuário não encontrado: {user_id}')
            raise AuthenticationFailed(
                _('Usuário não encontrado ou inativo'),
                code='user_not_found'
            )
        except KeyError as e:
            logger.error(f'Erro no token JWT: {str(e)}')
            raise AuthenticationFailed(
                _('Token inválido'),
                code='token_invalid'
            )
        except Exception as e:
            logger.error(f'Erro na autenticação JWT: {str(e)}')
            raise AuthenticationFailed(
                _('Erro na autenticação'),
                code='authentication_error'
            )