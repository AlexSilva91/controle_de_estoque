// Variáveis globais para controle dos lotes
let lotesProdutoAtual = null;
let loteEditando = null;
let todosLotes = [];
let paginacaoAtual = {
    pagina: 1,
    totalPaginas: 1,
    totalLotes: 0,
    porPagina: 10
};
let filtrosLotes = {
    produto: '',
    status: '',
    dataInicio: '',
    dataFim: '',
    busca: ''
};

// URL base da API - AJUSTE CONFORME SEU BLUEPRINT
const API_BASE_URL = '/admin/api';

// =============================================
// FUNÇÕES DE FORMATAÇÃO PARA PADRÃO BRASILEIRO
// =============================================

function converterParaNumero(valor) {
    if (valor === null || valor === undefined) return 0;
    if (typeof valor === 'number') return valor;
    if (typeof valor === 'string') {
        // Remove R$, espaços e converte de padrão brasileiro para float
        let valorLimpo = valor.toString()
            .replace('R$', '')
            .replace(/\./g, '')  // Remove pontos (separadores de milhar)
            .replace(',', '.')   // Substitui vírgula por ponto (decimal)
            .trim();

        const numero = parseFloat(valorLimpo);
        return isNaN(numero) ? 0 : numero;
    }
    return parseFloat(valor) || 0;
}

function formatarQuantidade(qtd) {
    const numero = converterParaNumero(qtd);
    // Sempre mostra 2 casas decimais, mesmo que sejam zeros
    return numero.toFixed(2).replace('.', ',');
}

function formatarValor(valor) {
    const numero = converterParaNumero(valor);

    // Formata com separadores de milhar e 2 casas decimais
    const partes = numero.toFixed(2).split('.');
    const inteiro = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    const decimal = partes[1];

    return `${inteiro},${decimal}`;
}

function formatarNumero(numero, casasDecimais = 2) {
    const num = converterParaNumero(numero);

    // Formata com número específico de casas decimais
    const partes = num.toFixed(casasDecimais).split('.');
    const inteiro = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    const decimal = partes[1];

    return `${inteiro},${decimal}`;
}

function formatarData(dataString) {
    const data = new Date(dataString);
    return data.toLocaleDateString('pt-BR') + ' ' + data.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// =============================================
// FUNÇÕES PARA MODAIS
// =============================================

function abrirModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        modal.style.justifyContent = 'center';
        modal.style.alignItems = 'center';
        document.body.style.overflow = 'hidden';

        // Adicionar animação de entrada
        const modalDialog = modal.querySelector('.modal-dialog');
        if (modalDialog) {
            modalDialog.style.animation = 'modalSlideIn 0.3s ease-out';
        }
    }
}

function fecharModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';

        // Limpar contexto se for o modal de edição
        if (modalId === 'editarLoteModal') {
            loteEditando = null;
        }
    }
}

// =============================================
// FUNÇÕES PARA A ABA DE LOTES (VISÃO GERAL)
// =============================================

// Inicialização da aba de lotes
function inicializarAbaLotes() {
    carregarTodosLotes();
    carregarProdutosParaFiltro();
    configurarEventListenersLotes();
}

function carregarTodosLotes(pagina = 1) {
    // Mostrar loading
    const lotesTable = document.getElementById('lotesTable');
    if (lotesTable) lotesTable.classList.add('loading-lotes');

    // Construir URL com filtros e paginação
    let url = `${API_BASE_URL}/lotes?`;
    const params = new URLSearchParams();

    if (filtrosLotes.produto) params.append('produto_id', filtrosLotes.produto);
    if (filtrosLotes.status) params.append('status', filtrosLotes.status);
    if (filtrosLotes.dataInicio) params.append('data_inicio', filtrosLotes.dataInicio);
    if (filtrosLotes.dataFim) params.append('data_fim', filtrosLotes.dataFim);

    // Parâmetros de paginação
    params.append('pagina', pagina);
    params.append('por_pagina', paginacaoAtual.porPagina);

    url += params.toString();

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Erro na resposta do servidor');
            return response.json();
        })
        .then(data => {
            todosLotes = data.lotes || [];
            paginacaoAtual = data.paginacao || paginacaoAtual;

            aplicarFiltrosLotes();
            atualizarResumoLotes(todosLotes);
            atualizarControlesPaginacao();

            if (lotesTable) lotesTable.classList.remove('loading-lotes');
        })
        .catch(error => {
            mostrarFlashMessage('Erro ao carregar lotes', 'error');
            if (lotesTable) lotesTable.classList.remove('loading-lotes');
        });
}

