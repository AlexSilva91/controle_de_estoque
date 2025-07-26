// Variáveis globais
let balanceVisible = true;
let currentBalance = 0;
let clients = [];
let products = [];
let currentEditingClient = null;
let selectedClient = null;
let selectedProducts = [];

// DOM Elements
const openingBalanceLabel = document.getElementById('opening-balance').querySelector('.balance-value');
const currentBalanceLabel = document.getElementById('current-balance').querySelector('.balance-value');
const currentDateElement = document.getElementById('current-date');
const toggleBalanceBtn = document.getElementById('toggle-balance');
const tabBtns = document.querySelectorAll('.menu-item');
const tabContents = document.querySelectorAll('.tab-content');
const productsList = document.getElementById('products-list');
const clientSearchInput = document.getElementById('client-search-input');
const selectedClientInput = document.getElementById('selected-client');
const selectedClientIdInput = document.getElementById('selected-client-id');
const productSearchInput = document.getElementById('product-search-input');
const addProductBtn = document.getElementById('add-product-btn');
const registerSaleBtn = document.getElementById('register-sale-btn');
const closeRegisterBtn = document.getElementById('close-register-btn');
const clientModal = document.getElementById('client-modal');
const clientModalTitle = document.getElementById('client-modal-title');
const clientForm = document.getElementById('client-form');
const modalCloses = document.querySelectorAll('.modal-close, #cancel-client');
const saleTotalElement = document.getElementById('sale-total');
const subtotalValueElement = document.getElementById('subtotal-value');
const changeValueElement = document.getElementById('change-value');
const amountReceivedInput = document.getElementById('amount-received');
const discountValueInput = document.getElementById('discount-value');
const discountTypeSelect = document.getElementById('discount-type');
const applyDiscountBtn = document.getElementById('apply-discount-btn');
const logoutBtn = document.getElementById('logout-btn');
const notification = document.getElementById('notification');
const notificationMessage = document.getElementById('notification-message');
const clientSearch = document.getElementById('client-search');
const searchClientBtn = document.getElementById('search-client-btn');
const productSearchModal = document.getElementById('product-search-modal');
const modalProductSearch = document.getElementById('modal-product-search');
const productSearchResults = document.getElementById('product-search-results');
const currentTabTitle = document.getElementById('current-tab-title');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateCurrentDate();
    loadClients();
    loadProducts();
    checkCaixaStatus();
    setupEventListeners();

    // Atualiza produtos a cada 10s
    setInterval(loadProducts, 10000);

    // Atualiza saldo a cada 10s
    setInterval(updateBalance, 10000);
});

function setupEventListeners() {
    toggleBalanceBtn.addEventListener('click', toggleBalance);
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    document.getElementById('search-client-btn').addEventListener('click', searchClient);
    clientSearchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchClient();
    });
    
    document.getElementById('add-client-btn').addEventListener('click', () => openClientModal());
    document.getElementById('search-product-btn').addEventListener('click', openProductSearchModal);
    productSearchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') openProductSearchModal();
    });
    
    addProductBtn.addEventListener('click', addEmptyProductRow);
    
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
    productsList.addEventListener('input', (e) => {
        if (e.target.classList.contains('quantity-input')) {
            updateProductQuantity(e.target);
            calculateSaleTotal();
        }
    });
    
    productsList.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-remove')) {
            removeProductRow(e.target);
            calculateSaleTotal();
        }
    });
    
    amountReceivedInput.addEventListener('input', calculateSaleTotal);
    applyDiscountBtn.addEventListener('click', applyDiscount);
    
    // Modal de busca de produtos
    document.getElementById('modal-search-product-btn').addEventListener('click', searchProductsInModal);
    modalProductSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchProductsInModal();
    });
}

async function checkCaixaStatus() {
    try {
        const response = await fetch('/operador/api/saldo');
        if (!response.ok) throw new Error('Erro ao verificar status do caixa');
        
        const data = await response.json();
        
        if (data.message === 'Nenhum caixa aberto encontrado') {
            closeRegisterBtn.style.display = 'none';
        } else {
            closeRegisterBtn.style.display = 'block';
            updateBalance();
        }
    } catch (error) {
        console.error('Error checking caixa status:', error);
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
    toggleBalanceBtn.innerHTML = balanceVisible ? '<i class="fas fa-eye-slash"></i>' : '<i class="fas fa-eye"></i>';
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
            openingBalanceLabel.textContent = formatCurrency(data.valor_abertura);
            currentBalanceLabel.textContent = data.saldo_formatado || 'R$ 0,00';
        } else {
            openingBalanceLabel.textContent = '******';
            currentBalanceLabel.textContent = '******';
        }
    } catch (error) {
        console.error('Error updating balance:', error);
        openingBalanceLabel.textContent = 'Erro';
        currentBalanceLabel.textContent = '';
    }
}

function formatCurrency(value) {
    if (typeof value === 'string') {
        value = parseFloat(value.replace(',', '.'));
    }
    return 'R$ ' + value.toFixed(2).replace('.', ',').replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
}

