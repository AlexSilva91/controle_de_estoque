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
const openingBalanceLabel = document
  .getElementById('opening-balance')
  ?.querySelector('.balance-value');
const currentBalanceLabel = document
  .getElementById('current-balance')
  ?.querySelector('.balance-value');
const currentMoneyLabel = document
  .getElementById('current-money')
  ?.querySelector('.balance-value');
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
    Pragma: 'no-cache',
    Expires: '0',
  },
};

// ==================== ATALHOS DE TECLADO ====================
const keyMap = {
  F1: showHelpMenu,
  F2: () => switchTab('sales'),
  F3: () => switchTab('day-sales'),
  F4: () => switchTab('clients'),
  F5: loadClients,
  F6: openClientModal,
  F7: openProductSearchModal,
  F8: openExpenseModal,
  F9: registerSale,
  F10: () => document.getElementById('amount-received')?.focus(),
  Escape: closeModal,
  'Ctrl+1': () => document.getElementById('client-search-input')?.focus(),
  'Ctrl+2': () => document.getElementById('product-search-input')?.focus(),
  'Ctrl+D': applyManualDiscount,
  'Ctrl+L': resetSaleForm,
  'Ctrl+Q': () => logoutBtn?.click(),
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
        const selectedItem = activeSearchDropdown.querySelector(
          '.search-result-item.selected',
        );
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
    await new Promise((resolve) => setTimeout(resolve, 100));
    updateCurrentDate();
    await loadCurrentUser();
    await loadClients();
    await loadProducts();
    await checkCaixaStatus();
    setupEventListeners();
    setupDiscountControls();
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
      method: 'GET',
    });
    if (!response.ok) throw new Error('Erro ao carregar dados do usuário');
    currentUser = await response.json();
  } catch (error) {
    showMessage(error.message, 'error');
  }
}

// ==================== FUNÇÕES DE CLIENTES ====================
// Variáveis globais para paginação
let currentPage = 1;
const clientsPerPage = 10;
let totalPages = 1;
let totalClients = 0;
let currentSearchTerm = '';

async function loadClients(page = 1, searchTerm = '') {
  try {
    showClientsLoading(true);
    currentPage = page;
    currentSearchTerm = searchTerm;

    let url = `/operador/api/clientes?page=${page}&per_page=${clientsPerPage}`;
    if (searchTerm) {
      url += `&search=${encodeURIComponent(searchTerm)}`;
    }

    const response = await fetch(url, {
      ...preventCacheConfig,
      method: 'GET',
    });

    if (!response.ok) throw new Error('Erro ao carregar clientes');

    const data = await response.json();
    clients = data.clientes;
    filteredClients = [...clients];

    totalPages = data.pagination.pages;
    totalClients = data.pagination.total;

    renderClientsTable();
    updateClientsCount();
    renderPagination();
  } catch (error) {
    const tbody = document.getElementById('clients-tbody');
    if (tbody) {
      tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 20px; color: #dc3545;">
                        <i class="fas fa-exclamation-circle"></i> ${error.message}
                    </td>
                </tr>
            `;
    }
    showClientsEmptyState(false);
  } finally {
    showClientsLoading(false);
  }
}

function renderClientsTable() {
  const tbody = document.getElementById('clients-tbody');
  if (!tbody) return;

  if (filteredClients.length === 0) {
    if (currentSearchTerm) {
      tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 20px; color: #6c757d;">
                        <i class="fas fa-search"></i> Nenhum cliente encontrado para "${currentSearchTerm}"
                    </td>
                </tr>
            `;
    } else {
      showClientsEmptyState(true);
    }
    return;
  }

  showClientsEmptyState(false);
  tbody.innerHTML = filteredClients
    .map(
      (client) => `
        <tr class="client-row" data-client-id="${client.id}">
            <td class="client-id">#${client.id}</td>
            <td class="client-name">
                <div class="client-name-container">
                    <strong>${client.nome || 'Não informado'}</strong>
                    ${
                      client.apelido
                        ? `<small class="client-nickname">(${client.apelido})</small>`
                        : ''
                    }
                </div>
            </td>
            <td class="client-document">
                <span class="document-value">${
                  formatDocument(client.documento) || 'Não informado'
                }</span>
            </td>
            <td class="client-phone">
                ${
                  client.telefone
                    ? `
                    <a href="tel:${client.telefone}" class="phone-link">
                        <i class="fas fa-phone"></i>
                        ${formatPhone(client.telefone)}
                    </a>
                `
                    : '<span class="text-muted">Não informado</span>'
                }
            </td>
            <td class="client-email">
                ${
                  client.email
                    ? `
                    <a href="mailto:${client.email}" class="email-link">
                        <i class="fas fa-envelope"></i>
                        ${client.email}
                    </a>
                `
                    : '<span class="text-muted">Não informado</span>'
                }
            </td>
            <td class="client-address">
                <div class="address-container">
                    ${
                      client.endereco
                        ? `
                        <span class="address-text" title="${client.endereco}">
                            ${truncateText(client.endereco, 30)}
                        </span>
                    `
                        : '<span class="text-muted">Não informado</span>'
                    }
                </div>
            </td>
            <td class="client-actions">
                <div class="action-buttons">
                    <button class="btn-action btn-edit" onclick="editClient(${
                      client.id
                    })" title="Editar cliente">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-action btn-view" onclick="viewClientDetails(${
                      client.id
                    })" title="Ver detalhes">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </td>
        </tr>
    `,
    )
    .join('');
}

function renderPagination() {
  const paginationContainer = document.getElementById('pagination-controls');
  if (!paginationContainer) return;

  if (totalPages <= 1) {
    paginationContainer.innerHTML = '';
    return;
  }

  let paginationHTML = '';

  // Botão anterior
  if (currentPage > 1) {
    paginationHTML += `<button class="pagination-btn" onclick="loadClients(${
      currentPage - 1
    }, '${currentSearchTerm}')">
            <i class="fas fa-chevron-left"></i>
        </button>`;
  } else {
    paginationHTML += `<button class="pagination-btn disabled" disabled>
            <i class="fas fa-chevron-left"></i>
        </button>`;
  }

  // Páginas
  const startPage = Math.max(1, currentPage - 2);
  const endPage = Math.min(totalPages, currentPage + 2);

  if (startPage > 1) {
    paginationHTML += `<button class="pagination-btn" onclick="loadClients(1, '${currentSearchTerm}')">1</button>`;
    if (startPage > 2) {
      paginationHTML += `<span class="pagination-ellipsis">...</span>`;
    }
  }

  for (let i = startPage; i <= endPage; i++) {
    if (i === currentPage) {
      paginationHTML += `<button class="pagination-btn active">${i}</button>`;
    } else {
      paginationHTML += `<button class="pagination-btn" onclick="loadClients(${i}, '${currentSearchTerm}')">${i}</button>`;
    }
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      paginationHTML += `<span class="pagination-ellipsis">...</span>`;
    }
    paginationHTML += `<button class="pagination-btn" onclick="loadClients(${totalPages}, '${currentSearchTerm}')">${totalPages}</button>`;
  }

  // Botão próximo
  if (currentPage < totalPages) {
    paginationHTML += `<button class="pagination-btn" onclick="loadClients(${
      currentPage + 1
    }, '${currentSearchTerm}')">
            <i class="fas fa-chevron-right"></i>
        </button>`;
  } else {
    paginationHTML += `<button class="pagination-btn disabled" disabled>
            <i class="fas fa-chevron-right"></i>
        </button>`;
  }

  paginationContainer.innerHTML = paginationHTML;
}

function updateClientsCount() {
  const countElement = document.getElementById('clients-count');
  if (countElement) {
    const startItem = (currentPage - 1) * clientsPerPage + 1;
    const endItem = Math.min(currentPage * clientsPerPage, totalClients);

    if (currentSearchTerm) {
      countElement.textContent = `Mostrando ${startItem}-${endItem} de ${totalClients} clientes (filtrado)`;
    } else {
      countElement.textContent = `Mostrando ${startItem}-${endItem} de ${totalClients} clientes`;
    }
  }
}

function filterClients(filterType) {
  currentFilter = filterType;
  const now = new Date();
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

  switch (filterType) {
    case 'recent':
      filteredClients = clients.filter(
        (client) => new Date(client.data_cadastro) >= thirtyDaysAgo,
      );
      break;
    case 'frequent':
      filteredClients = clients.filter(
        (client) => client.total_vendas && client.total_vendas > 5,
      );
      break;
    default:
      filteredClients = [...clients];
  }

  applySortAndFilter();
  renderClientsTable();
  updateClientsCount();
  document.querySelectorAll('.filter-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.filter === filterType);
  });
}

// Ordenação mantém funcionando no frontend para a página atual
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

// Funções auxiliares mantidas
function showClientsLoading(show) {
  const loading = document.getElementById('clients-loading');
  const table = document.querySelector('.clients-table-container');
  const footer = document.querySelector('.table-footer');
  if (loading) loading.style.display = show ? 'block' : 'none';
  if (table) table.style.display = show ? 'none' : 'block';
  if (footer) footer.style.display = show ? 'none' : 'flex';
}

function showClientsEmptyState(show) {
  const emptyState = document.getElementById('clients-empty-state');
  const table = document.querySelector('.clients-table-container');
  const footer = document.querySelector('.table-footer');
  if (emptyState) emptyState.style.display = show ? 'block' : 'none';
  if (table) table.style.display = show ? 'none' : 'block';
  if (footer) footer.style.display = show ? 'none' : 'flex';
}

// Variável para controlar a busca por nome
let currentNameSearch = '';

// Função para lidar com a busca por nome ao pressionar Enter
function handleNameSearch(event) {
  if (event.key === 'Enter') {
    performNameSearch();
  }
}

// Função para executar a busca por nome - CORRIGIDA
function performNameSearch() {
  const searchInput = document.getElementById('name-search-input');
  const clearButton = document.getElementById('clear-name-search');

  currentNameSearch = searchInput.value.trim();

  if (currentNameSearch) {
    clearButton.style.display = 'block';
    // Chama a função loadClients diretamente com o termo de busca
    loadClients(1, currentNameSearch);
  } else {
    clearNameSearch();
  }
}

// Função para limpar a busca por nome
function clearNameSearch() {
  const searchInput = document.getElementById('name-search-input');
  const clearButton = document.getElementById('clear-name-search');

  searchInput.value = '';
  currentNameSearch = '';
  clearButton.style.display = 'none';

  // Recarrega os clientes sem filtro
  loadClients(1, '');
}

// Inicialização do campo de busca - CORRIGIDA
document.addEventListener('DOMContentLoaded', function () {
  const searchInput = document.getElementById('name-search-input');
  const clearButton = document.getElementById('clear-name-search');

  // Event listener para o botão de limpar
  if (clearButton) {
    clearButton.addEventListener('click', clearNameSearch);
  }

  // Event listener para input (busca em tempo real opcional)
  if (searchInput) {
    // Opcional: busca em tempo real com debounce
    let searchTimeout;
    searchInput.addEventListener('input', function () {
      clearTimeout(searchTimeout);

      // Se o campo ficar vazio, limpa a busca
      if (this.value.trim() === '') {
        clearNameSearch();
        return;
      }

      // Busca automática após 1 segundo (opcional)
      searchTimeout = setTimeout(() => {
        currentNameSearch = this.value.trim();
        if (currentNameSearch) {
          clearButton.style.display = 'block';
          loadClients(1, currentNameSearch);
        }
      }, 1000);
    });

    // Foco no campo de busca quando a página carregar
    searchInput.focus();
  }

  // Carrega os clientes inicialmente
  loadClients(1);
});

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
    const response = await fetch(
      `/operador/api/clientes/buscar?q=${encodeURIComponent(
        searchTerm,
      )}&timestamp=${new Date().getTime()}`,
      {
        ...preventCacheConfig,
        method: 'GET',
      },
    );
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
    const client = clients.find((c) => c.id == clientId);
    if (client) return client;
  }

  // Se não encontrou, tenta extrair da tabela HTML (fallback)
  const clientRow = document.querySelector(`[data-client-id="${clientId}"]`);
  if (clientRow) {
    return {
      id: clientId,
      nome:
        clientRow.querySelector('.client-name strong')?.textContent ||
        `Cliente ${clientId}`,
      documento: clientRow.querySelector('.document-value')?.textContent || '',
      telefone:
        clientRow.querySelector('.phone-link')?.textContent.replace(/\D/g, '') || '',
      email: clientRow.querySelector('.email-link')?.textContent || '',
      endereco: clientRow.querySelector('.address-text')?.textContent || '',
    };
  }

  return null;
}

// Função para fechar modal (opcional)
function closeClientModal() {
  const modal =
    document.getElementById('clientModal') || document.querySelector('.client-modal');
  if (modal) {
    modal.style.display = 'none';
    modal.classList.remove('active');
  }
}

