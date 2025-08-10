document.addEventListener('DOMContentLoaded', function() {
    // Fallback para logo
    const logoImage = document.getElementById('logo-image');
    if (logoImage) {
        logoImage.onerror = function() {
            this.style.display = 'none';
            const logoText = document.getElementById('logo-text');
            if (logoText) logoText.style.display = 'block';
        };
    }

    // Formulário de login
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const cpf = document.getElementById('cpf').value.trim();
            const senha = document.getElementById('senha').value.trim();
            const button = document.getElementById('login-button');
            const flashContainer = document.getElementById('flash-messages');
            
            // Validação básica
            if (!cpf || !senha) {
                showFlashMessage('Preencha CPF e senha corretamente.', 'error', flashContainer);
                return;
            }

            button.disabled = true;
            button.textContent = 'Autenticando...';
            
            try {
                const response = await fetch('/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: `cpf=${encodeURIComponent(cpf)}&senha=${encodeURIComponent(senha)}`
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Verifica se precisa abrir caixa
                    if (data.needs_caixa) {
                        // Se é primeiro login, mostra modal de abertura manual
                        if (data.primeiro_login) {
                            showAberturaCaixaModal(data.valor_sugerido || 0);
                        } else {
                            // Se houve erro na abertura automática, mostra modal com mensagem
                            if (data.erro_abertura_automatica) {
                                showFlashMessage(data.message, 'warning', flashContainer);
                                showAberturaCaixaModal(data.valor_sugerido || 0);
                            }
                        }
                    } else {
                        // Se foi abertura automática, mostra mensagem de sucesso
                        if (data.abertura_automatica) {
                            showFlashMessage(data.message, 'success', flashContainer);
                        }
                        
                        // Aguarda um momento para mostrar a mensagem e redireciona
                        setTimeout(() => {
                            window.location.href = data.user_type === 'admin' 
                                ? '/admin/dashboard' 
                                : '/operador/dashboard';
                        }, data.abertura_automatica ? 2000 : 500);
                    }
                } else {
                    showFlashMessage(data.message || 'Erro ao autenticar', 'error', flashContainer);
                }
            } catch (error) {
                console.error('Login error:', error);
                showFlashMessage('Erro ao conectar com o servidor', 'error', flashContainer);
            } finally {
                button.disabled = false;
                button.textContent = 'Entrar';
            }
        });
    }
});

