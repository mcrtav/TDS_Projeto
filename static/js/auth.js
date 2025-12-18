// Gerenciador de Autenticação
class AuthManager {
    constructor() {
        this.apiBase = '/api/usuarios/';
        this.cepCache = {}; // Cache para CEPs
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkLoginStatus();
    }

    bindEvents() {
        // Login
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Cadastro
        const cadastroForm = document.getElementById('cadastro-form');
        if (cadastroForm) {
            cadastroForm.addEventListener('submit', (e) => this.handleCadastro(e));
            
            // Auto-completar CEP - com debounce
            const cepInput = document.getElementById('cep');
            if (cepInput) {
                let timeout;
                cepInput.addEventListener('input', () => {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => this.buscarCEP(), 1000); // 1 segundo de delay
                });
            }
        }

        // Recuperação de senha
        const recuperarForm = document.getElementById('recuperar-form');
        if (recuperarForm) {
            recuperarForm.addEventListener('submit', (e) => this.handleRecuperarSenha(e));
        }

        // Reset de senha
        const resetForm = document.getElementById('reset-form');
        if (resetForm) {
            resetForm.addEventListener('submit', (e) => this.handleResetSenha(e));
        }
    }

    checkLoginStatus() {
        try {
            const token = localStorage.getItem('access_token');
            const userData = localStorage.getItem('user_data');
            
            if (token && userData) {
                const user = JSON.parse(userData);
                this.updateUIForLoggedUser(user);
            }
        } catch (error) {
            console.error('Erro ao verificar login:', error);
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const form = e.target;
        const email = form.querySelector('#email').value.trim();
        const password = form.querySelector('#password').value;
        const errorDiv = form.querySelector('#login-error');

        // Validação básica
        if (!email || !password) {
            this.showError(errorDiv, 'Preencha todos os campos');
            return;
        }

        // Desabilitar botão para evitar múltiplos cliques
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Entrando...';
        submitBtn.disabled = true;

        try {
            const response = await this.makeRequest('POST', `${this.apiBase}login/`, {
                email: email,
                password: password
            });
            
            this.handleLoginSuccess(response);
        } catch (error) {
            console.error('Erro no login:', error);
            const errorMsg = error.detalhes || 'Email ou senha inválidos';
            this.showError(errorDiv, errorMsg);
        } finally {
            // Reabilitar botão
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    // No AuthManager, adicione este método:
async syncWithDjangoSession(token) {
    try {
        const response = await fetch('/sync-session/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ token: token })
        });
        
        const data = await response.json();
        return data.success;
    } catch (error) {
        console.error('Erro ao sincronizar sessão:', error);
        return false;
    }
}

// Modifique o handleLoginSuccess para sincronizar:
async handleLoginSuccess(data) {
    try {
        // Salvar tokens no localStorage
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('user_data', JSON.stringify(data.usuario));
        
        // Sincronizar com sessão Django
        await this.syncWithDjangoSession(data.access);
        
        // Atualizar configuração do axios
        if (window.axios && window.axios.defaults) {
            window.axios.defaults.headers.common['Authorization'] = `Bearer ${data.access}`;
        }
        
        // Mostrar mensagem de sucesso
        this.showMessage('Login realizado com sucesso!', 'success');
        
        // Recarregar a página para atualizar a sessão Django
        setTimeout(() => {
            window.location.reload(); // Recarrega para atualizar o contexto Django
        }, 1000);
        
    } catch (error) {
        console.error('Erro ao processar login:', error);
        this.showMessage('Erro ao processar login. Tente novamente.', 'danger');
    }
}
    async handleLoginSuccess(data) {
    try {
        // Salvar tokens no localStorage
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('user_data', JSON.stringify(data.usuario));
        
        // Sincronizar com sessão Django
        await this.syncWithDjangoSession(data.access);
        
        // Atualizar configuração do axios
        if (window.axios && window.axios.defaults) {
            window.axios.defaults.headers.common['Authorization'] = `Bearer ${data.access}`;
        }
        
        // Mostrar mensagem de sucesso
        this.showMessage('Login realizado com sucesso!', 'success');
        
        // Recarregar a página para atualizar a sessão Django
        setTimeout(() => {
            window.location.reload(); // Recarrega para atualizar o contexto Django
        }, 1000);
        
    } catch (error) {
        console.error('Erro ao processar login:', error);
        this.showMessage('Erro ao processar login. Tente novamente.', 'danger');
    }
}
    async handleCadastro(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        const errorDiv = form.querySelector('#cadastro-error');
        
        // Validação de senha
        const password = formData.get('password');
        const passwordConfirmacao = formData.get('password_confirmacao');
        
        if (password !== passwordConfirmacao) {
            this.showError(errorDiv, 'As senhas não coincidem');
            return;
        }
        
        // Validar força da senha
        if (!this.validarSenhaForte(password)) {
            this.showError(errorDiv, 
                'Senha deve ter: 8+ caracteres, 1 maiúscula, 1 minúscula, 1 número e 1 caractere especial'
            );
            return;
        }

        // Validar termos
        const termos = form.querySelector('#termos');
        if (termos && !termos.checked) {
            this.showError(errorDiv, 'Você deve aceitar os termos de uso');
            return;
        }

        // Desabilitar botão
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Criando conta...';
        submitBtn.disabled = true;

        try {
            const response = await this.makeRequest('POST', `${this.apiBase}cadastro/`, formData, true);
            this.handleCadastroSuccess(response);
        } catch (error) {
            console.error('Erro no cadastro:', error);
            const errorMsg = error.detalhes || 'Erro ao criar conta';
            this.showError(errorDiv, errorMsg);
        } finally {
            // Reabilitar botão
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    handleCadastroSuccess(data) {
        try {
            // Salvar tokens
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            localStorage.setItem('user_data', JSON.stringify(data.usuario));
            
            // Mostrar mensagem
            this.showMessage('Cadastro realizado com sucesso!', 'success');
            
            // Redirecionar
            setTimeout(() => {
                if (window.location.protocol === 'https:' || window.location.protocol === 'http:') {
                    window.location.href = '/';
                } else {
                    const baseUrl = window.location.origin || 'http://localhost:8000';
                    window.location.href = `${baseUrl}/`;
                }
            }, 1500);
            
        } catch (error) {
            console.error('Erro ao processar cadastro:', error);
            this.showMessage('Erro ao processar cadastro. Tente novamente.', 'danger');
        }
    }

    async buscarCEP() {
        const cepInput = document.getElementById('cep');
        if (!cepInput) return;
        
        const cep = cepInput.value.replace(/\D/g, '');
        
        if (cep.length !== 8) {
            return;
        }

        // Verificar cache
        if (this.cepCache[cep]) {
            this.preencherEndereco(this.cepCache[cep]);
            return;
        }

        try {
            // Adicionar delay para evitar muitas requisições
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const response = await fetch(`https://brasilapi.com.br/api/cep/v2/${cep}`, {
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('CEP não encontrado');
            }
            
            const data = await response.json();
            
            // Salvar no cache
            this.cepCache[cep] = data;
            
            // Preencher campos
            this.preencherEndereco(data);
            
        } catch (error) {
            console.warn('CEP não encontrado ou erro na API:', error);
            // Não mostrar alerta para não irritar o usuário
        }
    }

    preencherEndereco(data) {
        this.preencherCampo('logradouro', data.street);
        this.preencherCampo('bairro', data.neighborhood);
        this.preencherCampo('cidade', data.city);
        this.preencherCampo('estado', data.state);
    }

    preencherCampo(id, value) {
        const campo = document.getElementById(id);
        if (campo && !campo.value && value) {
            campo.value = value;
        }
    }

    validarSenhaForte(senha) {
        const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$/;
        return regex.test(senha);
    }

    async handleRecuperarSenha(e) {
        e.preventDefault();
        
        const form = e.target;
        const email = form.querySelector('#email').value.trim();
        const errorDiv = form.querySelector('#recuperar-error');
        const successDiv = form.querySelector('#recuperar-success');

        if (!email) {
            this.showError(errorDiv, 'Informe seu email');
            return;
        }

        // Desabilitar botão
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Enviando...';
        submitBtn.disabled = true;

        try {
            await this.makeRequest('POST', `${this.apiBase}reset-password/`, { email: email });
            
            this.showSuccess(successDiv, 'Email de recuperação enviado com sucesso!');
            form.reset();
            
        } catch (error) {
            console.error('Erro na recuperação:', error);
            this.showError(errorDiv, 'Erro ao enviar email de recuperação');
        } finally {
            // Reabilitar botão
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    async handleResetSenha(e) {
        e.preventDefault();
        
        const form = e.target;
        const novaSenha = form.querySelector('#nova_senha').value;
        const novaSenhaConfirmacao = form.querySelector('#nova_senha_confirmacao').value;
        const errorDiv = form.querySelector('#reset-error');
        
        // Pegar uid e token da URL
        const pathParts = window.location.pathname.split('/');
        const uid = pathParts[pathParts.length - 3];
        const token = pathParts[pathParts.length - 2];

        if (novaSenha !== novaSenhaConfirmacao) {
            this.showError(errorDiv, 'As senhas não coincidem');
            return;
        }
        
        if (!this.validarSenhaForte(novaSenha)) {
            this.showError(errorDiv, 
                'Senha deve ter: 8+ caracteres, 1 maiúscula, 1 minúscula, 1 número e 1 caractere especial'
            );
            return;
        }

        // Desabilitar botão
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Redefinindo...';
        submitBtn.disabled = true;

        try {
            await this.makeRequest('POST', `${this.apiBase}confirm-reset-password/`, {
                uid: uid,
                token: token,
                nova_senha: novaSenha,
                nova_senha_confirmacao: novaSenhaConfirmacao
            });
            
            this.showMessage('Senha redefinida com sucesso!', 'success');
            
            setTimeout(() => {
                if (window.location.protocol === 'https:' || window.location.protocol === 'http:') {
                    window.location.href = '/login';
                } else {
                    const baseUrl = window.location.origin || 'http://localhost:8000';
                    window.location.href = `${baseUrl}/login`;
                }
            }, 2000);
            
        } catch (error) {
            console.error('Erro ao resetar senha:', error);
            const errorMsg = error.erro || 'Erro ao redefinir senha';
            this.showError(errorDiv, errorMsg);
        } finally {
            // Reabilitar botão
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    updateUIForLoggedUser(user) {
        // Atualizar nome na navbar
        const userNameElement = document.getElementById('user-name');
        if (userNameElement && user.nome) {
            userNameElement.textContent = user.nome;
        }
    }

    // Método genérico para fazer requisições
    async makeRequest(method, url, data = null, isFormData = false) {
        const config = {
            method: method,
            headers: {}
        };

        // Adicionar token se disponível
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        // Adicionar CSRF token para Django
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
            config.headers['X-CSRFToken'] = csrfToken;
        }

        // Adicionar dados
        if (data) {
            if (isFormData) {
                config.body = data;
                // Não definir Content-Type para FormData - o navegador faz isso
            } else {
                config.headers['Content-Type'] = 'application/json';
                config.body = JSON.stringify(data);
            }
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw {
                    status: response.status,
                    ...errorData
                };
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erro na requisição:', error);
            throw error;
        }
    }

    getCSRFToken() {
        // Tentar pegar o token CSRF do cookie
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    showError(element, message) {
        if (element) {
            element.textContent = message;
            element.style.display = 'block';
            
            // Auto-esconder após 5 segundos
            setTimeout(() => {
                element.style.display = 'none';
            }, 5000);
        }
        
        // Também mostrar no console para debug
        console.error('Erro:', message);
    }

    showSuccess(element, message) {
        if (element) {
            element.textContent = message;
            element.style.display = 'block';
            
            setTimeout(() => {
                element.style.display = 'none';
            }, 5000);
        }
    }

    showMessage(message, type = 'info') {
        // Usar alerta global se disponível
        if (window.app && window.app.showAlert) {
            window.app.showAlert(message, type);
        } else {
            // Criar alerta temporário
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            alertDiv.style.cssText = `
                top: 20px;
                right: 20px;
                z-index: 9999;
                min-width: 300px;
                max-width: 500px;
            `;
            
            const icon = type === 'success' ? 'check-circle' :
                        type === 'danger' ? 'exclamation-circle' :
                        type === 'warning' ? 'exclamation-triangle' : 'info-circle';
            
            alertDiv.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="fas fa-${icon} me-2"></i>
                    <div class="flex-grow-1">${message}</div>
                    <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
                </div>
            `;
            
            document.body.appendChild(alertDiv);

            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
}

// Inicializar gerenciador de autenticação de forma segura
document.addEventListener('DOMContentLoaded', () => {
    try {
        // Verificar se estamos em um contexto seguro (http/https)
        if (window.location.protocol === 'http:' || 
            window.location.protocol === 'https:' || 
            window.location.hostname === 'localhost' ||
            window.location.hostname === '127.0.0.1') {
            
            window.authManager = new AuthManager();
        } else {
            console.warn('Contexto de segurança não suportado para authManager');
        }
    } catch (error) {
        console.error('Erro ao inicializar authManager:', error);
    }
});