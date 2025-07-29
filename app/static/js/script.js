document.addEventListener('DOMContentLoaded', function() {
    // Atualizar data e hora
    function updateDateTime() {
        const now = new Date();
        document.getElementById('updateTime').textContent = now.toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    updateDateTime();
    setInterval(updateDateTime, 60000);

    // Navegação por abas
    const navItems = document.querySelectorAll('.sidebar-nav li');
    const tabContents = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('page-title');
    
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            navItems.forEach(nav => nav.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            
            const tabName = this.querySelector('span').textContent;
            pageTitle.textContent = tabName;
            document.querySelector('.breadcrumb').textContent = `Home / ${tabName}`;

            // Carregar dados específicos da aba quando ativada
            if (tabId === 'dashboard') loadDashboardData();
            if (tabId === 'clientes') loadClientesData();
            if (tabId === 'produtos') loadProdutosData();
            if (tabId === 'financeiro') loadFinanceiroData();
            if (tabId === 'usuarios') loadUsuariosData();
            if (tabId === 'estoque') loadMovimentacoesData();
        });
    });

    // Botão de logout
    document.getElementById('logoutBtn').addEventListener('click', () => {
        if (confirm('Tem certeza que deseja sair do sistema?')) {
            window.location.href = '/logout';
        }
    });

    // Modal functions
    function openModal(modalId) {
        document.getElementById(modalId).style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    // Event listeners para modals
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal.id);
        });
    });

    // Abrir modals principais
    document.getElementById('addCliente').addEventListener('click', () => {
        // Limpar formulário antes de abrir o modal
        document.getElementById('clienteForm').reset();
        document.getElementById('clienteId').value = '';
        document.getElementById('clienteStatus').value = 'true';
        document.getElementById('clienteModalTitle').textContent = 'Cadastrar Cliente';
        document.getElementById('clienteModalSubmitText').textContent = 'Cadastrar';
        openModal('clienteModal');
    });
    
    document.getElementById('addProduto').addEventListener('click', () => openModal('produtoModal'));
    document.getElementById('addUsuario').addEventListener('click', () => openEditarUsuarioModal());

    // Fechar modal ao clicar fora do conteúdo
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay')) {
            const modal = e.target.closest('.modal');
            closeModal(modal.id);
        }
    });

    // Função para mostrar mensagens flash
    function showFlashMessage(type, message) {
        const flashContainer = document.querySelector('.flash-messages');
        const flashId = `flash-${Date.now()}`;
        
        const flashMessage = document.createElement('div');
        flashMessage.className = `flash-message ${type}`;
        flashMessage.id = flashId;
        
        flashMessage.innerHTML = `
            <div>
                <i class="fas 
                    ${type === 'success' ? 'fa-check-circle' : ''}
                    ${type === 'error' ? 'fa-exclamation-circle' : ''}
                    ${type === 'warning' ? 'fa-exclamation-triangle' : ''}
                    ${type === 'info' ? 'fa-info-circle' : ''}
                "></i>
                <span>${message}</span>
            </div>
        `;
        
        flashContainer.appendChild(flashMessage);
        
        // Auto-close flash messages after 5 seconds
        setTimeout(() => {
            flashMessage.classList.add('fade-out');
            setTimeout(() => flashMessage.remove(), 500);
        }, 5000);
    }

    // Processar mensagens flash do Flask ao carregar a página
    document.querySelectorAll('.flash-message').forEach(message => {
        setTimeout(() => {
            message.classList.add('fade-out');
            setTimeout(() => message.remove(), 500);
        }, 5000);
    });

    // Função auxiliar para chamadas à API
    async function fetchWithErrorHandling(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Erro na requisição:', error);
            showFlashMessage('error', 'Erro ao comunicar com o servidor');
            throw error;
        }
    }

    // ===== Funções para carregar dados =====
    
    // Carregar dados do dashboard
    async function loadDashboardData() {
        try {
            // Carregar métricas
            const metricsData = await fetchWithErrorHandling('/admin/dashboard/metrics');
            
            if (metricsData.success) {
                const metricsContainer = document.querySelector('.metrics-grid');
                metricsContainer.innerHTML = '';
                
                metricsData.metrics.forEach(metric => {
                    const card = document.createElement('div');
                    card.className = `metric-card ${metric.color}`;
                    
                    card.innerHTML = `
                        <div class="metric-icon">
                            <i class="fas fa-${metric.icon}"></i>
                        </div>
                        <div class="metric-info">
                            <h3>${metric.title}</h3>
                            <div class="value">${metric.value}</div>
                        </div>
                    `;
                    
                    metricsContainer.appendChild(card);
                });
            }
            
            // Carregar movimentações
            const movData = await fetchWithErrorHandling('/admin/dashboard/movimentacoes');
            
            if (movData.success) {
                const movTable = document.querySelector('#movimentacoesTable tbody');
                movTable.innerHTML = '';
                
                movData.movimentacoes.forEach(mov => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${mov.data}</td>
                        <td><span class="badge ${mov.tipo === 'Entrada' ? 'badge-success' : 'badge-danger'}">${mov.tipo}</span></td>
                        <td>${mov.produto}</td>
                        <td>${mov.quantidade}</td>
                        <td>${mov.valor}</td>
                    `;
                    movTable.appendChild(row);
                });
            }
        } catch (error) {
            console.error('Erro ao carregar dados do dashboard:', error);
            showFlashMessage('error', 'Erro ao carregar dados do dashboard');
        }
    }

    // Função para abrir modal de edição de cliente
    async function openEditarClienteModal(clienteId) {
        // Resetar todos os campos
        const form = document.getElementById('clienteForm');
        form.reset();
        document.getElementById('clienteId').value = '';
        document.getElementById('clienteStatus').value = 'true';

        // Ajustar título e botão
        document.getElementById('clienteModalTitle').textContent = 'Editar Cliente';
        document.getElementById('clienteModalSubmitText').textContent = 'Atualizar';

        try {
            const response = await fetchWithErrorHandling(`/admin/clientes/${clienteId}`);
            if (response.success) {
                const cliente = response.cliente;
                document.getElementById('clienteId').value = cliente.id;
                document.getElementById('clienteNome').value = cliente.nome;
                document.getElementById('clienteDocumento').value = cliente.documento || '';
                document.getElementById('clienteTelefone').value = cliente.telefone || '';
                document.getElementById('clienteEmail').value = cliente.email || '';
                document.getElementById('clienteEndereco').value = cliente.endereco || '';
                document.getElementById('clienteStatus').value = 
                cliente.ativo === 'Ativo' || cliente.ativo === true ? 'true' : 'false';
            } else {
                showFlashMessage('error', 'Erro ao carregar dados do cliente');
                return;
            }
        } catch (error) {
            console.error('Erro ao carregar cliente:', error);
            showFlashMessage('error', 'Erro ao carregar dados do cliente');
            return;
        }

        // Abrir modal
        openModal('clienteModal');
    }

    // Submissão do formulário de cliente
    document.getElementById('clienteForm').addEventListener('submit', async function (e) {
        e.preventDefault();

        const clienteId = document.getElementById('clienteId').value;
        const isEdit = clienteId !== '';

        const formData = {
            nome: document.getElementById('clienteNome').value,
            documento: document.getElementById('clienteDocumento').value,
            telefone: document.getElementById('clienteTelefone').value,
            email: document.getElementById('clienteEmail').value,
            endereco: document.getElementById('clienteEndereco').value,
            ativo: document.getElementById('clienteStatus').value === 'true'
        };

        const url = isEdit ? `/admin/clientes/${clienteId}` : '/admin/clientes';
        const method = isEdit ? 'PUT' : 'POST';

        try {
            const response = await fetchWithErrorHandling(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (response.success) {
                showFlashMessage('success', `Cliente ${isEdit ? 'atualizado' : 'cadastrado'} com sucesso`);
                closeModal('clienteModal');
                loadClientesData();
            } else {
                showFlashMessage('error', response.message || 'Erro ao salvar cliente');
            }
        } catch (error) {
            console.error('Erro ao salvar cliente:', error);
            showFlashMessage('error', 'Erro ao salvar cliente');
        }
    });

    // Configurar ações dos botões editar e remover após carregar tabela
    function setupClienteActions() {
        document.querySelectorAll('.editar-cliente').forEach(btn => {
            btn.addEventListener('click', function () {
                const clienteId = this.getAttribute('data-id');
                openEditarClienteModal(clienteId);
            });
        });

        document.querySelectorAll('.remover-cliente').forEach(btn => {
            btn.addEventListener('click', function () {
                const clienteId = this.getAttribute('data-id');
                document.getElementById('confirmarExclusaoTexto').textContent = `Tem certeza que deseja excluir o cliente ${clienteId}?`;
                document.getElementById('confirmarExclusaoBtn').setAttribute('data-id', clienteId);
                document.getElementById('confirmarExclusaoBtn').setAttribute('data-type', 'cliente');
                openModal('confirmarExclusaoModal');
            });
        });
    }

    // Carregar dados de clientes e montar tabela
    async function loadClientesData() {
        try {
            const searchText = document.getElementById('searchCliente').value.toLowerCase();
            const data = await fetchWithErrorHandling('/admin/clientes');

            if (data.success) {
                const clientesTable = document.querySelector('#clientesTable tbody');
                clientesTable.innerHTML = '';

                data.clientes.forEach(cliente => {
                    if (searchText && !cliente.nome.toLowerCase().includes(searchText)) return;

                    const status = cliente.ativo === 'Ativo' ? 'Ativo' : 'Inativo';

                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${cliente.id}</td>
                        <td>${cliente.nome}</td>
                        <td>${cliente.documento || ''}</td>
                        <td>${cliente.telefone || ''}</td>
                        <td>${cliente.email || ''}</td>
                        <td><span class="badge ${status === 'Ativo' ? 'badge-success' : 'badge-danger'}">${status}</span></td>
                        <td>
                            <div class="table-actions">
                                <button class="btn-icon btn-warning editar-cliente" data-id="${cliente.id}" title="Editar">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn-icon btn-danger remover-cliente" data-id="${cliente.id}" title="Remover">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    `;
                    clientesTable.appendChild(row);
                });

                setupClienteActions();
            }
        } catch (error) {
            console.error('Erro ao carregar clientes:', error);
            showFlashMessage('error', 'Erro ao carregar lista de clientes');
        }
    }

    // Carregar dados de produtos
    async function loadProdutosData() {
        try {
            const searchText = document.getElementById('searchProduto').value.toLowerCase();
            const data = await fetchWithErrorHandling('/admin/produtos');
            
            if (data.success) {
                const produtosTable = document.querySelector('#produtosTable tbody');
                produtosTable.innerHTML = '';
                
                data.produtos.forEach(produto => {
                    if (searchText && !produto.nome.toLowerCase().includes(searchText)) {
                        return;
                    }
                    
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${produto.id}</td>
                        <td>${produto.nome}</td>
                        <td>${produto.tipo}</td>
                        <td>${produto.unidade}</td>
                        <td>${produto.valor}</td>
                        <td>${produto.estoque_deposito}</td>
                        <td>${produto.estoque_loja}</td>
                        <td>${produto.estoque_fabrica}</td>
                        <td>
                            <div class="table-actions">
                                <button class="btn-icon btn-info movimentar-estoque" data-id="${produto.id}" title="Transferir entre estoques">
                                    <i class="fas fa-exchange-alt"></i>
                                </button>
                                <button class="btn-icon btn-warning editar-produto" data-id="${produto.id}" title="Editar">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn-icon btn-danger remover-produto" data-id="${produto.id}" title="Remover">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    `;
                    produtosTable.appendChild(row);
                });
                
                // Adicionar eventos aos botões de ação
                setupProdutoActions();
            }
        } catch (error) {
            console.error('Erro ao carregar produtos:', error);
            showFlashMessage('error', 'Erro ao carregar lista de produtos');
        }
    }

    function setupProdutoActions() {
        document.querySelectorAll('.editar-produto').forEach(btn => {
            btn.addEventListener('click', async function() {
                const produtoId = this.getAttribute('data-id');
                
                try {
                    const data = await fetchWithErrorHandling(`/admin/produtos/${produtoId}`);
                    
                    if (data.success) {
                        const produto = data.produto;
                        const formBody = document.querySelector('#editarProdutoModal .modal-body');
                        
                        // Tratamento seguro para valor_unitario
                        let valorUnitario = produto.valor_unitario;
                        if (typeof valorUnitario === 'string') {
                            // Remove formatação de moeda se existir
                            valorUnitario = valorUnitario.replace(/[^\d,.-]/g, '').replace(',', '.');
                        }
                        
                        // Tratamento seguro para estoque_quantidade
                        let estoqueQuantidade = produto.estoque_quantidade;
                        if (typeof estoqueQuantidade === 'string') {
                            // Remove unidade de medida se existir
                            estoqueQuantidade = estoqueQuantidade.split(' ')[0];
                        }
                        
                        formBody.innerHTML = `
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="editCodigo">Código*</label>
                                    <input type="text" id="editCodigo" class="form-control" value="${produto.codigo || ''}" required>
                                </div>
                                <div class="form-group">
                                    <label for="editMarca">Marca*</label>
                                    <input type="text" id="editMarca" class="form-control" value="${produto.marca || ''}" required>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="editNome">Nome*</label>
                                    <input type="text" id="editNome" class="form-control" value="${produto.nome}" required>
                                </div>
                                <div class="form-group">
                                    <label for="editTipo">Tipo*</label>
                                    <input type="text" id="editTipo" class="form-control" value="${produto.tipo}" required>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="editUnidade">Unidade*</label>
                                    <select id="editUnidade" class="form-control" required>
                                        <option value="kg" ${produto.unidade === 'kg' ? 'selected' : ''}>kg</option>
                                        <option value="saco" ${produto.unidade === 'saco' ? 'selected' : ''}>saco</option>
                                        <option value="unidade" ${produto.unidade === 'unidade' ? 'selected' : ''}>unidade</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label for="editValor">Valor Unitário*</label>
                                    <input type="number" id="editValor" class="form-control" value="${valorUnitario}" step="0.01" min="0" required>
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="editEstoque">Quantidade em Estoque*</label>
                                <input type="number" id="editEstoque" class="form-control" value="${estoqueQuantidade}" step="0.001" min="0" required>
                            </div>
                        `;
                        
                        document.getElementById('editarProdutoForm').setAttribute('data-produto-id', produtoId);
                        openModal('editarProdutoModal');
                    }
                } catch (error) {
                    console.error('Erro ao carregar dados do produto:', error);
                    showFlashMessage('error', 'Erro ao carregar dados do produto');
                }
            });
        });

        document.querySelectorAll('.remover-produto').forEach(btn => {
            btn.addEventListener('click', function() {
                const produtoId = this.getAttribute('data-id');
                document.getElementById('confirmarExclusaoTexto').textContent = `Tem certeza que deseja excluir o produto ${produtoId}?`;
                document.getElementById('confirmarExclusaoBtn').setAttribute('data-id', produtoId);
                document.getElementById('confirmarExclusaoBtn').setAttribute('data-type', 'produto');
                openModal('confirmarExclusaoModal');
            });
        });

        // Configurar botões de transferência de estoque
        document.querySelectorAll('.movimentar-estoque').forEach(btn => {
            btn.addEventListener('click', function() {
                const produtoId = this.getAttribute('data-id');
                openTransferenciaModal(produtoId);
            });
        });
    }

    // Função para abrir modal de transferência
    async function openTransferenciaModal(produtoId) {
        try {
            const response = await fetchWithErrorHandling(`/admin/produtos/${produtoId}`);
            if (response.success) {
                const produto = response.produto;
                
                document.getElementById('transferenciaProdutoId').value = produtoId;
                document.getElementById('transferenciaProdutoNome').textContent = produto.nome;
                
                // Resetar valores
                document.getElementById('transferenciaOrigem').value = 'loja';
                document.getElementById('transferenciaDestino').value = 'deposito';
                document.getElementById('transferenciaQuantidade').value = '';
                document.getElementById('transferenciaObservacao').value = '';
                
                openModal('transferenciaModal');
                updateEstoqueDisponivel();
            }
        } catch (error) {
            console.error('Erro ao abrir modal de transferência:', error);
            showFlashMessage('error', 'Erro ao carregar dados do produto');
        }
    }

    // Atualizar estoque disponível quando mudar a origem
    document.getElementById('transferenciaOrigem').addEventListener('change', updateEstoqueDisponivel);
    
    function updateEstoqueDisponivel() {
        const produtoId = document.getElementById('transferenciaProdutoId').value;
        const origem = document.getElementById('transferenciaOrigem').value;
        
        // Buscar estoque atual do produto
        fetchWithErrorHandling(`/admin/produtos/${produtoId}`)
            .then(response => {
                if (response.success) {
                    const produto = response.produto;
                    let estoque = 0;
                    
                    if (origem === 'loja') estoque = produto.estoque_loja;
                    else if (origem === 'deposito') estoque = produto.estoque_deposito;
                    else if (origem === 'fabrica') estoque = produto.estoque_fabrica;
                    
                    document.getElementById('transferenciaEstoqueDisponivel').textContent = 
                        `Disponível: ${estoque} ${produto.unidade}`;
                    
                    // Definir valor máximo para o campo de quantidade
                    document.getElementById('transferenciaQuantidade').max = estoque;
                }
            })
            .catch(error => {
                console.error('Erro ao buscar estoque:', error);
            });
    }

    // Formulário de transferência
    document.getElementById('transferenciaForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const produtoId = document.getElementById('transferenciaProdutoId').value;
        const origem = document.getElementById('transferenciaOrigem').value; // 'loja', 'deposito' ou 'fabrica'
        const destino = document.getElementById('transferenciaDestino').value;
        const quantidade = parseFloat(document.getElementById('transferenciaQuantidade').value);
        const observacao = document.getElementById('transferenciaObservacao').value;
        
        try {
            const response = await fetch('/admin/transferencias', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    produto_id: produtoId,
                    estoque_origem: origem,
                    estoque_destino: destino,
                    quantidade: quantidade,
                    observacao: observacao
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Erro ao realizar transferência');
            }
            
            if (data.success) {
                showFlashMessage('success', data.message);
                closeModal('transferenciaModal');
                loadProdutosData();
                loadMovimentacoesData();
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Erro:', error);
            showFlashMessage('error', error.message);
        }
    });

    // Carregar dados de movimentações
    async function loadMovimentacoesData() {
        try {
            const dateInicio = document.getElementById('movimentacaoDateInicio').value;
            const dateFim = document.getElementById('movimentacaoDateFim').value;
            const tipo = document.getElementById('movimentacaoTipo').value;
            
            let url = '/admin/transferencias';
            const params = new URLSearchParams();
            
            if (dateInicio) params.append('data_inicio', dateInicio);
            if (dateFim) params.append('data_fim', dateFim);
            if (tipo) params.append('tipo', tipo);
            
            if (params.toString()) {
                url += `?${params.toString()}`;
            }
            
            const data = await fetchWithErrorHandling(url);
            
            if (data.success) {
                const table = document.querySelector('#movimentacoesEstoqueTable tbody');
                table.innerHTML = '';
                
                data.transferencias.forEach(transf => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${transf.data}</td>
                        <td>${transf.observacao || '-'}</td>
                        <td>${transf.produto}</td>
                        <td>${transf.quantidade}</td>
                        <td>${transf.origem || '-'}</td>
                        <td>${transf.destino || '-'}</td>
                        <td>${transf.usuario}</td>
                    `;
                    table.appendChild(row);
                });
            }
        } catch (error) {
            console.error('Erro ao carregar movimentações:', error);
            showFlashMessage('error', 'Erro ao carregar histórico de movimentações');
        }
    }

    // Configurar filtro de movimentações
    document.getElementById('filterMovimentacoes').addEventListener('click', loadMovimentacoesData);

    // Carregar dados financeiros
    async function loadFinanceiroData() {
        try {
            const dateInicio = document.getElementById('dateInicio').value;
            const dateFim = document.getElementById('dateFim').value;
            
            let url = '/admin/financeiro';
            if (dateInicio || dateFim) {
                url += `?data_inicio=${dateInicio}&data_fim=${dateFim}`;
            }
            
            const data = await fetchWithErrorHandling(url);
            
            if (data.success) {
                // Atualizar resumo
                document.getElementById('receitasValue').textContent = data.resumo.receitas;
                document.getElementById('despesasValue').textContent = data.resumo.despesas;
                document.getElementById('saldoValue').textContent = data.resumo.saldo;
                
                // Atualizar tabela
                const financeiroTable = document.querySelector('#financeiroTable tbody');
                financeiroTable.innerHTML = '';
                
                data.lancamentos.forEach(lanc => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${lanc.data}</td>
                        <td><span class="badge ${lanc.tipo === 'Entrada' ? 'badge-success' : 'badge-danger'}">${lanc.tipo}</span></td>
                        <td>${lanc.categoria}</td>
                        <td style="font-weight: 500; color: ${lanc.tipo === 'Entrada' ? 'var(--success-dark)' : 'var(--danger-dark)'}">${lanc.valor}</td>
                        <td>${lanc.descricao}</td>
                        <td>${lanc.nota}</td>
                    `;
                    financeiroTable.appendChild(row);
                });
            }
        } catch (error) {
            console.error('Erro ao carregar dados financeiros:', error);
            showFlashMessage('error', 'Erro ao carregar dados financeiros');
        }
    }

    // Funções específicas para usuários
    async function openEditarUsuarioModal(usuarioId = null) {
        const isEdit = usuarioId !== null;
        
        // Configurar o modal conforme o modo (edição ou cadastro)
        document.getElementById('usuarioModalTitle').textContent = isEdit ? 'Editar Usuário' : 'Cadastrar Usuário';
        document.getElementById('usuarioModalSubmitText').textContent = isEdit ? 'Atualizar' : 'Cadastrar';
        
        // Configurar campos de senha
        const senhaInput = document.getElementById('usuarioSenha');
        const confirmaSenhaInput = document.getElementById('usuarioConfirmaSenha');

        if (isEdit) {
            senhaInput.required = false;
            confirmaSenhaInput.required = false;
            senhaInput.placeholder = "Deixe em branco para manter a senha atual";
            confirmaSenhaInput.placeholder = "Repita a nova senha se for alterar";
        } else {
            senhaInput.required = true;
            confirmaSenhaInput.required = true;
            senhaInput.placeholder = "";
            confirmaSenhaInput.placeholder = "";
        }
        
        // Limpar formulário se for novo usuário
        if (!isEdit) {
            document.getElementById('usuarioForm').reset();
            document.getElementById('usuarioId').value = '';
        }
        
        // Se for edição, carregar os dados do usuário
        if (isEdit) {
            try {
                const response = await fetchWithErrorHandling(`/admin/usuarios/${usuarioId}`);
                
                if (!response.success) {
                    throw new Error(response.message || 'Erro ao carregar usuário');
                }

                const usuario = response.usuario;
                
                // Preencher formulário
                document.getElementById('usuarioId').value = usuario.id;
                document.getElementById('usuarioNome').value = usuario.nome;
                document.getElementById('usuarioCpf').value = usuario.cpf;
                document.getElementById('usuarioPerfil').value = usuario.tipo.toLowerCase();
                document.getElementById('usuarioStatus').value = usuario.status ? 'true' : 'false';
                document.getElementById('usuarioObservacoes').value = usuario.observacoes || '';
                
                // Limpar campos de senha
                document.getElementById('usuarioSenha').value = '';
                document.getElementById('usuarioConfirmaSenha').value = '';
                
                // Aplicar máscara ao CPF
                if (usuario.cpf && typeof $ !== 'undefined') {
                    $(document.getElementById('usuarioCpf')).mask('000.000.000-00');
                }
            } catch (error) {
                console.error('Erro ao carregar dados do usuário:', error);
                showFlashMessage('error', error.message || 'Erro ao carregar dados do usuário');
                return; // Não abrir o modal se houver erro
            }
        } else {
            // Aplicar máscara ao CPF para novo usuário
            if (typeof $ !== 'undefined') {
                $(document.getElementById('usuarioCpf')).mask('000.000.000-00');
            }
        }
        
        openModal('usuarioModal');
    }

    // Formulário de usuário
    document.getElementById('usuarioForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const isEdit = document.getElementById('usuarioId').value !== '';
        const usuarioId = document.getElementById('usuarioId').value;
        
        const formData = {
            nome: document.getElementById('usuarioNome').value,
            cpf: document.getElementById('usuarioCpf').value,
            tipo: document.getElementById('usuarioPerfil').value,
            status: document.getElementById('usuarioStatus').value === 'true',
            observacoes: document.getElementById('usuarioObservacoes').value
        };
        
        // Verificar se há senha sendo enviada (tanto para edição quanto cadastro)
        const senha = document.getElementById('usuarioSenha').value;
        const confirmaSenha = document.getElementById('usuarioConfirmaSenha').value;
        
        if (senha || confirmaSenha) {
            if (senha !== confirmaSenha) {
                showFlashMessage('error', 'As senhas não coincidem');
                return;
            }
            if (senha.length > 0) { // Só adiciona se não estiver vazia
                formData.senha = senha;
                formData.confirma_senha = confirmaSenha;
            }
        }
        
        try {
            const url = isEdit ? `/admin/usuarios/${usuarioId}` : '/admin/usuarios';
            const method = isEdit ? 'PUT' : 'POST';
            
            const response = await fetchWithErrorHandling(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.success) {
                showFlashMessage('success', `Usuário ${isEdit ? 'atualizado' : 'cadastrado'} com sucesso`);
                closeModal('usuarioModal');
                loadUsuariosData();
            } else {
                showFlashMessage('error', response.message || `Erro ao ${isEdit ? 'atualizar' : 'cadastrar'} usuário`);
            }
        } catch (error) {
            console.error(`Erro ao ${isEdit ? 'atualizar' : 'cadastrar'} usuário:`, error);
            showFlashMessage('error', `Erro ao ${isEdit ? 'atualizar' : 'cadastrar'} usuário`);
        }
    });

    // Função para abrir modal de visualização de usuário
    async function openVisualizarUsuarioModal(usuarioId) {
        try {
            const response = await fetchWithErrorHandling(`/admin/usuarios/${usuarioId}`);
            
            if (response.success) {
                const usuario = response.usuario;
                
                document.getElementById('visualizarUsuarioNome').textContent = usuario.nome;
                document.getElementById('visualizarUsuarioCPF').textContent = usuario.cpf;
                document.getElementById('visualizarUsuarioUltimoAcesso').textContent = usuario.ultimo_acesso || 'Nunca acessou';
                document.getElementById('visualizarUsuarioDataCadastro').textContent = usuario.data_cadastro || 'Data não disponível';
                document.getElementById('visualizarUsuarioObservacoes').textContent = usuario.observacoes || 'Nenhuma observação';
                
                // Configurar badge de perfil
                const perfilBadge = document.getElementById('visualizarUsuarioPerfil');
                perfilBadge.textContent = formatPerfil(usuario.tipo);
                perfilBadge.className = 'badge';
                perfilBadge.classList.add(`badge-${usuario.tipo.toLowerCase()}`);
                
                // Configurar badge de status
                const statusBadge = document.getElementById('visualizarUsuarioStatus');
                statusBadge.textContent = usuario.status ? 'Ativo' : 'Inativo';
                statusBadge.className = 'badge';
                statusBadge.classList.add(usuario.status ? 'badge-success' : 'badge-danger');

                openModal('visualizarUsuarioModal');
            }
        } catch (error) {
            console.error('Erro ao carregar dados do usuário:', error);
            showFlashMessage('error', 'Erro ao carregar dados do usuário');
        }
    }

    // Configurar ações dos botões de usuário
    function setupUsuarioActions() {
        document.querySelectorAll('.visualizar-usuario').forEach(btn => {
            btn.addEventListener('click', function() {
                const usuarioId = this.getAttribute('data-id');
                openVisualizarUsuarioModal(usuarioId);
            });
        });

        document.querySelectorAll('.editar-usuario').forEach(btn => {
            btn.addEventListener('click', function() {
                const usuarioId = this.getAttribute('data-id');
                openEditarUsuarioModal(usuarioId);
            });
        });

        document.querySelectorAll('.alterar-status-usuario').forEach(btn => {
            btn.addEventListener('click', async function() {
                const usuarioId = this.getAttribute('data-id');
                const currentStatus = this.getAttribute('data-status') === 'Ativo';
                const newStatus = !currentStatus;
                
                if (confirm(`Tem certeza que deseja ${currentStatus ? 'desativar' : 'ativar'} este usuário?`)) {
                    try {
                        const response = await fetchWithErrorHandling(`/admin/usuarios/${usuarioId}`, {
                            method: 'PUT',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ 
                                status: newStatus
                            })
                        });
                        
                        if (response.success) {
                            showFlashMessage('success', `Usuário ${newStatus ? 'ativado' : 'desativado'} com sucesso`);
                            loadUsuariosData();
                        } else {
                            showFlashMessage('error', response.message || 'Erro ao alterar status do usuário');
                        }
                    } catch (error) {
                        console.error('Erro ao alterar status do usuário:', error);
                        showFlashMessage('error', 'Erro ao alterar status do usuário');
                    }
                }
            });
        });

        document.querySelectorAll('.remover-usuario').forEach(btn => {
            btn.addEventListener('click', function() {
                const usuarioId = this.getAttribute('data-id');
                document.getElementById('confirmarExclusaoTexto').textContent = `Tem certeza que deseja excluir permanentemente o usuário ${usuarioId}?`;
                document.getElementById('confirmarExclusaoBtn').setAttribute('data-id', usuarioId);
                document.getElementById('confirmarExclusaoBtn').setAttribute('data-type', 'usuario');
                openModal('confirmarExclusaoModal');
            });
        });
    }

    // Função para carregar dados de usuários
    async function loadUsuariosData() {
        try {
            const searchText = document.getElementById('searchUsuario').value.toLowerCase();
            const data = await fetchWithErrorHandling('/admin/usuarios');
            
            if (data.success) {
                const usuariosTable = document.querySelector('#usuariosTable tbody');
                usuariosTable.innerHTML = '';
                
                data.usuarios.forEach(usuario => {
                    if (searchText && !usuario.nome.toLowerCase().includes(searchText)) {
                        return;
                    }
                    
                    const statusBool = usuario.status === true || usuario.status === 'true' || usuario.status === 'Ativo';
                    const status = statusBool ? 'Ativo' : 'Inativo';
                    
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${usuario.id}</td>
                        <td>${usuario.nome}</td>
                        <td><span class="badge badge-${usuario.tipo.toLowerCase()}">${formatPerfil(usuario.tipo)}</span></td>
                        <td><span class="badge ${statusBool ? 'badge-success' : 'badge-danger'}">${status}</span></td>
                        <td>${usuario.ultimo_acesso || 'Nunca'}</td>
                        <td>
                            <div class="table-actions">
                                <button class="btn-icon btn-primary visualizar-usuario" data-id="${usuario.id}" title="Visualizar">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn-icon btn-warning editar-usuario" data-id="${usuario.id}" title="Editar">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn-icon ${statusBool ? 'btn-danger' : 'btn-success'} alterar-status-usuario" 
                                        data-id="${usuario.id}" 
                                        data-status="${status}"
                                        title="${statusBool ? 'Desativar' : 'Ativar'}">
                                    <i class="fas ${statusBool ? 'fa-user-slash' : 'fa-user-check'}"></i>
                                </button>
                                <button class="btn-icon btn-danger remover-usuario" data-id="${usuario.id}" title="Remover">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    `;
                    usuariosTable.appendChild(row);
                });
                
                // Adicionar eventos aos botões de ação
                setupUsuarioActions();
            }
        } catch (error) {
            console.error('Erro ao carregar usuários:', error);
            showFlashMessage('error', 'Erro ao carregar lista de usuários');
        }
    }

    // Funções auxiliares para formatar texto
    function formatPerfil(perfil) {
        const perfis = {
            'admin': 'Administrador',
            'operador': 'Operador',
        };
        return perfis[perfil.toLowerCase()] || perfil;
    }

    function formatStatus(status) {
        const statusMap = {
            'ativo': 'Ativo',
            'inativo': 'Inativo',
        };
        return statusMap[status.toLowerCase()] || status;
    }

    // ===== Formulários =====
    // Formulário de produto
    // Função para limpar campos do formulário de produto
    function limparCamposProduto() {
        document.getElementById('produtoCodigo').value = '';
        document.getElementById('produtoNome').value = '';
        document.getElementById('produtoTipo').value = '';
        document.getElementById('produtoMarca').value = '';
        document.getElementById('produtoUnidade').value = 'kg';
        document.getElementById('produtoValor').value = '';
        document.getElementById('produtoEstoqueTipo').value = 'loja';
        document.getElementById('produtoEstoque').value = '';
    }

    // Limpar campos quando o modal é aberto
    document.getElementById('produtoModal').addEventListener('show.bs.modal', function() {
        limparCamposProduto();
    });

    // Formulário de produto
    document.getElementById('produtoForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const estoqueTipo = document.getElementById('produtoEstoqueTipo').value;
        const estoqueQuantidade = document.getElementById('produtoEstoque').value;
        
        const formData = {
            codigo: document.getElementById('produtoCodigo').value,
            nome: document.getElementById('produtoNome').value,
            tipo: document.getElementById('produtoTipo').value,
            marca: document.getElementById('produtoMarca').value,
            unidade: document.getElementById('produtoUnidade').value,
            valor_unitario: document.getElementById('produtoValor').value,
            estoque_loja: estoqueTipo === 'loja' ? estoqueQuantidade : 0,
            estoque_deposito: estoqueTipo === 'deposito' ? estoqueQuantidade : 0,
            estoque_fabrica: estoqueTipo === 'fabrica' ? estoqueQuantidade : 0
        };
        
        try {
            const response = await fetchWithErrorHandling('/admin/produtos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.success) {
                showFlashMessage('success', 'Produto cadastrado com sucesso');
                closeModal('produtoModal');
                loadProdutosData();
            } else {
                showFlashMessage('error', response.message || 'Erro ao cadastrar produto');
            }
        } catch (error) {
            console.error('Erro ao cadastrar produto:', error);
            showFlashMessage('error', 'Erro ao cadastrar produto');
        }
    });

    // Formulário de entrada de produto
    document.getElementById('entradaForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const produtoId = this.getAttribute('data-produto-id');
        const formData = {
            tipo: 'entrada',
            quantidade: document.getElementById('entradaQuantidade').value,
            valor_unitario: document.getElementById('entradaValor').value,
            nota_fiscal: document.getElementById('entradaNota').value
        };
        
        try {
            const response = await fetchWithErrorHandling(`/admin/produtos/${produtoId}/movimentacao`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.success) {
                showFlashMessage('success', 'Entrada de produto registrada com sucesso');
                closeModal('entradaModal');
                loadDashboardData();
                loadProdutosData();
            } else {
                showFlashMessage('error', response.message || 'Erro ao registrar entrada de produto');
            }
        } catch (error) {
            console.error('Erro ao registrar entrada de produto:', error);
            showFlashMessage('error', 'Erro ao registrar entrada de produto');
        }
    });

    // Formulário de edição de produto
    document.getElementById('editarProdutoForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const produtoId = this.getAttribute('data-produto-id');
        const formData = {
            codigo: document.getElementById('editCodigo').value,
            nome: document.getElementById('editNome').value,
            tipo: document.getElementById('editTipo').value,
            marca: document.getElementById('editMarca').value,
            unidade: document.getElementById('editUnidade').value,
            valor_unitario: document.getElementById('editValor').value,
            estoque_quantidade: document.getElementById('editEstoque').value
        };
        
        try {
            const response = await fetchWithErrorHandling(`/admin/produtos/${produtoId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.success) {
                showFlashMessage('success', 'Produto atualizado com sucesso');
                closeModal('editarProdutoModal');
                loadProdutosData();
            } else {
                showFlashMessage('error', response.message || 'Erro ao atualizar produto');
            }
        } catch (error) {
            console.error('Erro ao atualizar produto:', error);
            showFlashMessage('error', 'Erro ao atualizar produto');
        }
    });

    // Confirmar exclusão
    document.getElementById('confirmarExclusaoBtn').addEventListener('click', async function() {
        const id = this.getAttribute('data-id');
        const type = this.getAttribute('data-type');
        
        try {
            let url;
            if (type === 'produto') {
                url = `/admin/produtos/${id}`;
            } else if (type === 'cliente') {
                url = `/admin/clientes/${id}`;
            } else if (type === 'usuario') {
                url = `/admin/usuarios/${id}`;
            }
            
            const response = await fetchWithErrorHandling(url, {
                method: 'DELETE'
            });
            
            if (response.success) {
                showFlashMessage('success', `${type.charAt(0).toUpperCase() + type.slice(1)} excluído com sucesso`);
                closeModal('confirmarExclusaoModal');
                
                if (type === 'produto') loadProdutosData();
                if (type === 'cliente') loadClientesData();
                if (type === 'usuario') loadUsuariosData();
            } else {
                showFlashMessage('error', response.message || `Erro ao excluir ${type}`);
            }
        } catch (error) {
            console.error(`Erro ao excluir ${type}:`, error);
            showFlashMessage('error', `Erro ao excluir ${type}`);
        }
    });

    // Filtros
    document.getElementById('searchCliente').addEventListener('input', loadClientesData);
    document.getElementById('searchProduto').addEventListener('input', loadProdutosData);
    document.getElementById('searchUsuario').addEventListener('input', loadUsuariosData);

    // Botões de atualização
    document.getElementById('refreshData').addEventListener('click', loadDashboardData);
    document.getElementById('refreshClientes').addEventListener('click', loadClientesData);
    document.getElementById('refreshProdutos').addEventListener('click', loadProdutosData);
    document.getElementById('refreshUsuarios').addEventListener('click', loadUsuariosData);
    document.getElementById('filterFinanceiro').addEventListener('click', loadFinanceiroData);

    // Verificar caixa aberto ao carregar a página
    async function checkCaixaStatus() {
        try {
            const response = await fetchWithErrorHandling('/admin/caixa/status');
            
            if (response.success && response.aberto) {
                showFlashMessage('info', `Caixa aberto por ${response.caixa.operador} com valor de R$ ${response.caixa.valor_abertura}`);
            }
        } catch (error) {
            console.error('Erro ao verificar status do caixa:', error);
        }
    }

    // Carregar dados iniciais
    async function loadInitialData() {
        try {
            await Promise.all([
                loadDashboardData(),
                loadClientesData(),
                loadProdutosData(),
                loadFinanceiroData(),
                loadUsuariosData(),
                checkCaixaStatus()
            ]);
        } catch (error) {
            console.error('Erro ao carregar dados iniciais:', error);
        }
    }

    loadInitialData();
});