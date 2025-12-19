from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from produtos.models import Produto, Categoria
from django.utils import timezone
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de teste'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando população do banco de dados...')
        
        # Criar usuário admin
        admin_user, created = User.objects.get_or_create(
            email='admin@email.com',
            defaults={
                'nome': 'Administrador',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            admin_user.set_password('Admin@123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Usuário admin criado: admin@email.com / Admin@123'))
        
        # Criar usuário normal
        normal_user, created = User.objects.get_or_create(
            email='usuario@email.com',
            defaults={
                'nome': 'Usuário Teste',
                'is_active': True,
            }
        )
        if created:
            normal_user.set_password('Usuario@123')
            normal_user.save()
            self.stdout.write(self.style.SUCCESS('Usuário normal criado: usuario@email.com / Usuario@123'))
        
        # Criar categorias
        categorias_data = [
            {'nome': 'Eletrônicos', 'descricao': 'Dispositivos eletrônicos e gadgets'},
            {'nome': 'Informática', 'descricao': 'Computadores e acessórios'},
            {'nome': 'Celulares', 'descricao': 'Smartphones e acessórios'},
            {'nome': 'Livros', 'descricao': 'Livros de todos os gêneros'},
            {'nome': 'Games', 'descricao': 'Jogos e consoles'},
            {'nome': 'Eletrodomésticos', 'descricao': 'Eletrodomésticos para casa'},
            {'nome': 'Móveis', 'descricao': 'Móveis e decoração'},
            {'nome': 'Roupas', 'descricao': 'Vestuário em geral'},
            {'nome': 'Esportes', 'descricao': 'Artigos esportivos'},
            {'nome': 'Beleza', 'descricao': 'Produtos de beleza e cuidados pessoais'},
        ]
        
        categorias = []
        for i, cat_data in enumerate(categorias_data):
            categoria, created = Categoria.objects.get_or_create(
                nome=cat_data['nome'],
                defaults={
                    'descricao': cat_data['descricao'],
                    'ordem': i,
                    'ativo': True,
                    'cor': f'#{hex(100 + i*20)[2:].zfill(2)}{hex(150 + i*10)[2:].zfill(2)}{hex(200 - i*15)[2:].zfill(2)}'
                }
            )
            categorias.append(categoria)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Categoria criada: {categoria.nome}'))
        
        # Criar produtos
        produtos_data = [
            {
                'nome': 'Smartphone Samsung Galaxy S23',
                'descricao': 'Smartphone topo de linha com câmera de 200MP',
                'marca': 'Samsung',
                'preco': 4999.99,
                'quantidade': 50,
                'categoria': categorias[2],  # Celulares
            },
            {
                'nome': 'Notebook Dell Inspiron 15',
                'descricao': 'Notebook com processador i7 e 16GB RAM',
                'marca': 'Dell',
                'preco': 3599.99,
                'quantidade': 30,
                'categoria': categorias[1],  # Informática
            },
            {
                'nome': 'Smart TV LG 55" 4K',
                'descricao': 'TV Smart 4K com webOS e Alexa integrada',
                'marca': 'LG',
                'preco': 2999.99,
                'quantidade': 25,
                'categoria': categorias[0],  # Eletrônicos
            },
            {
                'nome': 'Fone de Ouvido Sony WH-1000XM5',
                'descricao': 'Fone com cancelamento de ruído ativo',
                'marca': 'Sony',
                'preco': 1999.99,
                'quantidade': 100,
                'categoria': categorias[0],  # Eletrônicos
            },
            {
                'nome': 'Console PlayStation 5',
                'descricao': 'Console de última geração com SSD 1TB',
                'marca': 'Sony',
                'preco': 4499.99,
                'quantidade': 15,
                'categoria': categorias[4],  # Games
            },
            {
                'nome': 'Livro: O Hobbit',
                'descricao': 'Edição especial do clássico de Tolkien',
                'marca': 'Editora HarperCollins',
                'preco': 59.99,
                'quantidade': 200,
                'categoria': categorias[3],  # Livros
            },
            {
                'nome': 'Geladeira Brastemp Frost Free',
                'descricao': 'Geladeira duplex com função frost free',
                'marca': 'Brastemp',
                'preco': 3299.99,
                'quantidade': 20,
                'categoria': categorias[5],  # Eletrodomésticos
            },
            {
                'nome': 'Sofá 3 Lugares Retrátil',
                'descricao': 'Sofá em couro sintético com apoio retrátil',
                'marca': 'Mobly',
                'preco': 1899.99,
                'quantidade': 10,
                'categoria': categorias[6],  # Móveis
            },
            {
                'nome': 'Tênis Nike Air Max',
                'descricao': 'Tênis esportivo com tecnologia Air Max',
                'marca': 'Nike',
                'preco': 499.99,
                'quantidade': 150,
                'categoria': categorias[8],  # Esportes
            },
            {
                'nome': 'Kit Maquiagem Profissional',
                'descricao': 'Kit completo com 32 cores de sombra',
                'marca': 'Ruby Rose',
                'preco': 299.99,
                'quantidade': 80,
                'categoria': categorias[9],  # Beleza
            },
        ]
        
        for prod_data in produtos_data:
            produto, created = Produto.objects.get_or_create(
                nome=prod_data['nome'],
                defaults={
                    'descricao': prod_data['descricao'],
                    'descricao_curta': prod_data['descricao'][:247] + '...' if len(prod_data['descricao']) > 250 else prod_data['descricao'],
                    'marca': prod_data['marca'],
                    'preco': prod_data['preco'],
                    'quantidade': prod_data['quantidade'],
                    'categoria': prod_data['categoria'],
                    'estado': 'novo',
                    'sku': f'PROD-{uuid.uuid4().hex[:8].upper()}',
                    'publicado': True,
                    'em_promocao': prod_data['preco'] > 1000,  # Produtos caros em promoção
                    'preco_promocional': prod_data['preco'] * 0.9 if prod_data['preco'] > 1000 else None,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Produto criado: {produto.nome}'))
        
        self.stdout.write(self.style.SUCCESS('População do banco de dados concluída com sucesso!'))