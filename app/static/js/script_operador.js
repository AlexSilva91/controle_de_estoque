// ==================== VARIÁVEIS GLOBAIS ====================
let balanceVisible = true;
let currentBalance = 0;
let clients = [];
let filteredClients = [];
let currentSort = { field: 'nome', direction: 'asc' };
let currentFilter = 'all';
let products = [];
let currentEditingClient = null;
let selectedClient = null;
let selectedProducts = [];
let deliveryAddress = null;
let currentCaixaId = null;
let currentUser = null;
let activeSearchDropdown = null;
let clientSearchTimeout;
let productSearchTimeout;
let currentOpenModal = null;
let balanceUpdateInterval = null;

// ==================== ELEMENTOS DOM ====================
const openingBalanceLabel = document.getElementById('opening-balance')?.querySelector('.balance-value');
const currentBalanceLabel = document.getElementById('current-balance')?.querySelector('.balance-value');
const currentDateElement = document.getElementById('current-date');
const toggleBalanceBtn = document.getElementById('toggle-balance');
const tabBtns = document.querySelectorAll('.menu-item');
const tabContents = document.querySelectorAll('.tab-content');
const currentTabTitle = document.getElementById('current-tab-title');
const productsList = document.getElementById('products-list');
const productSearchInput = document.getElementById('product-search-input');
const addProductBtn = document.getElementById('add-product-btn');
const registerSaleBtn = document.getElementById('register-sale-btn');
const saleTotalElement = document.getElementById('sale-total');
const subtotalValueElement = document.getElementById('subtotal-value');
const changeValueElement = document.getElementById('change-value');
const amountReceivedInput = document.getElementById('amount-received');
const clientSearchInput = document.getElementById('client-search-input');
const selectedClientInput = document.getElementById('selected-client');
const selectedClientIdInput = document.getElementById('selected-client-id');
const daySalesContent = document.getElementById('day-sales');
const clientSearch = document.getElementById('client-search');
const searchClientBtn = document.getElementById('search-client-btn');
const clientModal = document.getElementById('client-modal');
const clientModalTitle = document.getElementById('client-modal-title');
const clientForm = document.getElementById('client-form');
const modalCloses = document.querySelectorAll('.modal-close, #cancel-client');
const productSearchModal = document.getElementById('product-search-modal');
const modalProductSearch = document.getElementById('modal-product-search');
const productSearchResults = document.getElementById('product-search-results');
const deliveryBtn = document.getElementById('delivery-btn');
const useClientAddressBtn = document.getElementById('use-client-address-btn');
const deliveryModal = document.getElementById('delivery-modal');
const saveDeliveryBtn = document.getElementById('save-delivery');
const cancelDeliveryBtn = document.getElementById('cancel-delivery');
const openExpenseModalBtn = document.getElementById('open-expense-modal-btn');
const expenseModal = document.getElementById('expense-modal');
const expenseForm = document.getElementById('expense-form');
const cancelExpenseBtn = document.getElementById('cancel-expense');
const saveExpenseBtn = document.getElementById('save-expense');
const closeRegisterBtn = document.getElementById('close-register-btn');
const logoutBtn = document.getElementById('logout-btn');
const notification = document.getElementById('notification');
const notificationMessage = document.getElementById('notification-message');

// ==================== CONFIGURAÇÕES ====================
const preventCacheConfig = {
    headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
};

// ==================== ATALHOS DE TECLADO ====================
const keyMap = {
    'F1': showHelpMenu,
    'F2': () => switchTab('sales'),
    'F3': () => switchTab('day-sales'),
    'F4': () => switchTab('clients'),
    'F5': loadClients,
    'F6': openClientModal,
    'F7': openProductSearchModal,
    'F8': openExpenseModal,
    'F9': registerSale,
    'F10': () => document.getElementById('amount-received')?.focus(),
    'Escape': closeModal,
    'Ctrl+1': () => document.getElementById('client-search-input')?.focus(),
    'Ctrl+2': () => document.getElementById('product-search-input')?.focus(),
    'Ctrl+D': applyManualDiscount,
    'Ctrl+L': resetSaleForm,
    'Ctrl+Q': () => logoutBtn?.click()
};

// ==================== MENU DE AJUDA ====================
function showHelpMenu() {
    const helpContent = `
        <div class="help-menu">
            <h2>Atalhos do Teclado</h2>
            <table>
                <tr><td><kbd>F1</kbd></td><td>Abrir este menu de ajuda</td></tr>
                <tr><td><kbd>F2</kbd></td><td>Aba de Vendas</td></tr>
                <tr><td><kbd>F3</kbd></td><td>Aba de Vendas do Dia</td></tr>
                <tr><td><kbd>F4</kbd></td><td>Aba de Clientes</td></tr>
                <tr><td><kbd>F5</kbd></td><td>Atualizar lista de clientes</td></tr>
                <tr><td><kbd>F6</kbd></td><td>Cadastrar novo cliente</td></tr>
                <tr><td><kbd>F8</kbd></td><td>Cadastrar despesa</td></tr>
                <tr><td><kbd>F9</kbd></td><td>Registrar venda</td></tr>
                <tr><td><kbd>F10</kbd></td><td>Focar no campo "Valor Recebido"</td></tr>
                <tr><td><kbd>ESC</kbd></td><td>Fechar modal/limpar busca</td></tr>
                <tr><td><kbd>Ctrl+1</kbd></td><td>Focar na busca de clientes</td></tr>
                <tr><td><kbd>Ctrl+2</kbd></td><td>Focar na busca de produtos</td></tr>
                <tr><td><kbd>Ctrl+D</kbd></td><td>Aplicar desconto manual</td></tr>
                <tr><td><kbd>Ctrl+L</kbd></td><td>Limpar venda atual</td></tr>
                <tr><td><kbd>Ctrl+Q</kbd></td><td>Sair do sistema</td></tr>
            </table>
            <button class="btn-primary" onclick="closeHelpMenu()">Fechar</button>
        </div>
    `;
    
    const helpMenu = document.createElement('div');
    helpMenu.id = 'help-menu-overlay';
    helpMenu.innerHTML = helpContent;
    document.body.appendChild(helpMenu);
    
    helpMenu.style.display = 'flex';
    helpMenu.addEventListener('click', (e) => {
        if (e.target === helpMenu) closeHelpMenu();
    });
}

function closeHelpMenu() {
    const helpMenu = document.getElementById('help-menu-overlay');
    if (helpMenu) helpMenu.remove();
}

// ==================== MANIPULAÇÃO DE TECLADO ====================
function handleKeyDown(e) {
    const key = e.key;
    const ctrlKey = e.ctrlKey || e.metaKey;
    
    if (ctrlKey) {
        const combo = `Ctrl+${key.toUpperCase()}`;
        if (keyMap[combo]) {
            e.preventDefault();
            keyMap[combo]();
        }
    } else {
        // Verifica teclas individuais
        if (key === 'Escape' && activeSearchDropdown) {
            closeAllDropdowns();
            return;
        }
        
        // Navegação nos resultados da busca
        if (activeSearchDropdown) {
            if (key === 'ArrowDown') {
                e.preventDefault();
                navigateSearchResults('down');
                return;
            } else if (key === 'ArrowUp') {
                e.preventDefault();
                navigateSearchResults('up');
                return;
            } else if (key === 'Enter') {
                e.preventDefault();
                const selectedItem = activeSearchDropdown.querySelector('.search-result-item.selected');
                if (selectedItem) {
                    selectedItem.click();
                }
                return;
            }
        }
        
        if (keyMap[key]) {
            e.preventDefault();
            keyMap[key]();
        }
    }
}

function navigateSearchResults(direction) {
    if (!activeSearchDropdown) return;

    const items = activeSearchDropdown.querySelectorAll('.search-result-item');
    if (items.length === 0) return;

    let selectedIndex = -1;
    items.forEach((item, index) => {
        if (item.classList.contains('selected')) {
            selectedIndex = index;
            item.classList.remove('selected');
        }
    });

    if (direction === 'down') {
        selectedIndex = (selectedIndex + 1) % items.length;
    } else if (direction === 'up') {
        selectedIndex = (selectedIndex - 1 + items.length) % items.length;
    }

    const newSelectedItem = items[selectedIndex];
    newSelectedItem.classList.add('selected');
    newSelectedItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await new Promise(resolve => setTimeout(resolve, 100));
        updateCurrentDate();
        await loadCurrentUser();
        await loadClients();
        await loadProducts();
        await checkCaixaStatus();
        setupEventListeners();
        document.addEventListener('keydown', handleKeyDown);
        setInterval(() => loadProducts(true), 10000);
        setInterval(() => updateBalance(true), 10000);
        startBalanceAutoUpdate();
    } catch (error) {
        console.error('Erro na inicialização:', error);
        showMessage('Erro ao inicializar o sistema', 'error');
    }
});

