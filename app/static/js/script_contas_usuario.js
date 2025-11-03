// Configurações globais
const API_BASE_URL = '/admin';
let usuarios = [];
let contas = [];
let formasPagamento = [];
let usuarioSelecionado = null;

// Inicialização da aplicação
document.addEventListener('DOMContentLoaded', function () {
    inicializarApp();
    configurarEventListeners();
    carregarDadosIniciais();
});

// Funções de inicialização
function inicializarApp() {
    inicializarDatasPadrao();
}

function configurarEventListeners() {
    // Filtros
    document.getElementById('btnFiltrar').addEventListener('click', aplicarFiltros);
    document.getElementById('searchInput').addEventListener('input', filtrarOperadores);

    // Transferências
    document.getElementById('btnConfirmarTransferencia').addEventListener('click', realizarTransferencia);

    // Relatórios
    document.getElementById('btnGerarRelatorio').addEventListener('click', gerarRelatorio);
    document.getElementById('btnExportarPdf').addEventListener('click', exportarPDF);

    // Detalhes do usuário
    document.getElementById('fecharDetalhes').addEventListener('click', fecharDetalhesUsuario);
    document.getElementById('refreshSaldo').addEventListener('click', carregarDadosIniciais);

    // Modais
    configurarModais();
}

function configurarModais() {
    // Fechar modais ao clicar no overlay ou no X
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function (e) {
            if (e.target.classList.contains('modal-overlay') || e.target.closest('.close-modal')) {
                fecharModal(modal.id);
            }
        });
    });

    // Configurar botões de cancelar nos modais
    document.querySelectorAll('.btn-outline[data-modal]').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const modalId = this.getAttribute('data-modal');
            fecharModal(modalId);
        });
    });

    // Configurar tecla ESC para fechar modais
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            fecharModalAberto();
        }
    });

    // Configurar botões de ação nos cards
    document.addEventListener('click', function (e) {
        if (e.target.closest('.btn-entrada')) {
            const card = e.target.closest('.metric-card');
            const usuarioId = card.getAttribute('data-usuario-id');
            abrirModalEntrada(usuarioId);
        }

        if (e.target.closest('.btn-saida')) {
            const card = e.target.closest('.metric-card');
            const usuarioId = card.getAttribute('data-usuario-id');
            abrirModalSaida(usuarioId);
        }

        if (e.target.closest('.btn-transferencia')) {
            const card = e.target.closest('.metric-card');
            const usuarioId = card.getAttribute('data-usuario-id');
            abrirModalTransferencia(usuarioId);
        }

        if (e.target.closest('.btn-relatorio')) {
            const card = e.target.closest('.metric-card');
            const usuarioId = card.getAttribute('data-usuario-id');
            gerarRelatorioIndividual(usuarioId);
        }
    });

    // Confirmar ações
    document.getElementById('btnConfirmarEntrada').addEventListener('click', confirmarEntrada);
    document.getElementById('btnConfirmarSaida').addEventListener('click', confirmarSaida);

    // Event listeners para atualizar saldos no modal de transferência
    document.getElementById('transferenciaContaOrigem').addEventListener('change', atualizarSaldoOrigem);
    document.getElementById('transferenciaContaDestino').addEventListener('change', atualizarSaldoDestino);
}

// Funções de API
async function carregarDadosIniciais() {
    try {
        mostrarLoading(true);

        await Promise.all([
            carregarUsuarios(),
            carregarContas(),
            carregarFormasPagamento()
        ]);
        atualizarCardsOperadores();
        atualizarFiltros();

        mostrarMensagem('Dados carregados com sucesso!', 'success');
    } catch (error) {
        mostrarMensagem('Erro ao carregar dados: ' + error.message, 'error');
    } finally {
        mostrarLoading(false);
    }
}

async function carregarUsuarios() {
    try {
        const response = await fetch(`${API_BASE_URL}/usuarios`);

        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.usuarios) {
            usuarios = data.usuarios.map(usuario => ({
                ...usuario,
                id: parseInt(usuario.id) // Garantir que id é número
            }));
        } else {
            throw new Error(data.message || 'Estrutura de dados inválida');
        }
    } catch (error) {
        usuarios = [];
        throw error;
    }
}