function switchTab(tabId) {
    // Atualiza a UI das abas
    tabBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabId));
    tabContents.forEach(content => content.classList.toggle('active', content.id === tabId));
    
    // Atualiza o título da aba atual
    const activeTabBtn = document.querySelector(`.menu-item[data-tab="${tabId}"]`);
    if (activeTabBtn) {
        currentTabTitle.textContent = activeTabBtn.querySelector('span').textContent;
    }
}

async function loadClients() {
    try {
        const response = await fetch('/operador/api/clientes');
        if (!response.ok) throw new Error('Erro ao carregar clientes');
        
        clients = await response.json();
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
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function searchClient() {
    const searchTerm = clientSearchInput.value.trim();
    if (!searchTerm) {
        showMessage('Digite um termo para busca', 'error');
        return;
    }

    try {
        const response = await fetch(`/operador/api/clientes/buscar?q=${encodeURIComponent(searchTerm)}`);
        if (!response.ok) throw new Error('Erro ao buscar clientes');
        
        const results = await response.json();
        
        if (results.length === 0) {
            showMessage('Nenhum cliente encontrado', 'error');
            return;
        }
        
        if (results.length === 1) {
            // Seleciona automaticamente se houver apenas um resultado
            selectClient(results[0]);
        } else {
            // Mostra modal com resultados para seleção
            showClientSearchResults(results);
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

function selectClient(client) {
    selectedClient = client;
    selectedClientInput.value = client.nome;
    selectedClientIdInput.value = client.id;
    showMessage(`Cliente selecionado: ${client.nome}`);
}

function showClientSearchResults(clients) {
    // Implementar modal de seleção de cliente se necessário
    // Por enquanto, seleciona o primeiro
    if (clients.length > 0) {
        selectClient(clients[0]);
    }
}

function renderClientCards(filteredClients = null) {
    const container = document.getElementById('clients-container');
    container.innerHTML = '';
    const clientsToRender = filteredClients || clients;
    
    clientsToRender.forEach(client => {
        const card = document.createElement('div');
        card.className = 'client-card';
        card.innerHTML = `
            <h4>${client.nome}</h4>
            <div class="client-info">
                <div class="client-info-label">Documento:</div>
                <div>${client.documento || 'Não informado'}</div>
                <div class="client-info-label">Telefone:</div>
                <div>${client.telefone || 'Não informado'}</div>
                <div class="client-info-label">Email:</div>
                <div>${client.email || 'Não informado'}</div>
                <div class="client-info-label">Endereço:</div>
                <div>${client.endereco || 'Não informado'}</div>
            </div>
            <div class="client-card-actions">
                <button class="btn-primary btn-edit-client" data-id="${client.id}">
                    <i class="fas fa-edit"></i> Editar
                </button>
            </div>
        `;
        container.appendChild(card);
    });
    
    // Adiciona event listeners para os botões de edição
    document.querySelectorAll('.btn-edit-client').forEach(btn => {
        btn.addEventListener('click', () => editClient(btn.dataset.id));
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

function openProductSearchModal() {
    const searchTerm = productSearchInput.value.trim();
    if (searchTerm) {
        modalProductSearch.value = searchTerm;
    }
    openModal('product-search');
    searchProductsInModal();
}

function searchProductsInModal() {
    const searchTerm = modalProductSearch.value.trim().toLowerCase();
    if (!searchTerm) {
        productSearchResults.innerHTML = '<p>Digite um termo para busca</p>';
        return;
    }

    const filteredProducts = products.filter(product => 
        product.nome.toLowerCase().includes(searchTerm) ||
        (product.marca && product.marca.toLowerCase().includes(searchTerm)) ||
        (product.codigo && product.codigo.toLowerCase().includes(searchTerm))
    );

    displayProductSearchResults(filteredProducts);
}

function displayProductSearchResults(products) {
    productSearchResults.innerHTML = '';
    
    if (products.length === 0) {
        productSearchResults.innerHTML = '<p>Nenhum produto encontrado</p>';
        return;
    }
    
    products.forEach(product => {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.innerHTML = `
            <h4>${product.nome}</h4>
            <p>Marca: ${product.marca || 'Não informada'} | Código: ${product.codigo || 'Não informado'}</p>
            <p>Preço: ${formatCurrency(product.valor_unitario)} | Estoque: ${product.estoque_quantidade} ${product.unidade}</p>
        `;
        item.addEventListener('click', () => {
            addProductToSale(product);
            closeModal();
        });
        productSearchResults.appendChild(item);
    });
}

function addProductToSale(product) {
    // Verifica se o produto já está na lista
    const existingProductIndex = selectedProducts.findIndex(p => p.id === product.id);
    
    if (existingProductIndex >= 0) {
        // Aumenta a quantidade se o produto já estiver na lista
        selectedProducts[existingProductIndex].quantity += 1;
    } else {
        // Adiciona novo produto à lista
        selectedProducts.push({
            id: product.id,
            name: product.nome,
            description: product.descricao || '',
            price: product.valor_unitario,
            quantity: 1,
            unit: product.unidade,
            stock: product.estoque_quantidade
        });
    }
    
    renderProductsList();
    calculateSaleTotal();
}

function addEmptyProductRow() {
    openProductSearchModal();
}

function renderProductsList() {
    productsList.innerHTML = '';
    
    selectedProducts.forEach((product, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${product.name}</td>
            <td>${product.description}</td>
            <td>${formatCurrency(product.price)}</td>
            <td>
                <input type="number" class="quantity-input" 
                       value="${product.quantity}" min="1" 
                       max="${product.stock}" data-index="${index}">
                <small>${product.unit}</small>
            </td>
            <td>${formatCurrency(product.price * product.quantity)}</td>
            <td>
                <button class="btn-remove" data-index="${index}">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        productsList.appendChild(row);
    });
}

function updateProductQuantity(input) {
    const index = parseInt(input.dataset.index);
    const newQuantity = parseInt(input.value);
    
    if (index >= 0 && index < selectedProducts.length && !isNaN(newQuantity) && newQuantity > 0) {
        selectedProducts[index].quantity = newQuantity;
    }
}

function removeProductRow(button) {
    const index = parseInt(button.dataset.index);
    if (index >= 0 && index < selectedProducts.length) {
        selectedProducts.splice(index, 1);
        renderProductsList();
    }
}

function calculateSaleTotal() {
    let subtotal = 0;
    
    // Calcula subtotal
    selectedProducts.forEach(product => {
        subtotal += product.price * product.quantity;
    });
    
    // Aplica desconto se existir
    let total = subtotal;
    let discount = parseFloat(discountValueInput.value) || 0;
    
    if (discount > 0) {
        if (discountTypeSelect.value === 'percent') {
            discount = subtotal * (discount / 100);
        }
        total = Math.max(0, subtotal - discount);
    }
    
    // Calcula troco
    let change = 0;
    const amountReceived = parseFloat(amountReceivedInput.value) || 0;
    
    if (amountReceived > 0) {
        change = Math.max(0, amountReceived - total);
    }
    
    // Atualiza UI
    subtotalValueElement.textContent = formatCurrency(subtotal);
    saleTotalElement.textContent = formatCurrency(total);
    changeValueElement.textContent = formatCurrency(change);
}

function applyDiscount() {
    calculateSaleTotal();
    showMessage('Desconto aplicado com sucesso');
}

async function registerSale() {
    if (!selectedClientIdInput.value) {
        showMessage('Selecione um cliente', 'error');
        return;
    }
    
    if (selectedProducts.length === 0) {
        showMessage('Adicione pelo menos um produto', 'error');
        return;
    }
    
    const paymentMethod = document.getElementById('payment-method').value;
    if (!paymentMethod) {
        showMessage('Selecione a forma de pagamento', 'error');
        return;
    }
    
    const notes = document.getElementById('sale-notes').value;
    const amountReceived = parseFloat(amountReceivedInput.value) || 0;
    const total = parseFloat(saleTotalElement.textContent.replace('R$ ', '').replace('.', '').replace(',', '.'));
    
    if (paymentMethod !== 'a_prazo' && amountReceived < total) {
        showMessage('Valor recebido menor que o total da venda', 'error');
        return;
    }
    
    // Preparar itens para envio
    const items = selectedProducts.map(product => ({
        produto_id: product.id,
        quantidade: product.quantity,
        valor_unitario: product.price
    }));
    
    // Preparar dados do desconto
    let discount = 0;
    const discountValue = parseFloat(discountValueInput.value) || 0;
    
    if (discountValue > 0) {
        discount = discountTypeSelect.value === 'percent' 
            ? (discountValue / 100) * items.reduce((sum, item) => sum + (item.valor_unitario * item.quantidade), 0)
            : discountValue;
    }
    
    try {
        const response = await fetch('/operador/api/vendas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cliente_id: parseInt(selectedClientIdInput.value),
                forma_pagamento: paymentMethod,
                valor_recebido: amountReceived,
                desconto: discount,
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
        showMessage(`Venda registrada! Total: ${formatCurrency(result.valor_total)}`);
        await loadProducts();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

function resetSaleForm() {
    selectedClient = null;
    selectedProducts = [];
    selectedClientInput.value = '';
    selectedClientIdInput.value = '';
    productsList.innerHTML = '';
    document.getElementById('payment-method').value = '';
    document.getElementById('sale-notes').value = '';
    amountReceivedInput.value = '';
    discountValueInput.value = '';
    discountTypeSelect.value = 'fixed';
    calculateSaleTotal();
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

function showMessage(message, type = 'success') {
    notification.className = `notification ${type} show`;
    notificationMessage.textContent = message;
    
    const icon = notification.querySelector('.notification-icon i');
    icon.className = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    
    setTimeout(() => notification.classList.remove('show'), 5000);
}