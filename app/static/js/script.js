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
    document.getElementById('addCliente').addEventListener('click', () => openModal('clienteModal'));
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

    // Carregar dados de clientes
    async function loadClientesData() {
        try {
            const searchText = document.getElementById('searchCliente').value.toLowerCase();
            const data = await fetchWithErrorHandling('/admin/clientes');
            
            if (data.success) {
                const clientesTable = document.querySelector('#clientesTable tbody');
                clientesTable.innerHTML = '';
                
                data.clientes.forEach(cliente => {
                    if (searchText && !cliente.nome.toLowerCase().includes(searchText)) {
                        return;
                    }
                    
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${cliente.id}</td>
                        <td>${cliente.nome}</td>
                        <td>${cliente.documento || ''}</td>
                        <td>${cliente.telefone || ''}</td>
                        <td>${cliente.email || ''}</td>
                        <td><span class="badge ${cliente.status === 'Ativo' ? 'badge-success' : 'badge-danger'}">${cliente.status}</span></td>
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
                
                // Adicionar eventos aos botões de ação
                setupClienteActions();
            }
        } catch (error) {
            console.error('Erro ao carregar clientes:', error);
            showFlashMessage('error', 'Erro ao carregar lista de clientes');
        }
    }

    function setupClienteActions() {
        document.querySelectorAll('.editar-cliente').forEach(btn => {
            btn.addEventListener('click', function() {
                const clienteId = this.getAttribute('data-id');
                // Implementar edição do cliente
                alert(`Editar cliente ${clienteId}`);
            });
        });

        document.querySelectorAll('.remover-cliente').forEach(btn => {
            btn.addEventListener('click', function() {
                const clienteId = this.getAttribute('data-id');
                document.getElementById('confirmarExclusaoTexto').textContent = `Tem certeza que deseja excluir o cliente ${clienteId}?`;
                document.getElementById('confirmarExclusaoBtn').setAttribute('data-id', clienteId);
                document.getElementById('confirmarExclusaoBtn').setAttribute('data-type', 'cliente');
                openModal('confirmarExclusaoModal');
            });
        });
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
                        <td>${produto.estoque}</td>
                        <td>
                            <div class="table-actions">
                                <button class="btn-icon btn-success entrada-produto" data-id="${produto.id}" data-nome="${produto.nome}" title="Entrada">
                                    <i class="fas fa-plus"></i>
                                </button>
                                <button class="btn-icon btn-danger saida-produto" data-id="${produto.id}" data-nome="${produto.nome}" title="Saída">
                                    <i class="fas fa-minus"></i>
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
        document.querySelectorAll('.entrada-produto').forEach(btn => {
            btn.addEventListener('click', function() {
                const produtoId = this.getAttribute('data-id');
                const produtoNome = this.getAttribute('data-nome');
                
                document.getElementById('entradaProdutoNome').textContent = produtoNome;
                document.getElementById('entradaForm').setAttribute('data-produto-id', produtoId);
                openModal('entradaModal');
            });
        });

        document.querySelectorAll('.saida-produto').forEach(btn => {
            btn.addEventListener('click', async function() {
                const produtoId = this.getAttribute('data-id');
                const produtoNome = this.getAttribute('data-nome');
                
                document.getElementById('saidaProdutoNome').textContent = produtoNome;
                document.getElementById('saidaForm').setAttribute('data-produto-id', produtoId);
                
                // Carregar clientes para o select
                try {
                    const data = await fetchWithErrorHandling('/admin/clientes');
                    
                    const clienteSelect = document.getElementById('saidaCliente');
                    clienteSelect.innerHTML = '<option value="">Selecione um cliente</option>';
                    
                    if (data.success) {
                        data.clientes.forEach(cliente => {
                            const option = document.createElement('option');
                            option.value = cliente.id;
                            option.textContent = cliente.nome;
                            clienteSelect.appendChild(option);
                        });
                    }
                } catch (error) {
                    console.error('Erro ao carregar clientes:', error);
                }
                
                openModal('saidaModal');
            });
        });

        document.querySelectorAll('.editar-produto').forEach(btn => {
            btn.addEventListener('click', async function() {
                const produtoId = this.getAttribute('data-id');
                
                try {
                    const data = await fetchWithErrorHandling(`/admin/produtos/${produtoId}`);
                    
                    if (data.success) {
                        const produto = data.produto;
                        const formBody = document.querySelector('#editarProdutoModal .modal-body');
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
                                    <input type="number" id="editValor" class="form-control" value="${produto.valor.replace('R$ ', '')}" step="0.01" min="0" required>
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="editEstoque">Quantidade em Estoque*</label>
                                <input type="number" id="editEstoque" class="form-control" value="${produto.estoque.split(' ')[0]}" step="0.001" min="0" required>
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
    }

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

    // Carregar dados de usuários
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
                    
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${usuario.id}</td>
                        <td>${usuario.nome}</td>
                        <td><span class="badge badge-${usuario.tipo.toLowerCase()}">${formatPerfil(usuario.tipo)}</span></td>
                        <td><span class="badge badge-${usuario.status.toLowerCase()}">${formatStatus(usuario.status)}</span></td>
                        <td>${usuario.ultimo_acesso}</td>
                        <td>
                            <div class="table-actions">
                                <button class="btn-icon btn-primary visualizar-usuario" data-id="${usuario.id}" title="Visualizar">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn-icon btn-warning editar-usuario" data-id="${usuario.id}" title="Editar">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn-icon ${usuario.status === 'Ativo' ? 'btn-danger' : 'btn-success'} alterar-status-usuario" 
                                        data-id="${usuario.id}" 
                                        data-status="${usuario.status}"
                                        title="${usuario.status === 'Ativo' ? 'Desativar' : 'Reativar'}">
                                    <i class="fas ${usuario.status === 'Ativo' ? 'fa-user-slash' : 'fa-user-check'}"></i>
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
            'gerente': 'Gerente',
            'operador': 'Operador',
            'visualizador': 'Visualizador'
        };
        return perfis[perfil.toLowerCase()] || perfil;
    }

    function formatStatus(status) {
        const statusMap = {
            'ativo': 'Ativo',
            'inativo': 'Inativo',
            'bloqueado': 'Bloqueado'
        };
        return statusMap[status.toLowerCase()] || status;
    }

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
                const currentStatus = this.getAttribute('data-status');
                const newStatus = currentStatus === 'Ativo' ? 'inativo' : 'ativo';
                
                if (confirm(`Tem certeza que deseja ${currentStatus === 'Ativo' ? 'desativar' : 'reativar'} este usuário?`)) {
                    try {
                        const response = await fetchWithErrorHandling(`/admin/usuarios/${usuarioId}/status`, {
                            method: 'PUT',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ status: newStatus })
                        });
                        
                        if (response.success) {
                            showFlashMessage('success', `Usuário ${currentStatus === 'Ativo' ? 'desativado' : 'reativado'} com sucesso`);
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

    // Função para abrir modal de visualização de usuário
    async function openVisualizarUsuarioModal(usuarioId) {
        try {
            const data = await fetchWithErrorHandling(`/admin/usuarios/${usuarioId}`);
            
            if (data.success) {
                const usuario = data.usuario;
                
                document.getElementById('visualizarUsuarioNome').textContent = usuario.nome;
                document.getElementById('visualizarUsuarioCPF').textContent = usuario.cpf;
                document.getElementById('visualizarUsuarioUltimoAcesso').textContent = usuario.ultimo_acesso;
                document.getElementById('visualizarUsuarioDataCadastro').textContent = usuario.data_cadastro;
                document.getElementById('visualizarUsuarioObservacoes').textContent = usuario.observacoes || 'Nenhuma observação';
                
                // Configurar badge de perfil
                const perfilBadge = document.getElementById('visualizarUsuarioPerfil');
                perfilBadge.textContent = usuario.tipo;
                perfilBadge.className = 'badge';
                perfilBadge.classList.add(`badge-${usuario.tipo.toLowerCase()}`);
                
                // Configurar badge de status
                const statusBadge = document.getElementById('visualizarUsuarioStatus');
                statusBadge.textContent = usuario.status;
                statusBadge.className = 'badge';
                statusBadge.classList.add(`badge-${usuario.status.toLowerCase()}`);

                openModal('visualizarUsuarioModal');
            }
        } catch (error) {
            console.error('Erro ao carregar dados do usuário:', error);
            showFlashMessage('error', 'Erro ao carregar dados do usuário');
        }
    }

    // Função para abrir modal de edição/cadastro de usuário
    function openEditarUsuarioModal(usuarioId = null) {
        const isEdit = usuarioId !== null;
        
        // Configurar o modal conforme o modo (edição ou cadastro)
        document.getElementById('usuarioModalTitle').textContent = isEdit ? 'Editar Usuário' : 'Cadastrar Usuário';
        document.getElementById('usuarioModalSubmitText').textContent = isEdit ? 'Atualizar' : 'Cadastrar';
        
        // Mostrar/ocultar campo de senha conforme necessário
        document.getElementById('usuarioSenhaGroup').style.display = isEdit ? 'none' : 'block';
        if (!isEdit) {
            document.getElementById('usuarioSenha').required = true;
        }
        
        // Configurar ações extras para edição
        const extraActions = document.getElementById('usuarioModalExtraActions');
        extraActions.innerHTML = '';
        
        if (isEdit) {
            // Carregar dados do usuário
            fetchWithErrorHandling(`/admin/usuarios/${usuarioId}`)
                .then(data => {
                    if (data.success) {
                        const usuario = data.usuario;
                        
                        document.getElementById('usuarioId').value = usuario.id;
                        document.getElementById('usuarioNome').value = usuario.nome;
                        document.getElementById('usuarioCpf').value = usuario.cpf;
                        document.getElementById('usuarioPerfil').value = usuario.tipo.toLowerCase();
                        document.getElementById('usuarioStatus').value = usuario.status.toLowerCase();
                        document.getElementById('usuarioObservacoes').value = usuario.observacoes || '';
                        
                        // Adicionar botão para redefinir senha
                        const resetPasswordBtn = document.createElement('button');
                        resetPasswordBtn.type = 'button';
                        resetPasswordBtn.className = 'btn btn-secondary';
                        resetPasswordBtn.innerHTML = '<i class="fas fa-key"></i> <span>Redefinir Senha</span>';
                        resetPasswordBtn.addEventListener('click', function() {
                            if (confirm(`Tem certeza que deseja redefinir a senha do usuário ${usuarioId}?`)) {
                                fetchWithErrorHandling(`/admin/usuarios/${usuarioId}/reset-password`, {
                                    method: 'POST'
                                })
                                .then(response => {
                                    if (response.success) {
                                        showFlashMessage('success', 'Senha redefinida com sucesso');
                                    } else {
                                        showFlashMessage('error', response.message || 'Erro ao redefinir senha');
                                    }
                                })
                                .catch(error => {
                                    console.error('Erro ao redefinir senha:', error);
                                    showFlashMessage('error', 'Erro ao redefinir senha');
                                });
                            }
                        });
                        extraActions.appendChild(resetPasswordBtn);
                        
                        // Adicionar botão para bloquear/desbloquear se necessário
                        if (usuario.status === 'Ativo' || usuario.status === 'Bloqueado') {
                            const blockBtn = document.createElement('button');
                            blockBtn.type = 'button';
                            blockBtn.className = 'btn btn-warning';
                            blockBtn.innerHTML = `<i class="fas ${usuario.status === 'Ativo' ? 'fa-lock' : 'fa-unlock'}"></i> <span>${usuario.status === 'Ativo' ? 'Bloquear' : 'Desbloquear'}</span>`;
                            blockBtn.addEventListener('click', function() {
                                const action = usuario.status === 'Ativo' ? 'bloquear' : 'desbloquear';
                                if (confirm(`Tem certeza que deseja ${action} o usuário ${usuarioId}?`)) {
                                    fetchWithErrorHandling(`/admin/usuarios/${usuarioId}/status`, {
                                        method: 'PUT',
                                        headers: {
                                            'Content-Type': 'application/json'
                                        },
                                        body: JSON.stringify({ 
                                            status: usuario.status === 'Ativo' ? 'bloqueado' : 'ativo'
                                        })
                                    })
                                    .then(response => {
                                        if (response.success) {
                                            showFlashMessage('success', `Usuário ${action === 'bloquear' ? 'bloqueado' : 'desbloqueado'} com sucesso`);
                                            loadUsuariosData();
                                            closeModal('usuarioModal');
                                        } else {
                                            showFlashMessage('error', response.message || `Erro ao ${action} usuário`);
                                        }
                                    })
                                    .catch(error => {
                                        console.error(`Erro ao ${action} usuário:`, error);
                                        showFlashMessage('error', `Erro ao ${action} usuário`);
                                    });
                                }
                            });
                            extraActions.appendChild(blockBtn);
                        }
                    }
                })
                .catch(error => {
                    console.error('Erro ao carregar dados do usuário:', error);
                    showFlashMessage('error', 'Erro ao carregar dados do usuário');
                });
        } else {
            // Limpar formulário para novo cadastro
            document.getElementById('usuarioForm').reset();
            document.getElementById('usuarioId').value = '';
        }
        
        openModal('usuarioModal');
    }

    // ===== Formulários =====
    
    // Formulário de cliente
    document.getElementById('clienteForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            nome: document.getElementById('clienteNome').value,
            documento: document.getElementById('clienteDocumento').value,
            telefone: document.getElementById('clienteTelefone').value,
            email: document.getElementById('clienteEmail').value,
            endereco: document.getElementById('clienteEndereco').value
        };
        
        try {
            const response = await fetchWithErrorHandling('/admin/clientes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.success) {
                showFlashMessage('success', 'Cliente cadastrado com sucesso');
                closeModal('clienteModal');
                loadClientesData();
            } else {
                showFlashMessage('error', response.message || 'Erro ao cadastrar cliente');
            }
        } catch (error) {
            console.error('Erro ao cadastrar cliente:', error);
            showFlashMessage('error', 'Erro ao cadastrar cliente');
        }
    });

    // Formulário de produto
    document.getElementById('produtoForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            codigo: document.getElementById('produtoCodigo').value,
            nome: document.getElementById('produtoNome').value,
            tipo: document.getElementById('produtoTipo').value,
            marca: document.getElementById('produtoMarca').value,
            unidade: document.getElementById('produtoUnidade').value,
            valor_unitario: document.getElementById('produtoValor').value,
            estoque_quantidade: document.getElementById('produtoEstoque').value
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

    // Formulário de saída de produto
    document.getElementById('saidaForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const produtoId = this.getAttribute('data-produto-id');
        const formData = {
            tipo: 'saida',
            quantidade: document.getElementById('saidaQuantidade').value,
            valor_unitario: document.getElementById('saidaValor').value,
            cliente_id: document.getElementById('saidaCliente').value || null
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
                showFlashMessage('success', 'Saída de produto registrada com sucesso');
                closeModal('saidaModal');
                loadDashboardData();
                loadProdutosData();
            } else {
                showFlashMessage('error', response.message || 'Erro ao registrar saída de produto');
            }
        } catch (error) {
            console.error('Erro ao registrar saída de produto:', error);
            showFlashMessage('error', 'Erro ao registrar saída de produto');
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

    // Formulário de usuário
    document.getElementById('usuarioForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const isEdit = document.getElementById('usuarioId').value !== '';
        const usuarioId = document.getElementById('usuarioId').value;
        
        const formData = {
            nome: document.getElementById('usuarioNome').value,
            cpf: document.getElementById('usuarioCpf').value,
            tipo: document.getElementById('usuarioPerfil').value,
            status: document.getElementById('usuarioStatus').value,
            observacoes: document.getElementById('usuarioObservacoes').value
        };
        
        if (!isEdit) {
            formData.senha = document.getElementById('usuarioSenha').value;
            formData.cpf = document.getElementById('usuarioCpf').value;
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