function carregarProdutosParaFiltro() {
    fetch(`${API_BASE_URL}/produtos/ativos`)
        .then(response => {
            if (!response.ok) throw new Error('Erro ao carregar produtos');
            return response.json();
        })
        .then(produtos => {
            const select = document.getElementById('filtroProdutoLote');
            if (select) {
                select.innerHTML = '<option value="">Todos os produtos</option>';

                produtos.forEach(produto => {
                    const option = document.createElement('option');
                    option.value = produto.id;
                    option.textContent = `${produto.nome} ${produto.marca ? `- ${produto.marca}` : ''} (${produto.codigo || 'Sem código'})`;
                    select.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Erro ao carregar produtos:', error);
        });
}

function configurarEventListenersLotes() {
    // Filtros
    const filtrarLotesBtn = document.getElementById('filtrarLotes');
    if (filtrarLotesBtn) {
        filtrarLotesBtn.addEventListener('click', () => {
            carregarTodosLotes(1);
        });
    }

    // Botão refresh
    const refreshLotesBtn = document.getElementById('refreshLotes');
    if (refreshLotesBtn) {
        refreshLotesBtn.addEventListener('click', () => {
            carregarTodosLotes(1);
        });
    }

    // Busca
    const searchLoteInput = document.getElementById('searchLote');
    if (searchLoteInput) {
        searchLoteInput.addEventListener('input', (e) => {
            filtrosLotes.busca = e.target.value;
            aplicarFiltrosLotes();
        });
    }

    // Filtros por change
    const filtroProduto = document.getElementById('filtroProdutoLote');
    if (filtroProduto) {
        filtroProduto.addEventListener('change', (e) => {
            filtrosLotes.produto = e.target.value;
            carregarTodosLotes(1);
        });
    }

    const filtroStatus = document.getElementById('filtroStatusLote');
    if (filtroStatus) {
        filtroStatus.addEventListener('change', (e) => {
            filtrosLotes.status = e.target.value;
            carregarTodosLotes(1);
        });
    }

    const filtroDataInicio = document.getElementById('filtroDataInicioLote');
    if (filtroDataInicio) {
        filtroDataInicio.addEventListener('change', (e) => {
            filtrosLotes.dataInicio = e.target.value;
            carregarTodosLotes(1);
        });
    }

    const filtroDataFim = document.getElementById('filtroDataFimLote');
    if (filtroDataFim) {
        filtroDataFim.addEventListener('change', (e) => {
            filtrosLotes.dataFim = e.target.value;
            carregarTodosLotes(1);
        });
    }

    // Botão limpar filtros
    const limparFiltrosBtn = document.getElementById('limparFiltrosLotes');
    if (limparFiltrosBtn) {
        limparFiltrosBtn.addEventListener('click', () => {
            limparFiltrosLotes();
        });
    }
}

function limparFiltrosLotes() {
    // Limpar valores dos inputs
    document.getElementById('filtroProdutoLote').value = '';
    document.getElementById('filtroStatusLote').value = '';
    document.getElementById('filtroDataInicioLote').value = '';
    document.getElementById('filtroDataFimLote').value = '';
    document.getElementById('searchLote').value = '';

    // Limpar variáveis
    filtrosLotes = {
        produto: '',
        status: '',
        dataInicio: '',
        dataFim: '',
        busca: ''
    };

    // Recarregar na página 1
    carregarTodosLotes(1);
}

function aplicarFiltrosLotes() {
    const buscaFiltro = filtrosLotes.busca.toLowerCase();

    let lotesFiltrados = todosLotes.filter(lote => {
        // Filtro por busca (nome do produto, marca, código)
        if (buscaFiltro) {
            const produtoNome = lote.produto_nome?.toLowerCase() || '';
            const produtoMarca = lote.produto_marca?.toLowerCase() || '';
            const produtoCodigo = lote.produto_codigo?.toLowerCase() || '';

            if (!produtoNome.includes(buscaFiltro) &&
                !produtoMarca.includes(buscaFiltro) &&
                !produtoCodigo.includes(buscaFiltro)) {
                return false;
            }
        }

        return true;
    });

    atualizarTabelaLotes(lotesFiltrados);
    atualizarResumoLotes(lotesFiltrados);
}

function atualizarTabelaLotes(lotes) {
    const tbody = document.querySelector('#lotesTable tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (lotes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-muted py-4">
                    <i class="fas fa-box-open fa-2x mb-2"></i>
                    <br>
                    Nenhum lote encontrado
                </td>
            </tr>
        `;
        return;
    }

    lotes.forEach(lote => {
        const tr = document.createElement('tr');
        const statusClass = `badge-lote ${lote.status}`;
        const statusText = lote.status === 'ativo' ? 'Ativo' :
            lote.status === 'parcial' ? 'Parcial' : 'Esgotado';

        // Converter valores para número antes de calcular
        const quantidadeInicial = converterParaNumero(lote.quantidade_inicial);
        const quantidadeDisponivel = converterParaNumero(lote.quantidade_disponivel);
        const valorUnitario = converterParaNumero(lote.valor_unitario_compra);

        const valorTotal = quantidadeInicial * valorUnitario;
        const percentualUtilizado = ((quantidadeInicial - quantidadeDisponivel) / quantidadeInicial) * 100;

        tr.innerHTML = `
            <td>
                <strong>${lote.produto_nome || 'N/A'}</strong>
                ${lote.produto_marca ? `<br><small class="text-muted">${lote.produto_marca}</small>` : ''}
                ${lote.produto_codigo ? `<br><small class="text-info">Cód: ${lote.produto_codigo}</small>` : ''}
            </td>
            <td>${formatarData(lote.data_entrada)}</td>
            <td>${formatarQuantidade(quantidadeInicial)}</td>
            <td>
                ${formatarQuantidade(quantidadeDisponivel)}
                ${lote.status === 'parcial' ? `<br><small class="text-warning">(${formatarNumero(percentualUtilizado, 1)}% utilizado)</small>` : ''}
            </td>
            <td>R$ ${formatarValor(valorUnitario)}</td>
            <td>R$ ${formatarValor(valorTotal)}</td>
            <td><span class="${statusClass}">${statusText}</span></td>
            <td>
                <div class="lote-actions">
                    <button class="btn-lote-action edit" data-lote-id="${lote.id}" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </td>
        `;

        tbody.appendChild(tr);
    });

    // Adicionar event listeners aos botões
    document.querySelectorAll('.btn-lote-action.edit').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const loteId = e.currentTarget.getAttribute('data-lote-id');
            abrirModalEditarLote(loteId);
        });
    });

    document.querySelectorAll('.btn-lote-action.delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const loteId = e.currentTarget.getAttribute('data-lote-id');
            confirmarExclusaoLote(loteId);
        });
    });
}

function atualizarResumoLotes(lotes) {
    let totalLotes = lotes.length;
    let quantidadeTotal = 0;
    let valorTotal = 0;
    let lotesEsgotados = 0;
    let lotesAtivos = 0;
    let lotesParciais = 0;

    lotes.forEach(lote => {
        const quantidadeDisponivel = converterParaNumero(lote.quantidade_disponivel);
        const valorUnitario = converterParaNumero(lote.valor_unitario_compra);

        quantidadeTotal += quantidadeDisponivel;
        valorTotal += quantidadeDisponivel * valorUnitario;

        if (lote.status === 'esgotado') {
            lotesEsgotados++;
        } else if (lote.status === 'ativo') {
            lotesAtivos++;
        } else if (lote.status === 'parcial') {
            lotesParciais++;
        }
    });

    // Atualizar elementos apenas se existirem
    const totalLotesEl = document.getElementById('totalLotes');
    const quantidadeTotalEl = document.getElementById('quantidadeTotalLotes');
    const valorTotalEl = document.getElementById('valorTotalLotes');
    const lotesEsgotadosEl = document.getElementById('lotesEsgotados');

    if (totalLotesEl) totalLotesEl.textContent = totalLotes;
    if (quantidadeTotalEl) quantidadeTotalEl.textContent = formatarQuantidade(quantidadeTotal);
    if (valorTotalEl) valorTotalEl.textContent = `R$ ${formatarValor(valorTotal)}`;
    if (lotesEsgotadosEl) lotesEsgotadosEl.textContent = lotesEsgotados;
}

function atualizarControlesPaginacao() {
    const paginacaoContainer = document.getElementById('paginacaoLotes');
    if (!paginacaoContainer) return;

    const { pagina_atual, total_paginas, total_lotes, tem_anterior, tem_proxima } = paginacaoAtual;

    let html = `
        <div class="paginacao-info">
            Página ${pagina_atual} de ${total_paginas} 
            (${total_lotes || 0} lotes)
        </div>
        <div class="paginacao-botoes">
    `;

    // Botão anterior
    if (tem_anterior) {
        html += `<button class="btn-pagina btn-pagina-anterior" data-pagina="${pagina_atual - 1}">
                    <i class="fas fa-chevron-left"></i> Anterior
                 </button>`;
    } else {
        html += `<button class="btn-pagina btn-pagina-anterior" disabled>
                    <i class="fas fa-chevron-left"></i> Anterior
                 </button>`;
    }

    // Números das páginas
    const inicio = Math.max(1, pagina_atual - 2);
    const fim = Math.min(total_paginas, pagina_atual + 2);

    for (let i = inicio; i <= fim; i++) {
        if (i === pagina_atual) {
            html += `<button class="btn-pagina btn-pagina-atual" disabled>${i}</button>`;
        } else {
            html += `<button class="btn-pagina" data-pagina="${i}">${i}</button>`;
        }
    }

    // Botão próximo
    if (tem_proxima) {
        html += `<button class="btn-pagina btn-pagina-proximo" data-pagina="${pagina_atual + 1}">
                    Próximo <i class="fas fa-chevron-right"></i>
                 </button>`;
    } else {
        html += `<button class="btn-pagina btn-pagina-proximo" disabled>
                    Próximo <i class="fas fa-chevron-right"></i>
                 </button>`;
    }

    html += `</div>`;

    paginacaoContainer.innerHTML = html;

    // Adicionar event listeners
    paginacaoContainer.querySelectorAll('.btn-pagina:not(:disabled)').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pagina = parseInt(e.target.getAttribute('data-pagina'));
            if (pagina && !isNaN(pagina)) {
                carregarTodosLotes(pagina);
            }
        });
    });
}

// =============================================
// FUNÇÕES PARA MODAIS DE LOTES (GERENCIAMENTO POR PRODUTO)
// =============================================

// Funções para gerenciar lotes por produto
function abrirModalLotesProduto(produtoId, produtoNome) {
    lotesProdutoAtual = produtoId;
    const lotesProdutoNomeEl = document.getElementById('lotesProdutoNome');
    if (lotesProdutoNomeEl) lotesProdutoNomeEl.textContent = produtoNome;

    // Carregar dados do produto para o resumo
    carregarResumoProduto(produtoId);

    // Carregar lotes do produto
    carregarLotesProduto(produtoId);

    // Abrir modal
    abrirModal('listarLotesModal');
}

function carregarResumoProduto(produtoId) {
    fetch(`${API_BASE_URL}/produtos/${produtoId}`)
        .then(response => {
            if (!response.ok) throw new Error('Erro ao carregar produto');
            return response.json();
        })
        .then(produto => {
            const estoqueAtualEl = document.getElementById('lotesEstoqueAtual');
            if (estoqueAtualEl) {
                estoqueAtualEl.textContent = formatarQuantidade(produto.estoque_loja);
            }
        })
        .catch(error => {
            mostrarFlashMessage('Erro ao carregar dados do produto', 'error');
        });
}

function carregarLotesProduto(produtoId, pagina = 1) {
    const url = `${API_BASE_URL}/produtos/${produtoId}/lotes?pagina=${pagina}&por_pagina=${paginacaoAtual.porPagina}`;

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Erro ao carregar lotes do produto');
            return response.json();
        })
        .then(data => {
            atualizarTabelaLotesProduto(data.lotes || []);
            atualizarResumoLotesProduto(data.lotes || []);

            // Atualizar paginação para o modal específico
            if (data.paginacao) {
                paginacaoAtual = data.paginacao;
                atualizarControlesPaginacaoModal();
            }
        })
        .catch(error => {
            mostrarFlashMessage('Erro ao carregar lotes', 'error');
        });
}

function atualizarTabelaLotesProduto(lotes) {
    // Usar a tabela específica do modal (se existir) ou a tabela principal
    const tbody = document.querySelector('#listarLotesModal #lotesTable tbody') ||
        document.querySelector('#lotesTable tbody');

    if (!tbody) {

        return;
    }

    tbody.innerHTML = '';

    if (lotes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted py-4">
                    <i class="fas fa-box-open fa-2x mb-2"></i>
                    <br>
                    Nenhum lote cadastrado para este produto
                </td>
            </tr>
        `;
        return;
    }

    lotes.forEach(lote => {
        const tr = document.createElement('tr');

        // Converter valores para número antes de calcular
        const quantidadeInicial = converterParaNumero(lote.quantidade_inicial);
        const quantidadeDisponivel = converterParaNumero(lote.quantidade_disponivel);
        const valorUnitario = converterParaNumero(lote.valor_unitario_compra);

        // Determinar status do lote
        let statusClass = 'ativo';
        let statusText = 'Ativo';

        if (quantidadeDisponivel === 0) {
            statusClass = 'esgotado';
            statusText = 'Esgotado';
        } else if (quantidadeDisponivel < quantidadeInicial) {
            statusClass = 'parcial';
            statusText = 'Parcial';
        }

        const valorTotal = quantidadeInicial * valorUnitario;

        tr.innerHTML = `
            <td>${formatarData(lote.data_entrada)}</td>
            <td>${formatarQuantidade(quantidadeInicial)}</td>
            <td>${formatarQuantidade(quantidadeDisponivel)}</td>
            <td>R$ ${formatarValor(valorUnitario)}</td>
            <td>R$ ${formatarValor(valorTotal)}</td>
            <td><span class="badge-lote ${statusClass}">${statusText}</span></td>
            <td>
                <div class="lote-actions">
                    <button class="btn-lote-action edit" data-lote-id="${lote.id}" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </td>
        `;

        tbody.appendChild(tr);
    });

    // Adicionar event listeners aos botões específicos do modal
    const modal = document.getElementById('listarLotesModal');
    if (modal) {
        modal.querySelectorAll('.btn-lote-action.edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const loteId = e.currentTarget.getAttribute('data-lote-id');
                abrirModalEditarLote(loteId);
            });
        });

        modal.querySelectorAll('.btn-lote-action.delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const loteId = e.currentTarget.getAttribute('data-lote-id');
                confirmarExclusaoLote(loteId);
            });
        });
    }
}