async function carregarContas() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/contas-usuario`);

        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.contas) {
            contas = data.contas.map(conta => ({
                ...conta,
                id: parseInt(conta.id),
                usuario_id: parseInt(conta.usuario_id)
            }));
        } else {
            throw new Error(data.error || 'Estrutura de dados inválida');
        }
    } catch (error) {
        contas = [];
        throw error;
    }
}

async function carregarFormasPagamento() {
    // Carregar formas de pagamento do enum
    formasPagamento = [
        { value: 'pix_fabiano', label: 'PIX Fabiano' },
        { value: 'pix_maquineta', label: 'PIX Maquineta' },
        { value: 'pix_edfrance', label: 'PIX Edfranci' },
        { value: 'pix_loja', label: 'PIX Loja' },
        { value: 'dinheiro', label: 'Dinheiro' },
        { value: 'cartao_credito', label: 'Cartão de Crédito' },
        { value: 'cartao_debito', label: 'Cartão de Débito' }
    ];
}

// Funções de exibição
function atualizarCardsOperadores() {
    const grid = document.getElementById('operadoresGrid');
    grid.innerHTML = '';

    if (contas.length === 0) {
        grid.innerHTML = '<div class="no-data-message">Nenhuma conta encontrada</div>';
        return;
    }

    let cardsCriados = 0;
    let usuariosSemConta = [];

    // Primeiro, verificar todos os usuários que têm contas
    usuarios.forEach(usuario => {
        const conta = contas.find(c => c.usuario_id === usuario.id);
        if (!conta) {
            usuariosSemConta.push(usuario.nome);
        }
    });
    contas.forEach(conta => {
        // Converter para número para garantir comparação correta
        const usuarioId = parseInt(conta.usuario_id);
        const usuario = usuarios.find(u => parseInt(u.id) === usuarioId);

        if (!usuario) {
            return;
        }

        const card = document.createElement('div');
        card.className = 'metric-card';
        card.setAttribute('data-usuario-id', usuario.id.toString());
        card.setAttribute('data-conta-id', conta.id.toString());

        // Usar o campo raw para comparação numérica correta
        const saldoTotalRaw = conta.saldo_total_raw || 0;
        const saldoTotalFormatado = conta.saldo_total || 'R$ 0,00';
        const classeSaldo = saldoTotalRaw >= 0 ? 'positivo' : 'negativo';

        // Formatar saldos por forma de pagamento
        const saldosFormaPagamento = conta.saldos_por_forma_pagamento || {};

        const formasPagamentoHTML = Object.entries(saldosFormaPagamento)
            .map(([forma, saldo]) => {
                const saldoFormatado = saldo;
                const formaLabel = formasPagamento.find(fp => fp.value === forma)?.label || forma;
                return `<span class="badge badge-primary" title="${formaLabel}">${formaLabel}: ${saldoFormatado}</span>`;
            })
            .join('');

        card.innerHTML = `
            <div class="metric-icon">
                <i class="fas fa-user"></i>
            </div>
            <div class="metric-info">
                <h3>${usuario.nome}</h3>
                <div class="value valor-saldo ${classeSaldo}">${saldoTotalFormatado}</div>
                <div class="formas-pagamento">
                    ${formasPagamentoHTML || '<span class="text-muted">Nenhum saldo específico</span>'}
                </div>
                <div class="card-actions">
                    <button class="btn btn-success btn-sm btn-entrada" title="Registrar Entrada">
                        <i class="fas fa-plus-circle"></i>
                        Entrada
                    </button>
                    <button class="btn btn-danger btn-sm btn-saida" title="Registrar Saída">
                        <i class="fas fa-minus-circle"></i>
                        Saída
                    </button>
                    <button class="btn btn-primary btn-sm btn-transferencia" title="Transferir">
                        <i class="fas fa-exchange-alt"></i>
                        Transferir
                    </button>
                    <button class="btn btn-warning btn-sm btn-relatorio" title="Relatório PDF">
                        <i class="fas fa-file-pdf"></i>
                        PDF
                    </button>
                </div>
            </div>
        `;

        card.addEventListener('click', (e) => {
            // Não abrir detalhes se clicou em um botão de ação
            if (!e.target.closest('.card-actions')) {
                toggleDetalhesUsuario(usuario.id);
            }
        });

        grid.appendChild(card);
        cardsCriados++;
    });

    if (cardsCriados === 0) {
        grid.innerHTML = '<div class="no-data-message">Nenhum operador com conta encontrado</div>';
    }
}

function toggleDetalhesUsuario(usuarioId) {
    if (usuarioSelecionado === usuarioId) {
        fecharDetalhesUsuario();
    } else {
        mostrarDetalhesUsuario(usuarioId);
    }
}

function mostrarDetalhesUsuario(usuarioId) {
    // Converter para número para garantir comparação correta
    const usuarioIdNum = parseInt(usuarioId);
    const conta = contas.find(c => parseInt(c.usuario_id) === usuarioIdNum);
    const usuario = usuarios.find(u => parseInt(u.id) === usuarioIdNum);

    if (!conta || !usuario) {
        mostrarMensagem('Erro ao carregar detalhes do usuário', 'error');
        return;
    }

    usuarioSelecionado = usuarioId;

    // Atualizar informações básicas
    document.getElementById('detalhesUsuarioNome').textContent = usuario.nome;
    document.getElementById('detalhesSaldoTotal').textContent = `${conta.saldo_total || 0}`;
    document.getElementById('detalhesAtualizadoEm').textContent =
        conta.atualizado_em ? new Date(conta.atualizado_em).toLocaleString('pt-BR') : '-';

    // Atualizar saldos por forma de pagamento
    const saldosContainer = document.getElementById('saldosFormaPagamento');
    saldosContainer.innerHTML = '';

    const saldosFormaPagamento = conta.saldos_por_forma_pagamento || {};
    Object.entries(saldosFormaPagamento).forEach(([forma, saldo]) => {
        const formaLabel = formasPagamento.find(fp => fp.value === forma)?.label || forma;
        const saldoItem = document.createElement('div');
        saldoItem.className = 'detail-item';
        saldoItem.innerHTML = `
            <label>${formaLabel}</label>
            <div class="value monetary">${saldo}</div>
        `;
        saldosContainer.appendChild(saldoItem);
    });

    if (Object.keys(saldosFormaPagamento).length === 0) {
        saldosContainer.innerHTML = '<div class="no-data-message">Nenhum saldo por forma de pagamento</div>';
    }

    // Carregar histórico de movimentações
    carregarHistoricoMovimentacoes(conta.id);

    // Mostrar seção de detalhes
    document.getElementById('detalhesUsuario').style.display = 'block';
}

function fecharDetalhesUsuario() {
    document.getElementById('detalhesUsuario').style.display = 'none';
    usuarioSelecionado = null;
}

async function carregarHistoricoMovimentacoes(contaId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/contas-usuario/${contaId}/movimentacoes`);

        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }

        const data = await response.json();
        const movimentacoes = data.movimentacoes || [];
        const tbody = document.querySelector('#historicoMovimentacoes tbody');
        tbody.innerHTML = '';

        if (movimentacoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="no-data-message">Nenhuma movimentação encontrada</td></tr>';
            return;
        }

        movimentacoes.forEach(mov => {
            const tr = document.createElement('tr');
            const dataFormatada = mov.data ? new Date(mov.data).toLocaleString('pt-BR') : '-';
            const tipoMap = {
                entrada: { classe: 'badge-success', texto: 'Entrada' },
                saida: { classe: 'badge-danger', texto: 'Saída' },
                transferencia: { classe: 'badge-warning', texto: 'Transferência' }
            };

            const tipoClasse = tipoMap[mov.tipo]?.classe || 'badge-secondary';
            const tipoTexto = tipoMap[mov.tipo]?.texto || 'Desconhecido';

            tr.innerHTML = `
                <td>${dataFormatada}</td>
                <td><span class="badge ${tipoClasse}">${tipoTexto}</span></td>
                <td>${formasPagamento.find(fp => fp.value === mov.forma_pagamento)?.label || mov.forma_pagamento}</td>
                <td class="monetary">${mov.valor || 0}</td>
                <td>${mov.descricao || '-'}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        const tbody = document.querySelector('#historicoMovimentacoes tbody');
        tbody.innerHTML = '<tr><td colspan="5" class="no-data-message">Erro ao carregar histórico</td></tr>';
    }
}

// Funções de Modal
function abrirModalEntrada(usuarioId) {
    // Converter para número para garantir comparação correta
    const usuarioIdNum = parseInt(usuarioId);
    const conta = contas.find(c => parseInt(c.usuario_id) === usuarioIdNum);
    const usuario = usuarios.find(u => parseInt(u.id) === usuarioIdNum);

    if (!conta || !usuario) {
        mostrarMensagem('Conta ou usuário não encontrado', 'error');
        return;
    }

    document.getElementById('entradaContaId').value = conta.id;

    // Preencher formas de pagamento
    const selectFormaPagamento = document.getElementById('entradaFormaPagamento');
    selectFormaPagamento.innerHTML = '<option value="">Selecione a forma de pagamento</option>';
    formasPagamento.forEach(forma => {
        const option = document.createElement('option');
        option.value = forma.value;
        option.textContent = forma.label;
        selectFormaPagamento.appendChild(option);
    });

    // Limpar formulário
    document.getElementById('entradaValor').value = '';
    document.getElementById('entradaDescricao').value = 'Entrada na conta';

    // Mostrar modal
    abrirModal('modalEntrada');
}

function abrirModalSaida(usuarioId) {
    // Converter para número para garantir comparação correta
    const usuarioIdNum = parseInt(usuarioId);
    const conta = contas.find(c => parseInt(c.usuario_id) === usuarioIdNum);
    const usuario = usuarios.find(u => parseInt(u.id) === usuarioIdNum);

    if (!conta || !usuario) {
        mostrarMensagem('Conta ou usuário não encontrado', 'error');
        return;
    }

    document.getElementById('saidaContaId').value = conta.id;

    // Preencher formas de pagamento
    const selectFormaPagamento = document.getElementById('saidaFormaPagamento');
    selectFormaPagamento.innerHTML = '<option value="">Selecione a forma de pagamento</option>';
    formasPagamento.forEach(forma => {
        const option = document.createElement('option');
        option.value = forma.value;
        option.textContent = forma.label;
        selectFormaPagamento.appendChild(option);
    });

    // Limpar formulário
    document.getElementById('saidaValor').value = '';
    document.getElementById('saidaDescricao').value = 'Saída da conta';

    // Mostrar modal
    abrirModal('modalSaida');
}

function abrirModalTransferencia(usuarioId) {
    // Converter para número para garantir comparação correta
    const usuarioIdNum = parseInt(usuarioId);
    const conta = contas.find(c => parseInt(c.usuario_id) === usuarioIdNum);

    if (!conta) {
        mostrarMensagem('Conta não encontrada', 'error');
        return;
    }

    // Preencher selects de contas
    const selectOrigem = document.getElementById('transferenciaContaOrigem');
    const selectDestino = document.getElementById('transferenciaContaDestino');

    selectOrigem.innerHTML = '<option value="">Selecione a conta de origem</option>';
    selectDestino.innerHTML = '<option value="">Selecione a conta de destino</option>';

    contas.forEach(contaItem => {
        const usuario = usuarios.find(u => u.id === contaItem.usuario_id);
        if (usuario) {
            const option = document.createElement('option');
            option.value = contaItem.id;
            option.textContent = `${usuario.nome}:(${contaItem.saldo_total || 0})`;

            const optionOrigem = option.cloneNode(true);
            const optionDestino = option.cloneNode(true);

            selectOrigem.appendChild(optionOrigem);
            selectDestino.appendChild(optionDestino);
        }
    });

    // Preencher forma de pagamento
    const selectFormaPagamento = document.getElementById('transferenciaFormaPagamento');
    selectFormaPagamento.innerHTML = '<option value="">Selecione a forma de pagamento</option>';
    formasPagamento.forEach(forma => {
        const option = document.createElement('option');
        option.value = forma.value;
        option.textContent = forma.label;
        selectFormaPagamento.appendChild(option);
    });

    // Definir conta de origem como a conta selecionada
    selectOrigem.value = conta.id;
    atualizarSaldoOrigem();

    // Limpar outros campos
    document.getElementById('transferenciaValor').value = '';
    document.getElementById('transferenciaDescricao').value = 'Transferência entre contas';

    abrirModal('modalTransferencia');
}

function atualizarSaldoOrigem() {
    const contaId = document.getElementById('transferenciaContaOrigem').value;
    const saldoInfo = document.getElementById('saldoOrigemInfo');

    if (contaId) {
        const conta = contas.find(c => c.id == contaId);
        if (conta) {
            const saldo = conta.saldo_total || 0;
            saldoInfo.innerHTML = `<small class="text-info">Saldo disponível: ${saldo}</small>`;
        }
    } else {
        saldoInfo.innerHTML = '';
    }
}

function atualizarSaldoDestino() {
    const contaId = document.getElementById('transferenciaContaDestino').value;
    const saldoInfo = document.getElementById('saldoDestinoInfo');

    if (contaId) {
        const conta = contas.find(c => c.id == contaId);
        if (conta) {
            const saldo = conta.saldo_total || 0;
            saldoInfo.innerHTML = `<small class="text-info">Saldo atual: ${saldo}</small>`;
        }
    } else {
        saldoInfo.innerHTML = '';
    }
}

function abrirModal(modalId) {
    document.getElementById(modalId).classList.add('active');
    document.body.style.overflow = 'hidden';
}

function fecharModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    document.body.style.overflow = 'auto';
}

function fecharModalAberto() {
    const modalAberto = document.querySelector('.modal.active');
    if (modalAberto) {
        fecharModal(modalAberto.id);
    }
}

// Funções de ação
async function confirmarEntrada() {
    try {
        const contaId = document.getElementById('entradaContaId').value;
        const formaPagamento = document.getElementById('entradaFormaPagamento').value;
        const valor = parseFloat(document.getElementById('entradaValor').value);
        const descricao = document.getElementById('entradaDescricao').value;

        // Validações
        if (!contaId || !formaPagamento || !valor || !descricao) {
            mostrarMensagem('Preencha todos os campos obrigatórios', 'error');
            return;
        }

        if (valor <= 0) {
            mostrarMensagem('O valor deve ser positivo', 'error');
            return;
        }

        mostrarLoading(true);

        const response = await fetch(`${API_BASE_URL}/conta/entrada`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                conta_id: parseInt(contaId),
                forma_pagamento: formaPagamento,
                valor: valor,
                descricao: descricao
            })
        });

        const resultado = await response.json();

        if (!response.ok) {
            throw new Error(resultado.error || 'Erro ao registrar entrada');
        }

        mostrarMensagem('Entrada registrada com sucesso!', 'success');
        fecharModal('modalEntrada');

        // Atualizar dados
        await carregarDadosIniciais();

    } catch (error) {
        mostrarMensagem(error.message, 'error');
    } finally {
        mostrarLoading(false);
    }
}

async function confirmarSaida() {
    try {
        const contaId = document.getElementById('saidaContaId').value;
        const formaPagamento = document.getElementById('saidaFormaPagamento').value;
        const valor = parseFloat(document.getElementById('saidaValor').value);
        const descricao = document.getElementById('saidaDescricao').value;

        // Validações
        if (!contaId || !formaPagamento || !valor || !descricao) {
            mostrarMensagem('Preencha todos os campos obrigatórios', 'error');
            return;
        }

        if (valor <= 0) {
            mostrarMensagem('O valor deve ser positivo', 'error');
            return;
        }

        mostrarLoading(true);

        const response = await fetch(`${API_BASE_URL}/conta/saida`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                conta_id: parseInt(contaId),
                forma_pagamento: formaPagamento,
                valor: valor,
                descricao: descricao
            })
        });

        const resultado = await response.json();

        if (!response.ok) {
            throw new Error(resultado.error || 'Erro ao registrar saída');
        }

        mostrarMensagem('Saída registrada com sucesso!', 'success');
        fecharModal('modalSaida');

        // Atualizar dados
        await carregarDadosIniciais();

    } catch (error) {
        mostrarMensagem(error.message, 'error');
    } finally {
        mostrarLoading(false);
    }
}

async function realizarTransferencia() {
    const dados = {
        conta_origem_id: parseInt(document.getElementById('transferenciaContaOrigem').value),
        conta_destino_id: parseInt(document.getElementById('transferenciaContaDestino').value),
        forma_pagamento: document.getElementById('transferenciaFormaPagamento').value,
        valor: parseFloat(document.getElementById('transferenciaValor').value),
        descricao: document.getElementById('transferenciaDescricao').value
    };

    // Validações
    if (!dados.conta_origem_id || !dados.conta_destino_id || !dados.forma_pagamento || !dados.valor) {
        mostrarMensagem('Preencha todos os campos obrigatórios', 'error');
        return;
    }

    if (dados.conta_origem_id === dados.conta_destino_id) {
        mostrarMensagem('Não é possível transferir para a mesma conta', 'error');
        return;
    }

    if (dados.valor <= 0) {
        mostrarMensagem('O valor da transferência deve ser positivo', 'error');
        return;
    }

    // Verificar saldo suficiente
    const contaOrigem = contas.find(c => c.id == dados.conta_origem_id);
    if (contaOrigem && parseFloat(contaOrigem.saldo_total) < dados.valor) {
        mostrarMensagem('Saldo insuficiente na conta de origem', 'error');
        return;
    }

    try {
        mostrarLoading(true);

        const response = await fetch(`${API_BASE_URL}/conta/transferir`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dados)
        });

        const resultado = await response.json();

        if (!response.ok) {
            throw new Error(resultado.error || 'Erro ao realizar transferência');
        }

        mostrarMensagem('Transferência realizada com sucesso!', 'success');
        fecharModal('modalTransferencia');

        // Atualizar dados
        await carregarDadosIniciais();

    } catch (error) {
        mostrarMensagem(error.message, 'error');
    } finally {
        mostrarLoading(false);
    }
}

async function gerarRelatorioIndividual(usuarioId) {
    try {
        // Converter para número para garantir comparação correta
        const usuarioIdNum = parseInt(usuarioId);
        const conta = contas.find(c => parseInt(c.usuario_id) === usuarioIdNum);
        const usuario = usuarios.find(u => parseInt(u.id) === usuarioIdNum);

        if (!conta || !usuario) {
            mostrarMensagem('Conta ou usuário não encontrado', 'error');
            return;
        }

        mostrarLoading(true);

        const hoje = new Date().toISOString().split('T')[0];
        const primeiroDiaMes = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];

        const filtros = {
            conta_id: conta.id,
            data_inicio: primeiroDiaMes,
            data_fim: hoje
        };

        const response = await fetch(`${API_BASE_URL}/api/relatorios/movimentacoes-contas-usuario/pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(filtros)
        });

        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }

        const blob = await response.blob();

        if (blob.size === 0) {
            throw new Error('PDF vazio gerado');
        }

        // Abrir PDF em nova aba
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');

        // Limpar URL após um tempo
        setTimeout(() => window.URL.revokeObjectURL(url), 1000);

        mostrarMensagem('PDF gerado com sucesso!', 'success');

    } catch (error) {
        mostrarMensagem(error.message, 'error');
    } finally {
        mostrarLoading(false);
    }
}

