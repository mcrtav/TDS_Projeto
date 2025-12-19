from rest_framework import serializers
from categorias.models import Categoria


class CategoriaSerializer(serializers.ModelSerializer):
    """
    Serializer principal para o modelo Categoria.
    """
    
    # Campo calculado (read-only)
    quantidade_produtos = serializers.IntegerField(
        read_only=True,
        help_text='Quantidade de produtos nesta categoria'
    )
    
    # Campos para estatísticas (opcional)
    criado_em_formatado = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Categoria
        fields = [
            'id',
            'nome',
            'descricao',
            'icone',
            'cor',
            'ordem',
            'ativo',
            'deletado',
            'criado_em',
            'atualizado_em',
            'quantidade_produtos',
            'criado_em_formatado',
            'status_display'
        ]
        read_only_fields = [
            'id',
            'criado_em',
            'atualizado_em',
            'deletado',
            'deletado_em',
            'quantidade_produtos'
        ]
        extra_kwargs = {
            'nome': {
                'help_text': 'Nome único da categoria (3-100 caracteres)'
            },
            'descricao': {
                'help_text': 'Descrição opcional da categoria'
            },
            'icone': {
                'help_text': 'Ícone FontAwesome (ex: fas fa-mobile)'
            },
            'cor': {
                'help_text': 'Cor em HEX (#RRGGBB)'
            },
            'ordem': {
                'help_text': 'Ordem de exibição (menor = primeiro)'
            }
        }
    
    def get_criado_em_formatado(self, obj):
        """Formata a data de criação."""
        return obj.criado_em.strftime('%d/%m/%Y %H:%M')
    
    def get_status_display(self, obj):
        """Retorna o status em formato legível."""
        if obj.deletado:
            return 'Deletada'
        return 'Ativa' if obj.ativo else 'Inativa'
    
    def validate_nome(self, value):
        """Validação personalizada para o nome."""
        value = value.strip()
        
        if len(value) < 3:
            raise serializers.ValidationError(
                'O nome deve ter no mínimo 3 caracteres.'
            )
        
        if len(value) > 100:
            raise serializers.ValidationError(
                'O nome deve ter no máximo 100 caracteres.'
            )
        
        # Verifica se já existe uma categoria com este nome
        instance = self.instance
        queryset = Categoria.objects.filter(nome__iexact=value)
        
        if instance:
            # Exclui a instância atual da verificação (para updates)
            queryset = queryset.exclude(id=instance.id)
        
        if queryset.exists():
            raise serializers.ValidationError(
                'Já existe uma categoria com este nome.'
            )
        
        return value
    
    def validate_cor(self, value):
        """Validação para a cor HEX."""
        if value:
            value = value.strip().upper()
            
            # Garante que começa com #
            if not value.startswith('#'):
                value = f'#{value}'
            
            # Valida formato HEX
            import re
            if not re.match(r'^#[0-9A-F]{6}$', value):
                raise serializers.ValidationError(
                    'Cor deve estar no formato HEX (#RRGGBB).'
                )
        
        return value
    
    def validate_ordem(self, value):
        """Validação para a ordem."""
        if value < 0:
            raise serializers.ValidationError(
                'A ordem não pode ser negativa.'
            )
        
        return value
    
    def create(self, validated_data):
        """Cria uma nova categoria."""
        # Garante que a nova categoria esteja ativa
        validated_data['ativo'] = True
        validated_data['deletado'] = False
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Atualiza uma categoria existente."""
        # Não permite alterar o status deletado diretamente
        if 'deletado' in validated_data:
            del validated_data['deletado']
        
        return super().update(instance, validated_data)


class CategoriaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para criação de categorias.
    """
    
    class Meta:
        model = Categoria
        fields = ['nome', 'descricao', 'icone', 'cor', 'ordem']
    
    def create(self, validated_data):
        validated_data['ativo'] = True
        return Categoria.objects.create(**validated_data)


class CategoriaUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de categorias.
    """
    
    class Meta:
        model = Categoria
        fields = ['nome', 'descricao', 'icone', 'cor', 'ordem', 'ativo']
    
    def validate(self, data):
        """Validação global."""
        # Se estiver desativando, verifica se não há produtos
        if 'ativo' in data and data['ativo'] is False:
            if self.instance.quantidade_produtos > 0:
                raise serializers.ValidationError({
                    'ativo': 'Não é possível desativar uma categoria com produtos.'
                })
        
        return data


class CategoriaDetailSerializer(CategoriaSerializer):
    """
    Serializer detalhado com produtos relacionados.
    """
    
    produtos = serializers.SerializerMethodField()
    
    class Meta(CategoriaSerializer.Meta):
        fields = CategoriaSerializer.Meta.fields + ['produtos']
    
    def get_produtos(self, obj):
        """Retorna os produtos desta categoria."""
        try:
            from produtos.models import Produto
            produtos = Produto.objects.filter(
                categoria=obj,
                publicado=True,
                deleted=False
            )[:10]  # Limita a 10 produtos
            
            from produtos.serializers import ProdutoListSerializer
            return ProdutoListSerializer(produtos, many=True, context=self.context).data
        except (ImportError, AttributeError):
            return []


class CategoriaEstatisticasSerializer(serializers.Serializer):
    """
    Serializer para estatísticas das categorias.
    """
    
    total_categorias = serializers.IntegerField()
    categorias_ativas = serializers.IntegerField()
    categorias_inativas = serializers.IntegerField()
    categorias_deletadas = serializers.IntegerField()
    media_produtos_por_categoria = serializers.FloatField()
    categoria_com_mais_produtos = serializers.CharField()
    quantidade_na_categoria_mais_produtos = serializers.IntegerField()
    total_produtos = serializers.IntegerField()
    atualizado_em = serializers.CharField()