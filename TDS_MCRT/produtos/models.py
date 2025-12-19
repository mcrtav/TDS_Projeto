from django.db import models
import uuid
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from categorias.models import Categoria
from usuarios.models import Usuario


def produto_imagem_path(instance, filename):
    """Função para determinar o caminho de upload das imagens do produto"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'produtos/{instance.id}/{filename}'


class Produto(models.Model):
    ESTADO_CHOICES = [
        ('novo', 'Novo'),
        ('usado', 'Usado'),
        ('seminovo', 'Seminovo'),
        ('recondicionado', 'Recondicionado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(
        max_length=200,
        verbose_name='Nome do Produto',
        help_text='Nome completo do produto'
    )
    descricao = models.TextField(
        verbose_name='Descrição',
        help_text='Descrição detalhada do produto'
    )
    descricao_curta = models.CharField(
        max_length=255,
        verbose_name='Descrição Curta',
        help_text='Descrição breve para listagens',
        blank=True,
        null=True
    )
    
    # Relação com Categoria (1:N)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos',
        verbose_name='Categoria',
        help_text='Categoria do produto'
    )
    
    marca = models.CharField(
        max_length=100,
        verbose_name='Marca',
        help_text='Marca do produto'
    )
    
    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço',
        help_text='Preço do produto em R$',
        validators=[MinValueValidator(0.01)]
    )
    
    preco_promocional = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço Promocional',
        help_text='Preço com desconto (opcional)',
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)]
    )
    
    quantidade = models.IntegerField(
        default=0,
        verbose_name='Quantidade em Estoque',
        help_text='Quantidade disponível',
        validators=[MinValueValidator(0)]
    )
    
    sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='SKU',
        help_text='Código único do produto',
        blank=True,
        null=True
    )
    
    codigo_barras = models.CharField(
        max_length=100,
        verbose_name='Código de Barras',
        blank=True,
        null=True
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='novo',
        verbose_name='Estado do Produto'
    )
    
    peso = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        verbose_name='Peso (kg)',
        help_text='Peso em quilogramas',
        null=True,
        blank=True
    )
    
    dimensoes = models.CharField(
        max_length=100,
        verbose_name='Dimensões',
        help_text='Largura x Altura x Profundidade (cm)',
        blank=True,
        null=True
    )
    
    # Imagens
    imagem_principal = models.ImageField(
        upload_to=produto_imagem_path,
        verbose_name='Imagem Principal',
        help_text='Imagem principal do produto',
        null=True,
        blank=True
    )
    
    imagem_secundaria = models.ImageField(
        upload_to=produto_imagem_path,
        verbose_name='Imagem Secundária',
        help_text='Imagem adicional do produto',
        null=True,
        blank=True
    )
    
    # Campos de SEO
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name='Slug',
        help_text='URL amigável para o produto',
        blank=True,
        null=True
    )
    
    meta_titulo = models.CharField(
        max_length=255,
        verbose_name='Meta Título',
        help_text='Título para SEO',
        blank=True,
        null=True
    )
    
    meta_descricao = models.TextField(
        verbose_name='Meta Descrição',
        help_text='Descrição para SEO',
        blank=True,
        null=True
    )
    
    # Campos de controle
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')
    publicado = models.BooleanField(default=True, verbose_name='Publicado')
    destaque = models.BooleanField(default=False, verbose_name='Produto em Destaque')
    em_promocao = models.BooleanField(default=False, verbose_name='Em Promoção')
    
    # Soft Delete
    deleted = models.BooleanField(default=False, verbose_name='Deletado')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Data de Exclusão')
    
    # Estatísticas
    visualizacoes = models.IntegerField(default=0, verbose_name='Visualizações')
    vendas = models.IntegerField(default=0, verbose_name='Quantidade Vendida')
    avaliacao_media = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name='Avaliação Média',
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_avaliacoes = models.IntegerField(default=0, verbose_name='Total de Avaliações')

    class Meta:
        db_table = 'produtos'
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['marca']),
            models.Index(fields=['categoria']),
            models.Index(fields=['preco']),
            models.Index(fields=['destaque']),
            models.Index(fields=['em_promocao']),
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['publicado', 'deleted']),
        ]

    def __str__(self):
        return f'{self.nome} - {self.marca}'

    def save(self, *args, **kwargs):
        # Auto-gerar descrição curta se não fornecida
        if not self.descricao_curta and self.descricao:
            self.descricao_curta = self.descricao[:247] + '...' if len(self.descricao) > 250 else self.descricao
        
        # Auto-gerar slug se não fornecido
        if not self.slug and self.nome:
            from django.utils.text import slugify
            base_slug = slugify(self.nome)
            self.slug = base_slug
            counter = 1
            while Produto.objects.filter(slug=self.slug).exclude(id=self.id).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        # Atualizar campo em_promocao baseado no preço_promocional
        self.em_promocao = bool(self.preco_promocional and self.preco_promocional < self.preco)
        
        super().save(*args, **kwargs)

    def soft_delete(self):
        """Soft delete do produto"""
        self.deleted = True
        self.deleted_at = timezone.now()
        self.publicado = False
        self.save()

    def restore(self):
        """Restaurar produto deletado"""
        self.deleted = False
        self.deleted_at = None
        self.publicado = True
        self.save()

    @property
    def disponivel(self):
        """Verifica se o produto está disponível para venda"""
        return self.publicado and not self.deleted and self.quantidade > 0

    @property
    def preco_atual(self):
        """Retorna o preço atual (promocional se disponível)"""
        return self.preco_promocional if self.preco_promocional else self.preco

    @property
    def desconto_percentual(self):
        """Calcula o percentual de desconto"""
        if self.preco_promocional and self.preco > 0:
            desconto = ((self.preco - self.preco_promocional) / self.preco) * 100
            return round(desconto, 2)
        return 0

    @property
    def preco_formatado(self):
        """Preço formatado para exibição"""
        preco = self.preco_atual
        return f'R$ {preco:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @property
    def preco_original_formatado(self):
        """Preço original formatado (se houver promoção)"""
        if self.preco_promocional:
            return f'R$ {self.preco:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        return None

    @property
    def possui_imagens(self):
        """Verifica se o produto possui imagens"""
        return bool(self.imagem_principal or self.imagem_secundaria)

    def incrementar_visualizacoes(self):
        """Incrementa o contador de visualizações"""
        self.visualizacoes += 1
        self.save(update_fields=['visualizacoes'])

    def atualizar_avaliacao(self, nova_avaliacao):
        """Atualiza a avaliação média do produto"""
        if 0 <= nova_avaliacao <= 5:
            total_pontos = (self.avaliacao_media * self.total_avaliacoes) + nova_avaliacao
            self.total_avaliacoes += 1
            self.avaliacao_media = total_pontos / self.total_avaliacoes
            self.save(update_fields=['avaliacao_media', 'total_avaliacoes'])


class Favorito(models.Model):
    """Modelo para produtos favoritados pelos usuários"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='favoritos',
        verbose_name='Usuário'
    )
    
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='favoritado_por',
        verbose_name='Produto'
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    notificar_promocao = models.BooleanField(
        default=True,
        verbose_name='Notificar Promoção',
        help_text='Receber notificações quando este produto entrar em promoção'
    )

    class Meta:
        db_table = 'favoritos'
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        unique_together = ['usuario', 'produto']
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['usuario', 'data_criacao']),
        ]

    def __str__(self):
        return f'{self.usuario.email} favoritou {self.produto.nome}'


class ProdutoHistoricoPreco(models.Model):
    """Histórico de preços do produto"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='historico_precos',
        verbose_name='Produto'
    )
    preco_antigo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço Antigo')
    preco_novo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço Novo')
    data_alteracao = models.DateTimeField(auto_now_add=True, verbose_name='Data da Alteração')
    alterado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Alterado Por'
    )

    class Meta:
        db_table = 'produto_historico_preco'
        verbose_name = 'Histórico de Preço'
        verbose_name_plural = 'Históricos de Preço'
        ordering = ['-data_alteracao']

    def __str__(self):
        return f'{self.produto.nome}: R${self.preco_antigo} → R${self.preco_novo}'

        # Adicione esta função no início do arquivo (após os imports)
def produto_imagem_path(instance, filename):
    """Função para determinar o caminho de upload das imagens do produto"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'produtos/{instance.id}/{filename}'

# A função categoria_imagem_path não existe, vamos criar se necessário
def categoria_imagem_path(instance, filename):
    """Função para determinar o caminho de upload das imagens da categoria"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'categorias/{instance.id}/{filename}'