function atualizarResumoLotesProduto(lotes) {
    let quantidadeTotal = 0;
    let valorTotal = 0;

    lotes.forEach(lote => {
        const quantidadeDisponivel = converterParaNumero(lote.quantidade_disponivel);
        const valorUnitario = converterParaNumero(lote.valor_unitario_compra);

        quantidadeTotal += quantidadeDisponivel;
        valorTotal += quantidadeDisponivel * valorUnitario;
    });

    const quantidadeTotalEl = document.getElementById('lotesQuantidadeTotal');
    const valorTotalEl = document.getElementById('lotesValorTotal');

    if (quantidadeTotalEl) quantidadeTotalEl.textContent = formatarQuantidade(quantidadeTotal);
    if (valorTotalEl) valorTotalEl.textContent = `R$ ${formatarValor(valorTotal)}`;
}

function atualizarControlesPaginacaoModal() {
    const paginacaoContainer = document.getElementById('paginacaoLotesModal');
    if (!paginacaoContainer || !lotesProdutoAtual) return;

    const { pagina_atual, total_paginas, tem_anterior, tem_proxima } = paginacaoAtual;

    let html = `
        <div class="paginacao-info">
            Página ${pagina_atual} de ${total_paginas}
        </div>
        <div class="paginacao-botoes">
    `;

    // Botão anterior
    if (tem_anterior) {
        html += `<button class="btn-pagina btn-pagina-anterior" data-pagina="${pagina_atual - 1}">
                    <i class="fas fa-chevron-left"></i>
                 </button>`;
    }

    // Botão próximo
    if (tem_proxima) {
        html += `<button class="btn-pagina btn-pagina-proximo" data-pagina="${pagina_atual + 1}">
                    <i class="fas fa-chevron-right"></i>
                 </button>`;
    }

    html += `</div>`;

    paginacaoContainer.innerHTML = html;

    // Adicionar event listeners
    paginacaoContainer.querySelectorAll('.btn-pagina').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pagina = parseInt(e.target.getAttribute('data-pagina'));
            if (pagina && !isNaN(pagina)) {
                carregarLotesProduto(lotesProdutoAtual, pagina);
            }
        });
    });
}