// ==================== FUNÇÕES DE USUÁRIO ====================
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
async function loadClients() {
    try {
        showClientsLoading(true);
        const response = await fetch('/operador/api/clientes', {
            ...preventCacheConfig,
            method: 'GET'
        });
        if (!response.ok) throw new Error('Erro ao carregar clientes');
        clients = await response.json();
        filteredClients = [...clients];
        renderClientsTable();
        updateClientsCount();
    } catch (error) {
        showMessage(error.message, 'error');
        showClientsEmptyState(true);
    } finally {
        showClientsLoading(false);
    }
}

function renderClientsTable() {
    const tbody = document.getElementById('clients-tbody');
    if (!tbody) return;
    
    if (filteredClients.length === 0) {
        showClientsEmptyState(true);
        return;
    }
    
    showClientsEmptyState(false);
    tbody.innerHTML = filteredClients.map(client => `
        <tr class="client-row" data-client-id="${client.id}">
            <td class="client-id">#${client.id}</td>
            <td class="client-name">
                <div class="client-name-container">
                    <strong>${client.nome || 'Não informado'}</strong>
                    ${client.apelido ? `<small class="client-nickname">(${client.apelido})</small>` : ''}
                </div>
            </td>
            <td class="client-document">
                <span class="document-value">${formatDocument(client.documento) || 'Não informado'}</span>
            </td>
            <td class="client-phone">
                ${client.telefone ? `
                    <a href="tel:${client.telefone}" class="phone-link">
                        <i class="fas fa-phone"></i>
                        ${formatPhone(client.telefone)}
                    </a>
                ` : '<span class="text-muted">Não informado</span>'}
            </td>
            <td class="client-email">
                ${client.email ? `
                    <a href="mailto:${client.email}" class="email-link">
                        <i class="fas fa-envelope"></i>
                        ${client.email}
                    </a>
                ` : '<span class="text-muted">Não informado</span>'}
            </td>
            <td class="client-address">
                <div class="address-container">
                    ${client.endereco ? `
                        <span class="address-text" title="${client.endereco}">
                            ${truncateText(client.endereco, 30)}
                        </span>
                    ` : '<span class="text-muted">Não informado</span>'}
                </div>
            </td>
            <td class="client-date">
                <span class="date-value" title="${formatDateTime(client.data_cadastro)}">
                    ${formatDate(client.data_cadastro)}
                </span>
            </td>
            <td class="client-actions">
                <div class="action-buttons">
                    <button class="btn-action btn-edit" onclick="editClient(${client.id})" title="Editar cliente">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-action btn-view" onclick="viewClientDetails(${client.id})" title="Ver detalhes">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-action btn-select" onclick="selectClientForSale(${client.id})" title="Selecionar para venda">
                        <i class="fas fa-shopping-cart"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function searchClients(searchTerm) {
    const term = searchTerm.toLowerCase().trim();
    if (!term) {
        filteredClients = [...clients];
    } else {
        filteredClients = clients.filter(client => 
            (client.nome && client.nome.toLowerCase().includes(term)) ||
            (client.documento && client.documento.includes(term)) ||
            (client.telefone && client.telefone.includes(term)) ||
            (client.email && client.email.toLowerCase().includes(term)) ||
            (client.endereco && client.endereco.toLowerCase().includes(term))
        );
    }
    applySortAndFilter();
    renderClientsTable();
    updateClientsCount();
}

function filterClients(filterType) {
    currentFilter = filterType;
    const now = new Date();
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    
    switch (filterType) {
        case 'recent':
            filteredClients = clients.filter(client => 
                new Date(client.data_cadastro) >= thirtyDaysAgo
            );
            break;
        case 'frequent':
            filteredClients = clients.filter(client => 
                client.total_vendas && client.total_vendas > 5
            );
            break;
        default:
            filteredClients = [...clients];
    }
    
    applySortAndFilter();
    renderClientsTable();
    updateClientsCount();
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === filterType);
    });
}

function sortClients(field) {
    if (currentSort.field === field) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.field = field;
        currentSort.direction = 'asc';
    }
    
    filteredClients.sort((a, b) => {
        let valueA = a[field] || '';
        let valueB = b[field] || '';
        
        if (field === 'id') {
            valueA = parseInt(valueA) || 0;
            valueB = parseInt(valueB) || 0;
        } else if (field === 'data_cadastro') {
            valueA = new Date(valueA);
            valueB = new Date(valueB);
        } else {
            valueA = valueA.toString().toLowerCase();
            valueB = valueB.toString().toLowerCase();
        }
        
        let comparison = 0;
        if (valueA > valueB) comparison = 1;
        if (valueA < valueB) comparison = -1;
        
        return currentSort.direction === 'desc' ? -comparison : comparison;
    });
    
    renderClientsTable();
    updateSortIcons();
}

function applySortAndFilter() {
    if (currentSort.field) {
        sortClients(currentSort.field);
    }
}

function updateSortIcons() {
    document.querySelectorAll('.sortable i').forEach(icon => {
        icon.className = 'fas fa-sort';
    });
    
    const activeHeader = document.querySelector(`[data-sort="${currentSort.field}"] i`);
    if (activeHeader) {
        activeHeader.className = currentSort.direction === 'asc' 
            ? 'fas fa-sort-up' 
            : 'fas fa-sort-down';
    }
}

function updateClientsCount() {
    const countElement = document.getElementById('clients-count');
    if (countElement) {
        const total = clients.length;
        const filtered = filteredClients.length;
        
        if (total === filtered) {
            countElement.textContent = `${total} cliente${total !== 1 ? 's' : ''} encontrado${total !== 1 ? 's' : ''}`;
        } else {
            countElement.textContent = `${filtered} de ${total} clientes`;
        }
    }
}

function showClientsLoading(show) {
    const loading = document.getElementById('clients-loading');
    const table = document.querySelector('.clients-table-container');
    if (loading) loading.style.display = show ? 'block' : 'none';
    if (table) table.style.display = show ? 'none' : 'block';
}

function showClientsEmptyState(show) {
    const emptyState = document.getElementById('clients-empty-state');
    const table = document.querySelector('.clients-table-container');
    const tableFooter = document.querySelector('.table-footer');
    if (emptyState) emptyState.style.display = show ? 'block' : 'none';
    if (table) table.style.display = show ? 'none' : 'block';
    if (tableFooter) tableFooter.style.display = show ? 'none' : 'flex';
}

function formatDocument(doc) {
    if (!doc) return '';
    const numbers = doc.replace(/\D/g, '');
    if (numbers.length === 11) {
        return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    } else if (numbers.length === 14) {
        return numbers.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
    return doc;
}

function formatPhone(phone) {
    if (!phone) return '';
    const numbers = phone.replace(/\D/g, '');
    if (numbers.length === 11) {
        return numbers.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    } else if (numbers.length === 10) {
        return numbers.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    }
    return phone;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

function formatDateTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
}

function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

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

// Função para selecionar cliente para venda (chamada pelo botão)
function selectClientForSale(clientId) {
    const client = findClientById(clientId);
    
    if (client) {
        selectClient(client);
        showMessage(`Cliente ${client.nome} selecionado para venda`);
    } else {
        showMessage('Cliente não encontrado', 'error');
    }
}

function findClientById(clientId) {
    // Primeiro tenta encontrar na lista de clientes carregada
    if (clients && Array.isArray(clients)) {
        const client = clients.find(c => c.id == clientId);
        if (client) return client;
    }
    
    // Se não encontrou, tenta extrair da tabela HTML (fallback)
    const clientRow = document.querySelector(`[data-client-id="${clientId}"]`);
    if (clientRow) {
        return {
            id: clientId,
            nome: clientRow.querySelector('.client-name strong')?.textContent || `Cliente ${clientId}`,
            documento: clientRow.querySelector('.document-value')?.textContent || '',
            telefone: clientRow.querySelector('.phone-link')?.textContent.replace(/\D/g, '') || '',
            email: clientRow.querySelector('.email-link')?.textContent || '',
            endereco: clientRow.querySelector('.address-text')?.textContent || ''
        };
    }
    
    return null;
}

// Função para fechar modal (opcional)
function closeClientModal() {
    const modal = document.getElementById('clientModal') || document.querySelector('.client-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
}

// Sua função selectClient existente (mantendo como está)
function selectClient(client) {
    if (!client) {
        // Define o cliente padrão quando nenhum cliente é selecionado
        selectedClient = {
            id: 1,
            nome: "PADRÃO",
            documento: "",
            telefone: "",
            email: "",
            endereco: ""
        };
        selectedClientInput.value = "PADRÃO"; // Mostra que está usando o padrão
        selectedClientIdInput.value = "1"; // ID 1 para o cliente padrão
    } else {
        // Atribui o cliente selecionado
        selectedClient = client;
        selectedClientInput.value = client.nome; // Exibe o nome do cliente
        selectedClientIdInput.value = client.id.toString();
    }
    updateCaixaStatus();
}
// Versão alternativa se você quiser passar o objeto cliente diretamente no botão
// Neste caso, o botão seria: onclick="selectClientForSaleByObject(this)" 
// E você adicionaria data-attributes no botão com as informações do cliente

function selectClientForSaleByObject(buttonElement) {
    const clientData = {
        id: buttonElement.getAttribute('data-client-id'),
        nome: buttonElement.getAttribute('data-client-name'),
        // Adicione outros campos conforme necessário
    };
    
    selectClient(clientData);
    closeClientModal();
}

function showClientSearchResults(clients) {
    const resultsContainer = document.getElementById('client-search-results');
    if (!resultsContainer) return;
    resultsContainer.innerHTML = '';
    
    if (clients.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">Nenhum cliente encontrado</div>';
        resultsContainer.style.display = 'block';
        return;
    }
    
    clients.forEach(client => {
        const resultItem = document.createElement('div');
        resultItem.className = 'search-result-item';
        resultItem.innerHTML = `
            <h4>${client.nome}</h4>
            <p>Documento: ${client.documento || 'Não informado'}</p>
            <p>Telefone: ${client.telefone || 'Não informado'}</p>
        `;
        resultItem.addEventListener('click', () => {
            selectClient(client);
            resultsContainer.style.display = 'none';
            if (clientSearchInput) clientSearchInput.value = '';
        });
        resultsContainer.appendChild(resultItem);
    });
    
    resultsContainer.style.display = 'block';
    activeSearchDropdown = resultsContainer;
}

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

function openClientModal() {
    if (!clientModalTitle || !clientForm) return;
    currentEditingClient = null;
    clientModalTitle.textContent = 'Cadastrar Cliente';
    clientForm.reset();
    openModal('client');
}

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
    const searchTerm = productSearchInput?.value.trim();
    if (searchTerm && modalProductSearch) {
        modalProductSearch.value = searchTerm;
    }
    openModal('product-search');
    searchProductsInModal();
}

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

async function addProductToSale(product, initialQuantity = 1) {
    if (!product) return;
    const discounts = await fetchProductDiscounts(product.id);
    const { finalPrice, discountApplied, discountInfo } = calculateDiscountedPrice(product.valor_unitario, initialQuantity, discounts);
    const existingProductIndex = selectedProducts.findIndex(p => p.id === product.id);
    
    if (existingProductIndex >= 0) {
        selectedProducts[existingProductIndex].quantity += 1;
        const newQuantity = selectedProducts[existingProductIndex].quantity;
        const newPriceInfo = calculateDiscountedPrice(product.valor_unitario, newQuantity, discounts);
        selectedProducts[existingProductIndex].price = newPriceInfo.finalPrice;
        selectedProducts[existingProductIndex].hasDiscount = newPriceInfo.discountApplied;
        selectedProducts[existingProductIndex].discountInfo = newPriceInfo.discountInfo;
    } else {
        selectedProducts.push({
            id: product.id,
            name: product.nome,
            description: product.descricao || '',
            valor_unitario: product.valor_unitario,
            price: finalPrice,
            originalPrice: product.valor_unitario,
            quantity: initialQuantity,
            unit: product.unidade,
            stock: product.estoque_loja,
            allowsFraction: product.unidade.toLowerCase() === 'kg',
            hasDiscount: discountApplied,
            discountInfo: discountInfo,
            availableDiscounts: discounts
        });
    }
    
    renderProductsList();
    calculateSaleTotal();
}

async function fetchProductDiscounts(productId) {
    try {
        const response = await fetch(`/operador/api/produtos/${productId}/descontos?timestamp=${new Date().getTime()}`);
        if (!response.ok) return [];
        return await response.json();
    } catch (error) {
        console.error('Erro ao buscar descontos:', error);
        return [];
    }
}

function calculateDiscountedPrice(basePrice, quantity, discounts) {
    if (!discounts || discounts.length === 0) {
        return {
            finalPrice: basePrice,
            discountApplied: false,
            discountInfo: null
        };
    }

    let bestDiscount = null;
    let bestPrice = basePrice;
    const sortedDiscounts = [...discounts].sort((a, b) => {
        if (a.tipo === 'percentual' && b.tipo !== 'percentual') return -1;
        if (a.tipo !== 'percentual' && b.tipo === 'percentual') return 1;
        return 0;
    });

    for (const discount of sortedDiscounts) {
        if (!discount.ativo) continue;
        if (discount.valido_ate) {
            const validUntil = new Date(discount.valido_ate);
            const today = new Date();
            if (today > validUntil) continue;
        }
        if (quantity < discount.quantidade_minima) continue;
        if (discount.quantidade_maxima && quantity > discount.quantidade_maxima) continue;
        
        let discountedPrice = basePrice;
        if (discount.tipo === 'percentual') {
            discountedPrice = basePrice * (1 - (discount.valor / 100));
        } else if (discount.tipo === 'fixo') {
            discountedPrice = Math.max(0, basePrice - discount.valor);
        }
        
        if (discountedPrice < bestPrice) {
            bestPrice = discountedPrice;
            bestDiscount = {
                ...discount,
                valor_aplicado: discount.tipo === 'percentual' 
                    ? `${discount.valor}%` 
                    : formatCurrency(discount.valor)
            };
        }
    }
    
    return {
        finalPrice: bestPrice,
        discountApplied: bestDiscount !== null,
        discountInfo: bestDiscount
    };
}

function updateAllProductDiscounts() {
    selectedProducts.forEach(async (product, index) => {
        const discounts = await fetchProductDiscounts(product.id);
        const { finalPrice, discountApplied, discountInfo } = calculateDiscountedPrice(
            product.originalPrice, 
            product.quantity, 
            discounts
        );
        selectedProducts[index] = {
            ...product,
            price: finalPrice,
            hasDiscount: discountApplied,
            discountInfo: discountInfo,
            availableDiscounts: discounts
        };
    });
    renderProductsList();
    calculateSaleTotal();
}

function applyManualDiscount() {
    try {
        const discountType = document.getElementById('discount-type').value;
        const discountValueInput = document.getElementById('discount-value').value.trim();
        
        if (!discountValueInput) {
            throw new Error('Digite um valor para o desconto');
        }

        const discountValue = parseFloat(discountValueInput.replace(',', '.'));
        if (isNaN(discountValue)) {
            throw new Error('Valor de desconto inválido. Use apenas números.');
        }

        if (discountType === 'percentual') {
            if (discountValue <= 0 || discountValue > 100) {
                throw new Error('Percentual deve ser entre 0.01% e 100%');
            }
        } else {
            if (discountValue <= 0) {
                throw new Error('Valor fixo deve ser maior que zero');
            }
            const minProductPrice = Math.min(...selectedProducts.map(p => p.originalPrice));
            if (discountValue >= minProductPrice) {
                throw new Error(`Desconto não pode ser maior que ${formatCurrency(minProductPrice)}`);
            }
        }

        if (selectedProducts.length === 0) {
            throw new Error('Adicione produtos antes de aplicar desconto');
        }

        selectedProducts = selectedProducts.map(product => {
            let newPrice = product.originalPrice;
            let discountAmount = 0;
            
            if (discountType === 'percentual') {
                discountAmount = product.originalPrice * (discountValue / 100);
                newPrice = product.originalPrice - discountAmount;
            } else {
                discountAmount = Math.min(discountValue, product.originalPrice);
                newPrice = product.originalPrice - discountAmount;
            }
            
            return {
                ...product,
                price: newPrice,
                hasDiscount: true,
                discountInfo: {
                    tipo: discountType,
                    valor: discountValue,
                    valor_aplicado: discountType === 'percentual' 
                        ? `${discountValue}%` 
                        : formatCurrency(discountValue),
                    identificador: 'MANUAL',
                    descricao: 'Desconto manual aplicado'
                }
            };
        });

        renderProductsList();
        calculateSaleTotal();
        showMessage('Desconto aplicado com sucesso!');
        document.getElementById('discount-value').value = '';
    } catch (error) {
        showMessage(error.message, 'error');
        return false;
    }
    return true;
}

function renderProductsList() {
    if (!productsList) return;
    productsList.innerHTML = '';
    
    selectedProducts.forEach((product, index) => {
        const totalValue = product.price * product.quantity;
        const originalTotalValue = product.originalPrice * product.quantity;
        const discountValue = originalTotalValue - totalValue;
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                ${product.name}
                ${product.hasDiscount ? 
                    `<span class="discount-badge" title="${product.discountInfo.descricao || 'Desconto aplicado'}">
                        <i class="fas fa-tag"></i> ${product.discountInfo.identificador || 'DESCONTO'}
                    </span>` : 
                    ''
                }
            </td>
            <td>${product.description}</td>
            <td>
                ${formatCurrency(product.price)}
                ${product.hasDiscount ? 
                    `<small class="original-price">${formatCurrency(product.originalPrice)}</small>` : 
                    ''
                }
            </td>
            <td>
                ${product.allowsFraction ? 
                    `<input type="text" class="quantity-input" 
                            value="${product.quantity.toFixed(3).replace('.', ',')}" 
                            data-index="${index}" pattern="[0-9]+([,\.][0-9]+)?" 
                            title="Use vírgula ou ponto para decimais">` :
                    `<input type="number" class="quantity-input" 
                            value="${product.quantity}" min="1" 
                            max="${product.stock}" data-index="${index}">`
                }
                <small>${product.unit}</small>
            </td>
            <td class="product-total">
                ${formatCurrency(totalValue)}
                ${product.hasDiscount ? 
                    `<small class="discount-value">(Economia: ${formatCurrency(discountValue)})</small>` : 
                    ''
                }
            </td>
            <td>
                <button class="btn-remove" data-index="${index}" title="Remover produto">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        productsList.appendChild(row);
    });
    
    document.querySelectorAll('.quantity-input').forEach(input => {
        input.addEventListener('change', async function(e) {
            await updateProductQuantity(e.target);
        });
        input.addEventListener('input', function(e) {
            if (e.target.type === 'text') {
                const value = e.target.value;
                if (!/^[0-9]*([,\.][0-9]*)?$/.test(value)) {
                    e.target.value = value.slice(0, -1);
                }
            }
        });
    });
}

async function updateProductQuantity(input) {
    const index = parseInt(input.dataset.index);
    if (isNaN(index)) return;

    let newQuantity;
    const product = selectedProducts[index];
    
    if (product.allowsFraction) {
        const value = input.value.trim().replace(',', '.');
        newQuantity = parseFloat(value);
        if (isNaN(newQuantity)) {
            input.value = product.quantity.toFixed(3).replace('.', ',');
            return;
        }
    } else {
        newQuantity = parseInt(input.value);
        if (isNaN(newQuantity)) {
            input.value = product.quantity;
            return;
        }
    }
    
    const { finalPrice, discountApplied, discountInfo } = calculateDiscountedPrice(
        product.originalPrice, 
        newQuantity, 
        product.availableDiscounts || []
    );
    
    selectedProducts[index] = {
        ...product,
        quantity: newQuantity > 0 ? newQuantity : product.quantity,
        price: finalPrice,
        hasDiscount: discountApplied,
        discountInfo: discountInfo || product.discountInfo
    };
    
    input.value = product.allowsFraction ? 
        selectedProducts[index].quantity.toFixed(3).replace('.', ',') : 
        selectedProducts[index].quantity;
    
    calculateSaleTotal();
}

function removeProductRow(button) {
    const index = parseInt(button.dataset.index);
    if (index >= 0 && index < selectedProducts.length) {
        selectedProducts.splice(index, 1);
        renderProductsList();
    }
}

function addEmptyProductRow() {
    openProductSearchModal();
}

// ==================== FUNÇÕES DE VENDA ====================
async function registerSale() {
    try {
        const clienteId = selectedClientIdInput?.value ? parseInt(selectedClientIdInput.value) : 1;
        
        if (selectedProducts.length === 0) {
            showMessage('Adicione pelo menos um produto', 'error');
            throw new Error('Nenhum produto selecionado');
        }

        const paymentMethods = [];
        const paymentItems = document.querySelectorAll('.payment-item');
        
        // Processa os métodos de pagamento já definidos
        paymentItems.forEach(item => {
            const method = item.querySelector('input[name="payment_methods[]"]').value;
            const amount = parseFloat(item.querySelector('input[name="payment_amounts[]"]').value.replace(',', '.'));
            if (!isNaN(amount) && amount > 0) {
                paymentMethods.push({
                    forma_pagamento: method,
                    valor: amount
                });
            }
        });

        const totalText = saleTotalElement?.textContent.replace('R$ ', '').replace(/\./g, '').replace(',', '.');
        const total = parseFloat(totalText) || 0;
        let valor_recebido = 0;
        
        if (paymentMethods.length > 0) {
            // Se há múltiplos métodos de pagamento, soma todos os valores
            valor_recebido = paymentMethods.reduce((sum, pm) => sum + pm.valor, 0);
        } else {
            // Se não há múltiplos pagamentos, usa o valor do campo "valor recebido"
            const amountReceivedText = amountReceivedInput?.value.replace(/\./g, '').replace(',', '.') || '0';
            valor_recebido = parseFloat(amountReceivedText) || 0;
        }

        const totalPagamentos = paymentMethods.reduce((sum, pm) => sum + pm.valor, 0);
        
        if (totalPagamentos < total) {
            const remaining = total - totalPagamentos;
            
            // Verifica se já existe um pagamento em dinheiro para somar
            const pagamentoDinheiroExistente = paymentMethods.find(pm => pm.forma_pagamento === 'dinheiro');
            
            if (pagamentoDinheiroExistente) {
                // Se já existe pagamento em dinheiro, adiciona o valor restante
                pagamentoDinheiroExistente.valor += remaining;
            } else {
                // Se não existe, cria um novo pagamento em dinheiro
                paymentMethods.push({
                    forma_pagamento: 'dinheiro',
                    valor: remaining
                });
            }
            
            // Atualiza o valor_recebido para incluir o pagamento em dinheiro
            valor_recebido = total;
        }
        
        // Se não há nenhum método de pagamento definido, assume pagamento total em dinheiro
        if (paymentMethods.length === 0) {
            paymentMethods.push({
                forma_pagamento: 'dinheiro',
                valor: total
            });
            valor_recebido = total;
        }

        const items = selectedProducts.map(product => {
            const originalTotal = product.originalPrice * product.quantity;
            const discountedTotal = product.price * product.quantity;
            const discountValue = originalTotal - discountedTotal;
            
            return {
                produto_id: product.id,
                quantidade: Number(product.quantity),
                valor_unitario: Number(product.originalPrice),
                valor_unitario_com_desconto: Number(product.price),
                valor_total: Number(discountedTotal),
                valor_desconto: Number(discountValue),
                desconto_info: product.discountInfo ? {
                    tipo: product.discountInfo.tipo,
                    valor: product.discountInfo.valor,
                    identificador: product.discountInfo.identificador,
                    descricao: product.discountInfo.descricao
                } : null
            };
        });

        const saleData = {
            cliente_id: clienteId,
            forma_pagamento: paymentMethods.length > 1 ? 'multiplos' : paymentMethods[0].forma_pagamento,
            valor_recebido: valor_recebido,
            valor_total: total,
            itens: items,
            pagamentos: paymentMethods, // Sempre envia a lista de pagamentos
            total_descontos: items.reduce((sum, item) => sum + item.valor_desconto, 0),
            observacao: document.getElementById('sale-notes')?.value
        };

        if (deliveryAddress) {
            saleData.endereco_entrega = {
                logradouro: deliveryAddress.logradouro || '',
                numero: deliveryAddress.numero || '',
                complemento: deliveryAddress.complemento || '',
                bairro: deliveryAddress.bairro || '',
                cidade: deliveryAddress.cidade || '',
                estado: deliveryAddress.estado || '',
                cep: deliveryAddress.cep || '',
                instrucoes: deliveryAddress.instrucoes || ''
            };
        }
        const response = await fetch('/operador/api/vendas', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(saleData)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || 'Erro ao registrar venda');
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.message || 'Erro ao registrar venda');
        }

        resetSaleForm();
        await updateBalance(true);
        await loadProducts(true);
        showMessage(`Venda registrada com sucesso!`);
        const paymentIdsStr = result.pagamentos_ids.join(',');
        window.open(`/operador/pdf/nota/${paymentIdsStr}?timestamp=${new Date().getTime()}`, '_blank');
    } catch (error) {
        console.error('Erro ao registrar venda:', error);
        showMessage(error.message, 'error');
    }
}

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
    
    if (subtotalValueElement) subtotalValueElement.textContent = formatCurrency(subtotal);
    if (saleTotalElement) saleTotalElement.textContent = formatCurrency(total);
    
    if (amountReceivedInput && amountReceivedInput.value) {
        const amountReceivedText = amountReceivedInput.value.replace(/\./g, '').replace(',', '.');
        const amountReceived = parseFloat(amountReceivedText) || 0;
        const change = Math.max(0, amountReceived - total);
        if (changeValueElement) changeValueElement.textContent = formatCurrency(change);
    } else {
        if (changeValueElement) changeValueElement.textContent = formatCurrency(0);
    }
}

function formatDecimal(num, decimals = 3) {
    return num.toFixed(decimals).replace('.', ',');
}

function formatCurrencyInput(input) {
    let value = input.value.replace(/[^\d,.]/g, '');
    const separators = value.match(/[,.]/g);
    if (separators && separators.length > 1) {
        value = value.replace(/[,.]/g, (m, i) => (i === value.lastIndexOf('.') || i === value.lastIndexOf(',')) ? m : '');
    }
    value = value.replace(/([,.])(?=.*\1)/g, '');
    const numericValue = value.replace(',', '.');
    input.value = value;
    return numericValue;
}

function resetSaleForm() {
    try {
        selectClient(null);
        if (selectedClientInput) selectedClientInput.value = '';
        if (selectedClientIdInput) selectedClientIdInput.value = '';
        if (productsList) productsList.innerHTML = '';
        selectedProducts = [];
        const selectedPaymentsList = document.querySelector('.selected-payments-list');
        if (selectedPaymentsList) selectedPaymentsList.innerHTML = '';
        const paymentMethodSelect = document.querySelector('.payment-method-select');
        const paymentAmountInput = document.querySelector('.payment-amount');
        if (paymentMethodSelect) paymentMethodSelect.value = '';
        if (paymentAmountInput) paymentAmountInput.value = '';
        const saleNotes = document.getElementById('sale-notes');
        if (saleNotes) saleNotes.value = '';
        if (amountReceivedInput) amountReceivedInput.value = '';
        const discountValue = document.getElementById('discount-value');
        const discountType = document.getElementById('discount-type');
        const discountDisplay = document.getElementById('discount-value-display');
        if (discountValue) discountValue.value = '';
        if (discountType) discountType.value = 'percentual';
        if (discountDisplay) discountDisplay.textContent = 'R$ 0.00';
        deliveryAddress = null;
        const deliveryBtn = document.getElementById('delivery-btn');
        if (deliveryBtn) {
            deliveryBtn.classList.remove('has-delivery');
            deliveryBtn.innerHTML = '<i class="fas fa-truck"></i> Adicionar Entrega';
        }
        const deliveryInfoDisplay = document.getElementById('delivery-info-display');
        if (deliveryInfoDisplay) {
            deliveryInfoDisplay.style.display = 'none';
            const deliveryAddressText = document.getElementById('delivery-address-text');
            if (deliveryAddressText) deliveryAddressText.textContent = '';
        }
        const deliveryInfo = document.querySelector('.delivery-info');
        if (deliveryInfo) deliveryInfo.remove();
        if (subtotalValueElement) subtotalValueElement.textContent = 'R$ 0.00';
        if (saleTotalElement) saleTotalElement.textContent = 'R$ 0.00';
        if (changeValueElement) changeValueElement.textContent = 'R$ 0.00';
        updateCaixaStatus();
        if (selectedClientInput) {
            const event = new Event('input', { bubbles: true, cancelable: true });
            selectedClientInput.dispatchEvent(event);
        }
        if (typeof calculateSaleTotal === 'function') {
            calculateSaleTotal();
        }
    } catch (error) {
        console.error("Erro ao resetar formulário de venda:", error);
    }
}

// ==================== FUNÇÕES DE ENTREGA ====================
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

function saveDeliveryAddress() {
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

function updateDeliveryUI() {
    if (!deliveryAddress) return;
    
    if (deliveryBtn) {
        deliveryBtn.classList.add('has-delivery');
        deliveryBtn.innerHTML = '<i class="fas fa-check-circle"></i> Endereço de Entrega Cadastrado';
    }
    showDeliveryInfo();
}

function showDeliveryInfo() {
    if (!deliveryBtn || !deliveryAddress) return;
    
    const existingInfo = document.querySelector('.delivery-info');
    if (existingInfo) existingInfo.remove();
    
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
    
    deliveryBtn.insertAdjacentElement('afterend', deliveryInfo);
    document.getElementById('edit-delivery-btn')?.addEventListener('click', openDeliveryModal);
    document.getElementById('remove-delivery-btn')?.addEventListener('click', removeDeliveryAddress);
}

function removeDeliveryAddress() {
    deliveryAddress = null;
    
    if (deliveryBtn) {
        deliveryBtn.classList.remove('has-delivery');
        deliveryBtn.innerHTML = '<i class="fas fa-truck"></i> Adicionar Entrega';
    }
    
    const deliveryInfo = document.querySelector('.delivery-info');
    if (deliveryInfo) {
        deliveryInfo.remove();
    }
    
    showMessage('Endereço de entrega removido');
}

// ==================== FUNÇÕES DE DESPESAS ====================
function openExpenseModal() {
    if (!expenseModal || !currentCaixaId) {
        showMessage('Nenhum caixa aberto encontrado', 'error');
        return;
    }
    
    expenseModal.style.display = 'flex';
    document.getElementById('expense-description')?.focus();
}

function closeExpenseModal() {
    if (!expenseModal || !expenseForm) return;
    expenseModal.style.display = 'none';
    expenseForm.reset();
}

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
            throw new Error(errorData.error || 'Erro ao registrar despesa');
        }
        
        showMessage('Despesa registrada com sucesso!');
        closeExpenseModal();
        updateBalance(true);
    } catch (error) {
        showMessage(error.message, 'error');
        console.error('Erro ao salvar despesa:', error);
    }
}

// ==================== FUNÇÕES DE VENDAS DO DIA ====================
async function loadDaySales() {
    const tableBody = document.querySelector('#day-sales-table tbody');
    if (!tableBody) return;

    try {
        tableBody.innerHTML = '<tr><td colspan="6"><div class="loading-spinner"></div></td></tr>';

        const response = await fetch('/operador/api/vendas/hoje', {
            ...preventCacheConfig,
            method: 'GET'
        });

        if (!response.ok) {
            let errorMessage = 'Erro ao carregar vendas do dia';
            try {
                // tenta ler como JSON
                const errorData = await response.json();
                errorMessage = errorData.message || errorMessage;
            } catch {
                // se não for JSON, tenta como texto
                const errorText = await response.text();
                if (errorText) errorMessage = errorText;
            }
            throw new Error(errorMessage);
        }

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.message || 'Erro ao carregar vendas');
        }

        const vendas = result.data || [];
        // Remover vendas duplicadas antes de renderizar
        const vendasUnicas = removerVendasDuplicadas(vendas);
        renderDaySales(vendasUnicas);

    } catch (error) {
        console.error("Erro ao carregar vendas:", error);
        tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: red;">${error.message}</td></tr>`;
        showMessage(error.message, 'error');
    }
}

