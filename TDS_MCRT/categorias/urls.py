from django.urls import path, include
from rest_framework.routers import DefaultRouter
from categorias import views

# Criar router
router = DefaultRouter()
router.register(r'categorias', views.CategoriaViewSet, basename='categoria')

# URLs básicas do router
router_urls = router.urls

urlpatterns = [
    path('', include(router_urls)),
    path('categorias/<uuid:pk>/produtos/', 
         views.CategoriaProdutosView.as_view(), 
         name='categoria-produtos'),
]