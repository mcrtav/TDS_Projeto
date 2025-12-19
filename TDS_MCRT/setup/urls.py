from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from usuarios.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API URLs - Mantendo organização por app
    path('api/usuarios/', include('usuarios.urls')),
    path('api/produtos/', include('produtos.urls')),
    path('api/categorias/', include('categorias.urls')),
    
    # 🔥 CORREÇÃO: URLs de token na raiz da API (como o frontend espera)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Frontend URLs
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('sobre/', TemplateView.as_view(template_name='sobre.html'), name='sobre'),
    
    # Auth URLs (frontend)
    path('login/', TemplateView.as_view(template_name='auth/login.html'), name='login'),
    path('cadastro/', TemplateView.as_view(template_name='auth/cadastro.html'), name='cadastro'),
    path('recuperar-senha/', TemplateView.as_view(template_name='auth/recuperar_senha.html'), name='recuperar-senha'),
    path('resetar-senha/<str:uid>/<str:token>/', TemplateView.as_view(template_name='auth/resetar_senha.html'), name='resetar-senha'),
    
    # Produtos URLs
    path('produtos/', TemplateView.as_view(template_name='produtos/listar.html'), name='produtos'),
    path('produtos/novo/', TemplateView.as_view(template_name='produtos/criar.html'), name='novo-produto'),
    path('produtos/<uuid:id>/', TemplateView.as_view(template_name='produtos/detalhe.html'), name='detalhe-produto'),
    path('produtos/<uuid:id>/editar/', TemplateView.as_view(template_name='produtos/editar.html'), name='editar-produto'),
    path('meus-favoritos/', TemplateView.as_view(template_name='produtos/favoritos.html'), name='favoritos'),
    
    # Usuario URLs
    path('perfil/', TemplateView.as_view(template_name='usuarios/perfil.html'), name='perfil'),
    path('perfil/editar/', TemplateView.as_view(template_name='usuarios/editar_perfil.html'), name='editar-perfil'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)