function removerVendasDuplicadas(vendas) {
    const vendasUnicas = [];
    const idsVistos = new Set();

    for (const venda of vendas) {
        if (!idsVistos.has(venda.id)) {
            idsVistos.add(venda.id);
            vendasUnicas.push(venda);
        }
    }

    return vendasUnicas;
}

function renderDaySales(vendas) {
    const tableBody = document.querySelector('#day-sales-table tbody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';

    if (!Array.isArray(vendas) || vendas.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 1rem; color: #666;">Nenhuma venda registrada para o dia.</td></tr>`;
        return;
    }

    // Ordenar vendas por data (mais recente primeiro)
    vendas.sort((a, b) => new Date(b.data_emissao) - new Date(a.data_emissao));

    // Criar linhas da tabela
    vendas.forEach(sale => {
        // Verificar se a venda tem itens antes de renderizar
        if (sale.itens && sale.itens.length > 0) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${sale.id}</td>
                <td>${new Date(sale.data_emissao).toLocaleString('pt-BR')}</td>
                <td>${sale.cliente?.nome || 'Consumidor Final'}</td>
                <td>${formatCurrency(sale.valor_total)}</td>
                <td>${formatPaymentMethod(sale.forma_pagamento) || '-'}</td>
                <td>
                    <button class="btn-view" data-id="${sale.id}">
                        <i class="fas fa-eye"></i> Detalhes
                    </button>
                    <button class="btn-void" data-id="${sale.id}">
                        <i class="fas fa-undo"></i> Estornar
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        }
    });

    // Configurar event listeners para os botões
    tableBody.addEventListener('click', function(e) {
        const viewBtn = e.target.closest('.btn-view');
        if (viewBtn) {
            openSaleDetailsModal(viewBtn.dataset.id);
            return;
        }
        
        const voidBtn = e.target.closest('.btn-void');
        if (voidBtn) {
            openVoidSaleModal(voidBtn.dataset.id);
            return;
        }
    });
}

