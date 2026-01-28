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
        'clientes-fiscais': 'Clientes Fiscais',  // NOVO
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
                setupProdutosFiscaisTabs();
                break;
            case 'transportadoras':
                data = await fetchData(`${API_BASE}/transportadoras`);
                renderTransportadoras(data.data || []);
                if (document.getElementById('select-transportadora-veiculos')) {
                    carregarTransportadorasParaSelect('select-transportadora-veiculos');
                }
                break;
            case 'veiculos':
                data = await fetchData(`${API_BASE}/veiculos`);
                renderVeiculos(data.data || []);
                if (document.getElementById('transportadora_id')) {
                    carregarTransportadorasParaSelect('transportadora_id');
                }
                break;
            case 'clientes-fiscais':
                data = await fetchData(`${API_BASE}/clientes-fiscais`);
                renderClientesFiscais(data.data || []);
                setupClientesFiscaisTabs();
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
                    <label class="form-label" for="codigo_municipio">Código do Município (IBGE) *</label>
                    <input type="text" id="codigo_municipio" name="codigo_municipio" class="form-input" 
                        value="${config.codigo_municipio || ''}" required>
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

// ============================================
// FUNÇÕES PARA PRODUTOS FISCAIS
// ============================================
function setupProdutosFiscaisTabs() {
    const tabs = document.querySelectorAll('#produtos-fiscais .tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', async () => {
            const tabId = tab.getAttribute('data-tab');
            
            // Atualizar tabs ativas
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Mostrar conteúdo da tab
            document.querySelectorAll('#produtos-fiscais .tab-content').forEach(content => {
                content.style.display = 'none';
            });
            document.getElementById(tabId).style.display = 'block';
            
            // Carregar dados específicos da tab
            if (tabId === 'produtos-nao-homologados') {
                await carregarProdutosNaoHomologados();
            }
            // Para 'produtos-buscar', o formulário já está disponível
        });
    });
}
// Renderizar lista de produtos fiscais
function renderProdutosFiscais(produtos) {
    const container = document.getElementById('produtos-list');
    
    if (!produtos || produtos.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-box"></i>
                <h3>Nenhum produto fiscal encontrado</h3>
                <p>Clique em "Novo Produto Fiscal" para começar</p>
                <button class="btn btn-primary mt-2" onclick="showCreateProdutoFiscalForm()">
                    <i class="fas fa-plus"></i> Novo Produto Fiscal
                </button>
            </div>
        `;
        return;
    }

    let html = `
        <div class="table-container">
            <div class="table-header">
                <h3 class="table-title">Produtos Fiscais</h3>
                <div class="table-actions">
                    <button class="btn btn-primary" onclick="showCreateProdutoFiscalForm()">
                        <i class="fas fa-plus"></i> Novo Produto Fiscal
                    </button>
                </div>
            </div>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Produto</th>
                            <th>NCM</th>
                            <th>CEST</th>
                            <th>Origem</th>
                            <th>CST ICMS</th>
                            <th>Homologado</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    produtos.forEach(produto => {
        // Formatar origem
        let origem = '';
        switch(produto.origem) {
            case '0': origem = 'Nacional'; break;
            case '1': origem = 'Estrangeira'; break;
            default: origem = produto.origem || 'N/A';
        }

        html += `
            <tr>
                <td>${produto.id}</td>
                <td>${produto.produto_nome || '-'}</td>
                <td>${produto.codigo_ncm || '-'}</td>
                <td>${produto.codigo_cest || '-'}</td>
                <td>${origem}</td>
                <td>${produto.cst_icms || '-'}</td>
                <td>
                    <span class="status-badge ${produto.homologado ? 'status-ativo' : 'status-inativo'}">
                        ${produto.homologado ? 'Sim' : 'Não'}
                    </span>
                </td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-secondary btn-sm" onclick="editProdutoFiscal(${produto.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        ${!produto.homologado ? `
                            <button class="btn btn-success btn-sm" onclick="showHomologarForm(${produto.id})">
                                <i class="fas fa-check"></i>
                            </button>
                        ` : ''}
                        <button class="btn btn-danger btn-sm" onclick="deleteProdutoFiscal(${produto.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// Carregar produtos não homologados
async function carregarProdutosNaoHomologados() {
    try {
        const response = await fetchData(`${API_BASE}/produtos-fiscais/listar-nao-homologados`);
        const produtos = response.data || [];
        
        const container = document.getElementById('produtos-nao-homologados');
        
        if (!produtos.length) {
            container.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i>
                    Todos os produtos estão homologados!
                </div>
            `;
            return;
        }

        let html = `
            <div class="table-container">
                <h3 class="table-title">Produtos Não Homologados</h3>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Produto ID</th>
                                <th>NCM</th>
                                <th>CEST</th>
                                <th>Origem</th>
                                <th>CFOP</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
        `;

        produtos.forEach(produto => {
            // Formatar origem
            let origem = '';
            switch(produto.origem) {
                case '0': origem = 'Nacional'; break;
                case '1': origem = 'Estrangeira'; break;
                default: origem = produto.origem || 'N/A';
            }

            html += `
                <tr>
                    <td>${produto.id}</td>
                    <td>${produto.produto_id || '-'}</td>
                    <td>${produto.codigo_ncm || '-'}</td>
                    <td>${produto.codigo_cest || '-'}</td>
                    <td>${origem}</td>
                    <td>${produto.cfop || '-'}</td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-secondary btn-sm" onclick="editProdutoFiscal(${produto.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-success btn-sm" onclick="showHomologarForm(${produto.id})">
                                <i class="fas fa-check"></i> Homologar
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="deleteProdutoFiscal(${produto.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });

        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        container.innerHTML = html;
        
    } catch (error) {
        showAlert('Erro ao carregar produtos não homologados', 'danger');
    }
}

// Mostrar formulário de criação de produto fiscal
async function showCreateProdutoFiscalForm() {
    const modal = document.getElementById('createProdutoFiscalModal');
    modal.querySelector('.modal-body').innerHTML = getProdutoFiscalForm();
    modal.classList.add('active');
    
    await carregarProdutosParaSelectParaCadastro();
}
// Obter formulário de produto fiscal
function getProdutoFiscalForm(produto = {}) {
    const isEdit = !!produto.id;
    return `
        <form id="produtoFiscalForm" onsubmit="handleProdutoFiscalSubmit(event, ${produto.id || ''})">
            <div class="form-grid">
                <div class="form-group">
                    <label class="form-label" for="produto_id">Produto *</label>
                    ${isEdit ? 
                        `<div class="produto-info-display">
                            <div class="produto-id-badge">ID: ${produto.produto_id || 'N/A'}</div>
                            <div class="produto-nome-text">${produto.produto_nome || 'Não encontrado'}</div>
                            <div class="produto-detalhes">
                                <span>Código: ${produto.produto_codigo || 'N/A'}</span>
                                <span>•</span>
                                <span>Unidade: ${produto.produto_unidade || 'N/A'}</span>
                                <span>•</span>
                                <span>Valor: R$ ${(produto.produto_valor_unitario || 0).toFixed(2)}</span>
                            </div>
                         </div>
                         <input type="hidden" id="produto_id" name="produto_id" value="${produto.produto_id || ''}">` :
                        `<select id="produto_id" name="produto_id" class="form-input form-select" required>
                            <option value="">Selecione um produto...</option>
                         </select>`
                    }
                    <small class="form-text">${isEdit ? 'Produto não pode ser alterado após criação' : 'Escolha um produto do sistema (apenas produtos sem dados fiscais aparecerão)'}</small>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="codigo_ncm">Código NCM *</label>
                    <input type="text" id="codigo_ncm" name="codigo_ncm" class="form-input" 
                           value="${produto.codigo_ncm || ''}" required
                           placeholder="Ex: 22030000" maxlength="8">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="codigo_cest">Código CEST</label>
                    <input type="text" id="codigo_cest" name="codigo_cest" class="form-input" 
                           value="${produto.codigo_cest || ''}"
                           placeholder="Ex: 0100100" maxlength="7">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="codigo_ean">Código EAN (GTIN)</label>
                    <input type="text" id="codigo_ean" name="codigo_ean" class="form-input" 
                           value="${produto.codigo_ean || ''}"
                           placeholder="Ex: 7891234567890" maxlength="14">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="codigo_gtin_trib">Código GTIN Tributário</label>
                    <input type="text" id="codigo_gtin_trib" name="codigo_gtin_trib" class="form-input" 
                           value="${produto.codigo_gtin_trib || ''}"
                           placeholder="Código GTIN para unidade tributável" maxlength="14">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="origem">Origem *</label>
                    <select id="origem" name="origem" class="form-input form-select" required>
                        <option value="0" ${produto.origem === '0' ? 'selected' : ''}>Nacional</option>
                        <option value="1" ${produto.origem === '1' ? 'selected' : ''}>Estrangeira - Importação Direta</option>
                        <option value="2" ${produto.origem === '2' ? 'selected' : ''}>Estrangeira - Adquirida no Mercado Interno</option>
                        <option value="3" ${produto.origem === '3' ? 'selected' : ''}>Nacional - Conteúdo Importado 40%</option>
                        <option value="4" ${produto.origem === '4' ? 'selected' : ''}>Nacional - Produção Conforme Processos Produtivos</option>
                        <option value="5" ${produto.origem === '5' ? 'selected' : ''}>Nacional - Conteúdo Importado 70%</option>
                        <option value="6" ${produto.origem === '6' ? 'selected' : ''}>Estrangeira - Importação Direta sem Similar Nacional</option>
                        <option value="7" ${produto.origem === '7' ? 'selected' : ''}>Estrangeira - Adquirida Mercado Interno sem Similar Nacional</option>
                        <option value="8" ${produto.origem === '8' ? 'selected' : ''}>Nacional - Conteúdo Importado Superior a 70%</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="tipo_item">Tipo do Item</label>
                    <select id="tipo_item" name="tipo_item" class="form-input form-select">
                        <option value="">Selecione</option>
                        <option value="00" ${produto.tipo_item === '00' ? 'selected' : ''}>Mercadoria para Revenda</option>
                        <option value="01" ${produto.tipo_item === '01' ? 'selected' : ''}>Matéria-Prima</option>
                        <option value="02" ${produto.tipo_item === '02' ? 'selected' : ''}>Embalagem</option>
                        <option value="03" ${produto.tipo_item === '03' ? 'selected' : ''}>Produto em Processo</option>
                        <option value="04" ${produto.tipo_item === '04' ? 'selected' : ''}>Produto Acabado</option>
                        <option value="05" ${produto.tipo_item === '05' ? 'selected' : ''}>Subproduto</option>
                        <option value="06" ${produto.tipo_item === '06' ? 'selected' : ''}>Produto Intermediário</option>
                        <option value="07" ${produto.tipo_item === '07' ? 'selected' : ''}>Material de Uso e Consumo</option>
                        <option value="08" ${produto.tipo_item === '08' ? 'selected' : ''}>Ativo Imobilizado</option>
                        <option value="09" ${produto.tipo_item === '09' ? 'selected' : ''}>Serviços</option>
                        <option value="10" ${produto.tipo_item === '10' ? 'selected' : ''}>Outros Insumos</option>
                        <option value="99" ${produto.tipo_item === '99' ? 'selected' : ''}>Outros</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="unidade_tributaria">Unidade Tributária</label>
                    <input type="text" id="unidade_tributaria" name="unidade_tributaria" class="form-input" 
                           value="${produto.unidade_tributaria || ''}"
                           placeholder="Ex: UN, KG, M2">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="valor_unitario_trib">Valor Unitário Tributário</label>
                    <input type="number" id="valor_unitario_trib" name="valor_unitario_trib" class="form-input" 
                           value="${produto.valor_unitario_trib || ''}" step="0.0001"
                           placeholder="Ex: 10.5000">
                </div>
                
                <div class="form-group full-width">
                    <h4>Tributação ICMS</h4>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="cst_icms">CST ICMS *</label>
                    <select id="cst_icms" name="cst_icms" class="form-input form-select" required>
                        <option value="">Selecione</option>
                        <option value="00" ${produto.cst_icms === '00' ? 'selected' : ''}>00 - Tributada integralmente</option>
                        <option value="10" ${produto.cst_icms === '10' ? 'selected' : ''}>10 - Tributada com cobrança do ICMS por ST</option>
                        <option value="20" ${produto.cst_icms === '20' ? 'selected' : ''}>20 - Com redução da BC</option>
                        <option value="30" ${produto.cst_icms === '30' ? 'selected' : ''}>30 - Isenta / não tributada</option>
                        <option value="40" ${produto.cst_icms === '40' ? 'selected' : ''}>40 - Isenta</option>
                        <option value="41" ${produto.cst_icms === '41' ? 'selected' : ''}>41 - Não tributada</option>
                        <option value="50" ${produto.cst_icms === '50' ? 'selected' : ''}>50 - Suspensão</option>
                        <option value="51" ${produto.cst_icms === '51' ? 'selected' : ''}>51 - Diferimento</option>
                        <option value="60" ${produto.cst_icms === '60' ? 'selected' : ''}>60 - ICMS cobrado anteriormente por ST</option>
                        <option value="70" ${produto.cst_icms === '70' ? 'selected' : ''}>70 - Com redução da BC e cobrança do ICMS por ST</option>
                        <option value="90" ${produto.cst_icms === '90' ? 'selected' : ''}>90 - Outras</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="cfop">CFOP *</label>
                    <input type="text" id="cfop" name="cfop" class="form-input" 
                           value="${produto.cfop || ''}" required
                           placeholder="Ex: 5102" maxlength="4">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="aliquota_icms">Alíquota ICMS (%)</label>
                    <input type="number" id="aliquota_icms" name="aliquota_icms" class="form-input" 
                           value="${produto.aliquota_icms || ''}" step="0.01" min="0" max="100"
                           placeholder="Ex: 18.00">
                </div>
                
                <div class="form-group full-width">
                    <h4>Tributação PIS/COFINS</h4>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="cst_pis">CST PIS</label>
                    <select id="cst_pis" name="cst_pis" class="form-input form-select">
                        <option value="">Selecione</option>
                        <option value="01" ${produto.cst_pis === '01' ? 'selected' : ''}>01 - Operação Tributável com Alíquota Básica</option>
                        <option value="02" ${produto.cst_pis === '02' ? 'selected' : ''}>02 - Operação Tributável com Alíquota Diferenciada</option>
                        <option value="03" ${produto.cst_pis === '03' ? 'selected' : ''}>03 - Operação Tributável com Alíquota por Unidade de Medida</option>
                        <option value="04" ${produto.cst_pis === '04' ? 'selected' : ''}>04 - Operação Tributável Monofásica - Revenda a Alíquota Zero</option>
                        <option value="05" ${produto.cst_pis === '05' ? 'selected' : ''}>05 - Operação Tributável por Substituição Tributária</option>
                        <option value="06" ${produto.cst_pis === '06' ? 'selected' : ''}>06 - Operação Tributável a Alíquota Zero</option>
                        <option value="07" ${produto.cst_pis === '07' ? 'selected' : ''}>07 - Operação Isenta da Contribuição</option>
                        <option value="08" ${produto.cst_pis === '08' ? 'selected' : ''}>08 - Operação sem Incidência da Contribuição</option>
                        <option value="09" ${produto.cst_pis === '09' ? 'selected' : ''}>09 - Operação com Suspensão da Contribuição</option>
                        <option value="49" ${produto.cst_pis === '49' ? 'selected' : ''}>49 - Outras Operações de Saída</option>
                        <option value="50" ${produto.cst_pis === '50' ? 'selected' : ''}>50 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="51" ${produto.cst_pis === '51' ? 'selected' : ''}>51 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="52" ${produto.cst_pis === '52' ? 'selected' : ''}>52 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="53" ${produto.cst_pis === '53' ? 'selected' : ''}>53 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="54" ${produto.cst_pis === '54' ? 'selected' : ''}>54 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="55" ${produto.cst_pis === '55' ? 'selected' : ''}>55 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="56" ${produto.cst_pis === '56' ? 'selected' : ''}>56 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="60" ${produto.cst_pis === '60' ? 'selected' : ''}>60 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="61" ${produto.cst_pis === '61' ? 'selected' : ''}>61 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="62" ${produto.cst_pis === '62' ? 'selected' : ''}>62 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="63" ${produto.cst_pis === '63' ? 'selected' : ''}>63 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="64" ${produto.cst_pis === '64' ? 'selected' : ''}>64 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="65" ${produto.cst_pis === '65' ? 'selected' : ''}>65 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="66" ${produto.cst_pis === '66' ? 'selected' : ''}>66 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="67" ${produto.cst_pis === '67' ? 'selected' : ''}>67 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="70" ${produto.cst_pis === '70' ? 'selected' : ''}>70 - Operação de Aquisição sem Direito a Crédito</option>
                        <option value="71" ${produto.cst_pis === '71' ? 'selected' : ''}>71 - Operação de Aquisição com Isenção</option>
                        <option value="72" ${produto.cst_pis === '72' ? 'selected' : ''}>72 - Operação de Aquisição com Suspensão</option>
                        <option value="73" ${produto.cst_pis === '73' ? 'selected' : ''}>73 - Operação de Aquisição a Alíquota Zero</option>
                        <option value="74" ${produto.cst_pis === '74' ? 'selected' : ''}>74 - Operação de Aquisição sem Incidência da Contribuição</option>
                        <option value="75" ${produto.cst_pis === '75' ? 'selected' : ''}>75 - Operação de Aquisição por Substituição Tributária</option>
                        <option value="98" ${produto.cst_pis === '98' ? 'selected' : ''}>98 - Outras Operações de Entrada</option>
                        <option value="99" ${produto.cst_pis === '99' ? 'selected' : ''}>99 - Outras Operações</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="aliquota_pis">Alíquota PIS (%)</label>
                    <input type="number" id="aliquota_pis" name="aliquota_pis" class="form-input" 
                           value="${produto.aliquota_pis || ''}" step="0.01" min="0" max="100"
                           placeholder="Ex: 1.65">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="cst_cofins">CST COFINS</label>
                    <select id="cst_cofins" name="cst_cofins" class="form-input form-select">
                        <option value="">Selecione</option>
                        <option value="01" ${produto.cst_cofins === '01' ? 'selected' : ''}>01 - Operação Tributável com Alíquota Básica</option>
                        <option value="02" ${produto.cst_cofins === '02' ? 'selected' : ''}>02 - Operação Tributável com Alíquota Diferenciada</option>
                        <option value="03" ${produto.cst_cofins === '03' ? 'selected' : ''}>03 - Operação Tributável com Alíquota por Unidade de Medida</option>
                        <option value="04" ${produto.cst_cofins === '04' ? 'selected' : ''}>04 - Operação Tributável Monofásica - Revenda a Alíquota Zero</option>
                        <option value="05" ${produto.cst_cofins === '05' ? 'selected' : ''}>05 - Operação Tributável por Substituição Tributária</option>
                        <option value="06" ${produto.cst_cofins === '06' ? 'selected' : ''}>06 - Operação Tributável a Alíquota Zero</option>
                        <option value="07" ${produto.cst_cofins === '07' ? 'selected' : ''}>07 - Operação Isenta da Contribuição</option>
                        <option value="08" ${produto.cst_cofins === '08' ? 'selected' : ''}>08 - Operação sem Incidência da Contribuição</option>
                        <option value="09" ${produto.cst_cofins === '09' ? 'selected' : ''}>09 - Operação com Suspensão da Contribuição</option>
                        <option value="49" ${produto.cst_cofins === '49' ? 'selected' : ''}>49 - Outras Operações de Saída</option>
                        <option value="50" ${produto.cst_cofins === '50' ? 'selected' : ''}>50 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="51" ${produto.cst_cofins === '51' ? 'selected' : ''}>51 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="52" ${produto.cst_cofins === '52' ? 'selected' : ''}>52 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="53" ${produto.cst_cofins === '53' ? 'selected' : ''}>53 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="54" ${produto.cst_cofins === '54' ? 'selected' : ''}>54 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="55" ${produto.cst_cofins === '55' ? 'selected' : ''}>55 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="56" ${produto.cst_cofins === '56' ? 'selected' : ''}>56 - Operação com Direito a Crédito - Vinculada</option>
                        <option value="60" ${produto.cst_cofins === '60' ? 'selected' : ''}>60 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="61" ${produto.cst_cofins === '61' ? 'selected' : ''}>61 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="62" ${produto.cst_cofins === '62' ? 'selected' : ''}>62 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="63" ${produto.cst_cofins === '63' ? 'selected' : ''}>63 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="64" ${produto.cst_cofins === '64' ? 'selected' : ''}>64 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="65" ${produto.cst_cofins === '65' ? 'selected' : ''}>65 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="66" ${produto.cst_cofins === '66' ? 'selected' : ''}>66 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="67" ${produto.cst_cofins === '67' ? 'selected' : ''}>67 - Crédito Presumido - Operação de Aquisição Vinculada</option>
                        <option value="70" ${produto.cst_cofins === '70' ? 'selected' : ''}>70 - Operação de Aquisição sem Direito a Crédito</option>
                        <option value="71" ${produto.cst_cofins === '71' ? 'selected' : ''}>71 - Operação de Aquisição com Isenção</option>
                        <option value="72" ${produto.cst_cofins === '72' ? 'selected' : ''}>72 - Operação de Aquisição com Suspensão</option>
                        <option value="73" ${produto.cst_cofins === '73' ? 'selected' : ''}>73 - Operação de Aquisição a Alíquota Zero</option>
                        <option value="74" ${produto.cst_cofins === '74' ? 'selected' : ''}>74 - Operação de Aquisição sem Incidência da Contribuição</option>
                        <option value="75" ${produto.cst_cofins === '75' ? 'selected' : ''}>75 - Operação de Aquisição por Substituição Tributária</option>
                        <option value="98" ${produto.cst_cofins === '98' ? 'selected' : ''}>98 - Outras Operações de Entrada</option>
                        <option value="99" ${produto.cst_cofins === '99' ? 'selected' : ''}>99 - Outras Operações</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="aliquota_cofins">Alíquota COFINS (%)</label>
                    <input type="number" id="aliquota_cofins" name="aliquota_cofins" class="form-input" 
                           value="${produto.aliquota_cofins || ''}" step="0.01" min="0" max="100"
                           placeholder="Ex: 7.60">
                </div>
                
                <div class="form-group full-width">
                    <h4>Informações Adicionais</h4>
                </div>
                
                <div class="form-group full-width">
                    <label class="form-label" for="informacoes_fisco">Informações ao Fisco</label>
                    <textarea id="informacoes_fisco" name="informacoes_fisco" class="form-input" rows="3"
                              placeholder="Informações relevantes para o fisco...">${produto.informacoes_fisco || ''}</textarea>
                </div>
                
                <div class="form-group full-width">
                    <label class="form-label" for="informacoes_complementares">Informações Complementares</label>
                    <textarea id="informacoes_complementares" name="informacoes_complementares" class="form-input" rows="3"
                              placeholder="Informações complementares para o cliente...">${produto.informacoes_complementares || ''}</textarea>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="homologado">Status de Homologação</label>
                    <select id="homologado" name="homologado" class="form-input form-select">
                        <option value="false" ${!produto.homologado ? 'selected' : ''}>Não Homologado</option>
                        <option value="true" ${produto.homologado ? 'selected' : ''}>Homologado</option>
                    </select>
                </div>
                
                <div class="form-group full-width">
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="closeModal('createProdutoFiscalModal')">
                            Cancelar
                        </button>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> ${produto.id ? 'Atualizar' : 'Salvar'} Produto Fiscal
                        </button>
                    </div>
                </div>
            </div>
        </form>
    `;
}

// Nova função específica para cadastro
async function carregarProdutosParaSelectParaCadastro() {
    try {
        const select = document.getElementById('produto_id');
        if (!select) {
            console.warn('Select produto_id não encontrado');
            return;
        }
        
        // Para cadastro, sempre carregar produtos
        const response = await fetchData(`${API_BASE}/produtos`);
        const produtos = response.data || [];
        
        if (!produtos.length) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Nenhum produto disponível';
            select.appendChild(option);
            return;
        }
        
        // Limpar opções existentes (mantendo a primeira)
        while (select.options.length > 1) {
            select.remove(1);
        }
        
        produtos.forEach(produto => {
            // Não mostrar produtos que já têm dados fiscais
            if (produto.tem_dados_fiscais) {
                return; // Pula este produto
            }
            
            const option = document.createElement('option');
            option.value = produto.id;
            option.textContent = `${produto.nome} (ID: ${produto.id}, Código: ${produto.codigo || 'N/A'})`;
            select.appendChild(option);
        });
        
    } catch (error) {
        console.error('Erro ao carregar produtos para select (cadastro):', error);
        const select = document.getElementById('produto_id');
        if (select) {
            while (select.options.length > 1) {
                select.remove(1);
            }
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Erro ao carregar produtos';
            select.appendChild(option);
        }
    }
}

async function carregarProdutosParaSelect() {
    try {
        const select = document.getElementById('produto_id');
        if (!select) {
            console.warn('Select produto_id não encontrado - elemento não existe no DOM');
            return;
        }
        
        // Se já tem produtos carregados (mais de 1 opção), não carregar novamente
        if (select.options && select.options.length > 1) {
            return;
        }
        
        // Para edição, carregar todos os produtos
        const response = await fetchData(`${API_BASE}/produtos`);
        const produtos = response.data || [];
        
        if (!produtos.length) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Nenhum produto disponível';
            select.appendChild(option);
            return;
        }
        
        produtos.forEach(produto => {
            const option = document.createElement('option');
            option.value = produto.id;
            option.textContent = `${produto.nome} (ID: ${produto.id}, Código: ${produto.codigo || 'N/A'})`;
            
            // Se for edição e este for o produto correto, marcar como selecionado
            if (window.currentEditingProdutoId && produto.tem_dados_fiscais && 
                produto.produto_fiscal_id == window.currentEditingProdutoId) {
                option.selected = true;
            }
            
            select.appendChild(option);
        });
        
    } catch (error) {
        console.error('Erro ao carregar produtos para select (edição):', error);
        const select = document.getElementById('produto_id');
        if (select && select.options) {
            while (select.options.length > 1) {
                select.remove(1);
            }
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Erro ao carregar produtos';
            select.appendChild(option);
        }
    }
}

// Manipular envio do formulário de produto fiscal
async function handleProdutoFiscalSubmit(event, id = null) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Converter valores booleanos
    data.homologado = data.homologado === 'true';
    
    // Converter string vazia para null
    Object.keys(data).forEach(key => {
        if (data[key] === '') {
            data[key] = null;
        }
    });
    
    // Converter números
    const numericFields = ['produto_id', 'valor_unitario_trib', 'aliquota_icms', 'aliquota_pis', 'aliquota_cofins'];
    numericFields.forEach(field => {
        if (data[field] !== null) {
            data[field] = parseFloat(data[field]);
        }
    });
    
    try {
        let response;
        if (id) {
            // Atualização
            response = await fetchData(`${API_BASE}/produtos-fiscais/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            showAlert('Produto fiscal atualizado com sucesso!', 'success');
        } else {
            // Criação
            response = await fetchData(`${API_BASE}/produtos-fiscais`, {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showAlert('Produto fiscal criado com sucesso!', 'success');
        }
        
        closeModal('createProdutoFiscalModal');
        
        // Recarregar dados baseado na aba atual
        const section = currentSection;
        if (section === 'produtos-fiscais') {
            // Recarregar lista principal
            const produtosResponse = await fetchData(`${API_BASE}/produtos-fiscais`);
            renderProdutosFiscais(produtosResponse.data || []);
            
            // Recarregar não homologados se estiver naquela aba
            const tabAtiva = document.querySelector('#produtos-fiscais .tab.active');
            if (tabAtiva && tabAtiva.getAttribute('data-tab') === 'produtos-nao-homologados') {
                await carregarProdutosNaoHomologados();
            }
        }
        
    } catch (error) {
        showAlert(id ? 'Erro ao atualizar produto fiscal' : 'Erro ao criar produto fiscal', 'danger');
        console.error('Erro detalhado:', error);
    }
}

// Editar produto fiscal
async function editProdutoFiscal(id) {
    try {
        window.currentEditingProdutoId = id;
        
        const response = await fetchData(`${API_BASE}/produtos-fiscais/${id}`);
        const produto = response.data;
        const modal = document.getElementById('createProdutoFiscalModal');
        modal.querySelector('.modal-title').textContent = 'Editar Produto Fiscal';
        modal.querySelector('.modal-body').innerHTML = getProdutoFiscalForm(produto);
        
        modal.classList.add('active');
        
        setTimeout(async () => {
            await carregarProdutosParaSelect();
        }, 100);
        
    } catch (error) {
        showAlert('Erro ao carregar produto fiscal', 'danger');
    }
}

// Excluir produto fiscal
async function deleteProdutoFiscal(id) {
    if (!confirm('Tem certeza que deseja excluir este produto fiscal?\nEsta ação não pode ser desfeita.')) {
        return;
    }
    
    try {
        await fetchData(`${API_BASE}/produtos-fiscais/${id}`, {
            method: 'DELETE'
        });
        
        showAlert('Produto fiscal excluído com sucesso!', 'success');
        
        // Recarregar dados
        const produtosResponse = await fetchData(`${API_BASE}/produtos-fiscais`);
        renderProdutosFiscais(produtosResponse.data || []);
        
        // Recarregar não homologados se estiver visível
        if (document.querySelector('#produtos-fiscais .tab.active').getAttribute('data-tab') === 'produtos-nao-homologados') {
            await carregarProdutosNaoHomologados();
        }
        
    } catch (error) {
        showAlert('Erro ao excluir produto fiscal', 'danger');
    }
}

// Buscar produtos fiscais
async function buscarProdutosFiscais() {
    try {
        const termo = document.getElementById('buscar-produto-fiscal').value.trim();
        
        if (!termo) {
            showAlert('Digite um termo para buscar', 'warning');
            return;
        }
        
        // Primeiro, tentar buscar por produto_id se for número
        if (!isNaN(termo)) {
            try {
                const response = await fetchData(`${API_BASE}/produtos-fiscais/${termo}`);
                if (response.success && response.data) {
                    exibirResultadoBusca([response.data]);
                    return;
                }
            } catch (error) {
                // Continua para buscar por outros critérios
            }
        }
        
        // Buscar por produto_id
        try {
            const response = await fetchData(`${API_BASE}/produtos-fiscais/produto/${termo}`);
            if (response.success && response.data) {
                exibirResultadoBusca([response.data]);
                return;
            }
        } catch (error) {
            // Continua para buscar por NCM
        }
        
        // Se não encontrou, buscar por NCM
        try {
            const response = await fetchData(`${API_BASE}/produtos-fiscais/ncm/${termo}`);
            if (response.success && response.data && response.data.length > 0) {
                exibirResultadoBusca(response.data);
                return;
            }
        } catch (error) {
            // Continua
        }
        
        // Se não encontrou, mostrar mensagem
        document.getElementById('resultados-busca-produtos-fiscais').innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i>
                Nenhum produto fiscal encontrado para "${termo}"
            </div>
        `;
        
    } catch (error) {
        showAlert('Erro ao buscar produtos fiscais', 'danger');
    }
}

// Exibir resultado da busca
function exibirResultadoBusca(produtos) {
    const container = document.getElementById('resultados-busca-produtos-fiscais');
    
    if (!produtos || produtos.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i>
                Nenhum produto fiscal encontrado
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="table-container">
            <h4>Resultados da Busca (${produtos.length} encontrados)</h4>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Produto ID</th>
                            <th>NCM</th>
                            <th>CEST</th>
                            <th>Origem</th>
                            <th>CST ICMS</th>
                            <th>Homologado</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    produtos.forEach(produto => {
        let origem = '';
        switch(produto.origem) {
            case '0': origem = 'Nacional'; break;
            case '1': origem = 'Estrangeira'; break;
            default: origem = produto.origem || 'N/A';
        }
        
        html += `
            <tr>
                <td>${produto.id}</td>
                <td>${produto.produto_id || '-'}</td>
                <td>${produto.codigo_ncm || '-'}</td>
                <td>${produto.codigo_cest || '-'}</td>
                <td>${origem}</td>
                <td>${produto.cst_icms || '-'}</td>
                <td>
                    <span class="status-badge ${produto.homologado ? 'status-ativo' : 'status-inativo'}">
                        ${produto.homologado ? 'Sim' : 'Não'}
                    </span>
                </td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-secondary btn-sm" onclick="editProdutoFiscal(${produto.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        ${!produto.homologado ? `
                            <button class="btn btn-success btn-sm" onclick="showHomologarForm(${produto.id})">
                                <i class="fas fa-check"></i>
                            </button>
                        ` : ''}
                        <button class="btn btn-danger btn-sm" onclick="deleteProdutoFiscal(${produto.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Mostrar formulário de homologação
function showHomologarForm(produtoId) {
    document.getElementById('homologar_produto_id').value = produtoId;
    document.getElementById('homologar_justificativa').value = '';
    
    const modal = document.getElementById('homologarProdutoModal');
    modal.classList.add('active');
}

// Submeter homologação
async function homologarProdutoSubmit(event) {
    event.preventDefault();
    
    const produtoId = document.getElementById('homologar_produto_id').value;
    const justificativa = document.getElementById('homologar_justificativa').value;
    
    if (!produtoId || !justificativa.trim()) {
        showAlert('Preencha a justificativa da homologação', 'warning');
        return;
    }
    
    try {
        const response = await fetchData(`${API_BASE}/produtos-fiscais/${produtoId}/homologar`, {
            method: 'POST',
            body: JSON.stringify({ justificativa: justificativa.trim() })
        });
        
        if (response.success) {
            showAlert('Produto homologado com sucesso!', 'success');
            closeModal('homologarProdutoModal');
            
            // Recarregar dados
            if (currentSection === 'produtos-fiscais') {
                const produtosResponse = await fetchData(`${API_BASE}/produtos-fiscais`);
                renderProdutosFiscais(produtosResponse.data || []);
                
                // Atualizar lista de não homologados
                await carregarProdutosNaoHomologados();
            }
        } else {
            showAlert(response.message || 'Erro ao homologar produto', 'danger');
        }
        
    } catch (error) {
        showAlert('Erro ao homologar produto', 'danger');
    }
}


// ============================================
// FUNÇÕES PARA TRANSPORTADORAS
// ============================================
function renderTransportadoras(transportadoras) {
    const section = document.getElementById('transportadoras');
    if (!section) return;
    
    let html = `
        <div class="tabs">
            <button class="tab active" data-tab="transp-list">Listar Transportadoras</button>
        </div>
        
        <div class="tab-content" id="transp-list" style="display: block;">
    `;
    
    if (!transportadoras || transportadoras.length === 0) {
        html += `
            <div class="empty-state">
                <i class="fas fa-truck"></i>
                <h3>Nenhuma transportadora encontrada</h3>
                <p>Clique em "Nova Transportadora" para começar</p>
                <button class="btn btn-primary mt-2" onclick="showCreateTransportadoraForm()">
                    <i class="fas fa-plus"></i> Nova Transportadora
                </button>
            </div>
        `;
    } else {
        html += `
            <div class="table-container">
                <div class="table-header">
                    <h3 class="table-title">Transportadoras</h3>
                    <div class="table-actions">
                        <button class="btn btn-primary" onclick="showCreateTransportadoraForm()">
                            <i class="fas fa-plus"></i> Nova Transportadora
                        </button>
                    </div>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Razão Social</th>
                            <th>Nome Fantasia</th>
                            <th>CNPJ/CPF</th>
                            <th>Município/UF</th>
                            <th>Status</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        transportadoras.forEach(transp => {
            // Formatar documento
            let documento = '';
            if (transp.cnpj) {
                documento = formatCNPJ(transp.cnpj);
            } else if (transp.cpf) {
                documento = formatCPF(transp.cpf);
            }
            
            html += `
                <tr>
                    <td>${transp.id}</td>
                    <td>${transp.razao_social || '-'}</td>
                    <td>${transp.nome_fantasia || '-'}</td>
                    <td>${documento || '-'}</td>
                    <td>${transp.municipio || ''}${transp.uf ? '/' + transp.uf : ''}</td>
                    <td>
                        <span class="status-badge ${transp.ativo ? 'status-ativo' : 'status-inativo'}">
                            ${transp.ativo ? 'Ativa' : 'Inativa'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="editTransportadora(${transp.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteTransportadora(${transp.id})">
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
    }
    
    html += `</div>`;
    section.innerHTML = html;
}

// Mostrar formulário de criação de transportadora
function showCreateTransportadoraForm() {
    const modal = document.getElementById('createTransportadoraModal');
    modal.querySelector('.modal-body').innerHTML = getTransportadoraForm();
    modal.classList.add('active');
}

// Obter formulário de transportadora
function getTransportadoraForm(transportadora = {}) {
    return `
        <form id="transportadoraForm" onsubmit="handleTransportadoraSubmit(event, ${transportadora.id || ''})">
            <div class="form-grid">
                <div class="form-group">
                    <label class="form-label" for="razao_social">Razão Social *</label>
                    <input type="text" id="razao_social" name="razao_social" class="form-input" 
                           value="${transportadora.razao_social || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="nome_fantasia">Nome Fantasia</label>
                    <input type="text" id="nome_fantasia" name="nome_fantasia" class="form-input" 
                           value="${transportadora.nome_fantasia || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="cnpj">CNPJ</label>
                    <input type="text" id="cnpj" name="cnpj" class="form-input" 
                           value="${transportadora.cnpj ? formatCNPJ(transportadora.cnpj) : ''}"
                           placeholder="00.000.000/0000-00">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="cpf">CPF</label>
                    <input type="text" id="cpf" name="cpf" class="form-input" 
                           value="${transportadora.cpf ? formatCPF(transportadora.cpf) : ''}"
                           placeholder="000.000.000-00">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="inscricao_estadual">Inscrição Estadual</label>
                    <input type="text" id="inscricao_estadual" name="inscricao_estadual" class="form-input" 
                           value="${transportadora.inscricao_estadual || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="modalidade_frete">Modalidade de Frete</label>
                    <select id="modalidade_frete" name="modalidade_frete" class="form-input form-select">
                        <option value="0" ${transportadora.modalidade_frete === '0' ? 'selected' : ''}>Por conta do emitente</option>
                        <option value="1" ${transportadora.modalidade_frete === '1' ? 'selected' : ''}>Por conta do destinatário</option>
                        <option value="2" ${transportadora.modalidade_frete === '2' ? 'selected' : ''}>Por conta de terceiros</option>
                        <option value="3" ${transportadora.modalidade_frete === '3' ? 'selected' : ''}>Próprio por conta do remetente</option>
                        <option value="4" ${transportadora.modalidade_frete === '4' ? 'selected' : ''}>Próprio por conta do destinatário</option>
                        <option value="9" ${transportadora.modalidade_frete === '9' ? 'selected' : ''}>Sem frete</option>
                    </select>
                </div>
                
                <div class="form-group full-width">
                    <h4>Endereço</h4>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="logradouro">Logradouro</label>
                    <input type="text" id="logradouro" name="logradouro" class="form-input" 
                           value="${transportadora.logradouro || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="numero">Número</label>
                    <input type="text" id="numero" name="numero" class="form-input" 
                           value="${transportadora.numero || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="complemento">Complemento</label>
                    <input type="text" id="complemento" name="complemento" class="form-input" 
                           value="${transportadora.complemento || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="bairro">Bairro</label>
                    <input type="text" id="bairro" name="bairro" class="form-input" 
                           value="${transportadora.bairro || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="municipio">Município</label>
                    <input type="text" id="municipio" name="municipio" class="form-input" 
                           value="${transportadora.municipio || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="uf">UF</label>
                    <input type="text" id="uf" name="uf" class="form-input" 
                           value="${transportadora.uf || ''}" maxlength="2" placeholder="SP">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="cep">CEP</label>
                    <input type="text" id="cep" name="cep" class="form-input" 
                           value="${transportadora.cep ? formatCEP(transportadora.cep) : ''}"
                           placeholder="00000-000">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="telefone">Telefone</label>
                    <input type="text" id="telefone" name="telefone" class="form-input" 
                           value="${transportadora.telefone || ''}" placeholder="(00) 0000-0000">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="email">Email</label>
                    <input type="email" id="email" name="email" class="form-input" 
                           value="${transportadora.email || ''}">
                </div>
                
                <div class="form-group full-width">
                    <h4>Veículo Principal</h4>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="placa_veiculo">Placa do Veículo</label>
                    <input type="text" id="placa_veiculo" name="placa_veiculo" class="form-input" 
                           value="${transportadora.placa_veiculo || ''}" placeholder="ABC1234">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="uf_veiculo">UF do Veículo</label>
                    <input type="text" id="uf_veiculo" name="uf_veiculo" class="form-input" 
                           value="${transportadora.uf_veiculo || ''}" maxlength="2" placeholder="SP">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="rntc">RNTC</label>
                    <input type="text" id="rntc" name="rntc" class="form-input" 
                           value="${transportadora.rntc || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="ativo">Status</label>
                    <select id="ativo" name="ativo" class="form-input form-select" required>
                        <option value="true" ${transportadora.ativo !== false ? 'selected' : ''}>Ativa</option>
                        <option value="false" ${transportadora.ativo === false ? 'selected' : ''}>Inativa</option>
                    </select>
                </div>
                
                <div class="form-group full-width">
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="closeModal('createTransportadoraModal')">
                            Cancelar
                        </button>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> ${transportadora.id ? 'Atualizar' : 'Salvar'} Transportadora
                        </button>
                    </div>
                </div>
            </div>
        </form>
    `;
}

// Manipular envio do formulário de transportadora
async function handleTransportadoraSubmit(event, id = null) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Remover formatação de CNPJ/CPF/CEP
    if (data.cnpj) {
        data.cnpj = data.cnpj.replace(/\D/g, '');
    }
    if (data.cpf) {
        data.cpf = data.cpf.replace(/\D/g, '');
    }
    if (data.cep) {
        data.cep = data.cep.replace(/\D/g, '');
    }
    if (data.telefone) {
        data.telefone = data.telefone.replace(/\D/g, '');
    }
    
    // Converter string para boolean
    data.ativo = data.ativo === 'true';
    
    // Converter string vazia para null
    Object.keys(data).forEach(key => {
        if (data[key] === '') {
            data[key] = null;
        }
    });
    
    try {
        let response;
        if (id) {
            // Atualização
            response = await fetchData(`${API_BASE}/transportadoras/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            showAlert('Transportadora atualizada com sucesso!', 'success');
        } else {
            // Criação
            response = await fetchData(`${API_BASE}/transportadoras`, {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showAlert('Transportadora criada com sucesso!', 'success');
        }
        
        closeModal('createTransportadoraModal');
        loadSectionData(currentSection);
    } catch (error) {
        showAlert(id ? 'Erro ao atualizar transportadora' : 'Erro ao criar transportadora', 'danger');
    }
}

// Editar transportadora
async function editTransportadora(id) {
    try {
        const response = await fetchData(`${API_BASE}/transportadoras/${id}`);
        const transportadora = response.data;
        
        // Formatar campos para exibição
        const transportadoraFormatada = {
            ...transportadora,
            cnpj: transportadora.cnpj ? formatCNPJ(transportadora.cnpj) : '',
            cpf: transportadora.cpf ? formatCPF(transportadora.cpf) : '',
            cep: transportadora.cep ? formatCEP(transportadora.cep) : '',
            telefone: transportadora.telefone ? formatTelefone(transportadora.telefone) : ''
        };
        
        const modal = document.getElementById('createTransportadoraModal');
        modal.querySelector('.modal-title').textContent = 'Editar Transportadora';
        modal.querySelector('.modal-body').innerHTML = getTransportadoraForm(transportadoraFormatada);
        
        modal.classList.add('active');
    } catch (error) {
        showAlert('Erro ao carregar transportadora', 'danger');
    }
}

// Excluir transportadora
async function deleteTransportadora(id) {
    if (!confirm('Tem certeza que deseja desativar esta transportadora?')) {
        return;
    }
    
    try {
        await fetchData(`${API_BASE}/transportadoras/${id}`, {
            method: 'DELETE'
        });
        
        showAlert('Transportadora desativada com sucesso!', 'success');
        loadSectionData(currentSection);
    } catch (error) {
        showAlert('Erro ao desativar transportadora', 'danger');
    }
}

// Buscar transportadoras por nome
async function buscarTransportadoras() {
    try {
        const nome = document.getElementById('buscar-transportadora').value;
        if (!nome) {
            showAlert('Digite um nome para buscar', 'warning');
            return;
        }
        
        const response = await fetchData(`${API_BASE}/transportadoras/buscar?nome=${encodeURIComponent(nome)}`);
        const transportadoras = response.data || [];
        
        const container = document.getElementById('resultados-busca-transp');
        
        if (!transportadoras.length) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    Nenhuma transportadora encontrada para "${nome}"
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="table-container">
                <h4>Resultados da busca</h4>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Razão Social</th>
                            <th>Nome Fantasia</th>
                            <th>CNPJ/CPF</th>
                            <th>Município/UF</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        transportadoras.forEach(transp => {
            let documento = '';
            if (transp.cnpj) {
                documento = formatCNPJ(transp.cnpj);
            } else if (transp.cpf) {
                documento = formatCPF(transp.cpf);
            }
            
            html += `
                <tr>
                    <td>${transp.id}</td>
                    <td>${transp.razao_social}</td>
                    <td>${transp.nome_fantasia || '-'}</td>
                    <td>${documento}</td>
                    <td>${transp.municipio || ''}${transp.uf ? '/' + transp.uf : ''}</td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="editTransportadora(${transp.id})">
                            <i class="fas fa-edit"></i> Editar
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
        
    } catch (error) {
        showAlert('Erro ao buscar transportadoras', 'danger');
    }
}

// Carregar transportadoras para select
async function carregarTransportadorasParaSelect(selectId) {
    try {
        const response = await fetchData(`${API_BASE}/transportadoras?limit=100`);
        const transportadoras = response.data || [];
        
        const select = document.getElementById(selectId);
        if (select) {
            // Limpar opções existentes (exceto a primeira)
            while (select.options.length > 1) {
                select.remove(1);
            }
            
            // Adicionar novas opções
            transportadoras.forEach(transp => {
                const option = document.createElement('option');
                option.value = transp.id;
                
                let documento = '';
                if (transp.cnpj) {
                    documento = formatCNPJ(transp.cnpj);
                } else if (transp.cpf) {
                    documento = formatCPF(transp.cpf);
                }
                
                option.textContent = `${transp.razao_social} ${documento ? `(${documento})` : ''}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar transportadoras:', error);
    }
}

// Carregar veículos por transportadora
async function carregarVeiculosPorTransportadora() {
    try {
        const transportadoraId = document.getElementById('select-transportadora-veiculos').value;
        
        if (!transportadoraId) {
            document.getElementById('lista-veiculos-transp').innerHTML = '';
            return;
        }
        
        const response = await fetchData(`${API_BASE}/veiculos/transportadora/${transportadoraId}`);
        const veiculos = response.data || [];
        
        const container = document.getElementById('lista-veiculos-transp');
        
        if (!veiculos.length) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    Nenhum veículo encontrado para esta transportadora
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="table-container">
                <h4>Veículos da Transportadora</h4>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Placa</th>
                            <th>UF</th>
                            <th>RNTC</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        veiculos.forEach(veiculo => {
            html += `
                <tr>
                    <td>${veiculo.id}</td>
                    <td>${formatPlaca(veiculo.placa)}</td>
                    <td>${veiculo.uf}</td>
                    <td>${veiculo.rntc || '-'}</td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="editVeiculo(${veiculo.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteVeiculo(${veiculo.id})">
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
        
    } catch (error) {
        showAlert('Erro ao carregar veículos da transportadora', 'danger');
    }
}

// Funções auxiliares de formatação
function formatTelefone(telefone) {
    if (!telefone) return '';
    const cleaned = telefone.replace(/\D/g, '');
    
    if (cleaned.length === 10) {
        return cleaned.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    } else if (cleaned.length === 11) {
        return cleaned.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    }
    
    return telefone;
}

function formatCEP(cep) {
    if (!cep) return '';
    const cleaned = cep.replace(/\D/g, '');
    if (cleaned.length === 8) {
        return cleaned.replace(/(\d{5})(\d{3})/, '$1-$2');
    }
    return cep;
}



// Renderizar veículos
function renderVeiculos(veiculos) {
    const section = document.getElementById('veiculos');
    if (!section) return;
    
    let html = `
        <div class="tabs">
            <button class="tab active" data-tab="veiculos-list">Listar Veículos</button>
        </div>
        
        <div class="tab-content" id="veiculos-list" style="display: block;">
    `;
    
    if (!veiculos || veiculos.length === 0) {
        html += `
            <div class="empty-state">
                <i class="fas fa-bus"></i>
                <h3>Nenhum veículo encontrado</h3>
                <p>Clique em "Novo Veículo" para começar</p>
                <button class="btn btn-primary mt-2" onclick="showCreateVeiculoForm()">
                    <i class="fas fa-plus"></i> Novo Veículo
                </button>
            </div>
        `;
    } else {
        html += `
            <div class="table-container">
                <div class="table-header">
                    <h3 class="table-title">Veículos de Transporte</h3>
                    <div class="table-actions">
                        <button class="btn btn-primary" onclick="showCreateVeiculoForm()">
                            <i class="fas fa-plus"></i> Novo Veículo
                        </button>
                    </div>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Placa</th>
                            <th>UF</th>
                            <th>Transportadora</th>
                            <th>Proprietário</th>
                            <th>Status</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        veiculos.forEach(veiculo => {
            html += `
                <tr>
                    <td>${veiculo.id}</td>
                    <td>${formatPlaca(veiculo.placa)}</td>
                    <td>${veiculo.uf}</td>
                    <td>${veiculo.transportadora_nome ? `${veiculo.transportadora_nome}` : 'Não vinculada'}</td>
                    <td>${veiculo.proprietario || '-'}</td>
                    <td>
                        <span class="status-badge ${veiculo.ativo === true  ? 'status-ativo' : 'status-inativo'}">
                            ${veiculo.ativo === true ? 'Ativo' : 'Inativo'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="editVeiculo(${veiculo.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteVeiculo(${veiculo.id})">
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
    }
    
    html += `</div>`;
    section.innerHTML = html;
}

// Formatar placa
function formatPlaca(placa) {
    if (!placa) return '';
    // Formato: ABC-1234
    const placaFormatada = placa.replace(/([A-Za-z]{3})([0-9]{1}[A-Za-z]{1}[0-9]{2})/i, '$1-$2');
    return placaFormatada.toUpperCase();
}

// Mostrar formulário de criação de veículo
async function showCreateVeiculoForm() {
    const modal = createModal('createVeiculoModal', 'Novo Veículo', getVeiculoForm());
    
    await loadTransportadorasParaSelect();
    
    modal.classList.add('active');
}

// Obter formulário de veículo
function getVeiculoForm(veiculo = {}) {
    // Mapear os tipos de veículo para tornar mais fácil a lógica
    const tiposVeiculo = [
        { value: '', label: 'Selecione' },
        { value: 'Caminhao', label: 'Caminhão' },
        { value: 'Carreta', label: 'Carreta' },
        { value: 'Bitrem', label: 'Bitrem' },
        { value: 'VUC', label: 'VUC' },
        { value: 'Toco', label: 'Toco' },
        { value: 'Truck', label: 'Truck' },
        { value: 'Rodotrem', label: 'Rodotrem' },
        { value: 'CavaloMecanico', label: 'Cavalo Mecânico' },
        { value: 'Furgao', label: 'Furgão' },
        { value: 'Van', label: 'Van' },
        { value: 'Carroceria', label: 'Carroceria' }
    ];
    
    // Gerar options para tipo de veículo
    const tipoVeiculoOptions = tiposVeiculo.map(tipo => 
        `<option value="${tipo.value}" ${veiculo.tipo_veiculo === tipo.value ? 'selected' : ''}>
            ${tipo.label}
        </option>`
    ).join('');
    
    return `
        <form id="veiculoForm" onsubmit="handleVeiculoSubmit(event, ${veiculo.id || ''})">
            <div class="form-grid">
                <div class="form-group">
                    <label class="form-label" for="placa">Placa *</label>
                    <input type="text" id="placa" name="placa" class="form-input" 
                           value="${veiculo.placa || ''}" required
                           placeholder="ABC1234 ou ABC1D23"
                           oninput="this.value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, '')"
                           maxlength="7">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="uf">UF *</label>
                    <select id="uf" name="uf" class="form-input form-select" required>
                        <option value="">Selecione</option>
                        ${getUFOptions(veiculo.uf)}
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="transportadora_id">Transportadora</label>
                    <select id="transportadora_id" name="transportadora_id" class="form-input form-select">
                        <option value="">Selecione uma transportadora</option>
                        <!-- As transportadoras serão carregadas via JavaScript -->
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="rntc">RNTC</label>
                    <input type="text" id="rntc" name="rntc" class="form-input" 
                           value="${veiculo.rntc || ''}" placeholder="Registro Nacional de Transportador">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="tipo_veiculo">Tipo de Veículo</label>
                    <select id="tipo_veiculo" name="tipo_veiculo" class="form-input form-select">
                        ${tipoVeiculoOptions}
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="capacidade_carga">Capacidade de Carga (kg)</label>
                    <input type="number" id="capacidade_carga" name="capacidade_carga" class="form-input" 
                           value="${veiculo.capacidade_carga || ''}" step="0.01" min="0"
                           placeholder="Ex: 15000.00">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="proprietario">Proprietário</label>
                    <input type="text" id="proprietario" name="proprietario" class="form-input" 
                           value="${veiculo.proprietario || ''}" placeholder="Nome do proprietário">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="ativo">Status</label>
                    <select id="ativo" name="ativo" class="form-input form-select" required>
                        <option value="true" ${veiculo.ativo !== false ? 'selected' : ''}>Ativo</option>
                        <option value="false" ${veiculo.ativo === false ? 'selected' : ''}>Inativo</option>
                    </select>
                </div>
                
                <div class="form-group full-width">
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="closeModal('createVeiculoModal')">
                            Cancelar
                        </button>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> ${veiculo.id ? 'Atualizar' : 'Salvar'} Veículo
                        </button>
                    </div>
                </div>
            </div>
        </form>
    `;
}

// Função auxiliar para gerar opções de UF
function getUFOptions(selectedUF = '') {
    const ufs = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
        'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
        'SP', 'SE', 'TO'
    ];
    
    return ufs.map(uf => 
        `<option value="${uf}" ${selectedUF === uf ? 'selected' : ''}>${uf}</option>`
    ).join('');
}
// Manipular envio do formulário de veículo
async function handleVeiculoSubmit(event, id = null) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Converter string para boolean
    data.ativo = data.ativo === 'true';
    
    // Converter string vazia para null
    Object.keys(data).forEach(key => {
        if (data[key] === '') {
            data[key] = null;
        }
    });
    
    try {
        let response;
        if (id) {
            // Atualização
            response = await fetchData(`${API_BASE}/veiculos/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            showAlert('Veículo atualizado com sucesso!', 'success');
        } else {
            // Criação
            response = await fetchData(`${API_BASE}/veiculos`, {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showAlert('Veículo criado com sucesso!', 'success');
        }
        
        closeModal('createVeiculoModal');
        loadSectionData(currentSection);
    } catch (error) {
        showAlert(id ? 'Erro ao atualizar veículo' : 'Erro ao criar veículo', 'danger');
    }
}

// Editar veículo
async function editVeiculo(id) {
    try {
        const response = await fetchData(`${API_BASE}/veiculos/${id}`);
        const veiculo = response.data;
        
        if (veiculo.placa) {
            veiculo.placa = veiculo.placa.replace(/[^A-Z0-9]/gi, '');
        }
        
        const modal = createModal('createVeiculoModal', 'Editar Veículo', getVeiculoForm(veiculo));
        
        await loadTransportadorasParaSelect(veiculo.transportadora_id);
        
        const tipoVeiculoSelect = document.getElementById('tipo_veiculo');
        if (tipoVeiculoSelect && veiculo.tipo_veiculo) {
            tipoVeiculoSelect.value = veiculo.tipo_veiculo;
        }
        
        modal.classList.add('active');
    } catch (error) {
        showAlert('Erro ao carregar veículo', 'danger');
    }
}

// Carregar transportadoras para select
async function loadTransportadorasParaSelect(selectedId = null) {
    try {
        const response = await fetchData(`${API_BASE}/transportadoras?limit=100`);
        const transportadoras = response.data || [];
        
        const select = document.getElementById('transportadora_id');
        if (select) {
            while (select.options.length > 1) {
                select.remove(1);
            }
            
            transportadoras.forEach(transp => {
                const option = document.createElement('option');
                option.value = transp.id;
                option.textContent = `${transp.razao_social} (${transp.cnpj || transp.cpf || 'N/D'})`;
                select.appendChild(option);
            });
            
            if (selectedId) {
                select.value = selectedId;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar transportadoras:', error);
    }
}

// Excluir veículo
async function deleteVeiculo(id) {
    if (!confirm('Tem certeza que deseja desativar este veículo?')) {
        return;
    }
    
    try {
        await fetchData(`${API_BASE}/veiculos/${id}`, {
            method: 'DELETE'
        });
        
        showAlert('Veículo desativado com sucesso!', 'success');
        loadSectionData(currentSection);
    } catch (error) {
        showAlert('Erro ao desativar veículo', 'danger');
    }
}

// Criar modal dinamicamente
function createModal(id, title, content) {
    let modal = document.getElementById(id);
    
    if (!modal) {
        modal = document.createElement('div');
        modal.id = id;
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3 class="modal-title">${title}</h3>
                    <button class="modal-close" onclick="closeModal('${id}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Adicionar evento para fechar ao clicar fora
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    } else {
        modal.querySelector('.modal-title').textContent = title;
        modal.querySelector('.modal-body').innerHTML = content;
    }
    
    return modal;
}

// ============================================
// FUNÇÕES PARA CLIENTES FISCAIS
// ============================================

// Configurar tabs de clientes fiscais
function setupClientesFiscaisTabs() {
    const tabs = document.querySelectorAll('#clientes-fiscais .tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', async () => {
            const tabId = tab.getAttribute('data-tab');
            
            // Atualizar tabs ativas
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Mostrar conteúdo da tab
            document.querySelectorAll('#clientes-fiscais .tab-content').forEach(content => {
                content.style.display = 'none';
            });
            document.getElementById(tabId).style.display = 'block';
            
            // Carregar dados específicos da tab
            switch(tabId) {
                case 'clientes-estatisticas':
                    await carregarEstatisticasClientes();
                    break;
                case 'clientes-nao-sincronizados':
                    await carregarClientesNaoSincronizados();
                    break;
            }
        });
    });
}

// Renderizar lista de clientes fiscais
function renderClientesFiscais(clientes) {
    const container = document.getElementById('clientes-list');
    
    if (!clientes || clientes.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <h3>Nenhum cliente fiscal encontrado</h3>
                <p>Clique em "Novo Cliente Fiscal" para começar</p>
                <button class="btn btn-primary mt-2" onclick="showCreateClienteFiscalForm()">
                    <i class="fas fa-plus"></i> Novo Cliente Fiscal
                </button>
            </div>
        `;
        return;
    }

    let html = `
        <div class="table-container">
            <div class="table-header">
                <h3 class="table-title">Clientes Fiscais</h3>
                <div class="table-actions">
                    <button class="btn btn-primary" onclick="showCreateClienteFiscalForm()">
                        <i class="fas fa-plus"></i> Novo Cliente Fiscal
                    </button>
                </div>
            </div>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nome</th>
                            <th>CPF/CNPJ</th>
                            <th>Tipo</th>
                            <th>Município/UF</th>
                            <th>Telefone</th>
                            <th>Status</th>
                            <th>Sincronizado</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    clientes.forEach(cliente => {
        // Formatar CPF/CNPJ
        let documento = cliente.cpf_cnpj || '';
        if (documento.length === 11) {
            documento = formatCPF(documento);
        } else if (documento.length === 14) {
            documento = formatCNPJ(documento);
        }
        
        // Formatar tipo
        const tipo = cliente.tipo_cliente === 'fisica' ? 'Pessoa Física' : 'Pessoa Jurídica';
        
        // Formatar sincronizado
        const sincronizadoStatus = cliente.sincronizado ? 'Sim' : 'Não';
        const sincronizadoClass = cliente.sincronizado ? 'status-ativo' : 'status-inativo';

        html += `
            <tr>
                <td>${cliente.id}</td>
                <td>${cliente.nome_cliente}</td>
                <td>${documento}</td>
                <td>${tipo}</td>
                <td>${cliente.municipio || ''}${cliente.uf ? '/' + cliente.uf : ''}</td>
                <td>${cliente.telefone ? formatTelefone(cliente.telefone) : '-'}</td>
                <td>
                    <span class="status-badge ${cliente.ativo ? 'status-ativo' : 'status-inativo'}">
                        ${cliente.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                </td>
                <td>
                    <span class="status-badge ${sincronizadoClass}">
                        ${sincronizadoStatus}
                    </span>
                </td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-secondary btn-sm" onclick="editClienteFiscal(${cliente.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        ${!cliente.sincronizado ? `
                            <button class="btn btn-success btn-sm" onclick="marcarClienteSincronizado(${cliente.id})">
                                <i class="fas fa-sync"></i>
                            </button>
                        ` : ''}
                        <button class="btn btn-danger btn-sm" onclick="deleteClienteFiscal(${cliente.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// Mostrar formulário de criação de cliente fiscal
function showCreateClienteFiscalForm() {
    const modal = document.getElementById('createClienteFiscalModal');
    modal.querySelector('.modal-body').innerHTML = getClienteFiscalForm();
    modal.classList.add('active');
}

// Obter formulário de cliente fiscal
function getClienteFiscalForm(cliente = {}) {
    const isEdit = !!cliente.id;
    
    return `
        <form id="clienteFiscalForm" onsubmit="handleClienteFiscalSubmit(event, ${cliente.id || ''})">
            <div class="form-grid">
                <div class="form-group full-width">
                    <h4>Identificação</h4>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="cpf_cnpj">CPF/CNPJ *</label>
                    <input type="text" id="cpf_cnpj" name="cpf_cnpj" class="form-input" 
                           value="${cliente.cpf_cnpj || ''}" required
                           oninput="formatarDocumento(this)"
                           placeholder="Digite CPF ou CNPJ">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="nome_cliente">Nome Completo/Razão Social *</label>
                    <input type="text" id="nome_cliente" name="nome_cliente" class="form-input" 
                           value="${cliente.nome_cliente || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="nome_fantasia">Nome Fantasia</label>
                    <input type="text" id="nome_fantasia" name="nome_fantasia" class="form-input" 
                           value="${cliente.nome_fantasia || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="tipo_cliente">Tipo de Cliente *</label>
                    <select id="tipo_cliente" name="tipo_cliente" class="form-input form-select" required>
                        <option value="">Selecione</option>
                        <option value="fisica" ${cliente.tipo_cliente === 'fisica' ? 'selected' : ''}>Pessoa Física</option>
                        <option value="juridica" ${cliente.tipo_cliente === 'juridica' ? 'selected' : ''}>Pessoa Jurídica</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="regime_tributario">Regime Tributário *</label>
                    <select id="regime_tributario" name="regime_tributario" class="form-input form-select" required>
                        <option value="">Selecione</option>
                        <option value="1" ${cliente.regime_tributario === '1' ? 'selected' : ''}>Simples Nacional</option>
                        <option value="2" ${cliente.regime_tributario === '2' ? 'selected' : ''}>Normal (Lucro Presumido/Real)</option>
                        <option value="3" ${cliente.regime_tributario === '3' ? 'selected' : ''}>MEI</option>
                    </select>
                </div>
                
                <div class="form-group full-width">
                    <h4>Dados Fiscais</h4>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="indicador_ie">Indicador IE *</label>
                    <select id="indicador_ie" name="indicador_ie" class="form-input form-select" required>
                        <option value="">Selecione</option>
                        <option value="1" ${cliente.indicador_ie === 1 ? 'selected' : ''}>Contribuinte ICMS</option>
                        <option value="2" ${cliente.indicador_ie === 2 ? 'selected' : ''}>Isento de Inscrição</option>
                        <option value="9" ${cliente.indicador_ie === 9 ? 'selected' : ''}>Não Contribuinte</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="inscricao_estadual">Inscrição Estadual</label>
                    <input type="text" id="inscricao_estadual" name="inscricao_estadual" class="form-input" 
                           value="${cliente.inscricao_estadual || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="inscricao_municipal">Inscrição Municipal *</label>
                    <input type="text" id="inscricao_municipal" name="inscricao_municipal" class="form-input" 
                           value="${cliente.inscricao_municipal || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="inscricao_suframa">Inscrição SUFRAMA *</label>
                    <input type="text" id="inscricao_suframa" name="inscricao_suframa" class="form-input" 
                           value="${cliente.inscricao_suframa || ''}" required>
                </div>
                
                <div class="form-group full-width">
                    <h4>Endereço</h4>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="cep">CEP *</label>
                    <input type="text" id="cep" name="cep" class="form-input" 
                           value="${cliente.endereco?.cep || cliente.cep || ''}" required
                           oninput="formatarCEP(this)"
                           placeholder="00000-000">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="logradouro">Logradouro *</label>
                    <input type="text" id="logradouro" name="logradouro" class="form-input" 
                           value="${cliente.endereco?.logradouro || cliente.logradouro || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="numero">Número *</label>
                    <input type="text" id="numero" name="numero" class="form-input" 
                           value="${cliente.endereco?.numero || cliente.numero || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="complemento">Complemento</label>
                    <input type="text" id="complemento" name="complemento" class="form-input" 
                           value="${cliente.endereco?.complemento || cliente.complemento || ''}">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="bairro">Bairro *</label>
                    <input type="text" id="bairro" name="bairro" class="form-input" 
                           value="${cliente.endereco?.bairro || cliente.bairro || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="municipio">Município *</label>
                    <input type="text" id="municipio" name="municipio" class="form-input" 
                           value="${cliente.endereco?.municipio || cliente.municipio || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="codigo_municipio">Código do Município (IBGE) *</label>
                    <input type="text" id="codigo_municipio" name="codigo_municipio" class="form-input" 
                           value="${cliente.endereco?.codigo_municipio || cliente.codigo_municipio || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="uf">UF *</label>
                    <select id="uf" name="uf" class="form-input form-select" required>
                        <option value="">Selecione</option>
                        ${getUFOptions(cliente.endereco?.uf || cliente.uf || '')}
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="codigo_pais">Código País *</label>
                    <input type="number" id="codigo_pais" name="codigo_pais" class="form-input" 
                           value="${cliente.endereco?.codigo_pais || cliente.codigo_pais || '1058'}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="pais">País *</label>
                    <input type="text" id="pais" name="pais" class="form-input" 
                           value="${cliente.endereco?.pais || cliente.pais || 'BRASIL'}" required>
                </div>
                
                <div class="form-group full-width">
                    <h4>Contato</h4>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="telefone">Telefone *</label>
                    <input type="text" id="telefone" name="telefone" class="form-input" 
                           value="${cliente.contato?.telefone || cliente.telefone || ''}" required
                           oninput="formatarTelefone(this)">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="celular">Celular *</label>
                    <input type="text" id="celular" name="celular" class="form-input" 
                           value="${cliente.contato?.celular || cliente.celular || ''}" required
                           oninput="formatarTelefone(this)">
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="email">Email *</label>
                    <input type="email" id="email" name="email" class="form-input" 
                           value="${cliente.contato?.email || cliente.email || ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="fax">Fax</label>
                    <input type="text" id="fax" name="fax" class="form-input" 
                           value="${cliente.contato?.fax || cliente.fax || ''}">
                </div>
                
                <div class="form-group full-width">
                    <h4>Informações Adicionais</h4>
                </div>
                
                <div class="form-group full-width">
                    <label class="form-label" for="observacoes">Observações</label>
                    <textarea id="observacoes" name="observacoes" class="form-input" rows="3"
                              placeholder="Informações adicionais sobre o cliente...">${cliente.observacoes || ''}</textarea>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="ativo">Status</label>
                    <select id="ativo" name="ativo" class="form-input form-select">
                        <option value="true" ${cliente.ativo !== false ? 'selected' : ''}>Ativo</option>
                        <option value="false" ${cliente.ativo === false ? 'selected' : ''}>Inativo</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="sincronizado">Sincronizado</label>
                    <select id="sincronizado" name="sincronizado" class="form-input form-select">
                        <option value="false" ${!cliente.sincronizado ? 'selected' : ''}>Não Sincronizado</option>
                        <option value="true" ${cliente.sincronizado ? 'selected' : ''}>Sincronizado</option>
                    </select>
                </div>
                
                <div class="form-group full-width">
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="closeModal('createClienteFiscalModal')">
                            Cancelar
                        </button>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> ${isEdit ? 'Atualizar' : 'Salvar'} Cliente
                        </button>
                    </div>
                </div>
            </div>
        </form>
    `;
}

// Funções auxiliares para formatação
function formatarDocumento(input) {
    let valor = input.value.replace(/\D/g, '');
    
    if (valor.length <= 11) {
        // Formata CPF
        input.value = valor.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    } else {
        // Formata CNPJ
        input.value = valor.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
}

function formatarCEP(input) {
    let valor = input.value.replace(/\D/g, '');
    if (valor.length > 5) {
        input.value = valor.replace(/(\d{5})(\d{3})/, '$1-$2');
    }
}

function formatarTelefone(input) {
    let valor = input.value.replace(/\D/g, '');
    
    if (valor.length === 10) {
        input.value = valor.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    } else if (valor.length === 11) {
        input.value = valor.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    }
}

// Manipular envio do formulário de cliente fiscal
async function handleClienteFiscalSubmit(event, id = null) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Remover formatação dos campos
    data.cpf_cnpj = data.cpf_cnpj.replace(/\D/g, '');
    data.cep = data.cep.replace(/\D/g, '');
    data.telefone = data.telefone.replace(/\D/g, '');
    data.celular = data.celular.replace(/\D/g, '');
    data.fax = data.fax ? data.fax.replace(/\D/g, '') : '';
    
    // Converter string para boolean e number
    data.ativo = data.ativo === 'true';
    data.sincronizado = data.sincronizado === 'true';
    data.indicador_ie = parseInt(data.indicador_ie);
    data.codigo_pais = parseInt(data.codigo_pais);
    
    // Converter string vazia para null
    Object.keys(data).forEach(key => {
        if (data[key] === '') {
            data[key] = null;
        }
    });
    
    try {
        let response;
        if (id) {
            // Atualização
            response = await fetchData(`${API_BASE}/clientes-fiscais/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            showAlert('Cliente fiscal atualizado com sucesso!', 'success');
        } else {
            // Criação
            response = await fetchData(`${API_BASE}/clientes-fiscais`, {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showAlert('Cliente fiscal criado com sucesso!', 'success');
        }
        
        closeModal('createClienteFiscalModal');
        loadSectionData(currentSection);
    } catch (error) {
        showAlert(id ? 'Erro ao atualizar cliente fiscal' : 'Erro ao criar cliente fiscal', 'danger');
        console.error('Erro detalhado:', error);
    }
}

// Editar cliente fiscal
async function editClienteFiscal(id) {
    try {
        const response = await fetchData(`${API_BASE}/clientes-fiscais/${id}`);
        const cliente = response.data;
        
        // Formatar campos para exibição
        if (cliente.cpf_cnpj) {
            if (cliente.cpf_cnpj.length === 11) {
                cliente.cpf_cnpj = formatCPF(cliente.cpf_cnpj);
            } else if (cliente.cpf_cnpj.length === 14) {
                cliente.cpf_cnpj = formatCNPJ(cliente.cpf_cnpj);
            }
        }
        
        if (cliente.cep) {
            cliente.cep = formatCEP(cliente.cep);
        }
        
        if (cliente.telefone) {
            cliente.telefone = formatTelefone(cliente.telefone);
        }
        
        if (cliente.celular) {
            cliente.celular = formatTelefone(cliente.celular);
        }
        
        const modal = document.getElementById('createClienteFiscalModal');
        modal.querySelector('.modal-title').textContent = 'Editar Cliente Fiscal';
        modal.querySelector('.modal-body').innerHTML = getClienteFiscalForm(cliente);
        
        modal.classList.add('active');
    } catch (error) {
        showAlert('Erro ao carregar cliente fiscal', 'danger');
    }
}

// Excluir cliente fiscal
async function deleteClienteFiscal(id) {
    if (!confirm('Tem certeza que deseja desativar este cliente fiscal?')) {
        return;
    }
    
    try {
        await fetchData(`${API_BASE}/clientes-fiscais/${id}`, {
            method: 'DELETE'
        });
        
        showAlert('Cliente fiscal desativado com sucesso!', 'success');
        loadSectionData(currentSection);
    } catch (error) {
        showAlert('Erro ao desativar cliente fiscal', 'danger');
    }
}

// Marcar cliente como sincronizado
async function marcarClienteSincronizado(id) {
    if (!confirm('Deseja marcar este cliente como sincronizado?')) {
        return;
    }
    
    try {
        await fetchData(`${API_BASE}/clientes-fiscais/${id}/marcar-sincronizado`, {
            method: 'POST'
        });
        
        showAlert('Cliente marcado como sincronizado com sucesso!', 'success');
        loadSectionData(currentSection);
    } catch (error) {
        showAlert('Erro ao marcar cliente como sincronizado', 'danger');
    }
}

// Buscar clientes fiscais
async function buscarClientesFiscais() {
    try {
        const termo = document.getElementById('buscar-cliente-fiscal').value.trim();
        
        if (!termo) {
            showAlert('Digite um termo para buscar', 'warning');
            return;
        }
        
        const response = await fetchData(`${API_BASE}/clientes-fiscais/buscar?termo=${encodeURIComponent(termo)}&limit=20`);
        const clientes = response.data || [];
        const container = document.getElementById('resultados-busca-clientes-fiscais');
        
        if (!clientes.length) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    Nenhum cliente encontrado para "${termo}"
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="table-container">
                <h4>Resultados da Busca (${clientes.length} encontrados)</h4>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Nome</th>
                                <th>CPF/CNPJ</th>
                                <th>Tipo</th>
                                <th>Município/UF</th>
                                <th>Telefone</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        clientes.forEach(cliente => {
            let documento = cliente.cpf_cnpj || '';
            if (documento.length === 11) {
                documento = formatCPF(documento);
            } else if (documento.length === 14) {
                documento = formatCNPJ(documento);
            }
            
            const tipo = cliente.tipo_cliente === 'fisica' ? 'Pessoa Física' : 'Pessoa Jurídica';
            
            html += `
                <tr>
                    <td>${cliente.id}</td>
                    <td>${cliente.nome_cliente}</td>
                    <td>${documento}</td>
                    <td>${tipo}</td>
                    <td>${cliente.endereco.municipio || ''}${cliente.endereco.uf ? '/' + cliente.endereco.uf : ''}</td>
                    <td>${cliente.contato.celular ? formatTelefone(cliente.contato.celular) : '-'}</td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="editClienteFiscal(${cliente.id})">
                            <i class="fas fa-edit"></i> Editar
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        
    } catch (error) {
        showAlert('Erro ao buscar clientes fiscais', 'danger');
    }
}

// Carregar estatísticas de clientes
async function carregarEstatisticasClientes() {
    try {
        const response = await fetchData(`${API_BASE}/clientes-fiscais/estatisticas`);
        const estatisticas = response.data;
        
        const container = document.getElementById('estatisticas-clientes');
        
        let html = `
            <div class="dashboard-grid">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Clientes Ativos</h3>
                        <div class="card-icon">
                            <i class="fas fa-user-check"></i>
                        </div>
                    </div>
                    <div class="card-content">
                        <div class="card-stat">${estatisticas.totais.ativos || 0}</div>
                        <p>Clientes ativos no sistema</p>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Clientes Inativos</h3>
                        <div class="card-icon">
                            <i class="fas fa-user-times"></i>
                        </div>
                    </div>
                    <div class="card-content">
                        <div class="card-stat">${estatisticas.totais.inativos || 0}</div>
                        <p>Clientes inativos no sistema</p>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Pessoas Físicas</h3>
                        <div class="card-icon">
                            <i class="fas fa-user"></i>
                        </div>
                    </div>
                    <div class="card-content">
                        <div class="card-stat">${estatisticas.totais.pessoas_fisicas || 0}</div>
                        <p>Clientes pessoas físicas</p>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Pessoas Jurídicas</h3>
                        <div class="card-icon">
                            <i class="fas fa-building"></i>
                        </div>
                    </div>
                    <div class="card-content">
                        <div class="card-stat">${estatisticas.totais.pessoas_juridicas || 0}</div>
                        <p>Clientes pessoas jurídicas</p>
                    </div>
                </div>
            </div>
            
            <div class="table-container mt-4">
                <h3>Distribuição por UF</h3>
                <table>
                    <thead>
                        <tr>
                            <th>UF</th>
                            <th>Total de Clientes</th>
                            <th>Percentual</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        const totalGeral = estatisticas.totais.ativos + estatisticas.totais.inativos;
        
        estatisticas.por_uf.forEach(item => {
            const percentual = totalGeral > 0 ? ((item.total / totalGeral) * 100).toFixed(1) : 0;
            
            html += `
                <tr>
                    <td>${item.uf}</td>
                    <td>${item.total}</td>
                    <td>${percentual}%</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = html;
        
    } catch (error) {
        showAlert('Erro ao carregar estatísticas de clientes', 'danger');
    }
}

// Carregar clientes não sincronizados
async function carregarClientesNaoSincronizados() {
    try {
        const response = await fetchData(`${API_BASE}/clientes-fiscais/listar-nao-sincronizados`);
        const clientes = response.data || [];
        
        const container = document.getElementById('lista-clientes-nao-sincronizados');
        
        if (!clientes.length) {
            container.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i>
                    Todos os clientes estão sincronizados!
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="table-container">
                <div class="table-header">
                    <h3 class="table-title">Clientes Não Sincronizados</h3>
                    <div class="table-actions">
                        <button class="btn btn-success" onclick="marcarTodosSincronizados()">
                            <i class="fas fa-sync"></i> Marcar Todos Sincronizados
                        </button>
                    </div>
                </div>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>
                                    <input type="checkbox" id="select-all-clientes" onchange="selecionarTodosClientes(this.checked)">
                                </th>
                                <th>ID</th>
                                <th>Nome</th>
                                <th>CPF/CNPJ</th>
                                <th>Tipo</th>
                                <th>Município/UF</th>
                                <th>Criado em</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        clientes.forEach(cliente => {
            let documento = cliente.cpf_cnpj || '';
            if (documento.length === 11) {
                documento = formatCPF(documento);
            } else if (documento.length === 14) {
                documento = formatCNPJ(documento);
            }
            
            const tipo = cliente.tipo_cliente === 'fisica' ? 'Pessoa Física' : 'Pessoa Jurídica';
            
            html += `
                <tr>
                    <td>
                        <input type="checkbox" class="cliente-checkbox" value="${cliente.id}">
                    </td>
                    <td>${cliente.id}</td>
                    <td>${cliente.nome_cliente}</td>
                    <td>${documento}</td>
                    <td>${tipo}</td>
                    <td>${cliente.municipio || ''}${cliente.uf ? '/' + cliente.uf : ''}</td>
                    <td>${formatDate(cliente.criado_em)}</td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-secondary btn-sm" onclick="editClienteFiscal(${cliente.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-success btn-sm" onclick="marcarClienteSincronizado(${cliente.id})">
                                <i class="fas fa-sync"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        
    } catch (error) {
        showAlert('Erro ao carregar clientes não sincronizados', 'danger');
    }
}

// Selecionar todos os clientes
function selecionarTodosClientes(checked) {
    const checkboxes = document.querySelectorAll('.cliente-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = checked;
    });
}

// Marcar todos os clientes selecionados como sincronizados
async function marcarTodosSincronizados() {
    const checkboxes = document.querySelectorAll('.cliente-checkbox:checked');
    const ids = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    if (ids.length === 0) {
        showAlert('Selecione pelo menos um cliente para marcar como sincronizado', 'warning');
        return;
    }
    
    if (!confirm(`Deseja marcar ${ids.length} cliente(s) como sincronizado(s)?`)) {
        return;
    }
    
    try {
        await fetchData(`${API_BASE}/clientes-fiscais/sincronizados/marcar-multiplos`, {
            method: 'POST',
            body: JSON.stringify({ ids: ids })
        });
        
        showAlert(`${ids.length} cliente(s) marcado(s) como sincronizado(s) com sucesso!`, 'success');
        await carregarClientesNaoSincronizados();
    } catch (error) {
        showAlert('Erro ao marcar clientes como sincronizados', 'danger');
    }
}