function selectClient(client) {
  if (!client) {
    // Define o cliente padrão quando nenhum cliente é selecionado
    selectedClient = {
      id: 1,
      nome: 'PADRÃO',
      documento: '',
      telefone: '',
      email: '',
      endereco: '',
    };
    selectedClientInput.value = 'PADRÃO'; // Mostra que está usando o padrão
    selectedClientIdInput.value = '1'; // ID 1 para o cliente padrão
  } else {
    // Atribui o cliente selecionado
    selectedClient = client;
    selectedClientInput.value = client.nome; // Exibe o nome do cliente
    selectedClientIdInput.value = client.id.toString();
  }
  updateCaixaStatus();
}
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
    resultsContainer.innerHTML =
      '<div class="no-results">Nenhum cliente encontrado</div>';
    resultsContainer.style.display = 'block';
    return;
  }

  clients.forEach((client) => {
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

  clientsToRender.forEach((client) => {
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

  document.querySelectorAll('.btn-edit-client').forEach((btn) => {
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
  const client = clients.find((c) => c.id == clientId);
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
    endereco: document.getElementById('client-address')?.value,
  };

  try {
    let response;
    if (currentEditingClient) {
      response = await fetch(`/operador/api/clientes/${currentEditingClient.id}`, {
        ...preventCacheConfig,
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(clientData),
      });
    } else {
      response = await fetch('/operador/api/clientes', {
        ...preventCacheConfig,
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(clientData),
      });
    }

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Erro ao salvar cliente');
    }

    showMessage(
      currentEditingClient
        ? 'Cliente atualizado com sucesso!'
        : 'Cliente cadastrado com sucesso!',
    );
    await loadClients();
    closeModal();
  } catch (error) {
    showMessage(error.message, 'error');
  }
}

async function viewClientDetails(clientId) {
  try {
    const client = await findClientById(clientId);

    if (!client) {
      showMessage('Cliente não encontrado', 'error');
      return;
    }

    const response = await fetch(`/operador/api/clientes/${clientId}/contas_receber`);

    if (!response.ok) {
      throw new Error('Erro ao buscar contas a receber');
    }

    const contasReceber = await response.json();

    // Separar contas abertas e pagas
    const contasAbertas = contasReceber.filter(
      (conta) => conta.status === 'pendente' || conta.status === 'parcial',
    );

    const contasPagas = contasReceber.filter((conta) => conta.status === 'quitado');

    let totalValorAberto = 0;
    let totalValorPago = 0;
    let totalValorOriginal = 0;
    let totalPagamentosNota = 0;
    let totalPagamentosConta = 0;

    contasReceber.forEach((conta) => {
      totalValorOriginal += conta.valor_original || 0;
      const valorAberto = conta.valor_aberto || 0;
      const valorPago = (conta.valor_original || 0) - valorAberto;

      totalValorAberto += valorAberto;
      totalValorPago += valorPago;
      totalPagamentosNota += conta.total_pago_nota || 0;
      totalPagamentosConta += conta.total_pago_conta || 0;
    });

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'client-details-modal';
    modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Detalhes do Cliente</h3>
                    <span class="modal-close">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="client-info-section">
                        <h4>Informações Básicas</h4>
                        <div class="client-detail">
                            <label>Nome:</label>
                            <p>${client.nome || 'Não informado'}</p>
                        </div>
                    </div>
                    
                    <div class="finance-summary-section">
                        <h4>Resumo Financeiro</h4>
                        <div class="summary-cards">
                            <div class="summary-card">
                                <div class="summary-label">Total em Aberto</div>
                                <div class="summary-value open-value">${formatCurrency(
                                  totalValorAberto,
                                )}</div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-label">Total Pago</div>
                                <div class="summary-value paid-value">${formatCurrency(
                                  totalValorPago,
                                )}</div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-label">Total Original</div>
                                <div class="summary-value original-value">${formatCurrency(
                                  totalValorOriginal,
                                )}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="contas-section">
                        <!-- Seção de Contas Abertas -->
                        <div class="contas-abertas-section collapsible-menu">
                            <div class="section-header collapsible-menu-header" data-toggle="collapse">
                                <span class="collapse-icon">▼</span>
                                <h4>Contas Abertas (${contasAbertas.length})</h4>
                            </div>
                            
                            <div class="contas-list collapsible-menu-content">
                                ${
                                  contasAbertas.length > 0
                                    ? contasAbertas
                                        .map((conta) => createContaCard(conta))
                                        .join('')
                                    : '<p class="no-accounts">Nenhuma conta em aberto</p>'
                                }
                            </div>
                        </div>
                        
                        <!-- Seção de Contas Pagas -->
                        <div class="contas-pagas-section collapsible-menu">
                            <div class="section-header collapsible-menu-header" data-toggle="collapse">
                                <span class="collapse-icon">▶</span>
                                <h4>Contas Pagas (${contasPagas.length})</h4>
                            </div>
                            
                            <div class="contas-list collapsible-menu-content" style="display: none;">
                                ${
                                  contasPagas.length > 0
                                    ? contasPagas
                                        .map((conta) => createContaCard(conta))
                                        .join('')
                                    : '<p class="no-accounts">Nenhuma conta paga</p>'
                                }
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary modal-close">Fechar</button>
                </div>
            </div>
        `;

    document.body.appendChild(modal);

    // Event listeners para menus retráteis
    modal.querySelectorAll('.collapsible-menu-header').forEach((header) => {
      header.addEventListener('click', (e) => {
        const menu = header.closest('.collapsible-menu');
        const content = menu.querySelector('.collapsible-menu-content');
        const icon = menu.querySelector('.collapse-icon');

        if (content.style.display === 'none') {
          content.style.display = 'block';
          icon.textContent = '▼';
        } else {
          content.style.display = 'none';
          icon.textContent = '▶';
        }
      });
    });

    // Event listeners para expandir/colapsar contas individuais
    modal.querySelectorAll('.conta-header-collapsible').forEach((header) => {
      header.addEventListener('click', (e) => {
        // Evita que cliques em botões acionem o toggle
        if (e.target.closest('button')) return;

        const card = header.closest('.conta-receber-card');
        const details = card.querySelector('.conta-details-collapsible');
        const icon = card.querySelector('.collapse-icon');

        if (details.style.display === 'none') {
          details.style.display = 'block';
          icon.textContent = '▼';
          card.classList.add('expanded');
        } else {
          details.style.display = 'none';
          icon.textContent = '▶';
          card.classList.remove('expanded');
        }
      });
    });

    modal.querySelectorAll('.modal-close').forEach((closeBtn) => {
      closeBtn.addEventListener('click', () => {
        modal.remove();
      });
    });

    modal.style.display = 'flex';

    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });

    // Configurar botões de pagamento
    setupPaymentButtons(modal);
  } catch (error) {
    console.error('Erro ao carregar detalhes do cliente:', error);
    showMessage('Erro ao carregar detalhes do cliente', 'error');
  }
}

// Função auxiliar para criar card de conta
function createContaCard(conta) {
  const valorPagoConta = (conta.valor_original || 0) - (conta.valor_aberto || 0);
  const totalPagoGeral = conta.total_pago_geral || 0;
  const valorAindaAberto = conta.valor_ainda_aberto || 0;

  return `
        <div class="conta-receber-card collapsible" data-conta-id="${conta.id}">
            <div class="conta-header-collapsible" data-toggle="collapse">
                <span class="collapse-icon">▶</span>
                <h5>${conta.descricao || 'Conta sem descrição'}</h5>
                <span class="summary-divider">|</span>
                <span class="summary-inline">Data: <strong>${formatDate(
                  conta.data_emissao,
                )}</strong></span>
                <span class="summary-divider">|</span>
                <span class="summary-inline">Em Aberto: <strong class="highlight-open">${formatCurrency(
                  valorAindaAberto,
                )}</strong></span>
                <span class="summary-divider">|</span>
                <span class="summary-inline">Pago: <strong class="highlight-paid">${formatCurrency(
                  valorPagoConta,
                )}</strong></span>
                <span class="status-badge ${conta.status}">${conta.status}</span>
            </div>
            
            <div class="conta-details-collapsible" style="display: none;">
                <div class="conta-info-grid">
                    ${
                      conta.observacoes
                        ? `
                        <div class="info-item full-width">
                            <strong>Observações:</strong> ${conta.observacoes}
                        </div>
                    `
                        : ''
                    }
                </div>
                
                ${
                  conta.pagamentos_nota_fiscal &&
                  conta.pagamentos_nota_fiscal.length > 0
                    ? `
                    <div class="pagamentos-section">
                        <h6>Formas de Pagamento Utilizadas</h6>
                        <div class="table-container">
                            <table class="pagamentos-table">
                                <thead>
                                    <tr>
                                        <th>Forma</th>
                                        <th>Valor</th>
                                        <th>Data</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${conta.pagamentos_nota_fiscal
                                      .map(
                                        (pag) => `
                                        <tr>
                                            <td>${pag.forma_pagamento}</td>
                                            <td>${formatCurrency(pag.valor)}</td>
                                            <td>${formatDate(pag.data)}</td>
                                        </tr>
                                    `,
                                      )
                                      .join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `
                    : ''
                }
                
                ${
                  conta.pagamentos_conta_receber &&
                  conta.pagamentos_conta_receber.length > 0
                    ? `
                    <div class="pagamentos-section">
                        <h6>Valor já quitado</h6>
                        <div class="table-container">
                            <table class="pagamentos-table">
                                <thead>
                                    <tr>
                                        <th>Forma</th>
                                        <th>Valor Pago</th>
                                        <th>Data</th>
                                        ${
                                          conta.pagamentos_conta_receber.some(
                                            (p) => p.observacoes,
                                          )
                                            ? '<th>Observações</th>'
                                            : ''
                                        }
                                    </tr>
                                </thead>
                                <tbody>
                                    ${conta.pagamentos_conta_receber
                                      .map(
                                        (pag) => `
                                        <tr>
                                            <td>${pag.forma_pagamento}</td>
                                            <td>${formatCurrency(pag.valor_pago)}</td>
                                            <td>${formatDate(pag.data_pagamento)}</td>
                                            ${
                                              conta.pagamentos_conta_receber.some(
                                                (p) => p.observacoes,
                                              )
                                                ? `<td>${pag.observacoes || ''}</td>`
                                                : ''
                                            }
                                        </tr>
                                    `,
                                      )
                                      .join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `
                    : ''
                }
                
                ${
                  conta.itens_nota_fiscal && conta.itens_nota_fiscal.length > 0
                    ? `
                    <div class="produtos-section">
                        <h6>Produtos Comprados:</h6>
                        <div class="table-container">
                            <table class="produtos-table">
                                <thead>
                                    <tr>
                                        <th>Produto</th>
                                        <th>Quantidade</th>
                                        <th>Valor Unit.</th>
                                        <th>Desconto Item</th>
                                        <th>Total Item</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${conta.itens_nota_fiscal
                                      .map((item) => {
                                        const valorBrutoItem =
                                          item.quantidade * item.valor_unitario;
                                        const temDesconto = item.desconto_aplicado > 0;

                                        return `
                                        <tr>
                                            <td>${item.produto_nome}</td>
                                            <td>${item.quantidade} ${
                                              item.unidade_medida
                                            }</td>
                                            <td>
                                            ${
                                              item.valor_pos_desconto > 0
                                                ? `
                                                    <span class="valor-desconto">
                                                    ${formatCurrency(
                                                      item.valor_pos_desconto,
                                                    )}
                                                    </span>
                                                    <br>
                                                    <small class="valor-original">
                                                    <s>${formatCurrency(
                                                      item.valor_unitario,
                                                    )}</s>
                                                    </small>
                                                `
                                                : formatCurrency(item.valor_unitario)
                                            }
                                            </td>
                                            <td>
                                                ${
                                                  temDesconto
                                                    ? `${formatCurrency(
                                                        item.desconto_aplicado,
                                                      )} 
                                                     ${
                                                       item.tipo_desconto
                                                         ? `(${item.tipo_desconto})`
                                                         : ''
                                                     }`
                                                    : 'Sem desconto'
                                                }
                                            </td>
                                            <td>
                                                ${
                                                  temDesconto
                                                    ? `<span style="text-decoration: line-through; color: #999; font-size: 0.9em;">${formatCurrency(
                                                        valorBrutoItem,
                                                      )}</span><br>`
                                                    : ''
                                                }
                                                <strong>${formatCurrency(
                                                  item.valor_total,
                                                )}</strong>
                                            </td>
                                        </tr>
                                        `;
                                      })
                                      .join('')}
                                </tbody>
                                <tfoot>
                                    <tr>
                                        <td colspan="4"><strong>Subtotal dos Itens:</strong></td>
                                        <td><strong>${formatCurrency(
                                          conta.itens_nota_fiscal.reduce(
                                            (sum, item) => sum + item.valor_total,
                                            0,
                                          ),
                                        )}</strong></td>
                                    </tr>
                                    ${
                                      conta.valor_desconto_nota > 0
                                        ? `
                                        <tr>
                                            <td colspan="4">
                                                <strong>Desconto na Nota ${
                                                  conta.tipo_desconto_nota
                                                    ? `(${conta.tipo_desconto_nota})`
                                                    : ''
                                                }:</strong>
                                            </td>
                                            <td><strong style="color: var(--danger);">-${formatCurrency(
                                              conta.valor_desconto_nota,
                                            )}</strong></td>
                                        </tr>
                                    `
                                        : ''
                                    }
                                    <tr style="border-top: 2px solid var(--secondary);">
                                        <td colspan="4"><strong>Total da Nota:</strong></td>
                                        <td><strong style="color: var(--success); font-size: 1.1em;">${formatCurrency(
                                          conta.valor_total_nota,
                                        )}</strong></td>
                                    </tr>
                                </tfoot>
                            </table>
                        </div>
                        
                        <div class="venda-resumo">
                            <div class="resumo-item">
                                <span>Total de Itens:</span>
                                <strong>${conta.itens_nota_fiscal.length}</strong>
                            </div>
                            <div class="resumo-item">
                                <span>Quantidade Total:</span>
                                <strong>${conta.itens_nota_fiscal.reduce(
                                  (sum, item) => sum + item.quantidade,
                                  0,
                                )} unidades</strong>
                            </div>
                        </div>
                    </div>
                `
                    : conta.nota_fiscal_id
                      ? '<p class="no-products">Nota fiscal sem produtos cadastrados</p>'
                      : '<p class="no-products">Sem nota fiscal associada</p>'
                }
            
                <div class="conta-actions">
                    ${
                      conta.status === 'pendente' || conta.status === 'parcial'
                        ? `
                        <button class="btn-pay-partial btn-small" data-conta-id="${conta.id}" 
                            data-valor-aberto="${conta.valor_aberto}">
                            💰 Pagar Parcial
                        </button>
                        <button class="btn-pay-full btn-small" data-conta-id="${conta.id}" 
                            data-valor-aberto="${conta.valor_aberto}">
                            ✅ Pagar Total
                        </button>
                    `
                        : `
                        <span class="status-info">✅ Conta quitada</span>
                    `
                    }
                    <button class="btn-receipt btn-small" data-conta-id="${conta.id}">
                        🧾 Comprovante
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Função para configurar botões de pagamento
function setupPaymentButtons(modal) {
  modal.querySelectorAll('.btn-pay-partial').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const contaId = e.target.getAttribute('data-conta-id');
      const valorAberto = parseFloat(e.target.getAttribute('data-valor-aberto'));
      showPartialPaymentModal(contaId, valorAberto);
    });
  });

  modal.querySelectorAll('.btn-pay-full').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const contaId = e.target.getAttribute('data-conta-id');
      const valorAberto = parseFloat(e.target.getAttribute('data-valor-aberto'));
      confirmFullPayment(contaId, valorAberto);
    });
  });

  modal.querySelectorAll('.btn-receipt').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const contaId = e.target.getAttribute('data-conta-id');
      generateReceipt(contaId);
    });
  });
}