function openVoidSaleModal(saleId) {
    closeModal();
    const modal = document.getElementById('void-sale-modal');
    if (!modal) {
        console.error('Modal de estorno não encontrado');
        return;
    }
    
    document.getElementById('void-sale-id').value = saleId;
    document.getElementById('void-sale-id-display').textContent = saleId;
    document.getElementById('void-sale-reason').value = '';
    modal.style.display = 'flex';
    currentOpenModal = modal;
}

async function voidSale() {
    const saleId = document.getElementById('void-sale-id').value;
    const reason = document.getElementById('void-sale-reason').value || "Sem motivo informado";
    
    if (!saleId) {
        showMessage('ID da venda não informado', 'error');
        return;
    }

    try {
        const button = document.querySelector('#void-sale-modal .btn-danger');
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
        button.disabled = true;

        const response = await fetch(`/operador/api/vendas/${saleId}/estornar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                motivo_estorno: reason
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `Erro ${response.status} ao estornar venda`);
        }
        
        const result = await response.json();
        showMessage(`Venda #${saleId} estornada com sucesso!`, 'success');
        closeModal('void-sale-modal');
        await updateBalance(true);
        await loadDaySales();
    } catch (error) {
        console.error('Erro ao estornar venda:', error);
        showMessage(error.message, 'error');
    } finally {
        const button = document.querySelector('#void-sale-modal .btn-danger');
        if (button) {
            button.innerHTML = '<i class="fas fa-undo"></i> Confirmar Estorno';
            button.disabled = false;
        }
    }
}

function generateDaySalesPDF() {
    try {
        const button = document.getElementById('generate-pdf-btn');
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Gerando...';
        button.disabled = true;
        
        const today = new Date();
        const dateStr = today.toISOString().split('T')[0];
        gerarRelatorioDiario(dateStr);
    } catch (error) {
        console.error("Erro ao gerar PDF:", error);
        showMessage("Erro ao gerar relatório em PDF", "error");
    } finally {
        setTimeout(() => {
            const button = document.getElementById('generate-pdf-btn');
            if (button) {
                button.innerHTML = '<i class="fas fa-file-pdf"></i> Gerar PDF';
                button.disabled = false;
            }
        }, 2000);
    }
}

function gerarRelatorioDiario(data = null, caixaId = null, operadorId = null) {
    let url = '/operador/api/vendas/relatorio-diario-pdf';
    const params = new URLSearchParams();
    const reportDate = data || new Date().toISOString().split('T')[0];
    params.append('data', reportDate);
    if (caixaId) params.append('caixa_id', caixaId);
    if (operadorId) params.append('operador_id', operadorId);
    url += '?' + params.toString();
    window.open(url, '_blank');
}

function closeModal(modalId = null) {
    if (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'none';
    } else {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }
    currentOpenModal = null;
}

async function openSaleDetailsModal(saleId) {
    try {
        closeModal();
        const modal = document.getElementById('sale-details-modal');
        if (!modal) {
            console.error('Modal de detalhes da venda não encontrado');
            return;
        }
        
        modal.style.display = 'flex';
        currentOpenModal = modal;
        
        // Reset elementos do modal
        const elementsToReset = [
            'sale-details-id',
            'sale-details-date',
            'sale-details-client',
            'sale-details-operator',
            'sale-details-total',
            'sale-details-discount',
            'sale-details-notes',
            'sale-details-delivery',
            'sale-details-delivery-instructions',
            'sale-details-products',
            'sale-details-payments'
        ];
        
        elementsToReset.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                if (id === 'sale-details-products' || id === 'sale-details-payments') {
                    el.innerHTML = '';
                } else {
                    el.textContent = '';
                }
            }
        });

        // Buscar dados da API
        const response = await fetch(`/operador/api/vendas/${saleId}/detalhes`);
        if (!response.ok) throw new Error('Erro ao buscar detalhes da venda');
        
        const result = await response.json();
        if (!result.success) throw new Error(result.message || 'Erro ao carregar detalhes');
        
        const venda = result.data;
        
        // Preencher informações básicas
        safeSetText('sale-details-id', saleId);
        safeSetText('sale-details-date', new Date(venda.data_emissao).toLocaleString('pt-BR'));
        safeSetText('sale-details-client', `${venda.cliente?.nome || 'Consumidor Final'}${venda.cliente?.documento ? ' (' + formatDocument(venda.cliente.documento) + ')' : ''}`);
        safeSetText('sale-details-operator', venda.operador?.nome || 'N/A');
        safeSetText('sale-details-total', formatCurrency(venda.valor_total));
        safeSetText('sale-details-discount', formatCurrency(venda.valor_desconto || 0));
        safeSetText('sale-details-notes', venda.observacao || 'Nenhuma observação');
        
        // Tratar informações de entrega
        handleDeliveryInfo(venda);
        
        // Tratar produtos com remoção de duplicatas
        handleProductsTable(venda.itens);
        
        // Tratar pagamentos com remoção de duplicatas
        handlePaymentsTable(venda);
        
        // Event listener para fechar modal
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal('sale-details-modal');
            }
        });
        
    } catch (error) {
        console.error("Erro ao abrir detalhes da venda:", error);
        showMessage(error.message || "Erro ao carregar detalhes da venda", 'error');
        closeModal('sale-details-modal');
    }
}

