// // static/js/cep.js
// class CepHandler {
//     constructor() {
//         this.cepInput = document.getElementById('id_cep');
//         this.logradouroInput = document.getElementById('id_logradouro');
//         this.bairroInput = document.getElementById('id_bairro');
//         this.cidadeInput = document.getElementById('id_cidade');
//         this.estadoInput = document.getElementById('id_estado');
        
//         if (this.cepInput) {
//             this.inicializar();
//         }
//     }

//     inicializar() {
//         // Configura o evento de blur (quando sai do campo)
//         this.cepInput.addEventListener('blur', (e) => this.buscarCEP(e.target.value));
        
//         // Configura o botão de buscar CEP se existir
//         const buscarBtn = document.getElementById('buscar-cep-btn');
//         if (buscarBtn) {
//             buscarBtn.addEventListener('click', () => this.buscarCEP(this.cepInput.value));
//         }
//     }

//     validarFormatoCEP(cep) {
//         // Remove qualquer caractere não numérico
//         cep = cep.replace(/\D/g, '');
        
//         // Verifica se tem 8 dígitos
//         if (cep.length !== 8) {
//             return false;
//         }
        
//         // Formato válido: 12345-678
//         this.cepInput.value = cep.replace(/^(\d{5})(\d{3})$/, '$1-$2');
//         return true;
//     }

//     async buscarCEP(cep) {
//         // Limpa campos primeiro
//         this.limparCampos();
        
//         // Valida formato
//         if (!this.validarFormatoCEP(cep)) {
//             this.mostrarErro('CEP inválido. Formato correto: 12345-678');
//             return;
//         }

//         // Remove hífen para a busca
//         cep = cep.replace('-', '');
        
//         // Mostra loading
//         this.mostrarLoading(true);

//         try {
//             // Busca na API ViaCEP
//             const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
            
//             if (!response.ok) {
//                 throw new Error('Erro na requisição');
//             }
            
//             const data = await response.json();
            
//             if (data.erro) {
//                 throw new Error('CEP não encontrado');
//             }
            
//             // Preenche os campos
//             this.preencherEnderecoPorCEP(data);
            
//         } catch (error) {
//             console.error('Erro ao buscar CEP:', error);
//             this.mostrarErro(error.message || 'Erro ao buscar CEP. Verifique o número digitado.');
//         } finally {
//             this.mostrarLoading(false);
//         }
//     }

//     preencherEnderecoPorCEP(data) {
//         if (this.logradouroInput) this.logradouroInput.value = data.logradouro || '';
//         if (this.bairroInput) this.bairroInput.value = data.bairro || '';
//         if (this.cidadeInput) this.cidadeInput.value = data.localidade || '';
//         if (this.estadoInput) this.estadoInput.value = data.uf || '';
        
//         // Foca no próximo campo (número) se logradouro foi preenchido
//         if (data.logradouro && this.logradouroInput.value) {
//             const numeroInput = document.getElementById('id_numero');
//             if (numeroInput) {
//                 numeroInput.focus();
//             }
//         }
//     }

//     limparCampos() {
//         if (this.logradouroInput) this.logradouroInput.value = '';
//         if (this.bairroInput) this.bairroInput.value = '';
//         if (this.cidadeInput) this.cidadeInput.value = '';
//         if (this.estadoInput) this.estadoInput.value = '';
//     }

//     mostrarErro(mensagem) {
//         // Remove erros anteriores
//         this.removerErro();
        
//         // Cria elemento de erro
//         const erroDiv = document.createElement('div');
//         erroDiv.className = 'alert alert-danger mt-2';
//         erroDiv.id = 'cep-erro';
//         erroDiv.textContent = mensagem;
        
//         // Insere após o campo CEP
//         this.cepInput.parentNode.appendChild(erroDiv);
        
//         // Adiciona classe de erro ao input
//         this.cepInput.classList.add('is-invalid');
//     }

//     removerErro() {
//         // Remove mensagem de erro anterior
//         const erroAntigo = document.getElementById('cep-erro');
//         if (erroAntigo) {
//             erroAntigo.remove();
//         }
        
//         // Remove classe de erro
//         this.cepInput.classList.remove('is-invalid');
//     }

//     mostrarLoading(mostrar) {
//         // Remove loading anterior
//         this.removerLoading();
        
//         if (mostrar) {
//             // Cria elemento de loading
//             const loadingDiv = document.createElement('div');
//             loadingDiv.className = 'spinner-border spinner-border-sm text-primary ms-2';
//             loadingDiv.id = 'cep-loading';
//             loadingDiv.setAttribute('role', 'status');
            
//             const loadingSpan = document.createElement('span');
//             loadingSpan.className = 'visually-hidden';
//             loadingSpan.textContent = 'Carregando...';
            