async function generateReceipt(contaId) {
  try {
    const response = await fetch(
      `/operador/api/contas_receber/${contaId}/comprovante`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      },
    );

    if (response.ok) {
      // Cria um blob do PDF e abre em nova aba
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
    } else {
      const error = await response.json();
      showMessage(`Erro ao gerar comprovante: ${error.error}`, 'error');
    }
  } catch (error) {
    console.error('Erro ao gerar comprovante:', error);
    showMessage('Erro ao gerar comprovante', 'error');
  }
}
/**
 * Mostra o modal para pagamento parcial
 */
function showPartialPaymentModal(contaId, valorAberto) {
  const paymentModal = document.createElement('div');
  paymentModal.className = 'modal';
  paymentModal.id = 'partial-payment-modal';
  paymentModal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Registrar Pagamento Parcial</h3>
                <span class="modal-close">&times;</span>
            </div>
            <div class="modal-body">
                <form id="partial-payment-form">
                    <div class="form-group">
                        <label for="payment-amount">Valor do Pagamento:</label>
                        <input type="text" id="payment-amount" name="payment-amount" 
                               placeholder="Ex: 1.950,50" required>
                        <small>Valor disponível: ${formatCurrency(valorAberto)}</small>
                    </div>
                    <div class="form-group">
                        <label for="payment-method">Forma de Pagamento:</label>
                        <select id="payment-method" name="payment-method" required>
                            <option value="">Selecione...</option>
                            <option value="pix_maquineta">PIX Maquineta</option>
                            <option value="pix_edfrance">PIX Edfranci</option>
                            <option value="pix_loja">PIX Loja</option>
                            <option value="dinheiro">Dinheiro</option>
                            <option value="cartao_credito">Cartão de Crédito</option>
                            <option value="cartao_debito">Cartão de Débito</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="payment-notes">Observações:</label>
                        <textarea id="payment-notes" name="payment-notes" 
                                  placeholder="Opcional"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary modal-close">Cancelar</button>
                <button class="btn-primary" id="confirm-partial-payment">Confirmar Pagamento</button>
            </div>
        </div>
    `;

  document.body.appendChild(paymentModal);

  // Add event listeners for closing the modal
  paymentModal.querySelectorAll('.modal-close').forEach((closeBtn) => {
    closeBtn.addEventListener('click', () => {
      paymentModal.remove();
    });
  });

  // Show the modal
  paymentModal.style.display = 'flex';

  // Close modal when clicking outside
  paymentModal.addEventListener('click', (e) => {
    if (e.target === paymentModal) {
      paymentModal.remove();
    }
  });

  // Mascara/validação do campo valor
  const amountInput = paymentModal.querySelector('#payment-amount');
  amountInput.addEventListener('input', () => {
    // Permitir apenas números, ponto e vírgula
    let value = amountInput.value.replace(/[^\d.,]/g, '');
    // Se tiver mais de uma vírgula, manter só a primeira
    const parts = value.split(',');
    if (parts.length > 2) {
      value = parts[0] + ',' + parts[1];
    }
    amountInput.value = value;
  });

  // Handle partial payment confirmation
  paymentModal
    .querySelector('#confirm-partial-payment')
    .addEventListener('click', async () => {
      const form = paymentModal.querySelector('#partial-payment-form');
      const formData = new FormData(form);

      let rawValue = formData.get('payment-amount').trim();

      // Converte valor brasileiro para float (1.950,50 -> 1950.50)
      let valorPago = parseFloat(rawValue.replace(/\./g, '').replace(',', '.'));

      const formaPagamento = formData.get('payment-method');
      const observacoes = formData.get('payment-notes');

      if (!valorPago || valorPago <= 0) {
        showMessage('Valor do pagamento inválido', 'error');
        return;
      }

      if (valorPago > valorAberto) {
        showMessage('Valor do pagamento excede o valor em aberto', 'error');
        return;
      }

      if (!formaPagamento) {
        showMessage('Selecione uma forma de pagamento', 'error');
        return;
      }

      try {
        const response = await registerPayment(
          contaId,
          valorPago,
          formaPagamento,
          observacoes,
        );

        if (response.success) {
          showMessage('Pagamento registrado com sucesso', 'success');
          paymentModal.remove();

          // Recarrega os dados do cliente para atualizar a tabela
          const clientId = await getClientIdFromConta(contaId);
          if (clientId) {
            // Fecha o modal atual e abre um novo com os dados atualizados
            document.querySelector('#client-details-modal')?.remove();
            viewClientDetails(clientId);
          }
        } else {
          showMessage(response.message || 'Erro ao registrar pagamento', 'error');
        }
      } catch (error) {
        console.error('Erro ao registrar pagamento:', error);
        showMessage('Erro ao registrar pagamento', 'error');
      }
    });
}

/**
 * Confirma o pagamento total
 */
async function confirmFullPayment(contaId, valorAberto) {
  const confirmModal = document.createElement('div');
  confirmModal.className = 'modal';
  confirmModal.id = 'confirm-payment-modal';
  confirmModal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Confirmar Pagamento Total</h3>
                <span class="modal-close">&times;</span>
            </div>
            <div class="modal-body">
                <p>Deseja registrar o pagamento total de ${formatCurrency(
                  valorAberto,
                )}?</p>
                <form id="full-payment-form">
                    <div class="form-group">
                        <label for="payment-method">Forma de Pagamento:</label>
                        <select id="payment-method" name="payment-method" required>
                            <option value="">Selecione...</option>
                            <option value="pix_maquineta">PIX Maquineta</option>
                            <option value="pix_edfrance">PIX Edfranci</option>
                            <option value="pix_loja">PIX Loja</option>
                            <option value="dinheiro">Dinheiro</option>
                            <option value="cartao_credito">Cartão de Crédito</option>
                            <option value="cartao_debito">Cartão de Débito</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="payment-notes">Observações:</label>
                        <textarea id="payment-notes" name="payment-notes" 
                                  placeholder="Opcional"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary modal-close">Cancelar</button>
                <button class="btn-primary" id="confirm-full-payment">Confirmar Pagamento</button>
            </div>
        </div>
    `;

  document.body.appendChild(confirmModal);

  // Add event listeners for closing the modal
  confirmModal.querySelectorAll('.modal-close').forEach((closeBtn) => {
    closeBtn.addEventListener('click', () => {
      confirmModal.remove();
    });
  });

  // Show the modal
  confirmModal.style.display = 'flex';

  // Close modal when clicking outside
  confirmModal.addEventListener('click', (e) => {
    if (e.target === confirmModal) {
      confirmModal.remove();
    }
  });

  // Handle full payment confirmation
  confirmModal
    .querySelector('#confirm-full-payment')
    .addEventListener('click', async () => {
      const form = confirmModal.querySelector('#full-payment-form');
      const formData = new FormData(form);

      const formaPagamento = formData.get('payment-method');
      const observacoes = formData.get('payment-notes');

      if (!formaPagamento) {
        showMessage('Selecione uma forma de pagamento', 'error');
        return;
      }

      try {
        const response = await registerPayment(
          contaId,
          valorAberto,
          formaPagamento,
          observacoes,
        );

        if (response.success) {
          showMessage('Pagamento total registrado com sucesso', 'success');
          confirmModal.remove();

          // Recarrega os dados do cliente para atualizar a tabela
          const clientId = await getClientIdFromConta(contaId);
          if (clientId) {
            // Fecha o modal atual e abre um novo com os dados atualizados
            document.querySelector('#client-details-modal')?.remove();
            viewClientDetails(clientId);
          }
        } else {
          showMessage(response.message || 'Erro ao registrar pagamento', 'error');
        }
      } catch (error) {
        console.error('Erro ao registrar pagamento:', error);
        showMessage('Erro ao registrar pagamento', 'error');
      }
    });
}

/**
 * Registra um pagamento no servidor
 */
async function registerPayment(contaId, valorPago, formaPagamento, observacoes) {
  try {
    const response = await fetch(`/operador/api/contas_receber/${contaId}/pagamento`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        valor_pago: valorPago.toFixed(2),
        forma_pagamento: formaPagamento,
        observacoes: observacoes,
      }),
    });
    updateBalance(true);
    return await response.json();
  } catch (error) {
    console.error('Erro ao registrar pagamento:', error);
    throw error;
  }
}

/**
 * Obtém o ID do cliente a partir do ID da conta
 */
async function getClientIdFromConta(contaId) {
  try {
    const response = await fetch(`/operador/api/contas_receber/${contaId}/cliente`);

    if (!response.ok) {
      throw new Error('Erro ao buscar cliente da conta');
    }

    const data = await response.json();
    return data.cliente_id;
  } catch (error) {
    console.error('Erro ao buscar cliente da conta:', error);
    return null;
  }
}

/**
 * Formata um valor monetário
 */
function formatCurrency(value) {
  if (value === null || value === undefined) return 'R$ 0,00';
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

/**
 * Formata uma data (sem hora)
 */
function formatDate(dateString) {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'N/A';

    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();

    return `${day}/${month}/${year}`;
  } catch (e) {
    console.error('Erro ao formatar data:', e);
    return 'N/A';
  }
}

/**
 * Formata data e hora
 */
function formatDateTime(dateTimeString) {
  if (!dateTimeString) return 'N/A';
  try {
    const date = new Date(dateTimeString);
    if (isNaN(date.getTime())) return 'N/A';

    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');

    return `${day}/${month}/${year} ${hours}:${minutes}`;
  } catch (e) {
    console.error('Erro ao formatar data/hora:', e);
    return 'N/A';
  }
}

/**
 * Formata documento (CPF/CNPJ)
 */
function formatDocument(doc) {
  if (!doc) return '';

  // Remove caracteres não numéricos
  const cleanDoc = doc.replace(/\D/g, '');

  // Formata como CPF (11 dígitos)
  if (cleanDoc.length === 11) {
    return cleanDoc.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  }

  // Formata como CNPJ (14 dígitos)
  if (cleanDoc.length === 14) {
    return cleanDoc.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
  }

  // Retorna o original se não for CPF nem CNPJ
  return doc;
}

/**
 * Formata telefone
 */
function formatPhone(phone) {
  if (!phone) return '';

  // Remove caracteres não numéricos
  const cleanPhone = phone.replace(/\D/g, '');

  // Formata como celular com 9º dígito (11 dígitos)
  if (cleanPhone.length === 11) {
    return cleanPhone.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
  }

  // Formata como telefone fixo (10 dígitos)
  if (cleanPhone.length === 10) {
    return cleanPhone.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  }

  // Retorna o original se não corresponder aos padrões
  return phone;
}

/**
 * Exibe uma mensagem para o usuário
 */
function showMessage(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 5000);
}

/**
 * Busca um cliente pelo ID
 */
async function findClientById(clientId) {
  try {
    const response = await fetch(`/operador/api/clientes/${clientId}`);

    if (!response.ok) {
      throw new Error('Erro ao buscar cliente');
    }

    return await response.json();
  } catch (error) {
    console.error('Erro ao buscar cliente:', error);
    return null;
  }
}

/**
 * Busca contas a receber de um cliente
 */
async function findContasReceberByClienteId(clienteId) {
  try {
    const response = await fetch(`/operador/api/clientes/${clienteId}/contas_receber`);

    if (!response.ok) {
      throw new Error('Erro ao buscar contas a receber');
    }

    const contas = await response.json();

    return contas.map((conta) => ({
      id: conta.id,
      descricao: conta.descricao || 'Sem descrição',
      valor_original: conta.valor_original,
      valor_aberto: conta.valor_aberto,
      status: conta.status,
      data_vencimento: conta.data_vencimento,
      data_emissao: conta.data_emissao,
      data_pagamento: conta.data_pagamento,
      nota_fiscal_id: conta.nota_fiscal_id,
      observacoes: conta.observacoes,
      // Incluir os dados dos produtos que estavam faltando
      itens_nota_fiscal: conta.itens_nota_fiscal || [],
      valor_total_nota: conta.valor_total_nota || 0.0,
      valor_desconto_nota: conta.valor_desconto_nota || 0.0,
      tipo_desconto_nota: conta.tipo_desconto_nota,
    }));
  } catch (error) {
    console.error('Erro ao buscar contas a receber:', error);
    showMessage('Erro ao carregar contas a receber', 'error');
    return [];
  }
}
/**
 * Busca notas fiscais de um cliente
 */
