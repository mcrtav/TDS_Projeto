from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F, Count, Sum, Avg, Min, Max
from django.db import transaction
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
import logging

from produtos.models import Produto, Favorito, ProdutoHistoricoPreco
from produtos.serializers import (
    ProdutoSerializer,
    ProdutoListSerializer,
    ProdutoCreateUpdateSerializer,
    FavoritoSerializer,
    FavoritoCreateSerializer,
    ProdutoHistoricoPrecoSerializer,
    ProdutoEstatisticasSerializer
)
from categorias.models import Categoria

logger = logging.getLogger(__name__)


class ProdutoPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.filter(deleted=False)
    pagination_class = ProdutoPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria', 'marca', 'estado', 'publicado', 'destaque', 'em_promocao']
    search_fields = ['nome', 'descricao', 'marca', 'sku', 'codigo_barras']
    ordering_fields = ['nome', 'preco', 'preco_promocional', 'data_criacao', 'avaliacao_media', 'visualizacoes']
    ordering = ['-data_criacao']
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """Retorna queryset baseado nas permissões"""
        queryset = super().get_queryset()
        
        # Usuários não autenticados só veem produtos publicados
        if not self.request.user.is_authenticated:
            return queryset.filter(publicado=True)
        
        # Admin vê tudo (incluindo não publicados)
        if self.request.user.is_staff:
            return queryset
        
        # Usuários normais só veem produtos publicados
        return queryset.filter(publicado=True)
    
    def get_permissions(self):
        """Define permissões baseadas na ação"""
        if self.action in ['list', 'retrieve', 'search', 'filter_products', 'categorias', 'destaques', 'promocoes']:
            return [AllowAny()]
        elif self.action in ['create', 'destroy', 'bulk_update', 'estatisticas', 'historico_precos']:
            return [IsAdminUser()]
        elif self.action in ['favoritar', 'desfavoritar', 'meus_favoritos', 'upload_imagem']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """Retorna serializer apropriado para cada ação"""
        if self.action == 'list':
            return ProdutoListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProdutoCreateUpdateSerializer
        return ProdutoSerializer
    
    def get_serializer_context(self):
        """Adiciona request ao contexto do serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def retrieve(self, request, *args, **kwargs):
        """Detalhes do produto com incremento de visualizações"""
        instance = self.get_object()
        
        # Incrementar visualizações (apenas para usuários não-admin)
        if not request.user.is_staff:
            instance.incrementar_visualizacoes()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Cria um novo produto"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        produto = serializer.save()
        
        logger.info(f'Produto criado: {produto.nome} por {request.user.email}')
        
        return Response(
            ProdutoSerializer(produto, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Atualiza um produto existente"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        produto = serializer.save()
        
        logger.info(f'Produto atualizado: {produto.nome} por {request.user.email}')
        
        return Response(
            ProdutoSerializer(produto, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Soft delete do produto"""
        instance = self.get_object()
        instance.soft_delete()
        
        logger.info(f'Produto deletado (soft): {instance.nome} por {request.user.email}')
        
        return Response({
            'mensagem': 'Produto deletado com sucesso'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='buscar')
    def search(self, request):
        """Busca avançada de produtos"""
        query = request.GET.get('q', '').strip()
        categoria_id = request.GET.get('categoria_id')
        min_preco = request.GET.get('min_preco')
        max_preco = request.GET.get('max_preco')
        marca = request.GET.get('marca')
        estado = request.GET.get('estado')
        destaque = request.GET.get('destaque')
        em_promocao = request.GET.get('em_promocao')
        
        produtos = self.get_queryset()
        
        # Aplicar filtros
        if query:
            produtos = produtos.filter(
                Q(nome__icontains=query) |
                Q(descricao__icontains=query) |
                Q(marca__icontains=query) |
                Q(sku__icontains=query)
            )
        
        if categoria_id:
            produtos = produtos.filter(categoria_id=categoria_id)
        
        if min_preco:
            try:
                produtos = produtos.filter(preco__gte=float(min_preco))
            except ValueError:
                pass
        
        if max_preco:
            try:
                produtos = produtos.filter(preco__lte=float(max_preco))
            except ValueError:
                pass
        
        if marca:
            produtos = produtos.filter(marca__iexact=marca)
        
        if estado:
            produtos = produtos.filter(estado=estado)
        
        if destaque is not None:
            produtos = produtos.filter(destaque=destaque.lower() == 'true')
        
        if em_promocao is not None:
            produtos = produtos.filter(em_promocao=em_promocao.lower() == 'true')
        
        # Paginação
        page = self.paginate_queryset(produtos)
        if page is not None:
            serializer = ProdutoListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProdutoListSerializer(produtos, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='filter')
    def filter_products(self, request):
        """Filtros avançados com opções disponíveis"""
        # Obter opções únicas para filtros
        marcas = Produto.objects.filter(
            publicado=True, deleted=False
        ).values_list('marca', flat=True).distinct().order_by('marca')
        
        estados = Produto.objects.filter(
            publicado=True, deleted=False
        ).values_list('estado', flat=True).distinct().order_by('estado')
        
        # Preços mínimo e máximo
        preco_stats = Produto.objects.filter(
            publicado=True, deleted=False
        ).aggregate(
            min_preco=Min('preco'),
            max_preco=Max('preco')
        )
        
        return Response({
            'marcas': list(marcas),
            'estados': list(estados),
            'faixa_preco': preco_stats
        })
    
    @action(detail=False, methods=['get'], url_path='destaques')
    def destaques(self, request):
        """Produtos em destaque"""
        produtos = self.get_queryset().filter(destaque=True)
        
        page = self.paginate_queryset(produtos)
        if page is not None:
            serializer = ProdutoListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProdutoListSerializer(produtos, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='promocoes')
    def promocoes(self, request):
        """Produtos em promoção"""
        produtos = self.get_queryset().filter(em_promocao=True)
        
        page = self.paginate_queryset(produtos)
        if page is not None:
            serializer = ProdutoListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProdutoListSerializer(produtos, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='categorias')
    def categorias(self, request):
        """Listar categorias ativas"""
        cache_key = 'categorias_ativas'
        categorias = cache.get(cache_key)
        
        if not categorias:
            categorias = Categoria.objects.filter(
                ativo=True, deletado=False
            ).values('id', 'nome', 'icone', 'cor')
            cache.set(cache_key, list(categorias), 60 * 60)  # Cache de 1 hora
        
        return Response(categorias)
    
    @action(detail=True, methods=['post'], url_path='favoritar')
    def favoritar(self, request, pk=None):
        """Adicionar produto aos favoritos"""
        produto = self.get_object()
        usuario = request.user
        
        serializer = FavoritoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        notificar_promocao = data.get('notificar_promocao', True)
        
        favorito, created = Favorito.objects.get_or_create(
            usuario=usuario,
            produto=produto,
            defaults={'notificar_promocao': notificar_promocao}
        )
        
        if not created:
            # Atualizar preferência de notificação
            favorito.notificar_promocao = notificar_promocao
            favorito.save()
        
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        mensagem = 'Produto adicionado aos favoritos' if created else 'Preferência de notificação atualizada'
        
        return Response({
            'mensagem': mensagem,
            'favorito': FavoritoSerializer(favorito).data
        }, status=status_code)
    
    @action(detail=True, methods=['delete'], url_path='desfavoritar')
    def desfavoritar(self, request, pk=None):
        """Remover produto dos favoritos"""
        produto = self.get_object()
        usuario = request.user
        
        try:
            favorito = Favorito.objects.get(usuario=usuario, produto=produto)
            favorito.delete()
            
            logger.info(f'Produto removido dos favoritos: {produto.nome} por {usuario.email}')
            
            return Response({
                'mensagem': 'Produto removido dos favoritos'
            }, status=status.HTTP_200_OK)
        except Favorito.DoesNotExist:
            return Response({
                'erro': 'Produto não estava nos favoritos'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='meus-favoritos')
    def meus_favoritos(self, request):
        """Listar favoritos do usuário"""
        favoritos = Favorito.objects.filter(usuario=request.user).select_related('produto')
        
        page = self.paginate_queryset(favoritos)
        if page is not None:
            serializer = FavoritoSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = FavoritoSerializer(favoritos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='upload-imagem')
    def upload_imagem(self, request, pk=None):
        """Upload de imagem para produto"""
        produto = self.get_object()
        imagem = request.FILES.get('imagem')
        tipo = request.data.get('tipo', 'principal')
        
        if not imagem:
            return Response({
                'erro': 'Nenhuma imagem enviada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar tipo de arquivo
        extensoes_validas = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        if not any(imagem.name.lower().endswith(ext) for ext in extensoes_validas):
            return Response({
                'erro': f'Formato de imagem inválido. Use: {", ".join(extensoes_validas)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar tamanho (max 10MB)
        if imagem.size > 10 * 1024 * 1024:
            return Response({
                'erro': 'Imagem muito grande. Tamanho máximo: 10MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Salvar imagem
        if tipo == 'secundaria':
            produto.imagem_secundaria = imagem
        else:
            produto.imagem_principal = imagem
        
        produto.save()
        
        logger.info(f'Imagem {tipo} upload para produto: {produto.nome}')
        
        return Response({
            'mensagem': f'Imagem {tipo} salva com sucesso',
            'url': request.build_absolute_uri(imagem.url) if hasattr(imagem, 'url') else None
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='historico-precos')
    def historico_precos(self, request, pk=None):
        """Histórico de preços do produto"""
        produto = self.get_object()
        historico = ProdutoHistoricoPreco.objects.filter(produto=produto).order_by('-data_alteracao')
        
        serializer = ProdutoHistoricoPrecoSerializer(historico, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='estatisticas')
    def estatisticas(self, request):
        """Estatísticas gerais dos produtos"""
        cache_key = 'produtos_estatisticas'
        estatisticas = cache.get(cache_key)
        
        if not estatisticas:
            # Estatísticas básicas
            total_produtos = Produto.objects.filter(deleted=False).count()
            produtos_ativos = Produto.objects.filter(publicado=True, deleted=False).count()
            produtos_em_promocao = Produto.objects.filter(em_promocao=True, publicado=True, deleted=False).count()
            produtos_sem_estoque = Produto.objects.filter(quantidade=0, publicado=True, deleted=False).count()
            
            # Produtos por categoria
            produtos_por_categoria = {}
            categorias = Categoria.objects.filter(ativo=True, deletado=False)
            for categoria in categorias:
                count = Produto.objects.filter(
                    categoria=categoria, 
                    publicado=True, 
                    deleted=False
                ).count()
                if count > 0:
                    produtos_por_categoria[categoria.nome] = count
            
            # Valor total do estoque
            valor_total_estoque = Produto.objects.filter(
                publicado=True, deleted=False
            ).aggregate(
                total=Sum(F('preco') * F('quantidade'))
            )['total'] or 0
            
            estatisticas = {
                'total_produtos': total_produtos,
                'produtos_ativos': produtos_ativos,
                'produtos_em_promocao': produtos_em_promocao,
                'produtos_sem_estoque': produtos_sem_estoque,
                'produtos_por_categoria': produtos_por_categoria,
                'valor_total_estoque': valor_total_estoque
            }
            
            cache.set(cache_key, estatisticas, 60 * 15)  # Cache de 15 minutos
        
        serializer = ProdutoEstatisticasSerializer(estatisticas)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update(self, request):
        """Atualização em massa de produtos"""
        produto_ids = request.data.get('produto_ids', [])
        acao = request.data.get('acao')
        
        if not produto_ids or not acao:
            return Response({
                'erro': 'IDs dos produtos e ação são obrigatórios'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        produtos = Produto.objects.filter(id__in=produto_ids, deleted=False)
        total_atualizados = 0
        
        with transaction.atomic():
            for produto in produtos:
                if acao == 'publicar':
                    produto.publicado = True
                elif acao == 'ocultar':
                    produto.publicado = False
                elif acao == 'destacar':
                    produto.destaque = True
                elif acao == 'remover_destaque':
                    produto.destaque = False
                elif acao == 'ativar_promocao':
                    produto.em_promocao = True
                elif acao == 'desativar_promocao':
                    produto.em_promocao = False
                else:
                    continue
                
                produto.save()
                total_atualizados += 1
        
        logger.info(f'Bulk update: {total_atualizados} produtos atualizados com ação "{acao}" por {request.user.email}')
        
        return Response({
            'mensagem': f'{total_atualizados} produtos atualizados com sucesso',
            'total_atualizados': total_atualizados
        }, status=status.HTTP_200_OK)