// Funções utilitárias globais

// Formatar moeda brasileira
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Formatar data
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Validar email
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Validar CPF
function validateCPF(cpf) {
    cpf = cpf.replace(/[^\d]+/g, '');
    if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false;
    
    let sum = 0;
    for (let i = 0; i < 9; i++) {
        sum += parseInt(cpf.charAt(i)) * (10 - i);
    }
    let remainder = (sum * 10) % 11;
    if (remainder === 10 || remainder === 11) remainder = 0;
    if (remainder !== parseInt(cpf.charAt(9))) return false;
    
    sum = 0;
    for (let i = 0; i < 10; i++) {
        sum += parseInt(cpf.charAt(i)) * (11 - i);
    }
    remainder = (sum * 10) % 11;
    if (remainder === 10 || remainder === 11) remainder = 0;
    
    return remainder === parseInt(cpf.charAt(10));
}

// Validar telefone
function validatePhone(phone) {
    const re = /^\(\d{2}\) \d{5}-\d{4}$/;
    return re.test(phone);
}

// Validar senha forte
function validatePassword(password) {
    const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$/;
    return re.test(password);
}

// Mostrar notificação toast
function showToast(message, type = 'info') {
    // Criar container de toasts se não existir
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1060;
            max-width: 350px;
        `;
        document.body.appendChild(toastContainer);
    }
    
    // Criar toast
    const toast = document.createElement('div');
    toast.className = `toast show ${type}`;
    toast.style.cssText = `
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : type === 'warning' ? '#ffc107' : '#17a2b8'};
        color: white;
        border-radius: 8px;
        padding: 15px 20px;
        margin-bottom: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease-out;
    `;
    
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-3" style="font-size: 1.5rem;"></i>
            <div>
                <strong class="d-block">${type === 'success' ? 'Sucesso!' : type === 'error' ? 'Erro!' : type === 'warning' ? 'Atenção!' : 'Informação'}</strong>
                <span>${message}</span>
            </div>
            <button type="button" class="btn-close btn-close-white ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Remover toast após 5 segundos
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 300);
        }
    }, 5000);
    
    // Adicionar estilos de animação
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Carregar dados do usuário autenticado
function loadUserProfile() {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) return;
    
    fetch('/api/usuarios/me/', {
        headers: {
            'Authorization': 'Bearer ' + accessToken
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Não autenticado');
    })
    .then(user => {
        localStorage.setItem('user', JSON.stringify(user));
        
        // Atualizar UI se necessário
        const userElements = document.querySelectorAll('[data-user-name]');
        userElements.forEach(el => {
            el.textContent = user.nome;
        });
        
        const userEmailElements = document.querySelectorAll('[data-user-email]');
        userEmailElements.forEach(el => {
            el.textContent = user.email;
        });
        
        // Adicionar avatar se existir
        if (user.foto) {
            const avatarElements = document.querySelectorAll('[data-user-avatar]');
            avatarElements.forEach(el => {
                el.src = user.foto;
                el.style.display = 'block';
            });
        }
    })
    .catch(error => {
        console.log('Usuário não autenticado ou sessão expirada');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    });
}

// Verificar autenticação em cada página
function checkAuth() {
    const accessToken = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');
    
    if (!accessToken || !userData) {
        // Se estiver em uma página que requer autenticação, redirecionar
        const authRequiredPages = ['/perfil/', '/perfil/editar/', '/meus-favoritos/'];
        const currentPath = window.location.pathname;
        
        if (authRequiredPages.some(page => currentPath.startsWith(page))) {
            window.location.href = '/login/?next=' + encodeURIComponent(currentPath);
        }
    } else {
        // Verificar se o token ainda é válido
        fetch('/api/token/verify/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token: accessToken })
        })
        .then(response => {
            if (!response.ok) {
                // Tentar refresh
                return refreshToken();
            }
        })
        .catch(error => {
            console.log('Token inválido, redirecionando para login');
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            window.location.href = '/login/';
        });
    }
}

// Refresh token
function refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
        throw new Error('No refresh token');
    }
    
    return fetch('/api/token/refresh/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshToken })
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Refresh failed');
    })
    .then(data => {
        localStorage.setItem('access_token', data.access);
        return data.access;
    });
}

// Configurar interceptors para todas as requisições fetch
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    const accessToken = localStorage.getItem('access_token');
    
    // Adicionar token de autorização se existir
    if (accessToken && url.startsWith('/api/')) {
        if (!options.headers) {
            options.headers = {};
        }
        options.headers['Authorization'] = 'Bearer ' + accessToken;
    }
    
    return originalFetch.call(this, url, options)
        .then(response => {
            // Se receber 401 (Unauthorized), tentar refresh
            if (response.status === 401 && accessToken) {
                return refreshToken()
                    .then(newAccessToken => {
                        // Atualizar token no header e retentar
                        options.headers['Authorization'] = 'Bearer ' + newAccessToken;
                        return originalFetch.call(this, url, options);
                    })
                    .catch(error => {
                        // Se refresh falhar, limpar tokens e redirecionar
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        localStorage.removeItem('user');
                        window.location.href = '/login/';
                        throw error;
                    });
            }
            return response;
        });
};

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    // Carregar perfil do usuário
    loadUserProfile();
    
    // Verificar autenticação
    checkAuth();
    
    // Adicionar máscaras a inputs
    addInputMasks();
    
    // Configurar tooltips do Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Configurar popovers do Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Adicionar máscaras a inputs
function addInputMasks() {
    // Máscara para CPF
    const cpfInputs = document.querySelectorAll('input[data-mask="cpf"]');
    cpfInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 11) {
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
                e.target.value = value;
            }
        });
    });
    
    // Máscara para telefone
    const phoneInputs = document.querySelectorAll('input[data-mask="phone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 11) {
                value = value.replace(/(\d{2})(\d)/, '($1) $2');
                value = value.replace(/(\d{5})(\d)/, '$1-$2');
                e.target.value = value;
            }
        });
    });
    
    // Máscara para CEP
    const cepInputs = document.querySelectorAll('input[data-mask="cep"]');
    cepInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 8) {
                value = value.replace(/(\d{5})(\d)/, '$1-$2');
                e.target.value = value;
            }
        });
    });
    
    // Máscara para moeda
    const currencyInputs = document.querySelectorAll('input[data-mask="currency"]');
    currencyInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = (parseInt(value) / 100).toFixed(2);
            e.target.value = formatCurrency(value).replace('R$', '').trim();
        });
    });
}

// Função para fazer logout
function logout() {
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (refreshToken) {
        fetch('/api/usuarios/logout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + localStorage.getItem('access_token')
            },
            body: JSON.stringify({
                refresh: refreshToken
            })
        })
        .catch(error => {
            console.error('Erro ao fazer logout:', error);
        });
    }
    
    // Limpar localStorage e redirecionar
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('remember');
    
    window.location.href = '/';
}

// Função para upload de arquivos com preview
function setupFileUpload(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    
    if (!input || !preview) return;
    
    input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        // Validar tipo de arquivo
        const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            showToast('Tipo de arquivo inválido. Use JPG, PNG, GIF ou WebP.', 'error');
            input.value = '';
            return;
        }
        
        // Validar tamanho (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showToast('Arquivo muito grande. Máximo 5MB.', 'error');
            input.value = '';
            return;
        }
        
        // Mostrar preview
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    });
}

// Função para confirmar ações
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Exportar funções globais
window.utils = {
    formatCurrency,
    formatDate,
    validateEmail,
    validateCPF,
    validatePhone,
    validatePassword,
    showToast,
    logout,
    confirmAction
};