import re
from rest_framework import serializers
from usuarios.models import Usuario
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import requests


class CadastroSerializer(serializers.ModelSerializer):
    senha = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Senha com mínimo 8 caracteres, incluindo maiúsculas, minúsculas, números e caracteres especiais'
    )
    senha_confirmacao = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Confirmação da senha'
    )
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'nome', 'email', 'cpf', 'telefone',
            'cep', 'logradouro', 'numero', 'complemento',
            'bairro', 'cidade', 'estado',
            'senha', 'senha_confirmacao', 'foto'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'nome': {'help_text': 'Nome completo com no mínimo 3 caracteres'},
            'email': {'help_text': 'E-mail válido e único'},
            'cpf': {'help_text': 'CPF no formato 000.000.000-00 (opcional)'},
            'telefone': {'help_text': 'Telefone no formato (00) 00000-0000 (opcional)'},
        }

    def validate_nome(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError(
                'Nome deve ter no mínimo 3 caracteres'
            )
        
        # Verificar se nome contém apenas letras e espaços
        if not re.match(r'^[A-Za-zÀ-ÿ\s]+$', value):
            raise serializers.ValidationError(
                'Nome deve conter apenas letras e espaços'
            )
        
        return value

    def validate_email(self, value):
        value = value.lower().strip()
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError('E-mail inválido')
        
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError('E-mail já cadastrado')
        
        return value

    def validate_cpf(self, value):
        if value:
            value = value.strip()
            # Remover formatação para validação
            cpf_numeros = re.sub(r'\D', '', value)
            
            if len(cpf_numeros) != 11:
                raise serializers.ValidationError('CPF deve ter 11 dígitos')
            
            # Validar dígitos verificadores
            if not self.validar_cpf(cpf_numeros):
                raise serializers.ValidationError('CPF inválido')
            
            # Verificar se CPF já existe
            if Usuario.objects.filter(cpf=value).exclude(cpf='').exists():
                raise serializers.ValidationError('CPF já cadastrado')
        
        return value

    def validate_telefone(self, value):
        if value:
            value = value.strip()
            # Verificar formato
            if not re.match(r'^\(\d{2}\) \d{5}-\d{4}$', value):
                raise serializers.ValidationError(
                    'Telefone deve estar no formato (00) 00000-0000'
                )
        return value

    def validate_senha(self, value):
        # Validar senha complexa
        valido, mensagem = Usuario.validar_senha_complexa(value)
        if not valido:
            raise serializers.ValidationError(mensagem)
        return value

    def validate_cep(self, value):
        if value:
            value = value.replace('-', '').strip()
            if len(value) != 8 or not value.isdigit():
                raise serializers.ValidationError('CEP inválido')
            
            # Formatar CEP
            value = f"{value[:5]}-{value[5:]}"
            
            # Consultar BrasilAPI
            try:
                response = requests.get(f'https://brasilapi.com.br/api/cep/v2/{value}')
                if response.status_code != 200:
                    raise serializers.ValidationError('CEP não encontrado')
            except:
                pass  # Se a API falhar, continuamos sem validação
        
        return value

    def validate(self, data):
        # Validar confirmação de senha
        if data.get('senha') != data.get('senha_confirmacao'):
            raise serializers.ValidationError({
                'senha_confirmacao': 'As senhas não coincidem'
            })
        
        return data

    def create(self, validated_data):
        # Remover campo de confirmação
        validated_data.pop('senha_confirmacao', None)
        senha = validated_data.pop('senha')
        
        # Garantir que email esteja em minúsculas
        validated_data['email'] = validated_data['email'].lower()
        
        # Buscar endereço pelo CEP se necessário
        if validated_data.get('cep') and not validated_data.get('logradouro'):
            self.buscar_endereco_por_cep(validated_data)
        
        usuario = Usuario.objects.create_user(
            **validated_data,
            password=senha
        )
        
        return usuario

    def buscar_endereco_por_cep(self, data):
        """Busca endereço usando BrasilAPI"""
        cep = data['cep'].replace('-', '')
        try:
            response = requests.get(f'https://brasilapi.com.br/api/cep/v2/{cep}')
            if response.status_code == 200:
                endereco = response.json()
                data['logradouro'] = endereco.get('street', data.get('logradouro', ''))
                data['bairro'] = endereco.get('neighborhood', data.get('bairro', ''))
                data['cidade'] = endereco.get('city', data.get('cidade', ''))
                data['estado'] = endereco.get('state', data.get('estado', ''))
        except:
            pass  # Silencia erros da API

    @staticmethod
    def validar_cpf(cpf):
        """Validação de CPF (algoritmo oficial)"""
        # Remover caracteres não numéricos
        cpf = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf) != 11:
            return False
        
        # Verificar se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Validar primeiro dígito verificador
        soma = 0
        peso = 10
        for i in range(9):
            soma += int(cpf[i]) * peso
            peso -= 1
        
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if digito1 != int(cpf[9]):
            return False
        
        # Validar segundo dígito verificador
        soma = 0
        peso = 11
        for i in range(10):
            soma += int(cpf[i]) * peso
            peso -= 1
        
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return digito2 == int(cpf[10])