// Função para tratar informações de entrega
function handleDeliveryInfo(venda) {
    const deliveryContainer = document.getElementById('sale-details-delivery-container');
    const deliveryInstructions = document.getElementById('sale-details-delivery-instructions');
    
    if (deliveryContainer) {
        if (venda.entrega) {
            const endereco = [
                venda.entrega.endereco || venda.entrega.logradouro,
                venda.entrega.numero,
                venda.entrega.complemento,
                venda.entrega.bairro,
                `${venda.entrega.cidade}/${venda.entrega.estado}`.toUpperCase(),
                venda.entrega.cep ? formatCEP(venda.entrega.cep) : ''
            ].filter(Boolean).join(', ');
            
            safeSetText('sale-details-delivery', endereco);
            deliveryContainer.style.display = 'flex';
            
            if (deliveryInstructions) {
                if (venda.entrega.instrucoes) {
                    deliveryInstructions.textContent = `Instruções: ${venda.entrega.instrucoes}`;
                    deliveryInstructions.style.display = 'block';
                } else {
                    deliveryInstructions.style.display = 'none';
                }
            }
        } else {
            deliveryContainer.style.display = 'none';
            if (deliveryInstructions) {
                deliveryInstructions.style.display = 'none';
            }
        }
    }
}

// Função para tratar tabela de produtos com remoção de duplicatas
function handleProductsTable(itens) {
    const productsTable = document.getElementById('sale-details-products');
    if (!productsTable || !itens) return;
    
    // Limpar tabela antes de popular
    productsTable.innerHTML = '';
    
    // Remover duplicatas baseado no produto_id ou produto_nome
    const itensUnicos = [];
    const idsVistos = new Set();
    
    itens.forEach(item => {
        // Usar uma chave única baseada no produto e valor unitário para evitar duplicatas
        const chaveUnica = `${item.produto_id || item.produto_nome}-${item.valor_unitario}-${item.quantidade}`;
        
        if (!idsVistos.has(chaveUnica)) {
            idsVistos.add(chaveUnica);
            itensUnicos.push(item);
        }
    });
    
    // Adicionar produtos únicos na tabela
    itensUnicos.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.produto_nome || item.nome || 'Produto não encontrado'}</td>
            <td class="text-right">${parseFloat(item.quantidade || 0).toLocaleString('pt-BR')}</td>
            <td class="text-right">${formatCurrency(item.valor_unitario || 0)}</td>
            <td class="text-right">${item.desconto_aplicado ? formatCurrency(item.desconto_aplicado) : '-'}</td>
            <td class="text-right">${formatCurrency(item.valor_total || item.total || 0)}</td>
        `;
        productsTable.appendChild(row);
    });
}

// Função para tratar tabela de pagamentos com remoção de duplicatas
function handlePaymentsTable(venda) {
    const paymentsTable = document.getElementById('sale-details-payments');
    if (!paymentsTable) return;
    
    // Limpar tabela antes de popular
    paymentsTable.innerHTML = '';
    
    if (venda.pagamentos && venda.pagamentos.length > 0) {
        // Agregar pagamentos para evitar duplicatas
        const pagamentosAgregados = agregarPagamentos(venda.pagamentos);
        
        pagamentosAgregados.forEach(pagamento => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${formatPaymentMethod(pagamento.forma_pagamento)}</td>
                <td class="text-right">${formatCurrency(pagamento.valor)}</td>
                <td>${new Date(pagamento.data).toLocaleString('pt-BR')}</td>
            `;
            paymentsTable.appendChild(row);
        });
        
        // Adicionar linha de total se houver múltiplos pagamentos
        if (pagamentosAgregados.length > 1) {
            const totalPagamentos = pagamentosAgregados.reduce((sum, pag) => sum + parseFloat(pag.valor), 0);
            const row = document.createElement('tr');
            row.className = 'total-row';
            row.innerHTML = `
                <td><strong>Total</strong></td>
                <td class="text-right"><strong>${formatCurrency(totalPagamentos)}</strong></td>
                <td></td>
            `;
            paymentsTable.appendChild(row);
        }
    } else {
        // Pagamento único (fallback para formato antigo)
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatPaymentMethod(venda.forma_pagamento)}</td>
            <td class="text-right">${formatCurrency(venda.valor_total)}</td>
            <td>${new Date(venda.data_emissao).toLocaleString('pt-BR')}</td>
        `;
        paymentsTable.appendChild(row);
    }
}

// Função para agregar pagamentos e remover duplicatas
function agregarPagamentos(pagamentos) {
    if (!pagamentos || !Array.isArray(pagamentos)) return [];
    
    const agregados = new Map();
    
    pagamentos.forEach(pag => {
        // Criar chave única baseada na forma de pagamento e data
        const data = new Date(pag.data);
        const dataFormatada = data.toISOString().split('T')[0]; // YYYY-MM-DD
        const chave = `${pag.forma_pagamento}-${dataFormatada}`;
        
        if (agregados.has(chave)) {
            // Somar valores de pagamentos duplicados
            const existing = agregados.get(chave);
            existing.valor = parseFloat(existing.valor) + parseFloat(pag.valor);
        } else {
            // Adicionar novo pagamento
            agregados.set(chave, {
                forma_pagamento: pag.forma_pagamento,
                valor: parseFloat(pag.valor),
                data: pag.data
            });
        }
    });
    
    return Array.from(agregados.values());
}

// Função auxiliar para definir texto de forma segura
function safeSetText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text || '';
    }
}
function safeSetText(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) el.textContent = text;
}

function formatCEP(cep) {
    if (!cep) return '';
    return cep.replace(/(\d{5})(\d{3})/, '$1-$2');
}

function formatPaymentMethod(method) {
    const methods = {
        'pix_fabiano': 'Pix (Fabiano)',
        'pix_edfrance': 'Pix (Edfrance)',
        'pix_loja': 'Pix (Loja)',
        'pix_maquineta': 'Pix (Maquineta)',
        'dinheiro': 'Dinheiro',
        'cartao_credito': 'Cartão de Crédito',
        'cartao_debito': 'Cartão de Débito',
        'a_prazo': 'A Prazo'
    };
    return methods[method] || method;
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

// Função para iniciar a atualização periódica do saldo
function startBalanceAutoUpdate() {
    // Atualiza imediatamente e depois a cada 10 segundos
    updateBalance(true);
    if (balanceUpdateInterval) clearInterval(balanceUpdateInterval);
    balanceUpdateInterval = setInterval(() => updateBalance(true), 10000);
}

// Função modificada para atualizar o saldo
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

        // Atualiza os valores na interface
        if (balanceVisible) {
            if (openingBalanceLabel) openingBalanceLabel.textContent = formatCurrency(data.valor_abertura);
            if (currentBalanceLabel) currentBalanceLabel.textContent = data.saldo_formatado || 'R$ 0,00';
        } else {
            if (openingBalanceLabel) openingBalanceLabel.textContent = '******';
            if (currentBalanceLabel) currentBalanceLabel.textContent = '******';
        }
        
        // Atualiza o saldo atual na variável global
        currentBalance = data.saldo || 0;
        
        // Dispara evento personalizado para notificar outras partes do sistema
        document.dispatchEvent(new CustomEvent('balanceUpdated', { detail: data }));
        
    } catch (error) {
        console.error('Error updating balance:', error);
        if (openingBalanceLabel) openingBalanceLabel.textContent = 'Erro';
        if (currentBalanceLabel) currentBalanceLabel.textContent = '';
    }
}

async function closeRegister() {
    // Criar o modal dinamicamente
    const modal = document.createElement('div');
    modal.className = 'custom-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>Fechamento de Caixa</h3>
            <div class="form-group">
                <label for="fechamento-valor">Valor de Fechamento:</label>
                <input type="text" id="fechamento-valor" class="currency-input" placeholder="0,00">
            </div>
            <div class="modal-buttons">
                <button id="confirm-fechamento" class="btn-primary">Confirmar</button>
                <button id="cancel-fechamento" class="btn-secondary">Cancelar</button>
            </div>
        </div>
    `;
    
    // Adicionar ao corpo do documento
    document.body.appendChild(modal);
    
    // Adicionar estilos básicos (você pode mover isso para seu CSS)
    const style = document.createElement('style');
    style.textContent = `
        .custom-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .custom-modal .modal-content {
            background: white;
            padding: 20px;
            border-radius: 8px;
            width: 90%;
            max-width: 400px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        .custom-modal .form-group {
            margin-bottom: 15px;
        }
        .custom-modal label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .custom-modal input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .custom-modal .modal-buttons {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 20px;
        }
    `;
    document.head.appendChild(style);
    
    // Configurar máscara para o input de valor
    const valorInput = document.getElementById('fechamento-valor');
    if (valorInput) {
        valorInput.addEventListener('input', function(e) {
            // Formatação para moeda
            let value = e.target.value.replace(/\D/g, '');
            value = (value/100).toLocaleString('pt-BR', {
                style: 'decimal',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
            e.target.value = value;
        });
    }
    
    // Retornar uma Promise que resolve quando o modal é confirmado ou rejeitado
    return new Promise(async (resolve, reject) => {
        // Evento de confirmação
        document.getElementById('confirm-fechamento')?.addEventListener('click', async () => {
            const valorText = valorInput?.value.replace(/\./g, '').replace(',', '.');
            const valorNumerico = parseFloat(valorText);
            
            if (!valorText || isNaN(valorNumerico) || valorNumerico <= 0) {
                showMessage('Valor de fechamento inválido', 'error');
                return;
            }
            
            try {
                const response = await fetch('/operador/api/fechar-caixa', {
                    ...preventCacheConfig,
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ valor_fechamento: valorNumerico })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Erro ao fechar caixa');
                }

                const now = new Date();
                showMessage(`Caixa fechado às ${now.toLocaleTimeString('pt-BR')}`);
                await checkCaixaStatus();
                
                // Remover modal e estilos
                modal.remove();
                style.remove();
                
                resolve(true);
            } catch (error) {
                showMessage(error.message, 'error');
                reject(error);
            }
        });
        
        // Evento de cancelamento
        document.getElementById('cancel-fechamento')?.addEventListener('click', () => {
            showMessage('Operação cancelada', 'warning');
            modal.remove();
            style.remove();
            resolve(false);
        });
    });
}

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
function showSearchResults(results, containerId, type) {
    const resultsContainer = document.getElementById(containerId);
    if (!resultsContainer) return;
    resultsContainer.innerHTML = '';

    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">Nenhum resultado encontrado</div>';
        resultsContainer.style.display = 'block';
        return;
    }

    results.forEach((item, index) => {
        const resultItem = document.createElement('div');
        resultItem.className = 'search-result-item';
        resultItem.dataset.id = item.id;
        resultItem.tabIndex = 0; // Torna o item focável
        
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
        
        // Permite selecionar com Enter quando o item está focado
        resultItem.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                resultItem.click();
            }
        });
        
        resultsContainer.appendChild(resultItem);
    });

    // Seleciona automaticamente o primeiro item
    if (results.length > 0) {
        resultsContainer.querySelector('.search-result-item').classList.add('selected');
    }

    resultsContainer.style.display = 'block';
    activeSearchDropdown = resultsContainer;
}