// =============================================
// FUNÇÕES COMPARTILHADAS PARA EDIÇÃO
// =============================================

// =============================================
// FUNÇÕES COMPARTILHADAS PARA EDIÇÃO
// =============================================

function abrirModalEditarLote(loteId) {
    if (!loteId) {
        mostrarFlashMessage('ID do lote não fornecido', 'error');
        return;
    }

    loteEditando = loteId;
    const modalTitle = document.getElementById('editarLoteModalTitle');
    const submitText = document.getElementById('editarLoteSubmitText');

    if (modalTitle) modalTitle.textContent = 'Editar Lote';
    if (submitText) submitText.textContent = 'Atualizar Lote';

    carregarDadosLote(loteId);
    abrirModal('editarLoteModal');

    // 🔒 Bloqueia campos que não devem ser alterados
    const quantidadeInicial = document.getElementById('loteQuantidadeInicial');
    const dataEntrada = document.getElementById('loteDataEntrada');

    if (quantidadeInicial) quantidadeInicial.readOnly = true;
    if (dataEntrada) {
        dataEntrada.readOnly = true;
        dataEntrada.disabled = true; // evita abrir o calendário
    }

    // 💅 Opcional: deixar visualmente desabilitados (cinza)
    if (quantidadeInicial) quantidadeInicial.classList.add('campo-desativado');
    if (dataEntrada) dataEntrada.classList.add('campo-desativado');
}


