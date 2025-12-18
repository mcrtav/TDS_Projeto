from django.urls import path, include
from rest_framework.routers import DefaultRouter
from produtos import views

# Criar router
router = DefaultRouter()
router.register(r'produtos', views.ProdutoViewSet, basename='produtos')

# URLs básicas do router
router_urls = router.urls

urlpatterns = [
    path('', include(router_urls)),
]

# URLs adicionais para funcionalidades específicas
extra_urlpatterns = [
    path('buscar/', views.ProdutoViewSet.as_view({'get': 'search'}), name='produtos-buscar'),
    path('filter/', views.ProdutoViewSet.as_view({'get': 'filter_products'}), name='produtos-filter'),
    path('destaques/', views.ProdutoViewSet.as_view({'get': 'destaques'}), name='produtos-destaques'),
    path('promocoes/', views.ProdutoViewSet.as_view({'get': 'promocoes'}), name='produtos-promocoes'),
    path('categorias/', views.ProdutoViewSet.as_view({'get': 'categorias'}), name='produtos-categorias'),
    path('estatisticas/', views.ProdutoViewSet.as_view({'get': 'estatisticas'}), name='produtos-estatisticas'),
    path('bulk-update/', views.ProdutoViewSet.as_view({'post': 'bulk_update'}), name='produtos-bulk-update'),
    path('meus-favoritos/', views.ProdutoViewSet.as_view({'get': 'meus_favoritos'}), name='meus-favoritos'),
    path('<uuid:pk>/favoritar/', views.ProdutoViewSet.as_view({'post': 'favoritar'}), name='produto-favoritar'),
    path('<uuid:pk>/desfavoritar/', views.ProdutoViewSet.as_view({'delete': 'desfavoritar'}), name='produto-desfavoritar'),
    path('<uuid:pk>/historico-precos/', views.ProdutoViewSet.as_view({'get': 'historico_precos'}), name='produto-historico-precos'),
]

urlpatterns += extra_urlpatterns