function showAberturaCaixaModal(valorSugerido = 0) {
    // Remove modal existente se houver
    const existingModal = document.getElementById('caixa-modal');
    if (existingModal) existingModal.remove();
    
    // Cria o modal
    const modalHTML = `
        <div id="caixa-modal" class="modal" style="display: block;">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Abertura de Caixa</h3>
                    <span class="close-modal">&times;</span>
                </div>
                <div class="modal-body">
                    <p>É necessário abrir o caixa antes de continuar.</p>
                    
                    <div class="form-group">
                        <label for="valor-abertura">Valor de Abertura (R$):</label>
                        <input type="number" class="form-control" id="valor-abertura" 
                               value="${valorSugerido.toFixed(2)}" step="0.01" min="0" required>
                        <small class="form-text text-muted">
                            ${valorSugerido > 0 ? 'Valor sugerido baseado no último fechamento' : 'Informe o valor inicial do caixa'}
                        </small>
                    </div>
                    
                    <div class="form-group">
                        <label for="observacao">Observação:</label>
                        <input type="text" class="form-control" id="observacao" 
                               value="Abertura manual" placeholder="Observação (opcional)">
                    </div>
                </div>
                <div class="modal-footer">
                    <button id="cancelar-abertura" class="btn btn-secondary">Cancelar</button>
                    <button id="confirmar-abertura" class="btn btn-primary">Abrir Caixa</button>
                </div>
                <div id="caixa-message" style="padding: 0 20px 20px;"></div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Foca no campo de valor após um breve delay para garantir que o modal foi renderizado
    setTimeout(() => {
        const valorInput = document.getElementById('valor-abertura');
        if (valorInput) {
            valorInput.focus();
            valorInput.select(); // Seleciona o valor atual para facilitar a edição
        }
    }, 100);
    
    // Eventos do modal
    document.querySelector('#caixa-modal .close-modal')?.addEventListener('click', closeModal);
    document.getElementById('cancelar-abertura')?.addEventListener('click', closeModal);
    document.getElementById('confirmar-abertura')?.addEventListener('click', confirmarAbertura);
    
    // Permite fechar o modal clicando fora dele
    document.getElementById('caixa-modal')?.addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
    
    // Permite confirmar com Enter no campo de valor
    document.getElementById('valor-abertura')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            confirmarAbertura();
        }
    });
}

function closeModal() {
    const modal = document.getElementById('caixa-modal');
    if (modal) {
        modal.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => modal.remove(), 300);
    }
    
    // Volta para a tela de login
    window.location.href = '/';
}

async function confirmarAbertura() {
    const valorInput = document.getElementById('valor-abertura');
    const observacaoInput = document.getElementById('observacao');
    const messageDiv = document.getElementById('caixa-message');
    const button = document.getElementById('confirmar-abertura');
    const cancelButton = document.getElementById('cancelar-abertura');
    
    const valor = parseFloat(valorInput?.value || 0);
    const observacao = observacaoInput?.value?.trim() || 'Abertura manual';
    
    // Validação
    if (isNaN(valor) || valor < 0) {
        showMessage(messageDiv, 'Por favor, insira um valor válido para abertura (maior ou igual a zero).', 'error');
        valorInput?.focus();
        return;
    }
    
    // Desabilita botões durante o processo
    button.disabled = true;
    cancelButton.disabled = true;
    button.textContent = 'Abrindo Caixa...';
    
    try {
        const response = await fetch('/abrir-caixa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                valor_abertura: valor,
                observacao: observacao
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // Se for erro 400 e já existir caixa aberto, redireciona para o dashboard
            if (response.status === 400 && data.caixa_id && data.redirect_url) {
                showMessage(messageDiv, data.message, 'info');
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 2000);
                return;
            }
            
            // Para outros tipos de erro
            throw new Error(data.message || `Erro HTTP ${response.status}`);
        }
        
        if (data.success) {
            showMessage(messageDiv, data.message || 'Caixa aberto com sucesso!', 'success');
            
            // Aguarda um momento e redireciona
            setTimeout(() => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    // Fallback para dashboard do operador
                    window.location.href = '/operador/dashboard';
                }
            }, 2000);
        } else {
            showMessage(messageDiv, data.message || 'Erro ao abrir caixa', 'error');
            button.disabled = false;
            cancelButton.disabled = false;
            button.textContent = 'Abrir Caixa';
        }
    } catch (error) {
        console.error('Erro na abertura de caixa:', error);
        showMessage(messageDiv, error.message || 'Erro ao conectar com o servidor', 'error');
        button.disabled = false;
        cancelButton.disabled = false;
        button.textContent = 'Abrir Caixa';
    }
}

// Função auxiliar para pegar cookies (caso necessário)
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

// Funções auxiliares para mensagens
function showFlashMessage(text, type, container) {
    if (!container) {
        console.warn('Container para flash message não encontrado');
        return;
    }
    
    // Remove mensagens antigas do mesmo tipo
    const existingMessages = container.querySelectorAll(`.flash-${type}`);
    existingMessages.forEach(msg => msg.remove());
    
    const message = document.createElement('div');
    message.className = `flash-message flash-${type}`;
    message.innerHTML = `
        <span class="flash-text">${text}</span>
        <span class="flash-close" onclick="this.parentElement.remove()">&times;</span>
    `;
    
    container.appendChild(message);
    
    // Auto remove após 5 segundos (exceto para mensagens de erro)
    if (type !== 'error') {
        setTimeout(() => {
            if (message.parentNode) {
                message.style.animation = 'fadeOut 0.5s forwards';
                message.addEventListener('animationend', () => {
                    if (message.parentNode) message.remove();
                });
            }
        }, 5000);
    }
}

function showMessage(element, text, type) {
    if (!element) {
        console.warn('Elemento para mensagem não encontrado');
        return;
    }
    
    element.innerHTML = `
        <div class="flash-message flash-${type}" style="margin-top: 15px;">
            ${text}
        </div>
    `;
    
    // Auto limpa mensagens de sucesso e info
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            if (element) element.innerHTML = '';
        }, 5000);
    }
}

// Adiciona estilos CSS para o modal e animações se não existirem
if (!document.getElementById('login-modal-styles')) {
    const styles = document.createElement('style');
    styles.id = 'login-modal-styles';
    styles.textContent = `
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(0, 0, 0, 0.6);
            z-index: 9999;
            display: flex !important;
            justify-content: center;
            align-items: center;
            animation: fadeIn 0.3s ease-out;
        }
        
        .modal-content {
            background: white;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            max-width: 500px;
            width: 90%;
            max-height: 85vh;
            overflow-y: auto;
            animation: slideIn 0.3s ease-out;
            position: relative;
            margin: 20px;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid #eee;
        }
        
        .modal-header h3 {
            margin: 0;
            color: #333;
        }
        
        .close-modal {
            font-size: 24px;
            cursor: pointer;
            color: #999;
            line-height: 1;
        }
        
        .close-modal:hover {
            color: #333;
        }
        
        .modal-body {
            padding: 20px;
        }
        
        .modal-footer {
            padding: 15px 20px;
            border-top: 1px solid #eee;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #333;
        }
        
        .form-control {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
        }
        
        .form-control:focus {
            border-color: #007bff;
            outline: none;
            box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
        }
        
        .form-text {
            font-size: 12px;
            margin-top: 5px;
            display: block;
        }
        
        .text-muted {
            color: #666;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }
        
        .btn-primary {
            background-color: #007bff;
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            background-color: #0056b3;
        }
        
        .btn-secondary {
            background-color: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover:not(:disabled) {
            background-color: #545b62;
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .flash-message {
            padding: 10px 15px;
            border-radius: 4px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .flash-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .flash-error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .flash-warning {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .flash-info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .flash-close {
            cursor: pointer;
            font-size: 18px;
            line-height: 1;
            margin-left: 10px;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        
        @keyframes slideIn {
            from { 
                transform: translateY(-30px) scale(0.95); 
                opacity: 0; 
            }
            to { 
                transform: translateY(0) scale(1); 
                opacity: 1; 
            }
        }
    `;
    document.head.appendChild(styles);
}