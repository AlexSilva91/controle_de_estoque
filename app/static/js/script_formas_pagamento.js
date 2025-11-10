// Configurações
const API_BASE_URL = window.location.origin;
let currentPage = 1;
let currentFilters = {};

// Elementos DOM
const elements = {
    loading: document.getElementById('loading'),
    errorState: document.getElementById('error-state'),
    errorMessage: document.getElementById('error-message'),
    retryBtn: document.getElementById('retry-btn'),
    tableBody: document.getElementById('table-body'),
    pagination: document.getElementById('pagination'),
    
    // Filtros
    dataInicio: document.getElementById('data-inicio'),
    dataFim: document.getElementById('data-fim'),
    formaPagamento: document.getElementById('forma-pagamento'),
    operador: document.getElementById('operador'),
    caixaId: document.getElementById('caixa-id'),
    btnFiltrar: document.getElementById('btn-filtrar'),
    btnLimpar: document.getElementById('btn-limpar')
};

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando aplicação...');
    initializeApp();
    
    // Event listeners
    elements.retryBtn.addEventListener('click', initializeApp);
    elements.btnFiltrar.addEventListener('click', aplicarFiltros);
    elements.btnLimpar.addEventListener('click', limparFiltros);
    
    // Carregar operadores
    carregarOperadores();
});

// Função principal de inicialização
async function initializeApp() {
    console.log('Inicializando app...');
    showLoading();
    hideError();
    
    try {
        await carregarDadosCaixas();
    } catch (error) {
        console.error('Erro na inicialização:', error);
        showError('Erro ao carregar dados dos caixas: ' + error.message);
    }
}

// Carregar operadores para o filtro
async function carregarOperadores() {
    try {
        console.log('Carregando operadores...');
        const response = await fetch('/admin/caixas/operadores/formas-pagamento');
        if (response.ok) {
            const data = await response.json();
            console.log('Dados operadores:', data);
            if (data.success) {
                data.operadores.forEach(op => {
                    const option = document.createElement('option');
                    option.value = op.id;
                    option.textContent = op.nome;
                    elements.operador.appendChild(option);
                });
                console.log(`Carregados ${data.operadores.length} operadores`);
            } else {
                console.error('Erro na resposta dos operadores:', data.error);
            }
        } else {
            console.error('Erro HTTP ao carregar operadores:', response.status);
        }
    } catch (error) {
        console.error('Erro ao carregar operadores:', error);
    }
}

// Carregar dados dos caixas
async function carregarDadosCaixas(page = 1) {
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: 10,
            ...currentFilters
        });

        console.log(`Carregando dados da página ${page} com filtros:`, Object.fromEntries(params));
        const response = await fetch(`/admin/caixas/financeiro/todos?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Dados recebidos:', data);
        
        if (data.success) {
            renderizarDados(data);
        } else {
            throw new Error(data.error || 'Erro desconhecido na API');
        }
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        throw error;
    }
}

// Renderizar dados na tabela
function renderizarDados(data) {
    console.log('Renderizando dados...', data);
    hideLoading();
    
    const { caixas, paginacao } = data;
    
    // Limpar tabela
    elements.tableBody.innerHTML = '';
    
    if (!caixas || caixas.length === 0) {
        elements.tableBody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; color: var(--text-muted); padding: var(--space-xxl);">
                    Nenhum caixa encontrado com os filtros aplicados
                </td>
            </tr>
        `;
        elements.pagination.innerHTML = '';
        return;
    }
    
    // Preencher tabela
    caixas.forEach(caixa => {
        console.log('Processando caixa:', caixa.id, 'Formas pagamento:', caixa.formas_pagamento, 'Contas prazo:', caixa.contas_prazo_recebidas);
        const row = criarLinhaTabela(caixa);
        elements.tableBody.appendChild(row);
    });
    
    // Atualizar paginação
    renderizarPaginacao(paginacao);
}

// Criar linha da tabela
function criarLinhaTabela(caixa) {
    const row = document.createElement('tr');
    
    // Formatar data
    const dataAbertura = new Date(caixa.data_abertura).toLocaleDateString('pt-BR');
    const statusClass = caixa.status === 'aberto' ? 'status-aberto' : 'status-fechado';
    
    row.innerHTML = `
        <td>${caixa.id}</td>
        <td>${dataAbertura}</td>
        <td>${caixa.operador_nome}</td>
        <td>
            <span class="status-badge ${statusClass}">${caixa.status}</span>
        </td>
        <td>${formatCurrency(caixa.totais_gerais.entradas)}</td>
        <td>${formatCurrency(caixa.totais_gerais.saidas)}</td>
        <td>${formatCurrency(caixa.totais_gerais.saldo)}</td>
        <td class="payment-methods-cell">
            ${criarListaFormasPagamento(caixa.formas_pagamento, 'Vendas')}
        </td>
        <td class="payment-methods-cell">
            ${criarListaFormasPagamento(caixa.contas_prazo_recebidas, 'Contas Recebidas')}
        </td>
    `;
    
    return row;
}

