// Gerenciador de Produtos
class ProductsManager {
    constructor() {
        this.apiBase = '/api/produtos/';
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadCategorias();
        this.loadProdutos();
    }

    bindEvents() {
        // Busca
        document.getElementById('btn-buscar')?.addEventListener('click', () => this.buscarProdutos());
        document.getElementById('input-busca')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.buscarProdutos();
        });

        // Filtros
        document.getElementById('filtro-categoria')?.addEventListener('change', () => this.aplicarFiltros());
        document.getElementById('filtro-estoque')?.addEventListener('change', () => this.aplicarFiltros());
        document.getElementById('filtro-destaque')?.addEventListener('change', () => this.aplicarFiltros());

        // Formulário de produto
        document.getElementById('form-produto')?.addEventListener('submit', (e) => this.salvarProduto(e));

        // Preview de imagem
        document.getElementById('imagem')?.addEventListener('change', (e) => this.previewImagem(e));
    }

    async loadCategorias() {
        try {
            const response = await axios.get('/api/produtos/categorias/ativas/');
            const data = response.data;
            const select = document.getElementById('categoria_id');
            
            if (select) {
                select.innerHTML = '<option value="">Selecione uma categoria</option>';
                data.categorias.forEach(categoria => {
                    const option = document.createElement('option');
                    option.value = categoria.id;
                    option.textContent = categoria.nome;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Erro ao carregar categorias:', error);
            this.showMessage('Erro ao carregar categorias', 'danger');
        }
    }

    async loadProdutos() {
        this.showLoading();
        
        try {
            const response = await axios.get(this.apiBase);
            const data = response.data;
            this.renderProdutos(data.results || data);
        } catch (error) {
            console.error('Erro ao carregar produtos:', error);
            this.showMessage('Erro ao carregar produtos', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    async buscarProdutos() {
        const termo = document.getElementById('input-busca')?.value.trim();
        
        if (!termo) {
            this.loadProdutos();
            return;
        }

        this.showLoading();
        
        try {
            const response = await axios.get(`${this.apiBase}buscar/?q=${encodeURIComponent(termo)}`);
            const data = response.data;
            this.renderProdutos(data.resultados || data);
            
            const titulo = document.querySelector('.page-title');
            if (titulo && data.termo) {
                titulo.textContent = `Resultados para: "${data.termo}"`;
            }
        } catch (error) {
            console.error('Erro na busca:', error);
            this.showMessage('Erro na busca', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    renderProdutos(produtos) {
        const container = document.getElementById('produtos-container');
        if (!container) return;

        if (!produtos || produtos.length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info text-center">
                        <i class="fas fa-info-circle me-2"></i>
                        Nenhum produto encontrado.
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = produtos.map(produto => this.createProdutoCard(produto)).join('');
    }

    createProdutoCard(produto) {
        const statusEstoque = produto.status_estoque;
        
        return `
            <div class="col-md-4 col-lg-3 mb-4 fade-in">
                <div class="card product-card h-100">
                    ${produto.em_destaque ? 
                        '<span class="badge bg-warning product-badge">Destaque</span>' : ''}
                    
                    <img src="${produto.imagem_url}" 
                         class="card-img-top product-img" 
                         alt="${produto.nome}"
                         onerror="this.src='/static/frontend/img/produto_padrao.png'">
                    
                    <div class="card-body d-flex flex-column">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h5 class="card-title product-title">${produto.nome}</h5>
                            <button class="btn btn-link btn-sm p-0 favorite-btn" 
                                    onclick="productsManager.toggleFavorito(${produto.id}, this)"
                                    title="Adicionar aos favoritos">
                                <i class="far fa-heart"></i>
                            </button>
                        </div>
                        
                        <p class="card-text text-muted small mb-2">
                            <i class="fas fa-tag me-1"></i> ${produto.marca}
                        </p>
                        
                        <p class="card-text small mb-3 flex-grow-1">
                            ${produto.resumo_descricao}
                        </p>
                        
                        <div class="mt-auto">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="product-price">${produto.preco_formatado}</span>
                                <span class="badge ${statusEstoque.classe}">
                                    ${statusEstoque.texto}
                                </span>
                            </div>
                            
                            <div class="d-flex justify-content-between">
                                <a href="/produtos/${produto.id}" class="btn btn-sm btn-outline-primary">
                                    <i class="fas fa-eye me-1"></i> Detalhes
                                </a>
                                <a href="/produtos/${produto.id}/editar" class="btn btn-sm btn-outline-secondary">
                                    <i class="fas fa-edit me-1"></i> Editar
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async toggleFavorito(produtoId, button) {
        const isFavorito = button.classList.contains('active');
        const icon = button.querySelector('i');
        
        try {
            const url = `/api/usuarios/${isFavorito ? 'desfavoritar' : 'favoritar'}/${produtoId}/`;
            const method = isFavorito ? 'DELETE' : 'POST';
            
            const response = await axios({
                method: method,
                url: url,
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.status === 200 || response.status === 204) {
                button.classList.toggle('active');
                icon.className = isFavorito ? 'far fa-heart' : 'fas fa-heart';
                
                this.showMessage(
                    isFavorito ? 'Produto removido dos favoritos' : 'Produto adicionado aos favoritos',
                    'success'
                );
            }
        } catch (error) {
            console.error('Erro ao atualizar favoritos:', error);
            this.showMessage('Erro ao atualizar favoritos', 'danger');
        }
    }

    previewImagem(event) {
        const input = event.target;
        const preview = document.getElementById('imagem-preview');
        
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
            
            reader.readAsDataURL(input.files[0]);
        }
    }

    showLoading() {
        if (window.app && window.app.showLoading) {
            window.app.showLoading();
        }
    }

    hideLoading() {
        if (window.app && window.app.hideLoading) {
            window.app.hideLoading();
        }
    }

    showMessage(message, type) {
        if (window.app && window.app.showAlert) {
            window.app.showAlert(message, type);
        }
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('produtos-container')) {
        window.productsManager = new ProductsManager();
    }
});