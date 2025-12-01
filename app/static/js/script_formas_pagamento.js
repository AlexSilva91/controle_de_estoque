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
    btnLimpar: document.getElementById('btn-limpar'),
    totaisGrid: document.getElementById('totais-grid'),

};

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando aplicação...');
    
    // Verificar se há parâmetros na URL e aplicar filtros automaticamente
    aplicarFiltrosDaURL();
    
    initializeApp();
    
    // Event listeners
    elements.retryBtn.addEventListener('click', initializeApp);
    elements.btnFiltrar.addEventListener('click', aplicarFiltros);
    elements.btnLimpar.addEventListener('click', limparFiltros);
    
    // Carregar operadores
    carregarOperadores();
});

// Aplicar filtros da URL automaticamente
function aplicarFiltrosDaURL() {
    console.log('Verificando parâmetros da URL...');
    const urlParams = new URLSearchParams(window.location.search);
    
    // Obter parâmetros da URL
    const formaPagamentoParam = urlParams.get('forma_pagamento');
    const dataInicioParam = urlParams.get('data_inicio');
    const dataFimParam = urlParams.get('data_fim');
    const operadorParam = urlParams.get('operador_id');
    const caixaIdParam = urlParams.get('caixa_id');
    
    console.log('Parâmetros da URL:', {
        forma_pagamento: formaPagamentoParam,
        data_inicio: dataInicioParam,
        data_fim: dataFimParam,
        operador_id: operadorParam,
        caixa_id: caixaIdParam
    });
    
    // Preencher campos de filtro com os parâmetros da URL
    if (formaPagamentoParam) {
        elements.formaPagamento.value = formaPagamentoParam;
        console.log(`Forma de pagamento definida: ${formaPagamentoParam}`);
    }
    
    if (dataInicioParam) {
        elements.dataInicio.value = dataInicioParam;
    }
    
    if (dataFimParam) {
        elements.dataFim.value = dataFimParam;
    }
    
    if (operadorParam) {
        // O operador será definido após carregar a lista
        setTimeout(() => {
            elements.operador.value = operadorParam;
        }, 500);
    }
    
    if (caixaIdParam) {
        elements.caixaId.value = caixaIdParam;
    }
    
    // Aplicar filtros automaticamente se houver parâmetros
    if (formaPagamentoParam || dataInicioParam || dataFimParam || operadorParam || caixaIdParam) {
        console.log('Aplicando filtros da URL automaticamente...');
        aplicarFiltrosAutomaticamente();
    }
}

// Aplicar filtros automaticamente sem clicar no botão
function aplicarFiltrosAutomaticamente() {
    console.log('Aplicando filtros automaticamente...');
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
    
    console.log('Filtros automáticos aplicados:', currentFilters);
    currentPage = 1;
    initializeApp();
}

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
                
                // Verificar se há parâmetro de operador na URL e aplicar
                const urlParams = new URLSearchParams(window.location.search);
                const operadorParam = urlParams.get('operador_id');
                if (operadorParam) {
                    elements.operador.value = operadorParam;
                    console.log(`Operador definido da URL: ${operadorParam}`);
                }
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
    
    const { caixas, paginacao, filtros } = data;
    renderizarTotaisConsolidados(data);

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
    
    // Mostrar informações dos filtros aplicados
    mostrarInfoFiltros(filtros);
}

// Mostrar informações dos filtros aplicados
function mostrarInfoFiltros(filtros) {
    const filtrosAtivos = [];
    
    if (filtros.data_inicio && filtros.data_fim) {
        filtrosAtivos.push(`Período: ${filtros.data_inicio} a ${filtros.data_fim}`);
    } else if (filtros.data_inicio) {
        filtrosAtivos.push(`Data: ${filtros.data_inicio}`);
    }
    
    if (filtros.forma_pagamento) {
        filtrosAtivos.push(`Forma de Pagamento: ${formatMethodName(filtros.forma_pagamento)}`);
    }
    
    if (filtros.operador_id) {
        // Tentar obter o nome do operador do select
        const operadorSelect = elements.operador;
        const selectedOption = operadorSelect.options[operadorSelect.selectedIndex];
        const nomeOperador = selectedOption ? selectedOption.text : filtros.operador_id;
        filtrosAtivos.push(`Operador: ${nomeOperador}`);
    }
    
    if (filtros.caixa_id) {
        filtrosAtivos.push(`Caixa ID: ${filtros.caixa_id}`);
    }
    
    if (filtrosAtivos.length > 0) {
        console.log('Filtros ativos:', filtrosAtivos);
        // Você pode exibir essas informações em algum lugar da interface se quiser
    }
}

function renderizarTotaisConsolidados(data) {
    const grid = elements.totaisGrid;
    grid.innerHTML = '';

    const totais = data.totais_por_forma_pagamento || {};
    const totalGeral = data.total_geral_formas_pagamento || "0,00";

    // Cards individuais por forma de pagamento
    const cardsFormas = Object.entries(totais).map(([forma, valor]) => `
        <div class="card-total">
            <h3>${formatMethodName(forma)}</h3>
            <p class="valor-total">${valor}</p>
        </div>
    `).join('');

    // Card do Total Geral
    const cardTotalGeral = `
        <div class="card-total card-total-geral">
            <h3>Total Geral</h3>
            <p class="valor-total">${totalGeral}</p>
        </div>
    `;

    // Inserir tudo no grid
    grid.innerHTML = cardsFormas + cardTotalGeral;
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

// Criar lista de formas de pagamento
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
    
    // Limpar também a URL
    const novaURL = window.location.pathname;
    window.history.replaceState({}, '', novaURL);
    
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
        'pix_edfrance': 'PIX Edfranci',
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