// Criar lista de formas de pagamento - ATUALIZADO
function criarListaFormasPagamento(formasPagamento, tipo = '') {
    console.log(`Criando lista ${tipo}:`, formasPagamento);
    
    if (!formasPagamento || Object.keys(formasPagamento).length === 0) {
        return `<span style="color: var(--text-muted);">Nenhuma ${tipo.toLowerCase()}</span>`;
    }
    
    return Object.entries(formasPagamento)
        .map(([forma, valorTotal]) => {
            console.log(`${tipo} - Forma: ${forma}, Valor Total:`, valorTotal);
            const isPrazoRecebido = tipo === 'Contas Recebidas';
            const badgeClass = isPrazoRecebido ? 'prazo-badge' : '';
            
            return `
                <div class="payment-method-item ${badgeClass}">
                    <span class="payment-method-name">${formatMethodName(forma)}</span>
                    <span class="payment-method-value">${formatCurrency(valorTotal)}</span>
                </div>
            `;
        })
        .join('');
}

// Renderizar paginação
function renderizarPaginacao(paginacao) {
    const { pagina_atual, total_paginas, total } = paginacao;
    
    let paginacaoHTML = `
        <div class="pagination-info">
            Mostrando ${((pagina_atual - 1) * 10) + 1}-${Math.min(pagina_atual * 10, total)} de ${total} caixas
        </div>
        <div class="pagination-controls">
    `;
    
    // Botão anterior
    if (pagina_atual > 1) {
        paginacaoHTML += `<button class="pagination-btn" onclick="mudarPagina(${pagina_atual - 1})">Anterior</button>`;
    }
    
    // Páginas
    const startPage = Math.max(1, pagina_atual - 2);
    const endPage = Math.min(total_paginas, pagina_atual + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === pagina_atual) {
            paginacaoHTML += `<button class="pagination-btn active">${i}</button>`;
        } else {
            paginacaoHTML += `<button class="pagination-btn" onclick="mudarPagina(${i})">${i}</button>`;
        }
    }
    
    // Botão próximo
    if (pagina_atual < total_paginas) {
        paginacaoHTML += `<button class="pagination-btn" onclick="mudarPagina(${pagina_atual + 1})">Próximo</button>`;
    }
    
    paginacaoHTML += '</div>';
    elements.pagination.innerHTML = paginacaoHTML;
}

// Mudar página
function mudarPagina(pagina) {
    console.log(`Mudando para página ${pagina}`);
    currentPage = pagina;
    carregarDadosCaixas(pagina);
}

// Aplicar filtros
function aplicarFiltros() {
    console.log('Aplicando filtros...');
    currentFilters = {};
    
    if (elements.dataInicio.value) {
        currentFilters.data_inicio = elements.dataInicio.value;
    }
    
    if (elements.dataFim.value) {
        currentFilters.data_fim = elements.dataFim.value;
    }
    
    if (elements.formaPagamento.value) {
        currentFilters.forma_pagamento = elements.formaPagamento.value;
    }
    
    if (elements.operador.value) {
        currentFilters.operador_id = elements.operador.value;
    }
    
    if (elements.caixaId.value) {
        currentFilters.caixa_id = elements.caixaId.value;
    }
    
    console.log('Filtros aplicados:', currentFilters);
    currentPage = 1;
    initializeApp();
}

// Limpar filtros
function limparFiltros() {
    console.log('Limpando filtros...');
    elements.dataInicio.value = '';
    elements.dataFim.value = '';
    elements.formaPagamento.value = '';
    elements.operador.value = '';
    elements.caixaId.value = '';
    
    currentFilters = {};
    currentPage = 1;
    initializeApp();
}

// Utilitários
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value || 0);
}

function formatMethodName(method) {
    const configs = {
        'dinheiro': 'Dinheiro',
        'cartao_credito': 'Cartão Crédito',
        'cartao_debito': 'Cartão Débito',
        'pix_fabiano': 'PIX Fabiano',
        'pix_maquineta': 'PIX Maquineta',
        'pix_edfrance': 'PIX EDFrance',
        'pix_loja': 'PIX Loja',
        'a_prazo': 'A Prazo'
    };
    
    return configs[method] || method.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

function showLoading() {
    elements.loading.style.display = 'flex';
    elements.errorState.style.display = 'none';
}

function hideLoading() {
    elements.loading.style.display = 'none';
}

function showError(message) {
    elements.loading.style.display = 'none';
    elements.errorState.style.display = 'block';
    elements.errorMessage.textContent = message;
}

function hideError() {
    elements.errorState.style.display = 'none';
}