async function findNotasFiscaisByClienteId(clienteId) {
  try {
    const response = await fetch(`/operador/api/clientes/${clienteId}/notas_fiscais`);

    if (!response.ok) {
      throw new Error('Erro ao buscar notas fiscais');
    }

    const notas = await response.json();

    // Processa os dados para o formato esperado
    return notas.map((nota) => ({
      id: nota.id,
      data_emissao: nota.data_emissao,
      valor_total: nota.valor_total,
      valor_desconto: nota.valor_desconto || 0,
      status: nota.status,
      a_prazo: nota.a_prazo || false,
      forma_pagamento: nota.forma_pagamento,
      valor_recebido: nota.valor_recebido,
      troco: nota.troco,
      operador_id: nota.operador_id,
      caixa_id: nota.caixa_id,
    }));
  } catch (error) {
    console.error('Erro ao buscar notas fiscais:', error);
    showMessage('Erro ao carregar histórico de compras', 'error');
    return [];
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
      method: 'GET',
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

  const filteredProducts = products.filter(
    (product) =>
      product.nome.toLowerCase().includes(searchTerm) ||
      (product.marca && product.marca.toLowerCase().includes(searchTerm)) ||
      (product.codigo && product.codigo.toLowerCase().includes(searchTerm)),
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

  products.forEach((product) => {
    const item = document.createElement('div');
    item.className = 'search-result-item';
    item.innerHTML = `
            <h4>${product.nome}</h4>
            <p>Marca: ${product.marca || 'Não informada'} | Código: ${
              product.codigo || 'Não informado'
            }</p>
            <p>Preço: ${formatCurrency(product.valor_unitario)} | Estoque Loja: ${
              product.estoque_loja
            } ${product.unidade}</p>
        `;
    item.addEventListener('click', () => {
      addProductToSale(product);
      closeModal();
    });
    productSearchResults.appendChild(item);
  });
}

// ==================== FUNÇÕES DE ESTOQUE ====================
function getAvailableStockTypes(product) {
  return [
    {
      id: 'loja',
      name: `Loja ${product.estoque_loja <= 0 ? '(Sem estoque)' : ''}`,
      icon: 'fas fa-store',
      disabled: product.estoque_loja <= 0,
    },
    {
      id: 'deposito',
      name: `Depósito ${product.estoque_deposito <= 0 ? '(Sem estoque)' : ''}`,
      icon: 'fas fa-warehouse',
      disabled: product.estoque_deposito <= 0,
    },
    {
      id: 'fabrica',
      name: `Fábrica ${product.estoque_fabrica <= 0 ? '(Sem estoque)' : ''}`,
      icon: 'fas fa-industry',
      disabled: product.estoque_fabrica <= 0,
    },
  ];
}

// Função para obter a quantidade disponível por tipo de estoque
function getStockByType(product, stockType) {
  switch (stockType) {
    case 'loja':
      return product.estoque_loja || 0;
    case 'deposito':
      return product.estoque_deposito || 0;
    case 'fabrica':
      return product.estoque_fabrica || 0;
    default:
      return 0;
  }
}

// Função para formatar o estoque
function formatStockInfo(product, selectedStockType = 'loja') {
  const stockTypes = getAvailableStockTypes(product);
  const currentStock = getStockByType(product, selectedStockType);

  let info = `Loja: ${product.estoque_loja || 0}`;

  if (product.estoque_deposito > 0) {
    info += ` | Depósito: ${product.estoque_deposito}`;
  }

  if (product.estoque_fabrica > 0) {
    info += ` | Fábrica: ${product.estoque_fabrica}`;
  }

  return info;
}

async function addProductToSale(product, initialQuantity = 1) {
  if (!product) return;

  // Busca descontos do produto
  const discounts = await fetchProductDiscounts(product.id);
  const { finalPrice, discountApplied, discountInfo } = calculateDiscountedPrice(
    product.valor_unitario,
    initialQuantity,
    discounts,
  );

  const uniqueId = `${product.id}_${Date.now()}`;
  const existingProductIndex = selectedProducts.findIndex((p) => p.id === product.id);

  // Define estoque padrão (loja)
  const defaultStockType = 'loja';
  const availableStockTypes = getAvailableStockTypes(product);

  if (existingProductIndex >= 0) {
    // Se o produto já existe, mantém o estoque selecionado anteriormente
    const existingStockType =
      selectedProducts[existingProductIndex].stockType || defaultStockType;
    selectedProducts[existingProductIndex].quantity += initialQuantity;
    const newQuantity = selectedProducts[existingProductIndex].quantity;

    // Recalcula desconto para a nova quantidade
    const newPriceInfo = calculateDiscountedPrice(
      product.valor_unitario,
      newQuantity,
      discounts,
    );

    selectedProducts[existingProductIndex].price = newPriceInfo.finalPrice;
    selectedProducts[existingProductIndex].hasDiscount = newPriceInfo.discountApplied;
    selectedProducts[existingProductIndex].discountInfo = newPriceInfo.discountInfo;
  } else {
    selectedProducts.push({
      uniqueId: uniqueId,
      id: product.id,
      name: product.nome,
      description: product.descricao || '',
      valor_unitario: product.valor_unitario,
      price: finalPrice,
      originalPrice: product.valor_unitario,
      quantity: initialQuantity,
      unit: product.unidade,
      stock: getStockByType(product, defaultStockType),
      stockType: defaultStockType,
      availableStockTypes: availableStockTypes,
      allowsFraction: product.unidade.toLowerCase() === 'kg',
      hasDiscount: discountApplied,
      discountInfo: discountInfo,
      availableDiscounts: discounts,
    });
  }

  renderProductsList();
  calculateSaleTotal();
}

async function refreshAllDiscounts() {
  await updateAllProductDiscounts();
  showMessage('Descontos atualizados com sucesso!');
}

// Adicione um botão para atualizar descontos manualmente (opcional)
function addDiscountRefreshButton() {
  const discountSection = document.querySelector('.discount-controls');
  if (discountSection && !document.getElementById('refresh-discounts-btn')) {
    const refreshBtn = document.createElement('button');
    refreshBtn.id = 'refresh-discounts-btn';
    refreshBtn.className = 'btn-secondary';
    refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Atualizar Descontos';
    refreshBtn.addEventListener('click', refreshAllDiscounts);
    discountSection.appendChild(refreshBtn);
  }
}

async function fetchProductDiscounts(productId) {
  try {
    const response = await fetch(
      `/operador/api/produtos/${productId}/descontos?timestamp=${new Date().getTime()}`,
    );
    if (!response.ok) return [];
    return await response.json();
  } catch (error) {
    console.error('Erro ao buscar descontos:', error);
    return [];
  }
}

function calculateDiscountedPrice(basePrice, quantity, discounts) {
  // Verifica se há descontos válidos
  if (!discounts || discounts.length === 0 || !quantity || quantity <= 0) {
    return {
      finalPrice: basePrice,
      discountApplied: false,
      discountInfo: null,
    };
  }

  let bestDiscount = null;
  let bestPrice = basePrice;
  const hoje = new Date();

  // Ordenar descontos: percentual primeiro, depois fixo
  const sortedDiscounts = [...discounts].sort((a, b) => {
    if (a.tipo === 'percentual' && b.tipo !== 'percentual') return -1;
    if (a.tipo !== 'percentual' && b.tipo === 'percentual') return 1;
    return 0;
  });

  for (const discount of sortedDiscounts) {
    try {
      // Verifica se o desconto está ativo
      if (!discount.ativo) {
        continue;
      }

      // Verifica a data limite (se existir)
      if (discount.valido_ate) {
        const validoAte = new Date(discount.valido_ate);
        if (hoje > validoAte) {
          continue; // Desconto expirado
        }
      }

      // Verifica quantidade mínima
      if (quantity < discount.quantidade_minima) {
        continue;
      }

      // Verifica quantidade máxima (se existir)
      if (discount.quantidade_maxima && quantity > discount.quantidade_maxima) {
        continue;
      }

      // Calcula preço com desconto
      let discountedPrice = basePrice;

      if (discount.tipo === 'percentual') {
        discountedPrice = basePrice * (1 - discount.valor / 100);
      } else if (discount.tipo === 'fixo') {
        discountedPrice = Math.max(0, basePrice - discount.valor);
      }

      // Verifica se é o melhor desconto encontrado até agora
      if (discountedPrice < bestPrice) {
        bestPrice = discountedPrice;
        bestDiscount = {
          ...discount,
          valor_aplicado:
            discount.tipo === 'percentual'
              ? `${discount.valor}%`
              : formatCurrency(discount.valor),
          valor_desconto: basePrice - discountedPrice,
        };
      }
    } catch (error) {
      console.error('Erro ao processar desconto:', error, discount);
      continue;
    }
  }

  return {
    finalPrice: bestPrice,
    discountApplied: bestDiscount !== null,
    discountInfo: bestDiscount,
  };
}

// Adicione esta chamada na inicialização para criar o botão de atualização
document.addEventListener('DOMContentLoaded', function () {
  setTimeout(addDiscountRefreshButton, 1000);
});

async function updateAllProductDiscounts() {
  for (let i = 0; i < selectedProducts.length; i++) {
    const product = selectedProducts[i];
    if (product.quantity && product.quantity > 0) {
      const discounts = await fetchProductDiscounts(product.id);
      const { finalPrice, discountApplied, discountInfo } = calculateDiscountedPrice(
        product.originalPrice,
        product.quantity,
        discounts,
      );

      selectedProducts[i] = {
        ...product,
        price: finalPrice,
        hasDiscount: discountApplied,
        discountInfo: discountInfo,
        availableDiscounts: discounts,
      };
    }
  }
  renderProductsList();
  calculateSaleTotal();
}

function applyManualDiscount() {
  try {
    // 1. Obtém os valores dos campos
    const discountType = document.getElementById('discount-type').value;
    const discountValueInput = document.getElementById('discount-value').value.trim();

    // 2. Validações básicas
    if (!discountValueInput) throw new Error('Digite um valor para o desconto');

    const discountValue = parseFloat(discountValueInput.replace(',', '.'));
    if (isNaN(discountValue)) throw new Error('Valor inválido. Use apenas números.');

    // 3. Calcula o total atual SEM descontos
    const subtotal = selectedProducts.reduce((sum, product) => {
      return sum + product.originalPrice * product.quantity;
    }, 0);

    // 4. Validações específicas
    if (discountType === 'percentual') {
      if (discountValue <= 0 || discountValue > 100) {
        throw new Error('Percentual deve ser entre 0.01% e 100%');
      }
    } else {
      if (discountValue <= 0) throw new Error('Valor fixo deve ser maior que zero');
      if (discountValue >= subtotal)
        throw new Error(`Desconto não pode ser maior que ${formatCurrency(subtotal)}`);
    }

    // 5. Calcula o valor total do desconto
    let totalDiscount = 0;
    if (discountType === 'percentual') {
      totalDiscount = subtotal * (discountValue / 100);
    } else {
      totalDiscount = discountValue;
    }

    // 6. Distribui o desconto proporcionalmente entre os produtos
    selectedProducts = selectedProducts.map((product) => {
      const productTotal = product.originalPrice * product.quantity;
      const discountRatio = productTotal / subtotal;
      const productDiscount = totalDiscount * discountRatio;
      const discountedPrice =
        product.originalPrice - productDiscount / product.quantity;

      return {
        ...product,
        price: discountedPrice,
        hasDiscount: true,
        discountInfo: {
          tipo: discountType,
          valor: discountValue,
          valor_aplicado:
            discountType === 'percentual'
              ? `${discountValue}%`
              : formatCurrency(discountValue),
          identificador: 'MANUAL',
          descricao: 'Desconto manual aplicado',
        },
      };
    });

    // 7. Atualiza a interface
    renderProductsList();
    calculateSaleTotal();
    showMessage(`Desconto de ${formatCurrency(totalDiscount)} aplicado ao total!`);
    document.getElementById('discount-value').value = '';
  } catch (error) {
    showMessage(error.message, 'error');
  }
}

function renderProductsList() {
  if (!productsList) return;
  productsList.innerHTML = '';

  selectedProducts.forEach((product, index) => {
    const totalValue = product.price * (product.quantity || 0);
    const originalTotalValue = product.originalPrice * (product.quantity || 0);
    const discountValue = originalTotalValue - totalValue;

    // Cria o seletor de estoque
    let stockSelector = '';
    if (product.availableStockTypes && product.availableStockTypes.length > 1) {
      stockSelector = `
                <div class="stock-selector-container">
                    <select class="stock-selector" data-unique-id="${
                      product.uniqueId
                    }" title="Selecione o estoque de origem">
                        ${product.availableStockTypes
                          .map(
                            (stockType) => `
                            <option value="${stockType.id}" 
                                ${product.stockType === stockType.id ? 'selected' : ''}
                                data-icon="${stockType.icon}">
                                ${stockType.name}
                            </option>
                        `,
                          )
                          .join('')}
                    </select>
                    <div class="stock-info">
                        Disponível: ${getStockByType(product, product.stockType)} ${
                          product.unit
                        }
                    </div>
                </div>
            `;
    } else {
      // Se só tem um tipo de estoque, mostra apenas a informação
      stockSelector = `
                <div class="stock-info-single">
                    <i class="fas fa-store"></i>
                    Disponível: ${getStockByType(product, 'loja')} ${product.unit}
                </div>
            `;
    }

    const row = document.createElement('tr');
    row.dataset.uniqueId = product.uniqueId; // Usa o uniqueId em vez do índice
    row.innerHTML = `
            <td>
                <div class="product-name-container">
                    <div class="product-name">${product.name}</div>
                    ${stockSelector}
                </div>
                <span class="discount-badge" 
                      title="${product.discountInfo?.descricao || ''}" 
                      style="display:${product.hasDiscount ? 'inline-block' : 'none'}">
                    ${
                      product.hasDiscount && product.discountInfo
                        ? `
                        <i class="fas fa-tag"></i> ${
                          product.discountInfo.identificador || 'DESCONTO'
                        }
                        ${
                          product.discountInfo.tipo === 'percentual'
                            ? ` (${product.discountInfo.valor}%)`
                            : ` (${formatCurrency(product.discountInfo.valor)})`
                        }
                    `
                        : ''
                    }
                </span>
            </td>
            <td>${product.description}</td>
            <td class="product-price">
                ${formatCurrency(product.price)}
                ${
                  product.hasDiscount
                    ? `<small class="original-price">${formatCurrency(
                        product.originalPrice,
                      )}</small>`
                    : ''
                }
            </td>
            <td>
                <input type="text" class="quantity-input" 
                       value="${
                         product.quantity !== null && product.quantity !== undefined
                           ? product.quantity.toString().replace('.', ',')
                           : ''
                       }" 
                       data-unique-id="${product.uniqueId}" 
                       title="Digite números com vírgula ou ponto. Pode deixar em branco.">
                <small>${product.unit}</small>
            </td>
            <td class="product-total">
                ${formatCurrency(totalValue)}
                ${
                  product.hasDiscount
                    ? `<small class="discount-value">(Economia: ${formatCurrency(
                        discountValue,
                      )})</small>`
                    : ''
                }
            </td>
            <td>
                <button class="btn-remove" data-unique-id="${
                  product.uniqueId
                }" title="Remover produto">
                    <i class="fas fa-trash"></i>
                </button>
                <!-- Espaço reservado para botão de remover desconto (será adicionado dinamicamente se necessário) -->
            </td>
        `;

    // Adiciona evento de clique para selecionar a linha
    row.addEventListener('click', function (e) {
      // Não seleciona se clicou em um botão ou input
      if (
        e.target.tagName === 'BUTTON' ||
        e.target.tagName === 'INPUT' ||
        e.target.tagName === 'SELECT' ||
        e.target.closest('button') ||
        e.target.closest('input') ||
        e.target.closest('select')
      ) {
        return;
      }

      // Remove seleção de outras linhas
      productsList.querySelectorAll('tr.selected').forEach((r) => {
        r.classList.remove('selected');
      });

      // Seleciona esta linha
      this.classList.add('selected');

      // Atualiza instruções
      showDiscountInstructions();
    });

    productsList.appendChild(row);

    // ADICIONA O BOTÃO DE REMOVER DESCONTO APÓS O BOTÃO DE REMOVER PRODUTO
    if (product.hasDiscount) {
      const actionsCell = row.querySelector('td:last-child');
      if (actionsCell) {
        const removeDiscountBtn = document.createElement('button');
        removeDiscountBtn.className = 'btn-remove-discount';
        removeDiscountBtn.dataset.uniqueId = product.uniqueId;
        removeDiscountBtn.title = 'Remover desconto deste produto';
        removeDiscountBtn.innerHTML = '<i class="fas fa-times"></i>';

        // Adiciona o botão APÓS o botão de remover produto
        const removeBtn = actionsCell.querySelector('.btn-remove');
        if (removeBtn) {
          removeBtn.insertAdjacentElement('afterend', removeDiscountBtn);
        } else {
          // Se por algum motivo não houver botão de remover, adiciona no final
          actionsCell.appendChild(removeDiscountBtn);
        }
      }
    }
  });

  // Adiciona eventos para os campos de quantidade
  document.querySelectorAll('.quantity-input').forEach((input) => {
    input.addEventListener('input', function (e) {
      let value = e.target.value;
      if (!/^[0-9]*[,.]?[0-9]*$/.test(value)) {
        e.target.value = value.slice(0, -1);
      }
    });

    input.addEventListener('input', async function (e) {
      await updateProductQuantity(e.target);
    });
  });

  // Adiciona eventos para os seletores de estoque
  document.querySelectorAll('.stock-selector').forEach((select) => {
    select.addEventListener('change', function (e) {
      const uniqueId = this.dataset.uniqueId;
      const newStockType = this.value;

      const productIndex = selectedProducts.findIndex((p) => p.uniqueId === uniqueId);

      if (productIndex >= 0 && productIndex < selectedProducts.length) {
        // Atualiza o tipo de estoque
        selectedProducts[productIndex].stockType = newStockType;

        // Atualiza a quantidade disponível para o novo estoque
        const product = products.find(
          (p) => p.id === selectedProducts[productIndex].id,
        );
        if (product) {
          selectedProducts[productIndex].stock = getStockByType(product, newStockType);

          // Atualiza o texto de estoque disponível
          const stockInfo = this.closest('.stock-selector-container').querySelector(
            '.stock-info',
          );
          if (stockInfo) {
            stockInfo.textContent = `Disponível: ${selectedProducts[productIndex].stock} ${selectedProducts[productIndex].unit}`;
          }
        }
      }
    });
  });

  // Corrigido: Evento de remover produto por uniqueId
  document.querySelectorAll('.btn-remove').forEach((button) => {
    button.addEventListener('click', function (e) {
      e.stopPropagation(); // Impede a seleção da linha
      const uniqueId = this.dataset.uniqueId;

      // Encontra o índice pelo uniqueId
      const productIndex = selectedProducts.findIndex((p) => p.uniqueId === uniqueId);

      if (productIndex !== -1) {
        // Remove o produto específico
        selectedProducts.splice(productIndex, 1);
        renderProductsList();
        calculateSaleTotal();
        // Atualiza instruções após remover produto
        showDiscountInstructions();
      }
    });
  });

  // Corrigido: Evento de remover desconto por uniqueId
  document.querySelectorAll('.btn-remove-discount').forEach((button) => {
    button.addEventListener('click', function (e) {
      e.stopPropagation(); // Impede a seleção da linha
      const uniqueId = this.dataset.uniqueId;

      // Encontra o índice pelo uniqueId
      const productIndex = selectedProducts.findIndex((p) => p.uniqueId === uniqueId);

      if (productIndex !== -1) {
        removeProductDiscount(productIndex);
        // Atualiza instruções após remover desconto
        showDiscountInstructions();
      }
    });
  });

  // Mostra instruções após renderizar a tabela
  showDiscountInstructions();
}

function showDiscountInstructions() {
  const discountControl = document.querySelector('.discount-control');
  if (!discountControl) return;

  // Remove instruções antigas se existirem
  const oldInstructions = discountControl.querySelector('.discount-instructions');
  if (oldInstructions) oldInstructions.remove();

  // Cria ou atualiza as instruções
  const instructions = document.createElement('div');
  instructions.className = 'discount-instructions';
  instructions.style.cssText = `
        font-size: 0.8rem;
        color: #6c757d;
        margin-top: 5px;
        padding: 5px;
        background-color: #f8f9fa;
        border-radius: 4px;
        border-left: 3px solid #007bff;
    `;

  const hasSelectedProduct = productsList && productsList.querySelector('tr.selected');

  if (hasSelectedProduct) {
    instructions.innerHTML = `
            <i class="fas fa-info-circle" style="color: #28a745; margin-right: 5px;"></i>
            <strong>Desconto específico:</strong> Será aplicado apenas no produto selecionado.
            <small style="display: block; margin-top: 2px;">Clique fora da tabela para aplicar em todos os produtos.</small>
        `;
    instructions.style.borderLeftColor = '#28a745';
  } else {
    instructions.innerHTML = `
            <i class="fas fa-info-circle" style="color: #6c757d; margin-right: 5px;"></i>
            <strong>Desconto geral:</strong> Será aplicado em todos os produtos.
            <small style="display: block; margin-top: 2px;">Clique em um produto na tabela para aplicar apenas nele.</small>
        `;
    instructions.style.borderLeftColor = '#007bff';
  }

  discountControl.appendChild(instructions);
}

document.addEventListener('click', function (e) {
  // Se clicar fora da tabela de produtos
  if (!e.target.closest('.products-table') && !e.target.closest('.discount-control')) {
    // Remove seleção de todas as linhas
    if (productsList) {
      productsList.querySelectorAll('tr.selected').forEach((r) => {
        r.classList.remove('selected');
      });
    }
    // Atualiza instruções
    showDiscountInstructions();
  }
});

// Atualiza instruções quando houver mudanças na quantidade
document.addEventListener('quantityUpdated', function () {
  setTimeout(showDiscountInstructions, 100);
});

function removeAllDiscounts() {
  if (selectedProducts.length === 0) {
    showMessage('Não há produtos na venda', 'error');
    return;
  }

  let discountRemoved = false;

  selectedProducts.forEach((product, index) => {
    if (product.hasDiscount) {
      // Restaura o preço original
      product.price = product.originalPrice;
      product.hasDiscount = false;
      product.discountInfo = null;
      discountRemoved = true;

      // Atualiza a linha específica
      updateProductRow(index);
    }
  });

  if (discountRemoved) {
    calculateSaleTotal();
    showMessage('Todos os descontos foram removidos!');
  } else {
    showMessage('Nenhum desconto aplicado para remover', 'info');
  }
}

function removeProductByUniqueId(uniqueId) {
  const indexToRemove = selectedProducts.findIndex((p) => p.uniqueId === uniqueId);

  if (indexToRemove !== -1) {
    console.log('Removendo produto:', selectedProducts[indexToRemove].name);
    selectedProducts.splice(indexToRemove, 1);
    renderProductsList();
    calculateSaleTotal();
  }
}

async function updateProductQuantity(input) {
  const uniqueId = input.dataset.uniqueId;
  if (!uniqueId) return;

  // Encontra o produto pelo uniqueId
  const productIndex = selectedProducts.findIndex((p) => p.uniqueId === uniqueId);
  if (productIndex === -1) return;

  const product = selectedProducts[productIndex];
  const value = input.value.trim().replace(',', '.');

  let newQuantity = parseFloat(value);

  if (isNaN(newQuantity) || newQuantity <= 0) {
    product.quantity = null;
    input.value = '';
    product.price = product.originalPrice;
    product.hasDiscount = false;
    product.discountInfo = null;
  } else {
    product.quantity = newQuantity;

    // Busca descontos atualizados e aplica automaticamente
    const discounts = await fetchProductDiscounts(product.id);
    const { finalPrice, discountApplied, discountInfo } = calculateDiscountedPrice(
      product.originalPrice,
      newQuantity,
      discounts,
    );

    selectedProducts[productIndex] = {
      ...product,
      price: finalPrice,
      hasDiscount: discountApplied,
      discountInfo: discountInfo,
      availableDiscounts: discounts,
    };
  }

  calculateSaleTotal();

  // Atualiza DOM sem recriar linha
  const updatedProduct = selectedProducts[productIndex];
  const row = input.closest('tr');
  if (row) {
    // Atualiza preço
    const priceCell = row.querySelector('.product-price');
    if (priceCell) {
      priceCell.innerHTML = `
                ${formatCurrency(updatedProduct.price)}
                ${
                  updatedProduct.hasDiscount
                    ? `<small class="original-price">${formatCurrency(
                        updatedProduct.originalPrice,
                      )}</small>`
                    : ''
                }
            `;
    }

    // Atualiza badge de desconto
    const badgeCell = row.querySelector('.discount-badge');
    if (badgeCell) {
      if (updatedProduct.hasDiscount && updatedProduct.discountInfo) {
        badgeCell.innerHTML = `
                    <i class="fas fa-tag"></i> ${
                      updatedProduct.discountInfo.identificador || 'DESCONTO'
                    }
                    ${
                      updatedProduct.discountInfo.tipo === 'percentual'
                        ? ` (${updatedProduct.discountInfo.valor}%)`
                        : ` (${formatCurrency(updatedProduct.discountInfo.valor)})`
                    }
                `;
        badgeCell.title = updatedProduct.discountInfo.descricao || 'Desconto aplicado';
        badgeCell.style.display = 'inline-block';
      } else {
        badgeCell.innerHTML = '';
        badgeCell.style.display = 'none';
      }
    }

    // Atualiza total
    const totalCell = row.querySelector('.product-total');
    if (totalCell) {
      const totalValue = updatedProduct.price * (updatedProduct.quantity || 0);
      const originalTotalValue =
        updatedProduct.originalPrice * (updatedProduct.quantity || 0);
      const discountValue = originalTotalValue - totalValue;

      totalCell.innerHTML = `
                ${formatCurrency(totalValue)}
                ${
                  updatedProduct.hasDiscount
                    ? `<small class="discount-value">(Economia: ${formatCurrency(
                        discountValue,
                      )})</small>`
                    : ''
                }
            `;
    }
  }
  document.dispatchEvent(
    new CustomEvent('quantityUpdated', {
      detail: { uniqueId, newQuantity },
    }),
  );
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
    const clienteId = selectedClientIdInput?.value
      ? parseInt(selectedClientIdInput.value)
      : 1;
    const observacao = document.getElementById('sale-notes')?.value || '';

    if (selectedProducts.length === 0) {
      showMessage('Adicione pelo menos um produto', 'error');
      throw new Error('Nenhum produto selecionado');
    }

    const paymentMethods = [];
    const paymentItems = document.querySelectorAll('.payment-item');

    // Processa os métodos de pagamento
    paymentItems.forEach((item) => {
      const method = item.querySelector('input[name="payment_methods[]"]').value;
      const amount = parseFloat(
        item.querySelector('input[name="payment_amounts[]"]').value.replace(',', '.'),
      );
      if (!isNaN(amount) && amount > 0) {
        paymentMethods.push({
          forma_pagamento: method,
          valor: amount,
        });
      }
    });

    const totalText = saleTotalElement?.textContent
      .replace('R$ ', '')
      .replace(/\./g, '')
      .replace(',', '.');
    const total = parseFloat(totalText) || 0;
    let valor_recebido = 0;

    if (paymentMethods.length > 0) {
      valor_recebido = paymentMethods.reduce((sum, pm) => sum + pm.valor, 0);
    } else {
      const amountReceivedText =
        amountReceivedInput?.value.replace(/\./g, '').replace(',', '.') || '0';
      valor_recebido = parseFloat(amountReceivedText) || 0;
    }

    const totalPagamentos = paymentMethods.reduce((sum, pm) => sum + pm.valor, 0);

    if (totalPagamentos < total) {
      const remaining = total - totalPagamentos;
      const pagamentoDinheiroExistente = paymentMethods.find(
        (pm) => pm.forma_pagamento === 'dinheiro',
      );

      if (pagamentoDinheiroExistente) {
        pagamentoDinheiroExistente.valor += remaining;
      } else {
        paymentMethods.push({
          forma_pagamento: 'dinheiro',
          valor: remaining,
        });
      }

      valor_recebido = total;
    }

    if (paymentMethods.length === 0) {
      paymentMethods.push({
        forma_pagamento: 'dinheiro',
        valor: total,
      });
      valor_recebido = total;
    }

    // Prepara os itens com estoque de origem
    const items = selectedProducts.map((product) => {
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
        estoque_origem: product.stockType || 'loja', // Inclui o estoque de origem
        desconto_info: product.discountInfo
          ? {
              tipo: product.discountInfo.tipo,
              valor: product.discountInfo.valor,
              identificador: product.discountInfo.identificador,
              descricao: product.discountInfo.descricao,
            }
          : null,
      };
    });

    const saleData = {
      cliente_id: clienteId,
      forma_pagamento:
        paymentMethods.length > 1 ? 'multiplos' : paymentMethods[0].forma_pagamento,
      valor_recebido: valor_recebido,
      valor_total: total,
      itens: items,
      pagamentos: paymentMethods,
      total_descontos: items.reduce((sum, item) => sum + item.valor_desconto, 0),
      observacao: observacao,
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
        instrucoes: deliveryAddress.instrucoes || '',
      };
    }

    // Usa a nova rota com estoque
    const response = await fetch('/operador/api/vendas_estoque', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(saleData),
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
    window.open(
      `/operador/pdf/nota/${paymentIdsStr}?timestamp=${new Date().getTime()}`,
      '_blank',
    );
  } catch (error) {
    console.error('Erro ao registrar venda:', error);
    showMessage(error.message, 'error');
  }
}

