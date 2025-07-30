// Variáveis globais
let balanceVisible = true;
let currentBalance = 0;
let clients = [];
let products = [];
let currentEditingClient = null;
let selectedClient = null;
let selectedProducts = [];
let deliveryAddress = null;
let currentCaixaId = null;
let currentUser = null;

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
const logoutBtn = document.getElementById('logout-btn');
const notification = document.getElementById('notification');
const notificationMessage = document.getElementById('notification-message');
const clientSearch = document.getElementById('client-search');
const searchClientBtn = document.getElementById('search-client-btn');
const productSearchModal = document.getElementById('product-search-modal');
const modalProductSearch = document.getElementById('modal-product-search');
const productSearchResults = document.getElementById('product-search-results');
const currentTabTitle = document.getElementById('current-tab-title');
const deliveryBtn = document.getElementById('delivery-btn');
const deliveryModal = document.getElementById('delivery-modal');
const saveDeliveryBtn = document.getElementById('save-delivery');
const cancelDeliveryBtn = document.getElementById('cancel-delivery');
const openExpenseModalBtn = document.getElementById('open-expense-modal-btn');
const expenseModal = document.getElementById('expense-modal');
const expenseForm = document.getElementById('expense-form');
const cancelExpenseBtn = document.getElementById('cancel-expense');
const saveExpenseBtn = document.getElementById('save-expense');

// Configuração para prevenir cache
const preventCacheConfig = {
    headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
};

// Initialize com prevenção de cache
document.addEventListener('DOMContentLoaded', async () => {
    updateCurrentDate();
    await loadCurrentUser();
    await loadClients();
    await loadProducts();
    await checkCaixaStatus();
    setupEventListeners();

    // Atualiza produtos a cada 10s com prevenção de cache
    setInterval(() => loadProducts(true), 10000);

    // Atualiza saldo a cada 10s com prevenção de cache
    setInterval(() => updateBalance(true), 10000);
});

async function loadCurrentUser() {
    try {
        const response = await fetch('/operador/api/usuario', {
            ...preventCacheConfig,
            method: 'GET'
        });
        if (!response.ok) throw new Error('Erro ao carregar dados do usuário');
        
        currentUser = await response.json();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

document.getElementById("remove-selected-client-btn").addEventListener("click", function () {
    // Limpa os campos de cliente selecionado
    document.getElementById("selected-client").value = "";
    document.getElementById("selected-client-id").value = "";

    // Atualiza o status do caixa
    window.updateCaixaStatus();
});

window.updateCaixaStatus = function() {
    const caixaStatusDisplay = document.querySelector('.caixa-status');
    if (selectedClientInput.value.trim() !== '') {
        caixaStatusDisplay.className = 'caixa-status caixa-operacao';
        caixaStatusDisplay.innerHTML = '<i class="fas fa-user-check"></i><span>CAIXA EM OPERAÇÃO</span>';
    } else {
        caixaStatusDisplay.className = 'caixa-status caixa-livre';
        caixaStatusDisplay.innerHTML = '<i class="fas fa-check-circle"></i><span>CAIXA LIVRE</span>';
    }
};

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
        // Forçar recarregamento sem cache
        window.location.href = '/logout?' + new Date().getTime();
    });
    
    searchClientBtn.addEventListener('click', searchClients);
    clientSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchClients();
    });
    
    productsList.addEventListener('input', (e) => {
        if (e.target.classList.contains('quantity-input')) {
            updateProductQuantity(e.target);
            calculateSaleTotal();
        }
    });
    
    productsList.addEventListener('click', (e) => {
        if (e.target.closest('.btn-remove')) {
            const button = e.target.closest('.btn-remove');
            removeProductRow(button);
            calculateSaleTotal();
        }
    });
    
    amountReceivedInput.addEventListener('input', calculateSaleTotal);
    
    document.getElementById('modal-search-product-btn').addEventListener('click', searchProductsInModal);
    modalProductSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchProductsInModal();
    });
    
    document.getElementById('cancel-product-search').addEventListener('click', () => {
        closeModal();
        productSearchInput.value = '';
    });
    
    deliveryBtn.addEventListener('click', openDeliveryModal);
    saveDeliveryBtn.addEventListener('click', saveDeliveryAddress);
    cancelDeliveryBtn.addEventListener('click', closeModal);
    
    openExpenseModalBtn.addEventListener('click', openExpenseModal);
    cancelExpenseBtn.addEventListener('click', closeExpenseModal);
    saveExpenseBtn.addEventListener('click', saveExpense);
}

