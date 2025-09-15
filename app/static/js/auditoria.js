document.addEventListener('DOMContentLoaded', function() {
    // Variáveis globais
    let paginaAtual = 1;
    const porPagina = 50;
    let filtrosAtuais = {};
    let logsCarregados = [];
    let totalPaginas = 1;

    // Elementos da DOM
    const tabelaAuditoria = document.getElementById('tabelaAuditoria');
    const tbodyAuditoria = tabelaAuditoria?.querySelector('tbody');
    const btnAplicarFiltros = document.getElementById('btnAplicarFiltros');
    const btnLimparFiltros = document.getElementById('btnLimparFiltros');
    const btnAnterior = document.getElementById('btnAnterior');
    const btnProximo = document.getElementById('btnProximo');
    const infoPaginacao = document.getElementById('infoPaginacao');
    const btnAtualizar = document.getElementById('btnAtualizar');
    const btnExportarCSV = document.getElementById('btnExportarCSV');
    const modalDetalhes = document.getElementById('detalhesLogModal');
    const btnFecharDetalhes = document.getElementById('btnFecharDetalhes');

    // Filtros
    const filtroTabela = document.getElementById('filtroTabela');
    const filtroAcao = document.getElementById('filtroAcao');
    const filtroUsuario = document.getElementById('filtroUsuario');
    const filtroDataInicio = document.getElementById('filtroDataInicio');
    const filtroDataFim = document.getElementById('filtroDataFim');

    // Elementos de estatísticas
    const totalRegistros = document.getElementById('totalRegistros');
    const totalInserts = document.getElementById('totalInserts');
    const totalUpdates = document.getElementById('totalUpdates');
    const totalDeletes = document.getElementById('totalDeletes');

    // Mapeamento de nomes de tabelas para nomes amigáveis
    const nomesTabelasAmigaveis = {
        'clientes': 'Clientes',
        'produtos': 'Produtos',
        'usuarios': 'Usuários',
        'transferencias_estoque': 'Transferências de Estoque',
        'descontos': 'Descontos',
        'contas_receber': 'Contas a Receber',
        'financeiro': 'Movimentações Financeiras',
        'pagamentos_contas_receber': 'Pagamentos de Contas',
        'notas_fiscais': 'Notas Fiscais',
        'pagamentos_nota_fiscal': 'Pagamentos de Notas',
        'nota_fiscal_itens': 'Itens de Notas Fiscais',
        'movimentacoes_estoque': 'Movimentações de Estoque',
        'caixas': 'Caixas'
    };

    // Mapeamento de campos para nomes amigáveis
    const camposAmigaveis = {
        'email': 'E-mail',
        'atualizado_em': 'Data de Atualização',
        'estoque_loja': 'Estoque da Loja',
        'ultimo_acesso': 'Último Acesso',
        'ativo': 'Status Ativo',
        'nome': 'Nome',
        'valor_aberto': 'Valor em Aberto',
        'data_pagamento': 'Data de Pagamento',
        'status': 'Situação',
        'observacoes': 'Observações',
        'valor': 'Valor',
        'quantidade_minima': 'Quantidade Mínima',
        'quantidade_maxima': 'Quantidade Máxima',
        'data_fechamento': 'Data de Fechamento',
        'valor_fechamento': 'Valor de Fechamento',
        'estoque_deposito': 'Estoque do Depósito',
        'observacao': 'Observação',
        'valor_total': 'Valor Total',
        'valor_desconto': 'Valor do Desconto',
        'quantidade': 'Quantidade',
        'valor_unitario': 'Valor Unitário',
        'forma_pagamento': 'Forma de Pagamento',
        'data_emissao': 'Data de Emissão',
        'cliente_id': 'Cliente',
        'usuario_id': 'Usuário',
        'produto_id': 'Produto',
        'id': 'ID',
        'codigo': 'Código',
        'tipo': 'Tipo',
        'marca': 'Marca',
        'unidade': 'Unidade',
        'peso_kg_por_saco': 'Peso por Saco (kg)',
        'pacotes_por_saco': 'Pacotes por Saco',
        'pacotes_por_fardo': 'Pacotes por Fardo',
        'estoque_minimo': 'Estoque Mínimo',
        'estoque_maximo': 'Estoque Máximo',
        'criado_em': 'Data de Criação',
        'sincronizado': 'Sincronizado',
        'categoria': 'Categoria',
        'descricao': 'Descrição',
        'data': 'Data',
        'conta_id': 'Conta',
        'caixa_id': 'Caixa',
        'valor_pago': 'Valor Pago',
        'operador_id': 'Operador',
        'chave_acesso': 'Chave de Acesso',
        'valor_recebido': 'Valor Recebido',
        'troco': 'Troco',
        'a_prazo': 'A Prazo',
        'nota_fiscal_id': 'Nota Fiscal',
        'nota_id': 'Nota',
        'estoque_origem': 'Estoque de Origem',
        'desconto_aplicado': 'Desconto Aplicado',
        'tipo_desconto': 'Tipo de Desconto',
        'pagamento_id': 'Pagamento',
        'conta_receber_id': 'Conta a Receber',
        'estoque_destino': 'Estoque de Destino',
        'valor_unitario_compra': 'Valor Unitário de Compra',
        'valor_total_compra': 'Valor Total de Compra',
        'imcs': 'IMCS',
        'estoque_fabrica': 'Estoque da Fábrica'
    };

    // Verificar se todos os elementos existem
    if (!tbodyAuditoria) {
        console.error('Erro: Tabela de auditoria não encontrada');
        return;
    }

    // Inicialização
    inicializarDataFiltros();
    carregarLogsAuditoria();
    configurarEventListeners();

    function inicializarDataFiltros() {
        const hoje = new Date();
        const seteDiasAtras = new Date();
        seteDiasAtras.setDate(hoje.getDate() - 7);
        
        if (filtroDataInicio) {
            filtroDataInicio.value = formatarDataParaInput(seteDiasAtras);
        }
        if (filtroDataFim) {
            filtroDataFim.value = formatarDataParaInput(hoje);
        }
    }

    function formatarDataParaInput(data) {
        return data.toISOString().split('T')[0];
    }

    function configurarEventListeners() {
        // Filtros
        if (btnAplicarFiltros) {
            btnAplicarFiltros.addEventListener('click', aplicarFiltros);
        }
        if (btnLimparFiltros) {
            btnLimparFiltros.addEventListener('click', limparFiltros);
        }
        
        // Paginação
        if (btnAnterior) {
            btnAnterior.addEventListener('click', () => mudarPagina(paginaAtual - 1));
        }
        if (btnProximo) {
            btnProximo.addEventListener('click', () => mudarPagina(paginaAtual + 1));
        }
        
        // Ações
        if (btnAtualizar) {
            btnAtualizar.addEventListener('click', carregarLogsAuditoria);
        }
        if (btnExportarCSV) {
            btnExportarCSV.addEventListener('click', exportarCSV);
        }
        
        // Modal
        if (btnFecharDetalhes) {
            btnFecharDetalhes.addEventListener('click', fecharModalDetalhes);
        }
        
        if (modalDetalhes) {
            const closeModal = modalDetalhes.querySelector('.close-modal');
            const modalOverlay = modalDetalhes.querySelector('.modal-overlay');
            
            if (closeModal) {
                closeModal.addEventListener('click', fecharModalDetalhes);
            }
            if (modalOverlay) {
                modalOverlay.addEventListener('click', fecharModalDetalhes);
            }
        }
        
        // Tecla ESC para fechar modal
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modalDetalhes && !modalDetalhes.classList.contains('hidden')) {
                fecharModalDetalhes();
            }
        });
    }

    function aplicarFiltros() {
        filtrosAtuais = {
            tabela: filtroTabela?.value || '',
            acao: filtroAcao?.value || '',
            usuario_id: filtroUsuario?.value || '',
            data_inicio: filtroDataInicio?.value || '',
            data_fim: filtroDataFim?.value || ''
        };
        
        paginaAtual = 1;
        carregarLogsAuditoria();
    }

    function limparFiltros() {
        if (filtroTabela) filtroTabela.value = '';
        if (filtroAcao) filtroAcao.value = '';
        if (filtroUsuario) filtroUsuario.value = '';
        
        // Reset para datas padrão (últimos 7 dias)
        inicializarDataFiltros();
        
        aplicarFiltros();
    }

    function carregarLogsAuditoria() {
        mostrarLoading();
        
        // Construir parâmetros da URL
        const params = new URLSearchParams({
            pagina: paginaAtual,
            por_pagina: porPagina,
            ...filtrosAtuais
        });
        
        // Remover parâmetros vazios
        for (const [key, value] of [...params.entries()]) {
            if (!value || value === '') {
                params.delete(key);
            }
        }
        
        fetch(`api/auditoria/logs?${params}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erro HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                logsCarregados = data.logs || [];
                preencherTabela(logsCarregados);
                atualizarPaginacao(data.total || 0, data.paginas || 1);
                atualizarEstatisticas(data);
                esconderLoading();
            })
            .catch(error => {
                console.error('Erro ao carregar logs:', error);
                mostrarErro('Erro ao carregar logs de auditoria: ' + error.message);
                esconderLoading();
            });
    }

    function preencherTabela(logs) {
        if (!tbodyAuditoria) return;
        
        tbodyAuditoria.innerHTML = '';
        
        if (!logs || logs.length === 0) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td colspan="8" class="text-center">Nenhum registro encontrado</td>`;
            tbodyAuditoria.appendChild(tr);
            return;
        }
        
        logs.forEach(log => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${log.id || ''}</td>
                <td>${formatarDataHora(log.criado_em)}</td>
                <td>${log.usuario_nome || 'N/A'}</td>
                <td><span class="badge badge-info">${obterNomeTabelaAmigavel(log.tabela)}</span></td>
                <td>${log.registro_id || ''}</td>
                <td><span class="badge ${obterClasseBadgeAcao(log.acao)}">${formatarAcao(log.acao)}</span></td>
                <td><strong>${contarAlteracoes(log)}</strong> alteração(ões)</td>
                <td>
                    <button class="btn btn-sm btn-outline btn-detalhes" data-log-id="${log.id}" title="Ver detalhes completos">
                        <i class="fas fa-eye"></i> Ver Detalhes
                    </button>
                </td>
            `;
            tbodyAuditoria.appendChild(tr);
        });
        
        // Adicionar event listeners aos botões de detalhes
        document.querySelectorAll('.btn-detalhes').forEach(btn => {
            btn.addEventListener('click', function() {
                const logId = this.getAttribute('data-log-id');
                const log = logsCarregados.find(l => l.id == logId);
                if (log) {
                    mostrarDetalhesLog(log);
                }
            });
        });
    }

    function obterNomeTabelaAmigavel(tabela) {
        return nomesTabelasAmigaveis[tabela] || tabela || 'Desconhecida';
    }

    function obterNomeCampoAmigavel(campo) {
        return camposAmigaveis[campo] || campo;
    }

    function contarAlteracoes(log) {
        if (log.diferencas && Array.isArray(log.diferencas)) {
            return log.diferencas.length;
        }
        
        // Se não há diferenças calculadas, tentar calcular baseado nos dados antes/depois
        if (log.antes && log.depois) {
            try {
                const antes = typeof log.antes === 'string' ? JSON.parse(log.antes) : log.antes;
                const depois = typeof log.depois === 'string' ? JSON.parse(log.depois) : log.depois;
                
                if (log.acao === 'insert') {
                    return Object.keys(depois || {}).length;
                } else if (log.acao === 'delete') {
                    return Object.keys(antes || {}).length;
                } else if (log.acao === 'update') {
                    let diferencas = 0;
                    const chavesAntes = Object.keys(antes || {});
                    const chavesDepois = Object.keys(depois || {});
                    const todasChaves = new Set([...chavesAntes, ...chavesDepois]);
                    
                    todasChaves.forEach(chave => {
                        if (JSON.stringify(antes[chave]) !== JSON.stringify(depois[chave])) {
                            diferencas++;
                        }
                    });
                    return diferencas;
                }
            } catch (e) {
                console.error('Erro ao calcular diferenças:', e);
            }
        }
        
        return 0;
    }

    function formatarDataHora(dataString) {
        if (!dataString) return 'N/A';
        
        try {
            const data = new Date(dataString);
            if (isNaN(data.getTime())) return 'Data inválida';
            
            // Formato mais amigável: 14/09/2025 às 20:59
            const opcoes = {
                day: '2-digit',
                month: '2-digit', 
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'America/Sao_Paulo'
            };
            
            return data.toLocaleString('pt-BR', opcoes).replace(',', ' às');
        } catch (e) {
            return 'Data inválida';
        }
    }

    function formatarAcao(acao) {
        const acoes = {
            'insert': 'Novo Registro',
            'update': 'Alteração',
            'delete': 'Remoção'
        };
        return acoes[acao] || acao || 'N/A';
    }

    function obterClasseBadgeAcao(acao) {
        const classes = {
            'insert': 'badge-success',
            'update': 'badge-warning',
            'delete': 'badge-danger'
        };
        return classes[acao] || 'badge-secondary';
    }

    function atualizarPaginacao(total, paginas) {
        totalPaginas = paginas;
        
        if (btnAnterior) {
            btnAnterior.disabled = paginaAtual <= 1;
        }
        if (btnProximo) {
            btnProximo.disabled = paginaAtual >= totalPaginas;
        }
        
        if (infoPaginacao) {
            infoPaginacao.textContent = `Página ${paginaAtual} de ${totalPaginas} (${total} registros encontrados)`;
        }
    }

    function mudarPagina(novaPagina) {
        if (novaPagina < 1 || novaPagina > totalPaginas) return;
        
        paginaAtual = novaPagina;
        carregarLogsAuditoria();
        
        // Scroll para o topo da tabela
        if (tabelaAuditoria) {
            tabelaAuditoria.scrollIntoView({ behavior: 'smooth' });
        }
    }

    function atualizarEstatisticas(data) {
        // Usar estatísticas do servidor se disponível, senão calcular localmente
        const stats = data.estatisticas || calcularEstatisticasLocais(logsCarregados);
        
        if (totalRegistros) {
            totalRegistros.textContent = stats.total || logsCarregados.length;
        }
        if (totalInserts) {
            totalInserts.textContent = stats.inserts || 0;
        }
        if (totalUpdates) {
            totalUpdates.textContent = stats.updates || 0;
        }
        if (totalDeletes) {
            totalDeletes.textContent = stats.deletes || 0;
        }
    }

    function calcularEstatisticasLocais(logs) {
        if (!logs || !Array.isArray(logs)) {
            return { total: 0, inserts: 0, updates: 0, deletes: 0 };
        }
        
        const inserts = logs.filter(log => log.acao === 'insert').length;
        const updates = logs.filter(log => log.acao === 'update').length;
        const deletes = logs.filter(log => log.acao === 'delete').length;
        
        return {
            total: logs.length,
            inserts: inserts,
            updates: updates,
            deletes: deletes
        };
    }

    function mostrarDetalhesLog(log) {
        if (!modalDetalhes) return;
        
        // Preencher informações básicas
        const elementos = {
            'detalheId': log.id,
            'detalheData': formatarDataHora(log.criado_em),
            'detalheUsuario': log.usuario_nome || 'N/A',
            'detalheTabela': obterNomeTabelaAmigavel(log.tabela),
            'detalheRegistroId': log.registro_id,
            'detalheAcao': formatarAcao(log.acao)
        };
        
        Object.entries(elementos).forEach(([id, valor]) => {
            const elemento = document.getElementById(id);
            if (elemento) {
                elemento.textContent = valor || '';
            }
        });
        
        // Preencher alterações
        const tbodyAlteracoes = document.getElementById('detalheAlteracoes');
        if (tbodyAlteracoes) {
            tbodyAlteracoes.innerHTML = '';
            
            const diferencas = calcularDiferencasDetalhadas(log);
            
            if (diferencas && diferencas.length > 0) {
                diferencas.forEach(diff => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><strong>${obterNomeCampoAmigavel(diff.campo)}</strong></td>
                        <td>${formatarValorAmigavel(diff.anterior)}</td>
                        <td>${formatarValorAmigavel(diff.novo)}</td>
                    `;
                    tbodyAlteracoes.appendChild(tr);
                });
            } else {
                const mensagem = log.acao === 'insert' ? 
                    'Este é um novo registro. Todos os campos foram preenchidos pela primeira vez.' :
                    log.acao === 'delete' ? 
                    'Este registro foi removido completamente do sistema.' :
                    'Não foram detectadas alterações específicas nos campos.';
                    
                tbodyAlteracoes.innerHTML = `<tr><td colspan="3" class="text-center" style="padding: 20px; font-style: italic;">${mensagem}</td></tr>`;
            }
        }
        
        // Preencher JSON completo com explicação
        const detalheAntes = document.getElementById('detalheAntes');
        const detalheDepois = document.getElementById('detalheDepois');
        
        if (detalheAntes) {
            if (log.antes) {
                detalheAntes.textContent = formatarJSON(log.antes);
            } else {
                detalheAntes.textContent = 'Este é um novo registro - não havia dados anteriores.';
                detalheAntes.style.fontStyle = 'italic';
                detalheAntes.style.color = '#666';
            }
        }
        
        if (detalheDepois) {
            if (log.depois) {
                detalheDepois.textContent = formatarJSON(log.depois);
            } else {
                detalheDepois.textContent = 'O registro foi removido - não há dados posteriores.';
                detalheDepois.style.fontStyle = 'italic';
                detalheDepois.style.color = '#666';
            }
        }
        
        // Mostrar modal
        modalDetalhes.classList.remove('hidden');
        if (modalDetalhes.style) {
            modalDetalhes.style.display = 'flex';
        }
        document.body.style.overflow = 'hidden';
    }

    function calcularDiferencasDetalhadas(log) {
        // Se já tem diferenças calculadas, usar elas
        if (log.diferencas && Array.isArray(log.diferencas)) {
            return log.diferencas;
        }
        
        // Calcular diferenças baseado nos dados antes/depois
        try {
            const antes = log.antes ? (typeof log.antes === 'string' ? JSON.parse(log.antes) : log.antes) : {};
            const depois = log.depois ? (typeof log.depois === 'string' ? JSON.parse(log.depois) : log.depois) : {};
            
            const diferencas = [];
            
            if (log.acao === 'insert' && depois) {
                // Para inserções, mostrar apenas os campos mais importantes
                const camposImportantes = ['nome', 'email', 'valor', 'quantidade', 'status', 'tipo', 'codigo', 'descricao'];
                Object.entries(depois).forEach(([campo, valor]) => {
                    // Mostrar campos importantes ou que não são técnicos
                    if (camposImportantes.includes(campo) || 
                        (!campo.includes('_em') && !campo.includes('_id') && campo !== 'sincronizado')) {
                        diferencas.push({
                            campo: campo,
                            anterior: null,
                            novo: valor
                        });
                    }
                });
            } else if (log.acao === 'delete' && antes) {
                // Para exclusões, mostrar campos importantes
                const camposImportantes = ['nome', 'email', 'valor', 'quantidade', 'status', 'tipo', 'codigo', 'descricao'];
                Object.entries(antes).forEach(([campo, valor]) => {
                    if (camposImportantes.includes(campo) || 
                        (!campo.includes('_em') && !campo.includes('_id') && campo !== 'sincronizado')) {
                        diferencas.push({
                            campo: campo,
                            anterior: valor,
                            novo: null
                        });
                    }
                });
            } else if (log.acao === 'update') {
                // Para atualizações, mostrar apenas campos que realmente mudaram
                const todasChaves = new Set([
                    ...Object.keys(antes),
                    ...Object.keys(depois)
                ]);
                
                todasChaves.forEach(campo => {
                    const valorAntes = antes[campo];
                    const valorDepois = depois[campo];
                    
                    // Comparação mais robusta
                    const antesStr = valorAntes === null || valorAntes === undefined ? '' : String(valorAntes);
                    const depoisStr = valorDepois === null || valorDepois === undefined ? '' : String(valorDepois);
                    
                    if (antesStr !== depoisStr) {
                        diferencas.push({
                            campo: campo,
                            anterior: valorAntes,
                            novo: valorDepois
                        });
                    }
                });
            }
            
            return diferencas;
        } catch (e) {
            console.error('Erro ao calcular diferenças detalhadas:', e);
            return [];
        }
    }

    function formatarJSON(dados) {
        if (!dados) return 'Nenhum dado disponível';
        
        try {
            const obj = typeof dados === 'string' ? JSON.parse(dados) : dados;
            return JSON.stringify(obj, null, 2);
        } catch (e) {
            return dados.toString();
        }
    }

    function formatarValorAmigavel(valor) {
        if (valor === null || valor === undefined || valor === '') {
            return '<span style="color: #999; font-style: italic;">Vazio</span>';
        }
        
        if (typeof valor === 'boolean') {
            return valor ? 
                '<span style="color: #28a745; font-weight: bold;">✓ Sim</span>' : 
                '<span style="color: #dc3545; font-weight: bold;">✗ Não</span>';
        }
        
        if (typeof valor === 'object') {
            return '<span style="color: #6c757d;">[Dados Complexos]</span>';
        }
        
        const valorStr = String(valor);
        
        // Formatar valores específicos
        if (valorStr.includes('@')) {
            return `<span style="color: #007bff;"><i class="fas fa-envelope" style="margin-right: 5px;"></i>${valorStr}</span>`;
        }
        
        if (valorStr.match(/^\d{4}-\d{2}-\d{2}/)) {
            try {
                const data = new Date(valorStr);
                return `<span style="color: #6f42c1;"><i class="fas fa-calendar" style="margin-right: 5px;"></i>${formatarDataHora(valorStr)}</span>`;
            } catch (e) {
                // Se não conseguir formatar como data, retornar como string normal
            }
        }
        
        if (valorStr.match(/^\d+\.\d{2}$/) || valorStr.match(/^\d+\.0{1,3}$/)) {
            return `<span style="color: #28a745; font-weight: bold;"><i class="fas fa-dollar-sign" style="margin-right: 5px;"></i>R$ ${valorStr}</span>`;
        }
        
        if (valorStr.includes('Status') || valorStr.includes('Tipo') || valorStr.includes('Forma')) {
            // Remover prefixos técnicos e formatar melhor
            const valorLimpo = valorStr.replace(/^(Status|Tipo|Forma)[A-Za-z]*\./, '');
            return `<span style="background-color: #e9ecef; padding: 2px 6px; border-radius: 3px; font-size: 0.9em;">${valorLimpo}</span>`;
        }
        
        // Truncar valores muito longos
        if (valorStr.length > 100) {
            return `<span title="${valorStr}">${valorStr.substring(0, 97)}...</span>`;
        }
        
        return `<span>${valorStr}</span>`;
    }

    function fecharModalDetalhes() {
        if (!modalDetalhes) return;
        
        modalDetalhes.classList.add('hidden');
        if (modalDetalhes.style) {
            modalDetalhes.style.display = 'none';
        }
        document.body.style.overflow = '';
    }

    function exportarCSV() {
        if (!logsCarregados || logsCarregados.length === 0) {
            alert('Não há dados para exportar no momento. Tente aplicar filtros diferentes ou recarregar os dados.');
            return;
        }
        
        try {
            // Criar cabeçalhos CSV mais amigáveis
            let csvContent = 'ID,Data e Hora,Usuário,Área do Sistema,ID do Registro,Tipo de Ação,Número de Alterações\n';
            
            // Adicionar dados
            logsCarregados.forEach(log => {
                const linha = [
                    log.id || '',
                    `"${formatarDataHora(log.criado_em)}"`,
                    `"${(log.usuario_nome || 'N/A').replace(/"/g, '""')}"`,
                    `"${obterNomeTabelaAmigavel(log.tabela).replace(/"/g, '""')}"`,
                    log.registro_id || '',
                    `"${formatarAcao(log.acao)}"`,
                    contarAlteracoes(log)
                ].join(',');
                
                csvContent += linha + '\n';
            });
            
            // Criar e baixar arquivo
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.setAttribute('href', url);
            link.setAttribute('download', `relatorio_auditoria_${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            // Mostrar mensagem de sucesso
            mostrarSucesso('Relatório exportado com sucesso!');
        } catch (e) {
            console.error('Erro ao exportar CSV:', e);
            mostrarErro('Não foi possível exportar o relatório. Tente novamente.');
        }
    }

    function mostrarLoading() {
        if (tbodyAuditoria) {
            tbodyAuditoria.innerHTML = '<tr><td colspan="8" class="text-center" style="padding: 40px;"><i class="fas fa-spinner fa-spin" style="font-size: 24px; color: #007bff;"></i><br><br>Carregando dados...</td></tr>';
        }
    }

    function esconderLoading() {
        // A função preencherTabela já substitui o conteúdo de loading
    }

    function mostrarErro(mensagem) {
        console.error(mensagem);
        mostrarNotificacao(mensagem, 'erro');
    }

    function mostrarSucesso(mensagem) {
        mostrarNotificacao(mensagem, 'sucesso');
    }

    function mostrarNotificacao(mensagem, tipo = 'erro') {
        // Remover notificações existentes
        const notificacoesExistentes = document.querySelectorAll('.notificacao-sistema');
        notificacoesExistentes.forEach(n => n.remove());
        
        // Criar nova notificação
        const notificacao = document.createElement('div');
        notificacao.className = `notificacao-sistema notificacao-${tipo}`;
        
        const cores = {
            erro: { bg: '#f8d7da', texto: '#721c24', borda: '#f5c6cb', icone: 'fas fa-exclamation-triangle' },
            sucesso: { bg: '#d4edda', texto: '#155724', borda: '#c3e6cb', icone: 'fas fa-check-circle' },
            info: { bg: '#d1ecf1', texto: '#0c5460', borda: '#bee5eb', icone: 'fas fa-info-circle' }
        };
        
        const cor = cores[tipo] || cores.erro;
        
        notificacao.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            padding: 15px 20px;
            background-color: ${cor.bg};
            color: ${cor.texto};
            border: 1px solid ${cor.borda};
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-family: inherit;
            font-size: 14px;
            line-height: 1.4;
            animation: slideIn 0.3s ease-out;
        `;
        
        notificacao.innerHTML = `
            <div style="display: flex; align-items: center;">
                <i class="${cor.icone}" style="margin-right: 10px; font-size: 16px;"></i>
                <div style="flex: 1;">
                    <strong>${tipo === 'erro' ? 'Atenção!' : tipo === 'sucesso' ? 'Sucesso!' : 'Informação'}</strong><br>
                    ${mensagem}
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; font-size: 18px; line-height: 1; color: inherit; cursor: pointer; margin-left: 10px; padding: 0; width: 20px; height: 20px;"
                        title="Fechar">×</button>
            </div>
        `;
        
        // Adicionar animação CSS
        if (!document.getElementById('notificacao-styles')) {
            const style = document.createElement('style');
            style.id = 'notificacao-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                .notificacao-sistema:hover {
                    transform: translateX(-5px);
                    transition: transform 0.2s ease;
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notificacao);
        
        // Auto-esconder após 7 segundos
        setTimeout(() => {
            if (notificacao && notificacao.parentNode) {
                notificacao.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => {
                    if (notificacao.parentNode) {
                        notificacao.remove();
                    }
                }, 300);
            }
        }, 7000);
    }

    // Função utilitária para debug (mantida para desenvolvedores)
    window.debugAuditoria = function() {
        console.log('🔍 Debug do Sistema de Auditoria:', {
            paginaAtual,
            totalPaginas,
            filtrosAtuais,
            totalLogsCarregados: logsCarregados.length,
            elementos: {
                tabelaEncontrada: !!tbodyAuditoria,
                modalEncontrado: !!modalDetalhes,
                filtrosDisponveis: {
                    tabela: !!filtroTabela,
                    acao: !!filtroAcao,
                    usuario: !!filtroUsuario,
                    dataInicio: !!filtroDataInicio,
                    dataFim: !!filtroDataFim
                }
            },
            ultimaRequisicao: new Date().toLocaleString('pt-BR')
        });
        
        mostrarNotificacao('Informações de debug foram exibidas no console do navegador (F12)', 'info');
    };

    // Função para explicar o que cada ação significa (para usuários leigos)
    window.explicarAcoes = function() {
        const explicacao = `
        📋 EXPLICAÇÃO DAS AÇÕES DE AUDITORIA:

        🆕 NOVO REGISTRO (Inserção)
        • Significa que um novo item foi criado no sistema
        • Exemplo: Cadastro de um novo cliente, produto ou usuário

        ✏️ ALTERAÇÃO (Atualização) 
        • Significa que informações existentes foram modificadas
        • Exemplo: Mudança de preço, alteração de e-mail, atualização de estoque

        🗑️ REMOÇÃO (Exclusão)
        • Significa que um item foi removido do sistema
        • Exemplo: Exclusão de um produto, remoção de um desconto

        💡 DICA: Clique em "Ver Detalhes" para saber exatamente o que foi alterado!
        `;
        
        console.log(explicacao);
        mostrarNotificacao('Explicação sobre as ações foi exibida no console (pressione F12 para ver)', 'info');
    };
});
