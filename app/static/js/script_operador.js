// Variáveis globais
let balanceVisible = true;
let currentBalance = 0;
let clients = [];
let products = [];
let currentEditingClient = null;

// DOM Elements
const openingBalanceLabel = document.getElementById('opening-balance');
const currentBalanceLabel = document.getElementById('current-balance');
const currentDateElement = document.getElementById('current-date');
const balanceLabel = document.getElementById('balance-label');
const toggleBalanceBtn = document.getElementById('toggle-balance');
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const productsContainer = document.getElementById('products-container');
const clientsContainer = document.getElementById('clients-container');
const clientSelect = document.getElementById('client-select');
const newClientBtn = document.getElementById('new-client-btn');
const addClientBtn = document.getElementById('add-client-btn');
const addProductBtn = document.getElementById('add-product-btn');
const registerSaleBtn = document.getElementById('register-sale-btn');
const closeRegisterBtn = document.getElementById('close-register-btn');
const clientModal = document.getElementById('client-modal');
const clientModalTitle = document.getElementById('client-modal-title');
const clientForm = document.getElementById('client-form');
const modalCloses = document.querySelectorAll('.modal-close, #cancel-client');
const saleTotalElement = document.getElementById('sale-total');
const amountReceivedInput = document.getElementById('amount-received');
const logoutBtn = document.getElementById('logout-btn');
const notification = document.getElementById('notification');
const notificationMessage = document.getElementById('notification-message');
const clientSearch = document.getElementById('client-search');
const searchClientBtn = document.getElementById('search-client-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateCurrentDate();
    loadClients();
    loadProducts();
    checkCaixaStatus();
    setupEventListeners();

    // Atualiza produtos a cada 10 segundos para refletir mudanças do servidor
    setInterval(loadProducts, 10000);
});

function setupEventListeners() {
    toggleBalanceBtn.addEventListener('click', toggleBalance);
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    newClientBtn.addEventListener('click', () => openClientModal());
    addClientBtn.addEventListener('click', () => openClientModal());
    addProductBtn.addEventListener('click', addProductRow);
    
    modalCloses.forEach(btn => {
        btn.addEventListener('click', closeModal);
    });
    
    document.getElementById('save-client').addEventListener('click', saveClient);
    registerSaleBtn.addEventListener('click', registerSale);
    closeRegisterBtn.addEventListener('click', closeRegister);

    logoutBtn.addEventListener('click', () => {
        window.location.href = '/logout';
    });
    
    searchClientBtn.addEventListener('click', searchClients);
    clientSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchClients();
    });
    
    // Listeners para produtos
    document.addEventListener('input', handleQuantityInput);
    document.addEventListener('click', handleRemoveClick);
    document.addEventListener('change', handleProductSelectChange);
    document.addEventListener('click', handleEditClientClick);
}

async function checkCaixaStatus() {
    try {
        const response = await fetch('/operador/api/saldo');
        if (!response.ok) throw new Error('Erro ao verificar status do caixa');
        
        const data = await response.json();
        
        if (data.message === 'Nenhum caixa aberto encontrado') {
            closeRegisterBtn.style.display = 'none';
            balanceLabel.textContent = 'Nenhum caixa aberto';
        } else {
            closeRegisterBtn.style.display = 'block';
            updateBalance();
        }
    } catch (error) {
        console.error('Error checking caixa status:', error);
    }
}

function handleQuantityInput(e) {
    if (e.target.classList.contains('quantity-input') && e.target.value.trim() !== '') {
        const row = e.target.closest('.product-row');
        if (row && row === productsContainer.lastElementChild) {
            addProductRow();
        }
        calculateSaleTotal();
    }
}

function handleRemoveClick(e) {
    if (e.target.closest('.btn-remove')) {
        const row = e.target.closest('.product-row');
        if (row && productsContainer.children.length > 1) {
            row.remove();
            calculateSaleTotal();
        }
    }
}

function handleProductSelectChange(e) {
    if (e.target.classList.contains('product-select')) {
        calculateSaleTotal();
    }
}

function handleEditClientClick(e) {
    if (e.target.closest('.btn-edit-client')) {
        const clientId = e.target.closest('.btn-edit-client').dataset.id;
        editClient(clientId);
    }
}

function updateCurrentDate() {
    const now = new Date();
    currentDateElement.textContent = now.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function toggleBalance() {
    balanceVisible = !balanceVisible;
    updateBalance();
    toggleBalanceBtn.textContent = balanceVisible ? 'Ocultar saldo' : 'Mostrar saldo';
}

async function updateBalance() {
    try {
        const response = await fetch('/operador/api/saldo');
        if (!response.ok) throw new Error('Erro ao carregar saldo');
        
        const data = await response.json();
        
        if (data.message === 'Nenhum caixa aberto encontrado') {
            openingBalanceLabel.textContent = 'Caixa fechado';
            currentBalanceLabel.textContent = '';
            return;
        }

        if (balanceVisible) {
            openingBalanceLabel.textContent = `Abertura: ${formatCurrency(data.valor_abertura)}`;
            currentBalanceLabel.textContent = `Saldo atual: ${data.saldo_formatado || 'R$ 0,00'}`;
        } else {
            openingBalanceLabel.textContent = 'Abertura: ******';
            currentBalanceLabel.textContent = 'Saldo atual: ******';
        }
    } catch (error) {
        console.error('Error updating balance:', error);
        openingBalanceLabel.textContent = 'Erro ao carregar dados';
        currentBalanceLabel.textContent = '';
    }
}

function formatCurrency(value) {
    // Formata números simples para o formato de moeda
    return 'R$ ' + parseFloat(value).toFixed(2).replace('.', ',').replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
}

// Inicializa
updateBalance();

function switchTab(tabId) {
    tabBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabId));
    tabContents.forEach(content => content.classList.toggle('active', content.id === tabId));
}

