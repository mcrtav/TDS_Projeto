from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone
from produtos.models import Produto
from produtos.serializers import ProdutoSerializer

from categorias.models import Categoria
from categorias.serializers import (
    CategoriaSerializer,
    CategoriaCreateSerializer,
    CategoriaUpdateSerializer,
    CategoriaDetailSerializer,
    CategoriaEstatisticasSerializer
)


class CategoriaPagination(PageNumberPagination):
    """
    Paginação personalizada para categorias.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'


class CategoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento completo de categorias.
    """
    
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    pagination_class = CategoriaPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ativo', 'deletado']
    ordering_fields = ['nome', 'ordem', 'criado_em', 'atualizado_em']
    ordering = ['ordem', 'nome']
    parser_classes = [JSONParser, MultiPartParser]
    
    def get_queryset(self):
        """
        Filtra o queryset baseado no usuário e parâmetros.
        """
        queryset = super().get_queryset()
        
        # Para usuários não autenticados, mostra apenas ativas e não deletadas
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(ativo=True, deletado=False)
        # Para usuários normais, esconde as deletadas
        elif not self.request.user.is_staff:
            queryset = queryset.filter(deletado=False)
        
        return queryset
    
    def get_serializer_class(self):
        """
        Retorna o serializer apropriado para cada ação.
        """
        if self.action == 'create':
            return CategoriaCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CategoriaUpdateSerializer
        elif self.action == 'retrieve':
            return CategoriaDetailSerializer
        return super().get_serializer_class()
    
    def get_permissions(self):
        """
        Define permissões baseadas na ação.
        """
        if self.action in ['list', 'retrieve', 'ativas']:
            permission_classes = [AllowAny]
        elif self.action in ['create', 'update', 'partial_update']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['destroy', 'restaurar']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def destroy(self, request, *args, **kwargs):
        """
        Sobrescreve o delete para fazer soft delete.
        """
        instance = self.get_object()
        
        # Verifica se a categoria pode ser deletada
        if instance.quantidade_produtos > 0:
            return Response(
                {
                    'erro': 'Não é possível deletar uma categoria com produtos.',
                    'quantidade_produtos': instance.quantidade_produtos
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.soft_delete()
        
        return Response(
            {
                'mensagem': 'Categoria deletada com sucesso.',
                'id': str(instance.id),
                'nome': instance.nome
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='ativar')
    def ativar(self, request, pk=None):
        """
        Ativa uma categoria.
        """
        categoria = self.get_object()
        
        if categoria.deletado:
            return Response(
                {'erro': 'Não é possível ativar uma categoria deletada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        categoria.ativo = True
        categoria.save()
        
        return Response(
            {
                'mensagem': 'Categoria ativada com sucesso.',
                'categoria': CategoriaSerializer(categoria).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='desativar')
    def desativar(self, request, pk=None):
        """
        Desativa uma categoria.
        """
        categoria = self.get_object()
        
        if categoria.deletado:
            return Response(
                {'erro': 'Não é possível desativar uma categoria deletada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if categoria.quantidade_produtos > 0:
            return Response(
                {
                    'erro': 'Não é possível desativar uma categoria com produtos.',
                    'quantidade_produtos': categoria.quantidade_produtos
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        categoria.ativo = False
        categoria.save()
        
        return Response(
            {
                'mensagem': 'Categoria desativada com sucesso.',
                'categoria': CategoriaSerializer(categoria).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='restaurar')
    def restaurar(self, request, pk=None):
        """
        Restaura uma categoria deletada (apenas admin).
        """
        if not request.user.is_staff:
            return Response(
                {'erro': 'Acesso negado.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        categoria = self.get_object()
        
        if not categoria.deletado:
            return Response(
                {'erro': 'Esta categoria não está deletada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        categoria.restaurar()
        
        return Response(
            {
                'mensagem': 'Categoria restaurada com sucesso.',
                'categoria': CategoriaSerializer(categoria).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='ativas')
    def ativas(self, request):
        """
        Lista apenas categorias ativas.
        """
        categorias = self.get_queryset().filter(ativo=True, deletado=False)
        
        page = self.paginate_queryset(categorias)
        if page is not None:
            serializer = CategoriaSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CategoriaSerializer(categorias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='estatisticas')
    def estatisticas(self, request):
        """
        Retorna estatísticas sobre as categorias.
        """
        try:
            # Estatísticas básicas
            total_categorias = Categoria.objects.count()
            categorias_ativas = Categoria.objects.filter(ativo=True, deletado=False).count()
            categorias_inativas = Categoria.objects.filter(ativo=False, deletado=False).count()
            categorias_deletadas = Categoria.objects.filter(deletado=True).count()
            
            # Categoria com mais produtos
            categoria_stats = Categoria.objects.filter(
                deletado=False
            ).annotate(
                num_produtos=Count('produto')
            ).order_by('-num_produtos').first()
            
            categoria_com_mais_produtos = categoria_stats.nome if categoria_stats else 'Nenhuma'
            quantidade_na_categoria_mais_produtos = categoria_stats.num_produtos if categoria_stats else 0
            
            # Média de produtos por categoria
            total_produtos = Produto.objects.filter(deleted=False).count()
            media_produtos_por_categoria = (
                total_produtos / categorias_ativas 
                if categorias_ativas > 0 else 0
            )
            
            estatisticas = {
                'total_categorias': total_categorias,
                'categorias_ativas': categorias_ativas,
                'categorias_inativas': categorias_inativas,
                'categorias_deletadas': categorias_deletadas,
                'media_produtos_por_categoria': round(media_produtos_por_categoria, 2),
                'categoria_com_mais_produtos': categoria_com_mais_produtos,
                'quantidade_na_categoria_mais_produtos': quantidade_na_categoria_mais_produtos,
                'total_produtos': total_produtos,
                'atualizado_em': timezone.now().strftime('%d/%m/%Y %H:%M:%S')
            }
            
            serializer = CategoriaEstatisticasSerializer(estatisticas)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'erro': 'Não foi possível calcular estatísticas.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoriaPublicViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    """
    ViewSet público para categorias (sem autenticação necessária).
    """
    queryset = Categoria.objects.filter(ativo=True, deletado=False)
    serializer_class = CategoriaSerializer
    pagination_class = CategoriaPagination
    ordering_fields = ['nome', 'ordem']
    ordering = ['ordem', 'nome']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CategoriaDetailSerializer
        return super().get_serializer_class()


class CategoriaProdutosView(APIView):
    """
    View para listar produtos de uma categoria específica.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, pk=None):
        """
        GET /api/categorias/{id}/produtos/
        Retorna os produtos de uma categoria específica.
        """
        try:
            categoria = Categoria.objects.get(id=pk, deletado=False)
        except Categoria.DoesNotExist:
            return Response(
                {'erro': 'Categoria não encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Filtra produtos da categoria
        produtos = Produto.objects.filter(
            categoria=categoria,
            publicado=True,
            deleted=False
        )
        
        # Filtros opcionais
        marca = request.query_params.get('marca', None)
        if marca:
            produtos = produtos.filter(marca__icontains=marca)
        
        min_preco = request.query_params.get('min_preco', None)
        if min_preco:
            try:
                produtos = produtos.filter(preco__gte=float(min_preco))
            except ValueError:
                pass
        
        max_preco = request.query_params.get('max_preco', None)
        if max_preco:
            try:
                produtos = produtos.filter(preco__lte=float(max_preco))
            except ValueError:
                pass
        
        # Ordenação
        ordenacao = request.query_params.get('ordenar', None)
        if ordenacao == 'preco_asc':
            produtos = produtos.order_by('preco')
        elif ordenacao == 'preco_desc':
            produtos = produtos.order_by('-preco')
        elif ordenacao == 'nome':
            produtos = produtos.order_by('nome')
        elif ordenacao == 'recentes':
            produtos = produtos.order_by('-data_criacao')
        
        # Paginação simples
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        produtos_paginados = produtos[start:end]
        
        serializer = ProdutoSerializer(
            produtos_paginados,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'categoria': {
                'id': str(categoria.id),
                'nome': categoria.nome,
                'descricao': categoria.descricao
            },
            'produtos': serializer.data,
            'total': produtos.count(),
            'page': page,
            'page_size': page_size,
            'total_pages': (produtos.count() + page_size - 1) // page_size
        })