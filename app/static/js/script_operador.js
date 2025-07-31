/**
 * SISTEMA DE CAIXA - OPERADOR
 * Arquivo completo com todas as funcionalidades do sistema de caixa
 * Documentado para fácil manutenção e atualização futura
 */

// ==================== VARIÁVEIS GLOBAIS ====================
/**
 * Variáveis de estado do sistema
 * @type {boolean} balanceVisible - Controla a visibilidade do saldo
 * @type {number} currentBalance - Armazena o saldo atual do caixa
 * @type {Array} clients - Lista de clientes cadastrados
 * @type {Array} products - Lista de produtos disponíveis
 * @type {Object|null} currentEditingClient - Cliente em edição
 * @type {Object|null} selectedClient - Cliente selecionado para venda
 * @type {Array} selectedProducts - Produtos selecionados para venda
 * @type {Object|null} deliveryAddress - Endereço de entrega
 * @type {number|null} currentCaixaId - ID do caixa aberto
 * @type {Object|null} currentUser - Dados do usuário logado
 */
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

// ==================== ELEMENTOS DOM ====================
/**
 * Seleção de todos os elementos DOM necessários
 * Cada grupo está documentado conforme sua função no sistema
 */

// Elementos de saldo e data
const openingBalanceLabel = document.getElementById('opening-balance')?.querySelector('.balance-value');
const currentBalanceLabel = document.getElementById('current-balance')?.querySelector('.balance-value');
const currentDateElement = document.getElementById('current-date');
const toggleBalanceBtn = document.getElementById('toggle-balance');

// Elementos de navegação por abas
const tabBtns = document.querySelectorAll('.menu-item');
const tabContents = document.querySelectorAll('.tab-content');
const currentTabTitle = document.getElementById('current-tab-title');

// Elementos de produtos e vendas
const productsList = document.getElementById('products-list');
const productSearchInput = document.getElementById('product-search-input');
const addProductBtn = document.getElementById('add-product-btn');
const registerSaleBtn = document.getElementById('register-sale-btn');
const saleTotalElement = document.getElementById('sale-total');
const subtotalValueElement = document.getElementById('subtotal-value');
const changeValueElement = document.getElementById('change-value');
const amountReceivedInput = document.getElementById('amount-received');

// Elementos de clientes
const clientSearchInput = document.getElementById('client-search-input');
const selectedClientInput = document.getElementById('selected-client');
const selectedClientIdInput = document.getElementById('selected-client-id');
const clientSearch = document.getElementById('client-search');
const searchClientBtn = document.getElementById('search-client-btn');

// Elementos modais
const clientModal = document.getElementById('client-modal');
const clientModalTitle = document.getElementById('client-modal-title');
const clientForm = document.getElementById('client-form');
const modalCloses = document.querySelectorAll('.modal-close, #cancel-client');
const productSearchModal = document.getElementById('product-search-modal');
const modalProductSearch = document.getElementById('modal-product-search');
const productSearchResults = document.getElementById('product-search-results');

// Elementos de entrega
const deliveryBtn = document.getElementById('delivery-btn');
const useClientAddressBtn = document.getElementById('use-client-address-btn');
const deliveryModal = document.getElementById('delivery-modal');
const saveDeliveryBtn = document.getElementById('save-delivery');
const cancelDeliveryBtn = document.getElementById('cancel-delivery');

// Elementos de despesas
const openExpenseModalBtn = document.getElementById('open-expense-modal-btn');
const expenseModal = document.getElementById('expense-modal');
const expenseForm = document.getElementById('expense-form');
const cancelExpenseBtn = document.getElementById('cancel-expense');
const saveExpenseBtn = document.getElementById('save-expense');

// Outros elementos
const closeRegisterBtn = document.getElementById('close-register-btn');
const logoutBtn = document.getElementById('logout-btn');
const notification = document.getElementById('notification');
const notificationMessage = document.getElementById('notification-message');

// ==================== CONFIGURAÇÕES ====================
/**
 * Configuração para prevenir cache nas requisições
 * @type {Object}
 */
const preventCacheConfig = {
    headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
};