// Funções de filtro
function aplicarFiltros() {
    const contaId = document.getElementById('filterConta').value;
    const usuarioId = document.getElementById('filterUsuario').value;
    const dataInicio = document.getElementById('filterDataInicio').value;
    const dataFim = document.getElementById('filterDataFim').value;

    // Aplicar filtros nos cards
    const cards = document.querySelectorAll('.metric-card');

    cards.forEach(card => {
        const cardUsuarioId = card.getAttribute('data-usuario-id');
        const usuario = usuarios.find(u => u.id == cardUsuarioId);
        const conta = contas.find(c => c.usuario_id == cardUsuarioId);

        let mostrar = true;

        // Filtro por conta
        if (contaId && conta && conta.id != contaId) {
            mostrar = false;
        }

        // Filtro por usuário
        if (usuarioId && usuario && usuario.id != usuarioId) {
            mostrar = false;
        }

        card.style.display = mostrar ? 'flex' : 'none';
    });

    // Se há um usuário selecionado, verificar se ele ainda deve ser mostrado
    if (usuarioSelecionado) {
        const usuarioFiltrado = usuarios.find(u => u.id == usuarioSelecionado);
        const contaFiltrada = contas.find(c => c.usuario_id == usuarioSelecionado);

        let usuarioDeveSerMostrado = true;

        if (contaId && contaFiltrada && contaFiltrada.id != contaId) {
            usuarioDeveSerMostrado = false;
        }

        if (usuarioId && usuarioFiltrado && usuarioFiltrado.id != usuarioId) {
            usuarioDeveSerMostrado = false;
        }

        if (!usuarioDeveSerMostrado) {
            fecharDetalhesUsuario();
        }
    }

    mostrarMensagem('Filtros aplicados com sucesso!', 'success');
}