//             loadingDiv.appendChild(loadingSpan);
            
//             // Insere após o campo CEP
//             this.cepInput.parentNode.appendChild(loadingDiv);
//         }
//     }

//     removerLoading() {
//         const loading = document.getElementById('cep-loading');
//         if (loading) {
//             loading.remove();
//         }
//     }
// }

// // Função global para ser chamada pelo onclick (se necessário)
// function buscarCep() {
//     const cepInput = document.getElementById('id_cep');
//     if (cepInput) {
//         const handler = new CepHandler();
//         handler.buscarCEP(cepInput.value);
//     }
// }

// // Inicializa automaticamente quando o DOM carrega
// document.addEventListener('DOMContentLoaded', function() {
//     new CepHandler();
// });

// // Exporta para uso global
// window.buscarCep = buscarCep;
// window.CepHandler = CepHandler;
// static/js/cep.js
/**
 * Sistema de busca de CEP com ViaCEP API
 * Versão completa com validação e tratamento de erros
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Sistema de CEP inicializado');
    
    // Inicializa o manipulador de CEP
    const cepHandler = new CepHandler();
    cepHandler.inicializar();
});

class CepHandler {
    constructor() {
        this.cepInput = document.getElementById('id_cep');
        this.logradouroInput = document.getElementById('id_logradouro');
        this.bairroInput = document.getElementById('id_bairro');
        this.cidadeInput = document.getElementById('id_cidade');
        this.estadoInput = document.getElementById('id_estado');
        this.numeroInput = document.getElementById('id_numero');
        this.complementoInput = document.getElementById('id_complemento');
        
        this.buscarBtn = document.getElementById('buscar-cep-btn');
        this.formulario = document.querySelector('form');
    }

    inicializar() {
        if (!this.cepInput) {
            console.warn('Campo CEP não encontrado');
            return;
        }

        console.log('Configurando eventos do CEP...');

        // Configura evento de blur no campo CEP
        this.cepInput.addEventListener('blur', (e) => {
            this.handleCepBlur(e);
        });

        // Configura evento de input para formatação automática
        this.cepInput.addEventListener('input', (e) => {
            this.formatarCEP(e);
        });

        // Configura botão de buscar (se existir)
        if (this.buscarBtn) {
            this.buscarBtn.addEventListener('click', () => {
                this.buscarCEP(this.cepInput.value);
            });
        }

        // Configura submissão do formulário para validar CEP
        if (this.formulario) {
            this.formulario.addEventListener('submit', (e) => {
                if (!this.validarCEPFormato(this.cepInput.value)) {
                    e.preventDefault();
                    this.mostrarErro('CEP inválido. Formato: 12345-678');
                    this.cepInput.focus();
                }
            });
        }

        // Adiciona máscara ao campo CEP
        this.adicionarMascaraCEP();
    }

    handleCepBlur(event) {
        const cep = event.target.value.trim();
        
        if (cep.length === 0) {
            return;
        }

        if (this.validarCEPFormato(cep)) {
            this.buscarCEP(cep);
        } else {
            this.mostrarErro('Formato de CEP inválido. Use: 12345-678');
        }
    }

    formatarCEP(event) {
        let cep = event.target.value.replace(/\D/g, '');
        
        if (cep.length > 5) {
            cep = cep.replace(/^(\d{5})(\d)/, '$1-$2');
        }
        
        if (cep.length > 9) {
            cep = cep.substring(0, 9);
        }
        
        event.target.value = cep;
    }

    adicionarMascaraCEP() {
        // Adiciona máscara visual
        this.cepInput.placeholder = '00000-000';
        this.cepInput.maxLength = 9;
        
        // Adiciona classe CSS para estilização
        this.cepInput.classList.add('cep-input');
    }

    validarCEPFormato(cep) {
        if (!cep) return false;
        
        // Remove qualquer caractere não numérico
        const cepNumerico = cep.replace(/\D/g, '');
        
        // Verifica se tem 8 dígitos
        if (cepNumerico.length !== 8) {
            return false;
        }
        
        // Verifica formato com ou sem hífen
        const regex = /^\d{5}-?\d{3}$/;
        return regex.test(cep);
    }

    async buscarCEP(cep) {
        console.log(`Buscando CEP: ${cep}`);
        
        // Valida formato
        if (!this.validarCEPFormato(cep)) {
            this.mostrarErro('CEP inválido. Formato correto: 12345-678');
            return;
        }

        // Remove hífen para a busca
        const cepNumerico = cep.replace('-', '');
        
        // Mostra estado de carregamento
        this.mostrarCarregamento(true);
        
        // Limpa erros anteriores
        this.limparErros();

        try {
            console.log(`Fazendo requisição para ViaCEP: ${cepNumerico}`);
            
            // Faz a requisição à API ViaCEP
            const response = await fetch(`https://viacep.com.br/ws/${cepNumerico}/json/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                },
                timeout: 10000 // 10 segundos timeout
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Resposta da API:', data);

            if (data.erro) {
                throw new Error('CEP não encontrado na base de dados');
            }

            // Preenche os campos com os dados retornados
            this.preencherEndereco(data);
            
            // Remove qualquer erro
            this.limparErros();
            
            // Adiciona sucesso visual
            this.mostrarSucesso('CEP encontrado com sucesso!');

        } catch (error) {
            console.error('Erro ao buscar CEP:', error);
            this.mostrarErro(`Erro: ${error.message}`);
        } finally {
            this.mostrarCarregamento(false);
        }
    }

    preencherEndereco(data) {
        console.log('Preenchendo endereço com dados:', data);
        
        // Preenche os campos se existirem
        if (this.logradouroInput) {
            this.logradouroInput.value = data.logradouro || '';
            this.logradouroInput.classList.add('preenchido-auto');
        }
        
        if (this.bairroInput) {
            this.bairroInput.value = data.bairro || '';
            this.bairroInput.classList.add('preenchido-auto');
        }
        
        if (this.cidadeInput) {
            this.cidadeInput.value = data.localidade || '';
            this.cidadeInput.classList.add('preenchido-auto');
        }
        
        if (this.estadoInput) {
            this.estadoInput.value = data.uf || '';
            this.estadoInput.classList.add('preenchido-auto');
        }
        
        // Foca no campo número automaticamente
        if (this.numeroInput && data.logradouro) {
            setTimeout(() => {
                this.numeroInput.focus();
            }, 100);
        }
    }

    mostrarCarregamento(mostrar) {
        // Remove loading anterior
        const loadingAntigo = document.getElementById('cep-loading');
        if (loadingAntigo) {
            loadingAntigo.remove();
        }

        if (mostrar) {
            // Cria elemento de loading
            const loadingDiv = document.createElement('div');
            loadingDiv.id = 'cep-loading';
            loadingDiv.className = 'cep-loading';
            loadingDiv.innerHTML = `
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Buscando CEP...</span>
                </div>
                <span class="cep-loading-text">Buscando CEP...</span>
            `;
            
            // Insere após o campo CEP
            this.cepInput.parentNode.appendChild(loadingDiv);
        }
    }

    mostrarErro(mensagem) {
        // Remove erros anteriores
        this.limparErros();
        
        // Adiciona classe de erro ao input
        this.cepInput.classList.add('is-invalid');
        this.cepInput.classList.remove('is-valid');
        
        // Cria elemento de erro
        const erroDiv = document.createElement('div');
        erroDiv.id = 'cep-error';
        erroDiv.className = 'invalid-feedback cep-error';
        erroDiv.textContent = mensagem;
        
        // Insere após o campo CEP
        this.cepInput.parentNode.appendChild(erroDiv);
    }

    mostrarSucesso(mensagem) {
        // Remove mensagens anteriores
        this.limparErros();
        
        // Adiciona classe de sucesso ao input
        this.cepInput.classList.add('is-valid');
        this.cepInput.classList.remove('is-invalid');
        
        // Cria elemento de sucesso (opcional)
        const sucessoDiv = document.createElement('div');
        sucessoDiv.id = 'cep-success';
        sucessoDiv.className = 'valid-feedback cep-success';
        sucessoDiv.textContent = mensagem;
        
        // Insere após o campo CEP
        this.cepInput.parentNode.appendChild(sucessoDiv);
        
        // Remove após 3 segundos
        setTimeout(() => {
            if (sucessoDiv.parentNode) {
                sucessoDiv.remove();
                this.cepInput.classList.remove('is-valid');
            }
        }, 3000);
    }

    limparErros() {
        // Remove elementos de erro/sucesso
        const errorElement = document.getElementById('cep-error');
        if (errorElement) errorElement.remove();
        
        const successElement = document.getElementById('cep-success');
        if (successElement) successElement.remove();
        
        const loadingElement = document.getElementById('cep-loading');
        if (loadingElement) loadingElement.remove();
        
        // Remove classes de validação
        this.cepInput.classList.remove('is-invalid', 'is-valid');
    }

    limparCamposEndereco() {
        const campos = [
            this.logradouroInput,
            this.bairroInput,
            this.cidadeInput,
            this.estadoInput
        ];
        
        campos.forEach(campo => {
            if (campo) {
                campo.value = '';
                campo.classList.remove('preenchido-auto');
            }
        });
    }
}

// Função global para uso externo (se necessário)
window.buscarCEPGlobal = function(cep) {
    const handler = new CepHandler();
    return handler.buscarCEP(cep);
};

// Exporta a classe para uso em outros módulos
window.CepHandler = CepHandler;