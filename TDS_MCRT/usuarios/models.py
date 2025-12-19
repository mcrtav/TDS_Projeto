import re
import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


def usuario_foto_path(instance, filename):
    """Função para determinar o caminho de upload da foto"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'usuarios/fotos/{filename}'


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, senha=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        if not nome:
            raise ValueError('O nome é obrigatório')
        
        email = self.normalize_email(email)
        usuario = self.model(email=email, nome=nome, **extra_fields)
        usuario.set_password(senha)
        usuario.save(using=self._db)
        return usuario
    
    def create_superuser(self, email, nome, senha=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(email, nome, senha, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(
        max_length=100,
        verbose_name='Nome Completo',
        help_text='Nome completo do usuário'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='E-mail',
        help_text='E-mail do usuário'
    )
    
    # Campo validado com Regex (CPF)
    cpf = models.CharField(
        max_length=14,
        verbose_name='CPF',
        help_text='CPF no formato 000.000.000-00',
        validators=[
            RegexValidator(
                regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
                message='CPF deve estar no formato 000.000.000-00'
            )
        ],
        null=True,
        blank=True
    )
    
    telefone = models.CharField(
        max_length=15,
        verbose_name='Telefone',
        help_text='Telefone no formato (00) 00000-0000',
        validators=[
            RegexValidator(
                regex=r'^\(\d{2}\) \d{5}-\d{4}$',
                message='Telefone deve estar no formato (00) 00000-0000'
            )
        ],
        null=True,
        blank=True
    )
    
    # Campos de endereço
    cep = models.CharField(max_length=9, null=True, blank=True)
    logradouro = models.CharField(max_length=200, null=True, blank=True)
    numero = models.CharField(max_length=10, null=True, blank=True)
    complemento = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=2, null=True, blank=True)
    
    foto = models.ImageField(
        upload_to=usuario_foto_path,
        null=True,
        blank=True,
        verbose_name='Foto de Perfil',
        help_text='Envie uma foto para seu perfil (opcional)'
    )
    
    # Campos de controle
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Campos para reset de senha
    reset_token = models.CharField(max_length=100, null=True, blank=True)
    reset_token_expires = models.DateTimeField(null=True, blank=True)
    
    # Soft Delete
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UsuarioManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['cpf']),
            models.Index(fields=['date_joined']),
            models.Index(fields=['deleted']),
        ]

    def __str__(self):
        return f'{self.nome} ({self.email})'

    def set_password(self, senha):
        """Hash da senha antes de salvar"""
        self.password = make_password(senha)

    def check_password(self, senha_texto):
        """Verifica se a senha em texto plano corresponde ao hash"""
        return check_password(senha_texto, self.password)

    def soft_delete(self):
        """Marca o usuário como deletado (soft delete)"""
        self.deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save()

    def restore(self):
        """Restaura um usuário deletado"""
        self.deleted = False
        self.deleted_at = None
        self.is_active = True
        self.save()

    def gerar_reset_token(self):
        """Gera um token para reset de senha"""
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expires = timezone.now() + timezone.timedelta(hours=1)
        self.save()
        return self.reset_token

    def reset_token_valido(self):
        """Verifica se o token de reset é válido"""
        if not self.reset_token or not self.reset_token_expires:
            return False
        return self.reset_token_expires > timezone.now()

    @property
    def endereco_completo(self):
        """Retorna o endereço completo formatado"""
        partes = []
        if self.logradouro:
            partes.append(self.logradouro)
        if self.numero:
            partes.append(f"Nº {self.numero}")
        if self.complemento:
            partes.append(f"({self.complemento})")
        if self.bairro:
            partes.append(f"- {self.bairro}")
        if self.cidade:
            partes.append(f", {self.cidade}")
        if self.estado:
            partes.append(f"/{self.estado}")
        if self.cep:
            partes.append(f"CEP: {self.cep}")
        
        return " ".join(partes) if partes else None

    @staticmethod
    def validar_senha_complexa(senha):
        """
        Valida senha com os requisitos:
        - Mínimo 8 caracteres
        - Pelo menos 1 letra maiúscula
        - Pelo menos 1 letra minúscula
        - Pelo menos 1 número
        - Pelo menos 1 caractere especial
        """
        erros = []
        
        if len(senha) < 8:
            erros.append("A senha deve ter no mínimo 8 caracteres")
        
        if not re.search(r'[A-Z]', senha):
            erros.append("A senha deve conter pelo menos 1 letra maiúscula")
        
        if not re.search(r'[a-z]', senha):
            erros.append("A senha deve conter pelo menos 1 letra minúscula")
        
        if not re.search(r'\d', senha):
            erros.append("A senha deve conter pelo menos 1 número")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
            erros.append("A senha deve conter pelo menos 1 caractere especial")
        
        return len(erros) == 0, erros[0] if erros else "Senha válida"