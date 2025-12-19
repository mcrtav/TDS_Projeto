from django.core.management.base import BaseCommand
from produtos.models import Produto, Categoria
from decimal import Decimal

class Command(BaseCommand):
    help = 'Popula o banco de dados com produtos de teste'
    
    def handle(self, *args, **options):
        # Criar categorias
        categorias_data = [
            {'nome': 'Eletrônicos', 'descricao': 'Produtos eletrônicos em geral'},
            {'nome': 'Informática', 'descricao': 'Computadores e acessórios'},
            {'nome': 'Celulares', 'descricao': 'Smartphones e tablets'},
            {'nome': 'Eletrodomésticos', 'descricao': 'Eletrodomésticos para casa'},
        ]
        
        categorias = []
        for cat_data in categorias_data:
            categoria, created = Categoria.objects.get_or_create(
                nome=cat_data['nome'],
                defaults=cat_data
            )
            categorias.append(categoria)
            if created:
                self.stdout.write(f'Categoria criada: {categoria.nome}')
        
        # Produtos de teste
        produtos_data = [
            {
                'nome': 'Notebook Dell Inspiron',
                'descricao': 'Notebook Dell Inspiron i7 16GB RAM 512GB SSD',
                'marca': 'Dell',
                'preco': Decimal('4299.99'),
                'categoria': categorias[1],
                'telefone_fornecedor': '(11) 99999-9999',
                'quantidade_estoque': 15,
                'em_destaque': True,
            },
            {
                'nome': 'iPhone 15',
                'descricao': 'Apple iPhone 15 128GB Preto',
                'marca': 'Apple',
                'preco': Decimal('5999.99'),
                'categoria': categorias[2],
                'telefone_fornecedor': '(21) 88888-8888',
                'quantidade_estoque': 8,
                'em_destaque': True,
            },
            {
                'nome': 'Smart TV Samsung 55"',
                'descricao': 'Smart TV Samsung 55" 4K UHD',
                'marca': 'Samsung',
                'preco': Decimal('2799.99'),
                'categoria': categorias[0],
                'telefone_fornecedor': '(31) 77777-7777',
                'quantidade_estoque': 12,
                'em_destaque': True,
            },
            {
                'nome': 'Geladeira Brastemp',
                'descricao': 'Geladeira Brastemp Frost Free 375L',
                'marca': 'Brastemp',
                'preco': Decimal('3299.99'),
                'categoria': categorias[3],
                'telefone_fornecedor': '(41) 66666-6666',
                'quantidade_estoque': 6,
            },
            {
                'nome': 'Mouse Logitech',
                'descricao': 'Mouse sem fio Logitech MX Master 3',
                'marca': 'Logitech',
                'preco': Decimal('399.99'),
                'categoria': categorias[1],
                'telefone_fornecedor': '(51) 55555-5555',
                'quantidade_estoque': 25,
            },
            {
                'nome': 'Tablet Samsung',
                'descricao': 'Tablet Samsung Galaxy Tab S8',
                'marca': 'Samsung',
                'preco': Decimal('2499.99'),
                'categoria': categorias[2],
                'telefone_fornecedor': '(61) 44444-4444',
                'quantidade_estoque': 10,
            },
            {
                'nome': 'Forno Elétrico',
                'descricao': 'Forno Elétrico de Embutir 56L',
                'marca': 'Electrolux',
                'preco': Decimal('899.99'),
                'categoria': categorias[3],
                'telefone_fornecedor': '(71) 33333-3333',
                'quantidade_estoque': 7,
            },
            {
                'nome': 'Headphone Sony',
                'descricao': 'Headphone Sony WH-1000XM4',
                'marca': 'Sony',
                'preco': Decimal('1299.99'),
                'categoria': categorias[0],
                'telefone_fornecedor': '(81) 22222-2222',
                'quantidade_estoque': 18,
            },
            {
                'nome': 'Monitor LG',
                'descricao': 'Monitor LG UltraGear 27" 144Hz',
                'marca': 'LG',
                'preco': Decimal('1499.99'),
                'categoria': categorias[1],
                'telefone_fornecedor': '(91) 11111-1111',
                'quantidade_estoque': 14,
            },
            {
                'nome': 'Ventilador de Teto',
                'descricao': 'Ventilador de Teto 6 Pás',
                'marca': 'Arno',
                'preco': Decimal('299.99'),
                'categoria': categorias[3],
                'telefone_fornecedor': '(19) 12345-6789',
                'quantidade_estoque': 22,
            },
        ]
        
        produtos_criados = 0
        for prod_data in produtos_data:
            produto, created = Produto.objects.get_or_create(
                nome=prod_data['nome'],
                defaults=prod_data
            )
            if created:
                produtos_criados += 1
                self.stdout.write(f'Produto criado: {produto.nome}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSeed concluído! {len(categorias)} categorias e {produtos_criados} produtos criados.')
        )