# # No arquivo serializers.py, modifique o LoginSerializer:

# class LoginSerializer(serializers.Serializer):
#     email = serializers.EmailField(
#         required=True,
#         help_text='E-mail cadastrado'
#     )
#     password = serializers.CharField(  # Alterado de 'senha' para 'password'
#         required=True,
#         write_only=True,
#         style={'input_type': 'password'},
#         help_text='Senha do usuário'
#     )
#     remember_me = serializers.BooleanField(
#         required=False,
#         default=False,
#         help_text='Manter sessão ativa por mais tempo'
#     )

#     def validate(self, data):
#         email = data.get('email').lower().strip()
#         password = data.get('password')  # Alterado de 'senha' para 'password'
        
#         try:
#             usuario = Usuario.objects.get(email=email)
#         except Usuario.DoesNotExist:
#             raise serializers.ValidationError({
#                 'email': 'Credenciais inválidas'
#             })
        
#         if not usuario.check_password(password):  # Alterado de 'senha' para 'password'
#             raise serializers.ValidationError({
#                 'password': 'Credenciais inválidas'  # Alterado de 'senha' para 'password'
#             })
        
#         if not usuario.is_active:
#             raise serializers.ValidationError('Usuário inativo. Contate o administrador.')
        
#         if usuario.deleted:
#             raise serializers.ValidationError('Usuário deletado. Contate o administrador para restaurar.')
        
#         data['usuario'] = usuario
#         return data

# No arquivo serializers.py, simplifique o LoginSerializer:

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        email = data.get('email').lower().strip()
        password = data.get('password')
        
        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError({
                'email': 'Credenciais inválidas'
            })
        
        if not usuario.check_password(password):
            raise serializers.ValidationError({
                'password': 'Credenciais inválidas'
            })
        
        if not usuario.is_active:
            raise serializers.ValidationError('Usuário inativo. Contate o administrador.')
        
        if usuario.deleted:
            raise serializers.ValidationError('Usuário deletado. Contate o administrador para restaurar.')
        
        data['usuario'] = usuario
        return data
    
class UsuarioSerializer(serializers.ModelSerializer):
    endereco_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'nome', 'email', 'cpf', 'telefone',
            'cep', 'logradouro', 'numero', 'complemento',
            'bairro', 'cidade', 'estado', 'endereco_completo',
            'foto', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'foto': {'required': False, 'allow_null': True}
        }
    
    def get_endereco_completo(self, obj):
        return obj.endereco_completo
    
    def validate_cep(self, value):
        if value:
            value = value.replace('-', '').strip()
            if len(value) != 8 or not value.isdigit():
                raise serializers.ValidationError('CEP inválido')
            value = f"{value[:5]}-{value[5:]}"
        return value


class UsuarioPerfilSerializer(serializers.ModelSerializer):
    endereco_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'nome', 'email', 'cpf', 'telefone',
            'endereco_completo', 'foto', 
            'date_joined', 'last_login'
        ]
        read_only_fields = fields
    
    def get_endereco_completo(self, obj):
        return obj.endereco_completo


class RecuperarSenhaSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        help_text='E-mail cadastrado para recuperação'
    )


class ResetarSenhaSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=True,
        help_text='Token de recuperação recebido por e-mail'
    )
    nova_senha = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Nova senha'
    )
    confirmar_senha = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Confirmação da nova senha'
    )

    def validate(self, data):
        if data['nova_senha'] != data['confirmar_senha']:
            raise serializers.ValidationError({
                'confirmar_senha': 'As senhas não coincidem'
            })
        
        # Validar senha complexa
        valido, mensagem = Usuario.validar_senha_complexa(data['nova_senha'])
        if not valido:
            raise serializers.ValidationError({'nova_senha': mensagem})
        
        return data


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'nome', 'cpf', 'telefone', 'cep', 'logradouro',
            'numero', 'complemento', 'bairro', 'cidade', 'estado', 'foto'
        ]
    
    def validate_cep(self, value):
        if value:
            value = value.replace('-', '').strip()
            if len(value) != 8 or not value.isdigit():
                raise serializers.ValidationError('CEP inválido')
            
            # Formatar CEP
            value = f"{value[:5]}-{value[5:]}"
            
            # Se logradouro não foi fornecido, buscar da API
            if not self.initial_data.get('logradouro'):
                try:
                    response = requests.get(f'https://brasilapi.com.br/api/cep/v2/{value}')
                    if response.status_code == 200:
                        endereco = response.json()
                        # Atualizar dados do serializer
                        self.initial_data['logradouro'] = endereco.get('street', '')
                        self.initial_data['bairro'] = endereco.get('neighborhood', '')
                        self.initial_data['cidade'] = endereco.get('city', '')
                        self.initial_data['estado'] = endereco.get('state', '')
                except:
                    pass
        
        return value