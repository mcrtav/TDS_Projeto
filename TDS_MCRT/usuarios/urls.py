from django.urls import path, include
from rest_framework.routers import DefaultRouter
from usuarios import views
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

# Criar router
router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet, basename='usuarios')

urlpatterns = [
    # URLs do router (CRUD básico de usuários)
    path('', include(router.urls)),
    
    # 🔥 REMOVIDO: As URLs de token foram movidas para setup/urls.py
    
    # Usuário autenticado atual
    path('me/', views.UsuarioMeView.as_view(), name='usuario-me'),
    
    # Verificar sessão Django
    path('session/', views.SessionAuthView.as_view(), name='session-auth'),
    
    # URLs específicas (ações)
    path('cadastro/', views.UsuarioViewSet.as_view({'post': 'cadastro'}), name='cadastro'),
    path('perfil/', views.UsuarioViewSet.as_view({'get': 'perfil'}), name='perfil'),
    path('perfil/atualizar/', views.UsuarioViewSet.as_view({'put': 'atualizar_perfil', 'patch': 'atualizar_perfil'}), name='atualizar-perfil'),
    path('logout/', views.UsuarioViewSet.as_view({'post': 'logout'}), name='logout'),
    path('recuperar-senha/', views.UsuarioViewSet.as_view({'post': 'recuperar_senha'}), name='recuperar-senha'),
    path('resetar-senha/', views.UsuarioViewSet.as_view({'post': 'resetar_senha'}), name='resetar-senha'),
    path('deletar-conta/', views.UsuarioViewSet.as_view({'delete': 'deletar_conta'}), name='deletar-conta'),
]