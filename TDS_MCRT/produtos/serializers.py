from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from produtos.models import Produto, Favorito, ProdutoHistoricoPreco
from categorias.serializers import CategoriaSerializer
from categorias.models import Categoria


class ProdutoSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    categoria_id = serializers.UUIDField(write_only=True, required=False)
    
    # Campos calculados
    is_favorito = serializers.SerializerMethodField()
    preco_atual = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    desconto_percentual = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    disponivel = serializers.BooleanField(read_only=True)
    
    # URLs das imagens
    imagem_principal_url = serializers.SerializerMethodField()
    imagem_secundaria_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Produto
        fields = [
            'id', 'nome', 'slug', 'descricao', 'descricao_curta',
            'categoria', 'categoria_id', 'marca', 'estado',
            'preco', 'preco_promocional', 'preco_atual', 'desconto_percentual',
            'quantidade', 'disponivel', 'sku', 'codigo_barras',
            'peso', 'dimensoes', 'imagem_principal', 'imagem_principal_url',
            'imagem_secundaria', 'imagem_secundaria_url', 'is_favorito',
            'meta_titulo', 'meta_descricao', 'data_criacao', 'data_atualizacao',
            'publicado', 'destaque', 'em_promocao', 'visualizacoes',
            'vendas', 'avaliacao_media', 'total_avaliacoes'
        ]
        
        read_only_fields = [
            'id', 'slug', 'preco_atual', 'desconto_percentual', 'disponivel',
            'data_criacao', 'data_atualizacao', 'visualizacoes', 'vendas',
            'avaliacao_media', 'total_avaliacoes', 'is_favorito',
            'imagem_principal_url', 'imagem_secundaria_url'
        ]
        extra_kwargs = {
            'nome': {'help_text': 'Nome completo do produto'},
            'descricao': {'help_text': 'Descrição detalhada do produto'},
            'preco': {'validators': [MinValueValidator(0.01)]},
            'preco_promocional': {'validators': [MinValueValidator(0.01)]},
            'quantidade': {'validators': [MinValueValidator(0)]},
        }

    def get_is_favorito(self, obj):
        """Verifica se o produto é favorito do usuário atual"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorito.objects.filter(
                usuario=request.user,
                produto=obj
            ).exists()
        return False

    def get_imagem_principal_url(self, obj):
        """Retorna a URL completa da imagem principal"""
        if obj.imagem_principal:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagem_principal.url)
            return obj.imagem_principal.url
        return None

    def get_imagem_secundaria_url(self, obj):
        """Retorna a URL completa da imagem secundária"""
        if obj.imagem_secundaria:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagem_secundaria.url)
            return obj.imagem_secundaria.url
        return None

    def validate(self, data):
        """Validações cruzadas"""
        errors = {}
        
        # Validar preço promocional
        preco_promocional = data.get('preco_promocional')
        preco = data.get('preco', getattr(self.instance, 'preco', None))
        
        if preco_promocional and preco:
            if preco_promocional >= preco:
                errors['preco_promocional'] = 'Preço promocional deve ser menor que o preço normal'
        
        # Validar SKU único
        sku = data.get('sku')
        if sku:
            queryset = Produto.objects.filter(sku=sku)
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            if queryset.exists():
                errors['sku'] = 'Este SKU já está em uso'
        
        # Validar slug único
        nome = data.get('nome')
        if nome and not data.get('slug'):
            slug = slugify(nome)
            queryset = Produto.objects.filter(slug=slug)
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            if queryset.exists():
                errors['nome'] = 'Já existe um produto com nome similar. Escolha um nome diferente ou informe um slug personalizado.'
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data

    def create(self, validated_data):
        """Cria um novo produto"""
        categoria_id = validated_data.pop('categoria_id', None)
        
        # Definir categoria se fornecida
        if categoria_id:
            try:
                categoria = Categoria.objects.get(id=categoria_id)
                validated_data['categoria'] = categoria
            except Categoria.DoesNotExist:
                raise serializers.ValidationError({'categoria_id': 'Categoria não encontrada'})
        
        # Criar produto
        produto = super().create(validated_data)
        
        # Registrar preço inicial no histórico
        ProdutoHistoricoPreco.objects.create(
            produto=produto,
            preco_antigo=0,
            preco_novo=produto.preco,
            alterado_por=self.context['request'].user if self.context.get('request') and self.context['request'].user.is_authenticated else None
        )
        
        return produto

    def update(self, instance, validated_data):
        """Atualiza um produto existente"""
        categoria_id = validated_data.pop('categoria_id', None)
        
        # Atualizar categoria se fornecida
        if categoria_id:
            try:
                categoria = Categoria.objects.get(id=categoria_id)
                validated_data['categoria'] = categoria
            except Categoria.DoesNotExist:
                raise serializers.ValidationError({'categoria_id': 'Categoria não encontrada'})
        
        # Verificar se o preço foi alterado
        preco_alterado = 'preco' in validated_data and validated_data['preco'] != instance.preco
        
        produto = super().update(instance, validated_data)
        
        # Registrar alteração de preço no histórico
        if preco_alterado:
            ProdutoHistoricoPreco.objects.create(
                produto=produto,
                preco_antigo=instance.preco,
                preco_novo=produto.preco,
                alterado_por=self.context['request'].user if self.context.get('request') and self.context['request'].user.is_authenticated else None
            )
        
        return produto


class ProdutoListSerializer(serializers.ModelSerializer):
    """Serializer otimizado para listagens"""
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    preco_atual = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    desconto_percentual = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    imagem_principal_url = serializers.SerializerMethodField()
    is_favorito = serializers.SerializerMethodField()
    
    class Meta:
        model = Produto
        fields = [
            'id', 'nome', 'slug', 'descricao_curta', 'categoria_nome',
            'marca', 'preco', 'preco_promocional', 'preco_atual', 'desconto_percentual',
            'quantidade', 'disponivel', 'imagem_principal_url', 'is_favorito',
            'destaque', 'em_promocao', 'avaliacao_media'
        ]
    
    def get_imagem_principal_url(self, obj):
        if obj.imagem_principal:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagem_principal.url)
            return obj.imagem_principal.url
        return None
    
    def get_is_favorito(self, obj):
        """Verifica se o produto é favorito do usuário atual"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorito.objects.filter(
                usuario=request.user,
                produto=obj
            ).exists()
        return False


class ProdutoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação e atualização de produtos"""
    categoria_id = serializers.UUIDField(required=False)
    
    class Meta:
        model = Produto
        fields = [
            'nome', 'descricao', 'descricao_curta', 'categoria_id',
            'marca', 'estado', 'preco', 'preco_promocional',
            'quantidade', 'sku', 'codigo_barras', 'peso', 'dimensoes',
            'imagem_principal', 'imagem_secundaria', 'meta_titulo',
            'meta_descricao', 'publicado', 'destaque'
        ]
        extra_kwargs = {
            'preco': {'validators': [MinValueValidator(0.01)]},
            'preco_promocional': {'validators': [MinValueValidator(0.01)]},
            'quantidade': {'validators': [MinValueValidator(0)]},
        }
    
    def validate(self, data):
        """Validações adicionais"""
        errors = {}
        
        # Validar preço promocional
        preco_promocional = data.get('preco_promocional')
        preco = data.get('preco')
        
        if preco_promocional and preco:
            if preco_promocional >= preco:
                errors['preco_promocional'] = 'Preço promocional deve ser menor que o preço normal'
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data


class FavoritoSerializer(serializers.ModelSerializer):
    produto = ProdutoListSerializer(read_only=True)
    
    class Meta:
        model = Favorito
        fields = ['id', 'produto', 'data_criacao', 'notificar_promocao']
        read_only_fields = ['id', 'data_criacao']


class FavoritoCreateSerializer(serializers.ModelSerializer):
    produto_id = serializers.UUIDField()
    
    class Meta:
        model = Favorito
        fields = ['produto_id', 'notificar_promocao']


class ProdutoHistoricoPrecoSerializer(serializers.ModelSerializer):
    alterado_por_nome = serializers.CharField(source='alterado_por.nome', read_only=True)
    
    class Meta:
        model = ProdutoHistoricoPreco
        fields = ['id', 'preco_antigo', 'preco_novo', 'data_alteracao', 'alterado_por_nome']
        read_only_fields = fields


class ProdutoEstatisticasSerializer(serializers.Serializer):
    """Serializer para estatísticas do produto"""
    total_produtos = serializers.IntegerField()
    produtos_ativos = serializers.IntegerField()
    produtos_em_promocao = serializers.IntegerField()
    produtos_sem_estoque = serializers.IntegerField()
    produtos_por_categoria = serializers.DictField(child=serializers.IntegerField())
    valor_total_estoque = serializers.DecimalField(max_digits=12, decimal_places=2)