function carregarDadosLote(loteId) {
    fetch(`${API_BASE_URL}/lotes/${loteId}`)
        .then(response => {
            if (!response.ok) throw new Error('Erro ao carregar lote');
            return response.json();
        })
        .then(lote => {
            document.getElementById('loteId').value = lote.id;
            document.getElementById('loteProdutoId').value = lote.produto_id;

            // Usar valores convertidos para preencher o formulário
            document.getElementById('loteQuantidadeInicial').value = converterParaNumero(lote.quantidade_inicial);
            document.getElementById('loteQuantidadeDisponivel').value = converterParaNumero(lote.quantidade_disponivel);
            document.getElementById('loteValorUnitario').value = converterParaNumero(lote.valor_unitario_compra);

            // Formatar data para o input datetime-local
            const dataEntrada = new Date(lote.data_entrada);
            const dataFormatada = dataEntrada.toISOString().slice(0, 16);
            document.getElementById('loteDataEntrada').value = dataFormatada;

            document.getElementById('loteObservacao').value = lote.observacao || '';

            calcularValoresLote();
        })
        .catch(error => {
            mostrarFlashMessage('Erro ao carregar dados do lote', 'error');
        });
}

function calcularValoresLote() {
    const quantidadeInicial = parseFloat(document.getElementById('loteQuantidadeInicial').value) || 0;
    const quantidadeDisponivel = parseFloat(document.getElementById('loteQuantidadeDisponivel').value) || 0;
    const valorUnitario = parseFloat(document.getElementById('loteValorUnitario').value) || 0;

    const valorTotal = quantidadeInicial * valorUnitario;
    const diferencaQuantidade = quantidadeInicial - quantidadeDisponivel;

    const valorTotalEl = document.getElementById('loteValorTotalCalculado');
    const diferencaQuantidadeEl = document.getElementById('loteDiferencaQuantidade');

    if (valorTotalEl) valorTotalEl.textContent = `R$ ${formatarValor(valorTotal)}`;
    if (diferencaQuantidadeEl) diferencaQuantidadeEl.textContent = formatarQuantidade(diferencaQuantidade);

    // Validação e feedback visual
    const quantidadeDisponivelInput = document.getElementById('loteQuantidadeDisponivel');
    const submitBtn = document.querySelector('#editarLoteForm button[type="submit"]');

    if (quantidadeDisponivelInput && submitBtn) {
        if (quantidadeDisponivel > quantidadeInicial) {
            quantidadeDisponivelInput.classList.add('is-invalid');
            submitBtn.disabled = true;
        } else {
            quantidadeDisponivelInput.classList.remove('is-invalid');
            submitBtn.disabled = false;
        }
    }
}