// Adicione este evento listener no seu código de inicialização
document.getElementById('sale-notes').addEventListener('input', function (e) {
  const maxLength = 500;
  const currentLength = e.target.value.length;

  if (currentLength > maxLength) {
    e.target.value = e.target.value.substring(0, maxLength);
    showMessage('Observação limitada a 500 caracteres', 'warning');
  }
});

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

  if (subtotalValueElement) {
    subtotalValueElement.textContent = formatCurrency(subtotal);
    subtotalValueElement.dataset.originalValue = subtotal.toFixed(2);
    subtotalValueElement.dataset.currentValue = subtotal.toFixed(2);
  }

  if (saleTotalElement) saleTotalElement.textContent = formatCurrency(total);

  if (amountReceivedInput && amountReceivedInput.value) {
    const amountReceivedText = amountReceivedInput.value
      .replace(/\./g, '')
      .replace(',', '.');
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
    value = value.replace(/[,.]/g, (m, i) =>
      i === value.lastIndexOf('.') || i === value.lastIndexOf(',') ? m : '',
    );
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

    const subtotalElement = document.getElementById('subtotal-value');
    if (subtotalElement) {
      subtotalElement.textContent = 'R$ 0,00';
      delete subtotalElement.dataset.originalValue;
      delete subtotalElement.dataset.currentValue;
    }

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
    console.error('Erro ao resetar formulário de venda:', error);
  }
}

