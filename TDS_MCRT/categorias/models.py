from django.db import models
from django.utils import timezone
import uuid
from django.core.validators import MinLengthValidator


class Categoria(models.Model):
    """
    Modelo para representar categorias de produtos.
    Suporta soft delete e relacionamento com produtos.
    """
    
    # ID único usando UUID
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )
    
    # Campos obrigatórios
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome',
        help_text='Nome da categoria (ex: Eletrônicos, Roupas)',
        validators=[MinLengthValidator(3)],
        error_messages={
            'unique': 'Já existe uma categoria com este nome.',
            'max_length': 'O nome não pode ter mais de 100 caracteres.'
        }
    )
    
    descricao = models.TextField(
        verbose_name='Descrição',
        help_text='Descrição detalhada da categoria',
        null=True,
        blank=True
    )
    
    # Campos opcionais para personalização
    icone = models.CharField(
        max_length=50,
        verbose_name='Ícone',
        help_text='Classe do FontAwesome para ícone (ex: fas fa-mobile)',
        null=True,
        blank=True,
        default='fas fa-tag'
    )
    
    cor = models.CharField(
        max_length=7,
        verbose_name='Cor',
        help_text='Cor em formato HEX (#RRGGBB)',
        default='#007bff'
    )
    
    # Campos de data
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    # Campos para soft delete
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativa',
        help_text='Se a categoria está ativa para uso'
    )
    
    deletado = models.BooleanField(
        default=False,
        verbose_name='Deletada',
        help_text='Se a categoria foi deletada (soft delete)'
    )
    
    deletado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Deletado em'
    )
    
    # Ordem de exibição
    ordem = models.IntegerField(
        default=0,
        verbose_name='Ordem',
        help_text='Ordem de exibição da categoria (menor = primeiro)'
    )

    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['ordem', 'nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['ativo']),
            models.Index(fields=['ordem']),
        ]
    
    def __str__(self):
        """Representação em string da categoria."""
        return f'{self.nome}'
    
    def __repr__(self):
        """Representação para debugging."""
        return f'<Categoria: {self.nome} ({self.id})>'
    
    def soft_delete(self):
        """
        Realiza soft delete da categoria.
        Marca como deletada, inativa e salva a data.
        """
        self.deletado = True
        self.ativo = False
        self.deletado_em = timezone.now()
        self.save()
    
    def restaurar(self):
        """
        Restaura uma categoria deletada.
        """
        self.deletado = False
        self.ativo = True
        self.deletado_em = None
        self.save()
    
    def toogle_ativo(self):
        """
        Alterna o status ativo/inativo da categoria.
        """
        self.ativo = not self.ativo
        self.save()
    
    @property
    def quantidade_produtos(self):
        """
        Retorna a quantidade de produtos nesta categoria.
        """
        try:
            from produtos.models import Produto
            return Produto.objects.filter(
                categoria=self,
                publicado=True,
                deleted=False
            ).count()
        except (ImportError, AttributeError):
            return 0
    
    @classmethod
    def categorias_ativas(cls):
        """Retorna todas as categorias ativas."""
        return cls.objects.filter(ativo=True, deletado=False)
    
    @classmethod
    def categorias_com_produtos(cls):
        """Retorna categorias que possuem produtos."""
        try:
            from produtos.models import Produto
            categorias_com_produtos = Produto.objects.filter(
                publicado=True,
                deleted=False
            ).values_list('categoria_id', flat=True).distinct()
            
            return cls.objects.filter(
                id__in=categorias_com_produtos,
                ativo=True,
                deletado=False
            )
        except (ImportError, AttributeError):
            return cls.objects.none()
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir consistência.
        """
        # Garante que o nome esteja capitalizado
        self.nome = self.nome.strip()
        
        # Se estiver deletado, garante que está inativo
        if self.deletado:
            self.ativo = False
        
        # Valida a cor HEX se fornecida
        if self.cor and not self.cor.startswith('#'):
            self.cor = f'#{self.cor}'
        
        super().save(*args, **kwargs)