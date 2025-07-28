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
                    if (data.needs_caixa) {
                        showAberturaCaixaModal(data.valor_sugerido);
                    } else {
                        // Redireciona conforme o tipo de usuário
                        window.location.href = data.user_type === 'admin' 
                            ? '/admin/dashboard' 
                            : '/operador/dashboard';
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
        <div id="caixa-modal" class="modal">
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
                    </div>
                    
                    <div class="form-group">
                        <label for="observacao">Observação:</label>
                        <input type="text" class="form-control" id="observacao" 
                               value="Abertura manual">
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
    
    // Foca no campo de valor
    document.getElementById('valor-abertura')?.focus();
    
    // Eventos do modal
    document.querySelector('.close-modal')?.addEventListener('click', closeModal);
    document.getElementById('cancelar-abertura')?.addEventListener('click', closeModal);
    document.getElementById('confirmar-abertura')?.addEventListener('click', confirmarAbertura);
}

function closeModal() {
    const modal = document.getElementById('caixa-modal');
    if (modal) modal.remove();
}

async function confirmarAbertura() {
    const valorInput = document.getElementById('valor-abertura');
    const observacaoInput = document.getElementById('observacao');
    const messageDiv = document.getElementById('caixa-message');
    const button = document.getElementById('confirmar-abertura');
    
    const valor = parseFloat(valorInput.value);
    const observacao = observacaoInput.value.trim();
    
    if (isNaN(valor) || valor < 0) {
        showMessage(messageDiv, 'Por favor, insira um valor válido para abertura.', 'error');
        valorInput.focus();
        return;
    }
    
    button.disabled = true;
    button.textContent = 'Abrindo...';
    
    try {
        const response = await fetch('/abrir-caixa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                valor_abertura: valor,
                observacao: observacao
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(messageDiv, data.message, 'success');
            setTimeout(() => {
                window.location.href = data.redirect_url || '/operador/dashboard';
            }, 1500);
        } else {
            showMessage(messageDiv, data.message, 'error');
        }
    } catch (error) {
        console.error('Abertura de caixa error:', error);
        showMessage(messageDiv, 'Erro ao conectar com o servidor', 'error');
    } finally {
        button.disabled = false;
        button.textContent = 'Abrir Caixa';
    }
}

// Funções auxiliares
function showFlashMessage(text, type, container) {
    if (!container) return;
    
    const message = document.createElement('div');
    message.className = `flash-message flash-${type}`;
    message.textContent = text;
    
    // Adiciona botão de fechar
    const closeBtn = document.createElement('span');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.marginLeft = '15px';
    closeBtn.style.cursor = 'pointer';
    closeBtn.onclick = () => message.remove();
    
    message.appendChild(closeBtn);
    container.appendChild(message);
    
    setTimeout(() => {
        message.style.animation = 'fadeOut 0.5s forwards';
        message.addEventListener('animationend', () => message.remove());
    }, 5000);
}

function showMessage(element, text, type) {
    if (!element) return;
    
    element.innerHTML = `
        <div class="flash-message flash-${type}">
            ${text}
        </div>
    `;
    
    setTimeout(() => {
        element.innerHTML = '';
    }, 5000);
}