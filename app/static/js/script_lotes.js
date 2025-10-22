// Variáveis globais para controle dos lotes
let lotesProdutoAtual = null;
let loteEditando = null;
let todosLotes = [];
let filtrosLotes = {
    produto: '',
    status: '',
    dataInicio: '',
    dataFim: ''
};

// URL base da API - AJUSTE CONFORME SEU BLUEPRINT
const API_BASE_URL = '/admin/api'; // Altere para o prefixo correto do seu admin_bp

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

function carregarTodosLotes() {
    // Mostrar loading
    const lotesTable = document.getElementById('lotesTable');
    if (lotesTable) lotesTable.classList.add('loading-lotes');

    // Construir URL com filtros
    let url = `${API_BASE_URL}/lotes?`;
    const params = new URLSearchParams();

    if (filtrosLotes.produto) params.append('produto_id', filtrosLotes.produto);
    if (filtrosLotes.dataInicio) params.append('data_inicio', filtrosLotes.dataInicio);
    if (filtrosLotes.dataFim) params.append('data_fim', filtrosLotes.dataFim);

    url += params.toString();

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Erro na resposta do servidor');
            return response.json();
        })
        .then(lotes => {
            todosLotes = lotes;
            aplicarFiltrosLotes();
            atualizarResumoLotes(lotes);
            if (lotesTable) lotesTable.classList.remove('loading-lotes');
        })
        .catch(error => {
            console.error('Erro ao carregar lotes:', error);
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
        filtrarLotesBtn.addEventListener('click', aplicarFiltrosLotes);
    }

    // Botão novo lote
    const addLoteBtn = document.getElementById('addLote');
    if (addLoteBtn) {
        addLoteBtn.addEventListener('click', () => {
            abrirModalNovoLote();
        });
    }

    // Botão refresh
    const refreshLotesBtn = document.getElementById('refreshLotes');
    if (refreshLotesBtn) {
        refreshLotesBtn.addEventListener('click', () => {
            carregarTodosLotes();
        });
    }

    // Busca
    const searchLoteInput = document.getElementById('searchLote');
    if (searchLoteInput) {
        searchLoteInput.addEventListener('input', (e) => {
            aplicarFiltrosLotes();
        });
    }

    // Filtros por change
    const filtroProduto = document.getElementById('filtroProdutoLote');
    if (filtroProduto) {
        filtroProduto.addEventListener('change', (e) => {
            filtrosLotes.produto = e.target.value;
            aplicarFiltrosLotes();
        });
    }

    const filtroStatus = document.getElementById('filtroStatusLote');
    if (filtroStatus) {
        filtroStatus.addEventListener('change', (e) => {
            filtrosLotes.status = e.target.value;
            aplicarFiltrosLotes();
        });
    }

    const filtroDataInicio = document.getElementById('filtroDataInicioLote');
    if (filtroDataInicio) {
        filtroDataInicio.addEventListener('change', (e) => {
            filtrosLotes.dataInicio = e.target.value;
            aplicarFiltrosLotes();
        });
    }

    const filtroDataFim = document.getElementById('filtroDataFimLote');
    if (filtroDataFim) {
        filtroDataFim.addEventListener('change', (e) => {
            filtrosLotes.dataFim = e.target.value;
            aplicarFiltrosLotes();
        });
    }
}