// ==================== FUNÇÕES DE DESPESAS ====================
function openExpenseModal() {
    if (!currentCaixaId) {
        showMessage('Nenhum caixa aberto encontrado', 'error');
        return;
    }
    
    expenseModal.style.display = 'flex';
    document.getElementById('expense-description').focus();
}

function closeExpenseModal() {
    expenseModal.style.display = 'none';
    expenseForm.reset();
}

async function saveExpense() {
    const description = document.getElementById('expense-description').value.trim();
    const amount = document.getElementById('expense-amount').value;
    const note = document.getElementById('expense-note').value.trim();
    
    if (!description) {
        showMessage('Descrição da despesa é obrigatória', 'error');
        return;
    }
    
    if (!amount || parseFloat(amount) <= 0) {
        showMessage('Valor da despesa deve ser maior que zero', 'error');
        return;
    }
    
    try {
        const response = await fetch('/operador/api/despesa', {
            ...preventCacheConfig,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                descricao: description,
                valor: amount,
                observacao: note,
                caixa_id: currentCaixaId
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.erro || 'Erro ao registrar despesa');
        }
        
        showMessage('Despesa registrada com sucesso!');
        closeExpenseModal();
        updateBalance(true); // Forçar atualização sem cache
    } catch (error) {
        showMessage(error.message, 'error');
        console.error('Erro ao salvar despesa:', error);
    }
}

// ==================== FUNÇÕES DE ENTREGA ====================
function openDeliveryModal() {
    if (deliveryAddress) {
        document.getElementById('delivery-address').value = deliveryAddress.logradouro || '';
        document.getElementById('delivery-number').value = deliveryAddress.numero || '';
        document.getElementById('delivery-complement').value = deliveryAddress.complemento || '';
        document.getElementById('delivery-neighborhood').value = deliveryAddress.bairro || '';
        document.getElementById('delivery-city').value = deliveryAddress.cidade || '';
        document.getElementById('delivery-state').value = deliveryAddress.estado || '';
        document.getElementById('delivery-zipcode').value = deliveryAddress.cep || '';
        document.getElementById('delivery-instructions').value = deliveryAddress.instrucoes || '';
    }
    
    openModal('delivery');
}

function saveDeliveryAddress() {
    const address = document.getElementById('delivery-address').value;
    const number = document.getElementById('delivery-number').value;
    
    if (!address || !number) {
        showMessage('Endereço e número são obrigatórios', 'error');
        return;
    }
    
    deliveryAddress = {
        logradouro: address,
        numero: number,
        complemento: document.getElementById('delivery-complement').value,
        bairro: document.getElementById('delivery-neighborhood').value,
        cidade: document.getElementById('delivery-city').value,
        estado: document.getElementById('delivery-state').value,
        cep: document.getElementById('delivery-zipcode').value,
        instrucoes: document.getElementById('delivery-instructions').value
    };
    
    deliveryBtn.classList.add('has-delivery');
    deliveryBtn.innerHTML = '<i class="fas fa-check-circle"></i> Endereço de Entrega Cadastrado';
    
    closeModal();
    showMessage('Endereço de entrega salvo com sucesso!');
    showDeliveryInfo();
}

function showDeliveryInfo() {
    const existingInfo = document.querySelector('.delivery-info');
    if (existingInfo) existingInfo.remove();
    
    const deliveryInfo = document.createElement('div');
    deliveryInfo.className = 'delivery-info';
    deliveryInfo.innerHTML = `
        <p><strong>Endereço de Entrega:</strong></p>
        <p>${deliveryAddress.logradouro}, ${deliveryAddress.numero}${deliveryAddress.complemento ? ', ' + deliveryAddress.complemento : ''}</p>
        <p>${deliveryAddress.bairro} - ${deliveryAddress.cidade}/${deliveryAddress.estado}</p>
        <p>CEP: ${deliveryAddress.cep}</p>
        ${deliveryAddress.instrucoes ? `<p><strong>Instruções:</strong> ${deliveryAddress.instrucoes}</p>` : ''}
        <button class="btn-edit-delivery" id="edit-delivery-btn">
            <i class="fas fa-edit"></i> Editar Endereço
        </button>
    `;
    
    deliveryBtn.insertAdjacentElement('afterend', deliveryInfo);
    document.getElementById('edit-delivery-btn').addEventListener('click', openDeliveryModal);
}

