const API_BASE = '/admin/fiscal';
let currentSection = 'dashboard';

// Elementos DOM
const sidebar = document.getElementById('sidebar');
const mobileToggle = document.getElementById('mobileToggle');
const pageTitle = document.getElementById('pageTitle');
const sections = document.querySelectorAll('.section');
const navLinks = document.querySelectorAll('.nav-link');
const contentSections = document.getElementById('contentSections');

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadDashboardData();
    setupEventListeners();
});

// Inicializar navegação
function initNavigation() {
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.getAttribute('data-section');
            
            if (section) {
                navigateToSection(section);
            }
            
            // Fechar sidebar no mobile
            if (window.innerWidth <= 1024) {
                sidebar.classList.remove('active');
            }
        });
    });

    // Toggle sidebar mobile
    mobileToggle.addEventListener('click', () => {
        sidebar.classList.toggle('active');
    });

    // Fechar sidebar ao clicar fora (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 1024 && 
            !sidebar.contains(e.target) && 
            !mobileToggle.contains(e.target)) {
            sidebar.classList.remove('active');
        }
    });
}

// Navegar entre seções
function navigateToSection(section) {
    // Atualizar navegação ativa
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-section') === section) {
            link.classList.add('active');
        }
    });

    // Ocultar todas as seções
    sections.forEach(sec => {
        sec.style.display = 'none';
    });

    // Mostrar seção atual
    const currentSectionEl = document.getElementById(section);
    if (currentSectionEl) {
        currentSectionEl.style.display = 'block';
        updatePageTitle(section);
        currentSection = section;
        
        // Carregar dados específicos da seção
        loadSectionData(section);
    }
}

// Atualizar título da página
function updatePageTitle(section) {
    const titles = {
        'dashboard': 'Dashboard Fiscal',
        'configuracoes': 'Configurações Fiscais',
        'produtos-fiscais': 'Produtos Fiscais',
        'transportadoras': 'Transportadoras',
        'veiculos': 'Veículos de Transporte',
        'historico': 'Histórico de Notas',
        'eventos': 'Eventos de Notas',
        'volumes': 'Volumes de Notas'
    };
    
    pageTitle.textContent = titles[section] || 'Gestão Fiscal';
}

// Configurar listeners de eventos
function setupEventListeners() {
    // Tabs
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');
            
            // Atualizar tabs ativas
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Mostrar conteúdo da tab
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            document.getElementById(tabId).style.display = 'block';
        });
    });

    // Fechar modal ao clicar fora
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
}

// Carregar dados do dashboard
async function loadDashboardData() {
    try {
        const [configs, produtos, transportadoras, eventos] = await Promise.all([
            fetchData(`${API_BASE}/configuracoes?limit=5`),
            fetchData(`${API_BASE}/produtos-fiscais/homologados?limit=5`),
            fetchData(`${API_BASE}/transportadoras?limit=5`),
            fetchData(`${API_BASE}/eventos?limit=5`)
        ]);

        // Atualizar contadores
        document.getElementById('configCount').textContent = configs.data?.length || 0;
        document.getElementById('produtosCount').textContent = produtos.data?.length || 0;
        document.getElementById('transportadorasCount').textContent = transportadoras.data?.length || 0;
        document.getElementById('eventosCount').textContent = eventos.data?.length || 0;

        // Atualizar tabela de configurações
        updateConfigTable(configs.data || []);
    } catch (error) {
        showAlert('Erro ao carregar dados do dashboard', 'danger');
    }
}

// Carregar dados específicos da seção
async function loadSectionData(section) {
    try {
        let data;
        switch(section) {
            case 'configuracoes':
                data = await fetchData(`${API_BASE}/configuracoes`);
                renderConfigList(data.data || []);
                break;
            case 'produtos-fiscais':
                data = await fetchData(`${API_BASE}/produtos-fiscais`);
                renderProdutosFiscais(data.data || []);
                break;
            case 'transportadoras':
                data = await fetchData(`${API_BASE}/transportadoras`);
                renderTransportadoras(data.data || []);
                break;
            case 'veiculos':
                data = await fetchData(`${API_BASE}/veiculos`);
                renderVeiculos(data.data || []);
                break;
            // Adicionar outros casos conforme necessário
        }
    } catch (error) {
        showAlert(`Erro ao carregar dados da seção ${section}`, 'danger');
    }
}

