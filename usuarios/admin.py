from django.contrib import admin
from django.utils.html import format_html
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('email', 'nome', 'is_active', 'is_staff', 'date_joined', 'deleted')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'deleted', 'date_joined', 'estado')
    search_fields = ('email', 'nome', 'cpf', 'telefone')
    readonly_fields = ('id', 'date_joined', 'last_login', 'foto_preview')
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('nome', 'email', 'cpf', 'telefone', 'foto', 'foto_preview')
        }),
        ('Endereço', {
            'fields': ('cep', 'logradouro', 'numero', 'complemento', 
                      'bairro', 'cidade', 'estado')
        }),
        ('Controle de Acesso', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Auditoria', {
            'fields': ('id', 'date_joined', 'last_login', 
                      'deleted', 'deleted_at')
        }),
        ('Recuperação de Senha', {
            'fields': ('reset_token', 'reset_token_expires'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Mostrar todos os usuários (incluindo deletados) para admin"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(deleted=False)
    
    def has_delete_permission(self, request, obj=None):
        """Permitir apenas soft delete"""
        return False
    
    def delete_model(self, request, obj):
        """Sobrescrever delete para usar soft delete"""
        obj.soft_delete()
    
    def foto_preview(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 50%;" />',
                obj.foto.url
            )
        return "Sem foto"
    
    foto_preview.short_description = 'Pré-visualização da Foto'