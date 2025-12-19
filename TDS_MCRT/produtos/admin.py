from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode
from .models import Produto, Favorito, ProdutoHistoricoPreco


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        'nome', 'marca', 'categoria', 'preco_atual', 
        'quantidade', 'disponivel', 'publicado', 'destaque', 
        'em_promocao', 'visualizacoes', 'avaliacao_media'
    )
    list_filter = (
        'categoria', 'marca', 'estado', 'publicado', 
        'destaque', 'em_promocao', 'deleted'
    )
    search_fields = ('nome', 'descricao', 'marca', 'sku', 'codigo_barras')
    readonly_fields = (
        'id', 'data_criacao', 'data_atualizacao', 
        'visualizacoes', 'vendas', 'avaliacao_media', 'total_avaliacoes',
        'slug', 'imagem_preview'
    )
    list_per_page = 20
    actions = ['publicar_selecionados', 'ocultar_selecionados', 'destacar_selecionados', 'ativar_promocao_selecionados']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'descricao', 'descricao_curta', 'categoria')
        }),
        ('Detalhes do Produto', {
            'fields': ('marca', 'estado', 'sku', 'codigo_barras', 'peso', 'dimensoes')
        }),
        ('Preços e Estoque', {
            'fields': ('preco', 'preco_promocional', 'quantidade')
        }),
        ('Imagens', {
            'fields': ('imagem_principal', 'imagem_secundaria', 'imagem_preview')
        }),
        ('SEO', {
            'fields': ('meta_titulo', 'meta_descricao'),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': ('publicado', 'destaque', 'deleted')
        }),
        ('Estatísticas', {
            'fields': ('visualizacoes', 'vendas', 'avaliacao_media', 'total_avaliacoes'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('id', 'data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Personalizar queryset para admin"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(deleted=False)
    
    def imagem_preview(self, obj):
        """Exibir preview da imagem principal"""
        if obj.imagem_principal:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.imagem_principal.url
            )
        return "Sem imagem"
    imagem_preview.short_description = 'Preview'
    
    def preco_atual(self, obj):
        """Exibir preço atual formatado"""
        return obj.preco_formatado
    preco_atual.short_description = 'Preço'
    
    def disponivel(self, obj):
        """Indicador de disponibilidade"""
        if obj.disponivel:
            return format_html('<span style="color: green;">● Disponível</span>')
        return format_html('<span style="color: red;">● Indisponível</span>')
    disponivel.short_description = 'Disponível'
    
    def view_favoritos_link(self, obj):
        """Link para ver quem favoritou o produto"""
        count = obj.favoritado_por.count()
        url = (
            reverse("admin:produtos_favorito_changelist")
            + "?"
            + urlencode({"produto__id": f"{obj.id}"})
        )
        return format_html('<a href="{}">{} favoritos</a>', url, count)
    view_favoritos_link.short_description = "Favoritos"
    
    # Actions personalizadas
    def publicar_selecionados(self, request, queryset):
        queryset.update(publicado=True)
        self.message_user(request, f"{queryset.count()} produtos publicados.")
    publicar_selecionados.short_description = "Publicar produtos selecionados"
    
    def ocultar_selecionados(self, request, queryset):
        queryset.update(publicado=False)
        self.message_user(request, f"{queryset.count()} produtos ocultados.")
    ocultar_selecionados.short_description = "Ocultar produtos selecionados"
    
    def destacar_selecionados(self, request, queryset):
        queryset.update(destaque=True)
        self.message_user(request, f"{queryset.count()} produtos destacados.")
    destacar_selecionados.short_description = "Destacar produtos selecionados"
    
    def ativar_promocao_selecionados(self, request, queryset):
        for produto in queryset:
            if not produto.preco_promocional:
                produto.preco_promocional = produto.preco * 0.9
                produto.em_promocao = True
                produto.save()
        self.message_user(request, f"{queryset.count()} produtos com promoção ativada.")
    ativar_promocao_selecionados.short_description = "Ativar promoção nos produtos selecionados"


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'produto', 'data_criacao', 'notificar_promocao')
    list_filter = ('notificar_promocao', 'data_criacao')
    search_fields = ('usuario__email', 'produto__nome')
    readonly_fields = ('id', 'data_criacao')
    list_per_page = 20
    
    def get_queryset(self, request):
        """Personalizar queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('usuario', 'produto')


@admin.register(ProdutoHistoricoPreco)
class ProdutoHistoricoPrecoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'preco_antigo', 'preco_novo', 'data_alteracao', 'alterado_por')
    list_filter = ('data_alteracao',)
    search_fields = ('produto__nome', 'alterado_por__email')
    readonly_fields = ('id', 'data_alteracao')
    list_per_page = 20
    
    def get_queryset(self, request):
        """Personalizar queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('produto', 'alterado_por')