// ==================== FUNÇÕES DE PRODUTOS ====================
function addProductToSale(product) {
    // Verifica se o produto já está na lista
    const existingProductIndex = selectedProducts.findIndex(p => p.id === product.id);
    
    if (existingProductIndex >= 0) {
        // Se já existe, apenas incrementa a quantidade
        selectedProducts[existingProductIndex].quantity += 1;
    } else {
        // Se não existe, adiciona o produto à lista
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
    
    // Atualiza a exibição da lista de produtos
    renderProductsList();
    // Recalcula o total da venda
    calculateSaleTotal();
}

function renderProductsList() {
    // Limpa a lista de produtos
    productsList.innerHTML = '';
    
    // Adiciona cada produto à lista
    selectedProducts.forEach((product, index) => {
        const totalValue = product.price * product.quantity;
        
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
            <td class="product-total">${formatCurrency(totalValue)}</td>
            <td>
                <button class="btn-remove" data-index="${index}" title="Remover produto">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        productsList.appendChild(row);
    });
}

function calculateSaleTotal() {
    let subtotal = 0;
    
    // Calcula o subtotal baseado nos produtos selecionados
    selectedProducts.forEach((product, index) => {
        const totalValue = product.price * product.quantity;
        subtotal += totalValue;
        
        // Atualiza o valor total na linha do produto
        const row = productsList.children[index];
        if (row) {
            const totalCell = row.querySelector('.product-total');
            if (totalCell) {
                totalCell.textContent = formatCurrency(totalValue);
            }
        }
    });
    
    let total = subtotal;
    let change = 0;
    const amountReceived = parseFloat(amountReceivedInput.value) || 0;
    
    // Calcula o troco se houver valor recebido
    if (amountReceived > 0) {
        change = Math.max(0, amountReceived - total);
    }
    
    // Atualiza os valores na interface
    subtotalValueElement.textContent = formatCurrency(subtotal);
    saleTotalElement.textContent = formatCurrency(total);
    changeValueElement.textContent = formatCurrency(change);
}

// ==================== FUNÇÕES DE CLIENTES ====================
async function loadClients() {
    try {
        const response = await fetch('/operador/api/clientes', {
            ...preventCacheConfig,
            method: 'GET'
        });
        if (!response.ok) throw new Error('Erro ao carregar clientes');
        
        clients = await response.json();
        renderClientCards();
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
        const response = await fetch(`/operador/api/clientes/buscar?q=${encodeURIComponent(searchTerm)}&timestamp=${new Date().getTime()}`, {
            ...preventCacheConfig,
            method: 'GET'
        });
        if (!response.ok) throw new Error('Erro ao buscar clientes');
        
        const results = await response.json();
        
        if (results.length === 0) {
            showMessage('Nenhum cliente encontrado', 'error');
            return;
        }
        
        if (results.length === 1) {
            selectClient(results[0]);
        } else {
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
    updateCaixaStatus();
}

function showClientSearchResults(clients) {
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

async function saveClient() {
    const clientData = {
        nome: document.getElementById('client-name').value,
        documento: document.getElementById('client-document').value,
        telefone: document.getElementById('client-phone').value,
        email: document.getElementById('client-email').value,
        endereco: document.getElementById('client-address').value
    };
    
    try {
        let response;
        if (currentEditingClient) {
            response = await fetch(`/operador/api/clientes/${currentEditingClient.id}`, {
                ...preventCacheConfig,
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(clientData)
            });
        } else {
            response = await fetch('/operador/api/clientes', {
                ...preventCacheConfig,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(clientData)
            });
        }
        
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

// ==================== FUNÇÕES DE PRODUTOS ====================
async function loadProducts(forceUpdate = false) {
    try {
        const url = forceUpdate 
            ? `/operador/api/produtos?timestamp=${new Date().getTime()}`
            : '/operador/api/produtos';
            
        const response = await fetch(url, {
            ...preventCacheConfig,
            method: 'GET'
        });
        if (!response.ok) throw new Error('Erro ao carregar produtos');
        
        products = await response.json();
    } catch (error) {
        showMessage(error.message, 'error');
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
            <p>Preço: ${formatCurrency(product.valor_unitario)} | Estoque Loja: ${product.estoque_loja} ${product.unidade}</p>
        `;
        item.addEventListener('click', () => {
            addProductToSale(product);
            closeModal();
        });
        productSearchResults.appendChild(item);
    });
}

// Variáveis globais para controle dos dropdowns
let clientSearchTimeout;
let productSearchTimeout;
let activeSearchDropdown = null;

// Função para mostrar os resultados da busca
function showSearchResults(results, containerId, type) {
    const resultsContainer = document.getElementById(containerId);
    resultsContainer.innerHTML = '';

    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">Nenhum resultado encontrado</div>';
        resultsContainer.style.display = 'block';
        return;
    }

    results.forEach(item => {
        const resultItem = document.createElement('div');
        resultItem.className = 'search-result-item';
        resultItem.dataset.id = item.id;
        
        if (type === 'client') {
            resultItem.innerHTML = `
                <h4>${item.nome}</h4>
                <p>Documento: ${item.documento || 'Não informado'}</p>
                <p>Telefone: ${item.telefone || 'Não informado'}</p>
            `;
            
            resultItem.addEventListener('click', () => {
                selectClient(item);
                resultsContainer.style.display = 'none';
                document.getElementById('client-search-input').value = '';
            });
        } else if (type === 'product') {
            resultItem.innerHTML = `
                <h4>${item.nome}</h4>
                <p>Código: ${item.codigo || 'Não informado'} | Marca: ${item.marca || 'Não informada'}</p>
                <p>Preço: ${formatCurrency(item.valor_unitario)} | Estoque loja: ${item.estoque_loja} ${item.unidade || 'un'} | Estoque depósito: ${item.estoque_deposito || 0} ${item.unidade || 'un'}</p>
            `;
            
            resultItem.addEventListener('click', () => {
                addProductToSale(item);
                resultsContainer.style.display = 'none';
                document.getElementById('product-search-input').value = '';
            });
        }
        
        resultsContainer.appendChild(resultItem);
    });

    resultsContainer.style.display = 'block';
    activeSearchDropdown = resultsContainer;
}

// Função para buscar clientes
async function searchClients(searchTerm) {
    try {
        const response = await fetch(`/operador/api/clientes/buscar?q=${encodeURIComponent(searchTerm)}&timestamp=${new Date().getTime()}`, {
            ...preventCacheConfig,
            method: 'GET'
        });
        if (!response.ok) throw new Error('Erro ao buscar clientes');

        const results = await response.json();
        showSearchResults(results, 'client-search-results', 'client');
    } catch (error) {
        console.error('Erro na busca de clientes:', error);
        showMessage(error.message, 'error');
    }
}

// Função para buscar produtos
async function searchProducts(searchTerm) {
    try {
        const response = await fetch(`/operador/api/produtos/buscar?q=${encodeURIComponent(searchTerm)}&timestamp=${new Date().getTime()}`, {
            ...preventCacheConfig,
            method: 'GET'
        });
        if (!response.ok) throw new Error('Erro ao buscar produtos');
        
        const results = await response.json();
        showSearchResults(results, 'product-search-results', 'product');
    } catch (error) {
        console.error('Erro na busca de produtos:', error);
        showMessage(error.message, 'error');
    }
}

// Função para fechar todos os dropdowns
function closeAllDropdowns() {
    document.querySelectorAll('.search-results-dropdown').forEach(dropdown => {
        dropdown.style.display = 'none';
    });
    activeSearchDropdown = null;
}

// Event listeners para os campos de busca
document.addEventListener('DOMContentLoaded', function() {
    // Configuração do campo de busca de clientes
    const clientSearchInput = document.getElementById('client-search-input');
    clientSearchInput.addEventListener('input', function(e) {
        clearTimeout(clientSearchTimeout);
        const searchTerm = e.target.value.trim();
        
        if (searchTerm.length >= 2) {
            clientSearchTimeout = setTimeout(() => {
                searchClients(searchTerm);
            }, 300);
        } else if (searchTerm.length === 0) {
            // Mostra todos os clientes quando o campo está vazio
            searchClients('');
        } else {
            closeAllDropdowns();
        }
    });
    
    clientSearchInput.addEventListener('focus', async function () {
        await searchClients(''); // Executa toda vez que o campo for focado
    });

    // Configuração do campo de busca de produtos
    const productSearchInput = document.getElementById('product-search-input');
    productSearchInput.addEventListener('input', function(e) {
        clearTimeout(productSearchTimeout);
        const searchTerm = e.target.value.trim();
        
        if (searchTerm.length >= 2) {
            productSearchTimeout = setTimeout(() => {
                searchProducts(searchTerm);
            }, 300);
        } else if (searchTerm.length === 0) {
            // Mostra todos os produtos quando o campo está vazio
            searchProducts('');
        } else {
            closeAllDropdowns();
        }
    });
    
    productSearchInput.addEventListener('focus', function() {
        if (productSearchInput.value.trim().length >= 2) {
            searchProducts(productSearchInput.value.trim());
        } else {
            // Mostra todos os produtos quando o campo recebe foco
            searchProducts('');
        }
    });
    
    // Fecha os dropdowns quando clicar fora
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-container') && activeSearchDropdown) {
            closeAllDropdowns();
        }
    });
    
    // Fecha os dropdowns ao pressionar Esc
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && activeSearchDropdown) {
            closeAllDropdowns();
        }
    });
    
    // Botões de busca (opcional - mantém a funcionalidade original)
    document.getElementById('search-client-btn').addEventListener('click', function() {
        const searchTerm = clientSearchInput.value.trim();
        if (searchTerm.length >= 2) {
            searchClients(searchTerm);
        } else {
            searchClients('');
        }
    });
    
    document.getElementById('search-product-btn').addEventListener('click', function() {
        const searchTerm = productSearchInput.value.trim();
        if (searchTerm.length >= 2) {
            searchProducts(searchTerm);
        } else {
            searchProducts('');
        }
    });
});

function addEmptyProductRow() {
    openProductSearchModal();
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

// ==================== FUNÇÕES DE VENDA ====================
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
    
    // Preparar itens para envio garantindo tipos numéricos
    const items = selectedProducts.map(product => ({
        produto_id: product.id,
        quantidade: Number(product.quantity),
        valor_unitario: Number(product.price),
        valor_total: Number(product.price * product.quantity)
    }));

    // Preparar dados da venda incluindo endereço de entrega se existir
    const saleData = {
        cliente_id: parseInt(selectedClientIdInput.value),
        forma_pagamento: paymentMethod,
        valor_recebido: amountReceived,
        itens: items,
        observacao: notes
    };

    // Adicionar dados de entrega se existirem
    if (deliveryAddress) {
        saleData.endereco_entrega = {
            logradouro: deliveryAddress.logradouro,
            numero: deliveryAddress.numero,
            complemento: deliveryAddress.complemento || null,
            bairro: deliveryAddress.bairro,
            cidade: deliveryAddress.cidade,
            estado: deliveryAddress.estado,
            cep: deliveryAddress.cep,
            instrucoes: deliveryAddress.instrucoes || null
        };
    }

    try {
        const response = await fetch('/operador/api/vendas', {
            ...preventCacheConfig,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(saleData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao registrar venda');
        }
        
        const result = await response.json();
        
        // LIMPEZA COMPLETA APÓS A VENDA
        resetSaleForm();
        
        await updateBalance(true); // Forçar atualização sem cache
        await loadProducts(true); // Forçar atualização sem cache
        
        showMessage('Registrando venda...');
        showMessage(`Venda registrada com sucesso! Nº Nota: ${result.nota_id}`);
        showMessage('Gerando comprovante...');
        
        // Abrir comprovante em nova aba sem cache
        window.open(`/operador/pdf/nota/${result.nota_id}?timestamp=${new Date().getTime()}`, '_blank');
    } catch (error) {
        console.error("Erro ao registrar venda:", error);
        showMessage(error.message, 'error');
    }
}

// Função para resetar completamente o formulário de venda
function resetSaleForm() {
    // Limpa dados do cliente
    selectedClient = null;
    selectedClientInput.value = '';
    selectedClientIdInput.value = '';

    // LIMPEZA COMPLETA DA LISTA DE PRODUTOS
    selectedProducts = [];
    productsList.innerHTML = '';

    // Limpa formas de pagamento e valores
    document.getElementById('payment-method').value = '';
    document.getElementById('sale-notes').value = '';
    amountReceivedInput.value = '';

    // Limpa entrega
    deliveryAddress = null;
    deliveryBtn.classList.remove('has-delivery');
    deliveryBtn.innerHTML = '<i class="fas fa-truck"></i> Adicionar Entrega';
    const deliveryInfo = document.querySelector('.delivery-info');
    if (deliveryInfo) deliveryInfo.remove();

    // Limpa resultado de busca de clientes, se houver
    const clientSearchResults = document.getElementById('client-search-results');
    if (clientSearchResults) {
        clientSearchResults.innerHTML = '';
        clientSearchResults.style.display = 'none';
    }

    // Limpa resultado de busca de produtos, se houver
    const productSearchResults = document.getElementById('product-search-results');
    if (productSearchResults) {
        productSearchResults.innerHTML = '';
        productSearchResults.style.display = 'none';
    }

    // Limpa os campos de busca
    const clientSearchInput = document.getElementById('client-search-input');
    const productSearchInput = document.getElementById('product-search-input');
    if (clientSearchInput) clientSearchInput.value = '';
    if (productSearchInput) productSearchInput.value = '';

    // Fecha todos os dropdowns de busca
    closeAllDropdowns();

    // Atualiza total (vai zerar todos os valores)
    calculateSaleTotal();

    // Atualiza status do caixa
    if (typeof updateCaixaStatus === 'function') {
        updateCaixaStatus();
    }

    // Dispara evento de input para garantir a atualização do status
    const event = new Event('input', {
        bubbles: true,
        cancelable: true,
    });
    selectedClientInput.dispatchEvent(event);
}

// ==================== FUNÇÕES DE CAIXA ====================
async function checkCaixaStatus() {
    try {
        const response = await fetch('/operador/api/saldo', {
            ...preventCacheConfig,
            method: 'GET'
        });
        if (!response.ok) throw new Error('Erro ao verificar status do caixa');
        
        const data = await response.json();
        
        if (data.message === 'Nenhum caixa aberto encontrado') {
            closeRegisterBtn.style.display = 'none';
            currentCaixaId = null;
        } else {
            closeRegisterBtn.style.display = 'block';
            currentCaixaId = data.caixa_id;
            updateBalance(true); // Forçar atualização sem cache
        }
    } catch (error) {
        console.error('Error checking caixa status:', error);
    }
}

async function updateBalance(forceUpdate = false) {
    try {
        const url = forceUpdate 
            ? `/operador/api/saldo?timestamp=${new Date().getTime()}`
            : '/operador/api/saldo';
            
        const response = await fetch(url, {
            ...preventCacheConfig,
            method: 'GET'
        });
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

async function closeRegister() {
    const valorFechamento = prompt('Informe o valor de fechamento do caixa:');
    if (!valorFechamento || isNaN(valorFechamento)) {
        return showMessage('Valor de fechamento inválido', 'error');
    }

    if (confirm('Deseja realmente fechar o caixa?')) {
        try {
            const response = await fetch('/operador/api/fechar-caixa', {
                ...preventCacheConfig,
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

// ==================== FUNÇÕES UTILITÁRIAS ====================
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

function formatCurrency(value) {
    const parsed = Number(
        typeof value === 'string'
            ? value.replace(',', '.')
            : value
    );
    
    if (isNaN(parsed)) return 'R$ 0,00';

    return 'R$ ' + parsed.toFixed(2)
        .replace('.', ',')
        .replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

function switchTab(tabId) {
    tabBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabId));
    tabContents.forEach(content => content.classList.toggle('active', content.id === tabId));
    
    const activeTabBtn = document.querySelector(`.menu-item[data-tab="${tabId}"]`);
    if (activeTabBtn) {
        currentTabTitle.textContent = activeTabBtn.querySelector('span').textContent;
    }
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

function showMessage(message, type = 'success') {
    notification.className = `notification ${type} show`;
    notificationMessage.textContent = message;
    
    const icon = notification.querySelector('.notification-icon i');
    icon.className = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    
    setTimeout(() => notification.classList.remove('show'), 5000);
}

// Função para forçar recarregamento sem cache em todas as requisições
function forceNoCacheFetch(url, options = {}) {
    const timestamp = new Date().getTime();
    const separator = url.includes('?') ? '&' : '?';
    const noCacheUrl = `${url}${separator}_=${timestamp}`;
    
    return fetch(noCacheUrl, {
        ...options,
        headers: {
            ...options.headers,
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    });
}