// Função genérica para fetch
async function fetchData(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',  
        ...options.headers
    };

    const response = await fetch(url, { 
        ...options, 
        headers,
        credentials: 'include'  
    });
    
    if (!response.ok) {
        if (response.status === 401) {
            window.location.reload(); 
        }
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
}
// Atualizar tabela de configurações
function updateConfigTable(configs) {
    const tbody = document.getElementById('configTableBody');
    tbody.innerHTML = '';

    configs.forEach(config => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${config.id}</td>
            <td>${config.razao_social}</td>
            <td>${formatCNPJ(config.cnpj)}</td>
            <td>${config.ambiente === '1' ? 'Produção' : 'Homologação'}</td>
            <td>
                <span class="status-badge ${config.ativo ? 'status-ativo' : 'status-inativo'}">
                    ${config.ativo ? 'Ativo' : 'Inativo'}
                </span>
            </td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="editConfig(${config.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger btn-sm" onclick="deleteConfig(${config.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Renderizar lista de configurações
function renderConfigList(configs) {
    const container = document.getElementById('config-list');
    
    if (!configs.length) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-cogs"></i>
                <h3>Nenhuma configuração encontrada</h3>
                <p>Clique em "Nova Configuração" para começar</p>
                <button class="btn btn-primary mt-2" onclick="showCreateConfigForm()">
                    <i class="fas fa-plus"></i> Nova Configuração
                </button>
            </div>
        `;
        return;
    }

    let html = `
        <div class="table-container">
            <div class="table-header">
                <h3 class="table-title">Configurações Fiscais</h3>
                <div class="table-actions">
                    <button class="btn btn-primary" onclick="showCreateConfigForm()">
                        <i class="fas fa-plus"></i> Nova Configuração
                    </button>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Razão Social</th>
                        <th>CNPJ</th>
                        <th>Ambiente</th>
                        <th>Status</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
    `;

    configs.forEach(config => {
        html += `
            <tr>
                <td>${config.id}</td>
                <td>${config.razao_social}</td>
                <td>${formatCNPJ(config.cnpj)}</td>
                <td>${config.ambiente === '1' ? 'Produção' : 'Homologação'}</td>
                <td>
                    <span class="status-badge ${config.ativo ? 'status-ativo' : 'status-inativo'}">
                        ${config.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="editConfig(${config.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deleteConfig(${config.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = html;
}

// Mostrar formulário de criação
function showCreateConfigForm() {
    const modal = document.getElementById('createConfigModal');
    modal.querySelector('.modal-body').innerHTML = getConfigForm();
    modal.classList.add('active');
}

// Obter formulário de configuração
function getConfigForm(config = {}) {
    return `
        <form id="configForm" onsubmit="handleConfigSubmit(event)">
            <div class="form-grid">
                <div class="form-group">
                    <label class="form-label" for="razao_social">Razão Social *</label>
                    <input type="text" id="razao_social" name="razao_social" class="form-input" 
                           value="${config.razao_social || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="nome_fantasia">Nome Fantasia</label>
                    <input type="text" id="nome_fantasia" name="nome_fantasia" class="form-input" 
                           value="${config.nome_fantasia || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="cnpj">CNPJ *</label>
                    <input type="text" id="cnpj" name="cnpj" class="form-input" 
                           value="${config.cnpj || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="inscricao_estadual">Inscrição Estadual</label>
                    <input type="text" id="inscricao_estadual" name="inscricao_estadual" class="form-input" 
                           value="${config.inscricao_estadual || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="regime_tributario">Regime Tributário</label>
                    <select id="regime_tributario" name="regime_tributario" class="form-input form-select">
                        <option value="">Selecione</option>
                        <option value="1" ${config.regime_tributario === '1' ? 'selected' : ''}>Simples Nacional</option>
                        <option value="2" ${config.regime_tributario === '2' ? 'selected' : ''}>Lucro Presumido</option>
                        <option value="3" ${config.regime_tributario === '3' ? 'selected' : ''}>Lucro Real</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="ambiente">Ambiente</label>
                    <select id="ambiente" name="ambiente" class="form-input form-select" required>
                        <option value="1" ${config.ambiente === '1' ? 'selected' : ''}>Produção</option>
                        <option value="2" ${config.ambiente === '2' ? 'selected' : ''}>Homologação</option>
                    </select>
                </div>
                
                <div class="form-group full-width">
                    <h4>Endereço</h4>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="logradouro">Logradouro *</label>
                    <input type="text" id="logradouro" name="logradouro" class="form-input" 
                           value="${config.logradouro || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="numero">Número *</label>
                    <input type="text" id="numero" name="numero" class="form-input" 
                           value="${config.numero || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="complemento">Complemento</label>
                    <input type="text" id="complemento" name="complemento" class="form-input" 
                           value="${config.complemento || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="bairro">Bairro *</label>
                    <input type="text" id="bairro" name="bairro" class="form-input" 
                           value="${config.bairro || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="municipio">Município *</label>
                    <input type="text" id="municipio" name="municipio" class="form-input" 
                           value="${config.municipio || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="uf">UF *</label>
                    <input type="text" id="uf" name="uf" class="form-input" 
                           value="${config.uf || ''}" maxlength="2" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="cep">CEP *</label>
                    <input type="text" id="cep" name="cep" class="form-input" 
                           value="${config.cep || ''}" required>
                </div>
                
                <div class="form-group full-width">
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="closeModal('createConfigModal')">
                            Cancelar
                        </button>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Salvar Configuração
                        </button>
                    </div>
                </div>
            </div>
        </form>
    `;
}

// Manipular envio do formulário de configuração
async function handleConfigSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Adicionar campos padrão
    data.ativo = true;
    
    try {
        const response = await fetchData(`${API_BASE}/configuracoes`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        showAlert('Configuração criada com sucesso!', 'success');
        closeModal('createConfigModal');
        loadDashboardData();
        loadSectionData(currentSection);
    } catch (error) {
        showAlert('Erro ao criar configuração', 'danger');
    }
}

// Editar configuração
async function editConfig(id) {
    try {
        const response = await fetchData(`${API_BASE}/configuracoes/${id}`);
        
        const modal = document.getElementById('createConfigModal');
        modal.querySelector('.modal-title').textContent = 'Editar Configuração';
        modal.querySelector('.modal-body').innerHTML = getConfigForm(response.data);
        
        // Atualizar formulário para edição
        const form = modal.querySelector('#configForm');
        form.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            try {
                await fetchData(`${API_BASE}/configuracoes/${id}`, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
                
                showAlert('Configuração atualizada com sucesso!', 'success');
                closeModal('createConfigModal');
                loadDashboardData();
                loadSectionData(currentSection);
            } catch (error) {
                showAlert('Erro ao atualizar configuração', 'danger');
            }
        };
        
        modal.classList.add('active');
    } catch (error) {
        showAlert('Erro ao carregar configuração', 'danger');
    }
}

// Excluir configuração
async function deleteConfig(id) {
    if (!confirm('Tem certeza que deseja excluir esta configuração?')) {
        return;
    }
    
    try {
        await fetchData(`${API_BASE}/configuracoes/${id}`, {
            method: 'DELETE'
        });
        
        showAlert('Configuração excluída com sucesso!', 'success');
        loadDashboardData();
        loadSectionData(currentSection);
    } catch (error) {
        showAlert('Erro ao excluir configuração', 'danger');
    }
}

// Mostrar alerta
function showAlert(message, type = 'info') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Inserir no início do main-content
    const mainContent = document.querySelector('.main-content');
    mainContent.insertBefore(alert, mainContent.firstChild);
    
    // Remover após 5 segundos
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Abrir modal
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

// Fechar modal
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Formatar CNPJ
function formatCNPJ(cnpj) {
    if (!cnpj) return '';
    return cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
}

// Formatar CPF
function formatCPF(cpf) {
    if (!cpf) return '';
    return cpf.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4');
}

// Formatar data
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

// Format date time
function formatDateTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
}

// Renderizar produtos fiscais
function renderProdutosFiscais(produtos) {
    // Implementar renderização de produtos fiscais
    console.log('Renderizando produtos fiscais:', produtos);
}

// Renderizar transportadoras
function renderTransportadoras(transportadoras) {
    // Implementar renderização de transportadoras
    console.log('Renderizando transportadoras:', transportadoras);
}

// Renderizar veículos
function renderVeiculos(veiculos) {
    // Implementar renderização de veículos
    console.log('Renderizando veículos:', veiculos);
}