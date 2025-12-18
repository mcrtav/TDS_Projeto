from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """
    Configuração do admin para o modelo Categoria.
    """
    
    list_display = [
        'nome',
        'icone_display',
        'cor_display',
        'ordem',
        'ativo',
        'deletado',
        'quantidade_produtos_display',
        'criado_em_formatado'
    ]
    
    list_filter = [
        'ativo',
        'deletado',
        'criado_em',
        'atualizado_em'
    ]
    
    search_fields = [
        'nome',
        'descricao'
    ]
    
    list_editable = [
        'ordem',
        'ativo'
    ]
    
    ordering = ['ordem', 'nome']
    
    readonly_fields = [
        'id',
        'criado_em',
        'atualizado_em',
        'deletado_em',
        'quantidade_produtos_display',
        'icone_display',
        'cor_display'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'icone', 'cor', 'ordem')
        }),
        ('Status', {
            'fields': ('ativo', 'deletado', 'deletado_em')
        }),
        ('Informações do Sistema', {
            'fields': ('id', 'criado_em', 'atualizado_em', 'quantidade_produtos_display'),
            'classes': ('collapse',)
        }),
        ('Visualização', {
            'fields': ('icone_display', 'cor_display'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['ativar_selecionadas', 'desativar_selecionadas', 'soft_delete_selecionadas']
    
    def icone_display(self, obj):
        """Exibe o ícone no admin."""
        if obj.icone:
            return format_html(
                '<i class="{}" style="font-size: 1.2em;"></i>',
                obj.icone
            )
        return '-'
    
    icone_display.short_description = 'Ícone'
    
    def cor_display(self, obj):
        """Exibe a cor no admin."""
        if obj.cor:
            return format_html(
                '<div style="background-color: {}; width: 30px; height: 30px; border-radius: 4px; border: 1px solid #ccc;"></div>',
                obj.cor
            )
        return '-'
    
    cor_display.short_description = 'Cor'
    
    def quantidade_produtos_display(self, obj):
        """Exibe a quantidade de produtos."""
        return obj.quantidade_produtos
    
    quantidade_produtos_display.short_description = 'Produtos'
    
    def criado_em_formatado(self, obj):
        """Formata a data de criação."""
        return obj.criado_em.strftime('%d/%m/%Y %H:%M')
    
    criado_em_formatado.short_description = 'Criado em'
    
    def ativar_selecionadas(self, request, queryset):
        """Ação para ativar categorias selecionadas."""
        updated = queryset.update(ativo=True)
        self.message_user(
            request,
            f'{updated} categoria(s) ativada(s) com sucesso.'
        )
    
    ativar_selecionadas.short_description = 'Ativar categorias selecionadas'
    
    def desativar_selecionadas(self, request, queryset):
        """Ação para desativar categorias selecionadas."""
        updated = queryset.update(ativo=False)
        if updated > 0:
            self.message_user(
                request,
                f'{updated} categoria(s) desativada(s) com sucesso.'
            )
    
    desativar_selecionadas.short_description = 'Desativar categorias selecionadas'
    
    def soft_delete_selecionadas(self, request, queryset):
        """Ação para soft delete de categorias selecionadas."""
        from django.utils import timezone
        updated = queryset.update(deletado=True, deletado_em=timezone.now(), ativo=False)
        if updated > 0:
            self.message_user(
                request,
                f'{updated} categoria(s) deletada(s) com sucesso.'
            )
    
    soft_delete_selecionadas.short_description = 'Deletar categorias selecionadas (soft delete)'
    
    def get_queryset(self, request):
        """Personaliza o queryset no admin."""
        qs = super().get_queryset(request)
        # Mostra todas as categorias para admin
        return qs
    
    def has_delete_permission(self, request, obj=None):
        """
        Remove a opção de delete físico (usamos soft delete).
        """
        return False