function filtrarOperadores() {
    const termo = document.getElementById('searchInput').value.toLowerCase();
    const cards = document.querySelectorAll('.metric-card');

    cards.forEach(card => {
        const usuarioId = card.getAttribute('data-usuario-id');
        const usuario = usuarios.find(u => u.id == usuarioId);
        const nome = usuario ? usuario.nome.toLowerCase() : '';
        card.style.display = nome.includes(termo) ? 'flex' : 'none';
    });
}

function atualizarFiltros() {
    // Atualizar filtro de contas
    const selectConta = document.getElementById('filterConta');
    selectConta.innerHTML = '<option value="">Todas as contas</option>';
    contas.forEach(conta => {
        const usuario = usuarios.find(u => u.id === conta.usuario_id);
        if (usuario) {
            const option = document.createElement('option');
            option.value = conta.id;
            option.textContent = `${usuario.nome} (${conta.id})`;
            selectConta.appendChild(option);
        }
    });

    // Atualizar filtro de usuários
    const selectUsuario = document.getElementById('filterUsuario');
    selectUsuario.innerHTML = '<option value="">Todos os usuários</option>';
    usuarios.forEach(usuario => {
        const option = document.createElement('option');
        option.value = usuario.id;
        option.textContent = usuario.nome;
        selectUsuario.appendChild(option);
    });

    // Atualizar formas de pagamento nos selects
    const selectsFormaPagamento = document.querySelectorAll('select[id*="FormaPagamento"]');
    selectsFormaPagamento.forEach(select => {
        select.innerHTML = '<option value="">Selecione a forma de pagamento</option>';
        formasPagamento.forEach(forma => {
            const option = document.createElement('option');
            option.value = forma.value;
            option.textContent = forma.label;
            select.appendChild(option);
        });
    });

    // Atualizar selects de transferência
    const selectOrigem = document.getElementById('transferenciaContaOrigem');
    const selectDestino = document.getElementById('transferenciaContaDestino');

    selectOrigem.innerHTML = '<option value="">Selecione a conta de origem</option>';
    selectDestino.innerHTML = '<option value="">Selecione a conta de destino</option>';

    contas.forEach(conta => {
        const usuario = usuarios.find(u => u.id === conta.usuario_id);
        if (usuario) {
            const option = document.createElement('option');
            option.value = conta.id;
            option.textContent = `${usuario.nome} (Saldo: R$ ${parseFloat(conta.saldo_total || 0).toFixed(2)})`;

            const optionOrigem = option.cloneNode(true);
            const optionDestino = option.cloneNode(true);

            selectOrigem.appendChild(optionOrigem);
            selectDestino.appendChild(optionDestino);
        }
    });

    // Atualizar filtros de relatório
    const relatorioConta = document.getElementById('relatorioConta');
    const relatorioUsuario = document.getElementById('relatorioUsuario');

    relatorioConta.innerHTML = '<option value="">Todas as contas</option>';
    relatorioUsuario.innerHTML = '<option value="">Todos os usuários</option>';

    contas.forEach(conta => {
        const usuario = usuarios.find(u => u.id === conta.usuario_id);
        if (usuario) {
            const optionConta = document.createElement('option');
            optionConta.value = conta.id;
            optionConta.textContent = `${usuario.nome} (${conta.id})`;
            relatorioConta.appendChild(optionConta);
        }
    });

    usuarios.forEach(usuario => {
        const optionUsuario = document.createElement('option');
        optionUsuario.value = usuario.id;
        optionUsuario.textContent = usuario.nome;
        relatorioUsuario.appendChild(optionUsuario);
    });

}

