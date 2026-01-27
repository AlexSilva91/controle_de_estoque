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

// Renderizar produtos fiscais
function renderProdutosFiscais(produtos) {
    // Implementar renderização de produtos fiscais
    console.log('Renderizando produtos fiscais:', produtos);
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