// ==================== INICIALIZAÇÃO ====================
/**
 * Inicializa o sistema quando o DOM estiver completamente carregado
 * Carrega dados iniciais e configura event listeners
 */
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Aguarda breve momento para garantir que todos os elementos estejam disponíveis
        await new Promise(resolve => setTimeout(resolve, 100));
        
        updateCurrentDate();
        await loadCurrentUser();
        await loadClients();
        await loadProducts();
        await checkCaixaStatus();
        setupEventListeners();

        // Atualizações periódicas
        setInterval(() => loadProducts(true), 10000);
        setInterval(() => updateBalance(true), 10000);
    } catch (error) {
        console.error('Erro na inicialização:', error);
        showMessage('Erro ao inicializar o sistema', 'error');
    }
});

// ==================== FUNÇÕES DE USUÁRIO ====================
/**
 * Carrega os dados do usuário logado
 * @async
 */
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

// ==================== FUNÇÕES DE CLIENTES ====================
/**
 * Carrega a lista de clientes do servidor
 * @async
 */
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

/**
 * Busca clientes com base em um termo de pesquisa
 * @async
 * @param {string} searchTerm - Termo para busca
 */
async function searchClient() {
    const searchTerm = clientSearchInput?.value.trim();
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

/**
 * Seleciona um cliente para a venda atual
 * @param {Object} client - Cliente selecionado
 */
function selectClient(client) {
    if (!client || !selectedClientInput || !selectedClientIdInput) return;
    
    selectedClient = client;
    selectedClientInput.value = client.nome;
    selectedClientIdInput.value = client.id;
    showMessage(`Cliente selecionado: ${client.nome}`);
    updateCaixaStatus();
}

/**
 * Exibe resultados da busca de clientes
 * @param {Array} clients - Lista de clientes encontrados
 */
function showClientSearchResults(clients) {
    if (clients.length > 0) {
        selectClient(clients[0]);
    }
}

/**
 * Renderiza os cards de clientes na interface
 * @param {Array|null} [filteredClients=null] - Lista filtrada de clientes (opcional)
 */
function renderClientCards(filteredClients = null) {
    const container = document.getElementById('clients-container');
    if (!container) return;
    
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

/**
 * Abre o modal para cadastro de novo cliente
 */
function openClientModal() {
    if (!clientModalTitle || !clientForm) return;
    
    currentEditingClient = null;
    clientModalTitle.textContent = 'Cadastrar Cliente';
    clientForm.reset();
    openModal('client');
}

/**
 * Preenche o modal com dados do cliente para edição
 * @param {string} clientId - ID do cliente a ser editado
 */
function editClient(clientId) {
    const client = clients.find(c => c.id == clientId);
    if (!client || !clientModalTitle) return;
    
    currentEditingClient = client;
    clientModalTitle.textContent = 'Editar Cliente';
    
    document.getElementById('client-name').value = client.nome;
    document.getElementById('client-document').value = client.documento || '';
    document.getElementById('client-phone').value = client.telefone || '';
    document.getElementById('client-email').value = client.email || '';
    document.getElementById('client-address').value = client.endereco || '';
    
    openModal('client');
}

/**
 * Salva os dados do cliente (novo ou edição)
 * @async
 */
async function saveClient() {
    if (!clientForm) return;
    
    const clientData = {
        nome: document.getElementById('client-name')?.value,
        documento: document.getElementById('client-document')?.value,
        telefone: document.getElementById('client-phone')?.value,
        email: document.getElementById('client-email')?.value,
        endereco: document.getElementById('client-address')?.value
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
/**
 * Carrega a lista de produtos do servidor
 * @async
 * @param {boolean} [forceUpdate=false] - Força atualização sem cache
 */
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

/**
 * Abre o modal de busca de produtos
 */
function openProductSearchModal() {
    const searchTerm = productSearchInput?.value.trim();
    if (searchTerm && modalProductSearch) {
        modalProductSearch.value = searchTerm;
    }
    openModal('product-search');
    searchProductsInModal();
}

/**
 * Busca produtos dentro do modal de busca
 */
function searchProductsInModal() {
    if (!modalProductSearch || !productSearchResults) return;
    
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

/**
 * Exibe os resultados da busca de produtos no modal
 * @param {Array} products - Lista de produtos encontrados
 */
function displayProductSearchResults(products) {
    if (!productSearchResults) return;
    
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

/**
 * Adiciona um produto à lista de venda
 * @param {Object} product - Produto a ser adicionado
 */
function addProductToSale(product) {
    if (!product) return;
    
    const existingProductIndex = selectedProducts.findIndex(p => p.id === product.id);
    
    if (existingProductIndex >= 0) {
        selectedProducts[existingProductIndex].quantity += 1;
    } else {
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

/**
 * Renderiza la lista de productos seleccionados para la venta
 */
function renderProductsList() {
    if (!productsList) return;
    
    productsList.innerHTML = '';
    
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

/**
 * Atualiza a quantidade de um produto na lista de venda
 * @param {HTMLInputElement} input - Campo de quantidade
 */
function updateProductQuantity(input) {
    const index = parseInt(input.dataset.index);
    const newQuantity = parseInt(input.value);
    
    if (index >= 0 && index < selectedProducts.length && !isNaN(newQuantity) && newQuantity > 0) {
        selectedProducts[index].quantity = newQuantity;
    }
}

/**
 * Remove um produto da lista de venda
 * @param {HTMLButtonElement} button - Botão de remoção
 */
function removeProductRow(button) {
    const index = parseInt(button.dataset.index);
    if (index >= 0 && index < selectedProducts.length) {
        selectedProducts.splice(index, 1);
        renderProductsList();
    }
}

/**
 * Adiciona uma linha vazia para seleção de produto
 */
function addEmptyProductRow() {
    openProductSearchModal();
}

// ==================== FUNÇÕES DE VENDA ====================
/**
 * Registra uma nova venda no sistema
 * @async
 */
async function registerSale() {
    if (!selectedClientIdInput?.value) {
        showMessage('Selecione um cliente', 'error');
        return;
    }
    
    if (selectedProducts.length === 0) {
        showMessage('Adicione pelo menos um produto', 'error');
        return;
    }
    
    const paymentMethod = document.getElementById('payment-method')?.value;
    if (!paymentMethod) {
        showMessage('Selecione a forma de pagamento', 'error');
        return;
    }
    
    const notes = document.getElementById('sale-notes')?.value;
    const amountReceived = parseFloat(amountReceivedInput?.value) || 0;
    const totalText = saleTotalElement?.textContent.replace('R$ ', '').replace('.', '').replace(',', '.');
    const total = parseFloat(totalText) || 0;
    
    if (paymentMethod !== 'a_prazo' && amountReceived < total) {
        showMessage('Valor recebido menor que o total da venda', 'error');
        return;
    }
    
    const items = selectedProducts.map(product => ({
        produto_id: product.id,
        quantidade: Number(product.quantity),
        valor_unitario: Number(product.price),
        valor_total: Number(product.price * product.quantity)
    }));

    const saleData = {
        cliente_id: parseInt(selectedClientIdInput.value),
        forma_pagamento: paymentMethod,
        valor_recebido: amountReceived,
        itens: items,
        observacao: notes
    };

    if (deliveryAddress) {
        saleData.endereco_entrega = {
            logradouro: deliveryAddress.logradouro || null,
            numero: deliveryAddress.numero || null,
            complemento: deliveryAddress.complemento || null,
            bairro: deliveryAddress.bairro || null,
            cidade: deliveryAddress.cidade || null,
            estado: deliveryAddress.estado || null,
            cep: deliveryAddress.cep || null,
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
        
        resetSaleForm();
        
        await updateBalance(true);
        await loadProducts(true);
        
        showMessage('Registrando venda...');
        showMessage(`Venda registrada com sucesso! Nº Nota: ${result.nota_id}`);
        showMessage('Gerando comprovante...');
        
        window.open(`/operador/pdf/nota/${result.nota_id}?timestamp=${new Date().getTime()}`, '_blank');
    } catch (error) {
        console.error("Erro ao registrar venda:", error);
        showMessage(error.message, 'error');
    }
}

/**
 * Calcula o total da venda com base nos produtos selecionados
 */
function calculateSaleTotal() {
    let subtotal = 0;
    
    selectedProducts.forEach((product, index) => {
        const totalValue = product.price * product.quantity;
        subtotal += totalValue;
        
        if (productsList && productsList.children[index]) {
            const row = productsList.children[index];
            const totalCell = row.querySelector('.product-total');
            if (totalCell) {
                totalCell.textContent = formatCurrency(totalValue);
            }
        }
    });
    
    let total = subtotal;
    let change = 0;
    const amountReceived = parseFloat(amountReceivedInput?.value) || 0;
    
    if (amountReceived > 0) {
        change = Math.max(0, amountReceived - total);
    }
    
    if (subtotalValueElement) subtotalValueElement.textContent = formatCurrency(subtotal);
    if (saleTotalElement) saleTotalElement.textContent = formatCurrency(total);
    if (changeValueElement) changeValueElement.textContent = formatCurrency(change);
}

/**
 * Reseta completamente o formulário de venda
 */
function resetSaleForm() {
    try {
        // Limpa cliente
        const selectedClientInput = document.getElementById('selected-client');
        const selectedClientIdInput = document.getElementById('selected-client-id');
        
        if (selectedClientInput) selectedClientInput.value = '';
        if (selectedClientIdInput) selectedClientIdInput.value = '';

        // Limpa produtos
        if (productsList) productsList.innerHTML = '';
        selectedProducts = [];

        // Limpa pagamento
        const paymentMethod = document.getElementById('payment-method');
        if (paymentMethod) paymentMethod.value = '';
        
        const saleNotes = document.getElementById('sale-notes');
        if (saleNotes) saleNotes.value = '';
        
        if (amountReceivedInput) amountReceivedInput.value = '';

        // Limpa entrega
        deliveryAddress = null;
        const deliveryBtn = document.getElementById('delivery-btn');
        if (deliveryBtn) {
            deliveryBtn.classList.remove('has-delivery');
            deliveryBtn.innerHTML = '<i class="fas fa-truck"></i> Adicionar Entrega';
        }
        
        const deliveryInfo = document.querySelector('.delivery-info');
        if (deliveryInfo) deliveryInfo.remove();

        // Limpa totais
        if (subtotalValueElement) subtotalValueElement.textContent = 'R$ 0.00';
        if (saleTotalElement) saleTotalElement.textContent = 'R$ 0.00';
        if (changeValueElement) changeValueElement.textContent = 'R$ 0.00';

        // Atualiza status
        updateCaixaStatus();

        // Dispara evento se necessário
        if (selectedClientInput) {
            const event = new Event('input', { bubbles: true, cancelable: true });
            selectedClientInput.dispatchEvent(event);
        }
    } catch (error) {
        console.error("Erro ao resetar formulário de venda:", error);
    }
}

// ==================== FUNÇÕES DE ENTREGA ====================
/**
 * Abre o modal de cadastro de endereço de entrega
 */
function openDeliveryModal() {
    if (!deliveryModal) return;
    
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

/**
 * Salva o endereço de entrega
 */
function saveDeliveryAddress() {
    // Remova as validações obrigatórias
    deliveryAddress = {
        logradouro: document.getElementById('delivery-address')?.value || '',
        numero: document.getElementById('delivery-number')?.value || '',
        complemento: document.getElementById('delivery-complement')?.value || '',
        bairro: document.getElementById('delivery-neighborhood')?.value || '',
        cidade: document.getElementById('delivery-city')?.value || '',
        estado: document.getElementById('delivery-state')?.value || '',
        cep: document.getElementById('delivery-zipcode')?.value || '',
        instrucoes: document.getElementById('delivery-instructions')?.value || '',
        endereco_completo: `${document.getElementById('delivery-address')?.value || ''}, ${document.getElementById('delivery-number')?.value || ''}`
    };
    
    updateDeliveryUI();
    closeModal();
    showMessage('Endereço de entrega salvo com sucesso!');
}

/**
 * Função para capturar e processar o endereço do cliente selecionado
 */
function useClientAddress() {
    if (!selectedClientIdInput || !selectedClientIdInput.value) {
        showMessage('Nenhum cliente selecionado', 'error');
        return;
    }

    const clientId = selectedClientIdInput.value;
    const client = clients.find(c => c.id == clientId);
    
    if (!client || (!client.endereco && !client.endereco_completo)) {
        showMessage('Cliente não possui endereço cadastrado', 'error');
        return;
    }

    // Verifica se já existe um endereço estruturado no cliente
    if (client.logradouro && client.numero && client.bairro && client.cidade && client.estado) {
        deliveryAddress = {
            logradouro: client.logradouro,
            numero: client.numero,
            complemento: client.complemento || '',
            bairro: client.bairro,
            cidade: client.cidade,
            estado: client.estado,
            cep: client.cep || '',
            instrucoes: '',
            endereco_completo: `${client.logradouro}, ${client.numero}, ${client.bairro}, ${client.cidade}-${client.estado}`
        };
    } else {
        // Caso o endereço esteja em uma string única
        const addressString = client.endereco || client.endereco_completo;
        const addressRegex = /^(.*?)(?:,\s*(?:nº|no|numero|número)\s*(\d+))?(?:,\s*(.*?))?(?:,\s*(.*?)\s*-\s*([A-Z]{2}))?$/i;
        const matches = addressString.match(addressRegex);
        
        deliveryAddress = {
            endereco_completo: addressString,
            logradouro: matches[1]?.trim() || '',
            numero: matches[2]?.trim() || '',
            complemento: '',
            bairro: matches[3]?.trim() || '',
            cidade: matches[4]?.trim() || '',
            estado: matches[5]?.trim() || '',
            cep: '',
            instrucoes: ''
        };

        // Fallback para extrair cidade/estado
        if (!deliveryAddress.cidade && !deliveryAddress.estado && matches[3]) {
            const cityStateMatch = matches[3].match(/(.*?)\s*-\s*([A-Z]{2})$/i);
            if (cityStateMatch) {
                deliveryAddress.bairro = '';
                deliveryAddress.cidade = cityStateMatch[1]?.trim() || '';
                deliveryAddress.estado = cityStateMatch[2]?.trim() || '';
            }
        }
    }

    updateDeliveryUI();
    showMessage('Endereço do cliente definido para entrega!');
}

/**
 * Atualiza a interface com as informações de entrega
 */
function updateDeliveryUI() {
    if (!deliveryAddress) return;
    
    // Atualiza o botão de entrega
    if (deliveryBtn) {
        deliveryBtn.classList.add('has-delivery');
        deliveryBtn.innerHTML = '<i class="fas fa-check-circle"></i> Endereço de Entrega Cadastrado';
    }
    
    // Exibe as informações de entrega
    showDeliveryInfo();
}

/**
 * Exibe as informações de entrega na interface
 */
function showDeliveryInfo() {
    if (!deliveryBtn || !deliveryAddress) return;
    
    // Remove qualquer informação de entrega existente
    const existingInfo = document.querySelector('.delivery-info');
    if (existingInfo) existingInfo.remove();
    
    // Cria o elemento com as informações de entrega
    const deliveryInfo = document.createElement('div');
    deliveryInfo.className = 'delivery-info';
    deliveryInfo.innerHTML = `
        <p><strong>Endereço de Entrega:</strong></p>
        <p>${deliveryAddress.logradouro}, ${deliveryAddress.numero}${deliveryAddress.complemento ? ', ' + deliveryAddress.complemento : ''}</p>
        <p>${deliveryAddress.bairro} - ${deliveryAddress.cidade}/${deliveryAddress.estado}</p>
        ${deliveryAddress.cep ? `<p>CEP: ${deliveryAddress.cep}</p>` : ''}
        ${deliveryAddress.instrucoes ? `<p><strong>Instruções:</strong> ${deliveryAddress.instrucoes}</p>` : ''}
        <div class="delivery-actions">
            <button class="btn-edit-delivery" id="edit-delivery-btn">
                <i class="fas fa-edit"></i> Editar Endereço
            </button>
            <button class="btn-remove-delivery" id="remove-delivery-btn">
                <i class="fas fa-trash"></i> Remover
            </button>
        </div>
    `;
    
    // Insere após o botão de entrega
    deliveryBtn.insertAdjacentElement('afterend', deliveryInfo);
    
    // Adiciona os event listeners aos botões
    document.getElementById('edit-delivery-btn')?.addEventListener('click', openDeliveryModal);
    document.getElementById('remove-delivery-btn')?.addEventListener('click', removeDeliveryAddress);
}

/**
 * Remove o endereço de entrega
 */
function removeDeliveryAddress() {
    deliveryAddress = null;
    
    // Remove a classe e restaura o ícone do botão
    if (deliveryBtn) {
        deliveryBtn.classList.remove('has-delivery');
        deliveryBtn.innerHTML = '<i class="fas fa-truck"></i> Adicionar Entrega';
    }
    
    // Remove o bloco de informações de entrega
    const deliveryInfo = document.querySelector('.delivery-info');
    if (deliveryInfo) {
        deliveryInfo.remove();
    }
    
    showMessage('Endereço de entrega removido');
}

// ==================== FUNÇÕES DE DESPESAS ====================
/**
 * Abre o modal de cadastro de despesas
 */
function openExpenseModal() {
    if (!expenseModal || !currentCaixaId) {
        showMessage('Nenhum caixa aberto encontrado', 'error');
        return;
    }
    
    expenseModal.style.display = 'flex';
    document.getElementById('expense-description')?.focus();
}

/**
 * Fecha o modal de despesas
 */
function closeExpenseModal() {
    if (!expenseModal || !expenseForm) return;
    
    expenseModal.style.display = 'none';
    expenseForm.reset();
}

/**
 * Registra uma nova despesa no sistema
 * @async
 */
async function saveExpense() {
    const description = document.getElementById('expense-description')?.value.trim();
    const amount = document.getElementById('expense-amount')?.value;
    const note = document.getElementById('expense-note')?.value.trim();
    
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
        updateBalance(true);
    } catch (error) {
        showMessage(error.message, 'error');
        console.error('Erro ao salvar despesa:', error);
    }
}

// ==================== FUNÇÕES DE CAIXA ====================
/**
 * Verifica o status atual do caixa (aberto/fechado)
 * @async
 */
async function checkCaixaStatus() {
    try {
        const response = await fetch('/operador/api/saldo', {
            ...preventCacheConfig,
            method: 'GET'
        });
        if (!response.ok) throw new Error('Erro ao verificar status do caixa');
        
        const data = await response.json();
        
        if (data.message === 'Nenhum caixa aberto encontrado') {
            if (closeRegisterBtn) closeRegisterBtn.style.display = 'none';
            currentCaixaId = null;
        } else {
            if (closeRegisterBtn) closeRegisterBtn.style.display = 'block';
            currentCaixaId = data.caixa_id;
            updateBalance(true);
        }
    } catch (error) {
        console.error('Error checking caixa status:', error);
    }
}

/**
 * Atualiza o saldo do caixa na interface
 * @async
 * @param {boolean} [forceUpdate=false] - Força atualização sem cache
 */
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
            if (openingBalanceLabel) openingBalanceLabel.textContent = 'Caixa fechado';
            if (currentBalanceLabel) currentBalanceLabel.textContent = '';
            return;
        }

        if (balanceVisible) {
            if (openingBalanceLabel) openingBalanceLabel.textContent = formatCurrency(data.valor_abertura);
            if (currentBalanceLabel) currentBalanceLabel.textContent = data.saldo_formatado || 'R$ 0,00';
        } else {
            if (openingBalanceLabel) openingBalanceLabel.textContent = '******';
            if (currentBalanceLabel) currentBalanceLabel.textContent = '******';
        }
    } catch (error) {
        console.error('Error updating balance:', error);
        if (openingBalanceLabel) openingBalanceLabel.textContent = 'Erro';
        if (currentBalanceLabel) currentBalanceLabel.textContent = '';
    }
}

/**
 * Fecha o caixa atual
 * @async
 */
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

/**
 * Atualiza o status visual do caixa (livre/em operação)
 */
window.updateCaixaStatus = function() {
    const caixaStatusDisplay = document.querySelector('.caixa-status');
    if (!caixaStatusDisplay || !selectedClientInput) return;
    
    if (selectedClientInput.value.trim() !== '') {
        caixaStatusDisplay.className = 'caixa-status caixa-operacao';
        caixaStatusDisplay.innerHTML = '<i class="fas fa-user-check"></i><span>CAIXA EM OPERAÇÃO</span>';
    } else {
        caixaStatusDisplay.className = 'caixa-status caixa-livre';
        caixaStatusDisplay.innerHTML = '<i class="fas fa-check-circle"></i><span>CAIXA LIVRE</span>';
    }
};

// ==================== FUNÇÕES DE BUSCA DINÂMICA ====================
/**
 * Variáveis para controle dos timeouts de busca
 */
let clientSearchTimeout;
let productSearchTimeout;
let activeSearchDropdown = null;

/**
 * Exibe resultados de busca em um dropdown
 * @param {Array} results - Resultados da busca
 * @param {string} containerId - ID do container de resultados
 * @param {string} type - Tipo de busca ('client' ou 'product')
 */
function showSearchResults(results, containerId, type) {
    const resultsContainer = document.getElementById(containerId);
    if (!resultsContainer) return;
    
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
                if (clientSearchInput) clientSearchInput.value = '';
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
                if (productSearchInput) productSearchInput.value = '';
            });
        }
        
        resultsContainer.appendChild(resultItem);
    });

    resultsContainer.style.display = 'block';
    activeSearchDropdown = resultsContainer;
}

/**
 * Busca clientes dinamicamente
 * @async
 * @param {string} searchTerm - Termo para busca
 */
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

/**
 * Busca produtos dinamicamente
 * @async
 * @param {string} searchTerm - Termo para busca
 */
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

/**
 * Fecha todos os dropdowns de busca
 */
function closeAllDropdowns() {
    document.querySelectorAll('.search-results-dropdown').forEach(dropdown => {
        dropdown.style.display = 'none';
    });
    activeSearchDropdown = null;
}

// ==================== FUNÇÕES UTILITÁRIAS ====================
/**
 * Atualiza a data e hora atual na interface
 */
function updateCurrentDate() {
    const now = new Date();
    if (currentDateElement) {
        currentDateElement.textContent = now.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

/**
 * Alterna a visibilidade do saldo
 */
function toggleBalance() {
    balanceVisible = !balanceVisible;
    updateBalance();
    if (toggleBalanceBtn) {
        toggleBalanceBtn.innerHTML = balanceVisible ? '<i class="fas fa-eye-slash"></i>' : '<i class="fas fa-eye"></i>';
    }
}

/**
 * Formata um valor numérico como moeda (R$)
 * @param {number|string} value - Valor a ser formatado
 * @returns {string} Valor formatado como moeda
 */
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

/**
 * Alterna entre as abas da interface
 * @param {string} tabId - ID da aba a ser ativada
 */
function switchTab(tabId) {
    tabBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabId));
    tabContents.forEach(content => content.classList.toggle('active', content.id === tabId));
    
    const activeTabBtn = document.querySelector(`.menu-item[data-tab="${tabId}"]`);
    if (activeTabBtn && currentTabTitle) {
        const span = activeTabBtn.querySelector('span');
        if (span) currentTabTitle.textContent = span.textContent;
    }
}

/**
 * Abre um modal específico
 * @param {string} type - Tipo do modal ('client', 'product-search', 'delivery', etc.)
 */
function openModal(type) {
    const modal = document.getElementById(`${type}-modal`);
    if (modal) modal.style.display = 'flex';
}

/**
 * Fecha todos os modais abertos
 */
function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

/**
 * Exibe uma mensagem de notificação na interface
 * @param {string} message - Mensagem a ser exibida
 * @param {string} [type='success'] - Tipo da mensagem ('success' ou 'error')
 */
function showMessage(message, type = 'success') {
    if (!notification || !notificationMessage) return;
    
    notification.className = `notification ${type} show`;
    notificationMessage.textContent = message;
    
    const icon = notification.querySelector('.notification-icon i');
    if (icon) {
        icon.className = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    }
    
    setTimeout(() => notification.classList.remove('show'), 5000);
}

/**
 * Força requisições sem cache
 * @param {string} url - URL da requisição
 * @param {Object} [options={}] - Opções adicionais para fetch
 * @returns {Promise} Promise da requisição fetch
 */
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

// ==================== CONFIGURAÇÃO DE EVENT LISTENERS ====================
/**
 * Configura todos os event listeners da aplicação
 */
function setupEventListeners() {
    // Event listeners básicos
    if (toggleBalanceBtn) toggleBalanceBtn.addEventListener('click', toggleBalance);
    
    if (tabBtns) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => switchTab(btn.dataset.tab));
        });
    }
    
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            window.location.href = '/logout?' + new Date().getTime();
        });
    }
    
    // Event listeners de clientes
    const searchClientBtn = document.getElementById('search-client-btn');
    if (searchClientBtn) searchClientBtn.addEventListener('click', searchClient);
    
    if (clientSearchInput) {
        clientSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchClient();
        });
    }
    
    const addClientBtn = document.getElementById('add-client-btn');
    if (addClientBtn) addClientBtn.addEventListener('click', openClientModal);
    
    // Event listeners de produtos
    const searchProductBtn = document.getElementById('search-product-btn');
    if (searchProductBtn) searchProductBtn.addEventListener('click', openProductSearchModal);
    
    if (productSearchInput) {
        productSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') openProductSearchModal();
        });
    }
    
    if (addProductBtn) addProductBtn.addEventListener('click', addEmptyProductRow);
    
    // Event listeners modais
    if (modalCloses) {
        modalCloses.forEach(btn => {
            btn.addEventListener('click', closeModal);
        });
    }
    
    const saveClientBtn = document.getElementById('save-client');
    if (saveClientBtn) saveClientBtn.addEventListener('click', saveClient);
    
    // Event listeners de venda
    if (registerSaleBtn) registerSaleBtn.addEventListener('click', registerSale);
    if (closeRegisterBtn) closeRegisterBtn.addEventListener('click', closeRegister);
    
    if (productsList) {
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
    }
    
    if (amountReceivedInput) {
        amountReceivedInput.addEventListener('input', calculateSaleTotal);
    }
    
    // Event listeners de entrega
    if (useClientAddressBtn) {
        useClientAddressBtn.addEventListener('click', useClientAddress);
    }
    
    if (deliveryBtn) {
        deliveryBtn.addEventListener('click', openDeliveryModal);
    }
    
    if (saveDeliveryBtn) {
        saveDeliveryBtn.addEventListener('click', saveDeliveryAddress);
    }
    
    if (cancelDeliveryBtn) {
        cancelDeliveryBtn.addEventListener('click', closeModal);
    }
    
    // Event listeners de busca dinâmica
    if (clientSearchInput) {
        clientSearchInput.addEventListener('input', function(e) {
            clearTimeout(clientSearchTimeout);
            const searchTerm = e.target.value.trim();
            
            if (searchTerm.length >= 2) {
                clientSearchTimeout = setTimeout(() => {
                    searchClients(searchTerm);
                }, 300);
            } else if (searchTerm.length === 0) {
                searchClients('');
            } else {
                closeAllDropdowns();
            }
        });
        
        clientSearchInput.addEventListener('focus', async function() {
            await searchClients('');
        });
    }
    
    if (productSearchInput) {
        productSearchInput.addEventListener('input', function(e) {
            clearTimeout(productSearchTimeout);
            const searchTerm = e.target.value.trim();
            
            if (searchTerm.length >= 2) {
                productSearchTimeout = setTimeout(() => {
                    searchProducts(searchTerm);
                }, 300);
            } else if (searchTerm.length === 0) {
                searchProducts('');
            } else {
                closeAllDropdowns();
            }
        });
        
        productSearchInput.addEventListener('focus', function() {
            if (productSearchInput.value.trim().length >= 2) {
                searchProducts(productSearchInput.value.trim());
            } else {
                searchProducts('');
            }
        });
    }
    
    // Event listeners globais
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-container') && activeSearchDropdown) {
            closeAllDropdowns();
        }
    });
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && activeSearchDropdown) {
            closeAllDropdowns();
        }
    });
    
    // Event listener para remover cliente selecionado
    const removeClientBtn = document.getElementById("remove-selected-client-btn");
    if (removeClientBtn) {
        removeClientBtn.addEventListener("click", function() {
            if (selectedClientInput) selectedClientInput.value = "";
            if (selectedClientIdInput) selectedClientIdInput.value = "";
            updateCaixaStatus();
        });
    }
}

// ==================== INICIALIZAÇÃO ADICIONAL ====================
/**
 * Configura listeners adicionais após o carregamento do DOM
 */
document.addEventListener('DOMContentLoaded', function() {
    // Configuração adicional para busca dinâmica
    const modalSearchProductBtn = document.getElementById('modal-search-product-btn');
    if (modalSearchProductBtn) {
        modalSearchProductBtn.addEventListener('click', searchProductsInModal);
    }
    
    if (modalProductSearch) {
        modalProductSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchProductsInModal();
        });
    }
    
    const cancelProductSearchBtn = document.getElementById('cancel-product-search');
    if (cancelProductSearchBtn) {
        cancelProductSearchBtn.addEventListener('click', () => {
            closeModal();
            if (productSearchInput) productSearchInput.value = '';
        });
    }
    
    // Configuração de despesas
    if (openExpenseModalBtn) openExpenseModalBtn.addEventListener('click', openExpenseModal);
    if (cancelExpenseBtn) cancelExpenseBtn.addEventListener('click', closeExpenseModal);
    if (saveExpenseBtn) saveExpenseBtn.addEventListener('click', saveExpense);
});