// Funções de relatório
async function gerarRelatorio() {
    try {
        mostrarLoading(true);

        const filtros = {
            conta_id: document.getElementById('relatorioConta').value || null,
            usuario_id: document.getElementById('relatorioUsuario').value || null,
            data_inicio: document.getElementById('relatorioDataInicio').value || null,
            data_fim: document.getElementById('relatorioDataFim').value || null
        };

        // Remover filtros vazios
        Object.keys(filtros).forEach(key => {
            if (!filtros[key]) delete filtros[key];
        });

        const queryString = new URLSearchParams(filtros).toString();
        const response = await fetch(`${API_BASE_URL}/api/relatorios/movimentacoes-contas-usuario?${queryString}`);

        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Erro ao gerar relatório');
        }

        preencherTabelaRelatorio(data.dados || []);
        mostrarMensagem('Relatório gerado com sucesso!', 'success');

    } catch (error) {
        mostrarMensagem(error.message, 'error');
    } finally {
        mostrarLoading(false);
    }
}

function preencherTabelaRelatorio(dados) {
    const tbody = document.querySelector('#tabelaRelatorio tbody');
    tbody.innerHTML = '';

    if (dados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="no-data-message">Nenhum dado encontrado para os filtros aplicados</td></tr>';
        return;
    }

    dados.forEach(item => {
        const tr = document.createElement('tr');
        const saldo = parseFloat(item.entradas || 0) - parseFloat(item.saidas || 0);
        const classeSaldo = saldo >= 0 ? 'positivo' : 'negativo';
        const dataFormatada = item.data ? new Date(item.data).toLocaleDateString('pt-BR') : '-';

        tr.innerHTML = `
            <td>${item.usuario_nome || '-'}</td>
            <td>${item.conta_id || '-'}</td>
            <td>${formasPagamento.find(fp => fp.value === item.forma_pagamento)?.label || item.forma_pagamento || '-'}</td>
            <td class="monetary">R$ ${parseFloat(item.entradas || 0).toFixed(2)}</td>
            <td class="monetary">R$ ${parseFloat(item.saidas || 0).toFixed(2)}</td>
            <td class="monetary valor-saldo ${classeSaldo}">
                R$ ${saldo}
            </td>
            <td>${dataFormatada}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function exportarPDF() {
    try {
        mostrarLoading(true);

        const filtros = {
            data_inicio: document.getElementById('relatorioDataInicio').value,
            data_fim: document.getElementById('relatorioDataFim').value,
            conta_id: document.getElementById('relatorioConta').value,
            usuario_id: document.getElementById('relatorioUsuario').value
        };

        // Remover filtros vazios
        Object.keys(filtros).forEach(key => {
            if (!filtros[key]) delete filtros[key];
        });

        const response = await fetch(`${API_BASE_URL}/api/relatorios/movimentacoes-contas-usuario/pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(filtros)
        });

        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }

        const blob = await response.blob();

        if (blob.size === 0) {
            throw new Error('PDF vazio gerado');
        }

        // Abrir PDF em nova aba
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');

        // Limpar URL após um tempo
        setTimeout(() => window.URL.revokeObjectURL(url), 1000);

        mostrarMensagem('PDF gerado com sucesso!', 'success');

    } catch (error) {
        mostrarMensagem(error.message, 'error');
    } finally {
        mostrarLoading(false);
    }
}