function aplicarFiltrosLotes() {
    const statusFiltro = document.getElementById('filtroStatusLote')?.value || '';
    const buscaFiltro = document.getElementById('searchLote')?.value.toLowerCase() || '';

    let lotesFiltrados = todosLotes.filter(lote => {
        // Filtro por status
        if (statusFiltro && lote.status !== statusFiltro) {
            return false;
        }

        // Filtro por busca (nome do produto)
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
            <td>${lote.id}</td>
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
                    <button class="btn-lote-action delete" data-lote-id="${lote.id}" title="Excluir">
                        <i class="fas fa-trash"></i>
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

function abrirModalNovoLote() {
    // Limpar formulário e abrir modal para novo lote
    limparFormularioLote();
    const modalTitle = document.getElementById('editarLoteModalTitle');
    const submitText = document.getElementById('editarLoteSubmitText');

    if (modalTitle) modalTitle.textContent = 'Adicionar Lote';
    if (submitText) submitText.textContent = 'Criar Lote';

    abrirModal('editarLoteModal');
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
            console.error('Erro ao carregar resumo do produto:', error);
            mostrarFlashMessage('Erro ao carregar dados do produto', 'error');
        });
}

function carregarLotesProduto(produtoId) {
    fetch(`${API_BASE_URL}/produtos/${produtoId}/lotes`)
        .then(response => {
            if (!response.ok) throw new Error('Erro ao carregar lotes do produto');
            return response.json();
        })
        .then(lotes => {
            atualizarTabelaLotesProduto(lotes);
            atualizarResumoLotesProduto(lotes);
        })
        .catch(error => {
            console.error('Erro ao carregar lotes:', error);
            mostrarFlashMessage('Erro ao carregar lotes', 'error');
        });
}

function atualizarTabelaLotesProduto(lotes) {
    // Usar a tabela específica do modal (se existir) ou a tabela principal
    const tbody = document.querySelector('#listarLotesModal #lotesTable tbody') ||
        document.querySelector('#lotesTable tbody');

    if (!tbody) {
        console.error('Tabela de lotes não encontrada');
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
            <td>${lote.id}</td>
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
                    <button class="btn-lote-action delete" data-lote-id="${lote.id}" title="Excluir">
                        <i class="fas fa-trash"></i>
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

// =============================================
// FUNÇÕES COMPARTILHADAS PARA EDIÇÃO/CRIAÇÃO
// =============================================

function abrirModalEditarLote(loteId = null) {
    loteEditando = loteId;
    const modalTitle = document.getElementById('editarLoteModalTitle');
    const submitText = document.getElementById('editarLoteSubmitText');

    if (loteId) {
        if (modalTitle) modalTitle.textContent = 'Editar Lote';
        if (submitText) submitText.textContent = 'Atualizar Lote';
        carregarDadosLote(loteId);
    } else {
        if (modalTitle) modalTitle.textContent = 'Adicionar Lote';
        if (submitText) submitText.textContent = 'Criar Lote';
        limparFormularioLote();

        // Debug: verificar se o contexto está sendo preservado
        console.log('Abrindo modal para novo lote - Contexto:', {
            lotesProdutoAtual: lotesProdutoAtual,
            campoProdutoId: document.getElementById('loteProdutoId').value
        });
    }

    abrirModal('editarLoteModal');
}

function carregarDadosLote(loteId) {
    fetch(`${API_BASE_URL}/lotes/${loteId}`)
        .then(response => {
            if (!response.ok) throw new Error('Erro ao carregar lote');
            return response.json();
        })
        .then(lote => {
            document.getElementById('loteId').value = lote.id;
            // Priorizar o contexto atual, mas usar o produto_id do lote se não houver contexto
            document.getElementById('loteProdutoId').value = lotesProdutoAtual || lote.produto_id;
            
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
            console.error('Erro ao carregar dados do lote:', error);
            mostrarFlashMessage('Erro ao carregar dados do lote', 'error');
        });
}

function limparFormularioLote() {
    document.getElementById('loteId').value = '';
    // Manter o produto_id do contexto atual se existir
    const produtoIdAtual = lotesProdutoAtual || '';
    document.getElementById('loteProdutoId').value = produtoIdAtual;

    document.getElementById('loteQuantidadeInicial').value = '';
    document.getElementById('loteQuantidadeDisponivel').value = '';
    document.getElementById('loteValorUnitario').value = '';
    document.getElementById('loteDataEntrada').value = '';
    document.getElementById('loteObservacao').value = '';

    // Definir data atual como padrão
    const agora = new Date();
    const dataFormatada = agora.toISOString().slice(0, 16);
    document.getElementById('loteDataEntrada').value = dataFormatada;

    calcularValoresLote();

    // Debug
    console.log('Formulário limpo - produtoId:', produtoIdAtual);
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

    // Adicionar classe de warning se quantidade disponível > quantidade inicial
    const quantidadeDisponivelInput = document.getElementById('loteQuantidadeDisponivel');
    if (quantidadeDisponivelInput) {
        if (quantidadeDisponivel > quantidadeInicial) {
            quantidadeDisponivelInput.classList.add('is-invalid');
        } else {
            quantidadeDisponivelInput.classList.remove('is-invalid');
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
            console.error('Erro ao carregar dados do lote:', error);
            mostrarFlashMessage('Erro ao carregar dados do lote', 'error');
        });
}

function excluirLote(loteId) {
    fetch(`${API_BASE_URL}/lotes/${loteId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (response.ok) {
                mostrarFlashMessage('Lote excluído com sucesso', 'success');
                fecharModal('confirmarExclusaoLoteModal');

                // Recarregar dados conforme o contexto
                if (lotesProdutoAtual) {
                    // Se estamos no modal de produto específico
                    carregarLotesProduto(lotesProdutoAtual);
                    carregarResumoProduto(lotesProdutoAtual);
                } else {
                    // Se estamos na aba geral de lotes
                    carregarTodosLotes();
                }
            } else {
                return response.json().then(data => {
                    throw new Error(data.error || 'Erro ao excluir lote');
                });
            }
        })
        .catch(error => {
            console.error('Erro ao excluir lote:', error);
            mostrarFlashMessage(error.message || 'Erro ao excluir lote', 'error');
        });
}

function salvarLote() {
    const formData = new FormData(document.getElementById('editarLoteForm'));

    // Obter o produto_id - priorizar o contexto atual ou o valor do formulário
    let produtoId = formData.get('loteProdutoId');

    // Se não há produto_id no formulário, usar o contexto atual
    if (!produtoId && lotesProdutoAtual) {
        produtoId = lotesProdutoAtual;
    }

    // Preparar dados para envio - ENVIAR TODOS OS CAMPOS COM VALORES PADRÃO
    const dados = {
        produto_id: parseInt(produtoId),
        quantidade_inicial: parseFloat(formData.get('loteQuantidadeInicial')) || 0,
        quantidade_disponivel: parseFloat(formData.get('loteQuantidadeDisponivel')) || 0,
        valor_unitario_compra: parseFloat(formData.get('loteValorUnitario')) || 0,
        observacao: formData.get('loteObservacao') || ''
    };

    // Data de entrada - usar atual se não fornecida
    const dataEntrada = formData.get('loteDataEntrada');
    if (dataEntrada) {
        dados.data_entrada = dataEntrada;
    } else {
        // Se não há data, usar data atual
        const now = new Date();
        dados.data_entrada = now.toISOString().slice(0, 16); // Formato YYYY-MM-DDTHH:mm
    }

    const loteId = formData.get('loteId');
    const url = loteId ? `${API_BASE_URL}/lotes/${loteId}` : `${API_BASE_URL}/lotes`;
    const method = loteId ? 'PUT' : 'POST';

    // Mostrar loading
    const submitBtn = document.querySelector('#editarLoteForm button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
    submitBtn.disabled = true;

    // Debug
    console.log('Enviando dados para API:', {
        url: url,
        method: method,
        dados: dados,
        loteId: loteId
    });

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dados)
    })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                return response.json().then(data => {
                    throw new Error(data.error || `Erro ${response.status}: ${response.statusText}`);
                });
            }
        })
        .then(data => {
            mostrarFlashMessage(
                loteId ? 'Lote atualizado com sucesso' : 'Lote criado com sucesso',
                'success'
            );
            fecharModal('editarLoteModal');

            // Recarregar dados conforme o contexto
            if (lotesProdutoAtual) {
                carregarLotesProduto(lotesProdutoAtual);
                carregarResumoProduto(lotesProdutoAtual);
            } else {
                carregarTodosLotes();
            }
        })
        .catch(error => {
            console.error('Erro ao salvar lote:', error);
            mostrarFlashMessage(error.message || 'Erro ao salvar lote', 'error');
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
    // Botão novo lote na aba geral
    const addLoteBtn = document.getElementById('addLote');
    if (addLoteBtn) {
        addLoteBtn.addEventListener('click', () => {
            // Na aba geral, não temos um produto específico
            lotesProdutoAtual = null;
            abrirModalNovoLote();
        });
    }

    // Botão refresh lotes na aba geral
    const refreshLotesBtn = document.getElementById('refreshLotes');
    if (refreshLotesBtn) {
        refreshLotesBtn.addEventListener('click', () => {
            carregarTodosLotes();
        });
    }

    // Botão novo lote no modal de produto
    const btnNovoLote = document.getElementById('btnNovoLote');
    if (btnNovoLote) {
        btnNovoLote.addEventListener('click', () => {
            // No modal de produto, temos o contexto definido
            abrirModalEditarLote();
        });
    }

    // Botão refresh lotes no modal de produto
    const refreshLotesModalBtn = document.getElementById('refreshLotes');
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

// Função para mostrar mensagens flash (se não existir)
function mostrarFlashMessage(mensagem, tipo = 'info') {
    // Implementação básica - adapte conforme seu sistema
    console.log(`[${tipo.toUpperCase()}] ${mensagem}`);
    // Aqui você pode integrar com seu sistema de flash messages existente
    // Exemplo básico:
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

// Adicionar função para selecionar produto quando estiver na aba geral
function selecionarProdutoParaLote(produtoId, produtoNome) {
    lotesProdutoAtual = produtoId;
    document.getElementById('loteProdutoId').value = produtoId;
    mostrarFlashMessage(`Produto selecionado: ${produtoNome}`, 'success');
}