async function searchClients(searchTerm) {
    try {
        const response = await fetch(`/operador/api/clientes/buscar?q=${encodeURIComponent(searchTerm)}&timestamp=${new Date().getTime()}`, {
            ...preventCacheConfig,
            method: 'GET'
        });
        if (!response.ok) throw new Error('Erro ao buscar clientes');
        const results = await response.json();
        showClientSearchResults(results);
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

function showClientResultsDropdown(clients) {
    const dropdown = document.getElementById('client-search-results');
    if (!dropdown) return;
    dropdown.innerHTML = '';
    
    clients.forEach(client => {
        const item = document.createElement('div');
        item.className = 'client-result-item';
        item.innerHTML = `
            <div class="client-info">
                <strong>${client.nome}</strong>
                <div class="client-details">
                    <span>${client.documento ? 'CPF: ' + formatDocument(client.documento) : ''}</span>
                    <span>${client.telefone ? 'Tel: ' + formatPhone(client.telefone) : ''}</span>
                </div>
            </div>
        `;
        item.addEventListener('click', () => {
            selectClient(client);
            dropdown.innerHTML = '';
            clientSearchInput.value = '';
        });
        dropdown.appendChild(item);
    });
    dropdown.style.display = 'block';
}

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

function closeAllDropdowns() {
    document.querySelectorAll('.search-results-dropdown').forEach(dropdown => {
        dropdown.style.display = 'none';
        dropdown.querySelectorAll('.search-result-item').forEach(item => {
            item.classList.remove('selected');
        });
    });
    activeSearchDropdown = null;
}

// ==================== FUNÇÕES UTILITÁRIAS ====================
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

function toggleBalance() {
    balanceVisible = !balanceVisible;
    updateBalance();
    if (toggleBalanceBtn) {
        toggleBalanceBtn.innerHTML = balanceVisible ? '<i class="fas fa-eye-slash"></i>' : '<i class="fas fa-eye"></i>';
    }
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
    if (activeTabBtn && currentTabTitle) {
        const span = activeTabBtn.querySelector('span');
        if (span) currentTabTitle.textContent = span.textContent;
    }
    if (tabId === 'day-sales') {
        loadDaySales();
    }
}

function openModal(type) {
    const modal = document.getElementById(`${type}-modal`);
    if (modal) modal.style.display = 'flex';
}

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
function setupEventListeners() {
    if (toggleBalanceBtn) toggleBalanceBtn.addEventListener('click', toggleBalance);
    if (tabBtns) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => switchTab(btn.dataset.tab));
        });
    }
    if (clientSearchInput) {
    clientSearchInput.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown' && activeSearchDropdown) {
            e.preventDefault();
            navigateSearchResults('down');
        }
    })};
    if (productSearchInput) {
    productSearchInput.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown' && activeSearchDropdown) {
            e.preventDefault();
            navigateSearchResults('down');
        }
    })};
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            window.location.href = '/logout?' + new Date().getTime();
        });
    }
    const searchClientBtn = document.getElementById('search-client-btn');
    if (searchClientBtn) searchClientBtn.addEventListener('click', searchClient);
    if (clientSearchInput) {
        clientSearchInput.addEventListener('focus', function() {
            showClientSearchResults(clients);
        });
        clientSearchInput.addEventListener('input', function(e) {
            clearTimeout(clientSearchTimeout);
            const searchTerm = e.target.value.trim();
            if (searchTerm.length >= 2) {
                clientSearchTimeout = setTimeout(() => {
                    searchClients(searchTerm);
                }, 300);
            } else if (searchTerm.length === 0) {
                showClientSearchResults(clients);
            }
        });
        clientSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const searchTerm = clientSearchInput.value.trim();
                if (searchTerm) searchClients(searchTerm);
            }
        });
    }
    const addClientBtn = document.getElementById('add-client-btn');
    if (addClientBtn) addClientBtn.addEventListener('click', openClientModal);
    const searchProductBtn = document.getElementById('search-product-btn');
    if (searchProductBtn) searchProductBtn.addEventListener('click', openProductSearchModal);
    if (productSearchInput) {
        productSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') openProductSearchModal();
        });
    }
    if (addProductBtn) addProductBtn.addEventListener('click', addEmptyProductRow);
    if (modalCloses) {
        modalCloses.forEach(btn => {
            btn.addEventListener('click', closeModal);
        });
    }
    const saveClientBtn = document.getElementById('save-client');
    if (saveClientBtn) saveClientBtn.addEventListener('click', saveClient);
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
    document.addEventListener('balanceUpdated', (event) => console.log('Saldo atualizado:', event.detail));
    document.getElementById('day-sales-tab')?.addEventListener('click', loadDaySales);
    if (amountReceivedInput) {
        amountReceivedInput.addEventListener('input', calculateSaleTotal);
    }
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
    const removeClientBtn = document.getElementById("remove-selected-client-btn");
    if (removeClientBtn) {
        removeClientBtn.addEventListener("click", function() {
            if (selectedClientInput) selectedClientInput.value = "";
            if (selectedClientIdInput) selectedClientIdInput.value = "";
            updateCaixaStatus();
        });
    }
    
    const paymentMethodSelect = document.getElementById('payment-method');
    if (paymentMethodSelect) {
        paymentMethodSelect.addEventListener('change', function() {
            if (this.value === 'dinheiro' && amountReceivedInput) {
                const totalText = saleTotalElement.textContent.replace('R$ ', '').replace(/\./g, '').replace(',', '.');
                const total = parseFloat(totalText) || 0;
                amountReceivedInput.value = total.toFixed(2).replace('.', ',');
                const event = new Event('input', { bubbles: true });
                amountReceivedInput.dispatchEvent(event);
            } else if (this.value === 'a_prazo' && amountReceivedInput) {
                amountReceivedInput.value = '0,00';
                const event = new Event('input', { bubbles: true });
                amountReceivedInput.dispatchEvent(event);
            }
        });
    }
    
    // Adiciona listeners para múltiplas formas de pagamento
    document.querySelector('.add-payment-method')?.addEventListener('click', addPaymentMethod);
    document.querySelector('.payment-amount')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addPaymentMethod();
        }
    });
}