// Funções utilitárias
function mostrarMensagem(mensagem, tipo = 'info') {
    // Criar elemento de mensagem
    const mensagemDiv = document.createElement('div');
    mensagemDiv.className = `flash-message ${tipo}`;
    mensagemDiv.innerHTML = `
        <div class="flash-content">
            <i class="fas fa-${getIconeTipo(tipo)}"></i>
            <span>${mensagem}</span>
        </div>
        <button class="close-flash">&times;</button>
    `;

    // Adicionar ao container de mensagens
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }

    container.appendChild(mensagemDiv);

    // Configurar auto-remover
    setTimeout(() => {
        mensagemDiv.classList.add('fade-out');
        setTimeout(() => {
            if (mensagemDiv.parentNode) {
                mensagemDiv.parentNode.removeChild(mensagemDiv);
            }
        }, 500);
    }, 5000);

    // Configurar botão de fechar
    mensagemDiv.querySelector('.close-flash').addEventListener('click', () => {
        mensagemDiv.classList.add('fade-out');
        setTimeout(() => {
            if (mensagemDiv.parentNode) {
                mensagemDiv.parentNode.removeChild(mensagemDiv);
            }
        }, 500);
    });
}

function getIconeTipo(tipo) {
    const icones = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icones[tipo] || 'info-circle';
}

