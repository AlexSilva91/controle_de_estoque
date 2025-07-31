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

  // Menu Mobile
  const mobileMenuToggle = document.getElementById('mobileMenuToggle');
  const sidebar = document.querySelector('.sidebar');

  mobileMenuToggle.addEventListener('click', function() {
    this.classList.toggle('active');
    sidebar.classList.toggle('active');
  });

  // Fechar menu ao clicar em um item (para mobile)
  document.querySelectorAll('.sidebar-nav li').forEach(item => {
    item.addEventListener('click', function() {
      if (window.innerWidth <= 768) {
        mobileMenuToggle.classList.remove('active');
        sidebar.classList.remove('active');
      }
    });
  });

  // Navegação por abas
  const navItems = document.querySelectorAll('.sidebar-nav li');
  const tabContents = document.querySelectorAll('.tab-content');
  const pageTitle = document.getElementById('page-title');
  const breadcrumb = document.querySelector('.breadcrumb');
  
  navItems.forEach(item => {
    item.addEventListener('click', function() {
      navItems.forEach(nav => nav.classList.remove('active'));
      tabContents.forEach(content => content.classList.remove('active'));
      
      this.classList.add('active');
      const tabId = this.getAttribute('data-tab');
      document.getElementById(tabId).classList.add('active');
      
      const tabName = this.querySelector('span').textContent;
      pageTitle.textContent = tabName;
      breadcrumb.textContent = `Home / ${tabName}`;

      // Carregar dados específicos da aba quando ativada
      if (tabId === 'dashboard') loadDashboardData();
      if (tabId === 'clientes') loadClientesData();
      if (tabId === 'produtos') loadProdutosData();
      if (tabId === 'financeiro') loadFinanceiroData();
      if (tabId === 'usuarios') loadUsuariosData();
      if (tabId === 'estoque') loadMovimentacoesData();
      if (tabId === 'descontos') loadDescontosData();
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
      <button class="close-flash" aria-label="Fechar">&times;</button>
    `;
    
    flashContainer.appendChild(flashMessage);
    
    // Fechar mensagem ao clicar no botão
    flashMessage.querySelector('.close-flash').addEventListener('click', () => {
      flashMessage.remove();
    });
    
    // Auto-close flash messages after 5 seconds
    setTimeout(() => {
      flashMessage.classList.add('fade-out');
      setTimeout(() => flashMessage.remove(), 500);
    }, 5000);
  }

  // Processar mensagens flash do Flask ao carregar a página
  document.querySelectorAll('.flash-message').forEach(message => {
    const closeBtn = message.querySelector('.close-flash');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        message.remove();
      });
    }
    
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
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Erro na requisição:', error);
      showFlashMessage('error', error.message || 'Erro ao comunicar com o servidor');
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

  // ===== CLIENTES =====
  // Função para abrir modal de edição de cliente
  async function openEditarClienteModal(clienteId) {
    // Resetar formulário
    document.getElementById('clienteForm').reset();
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
        document.getElementById('clienteStatus').value = cliente.ativo ? 'true' : 'false';
      } else {
        showFlashMessage('error', 'Erro ao carregar dados do cliente');
        return;
      }
    } catch (error) {
      console.error('Erro ao carregar cliente:', error);
      showFlashMessage('error', 'Erro ao carregar dados do cliente');
      return;
    }

    openModal('clienteModal');
  }

  // Submissão do formulário de cliente
  document.getElementById('clienteForm').addEventListener('submit', async function(e) {
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
      btn.addEventListener('click', function() {
        const clienteId = this.getAttribute('data-id');
        openEditarClienteModal(clienteId);
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

          const status = cliente.ativo === 'Ativo' || cliente.ativo === true ? 'Ativo' : 'Inativo';

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

  // ===== PRODUTOS =====
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
                  <label for="editUnidade">Unidade</label>
                  <input type="text" id="editUnidade" class="form-control" value="${produto.unidade}" disabled>
                </div>
                <div class="form-group">
                  <label for="editValor">Valor Unitário*</label>
                  <input type="number" id="editValor" class="form-control" value="${valorUnitario}" step="0.01" min="0" required>
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="editValorCompra">Valor Unitário de Compra</label>
                  <input type="number" id="editValorCompra" class="form-control" value="${produto.valor_unitario_compra || ''}" step="0.01" min="0">
                </div>
                <div class="form-group">
                  <label for="editValorTotalCompra">Valor Total de Compra</label>
                  <input type="number" id="editValorTotalCompra" class="form-control" value="${produto.valor_total_compra || ''}" step="0.01" min="0">
                </div>
                <div class="form-group">
                  <label for="editICMS">ICMS (%)</label>
                  <input type="number" id="editICMS" class="form-control" value="${produto.imcs || ''}" step="0.01" min="0">
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="editEstoqueLoja">Estoque Loja</label>
                  <input type="number" id="editEstoqueLoja" class="form-control" value="${produto.estoque_loja}" step="0.001" min="0">
                </div>
                <div class="form-group">
                  <label for="editEstoqueDeposito">Estoque Depósito</label>
                  <input type="number" id="editEstoqueDeposito" class="form-control" value="${produto.estoque_deposito}" step="0.001" min="0">
                </div>
                <div class="form-group">
                  <label for="editEstoqueFabrica">Estoque Fábrica</label>
                  <input type="number" id="editEstoqueFabrica" class="form-control" value="${produto.estoque_fabrica}" step="0.001" min="0">
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="editEstoqueMinimo">Estoque Mínimo</label>
                  <input type="number" id="editEstoqueMinimo" class="form-control" value="${produto.estoque_minimo || 0}" step="0.001" min="0">
                </div>
                <div class="form-group">
                  <label for="editEstoqueMaximo">Estoque Máximo</label>
                  <input type="number" id="editEstoqueMaximo" class="form-control" value="${produto.estoque_maximo || ''}" step="0.001" min="0">
                </div>
                <div class="form-group">
                  <label for="editAtivo">Ativo</label>
                  <select id="editAtivo" class="form-control">
                    <option value="true" ${produto.ativo ? 'selected' : ''}>Sim</option>
                    <option value="false" ${!produto.ativo ? 'selected' : ''}>Não</option>
                  </select>
                </div>
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
              document.getElementById('transferenciaUnidadeAtual').textContent = produto.unidade;
              
              // Resetar valores
              document.getElementById('transferenciaOrigem').value = 'loja';
              document.getElementById('transferenciaDestino').value = 'deposito';
              document.getElementById('transferenciaQuantidade').value = '';
              document.getElementById('transferenciaValorUnitarioDestino').value = produto.valor_unitario;
              document.getElementById('transferenciaObservacao').value = '';
              
              openModal('transferenciaModal');
              updateEstoqueDisponivel();
          }
      } catch (error) {
          console.error('Erro ao abrir modal de transferência:', error);
          showFlashMessage('error', 'Erro ao carregar dados do produto');
      }
  }

  // Formulário de transferência SEM conversão
  document.getElementById('transferenciaForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const produtoId = document.getElementById('transferenciaProdutoId').value;
      const origem = document.getElementById('transferenciaOrigem').value;
      const destino = document.getElementById('transferenciaDestino').value;
      const quantidade = parseFloat(document.getElementById('transferenciaQuantidade').value);
      const valorUnitarioDestino = parseFloat(document.getElementById('transferenciaValorUnitarioDestino').value);
      const observacao = document.getElementById('transferenciaObservacao').value;
      
      // Validações
      if (origem === destino) {
          showFlashMessage('error', 'Origem e destino não podem ser iguais');
          return;
      }
      
      if (quantidade <= 0 || isNaN(quantidade)) {
          showFlashMessage('error', 'Informe uma quantidade válida');
          return;
      }
      
      if (valorUnitarioDestino <= 0 || isNaN(valorUnitarioDestino)) {
          showFlashMessage('error', 'Informe um valor unitário válido');
          return;
      }
      
      try {
          const response = await fetchWithErrorHandling('/admin/transferencias', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                  produto_id: produtoId,
                  estoque_origem: origem,
                  estoque_destino: destino,
                  quantidade: quantidade,
                  valor_unitario_destino: valorUnitarioDestino,
                  observacao: observacao,
                  converter_unidade: false // Sempre false para transferência sem conversão
              })
          });
          
          if (response.success) {
              showFlashMessage('success', 'Transferência realizada com sucesso');
              closeModal('transferenciaModal');
              loadProdutosData();
              loadMovimentacoesData();
          } else {
              showFlashMessage('error', response.message || 'Erro ao realizar transferência');
          }
      } catch (error) {
          console.error('Erro ao realizar transferência:', error);
          showFlashMessage('error', error.message || 'Erro ao realizar transferência');
      }
  });

  // Atualizar estoque disponível quando origem muda
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

    const valorCompra = document.getElementById('produtoValorCompra').value;
    const valorTotal = document.getElementById('produtoValorTotalCompra').value;
    const icms = document.getElementById('produtoICMS').value;
    const estoqueMinimo = document.getElementById('produtoEstoqueMinimo').value;

    if (valorCompra) formData.valor_unitario_compra = valorCompra;
    if (valorTotal) formData.valor_total_compra = valorTotal;
    if (icms) formData.imcs = icms;
    if (estoqueMinimo) formData.estoque_minimo = estoqueMinimo;
    
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

  // Formulário de edição de produto
  document.getElementById('editarProdutoForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const produtoId = this.getAttribute('data-produto-id');
  const formData = {
    codigo: document.getElementById('editCodigo').value,
    nome: document.getElementById('editNome').value,
    tipo: document.getElementById('editTipo').value,
    marca: document.getElementById('editMarca').value,
    valor_unitario: document.getElementById('editValor').value,
    valor_unitario_compra: document.getElementById('editValorCompra').value,
    valor_total_compra: document.getElementById('editValorTotalCompra').value,
    imcs: document.getElementById('editICMS').value,
    estoque_loja: document.getElementById('editEstoqueLoja').value,
    estoque_deposito: document.getElementById('editEstoqueDeposito').value,
    estoque_fabrica: document.getElementById('editEstoqueFabrica').value,
    estoque_minimo: document.getElementById('editEstoqueMinimo').value,
    estoque_maximo: document.getElementById('editEstoqueMaximo').value,
    ativo: document.getElementById('editAtivo').value === 'true'
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

  // ===== MOVIMENTAÇÕES =====
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

  // ===== FINANCEIRO =====
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

  // ===== USUÁRIOS =====
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
      } catch (error) {
        console.error('Erro ao carregar dados do usuário:', error);
        showFlashMessage('error', error.message || 'Erro ao carregar dados do usuário');
        return; // Não abrir o modal se houver erro
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
        
        setupUsuarioActions();
      }
    } catch (error) {
      console.error('Erro ao carregar usuários:', error);
      showFlashMessage('error', 'Erro ao carregar lista de usuários');
    }
  }

  // ===== DESCONTOS =====
  async function loadDescontosData() {
      try {
          const searchText = document.getElementById('searchDesconto').value.toLowerCase();
          const data = await fetchWithErrorHandling('/admin/descontos');
          
          if (data.success) {
              const descontosTable = document.querySelector('#descontosTable tbody');
              descontosTable.innerHTML = '';
              
              data.descontos.forEach(desconto => {
                  if (searchText && !desconto.produto_nome.toLowerCase().includes(searchText)) {
                      return;
                  }
                  
                  const row = document.createElement('tr');
                  row.innerHTML = `
                      <td>${desconto.quantidade_minima}</td>
                      <td>${desconto.quantidade_maxima}</td>
                      <td>${desconto.valor_unitario_com_desconto}</td>
                      <td>${desconto.valido_ate || '-'}</td>
                      <td><span class="badge ${desconto.ativo ? 'badge-success' : 'badge-danger'}">${desconto.ativo ? 'Ativo' : 'Inativo'}</span></td>
                      <td>
                          <div class="table-actions">
                              <button class="btn-icon btn-warning editar-desconto" data-id="${desconto.id}" title="Editar">
                                  <i class="fas fa-edit"></i>
                              </button>
                              <button class="btn-icon btn-danger remover-desconto" data-id="${desconto.id}" title="Remover">
                                  <i class="fas fa-trash"></i>
                              </button>
                          </div>
                      </td>
                  `;
                  descontosTable.appendChild(row);
              });
              
              setupDescontoActions();
          }
      } catch (error) {
          console.error('Erro ao carregar descontos:', error);
          showFlashMessage('error', 'Erro ao carregar lista de descontos');
      }
  }

  function setupDescontoActions() {
      document.querySelectorAll('.editar-desconto').forEach(btn => {
          btn.addEventListener('click', function() {
              const descontoId = this.getAttribute('data-id');
              openEditarDescontoModal(descontoId);
          });
      });

      document.querySelectorAll('.remover-desconto').forEach(btn => {
          btn.addEventListener('click', function() {
              const descontoId = this.getAttribute('data-id');
              document.getElementById('confirmarExclusaoTexto').textContent = `Tem certeza que deseja excluir este desconto?`;
              document.getElementById('confirmarExclusaoBtn').setAttribute('data-id', descontoId);
              document.getElementById('confirmarExclusaoBtn').setAttribute('data-type', 'desconto');
              openModal('confirmarExclusaoModal');
          });
      });
  }

  // Função para limpar o valor monetário
  function limparValor(valor) {
      return parseFloat(valor.replace('R$', '').replace(',', '.').trim());
  }

  async function openEditarDescontoModal(descontoId) {
      try {
          const response = await fetchWithErrorHandling(`/admin/descontos/${descontoId}`);

          if (response.success) {
              const desconto = response.desconto;

              // Preencher o formulário com os dados do desconto
              document.getElementById('descontoId').value = desconto.id;
              document.getElementById('descontoProdutoId').value = desconto.produto_id;
              document.getElementById('descontoIdentificador').value = desconto.identificador;
              document.getElementById('descontoQuantidadeMinima').value = desconto.quantidade_minima;
              document.getElementById('descontoQuantidadeMaxima').value = desconto.quantidade_maxima;
              document.getElementById('descontoValorUnitario').value = limparValor(desconto.valor_unitario_com_desconto);

              // Tratamento da data para o formato 'YYYY-MM-DD'
              if (desconto.valido_ate) {
                  let dataValidoAte = desconto.valido_ate;

                  // Verificar se a data tem formato com hora e minuto
                  if (dataValidoAte.includes(' ')) {
                      dataValidoAte = dataValidoAte.split(' ')[0]; // Pega apenas a parte 'YYYY-MM-DD'
                  }

                  // Definir o valor do input de data
                  document.getElementById('descontoValidoAte').value = dataValidoAte;
              } else {
                  document.getElementById('descontoValidoAte').value = '';  // Se não houver data, limpa o campo
              }

              document.getElementById('descontoDescricao').value = desconto.descricao || '';
              document.getElementById('descontoAtivo').value = desconto.ativo ? 'true' : 'false';

              // Atualizar título do modal
              document.getElementById('descontoModalTitle').textContent = 'Editar Desconto';
              openModal('descontoModal');
          } else {
              showFlashMessage('error', response.erro || 'Erro ao carregar dados do desconto');
          }
      } catch (error) {
          console.error('Erro ao carregar dados do desconto:', error);
          showFlashMessage('error', 'Erro ao carregar dados do desconto');
      }
  }

  // Formulário de desconto
  document.getElementById('descontoForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const descontoId = document.getElementById('descontoId').value;
      const isEdit = descontoId !== '';
      
      const formData = {
          identificador: document.getElementById('descontoIdentificador').value,
          quantidade_minima: document.getElementById('descontoQuantidadeMinima').value,
          quantidade_maxima: document.getElementById('descontoQuantidadeMaxima').value,
          valor_unitario_com_desconto: document.getElementById('descontoValorUnitario').value,
          valido_ate: document.getElementById('descontoValidoAte').value || null,
          descricao: document.getElementById('descontoDescricao').value,
          ativo: document.getElementById('descontoAtivo').value === 'true'
      };
      
      const url = isEdit ? `/admin/descontos/${descontoId}` : '/admin/descontos';
      const method = isEdit ? 'PUT' : 'POST';
      
      try {
          const response = await fetchWithErrorHandling(url, {
              method: method,
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(formData)
          });
          
          if (response.success) {
              showFlashMessage('success', `Desconto ${isEdit ? 'atualizado' : 'cadastrado'} com sucesso`);
              closeModal('descontoModal');
              loadDescontosData();
          } else {
              showFlashMessage('error', response.message || `Erro ao salvar desconto`);
          }
      } catch (error) {
          console.error('Erro ao salvar desconto:', error);
          showFlashMessage('error', 'Erro ao salvar desconto');
      }
  });

  // Botão para adicionar novo desconto
  document.getElementById('addDesconto').addEventListener('click', () => {
      document.getElementById('descontoForm').reset();
      document.getElementById('descontoId').value = '';
      document.getElementById('descontoAtivo').value = 'true';
      document.getElementById('descontoModalTitle').textContent = 'Cadastrar Desconto';
      openModal('descontoModal');
  });

  // Botão para adicionar desconto a partir da visualização do produto
  document.addEventListener('click', function(e) {
      if (e.target && e.target.id === 'addDescontoBtn') {
          const produtoId = e.target.getAttribute('data-produto-id');
          document.getElementById('descontoForm').reset();
          document.getElementById('descontoId').value = '';
          document.getElementById('descontoProdutoId').value = produtoId;
          document.getElementById('descontoProdutoNome').textContent = document.getElementById('visualizarProdutoNome').textContent;
          document.getElementById('descontoAtivo').value = 'true';
          document.getElementById('descontoModalTitle').textContent = 'Cadastrar Desconto';
          openModal('descontoModal');
      }
  });

  document.addEventListener('DOMContentLoaded', function () {
      const tabDescontos = document.querySelector('li[data-tab="descontos"] a');

      if (tabDescontos) {
          tabDescontos.addEventListener('click', function (event) {
              // Se necessário, previna o comportamento padrão
              // event.preventDefault();

              // Carrega os dados de descontos
              loadDescontosData();
          });
      }
  });

  // ===== FUNÇÕES GERAIS =====
  // Funções auxiliares para formatar texto
  function formatPerfil(perfil) {
    const perfis = {
      'admin': 'Administrador',
      'operador': 'Operador',
    };
    return perfis[perfil.toLowerCase()] || perfil;
  }

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
          } else if (type === 'desconto') {
              url = `/admin/descontos/${id}`;
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
              if (type === 'desconto') loadDescontosData();
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
  document.getElementById('searchDesconto').addEventListener('input', loadDescontosData);

  // Botões de atualização
  document.getElementById('refreshData').addEventListener('click', loadDashboardData);
  document.getElementById('refreshClientes').addEventListener('click', loadClientesData);
  document.getElementById('refreshProdutos').addEventListener('click', loadProdutosData);
  document.getElementById('refreshUsuarios').addEventListener('click', loadUsuariosData);
  document.getElementById('refreshDescontos').addEventListener('click', loadDescontosData);
  document.getElementById('filterFinanceiro').addEventListener('click', loadFinanceiroData);

  // Botão para adicionar novo usuário
  document.getElementById('addUsuario').addEventListener('click', () => openEditarUsuarioModal());

  // Botão para adicionar novo cliente
  document.getElementById('addCliente').addEventListener('click', () => {
    document.getElementById('clienteForm').reset();
    document.getElementById('clienteId').value = '';
    document.getElementById('clienteStatus').value = 'true';
    document.getElementById('clienteModalTitle').textContent = 'Cadastrar Cliente';
    document.getElementById('clienteModalSubmitText').textContent = 'Cadastrar';
    openModal('clienteModal');
  });

  // Botão para adicionar novo produto
  document.getElementById('addProduto').addEventListener('click', () => {
    document.getElementById('produtoForm').reset();
    document.getElementById('produtoEstoqueTipo').value = 'loja';
    document.getElementById('produtoUnidade').value = 'kg';
    openModal('produtoModal');
  });

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
        checkCaixaStatus()
      ]);
      
      // Carrega a aba ativa
      const activeTab = document.querySelector('.sidebar-nav li.active');
      if (activeTab) {
        const tabId = activeTab.getAttribute('data-tab');
        if (tabId === 'clientes') loadClientesData();
        if (tabId === 'produtos') loadProdutosData();
        if (tabId === 'financeiro') loadFinanceiroData();
        if (tabId === 'usuarios') loadUsuariosData();
        if (tabId === 'estoque') loadMovimentacoesData();
        if (tabId === 'descontos') loadDescontosData();
      }
    } catch (error) {
      console.error('Erro ao carregar dados iniciais:', error);
    }
  }

  // Inicializar
  loadInitialData();
});