// ==================== FUNÇÕES PARA MÚLTIPLAS FORMAS DE PAGAMENTO ====================
function addPaymentMethod() {
    const paymentMethodSelect = document.querySelector('.payment-method-select');
    const paymentAmountInput = document.querySelector('.payment-amount');
    const selectedPaymentsList = document.querySelector('.selected-payments-list');
    
    if (!paymentMethodSelect || !paymentAmountInput || !selectedPaymentsList) return;
    
    const method = paymentMethodSelect.value;
    const amountText = paymentAmountInput.value.replace(/\./g, '').replace(',', '.');
    const amount = parseFloat(amountText);
    
    if (!method) {
        showMessage('Selecione uma forma de pagamento', 'error');
        return;
    }
    
    if (isNaN(amount) || amount <= 0) {
        showMessage('Digite um valor válido para o pagamento', 'error');
        return;
    }
    
    const paymentItem = document.createElement('div');
    paymentItem.className = 'payment-item';
    paymentItem.innerHTML = `
        <input type="hidden" name="payment_methods[]" value="${method}">
        <input type="hidden" name="payment_amounts[]" value="${amount.toFixed(2).replace('.', ',')}">
        <span class="payment-method">${formatPaymentMethod(method)}</span>
        <span class="payment-amount">${formatCurrency(amount)}</span>
        <button class="btn-remove-payment" title="Remover pagamento">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    selectedPaymentsList.appendChild(paymentItem);
    
    // Adiciona listener para o botão de remover
    paymentItem.querySelector('.btn-remove-payment').addEventListener('click', function() {
        paymentItem.remove();
        calculateSaleTotal();
    });
    
    // Limpa os campos
    paymentMethodSelect.value = '';
    paymentAmountInput.value = '';
    
    // Calcula o total novamente
    calculateSaleTotal();
}

// ==================== INICIALIZAÇÃO ADICIONAL ====================
document.addEventListener('DOMContentLoaded', function() {
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
    if (openExpenseModalBtn) openExpenseModalBtn.addEventListener('click', openExpenseModal);
    if (cancelExpenseBtn) cancelExpenseBtn.addEventListener('click', closeExpenseModal);
    if (saveExpenseBtn) saveExpenseBtn.addEventListener('click', saveExpense);
    document.getElementById('generate-pdf-btn')?.addEventListener('click', generateDaySalesPDF);
    document.getElementById('confirm-void-sale')?.addEventListener('click', voidSale);
    document.getElementById('cancel-void-sale')?.addEventListener('click', () => {
        closeModal('void-sale-modal');
    });
});