function mostrarLoading(mostrar) {
    const loadingElement = document.getElementById('loadingOverlay');
    if (!loadingElement && mostrar) {
        const overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
        overlay.innerHTML = `
            <div style="background: var(--card-bg); padding: 20px; border-radius: 8px; display: flex; align-items: center; gap: 10px; color: var(--text-primary); border: 1px solid var(--border-color);">
                <div class="loading-spinner"></div>
                <span>Carregando...</span>
            </div>
        `;
        document.body.appendChild(overlay);
    } else if (loadingElement && !mostrar) {
        loadingElement.remove();
    }
}

// Inicializar data filters com datas padrão
function inicializarDatasPadrao() {
    const hoje = new Date().toISOString().split('T')[0];
    const primeiroDiaMes = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];

    document.getElementById('filterDataInicio').value = primeiroDiaMes;
    document.getElementById('filterDataFim').value = hoje;
    document.getElementById('relatorioDataInicio').value = primeiroDiaMes;
    document.getElementById('relatorioDataFim').value = hoje;
}

// Adicionar estilos CSS para loading spinner se não existirem
if (!document.querySelector('#loading-spinner-styles')) {
    const style = document.createElement('style');
    style.id = 'loading-spinner-styles';
    style.textContent = `
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: var(--primary-color);
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .no-data-message {
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-style: italic;
        }

        .card-actions {
            margin-top: 20px;
            display: flex;
            flex-wrap: wrap;        /* permite quebrar linha */
            justify-content: flex-end; /* alinha tudo à direita */
            gap: 5px;
        }

        .card-actions .btn {
            padding: 4px 8px;
            font-size: 0.75rem;
            flex: 0 0 calc(50% - 5px); /* dois por linha (50% da largura menos o gap) */
            min-width: 60px;
            box-sizing: border-box;
            text-align: center;
        }

        .modal.active {
            display: flex !important;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes fadeOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}