// ==================== FUNÇÕES DE ENTREGA ====================
function openDeliveryModal() {
  if (!deliveryModal) return;

  if (deliveryAddress) {
    document.getElementById('delivery-address').value =
      deliveryAddress.logradouro || '';
    document.getElementById('delivery-number').value = deliveryAddress.numero || '';
    document.getElementById('delivery-complement').value =
      deliveryAddress.complemento || '';
    document.getElementById('delivery-neighborhood').value =
      deliveryAddress.bairro || '';
    document.getElementById('delivery-city').value = deliveryAddress.cidade || '';
    document.getElementById('delivery-state').value = deliveryAddress.estado || '';
    document.getElementById('delivery-zipcode').value = deliveryAddress.cep || '';
    document.getElementById('delivery-instructions').value =
      deliveryAddress.instrucoes || '';
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
    endereco_completo: `${document.getElementById('delivery-address')?.value || ''}, ${
      document.getElementById('delivery-number')?.value || ''
    }`,
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
  const client = clients.find((c) => c.id == clientId);

  if (!client || (!client.endereco && !client.endereco_completo)) {
    showMessage('Cliente não possui endereço cadastrado', 'error');
    return;
  }

  if (
    client.logradouro &&
    client.numero &&
    client.bairro &&
    client.cidade &&
    client.estado
  ) {
    deliveryAddress = {
      logradouro: client.logradouro,
      numero: client.numero,
      complemento: client.complemento || '',
      bairro: client.bairro,
      cidade: client.cidade,
      estado: client.estado,
      cep: client.cep || '',
      instrucoes: '',
      endereco_completo: `${client.logradouro}, ${client.numero}, ${client.bairro}, ${client.cidade}-${client.estado}`,
    };
  } else {
    const addressString = client.endereco || client.endereco_completo;
    const addressRegex =
      /^(.*?)(?:,\s*(?:nº|no|numero|número)\s*(\d+))?(?:,\s*(.*?))?(?:,\s*(.*?)\s*-\s*([A-Z]{2}))?$/i;
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
      instrucoes: '',
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
    deliveryBtn.innerHTML =
      '<i class="fas fa-check-circle"></i> Endereço de Entrega Cadastrado';
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
        <p>${deliveryAddress.logradouro}, ${deliveryAddress.numero}${
          deliveryAddress.complemento ? ', ' + deliveryAddress.complemento : ''
        }</p>
        <p>${deliveryAddress.bairro} - ${deliveryAddress.cidade}/${
          deliveryAddress.estado
        }</p>
        ${deliveryAddress.cep ? `<p>CEP: ${deliveryAddress.cep}</p>` : ''}
        ${
          deliveryAddress.instrucoes
            ? `<p><strong>Instruções:</strong> ${deliveryAddress.instrucoes}</p>`
            : ''
        }
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
  document
    .getElementById('edit-delivery-btn')
    ?.addEventListener('click', openDeliveryModal);
  document
    .getElementById('remove-delivery-btn')
    ?.addEventListener('click', removeDeliveryAddress);
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

function parseBrazilianNumber(value) {
  if (!value) return 0;

  value = value.trim();
  if (value.includes(',')) {
    value = value.replace(/\./g, '');
    value = value.replace(',', '.');
  } else {
    const partes = value.split('.');
    if (partes.length > 1 && partes[partes.length - 1].length !== 3) {
      value = value.replace(',', '.');
    } else {
      value = value.replace(/\./g, '');
    }
  }

  const number = parseFloat(value);
  return isNaN(number) ? 0 : number;
}

async function saveExpense() {
  const description = document.getElementById('expense-description')?.value.trim();
  const amountStr = document.getElementById('expense-amount')?.value.trim();
  const note = document.getElementById('expense-note')?.value.trim();

  const amount = parseBrazilianNumber(amountStr);

  if (!description) {
    showMessage('Descrição da despesa é obrigatória', 'error');
    return;
  }

  if (!amount || amount <= 0) {
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
        caixa_id: currentCaixaId,
      }),
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

async function gerarOrcamentoPDF() {
  try {
    // Preparar dados para o orçamento
    const orcamentoData = {
      cliente: selectedClient || { nome: 'CONSUMIDOR FINAL' },
      itens: selectedProducts.map((produto) => ({
        id: produto.id,
        nome: produto.name,
        descricao: produto.description,
        quantidade: produto.quantity,
        valor_unitario: produto.originalPrice,
        valor_total: produto.price * produto.quantity,
        valor_desconto:
          produto.originalPrice * produto.quantity - produto.price * produto.quantity,
        unidade: produto.unit,
      })),
      observacoes: document.getElementById('sale-notes')?.value || '',
    };

    // Chamar a API para gerar o PDF
    const response = await fetch('/operador/api/orcamento/pdf', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(orcamentoData),
    });

    if (!response.ok) {
      throw new Error('Erro ao gerar orçamento');
    }

    // Criar blob e abrir em nova janela
    const pdfBlob = await response.blob();
    const pdfUrl = URL.createObjectURL(pdfBlob);
    window.open(pdfUrl, '_blank');
  } catch (error) {
    console.error('Erro ao gerar orçamento:', error);
    showMessage(error.message, 'error');
  }
}
// ==================== FUNÇÕES DE VENDAS DO DIA ====================
async function loadDaySales() {
  const tableBody = document.querySelector('#day-sales-table tbody');
  if (!tableBody) return;

  try {
    tableBody.innerHTML =
      '<tr><td colspan="6"><div class="loading-spinner"></div></td></tr>';

    const response = await fetch('/operador/api/vendas/hoje', {
      ...preventCacheConfig,
      method: 'GET',
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
    console.error('Erro ao carregar vendas:', error);
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: red;">${error.message}</td></tr>`;
    showMessage(error.message, 'error');
  }
}

async function carregarDespesasDoDia() {
  try {
    const response = await fetch('/operador/api/despesas/hoje');
    const data = await response.json();

    const tbody = document.querySelector('#day-expenses-table tbody');
    tbody.innerHTML = '';

    if (data.sucesso && data.despesas.length > 0) {
      data.despesas.forEach((d) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
                    <td>${d.id}</td>
                    <td>${d.descricao}</td>
                    <td>${formatCurrency(d.valor)}</td>
                    <td>${d.data}</td>
                `;
        tbody.appendChild(tr);
      });
    } else {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">Nenhuma despesa encontrada</td></tr>`;
    }
  } catch (error) {
    console.error('Erro ao carregar despesas:', error);
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
function formatPaymentMethods(pagamentos) {
  if (!pagamentos || !Array.isArray(pagamentos) || pagamentos.length === 0) {
    return '-';
  }

  // Se houver apenas um pagamento, mostra normalmente
  if (pagamentos.length === 1) {
    return formatPaymentMethod(pagamentos[0].forma_pagamento);
  }

  // Para múltiplos pagamentos, cria um tooltip ou texto resumido
  const formasUnicas = [...new Set(pagamentos.map((p) => p.forma_pagamento))];

  if (formasUnicas.length === 1) {
    // Mesma forma em múltiplos pagamentos
    return `${formatPaymentMethod(formasUnicas[0])} (${pagamentos.length}x)`;
  } else {
    // Diferentes formas de pagamento
    return formasUnicas.map((fp) => formatPaymentMethod(fp)).join(' + ');
  }
}

function renderDaySales(vendas) {
  const tableBody = document.querySelector('#day-sales-table tbody');
  if (!tableBody) return;

  tableBody.innerHTML = '';

  if (!Array.isArray(vendas) || vendas.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 1rem; color: #666;">Nenhuma venda registrada para o dia.</td></tr>`;
    return;
  }

  // Ordenar vendas por data (mais recente primeiro)
  vendas.sort((a, b) => new Date(b.data_emissao) - new Date(a.data_emissao));

  // Criar linhas da tabela
  vendas.forEach((sale) => {
    // Verificar se a venda tem itens antes de renderizar
    if (sale.itens && sale.itens.length > 0) {
      const row = document.createElement('tr');
      row.innerHTML = `
                <td>${sale.id}</td>
                <td>${sale.data_emissao}</td>
                <td>${sale.cliente?.nome || 'Consumidor Final'}</td>
                <td>${formatCurrency(sale.valor_total)}</td>
                <td>${formatPaymentMethods(sale.pagamentos)}</td>
                <td>
                    <button class="btn-view" data-id="${sale.id}">
                        <i class="fas fa-eye"></i> Detalhes
                    </button>
                    <button class="btn-download" data-id="${sale.id}">
                        <i class="fas fa-file-pdf"></i> Nota
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
  tableBody.addEventListener('click', function (e) {
    const viewBtn = e.target.closest('.btn-view');
    if (viewBtn) {
      openSaleDetailsModal(viewBtn.dataset.id);
      return;
    }

    const downloadBtn = e.target.closest('.btn-download');
    if (downloadBtn) {
      downloadSaleReceipt(downloadBtn.dataset.id);
      return;
    }

    const voidBtn = e.target.closest('.btn-void');
    if (voidBtn) {
      openVoidSaleModal(voidBtn.dataset.id);
      return;
    }
  });
  carregarDespesasDoDia();
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

async function downloadSaleReceipt(saleId) {
  if (!saleId) {
    showMessage('ID da venda não informado', 'error');
    return;
  }

  // ========== ADIÇÃO CRÍTICA ==========
  const downloadBtn = document.querySelector(`.btn-download[data-id="${saleId}"]`);
  if (downloadBtn && downloadBtn.dataset.processing === 'true') {
    return; // Já está processando, ignora clique
  }
  if (downloadBtn) {
    downloadBtn.dataset.processing = 'true'; // Marca como processando
  }
  // ===================================

  try {
    if (downloadBtn) {
      const originalText = downloadBtn.innerHTML;
      downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Gerando...';
      downloadBtn.disabled = true;
    }

    const pdfUrl = `/operador/pdf/nota-venda/${saleId}`;
    window.open(pdfUrl, '_blank');

    setTimeout(() => {
      if (downloadBtn) {
        downloadBtn.innerHTML = '<i class="fas fa-file-pdf"></i> Nota';
        downloadBtn.disabled = false;
        downloadBtn.dataset.processing = 'false'; // Libera para novo clique
      }
    }, 3000);
  } catch (error) {
    console.error('Erro ao abrir nota fiscal:', error);
    showMessage(error.message, 'error');

    if (downloadBtn) {
      downloadBtn.innerHTML = '<i class="fas fa-file-pdf"></i> Nota';
      downloadBtn.disabled = false;
      downloadBtn.dataset.processing = 'false';
    }
  }
}

async function voidSale() {
  const saleId = document.getElementById('void-sale-id').value;
  const reason =
    document.getElementById('void-sale-reason').value || 'Sem motivo informado';

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
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        motivo_estorno: reason,
      }),
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

    gerarRelatorioDiario();
  } catch (error) {
    console.error('Erro ao gerar PDF:', error);
    showMessage('Erro ao gerar relatório em PDF', 'error');
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

function gerarRelatorioDiario(caixaId = null, operadorId = null) {
  let url = '/operador/api/vendas/relatorio-diario-pdf';
  const params = new URLSearchParams();
  if (caixaId) params.append('caixa_id', caixaId);
  if (operadorId) params.append('operador_id', operadorId);
  if ([...params].length > 0) {
    url += '?' + params.toString();
  }
  window.open(url, '_blank');
}

function closeModal(modalId = null) {
  if (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'none';
  } else {
    document.querySelectorAll('.modal').forEach((modal) => {
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
      'sale-details-payments',
    ];

    elementsToReset.forEach((id) => {
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
    safeSetText(
      'sale-details-date',
      new Date(venda.data_emissao).toLocaleString('pt-BR'),
    );
    safeSetText(
      'sale-details-client',
      `${venda.cliente?.nome || 'Consumidor Final'}${
        venda.cliente?.documento
          ? ' (' + formatDocument(venda.cliente.documento) + ')'
          : ''
      }`,
    );
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
    modal.addEventListener('click', function (e) {
      if (e.target === modal) {
        closeModal('sale-details-modal');
      }
    });
  } catch (error) {
    console.error('Erro ao abrir detalhes da venda:', error);
    showMessage(error.message || 'Erro ao carregar detalhes da venda', 'error');
    closeModal('sale-details-modal');
  }
}

// Função para tratar informações de entrega
function handleDeliveryInfo(venda) {
  const deliveryContainer = document.getElementById('sale-details-delivery-container');
  const deliveryInstructions = document.getElementById(
    'sale-details-delivery-instructions',
  );

  if (deliveryContainer) {
    if (venda.entrega) {
      const endereco = [
        venda.entrega.endereco || venda.entrega.logradouro,
        venda.entrega.numero,
        venda.entrega.complemento,
        venda.entrega.bairro,
        `${venda.entrega.cidade}/${venda.entrega.estado}`.toUpperCase(),
        venda.entrega.cep ? formatCEP(venda.entrega.cep) : '',
      ]
        .filter(Boolean)
        .join(', ');

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

  itens.forEach((item) => {
    // Usar uma chave única baseada no produto e valor unitário para evitar duplicatas
    const chaveUnica = `${item.produto_id || item.produto_nome}-${
      item.valor_unitario
    }-${item.quantidade}`;

    if (!idsVistos.has(chaveUnica)) {
      idsVistos.add(chaveUnica);
      itensUnicos.push(item);
    }
  });

  // Adicionar produtos únicos na tabela
  itensUnicos.forEach((item) => {
    const row = document.createElement('tr');
    row.innerHTML = `
            <td>${item.produto_nome || item.nome || 'Produto não encontrado'}</td>
            <td class="text-right">${parseFloat(item.quantidade || 0).toLocaleString(
              'pt-BR',
            )}</td>
            <td class="text-right">${formatCurrency(item.valor_unitario || 0)}</td>
            <td class="text-right">${
              item.desconto_aplicado ? formatCurrency(item.desconto_aplicado) : '-'
            }</td>
            <td class="text-right">${formatCurrency(
              item.valor_total || item.total || 0,
            )}</td>
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

    pagamentosAgregados.forEach((pagamento) => {
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
      const totalPagamentos = pagamentosAgregados.reduce(
        (sum, pag) => sum + parseFloat(pag.valor),
        0,
      );
      const row = document.createElement('tr');
      row.className = 'total-row';
      row.innerHTML = `
                <td><strong>Total</strong></td>
                <td class="text-right"><strong>${formatCurrency(
                  totalPagamentos,
                )}</strong></td>
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

  pagamentos.forEach((pag) => {
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
        data: pag.data,
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
    pix_edfrance: 'Pix (Edfranci)',
    pix_loja: 'Pix (Loja)',
    pix_maquineta: 'Pix (Maquineta)',
    dinheiro: 'Dinheiro',
    cartao_credito: 'Cartão de Crédito',
    cartao_debito: 'Cartão de Débito',
    a_prazo: 'A Prazo',
  };
  return methods[method] || method;
}

// ==================== FUNÇÕES DE CAIXA ====================
async function checkCaixaStatus() {
  try {
    const response = await fetch('/operador/api/saldo', {
      ...preventCacheConfig,
      method: 'GET',
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
      method: 'GET',
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
      if (openingBalanceLabel)
        openingBalanceLabel.textContent = formatCurrency(data.valor_abertura);
      if (currentBalanceLabel)
        currentBalanceLabel.textContent = data.saldo_formatado || 'R$ 0,00';
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
            <div class="form-group">
                <label for="fechamento-observacao">Observação:</label>
                <textarea id="fechamento-observacao" rows="3" placeholder="Digite uma observação (opcional)"></textarea>
            </div>
            <div class="modal-buttons">
                <button id="confirm-fechamento" class="btn-primary">Confirmar</button>
                <button id="cancel-fechamento" class="btn-secondary">Cancelar</button>
            </div>
        </div>
    `;

  document.body.appendChild(modal);

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
        .custom-modal input,
        .custom-modal textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .custom-modal textarea {
            resize: vertical;
        }
        .custom-modal .modal-buttons {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 20px;
        }
    `;
  document.head.appendChild(style);

  const valorInput = document.getElementById('fechamento-valor');
  const observacaoInput = document.getElementById('fechamento-observacao');

  valorInput.addEventListener('input', (e) => {
    let value = e.target.value.replace(/\D/g, '');
    value = (value / 100).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    e.target.value = value;
  });

  return new Promise((resolve, reject) => {
    document
      .getElementById('confirm-fechamento')
      .addEventListener('click', async () => {
        const valorText = valorInput.value.replace(/\./g, '').replace(',', '.');
        const valorNumerico = parseFloat(valorText);
        const observacao = observacaoInput.value || '';

        if (isNaN(valorNumerico) || valorNumerico <= 0) {
          showMessage('Valor de fechamento inválido', 'error');
          return;
        }

        try {
          // 1️⃣ FECHA O CAIXA PRIMEIRO
          const fechamentoResponse = await fetch('/operador/api/fechar-caixa', {
            ...preventCacheConfig,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              valor_fechamento: valorNumerico,
              observacao,
            }),
          });

          if (!fechamentoResponse.ok) {
            const errorData = await fechamentoResponse.json();
            throw new Error(errorData.error || 'Erro ao fechar caixa');
          }

          // 2️⃣ AGORA ABRE O PDF EM NOVA ABA (caixa já fechado)
          window.open('/operador/api/vendas/relatorio-diario-pdf', '_blank');

          showMessage('Caixa fechado com sucesso', 'success');
          await checkCaixaStatus();

          modal.remove();
          style.remove();
          resolve(true);
        } catch (error) {
          showMessage(error.message, 'error');
          reject(error);
        }
      });

    document.getElementById('cancel-fechamento').addEventListener('click', () => {
      showMessage('Operação cancelada', 'warning');
      modal.remove();
      style.remove();
      resolve(false);
    });
  });
}

window.updateCaixaStatus = function () {
  const caixaStatusDisplay = document.querySelector('.caixa-status');
  if (!caixaStatusDisplay || !selectedClientInput) return;

  if (selectedClientInput.value.trim() !== '') {
    caixaStatusDisplay.className = 'caixa-status caixa-operacao';
    caixaStatusDisplay.innerHTML =
      '<i class="fas fa-user-check"></i><span>CAIXA EM OPERAÇÃO</span>';
  } else {
    caixaStatusDisplay.className = 'caixa-status caixa-livre';
    caixaStatusDisplay.innerHTML =
      '<i class="fas fa-check-circle"></i><span>CAIXA LIVRE</span>';
  }
};

// ==================== FUNÇÕES DE BUSCA DINÂMICA ====================
function showSearchResults(results, containerId, type) {
  const resultsContainer = document.getElementById(containerId);
  if (!resultsContainer) return;
  resultsContainer.innerHTML = '';

  if (results.length === 0) {
    resultsContainer.innerHTML =
      '<div class="no-results">Nenhum resultado encontrado</div>';
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
        <div class="client-info">
          <strong>${item.nome}</strong>
          <div class="client-details">
            ${item.documento ? `<span>Documento: ${formatDocument(item.documento)}</span>` : ''}
            ${item.telefone ? `<span>Telefone: ${formatPhone(item.telefone)}</span>` : ''}
          </div>
        </div>
      `;
      resultItem.addEventListener('click', () => {
        selectClient(item);
        resultsContainer.style.display = 'none';
        if (clientSearchInput) clientSearchInput.value = '';
      });
    } else if (type === 'product') {
      const productImage = item.foto
        ? `<img src="${item.foto}" alt="${item.nome}" class="product-image">`
        : `<div class="product-image-placeholder">Sem imagem</div>`;

      resultItem.innerHTML = `
        <div class="product-result-item">
          <div class="product-image-container">
            ${productImage}
          </div>
          <div class="product-info">
            <h4>${item.nome}</h4>
            <div class="product-details">
              <span class="product-detail-item">Código: ${item.codigo || 'N/A'}</span>
              ${item.marca ? `<span class="product-detail-item">Marca: ${item.marca}</span>` : ''}
              <span class="product-price">${formatCurrency(item.valor_unitario)}</span>
            </div>
            <div class="product-stock">
              <div class="stock-item loja">
                <span>Loja:</span>
                <strong>${item.estoque_loja || 0} ${item.unidade || 'un'}</strong>
              </div>
              <div class="stock-item deposito">
                <span>Depósito:</span>
                <strong>${item.estoque_deposito || 0} ${item.unidade || 'un'}</strong>
              </div>
            </div>
          </div>
        </div>
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
    const response = await fetch(
      `/operador/api/clientes/buscar?q=${encodeURIComponent(
        searchTerm,
      )}&timestamp=${new Date().getTime()}`,
      {
        ...preventCacheConfig,
        method: 'GET',
      },
    );
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

  if (clients.length === 0) {
    dropdown.innerHTML = '<div class="no-results">Nenhum cliente encontrado</div>';
    dropdown.style.display = 'block';
    return;
  }

  clients.forEach((client) => {
    const item = document.createElement('div');
    item.className = 'client-result-item';
    item.innerHTML = `
      <div class="client-info">
        <strong>${client.nome}</strong>
        <div class="client-details">
          ${client.documento ? `<span>CPF: ${formatDocument(client.documento)}</span>` : ''}
          ${client.telefone ? `<span>Tel: ${formatPhone(client.telefone)}</span>` : ''}
        </div>
      </div>
    `;
    item.addEventListener('click', () => {
      selectClient(client);
      dropdown.innerHTML = '';
      clientSearchInput.value = '';
    });

    // Adiciona funcionalidade de teclado
    item.tabIndex = 0;
    item.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        item.click();
      }
    });

    dropdown.appendChild(item);
  });

  // Seleciona automaticamente o primeiro item
  if (clients.length > 0) {
    dropdown.querySelector('.client-result-item').classList.add('selected');
  }

  dropdown.style.display = 'block';
}

// Funções auxiliares para formatação (caso não existam)
function formatDocument(doc) {
  // Formata CPF ou CNPJ
  if (doc.length === 11) {
    return doc.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  } else if (doc.length === 14) {
    return doc.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
  }
  return doc;
}

function formatPhone(phone) {
  // Formata telefone
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 11) {
    return cleaned.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
  } else if (cleaned.length === 10) {
    return cleaned.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  }
  return phone;
}

function formatCurrency(value) {
  // Formata valor monetário
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value || 0);
}

async function searchProducts(searchTerm) {
  try {
    const response = await fetch(
      `/operador/api/produtos/buscar?q=${encodeURIComponent(
        searchTerm,
      )}&timestamp=${new Date().getTime()}`,
      {
        ...preventCacheConfig,
        method: 'GET',
      },
    );
    if (!response.ok) throw new Error('Erro ao buscar produtos');
    const results = await response.json();
    showSearchResults(results, 'product-search-results', 'product');
  } catch (error) {
    console.error('Erro na busca de produtos:', error);
    showMessage(error.message, 'error');
  }
}

function closeAllDropdowns() {
  document.querySelectorAll('.search-results-dropdown').forEach((dropdown) => {
    dropdown.style.display = 'none';
    dropdown.querySelectorAll('.search-result-item').forEach((item) => {
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
      minute: '2-digit',
    });
  }
}

function toggleBalance() {
  balanceVisible = !balanceVisible;
  updateBalance();
  if (toggleBalanceBtn) {
    toggleBalanceBtn.innerHTML = balanceVisible
      ? '<i class="fas fa-eye-slash"></i>'
      : '<i class="fas fa-eye"></i>';
  }
}

function formatCurrency(value) {
  const parsed = Number(typeof value === 'string' ? value.replace(',', '.') : value);
  if (isNaN(parsed)) return 'R$ 0,00';
  return (
    'R$ ' +
    parsed
      .toFixed(2)
      .replace('.', ',')
      .replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  );
}

function switchTab(tabId) {
  tabBtns.forEach((btn) => btn.classList.toggle('active', btn.dataset.tab === tabId));
  tabContents.forEach((content) =>
    content.classList.toggle('active', content.id === tabId),
  );
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
    icon.className =
      type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
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
      Pragma: 'no-cache',
      Expires: '0',
    },
  });
}

// ==================== CONFIGURAÇÃO DE EVENT LISTENERS ====================
function setupEventListeners() {
  if (toggleBalanceBtn) toggleBalanceBtn.addEventListener('click', toggleBalance);
  if (tabBtns) {
    tabBtns.forEach((btn) => {
      btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
  }
  if (clientSearchInput) {
    clientSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown' && activeSearchDropdown) {
        e.preventDefault();
        navigateSearchResults('down');
      }
    });
  }
  if (productSearchInput) {
    productSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown' && activeSearchDropdown) {
        e.preventDefault();
        navigateSearchResults('down');
      }
    });
  }
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      window.location.href = '/logout?' + new Date().getTime();
    });
  }
  const searchClientBtn = document.getElementById('search-client-btn');
  if (searchClientBtn) searchClientBtn.addEventListener('click', searchClient);
  if (clientSearchInput) {
    clientSearchInput.addEventListener('focus', function () {
      showClientSearchResults(clients);
    });
    clientSearchInput.addEventListener('input', function (e) {
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
  if (searchProductBtn)
    searchProductBtn.addEventListener('click', openProductSearchModal);
  if (productSearchInput) {
    productSearchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') openProductSearchModal();
    });
  }
  if (addProductBtn) addProductBtn.addEventListener('click', addEmptyProductRow);
  if (modalCloses) {
    modalCloses.forEach((btn) => {
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
  // document.addEventListener('balanceUpdated', (event) => console.log('Saldo atualizado:', event.detail));
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
    clientSearchInput.addEventListener('input', function (e) {
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
    clientSearchInput.addEventListener('focus', async function () {
      await searchClients('');
    });
  }
  if (productSearchInput) {
    productSearchInput.addEventListener('input', function (e) {
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
    productSearchInput.addEventListener('focus', function () {
      if (productSearchInput.value.trim().length >= 2) {
        searchProducts(productSearchInput.value.trim());
      } else {
        searchProducts('');
      }
    });
  }
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.search-container') && activeSearchDropdown) {
      closeAllDropdowns();
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && activeSearchDropdown) {
      closeAllDropdowns();
    }
  });
  const removeClientBtn = document.getElementById('remove-selected-client-btn');
  if (removeClientBtn) {
    removeClientBtn.addEventListener('click', function () {
      if (selectedClientInput) selectedClientInput.value = '';
      if (selectedClientIdInput) selectedClientIdInput.value = '';
      updateCaixaStatus();
    });
  }

  const paymentMethodSelect = document.getElementById('payment-method');
  if (paymentMethodSelect) {
    paymentMethodSelect.addEventListener('change', function () {
      if (this.value === 'dinheiro' && amountReceivedInput) {
        const totalText = saleTotalElement.textContent
          .replace('R$ ', '')
          .replace(/\./g, '')
          .replace(',', '.');
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
  document
    .querySelector('.add-payment-method')
    ?.addEventListener('click', addPaymentMethod);
  document.querySelector('.payment-amount')?.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
      addPaymentMethod();
    }
  });
}
// ==================== FUNÇÕES DE DESCONTO MANUAL ====================
function setupDiscountControls() {
  const applyDiscountBtn = document.getElementById('apply-discount-btn');
  if (applyDiscountBtn) {
    applyDiscountBtn.addEventListener('click', applyDiscount);
  }

  // Adiciona listener para tecla Enter no campo de valor do desconto
  const discountValueInput = document.getElementById('discount-value');
  if (discountValueInput) {
    discountValueInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        applyDiscount();
      }
    });
  }

  // Adiciona listener para o botão de remover todos os descontos
  const removeAllDiscountsBtn = document.getElementById('remove-all-discounts-btn');
  if (removeAllDiscountsBtn) {
    removeAllDiscountsBtn.addEventListener('click', removeAllDiscounts);
  }
}

function applyDiscount() {
  try {
    const discountType = document.getElementById('discount-type').value;
    const discountValueInput = document.getElementById('discount-value').value.trim();
    const selectedProductIndex = getSelectedProductIndex();

    if (!discountValueInput) {
      throw new Error('Digite um valor para o desconto');
    }

    const discountValue = parseFloat(discountValueInput.replace(',', '.'));
    if (isNaN(discountValue)) {
      throw new Error('Valor de desconto inválido. Use apenas números.');
    }

    // Se houver um produto selecionado na tabela, aplica desconto apenas nesse produto
    if (selectedProductIndex !== -1) {
      applyProductDiscount(selectedProductIndex, discountType, discountValue);
    } else {
      // Se não houver produto selecionado, aplica desconto geral
      applyGlobalDiscount(discountType, discountValue);
    }

    // Limpa o campo de valor
    document.getElementById('discount-value').value = '';
  } catch (error) {
    showMessage(error.message, 'error');
  }
}

function applyProductDiscount(productIndex, discountType, discountValue) {
  if (productIndex < 0 || productIndex >= selectedProducts.length) {
    throw new Error('Produto selecionado inválido');
  }

  const product = selectedProducts[productIndex];

  // Validações específicas
  if (discountType === 'percentual') {
    if (discountValue <= 0 || discountValue > 100) {
      throw new Error('Percentual deve ser entre 0.01% e 100%');
    }
    // Calcula desconto percentual
    const discountAmount = product.originalPrice * (discountValue / 100);
    product.price = product.originalPrice - discountAmount;
  } else {
    // Desconto fixo
    if (discountValue <= 0) {
      throw new Error('Valor fixo deve ser maior que zero');
    }
    if (discountValue >= product.originalPrice) {
      throw new Error(
        `Desconto não pode ser maior que ${formatCurrency(product.originalPrice)}`,
      );
    }
    product.price = product.originalPrice - discountValue;
  }

  product.hasDiscount = true;
  product.discountInfo = {
    tipo: discountType,
    valor: discountValue,
    valor_aplicado:
      discountType === 'percentual'
        ? `${discountValue}%`
        : formatCurrency(discountValue),
    identificador: 'MANUAL',
    descricao: 'Desconto manual aplicado no produto',
  };

  // Atualiza a linha específica
  updateProductRow(productIndex);
  calculateSaleTotal();

  showMessage(`Desconto aplicado no produto ${product.name}!`);
}

function updateProductRow(productIndex) {
  const product = selectedProducts[productIndex];
  const row = productsList.querySelector(`[data-unique-id="${product.uniqueId}"]`);

  if (!row) return;

  const totalValue = product.price * (product.quantity || 0);
  const originalTotalValue = product.originalPrice * (product.quantity || 0);
  const discountValue = originalTotalValue - totalValue;

  // Atualiza o preço unitário
  const priceCell = row.querySelector('.product-price');
  if (priceCell) {
    priceCell.innerHTML = `
            ${formatCurrency(product.price)}
            ${
              product.hasDiscount
                ? `<small class="original-price">${formatCurrency(
                    product.originalPrice,
                  )}</small>`
                : ''
            }
        `;
  }

  // Atualiza badge de desconto
  const badgeCell = row.querySelector('.discount-badge');
  if (badgeCell) {
    if (product.hasDiscount && product.discountInfo) {
      badgeCell.innerHTML = `
                <i class="fas fa-tag"></i> ${
                  product.discountInfo.identificador || 'DESCONTO'
                }
                ${
                  product.discountInfo.tipo === 'percentual'
                    ? ` (${product.discountInfo.valor}%)`
                    : ` (${formatCurrency(product.discountInfo.valor)})`
                }
            `;
      badgeCell.title = product.discountInfo.descricao || 'Desconto aplicado';
      badgeCell.style.display = 'inline-block';
    } else {
      badgeCell.innerHTML = '';
      badgeCell.style.display = 'none';
    }
  }

  // Atualiza total
  const totalCell = row.querySelector('.product-total');
  if (totalCell) {
    totalCell.innerHTML = `
            ${formatCurrency(totalValue)}
            ${
              product.hasDiscount
                ? `<small class="discount-value">(Economia: ${formatCurrency(
                    discountValue,
                  )})</small>`
                : ''
            }
        `;
  }

  // ATUALIZA O BOTÃO DE REMOVER DESCONTO - CORRIGIDO
  const actionsCell = row.querySelector('td:last-child');
  if (actionsCell) {
    // Remove botão de remover desconto existente
    const existingRemoveDiscountBtn = actionsCell.querySelector('.btn-remove-discount');
    if (existingRemoveDiscountBtn) {
      existingRemoveDiscountBtn.remove();
    }

    // Adiciona novo botão se tiver desconto
    if (product.hasDiscount) {
      const removeDiscountBtn = document.createElement('button');
      removeDiscountBtn.className = 'btn-remove-discount';
      removeDiscountBtn.dataset.uniqueId = product.uniqueId;
      removeDiscountBtn.title = 'Remover desconto deste produto';
      removeDiscountBtn.innerHTML = '<i class="fas fa-times"></i>';

      // Adiciona evento de clique
      removeDiscountBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        const uniqueId = this.dataset.uniqueId;
        const index = selectedProducts.findIndex((p) => p.uniqueId === uniqueId);
        if (index !== -1) {
          removeProductDiscount(index);
        }
      });

      // CORREÇÃO: Adiciona o botão APÓS o botão de remover produto (não antes)
      const removeBtn = actionsCell.querySelector('.btn-remove');
      if (removeBtn) {
        // Insere APÓS o botão de remover, não antes
        removeBtn.insertAdjacentElement('afterend', removeDiscountBtn);
      } else {
        // Se por algum motivo não houver botão de remover, adiciona no final
        actionsCell.appendChild(removeDiscountBtn);
      }
    }
  }
}

function getSelectedProductIndex() {
  const selectedRow = productsList.querySelector('tr.selected');
  if (selectedRow) {
    const uniqueId = selectedRow.dataset.uniqueId;
    if (uniqueId) {
      return selectedProducts.findIndex((p) => p.uniqueId === uniqueId);
    }
  }
  return -1;
}

function applyGlobalDiscount(discountType, discountValue) {
  // Valida se há produtos na venda
  if (selectedProducts.length === 0) {
    throw new Error('Adicione produtos antes de aplicar desconto');
  }

  // Calcula o subtotal atual
  const subtotal = selectedProducts.reduce((sum, product) => {
    return sum + product.originalPrice * product.quantity;
  }, 0);

  // Validações específicas
  if (discountType === 'percentual') {
    if (discountValue <= 0 || discountValue > 100) {
      throw new Error('Percentual deve ser entre 0.01% e 100%');
    }
  } else {
    if (discountValue <= 0) throw new Error('Valor fixo deve ser maior que zero');
    if (discountValue >= subtotal) {
      throw new Error(`Desconto não pode ser maior que ${formatCurrency(subtotal)}`);
    }
  }

  // Calcula o valor total do desconto
  let totalDiscount = 0;
  if (discountType === 'percentual') {
    totalDiscount = subtotal * (discountValue / 100);
  } else {
    totalDiscount = discountValue;
  }

  // Calcula o fator de ajuste para manter a proporção dos produtos
  const totalWithDiscount = subtotal - totalDiscount;
  const adjustmentFactor = totalWithDiscount / subtotal;

  // Aplica o fator de ajuste para manter a proporção entre os produtos
  selectedProducts.forEach((product, index) => {
    const newPrice = product.originalPrice * adjustmentFactor;

    selectedProducts[index] = {
      ...product,
      price: newPrice,
      hasDiscount: true,
      discountInfo: {
        tipo: discountType,
        valor: discountValue,
        valor_aplicado:
          discountType === 'percentual'
            ? `${discountValue}%`
            : formatCurrency(discountValue),
        identificador: 'MANUAL',
        descricao: 'Desconto manual aplicado',
      },
    };
  });

  // Atualiza a interface
  renderProductsList();
  calculateSaleTotal();
  showMessage(`Desconto de ${formatCurrency(totalDiscount)} aplicado ao total!`);
}

function removeProductDiscount(productIndex) {
  if (productIndex < 0 || productIndex >= selectedProducts.length) {
    return;
  }

  const product = selectedProducts[productIndex];

  // Restaura o preço original
  product.price = product.originalPrice;
  product.hasDiscount = false;
  product.discountInfo = null;

  // Atualiza a linha
  updateProductRow(productIndex);
  calculateSaleTotal();

  showMessage(`Desconto removido do produto ${product.name}`);
}

// ==================== FUNÇÕES PARA MÚLTIPLAS FORMAS DE PAGAMENTO ====================
function updateRemainingSubtotal() {
  const subtotalElement = document.getElementById('subtotal-value');
  const selectedPaymentsList = document.querySelector('.selected-payments-list');
  if (!subtotalElement || !selectedPaymentsList) return;

  if (!subtotalElement.dataset.originalValue) {
    subtotalElement.dataset.originalValue = '0';
  }

  const originalSubtotal = parseFloat(subtotalElement.dataset.originalValue) || 0;

  let totalPayments = 0;
  selectedPaymentsList
    .querySelectorAll('input[name="payment_amounts[]"]')
    .forEach((input) => {
      const value = parseFloat(input.value.replace(',', '.')) || 0;
      totalPayments += value;
    });

  const remaining = Math.max(originalSubtotal - totalPayments, 0);

  subtotalElement.textContent = formatCurrency(remaining);

  subtotalElement.dataset.currentValue = remaining.toFixed(2);
}

function addPaymentMethod() {
  const paymentMethodSelect = document.querySelector('.payment-method-select');
  const paymentAmountInput = document.querySelector('.payment-amount');
  const selectedPaymentsList = document.querySelector('.selected-payments-list');
  const subtotalElement = document.getElementById('subtotal-value');

  if (
    !paymentMethodSelect ||
    !paymentAmountInput ||
    !selectedPaymentsList ||
    !subtotalElement
  )
    return;

  // Garante valor atualizado
  updateRemainingSubtotal();

  const currentSubtotal = parseFloat(subtotalElement.dataset.currentValue || 0);

  // Impede adicionar se subtotal zerado
  if (currentSubtotal <= 0) {
    showMessage('O subtotal já foi totalmente pago.', 'error');
    return;
  }

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

  // Verifica se valor excede o restante
  if (amount > currentSubtotal) {
    showMessage('O valor digitado é maior que o valor restante do subtotal.', 'error');
    return;
  }

  // Cria item de pagamento
  const paymentItem = document.createElement('div');
  paymentItem.className = 'payment-item';
  paymentItem.innerHTML = `
        <input type="hidden" name="payment_methods[]" value="${method}">
        <input type="hidden" name="payment_amounts[]" value="${amount
          .toFixed(2)
          .replace('.', ',')}">
        <span class="payment-method">${formatPaymentMethod(method)}</span>
        <span class="payment-amount">${formatCurrency(amount)}</span>
        <button class="btn-remove-payment" title="Remover pagamento">
            <i class="fas fa-trash"></i>
        </button>
    `;

  selectedPaymentsList.appendChild(paymentItem);

  // Remove pagamento
  paymentItem
    .querySelector('.btn-remove-payment')
    .addEventListener('click', function () {
      paymentItem.remove();
      calculateSaleTotal();
      updateRemainingSubtotal();
    });

  // Limpa campos
  paymentMethodSelect.value = '';
  paymentAmountInput.value = '';

  calculateSaleTotal();
  updateRemainingSubtotal();
}

// ==================== INICIALIZAÇÃO ADICIONAL ====================
document.addEventListener('DOMContentLoaded', function () {
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
  if (openExpenseModalBtn)
    openExpenseModalBtn.addEventListener('click', openExpenseModal);
  if (cancelExpenseBtn) cancelExpenseBtn.addEventListener('click', closeExpenseModal);
  if (saveExpenseBtn) saveExpenseBtn.addEventListener('click', saveExpense);
  document
    .getElementById('generate-pdf-btn')
    ?.addEventListener('click', generateDaySalesPDF);
  document.getElementById('confirm-void-sale')?.addEventListener('click', voidSale);
  document.getElementById('cancel-void-sale')?.addEventListener('click', () => {
    closeModal('void-sale-modal');
  });
});