async function loadClients() {
    try {
        const response = await fetch('/operador/api/clientes');
        if (!response.ok) throw new Error('Erro ao carregar clientes');
        
        clients = await response.json();
        updateClientSelect();
        renderClientCards();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function loadProducts() {
    try {
        const response = await fetch('/operador/api/produtos');
        if (!response.ok) throw new Error('Erro ao carregar produtos');
        
        products = await response.json();
        updateProductSelects();
        calculateSaleTotal();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

function updateClientSelect() {
    clientSelect.innerHTML = '<option value="">Selecione um cliente</option>';
    clients.forEach(client => {
        const option = document.createElement('option');
        option.value = client.id;
        option.textContent = client.nome;
        clientSelect.appendChild(option);
    });
}

function updateProductSelects() {
    const productSelects = document.querySelectorAll('.product-select');
    productSelects.forEach(select => {
        const currentValue = select.value;
        select.innerHTML = '<option value="">Selecione um produto</option>';
        
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = `${product.nome} (Estoque: ${product.estoque_quantidade} ${product.unidade})`;
            select.appendChild(option);
        });
        
        if (currentValue) select.value = currentValue;
    });
}

function renderClientCards(filteredClients = null) {
    clientsContainer.innerHTML = '';
    const clientsToRender = filteredClients || clients;
    
    clientsToRender.forEach(client => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <div class="card-title">${client.nome}</div>
            <div class="form-grid">
                <div class="form-grid-label">Documento:</div>
                <div>${client.documento || 'Não informado'}</div>
                <div class="form-grid-label">Telefone:</div>
                <div>${client.telefone || 'Não informado'}</div>
                <div class="form-grid-label">Email:</div>
                <div>${client.email || 'Não informado'}</div>
                <div class="form-grid-label">Endereço:</div>
                <div>${client.endereco || 'Não informado'}</div>
            </div>
            <div class="card-actions">
                <button class="btn btn-primary btn-edit-client" data-id="${client.id}">
                    <i class="fas fa-edit"></i> Editar
                </button>
            </div>
        `;
        clientsContainer.appendChild(card);
    });
}

function openClientModal() {
    currentEditingClient = null;
    clientModalTitle.textContent = 'Cadastrar Cliente';
    clientForm.reset();
    openModal('client');
}

function editClient(clientId) {
    const client = clients.find(c => c.id == clientId);
    if (client) {
        currentEditingClient = client;
        clientModalTitle.textContent = 'Editar Cliente';
        
        document.getElementById('client-name').value = client.nome;
        document.getElementById('client-document').value = client.documento || '';
        document.getElementById('client-phone').value = client.telefone || '';
        document.getElementById('client-email').value = client.email || '';
        document.getElementById('client-address').value = client.endereco || '';
        
        openModal('client');
    }
}

function addProductRow() {
    const row = document.createElement('div');
    row.className = 'product-row';
    row.innerHTML = `
        <select class="form-control product-select">
            <option value="">Selecione um produto</option>
        </select>
        <input type="number" class="form-control quantity-input" placeholder="Quantidade" min="1" step="1">
        <button class="btn-remove">
            <i class="fas fa-times"></i>
        </button>
    `;
    productsContainer.appendChild(row);
    updateProductSelects();
}

function calculateSaleTotal() {
    let total = 0;
    const rows = document.querySelectorAll('.product-row');
    
    rows.forEach(row => {
        const productSelect = row.querySelector('.product-select');
        const quantityInput = row.querySelector('.quantity-input');
        const productId = productSelect.value;
        
        if (productId && quantityInput.value) {
            const product = products.find(p => p.id == productId);
            const quantity = parseFloat(quantityInput.value);
            
            if (product && !isNaN(quantity)) {
                total += quantity * product.valor_unitario;
            }
        }
    });
    
    saleTotalElement.textContent = `R$ ${total.toFixed(2)}`;
}

function openModal(type) {
    const modal = document.getElementById(`${type}-modal`);
    if (modal) modal.style.display = 'flex';
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

async function saveClient() {
    const clientData = {
        nome: document.getElementById('client-name').value,
        documento: document.getElementById('client-document').value,
        telefone: document.getElementById('client-phone').value,
        email: document.getElementById('client-email').value,
        endereco: document.getElementById('client-address').value
    };
    
    try {
        const url = currentEditingClient 
            ? `/operador/api/clientes/${currentEditingClient.id}`
            : '/operador/api/clientes';
            
        const method = currentEditingClient ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(clientData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao salvar cliente');
        }
        
        showMessage(currentEditingClient ? 'Cliente atualizado com sucesso!' : 'Cliente cadastrado com sucesso!');
        await loadClients();
        closeModal();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function registerSale() {
    const clienteId = clientSelect.value;
    const paymentMethod = document.getElementById('payment-method').value;
    const notes = document.getElementById('sale-notes').value;
    const amountReceivedRaw = amountReceivedInput.value.trim();
    
    // Validações básicas
    if (!clienteId) return showMessage('Selecione um cliente', 'error');
    if (!paymentMethod) return showMessage('Selecione a forma de pagamento', 'error');
    if (!amountReceivedRaw) return showMessage('Informe o valor recebido', 'error');

    const amountReceived = parseFloat(amountReceivedRaw.replace(',', '.'));
    if (isNaN(amountReceived) || amountReceived < 0) return showMessage('Valor recebido inválido', 'error');
    
    // Preparar itens
    const items = [];
    const rows = document.querySelectorAll('.product-row');
    
    for (const row of rows) {
        const productSelect = row.querySelector('.product-select');
        const quantityInput = row.querySelector('.quantity-input');
        const productId = productSelect.value;
        const quantity = parseFloat(quantityInput.value);
        
        if (productId && quantity > 0) {
            const product = products.find(p => p.id == productId);
            if (product) {
                items.push({
                    produto_id: parseInt(productId),
                    quantidade: quantity,
                    valor_unitario: product.valor_unitario
                });
            }
        }
    }
    
    if (items.length === 0) {
        return showMessage('Adicione pelo menos um produto', 'error');
    }

    // Calcula total da venda
    let totalSale = 0;
    items.forEach(item => {
        totalSale += item.quantidade * item.valor_unitario;
    });

    if (amountReceived < totalSale && paymentMethod !== 'a_prazo') {
        return showMessage('Valor recebido menor que o total', 'error');
    }

    const troco = (amountReceived - totalSale).toFixed(2);

    // Confirma troco antes de finalizar
    if (!confirm(`Troco: R$ ${troco}\nDeseja finalizar a venda?`)) {
        return;
    }

    try {
        const response = await fetch('/operador/api/vendas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cliente_id: parseInt(clienteId),
                forma_pagamento: paymentMethod,
                valor_recebido: amountReceived,
                observacao: notes,
                itens: items
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao registrar venda');
        }
        
        const result = await response.json();
        resetSaleForm();
        await updateBalance();
        showMessage(`Venda registrada! Total: R$ ${result.valor_total.toFixed(2)} | Troco: R$ ${troco}`);
        await loadProducts();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

function resetSaleForm() {
    // Limpa todas as linhas exceto a primeira
    while (productsContainer.children.length > 1) {
        productsContainer.removeChild(productsContainer.lastChild);
    }
    
    // Reseta a primeira linha
    const firstRow = productsContainer.firstElementChild;
    firstRow.querySelector('.product-select').value = '';
    firstRow.querySelector('.quantity-input').value = '';
    
    // Reseta outros campos
    clientSelect.value = '';
    document.getElementById('payment-method').value = '';
    document.getElementById('sale-notes').value = '';
    amountReceivedInput.value = '';
    saleTotalElement.textContent = 'R$ 0.00';
}

async function closeRegister() {
    const valorFechamento = prompt('Informe o valor de fechamento do caixa:');
    if (!valorFechamento || isNaN(valorFechamento)) {
        return showMessage('Valor de fechamento inválido', 'error');
    }

    if (confirm('Deseja realmente fechar o caixa?')) {
        try {
            const response = await fetch('/operador/api/fechar-caixa', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ valor_fechamento: parseFloat(valorFechamento) })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Erro ao fechar caixa');
            }
            
            const now = new Date();
            showMessage(`Caixa fechado às ${now.toLocaleTimeString('pt-BR')}`);
            await checkCaixaStatus();
        } catch (error) {
            showMessage(error.message, 'error');
        }
    }
}

function searchClients() {
    const searchTerm = clientSearch.value.toLowerCase();
    if (!searchTerm) return renderClientCards();
    
    const filteredClients = clients.filter(client => 
        client.nome.toLowerCase().includes(searchTerm) ||
        (client.documento && client.documento.toLowerCase().includes(searchTerm)) ||
        (client.telefone && client.telefone.toLowerCase().includes(searchTerm))
    );
    
    renderClientCards(filteredClients);
}

function showMessage(message, type = 'success') {
    notification.className = `notification ${type} show`;
    notificationMessage.textContent = message;
    
    const icon = notification.querySelector('i');
    icon.className = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    
    setTimeout(() => notification.classList.remove('show'), 5000);
}

// Função para fechar o modal de troco (se necessário)
function fecharModalTroco() {
    const modal = document.getElementById('troco-modal');
    if (modal) modal.style.display = 'none';
}