function confirmarExclusaoLote(loteId) {
    fetch(`${API_BASE_URL}/lotes/${loteId}`)
        .then(response => {
            if (!response.ok) throw new Error('Erro ao carregar lote');
            return response.json();
        })
        .then(lote => {
            const texto = `Tem certeza que deseja excluir o lote #${lote.id} do produto "${lote.produto_nome}"?`;
            const textoEl = document.getElementById('confirmarExclusaoLoteTexto');
            if (textoEl) textoEl.textContent = texto;

            const btnConfirmar = document.getElementById('confirmarExclusaoLoteBtn');
            if (btnConfirmar) {
                btnConfirmar.onclick = () => excluirLote(loteId);
            }

            abrirModal('confirmarExclusaoLoteModal');
        })
        .catch(error => {
            mostrarFlashMessage('Erro ao carregar dados do lote', 'error');
        });
}

function salvarLote() {
    const formData = new FormData(document.getElementById('editarLoteForm'));
    const loteId = formData.get('loteId');

    // VALIDAÇÃO: Garantir que temos um ID de lote para edição
    if (!loteId) {
        mostrarFlashMessage('ID do lote não encontrado. Apenas edição é permitida.', 'error');
        return;
    }

    // Preparar dados para envio - CONVERTER CORRETAMENTE OS VALORES
    const dados = {
        quantidade_inicial: parseFloat(formData.get('loteQuantidadeInicial')) || 0,
        quantidade_disponivel: parseFloat(formData.get('loteQuantidadeDisponivel')) || 0,
        valor_unitario_compra: parseFloat(formData.get('loteValorUnitario')) || 0,
        observacao: formData.get('loteObservacao') || ''
    };

    // VALIDAÇÃO: quantidade_disponivel não pode ser maior que quantidade_inicial
    if (dados.quantidade_disponivel > dados.quantidade_inicial) {
        mostrarFlashMessage('Quantidade disponível não pode ser maior que quantidade inicial', 'error');
        return;
    }

    // Data de entrada
    const dataEntrada = formData.get('loteDataEntrada');
    if (dataEntrada) {
        // Garantir que a data está no formato correto
        const dataObj = new Date(dataEntrada);
        if (!isNaN(dataObj.getTime())) {
            dados.data_entrada = dataObj.toISOString().slice(0, 16); // Formato YYYY-MM-DDTHH:mm
        }
    }

    const url = `${API_BASE_URL}/lotes/${loteId}`;
    const method = 'PUT';

    // Mostrar loading
    const submitBtn = document.querySelector('#editarLoteForm button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';
    submitBtn.disabled = true;

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dados)
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `Erro ${response.status}: ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            mostrarFlashMessage('Lote atualizado com sucesso', 'success');
            fecharModal('editarLoteModal');

            // Recarregar dados conforme o contexto
            if (lotesProdutoAtual) {
                carregarLotesProduto(lotesProdutoAtual);
                carregarResumoProduto(lotesProdutoAtual);
            } else {
                carregarTodosLotes(1);
            }
        })
        .catch(error => {
            mostrarFlashMessage(error.message || 'Erro ao atualizar lote', 'error');
        })
        .finally(() => {
            // Restaurar botão
            if (submitBtn) {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
}

// =============================================
// EVENT LISTENERS GLOBAIS
// =============================================

document.addEventListener('DOMContentLoaded', function () {
    // Botão refresh lotes na aba geral
    const refreshLotesBtn = document.getElementById('refreshLotes');
    if (refreshLotesBtn) {
        refreshLotesBtn.addEventListener('click', () => {
            carregarTodosLotes(1);
        });
    }

    // Botão refresh lotes no modal de produto
    const refreshLotesModalBtn = document.getElementById('refreshLotesModal');
    if (refreshLotesModalBtn) {
        refreshLotesModalBtn.addEventListener('click', () => {
            if (lotesProdutoAtual) {
                carregarLotesProduto(lotesProdutoAtual);
                carregarResumoProduto(lotesProdutoAtual);
            }
        });
    }

    // Formulário de lote
    const editarLoteForm = document.getElementById('editarLoteForm');
    if (editarLoteForm) {
        editarLoteForm.addEventListener('submit', function (e) {
            e.preventDefault();
            salvarLote();
        });
    }

    // Cálculos automáticos no formulário
    const camposCalculo = ['loteQuantidadeInicial', 'loteQuantidadeDisponivel', 'loteValorUnitario'];
    camposCalculo.forEach(campo => {
        const elemento = document.getElementById(campo);
        if (elemento) {
            elemento.addEventListener('input', calcularValoresLote);
        }
    });

    // Event listeners para fechar modais
    document.querySelectorAll('.close-modal, .modal-overlay').forEach(element => {
        element.addEventListener('click', function (e) {
            e.preventDefault();
            const modal = this.closest('.modal');
            if (modal) {
                fecharModal(modal.id);
            }
        });
    });

    // Inicializar aba de lotes se estiver ativa
    if (document.querySelector('#lotes.tab-content.active')) {
        inicializarAbaLotes();
    }

    // Quando a aba de lotes for clicada
    document.addEventListener('click', function (e) {
        if (e.target.closest('[data-tab="lotes"]')) {
            setTimeout(() => {
                inicializarAbaLotes();
            }, 100);
        }
    });
});

// =============================================
// FUNÇÕES AUXILIARES ADICIONAIS
// =============================================

function formatarPercentual(valor, casasDecimais = 1) {
    return formatarNumero(valor, casasDecimais);
}

// Função para navegar entre abas (se não existir)
function switchToTab(tabName) {
    const tabElement = document.querySelector(`[data-tab="${tabName}"]`);
    if (tabElement) {
        tabElement.click();
    }
}

function mostrarFlashMessage(mensagem, tipo = 'info') {

    const flashContainer = document.querySelector('.flash-messages');
    if (flashContainer) {
        const flashMessage = document.createElement('div');
        flashMessage.className = `flash-message ${tipo}`;
        flashMessage.innerHTML = `
            <div class="flash-content">
                <i class="fas ${tipo === 'success' ? 'fa-check-circle' : tipo === 'error' ? 'fa-exclamation-circle' : tipo === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'}"></i>
                <span>${mensagem}</span>
            </div>
            <button class="close-flash" aria-label="Fechar">&times;</button>
        `;
        flashContainer.appendChild(flashMessage);

        // Auto-remover após 5 segundos
        setTimeout(() => {
            flashMessage.remove();
        }, 5000);

        // Adicionar evento para fechar manualmente
        flashMessage.querySelector('.close-flash').addEventListener('click', function () {
            flashMessage.remove();
        });
    }
}