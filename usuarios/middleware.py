import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)
User = get_user_model()


class JWTAuthMiddleware(MiddlewareMixin):
    """
    Middleware para autenticar usuários via JWT e sincronizar com sessão Django.
    """
    
    def process_request(self, request):
        # Tentar autenticar via token JWT
        token = self.get_token_from_request(request)
        
        if token:
            try:
                # Validar token JWT
                validated_token = UntypedToken(token)
                user_id = validated_token.get('user_id')
                
                if user_id:
                    # Buscar usuário
                    try:
                        user = User.objects.get(
                            id=user_id,
                            is_active=True,
                            deleted=False
                        )
                        
                        # Autenticar usuário na request Django
                        request.user = user
                        
                        # Sincronizar com sessão Django se não existir
                        if not request.session.session_key:
                            request.session.create()
                        
                        # Armazenar token JWT na sessão
                        request.session['jwt_access'] = token
                        request.session['user_id'] = str(user_id)
                        request.session.save()
                        
                        logger.debug(f'Usuário autenticado via middleware JWT: {user.email}')
                        
                    except User.DoesNotExist:
                        request.user = AnonymousUser()
                        logger.warning(f'Usuário não encontrado no middleware: {user_id}')
                
            except (InvalidToken, TokenError, jwt.DecodeError, 
                    jwt.ExpiredSignatureError, jwt.InvalidSignatureError) as e:
                # Token JWT inválido, tentar sessão Django
                request.user = AnonymousUser()
                logger.debug(f'Token JWT inválido no middleware: {str(e)}')
        
        # Se JWT falhou, verificar sessão Django
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            user_id = request.session.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(
                        id=user_id,
                        is_active=True,
                        deleted=False
                    )
                    request.user = user
                    logger.debug(f'Usuário autenticado via sessão no middleware: {user.email}')
                except User.DoesNotExist:
                    request.user = AnonymousUser()
                    # Limpar sessão inválida
                    if 'user_id' in request.session:
                        del request.session['user_id']
                        request.session.save()
    
    def get_token_from_request(self, request):
        """
        Obtém token JWT da request em múltiplas fontes.
        """
        # 1. Header Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        
        # 2. Cookie
        token = request.COOKIES.get('jwt_access')
        if token:
            return token
        
        # 3. Query string (apenas desenvolvimento)
        if settings.DEBUG:
            token = request.GET.get('token')
            if token:
                return token
        
        return None
    
    def process_response(self, request, response):
        """
        Processa a resposta para manter sessão sincronizada.
        """
        # Se o usuário está autenticado e tem tokens JWT na sessão
        if hasattr(request, 'user') and request.user.is_authenticated:
            jwt_access = request.session.get('jwt_access')
            
            # Se há token JWT na sessão, adicionar ao header da resposta (opcional)
            if jwt_access and 'Authorization' not in response.headers:
                response['Authorization'] = f'Bearer {jwt_access}'
        
        return response