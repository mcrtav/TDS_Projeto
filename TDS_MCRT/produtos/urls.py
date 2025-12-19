from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  # Importando views corretamente
from produtos import views as produto_views  # Importação alternativa

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

# URLs para as páginas HTML (renderizadas)
html_urlpatterns = [
    # Páginas HTML - comente estas se não tiver as views correspondentes ainda
    # path('html/', produto_views.listar_produtos, name='listar-produtos'),
    # path('html/novo/', produto_views.criar_produto, name='criar-produto'),
    # path('html/<uuid:produto_id>/', produto_views.detalhe_produto, name='detalhe-produto'),
    # path('html/<uuid:produto_id>/editar/', produto_views.editar_produto, name='editar-produto'),
    # path('html/favoritos/', produto_views.meus_favoritos, name='favoritos-html'),
]

urlpatterns += extra_urlpatterns
# urlpatterns += html_urlpatterns  # Descomente quando criar as views HTML