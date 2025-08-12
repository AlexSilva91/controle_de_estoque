document.addEventListener('DOMContentLoaded', function() {
  // ===== VARIÁVEIS GLOBAIS =====
  let produtosVendaRetroativa = [];
  let clientesVendaRetroativa = [];
  let caixasFechados = [];
  let itensVendaRetroativa = [];
  let pagamentosVendaRetroativa = [];
  let vendasDespesasChart, formasPagamentoChart, caixasChart, vendasDiariasChart;
  let caixaIdAtual = null;

  // ===== CONFIGURAÇÃO DOS GRÁFICOS =====
  Chart.defaults.color = '#e0e0e0';
  Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

  const chartColors = {
    green: 'rgba(102, 187, 106, 0.7)',
    greenBorder: 'rgba(102, 187, 106, 1)',
    red: 'rgba(239, 83, 80, 0.7)',
    redBorder: 'rgba(239, 83, 80, 1)',
    blue: 'rgba(66, 165, 245, 0.7)',
    blueBorder: 'rgba(66, 165, 245, 1)',
    yellow: 'rgba(255, 213, 79, 0.7)',
    yellowBorder: 'rgba(255, 213, 79, 1)',
    purple: 'rgba(171, 71, 188, 0.7)',
    purpleBorder: 'rgba(171, 71, 188, 1)',
    orange: 'rgba(255, 167, 38, 0.7)',
    orangeBorder: 'rgba(255, 167, 38, 1)',
    teal: 'rgba(38, 166, 154, 0.7)',
    tealBorder: 'rgba(38, 166, 154, 1)'
  };

  function formatMoney(value) {
    if (typeof value === 'string') {
      value = value.replace(/[^\d,]/g, '').replace(',', '.');
    }
    return 'R$ ' + parseFloat(value).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  // ===== FUNÇÕES UTILITÁRIAS =====
  function updateDateTime() {
    const now = new Date();
    const updateTimeElement = document.getElementById('updateTime');
    if (updateTimeElement) {
      updateTimeElement.textContent = now.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  }

  function showFlashMessage(type, message) {
    const flashContainer = document.querySelector('.flash-messages');
    if (!flashContainer) return;
    
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
    
    const closeBtn = flashMessage.querySelector('.close-flash');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        flashMessage.remove();
      });
    }
    
    setTimeout(() => {
      flashMessage.classList.add('fade-out');
      setTimeout(() => flashMessage.remove(), 500);
    }, 5000);
  }

  async function fetchWithErrorHandling(url, options = {}) {
    try {
      const response = await fetch(url, options);
      const contentType = response.headers.get('content-type');
      
      if (!response.ok) {
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json();
          
          if (Array.isArray(data.message)) {
            data.message.forEach(msg => {
              showFlashMessage('error', msg);
            });
          } else if (data.message && typeof data.message === 'object') {
            for (const [key, value] of Object.entries(data.message)) {
              if (Array.isArray(value)) {
                value.forEach(msg => showFlashMessage('error', msg));
              } else {
                showFlashMessage('error', value);
              }
            }
          } else if (data.message) {
            showFlashMessage('error', data.message);
          } else {
            showFlashMessage('error', `HTTP error! status: ${response.status}`);
          }
          
          throw new Error(data.message || `HTTP error! status: ${response.status}`);
        } else {
          const text = await response.text();
          showFlashMessage('error', text || `HTTP error! status: ${response.status}`);
          throw new Error(text || `HTTP error! status: ${response.status}`);
        }
      }
      
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        return text;
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Erro na requisição:', error);
      
      if (error.message && error.message.includes('HTTP error')) {
        throw error;
      }
      
      showFlashMessage('error', error.message || 'Erro ao comunicar com o servidor');
      throw error;
    }
  }
  
  function formatPerfil(perfil) {
    const perfis = {
      'admin': 'Administrador',
      'operador': 'Operador'
    };
    return perfis[perfil.toLowerCase()] || perfil;
  }

  function formatarMoeda(valor) {
    return parseFloat(valor || 0).toLocaleString('pt-BR', { 
      style: 'currency', 
      currency: 'BRL' 
    });
  }

  function formatarDataParaInput(date) {
    const pad = num => num.toString().padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
  }

  function formatDateTime(dateTimeString) {
    if (!dateTimeString) return '-';
    const date = new Date(dateTimeString);
    return date.toLocaleString('pt-BR');
  }

  function limparValor(valor) {
    if (!valor) return 0;
    return parseFloat(valor.replace('R$', '').replace(',', '.').trim());
  }

  function formatCurrency(value) {
    if (!value) return '-';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  }

  // ===== FUNÇÕES DE MODAL =====
  function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    }
  }

  function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.style.display = 'none';
      document.body.style.overflow = 'auto';
    }
  }

  function setupModalEvents() {
    document.querySelectorAll('.close-modal').forEach(btn => {
      btn.addEventListener('click', function() {
        const modal = this.closest('.modal');
        if (modal) {
          closeModal(modal.id);
        }
      });
    });

    window.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-overlay')) {
        const modal = e.target.closest('.modal');
        if (modal) {
          closeModal(modal.id);
        }
      }
    });

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
  }

  // ===== NAVEGAÇÃO =====
  function setupNavigation() {
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.querySelector('.sidebar');

    if (mobileMenuToggle && sidebar) {
      mobileMenuToggle.addEventListener('click', function () {
        this.classList.toggle('active');
        sidebar.classList.toggle('active');
      });
    }

    document.querySelectorAll('.sidebar-nav li').forEach(item => {
      item.addEventListener('click', function() {
        if (window.innerWidth <= 768 && mobileMenuToggle && sidebar) {
          mobileMenuToggle.classList.remove('active');
          sidebar.classList.remove('active');
        }
      });
    });

    const navItems = document.querySelectorAll('.sidebar-nav li');
    const tabContents = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('page-title');
    const breadcrumb = document.querySelector('.breadcrumb');

    navItems.forEach(item => {
      item.addEventListener('click', function() {
        if (mobileMenuToggle && sidebar && sidebar.classList.contains('active')) {
          mobileMenuToggle.classList.remove('active');
          sidebar.classList.remove('active');
        }

        navItems.forEach(nav => nav.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));

        this.classList.add('active');
        const tabId = this.getAttribute('data-tab');
        const tabContent = document.getElementById(tabId);

        if (tabContent) {
          tabContent.classList.add('active');
        }

        const tabName = this.querySelector('span')?.textContent || '';
        if (pageTitle) pageTitle.textContent = tabName;
        if (breadcrumb) breadcrumb.textContent = `Home / ${tabName}`;

        if (tabId === 'dashboard') loadDashboardData();
        if (tabId === 'clientes') loadClientesData();
        if (tabId === 'produtos') loadProdutosData();
        if (tabId === 'financeiro') loadFinanceiroData();
        if (tabId === 'usuarios') loadUsuariosData();
        if (tabId === 'estoque') loadMovimentacoesData();
        if (tabId === 'descontos') loadDescontosData();
        if (tabId === 'caixas') loadCaixasData();
      });
    });

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        if (confirm('Tem certeza que deseja sair do sistema?')) {
          window.location.href = '/logout';
        }
      });
    }
  }

  // ===== DASHBOARD =====
  function toggleMovimentacoes() {
    const body = document.getElementById('movimentacoesBody');
    const icon = document.querySelector('#movimentacoesHeader .toggle-icon i');
    
    if (!body || !icon) return;
    
    if (body.style.display === 'none') {
      body.style.display = 'block';
      icon.classList.remove('fa-chevron-down');
      icon.classList.add('fa-chevron-up');
    } else {
      body.style.display = 'none';
      icon.classList.remove('fa-chevron-up');
      icon.classList.add('fa-chevron-down');
    }
  }

  function toggleDetailsTable(header) {
    const container = header.nextElementSibling;
    const icon = header.querySelector('.toggle-icon');

    if (!container || !icon) return;

    if (container.style.display === 'none' || container.style.display === '') {
      container.style.display = 'block';
      icon.classList.remove('fa-chevron-down');
      icon.classList.add('fa-chevron-up');
    } else {
      container.style.display = 'none';
      icon.classList.remove('fa-chevron-up');
      icon.classList.add('fa-chevron-down');
    }
  }

  async function updateCharts() {
    try {
      if (vendasDespesasChart) vendasDespesasChart.destroy();
      if (formasPagamentoChart) formasPagamentoChart.destroy();
      if (caixasChart) caixasChart.destroy();
      if (vendasDiariasChart) vendasDiariasChart.destroy();

      const vendasMensaisData = await fetchWithErrorHandling('/admin/dashboard/vendas-mensais');
      if (vendasMensaisData.success) {
        const vendasDespesasCtx = document.getElementById('vendasDespesasChart').getContext('2d');
        vendasDespesasChart = new Chart(vendasDespesasCtx, {
          type: 'bar',
          data: {
            labels: vendasMensaisData.meses,
            datasets: [
              {
                label: 'Vendas',
                data: vendasMensaisData.vendas,
                backgroundColor: chartColors.green,
                borderColor: chartColors.greenBorder,
                borderWidth: 2
              },
              {
                label: 'Despesas',
                data: vendasMensaisData.despesas,
                backgroundColor: chartColors.red,
                borderColor: chartColors.redBorder,
                borderWidth: 2
              }
            ]
          },
          options: {
            responsive: true,
            plugins: {
              legend: {
                position: 'top',
                labels: {
                  color: '#e0e0e0'
                }
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    return `${context.dataset.label}: ${formatMoney(context.raw)}`;
                  }
                }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                grid: {
                  color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                  callback: function(value) {
                    return formatMoney(value);
                  }
                }
              },
              x: {
                grid: {
                  color: 'rgba(255, 255, 255, 0.1)'
                }
              }
            }
          }
        });
      }

      const vendasDiariasData = await fetchWithErrorHandling('/admin/dashboard/vendas-diarias');
      if (vendasDiariasData.success) {
        const formasPagamentoMap = new Map();
        
        vendasDiariasData.dados.forEach(dia => {
          dia.formas_pagamento.forEach(fp => {
            const forma = fp.forma.replace('pix_', '').replace(/_/g, ' ').replace('cartao', 'cartão');
            const total = parseFloat(fp.total.replace(/[^\d,]/g, '').replace(',', '.'));
            
            if (formasPagamentoMap.has(forma)) {
              formasPagamentoMap.set(forma, formasPagamentoMap.get(forma) + total);
            } else {
              formasPagamentoMap.set(forma, total);
            }
          });
        });

        const formasPagamentoCtx = document.getElementById('formasPagamentoChart').getContext('2d');
        formasPagamentoChart = new Chart(formasPagamentoCtx, {
          type: 'doughnut',
          data: {
            labels: Array.from(formasPagamentoMap.keys()),
            datasets: [{
              data: Array.from(formasPagamentoMap.values()),
              backgroundColor: [
                chartColors.green,
                chartColors.blue,
                chartColors.yellow,
                chartColors.purple,
                chartColors.orange,
                chartColors.teal,
                chartColors.red
              ],
              borderColor: [
                chartColors.greenBorder,
                chartColors.blueBorder,
                chartColors.yellowBorder,
                chartColors.purpleBorder,
                chartColors.orangeBorder,
                chartColors.tealBorder,
                chartColors.redBorder
              ],
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            cutout: '70%',
            plugins: {
              legend: {
                position: 'right',
                labels: {
                  color: '#e0e0e0',
                  font: {
                    size: 12
                  }
                }
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    const label = context.label || '';
                    const value = context.raw || 0;
                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                    const percentage = Math.round((value / total) * 100);
                    return `${label}: ${formatMoney(value)} (${percentage}%)`;
                  }
                }
              }
            }
          }
        });
      }

      if (vendasDiariasData?.success) {
        const caixasCtx = document.getElementById('caixasChart').getContext('2d');
        caixasChart = new Chart(caixasCtx, {
          type: 'bar',
          data: {
            labels: vendasDiariasData.vendas_mensais_caixa.map(c => 'Caixa ' + c.caixa_id),
            datasets: [{
              label: 'Valor Total',
              data: vendasDiariasData.vendas_mensais_caixa.map(c => 
                parseFloat(c.total_vendas.replace(/[^\d,]/g, '').replace(',', '.'))
              ),
              backgroundColor: chartColors.blue,
              borderColor: chartColors.blueBorder,
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: {
                display: false,
                labels: {
                  color: '#e0e0e0'
                }
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    return formatMoney(context.raw);
                  }
                }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                grid: {
                  color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                  callback: function(value) {
                    return formatMoney(value);
                  }
                }
              },
              x: {
                grid: {
                  color: 'rgba(255, 255, 255, 0.1)'
                }
              }
            }
          }
        });
      }

      if (vendasDiariasData?.success) {
        const vendasDiariasCtx = document.getElementById('vendasDiariasChart').getContext('2d');
        
        const labels = vendasDiariasData.dados.map(item => item.data);
        const vendas = vendasDiariasData.dados.map(item => 
          parseFloat(item.total_vendas.replace(/[^\d,]/g, '').replace(',', '.'))
        );
        const despesas = vendasDiariasData.dados.map(item => 
          parseFloat(item.total_despesas.replace(/[^\d,]/g, '').replace(',', '.'))
        );
        
        vendasDiariasChart = new Chart(vendasDiariasCtx, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [
              {
                label: 'Vendas (R$)',
                data: vendas,
                backgroundColor: chartColors.green,
                borderColor: chartColors.greenBorder,
                borderWidth: 3,
                tension: 0.4,
                fill: false,
                pointBackgroundColor: '#fff',
                pointBorderColor: chartColors.greenBorder,
                pointRadius: 5,
                pointHoverRadius: 7
              },
              {
                label: 'Despesas (R$)',
                data: despesas,
                backgroundColor: chartColors.red,
                borderColor: chartColors.redBorder,
                borderWidth: 3,
                tension: 0.4,
                fill: false,
                pointBackgroundColor: '#fff',
                pointBorderColor: chartColors.redBorder,
                pointRadius: 5,
                pointHoverRadius: 7
              }
            ]
          },
          options: {
            responsive: true,
            plugins: {
              legend: {
                position: 'top',
                labels: {
                  color: '#e0e0e0'
                }
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    return `${context.dataset.label}: ${formatMoney(context.raw)}`;
                  }
                }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                grid: {
                  color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                  callback: function(value) {
                    return formatMoney(value);
                  }
                }
              },
              x: {
                grid: {
                  color: 'rgba(255, 255, 255, 0.1)'
                }
              }
            }
          }
        });
      }
    } catch (error) {
      console.error('Erro ao atualizar gráficos:', error);
      showFlashMessage('error', 'Erro ao atualizar gráficos');
    }
  }

  async function loadMovimentacoes() {
    try {
      const movData = await fetchWithErrorHandling('/admin/dashboard/movimentacoes');
      if (movData.success) {
        const movTable = document.querySelector('#movimentacoesTable tbody');
        if (movTable) {
          movTable.innerHTML = movData.movimentacoes.map(mov => `
            <tr>
              <td>${mov.data}</td>
              <td><span class="badge ${mov.tipo === 'Entrada' ? 'badge-success' : 'badge-danger'}">${mov.tipo}</span></td>
              <td>${mov.produto}</td>
              <td>${mov.quantidade}</td>
              <td>${mov.valor}</td>
            </tr>
          `).join('');
        }
      }
    } catch (error) {
      console.error('Erro ao carregar movimentações:', error);
      showFlashMessage('error', 'Erro ao carregar movimentações');
    }
  }

  async function updateMetrics() {
    try {
      const metricsData = await fetchWithErrorHandling('/admin/dashboard/metrics');
      
      if (metricsData.success) {
        const metricsContainer = document.querySelector('.metrics-grid');
        if (metricsContainer) {
          metricsContainer.innerHTML = `
            <div class="metric-card">
              <div class="metric-icon">
                <i class="fas fa-weight"></i>
              </div>
              <div class="metric-info">
                <h3>Estoque (Kg)</h3>
                <div class="value">${metricsData.metrics.estoque.kg}</div>
              </div>
            </div>
            <div class="metric-card">
              <div class="metric-icon">
                <i class="fa-solid fa-boxes-packing"></i>
              </div>
              <div class="metric-info">
                <h3>Estoque (Sacos)</h3>
                <div class="value">${metricsData.metrics.estoque.sacos}</div>
              </div>
            </div>
            <div class="metric-card">
              <div class="metric-icon">
                <i class="fas fa-boxes"></i>
              </div>
              <div class="metric-info">
                <h3>Estoque (Unidades)</h3>
                <div class="value">${metricsData.metrics.estoque.unidades}</div>
              </div>
            </div>
            <div class="metric-card">
              <div class="metric-icon">
                <i class="fas fa-money-bill-wave"></i>
              </div>
              <div class="metric-info">
                <h3>Entradas (Mês)</h3>
                <div class="value">${metricsData.metrics.financeiro.entradas_mes}</div>
              </div>
            </div>
            <div class="metric-card">
              <div class="metric-icon">
                <i class="fas fa-receipt"></i>
              </div>
              <div class="metric-info">
                <h3>Despesas (Mês)</h3>
                <div class="value">${metricsData.metrics.financeiro.saidas_mes}</div>
              </div>
            </div>
            <div class="metric-card">
              <div class="metric-icon">
                <i class="fas fa-piggy-bank"></i>
              </div>
              <div class="metric-info">
                <h3>Saldo (Mês)</h3>
                <div class="value">${metricsData.metrics.financeiro.saldo_mes}</div>
              </div>
            </div>
          `;
        }
      }
    } catch (error) {
      console.error('Erro ao atualizar métricas:', error);
      showFlashMessage('error', 'Erro ao atualizar métricas');
    }
  }

  async function loadDashboardData() {
    try {
      const loadingElement = document.getElementById('loadingIndicator');
      if (loadingElement) loadingElement.style.display = 'block';
      
      await updateMetrics();
      await updateCharts();
      await loadMovimentacoes();
      
      if (loadingElement) loadingElement.style.display = 'none';
    } catch (error) {
      console.error('Erro ao carregar dados do dashboard:', error);
      showFlashMessage('error', 'Erro ao carregar dados do dashboard');
      
      const loadingElement = document.getElementById('loadingIndicator');
      if (loadingElement) loadingElement.style.display = 'none';
    }
  }

  // Event Listeners para Dashboard
  const movimentacoesHeader = document.getElementById('movimentacoesHeader');
  if (movimentacoesHeader) {
    movimentacoesHeader.addEventListener('click', function(e) {
      if (!e.target.closest('.btn-icon')) {
        toggleMovimentacoes();
      }
    });
  }

  const toggleHeaders = document.querySelectorAll('.details-table-section .toggle-table-header');
  toggleHeaders.forEach(header => {
    header.addEventListener('click', (e) => {
      if (!e.target.closest('button')) {
        toggleDetailsTable(header);
      }
    });
  });

  // ===== CLIENTES =====
  async function loadClientesData() {
    try {
      const searchText = document.getElementById('searchCliente')?.value.toLowerCase() || '';
      const data = await fetchWithErrorHandling('/admin/clientes');

      if (data.success) {
        const clientesTable = document.querySelector('#clientesTable tbody');
        if (clientesTable) {
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
      }
    } catch (error) {
      console.error('Erro ao carregar clientes:', error);
      showFlashMessage('error', 'Erro ao carregar lista de clientes');
    }
  }

  async function openEditarClienteModal(clienteId) {
    const clienteForm = document.getElementById('clienteForm');
    if (clienteForm) clienteForm.reset();
    
    const clienteIdField = document.getElementById('clienteId');
    if (clienteIdField) clienteIdField.value = '';
    
    const clienteStatus = document.getElementById('clienteStatus');
    if (clienteStatus) clienteStatus.value = 'true';

    const clienteModalTitle = document.getElementById('clienteModalTitle');
    if (clienteModalTitle) clienteModalTitle.textContent = 'Editar Cliente';
    
    const clienteModalSubmitText = document.getElementById('clienteModalSubmitText');
    if (clienteModalSubmitText) clienteModalSubmitText.textContent = 'Atualizar';

    try {
      const response = await fetchWithErrorHandling(`/admin/clientes/${clienteId}`);
      if (response.success) {
        const cliente = response.cliente;
        
        if (document.getElementById('clienteId')) document.getElementById('clienteId').value = cliente.id;
        if (document.getElementById('clienteNome')) document.getElementById('clienteNome').value = cliente.nome;
        if (document.getElementById('clienteDocumento')) document.getElementById('clienteDocumento').value = cliente.documento || '';
        if (document.getElementById('clienteTelefone')) document.getElementById('clienteTelefone').value = cliente.telefone || '';
        if (document.getElementById('clienteEmail')) document.getElementById('clienteEmail').value = cliente.email || '';
        if (document.getElementById('clienteEndereco')) document.getElementById('clienteEndereco').value = cliente.endereco || '';
        if (document.getElementById('clienteStatus')) document.getElementById('clienteStatus').value = cliente.ativo ? 'true' : 'false';
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
        const confirmarExclusaoTexto = document.getElementById('confirmarExclusaoTexto');
        const confirmarExclusaoBtn = document.getElementById('confirmarExclusaoBtn');
        
        if (confirmarExclusaoTexto) confirmarExclusaoTexto.textContent = `Tem certeza que deseja excluir o cliente ${clienteId}?`;
        if (confirmarExclusaoBtn) {
          confirmarExclusaoBtn.setAttribute('data-id', clienteId);
          confirmarExclusaoBtn.setAttribute('data-type', 'cliente');
        }
        openModal('confirmarExclusaoModal');
      });
    });
  }

  // Event Listeners para Clientes
  document.getElementById('searchCliente')?.addEventListener('input', loadClientesData);
  document.getElementById('refreshClientes')?.addEventListener('click', loadClientesData);
  document.getElementById('addCliente')?.addEventListener('click', () => {
    const clienteForm = document.getElementById('clienteForm');
    if (clienteForm) clienteForm.reset();
    
    if (document.getElementById('clienteId')) document.getElementById('clienteId').value = '';
    if (document.getElementById('clienteStatus')) document.getElementById('clienteStatus').value = 'true';
    
    const clienteModalTitle = document.getElementById('clienteModalTitle');
    if (clienteModalTitle) clienteModalTitle.textContent = 'Cadastrar Cliente';
    
    const clienteModalSubmitText = document.getElementById('clienteModalSubmitText');
    if (clienteModalSubmitText) clienteModalSubmitText.textContent = 'Cadastrar';
    openModal('clienteModal');
  });

  const clienteForm = document.getElementById('clienteForm');
  if (clienteForm) {
    clienteForm.addEventListener('submit', async function(e) {
      e.preventDefault();

      const clienteId = document.getElementById('clienteId')?.value || '';
      const isEdit = clienteId !== '';

      const formData = {
        nome: document.getElementById('clienteNome')?.value || '',
        documento: document.getElementById('clienteDocumento')?.value || '',
        telefone: document.getElementById('clienteTelefone')?.value || '',
        email: document.getElementById('clienteEmail')?.value || '',
        endereco: document.getElementById('clienteEndereco')?.value || '',
        ativo: document.getElementById('clienteStatus')?.value === 'true'
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
  }

  // ===== PRODUTOS =====
  async function loadProdutosData() {
    try {
      const searchText = document.getElementById('searchProduto')?.value.toLowerCase() || '';
      const data = await fetchWithErrorHandling('/admin/produtos');
      
      if (data.success) {
        const produtosTable = document.querySelector('#produtosTable tbody');
        if (produtosTable) {
          produtosTable.innerHTML = '';
          
          data.produtos.forEach(produto => {
            if (searchText && !produto.nome.toLowerCase().includes(searchText)) return;
            
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
        await openEditarProdutoModal(produtoId);
      });
    });

    document.querySelectorAll('.remover-produto').forEach(btn => {
      btn.addEventListener('click', function() {
        const produtoId = this.getAttribute('data-id');
        const confirmarExclusaoTexto = document.getElementById('confirmarExclusaoTexto');
        const confirmarExclusaoBtn = document.getElementById('confirmarExclusaoBtn');
        
        if (confirmarExclusaoTexto) confirmarExclusaoTexto.textContent = `Tem certeza que deseja excluir o produto ${produtoId}?`;
        if (confirmarExclusaoBtn) {
          confirmarExclusaoBtn.setAttribute('data-id', produtoId);
          confirmarExclusaoBtn.setAttribute('data-type', 'produto');
        }
        openModal('confirmarExclusaoModal');
      });
    });

    document.querySelectorAll('.movimentar-estoque').forEach(btn => {
      btn.addEventListener('click', function() {
        const produtoId = this.getAttribute('data-id');
        openTransferenciaModal(produtoId);
      });
    });
  }

  async function openEditarProdutoModal(produtoId) {
    try {
      const produtoResponse = await fetchWithErrorHandling(`/admin/produtos/${produtoId}`);
      
      if (produtoResponse.success) {
        const produto = produtoResponse.produto;
        
        const descontosResponse = await fetchWithErrorHandling('/admin/descontos');
        
        if (descontosResponse.success) {
          const formBody = document.querySelector('#editarProdutoModal .modal-body');
          
          if (!formBody) return;
          
          let valorUnitario = produto.valor_unitario;
          if (typeof valorUnitario === 'string') {
            valorUnitario = valorUnitario.replace(/[^\d,.-]/g, '').replace(',', '.');
          }
          
          const descontosAtuais = produto.descontos || [];
          const descontosAtuaisIds = descontosAtuais.map(d => d.id);
          
          const todosDescontos = descontosResponse.descontos || [];
          
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

            <div class="form-row">
              <div class="form-group" style="width: 100%;">
                <label>Descontos Aplicados</label>
                <div id="descontosContainer" class="descontos-container">
                  ${descontosAtuais.map(desconto => `
                    <div class="desconto-item" data-id="${desconto.id}">
                      <span>${desconto.identificador} - 
                      ${desconto.tipo === 'fixo' ? `R$ ${desconto.valor}` : `${desconto.valor}%`} - 
                      Mín: ${desconto.quantidade_minima}${desconto.quantidade_maxima ? `, Máx: ${desconto.quantidade_maxima}` : ''}</span>
                      <button type="button" class="btn-icon btn-danger btn-remover-desconto">
                        <i class="fas fa-times"></i>
                      </button>
                    </div>
                  `).join('')}
                </div>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group" style="width: 100%;">
                <label for="selecionarDesconto">Adicionar Desconto</label>
                <div class="desconto-select-container">
                  <select id="selecionarDesconto" class="form-control">
                    <option value="">Selecione um desconto...</option>
                    ${todosDescontos
                      .filter(d => !descontosAtuaisIds.includes(d.id))
                      .map(desconto => `
                        <option value="${desconto.id}" 
                          data-quantidade-minima="${desconto.quantidade_minima}"
                          data-quantidade-maxima="${desconto.quantidade_maxima || ''}"
                          data-valor="${desconto.valor}"
                          data-tipo="${desconto.tipo}"
                          data-identificador="${desconto.identificador}">
                          ${desconto.identificador} - 
                          ${desconto.tipo === 'fixo' ? `R$ ${desconto.valor}` : `${desconto.valor}%`} - 
                          Mín: ${desconto.quantidade_minima}${desconto.quantidade_maxima ? `, Máx: ${desconto.quantidade_maxima}` : ''}
                        </option>
                      `).join('')}
                  </select>
                  <button type="button" id="btnAdicionarDesconto" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Adicionar
                  </button>
                </div>
              </div>
            </div>
          `;
          
          const editarProdutoForm = document.getElementById('editarProdutoForm');
          if (editarProdutoForm) {
            editarProdutoForm.setAttribute('data-produto-id', produtoId);
          }
          setupDescontoEvents();
          openModal('editarProdutoModal');
        } else {
          throw new Error('Erro ao carregar descontos');
        }
      } else {
        throw new Error('Erro ao carregar dados do produto');
      }
    } catch (error) {
      console.error('Erro ao carregar dados do produto:', error);
      showFlashMessage('error', 'Erro ao carregar dados do produto');
    }
  }

  function setupDescontoEvents() {
    const btnAdicionarDesconto = document.getElementById('btnAdicionarDesconto');
    if (btnAdicionarDesconto) {
      btnAdicionarDesconto.addEventListener('click', function() {
        const select = document.getElementById('selecionarDesconto');
        if (!select) return;
        
        const selectedOption = select.options[select.selectedIndex];
        
        if (!selectedOption.value) {
          showFlashMessage('warning', 'Selecione um desconto para adicionar');
          return;
        }
        
        const descontoId = selectedOption.value;
        const container = document.getElementById('descontosContainer');
        if (!container) return;
        
        if (document.querySelector(`.desconto-item[data-id="${descontoId}"]`)) {
          showFlashMessage('warning', 'Este desconto já foi adicionado');
          return;
        }
        
        const item = document.createElement('div');
        item.className = 'desconto-item';
        item.dataset.id = descontoId;
        item.innerHTML = `
          <span>${selectedOption.dataset.identificador} - 
          ${selectedOption.dataset.tipo === 'fixo' ? `R$ ${selectedOption.dataset.valor}` : `${selectedOption.dataset.valor}%`} - 
          Mín: ${selectedOption.dataset.quantidadeMinima}${selectedOption.dataset.quantidadeMaxima ? `, Máx: ${selectedOption.dataset.quantidadeMaxima}` : ''}</span>
          <button type="button" class="btn-icon btn-danger btn-remover-desconto">
            <i class="fas fa-times"></i>
          </button>
        `;
        
        container.appendChild(item);
        
        select.value = '';
        
        const removeBtn = item.querySelector('.btn-remover-desconto');
        if (removeBtn) {
          removeBtn.addEventListener('click', function() {
            item.remove();
          });
        }
      });
    }
    
    document.querySelectorAll('.btn-remover-desconto').forEach(btn => {
      btn.addEventListener('click', function() {
        const item = this.closest('.desconto-item');
        if (item) {
          item.remove();
        }
      });
    });
  }

  async function openTransferenciaModal(produtoId) {
    try {
      const response = await fetchWithErrorHandling(`/admin/produtos/${produtoId}`);
      if (response.success) {
        const produto = response.produto;
        
        const transferenciaProdutoId = document.getElementById('transferenciaProdutoId');
        if (transferenciaProdutoId) transferenciaProdutoId.value = produtoId;
        
        const transferenciaProdutoNome = document.getElementById('transferenciaProdutoNome');
        if (transferenciaProdutoNome) transferenciaProdutoNome.textContent = produto.nome;
        
        const transferenciaUnidadeAtual = document.getElementById('transferenciaUnidadeAtual');
        if (transferenciaUnidadeAtual) transferenciaUnidadeAtual.textContent = produto.unidade;
        
        const transferenciaOrigem = document.getElementById('transferenciaOrigem');
        if (transferenciaOrigem) transferenciaOrigem.value = 'loja';
        
        const transferenciaDestino = document.getElementById('transferenciaDestino');
        if (transferenciaDestino) transferenciaDestino.value = 'deposito';
        
        const transferenciaQuantidade = document.getElementById('transferenciaQuantidade');
        if (transferenciaQuantidade) transferenciaQuantidade.value = '';
        
        const transferenciaValorUnitarioDestino = document.getElementById('transferenciaValorUnitarioDestino');
        if (transferenciaValorUnitarioDestino) transferenciaValorUnitarioDestino.value = produto.valor_unitario;
        
        const transferenciaObservacao = document.getElementById('transferenciaObservacao');
        if (transferenciaObservacao) transferenciaObservacao.value = '';
        
        openModal('transferenciaModal');
        updateEstoqueDisponivel();
      }
    } catch (error) {
      console.error('Erro ao abrir modal de transferência:', error);
      showFlashMessage('error', 'Erro ao carregar dados do produto');
    }
  }

  function updateEstoqueDisponivel() {
    const produtoId = document.getElementById('transferenciaProdutoId')?.value;
    const origem = document.getElementById('transferenciaOrigem')?.value;
    
    if (!produtoId || !origem) return;
    
    fetchWithErrorHandling(`/admin/produtos/${produtoId}`)
      .then(response => {
        if (response.success) {
          const produto = response.produto;
          let estoque = 0;
          
          if (origem === 'loja') estoque = produto.estoque_loja;
          else if (origem === 'deposito') estoque = produto.estoque_deposito;
          else if (origem === 'fabrica') estoque = produto.estoque_fabrica;
          
          const transferenciaEstoqueDisponivel = document.getElementById('transferenciaEstoqueDisponivel');
          if (transferenciaEstoqueDisponivel) {
            transferenciaEstoqueDisponivel.textContent = 
              `Disponível: ${estoque} ${produto.unidade}`;
          }
          
          const transferenciaQuantidade = document.getElementById('transferenciaQuantidade');
          if (transferenciaQuantidade) {
            transferenciaQuantidade.max = estoque;
          }
        }
      })
      .catch(error => {
        console.error('Erro ao buscar estoque:', error);
      });
  }

  // Event Listeners para Produtos
  document.getElementById('searchProduto')?.addEventListener('input', loadProdutosData);
  document.getElementById('refreshProdutos')?.addEventListener('click', loadProdutosData);
  document.getElementById('addProduto')?.addEventListener('click', () => {
    const produtoForm = document.getElementById('produtoForm');
    if (produtoForm) produtoForm.reset();
    
    if (document.getElementById('produtoEstoqueTipo')) document.getElementById('produtoEstoqueTipo').value = 'loja';
    if (document.getElementById('produtoUnidade')) document.getElementById('produtoUnidade').value = 'kg';
    openModal('produtoModal');
  });

  const produtoForm = document.getElementById('produtoForm');
  if (produtoForm) {
    produtoForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const estoqueTipo = document.getElementById('produtoEstoqueTipo')?.value || 'loja';
      const estoqueQuantidade = parseFloat(document.getElementById('produtoEstoque')?.value) || 0;
      
      const formData = {
        codigo: document.getElementById('produtoCodigo')?.value || '',
        nome: document.getElementById('produtoNome')?.value || '',
        tipo: document.getElementById('produtoTipo')?.value || '',
        marca: document.getElementById('produtoMarca')?.value || '',
        unidade: document.getElementById('produtoUnidade')?.value || 'kg',
        valor_unitario: parseFloat(document.getElementById('produtoValor')?.value) || 0,
        estoque_loja: estoqueTipo === 'loja' ? estoqueQuantidade : 0,
        estoque_deposito: estoqueTipo === 'deposito' ? estoqueQuantidade : 0,
        estoque_fabrica: estoqueTipo === 'fabrica' ? estoqueQuantidade : 0
      };

      const valorCompra = parseFloat(document.getElementById('produtoValorCompra')?.value);
      const valorTotal = parseFloat(document.getElementById('produtoValorTotalCompra')?.value);
      const icms = parseFloat(document.getElementById('produtoICMS')?.value);
      const estoqueMinimo = parseFloat(document.getElementById('produtoEstoqueMinimo')?.value);

      if (!isNaN(valorCompra)) formData.valor_unitario_compra = valorCompra;
      if (!isNaN(valorTotal)) formData.valor_total_compra = valorTotal;
      if (!isNaN(icms)) formData.imcs = icms;
      if (!isNaN(estoqueMinimo)) formData.estoque_minimo = estoqueMinimo;
      
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
  }

  const editarProdutoForm = document.getElementById('editarProdutoForm');
  if (editarProdutoForm) {
    editarProdutoForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const produtoId = this.getAttribute('data-produto-id');
      if (!produtoId) return;
      
      const descontos = [];
      document.querySelectorAll('#descontosContainer .desconto-item').forEach(item => {
        descontos.push(item.dataset.id);
      });
      
      const formData = {
        codigo: document.getElementById('editCodigo')?.value || '',
        nome: document.getElementById('editNome')?.value || '',
        tipo: document.getElementById('editTipo')?.value || '',
        marca: document.getElementById('editMarca')?.value || '',
        valor_unitario: parseFloat(document.getElementById('editValor')?.value) || 0,
        valor_unitario_compra: parseFloat(document.getElementById('editValorCompra')?.value) || 0,
        valor_total_compra: parseFloat(document.getElementById('editValorTotalCompra')?.value) || 0,
        imcs: parseFloat(document.getElementById('editICMS')?.value) || 0,
        estoque_loja: parseFloat(document.getElementById('editEstoqueLoja')?.value) || 0,
        estoque_deposito: parseFloat(document.getElementById('editEstoqueDeposito')?.value) || 0,
        estoque_fabrica: parseFloat(document.getElementById('editEstoqueFabrica')?.value) || 0,
        estoque_minimo: parseFloat(document.getElementById('editEstoqueMinimo')?.value) || 0,
        estoque_maximo: parseFloat(document.getElementById('editEstoqueMaximo')?.value) || 0,
        ativo: document.getElementById('editAtivo')?.value === 'true',
        descontos: descontos
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
  }

  const transferenciaForm = document.getElementById('transferenciaForm');
  if (transferenciaForm) {
    transferenciaForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const produtoId = document.getElementById('transferenciaProdutoId')?.value;
      const origem = document.getElementById('transferenciaOrigem')?.value;
      const destino = document.getElementById('transferenciaDestino')?.value;
      const quantidade = parseFloat(document.getElementById('transferenciaQuantidade')?.value || 0);
      const valorUnitarioDestino = parseFloat(document.getElementById('transferenciaValorUnitarioDestino')?.value || 0);
      const observacao = document.getElementById('transferenciaObservacao')?.value || '';
      
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
            converter_unidade: false
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
  }

  document.getElementById('transferenciaOrigem')?.addEventListener('change', updateEstoqueDisponivel);

  // ===== VENDAS RETROATIVAS =====
  function limparFormularioRetroativa() {
    document.getElementById('formVendaRetroativa').reset();
    itensVendaRetroativa = [];
    pagamentosVendaRetroativa = [];
    atualizarTabelaProdutosRetroativa();
    atualizarTabelaPagamentosRetroativa();
    $('#clienteRetroativo').val('').trigger('change');
    $('#produtoRetroativo').val('').trigger('change');
  }

  function atualizarTabelaProdutosRetroativa() {
    const tbody = document.querySelector('#tabelaProdutosRetroativa tbody');
    tbody.innerHTML = '';
    
    itensVendaRetroativa.forEach((item, index) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${index + 1}</td>
        <td>${item.nome}</td>
        <td>${item.quantidade} ${item.unidade}</td>
        <td>${formatarMoeda(item.valor_unitario)}</td>
        <td>${formatarMoeda(item.valor_total)}</td>
        <td>
          <button type="button" class="btn btn-sm btn-danger btn-remover-produto" data-index="${index}">
            <i class="fas fa-trash"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
    
    calcularTotaisRetroativa();
  }

  function atualizarTabelaPagamentosRetroativa() {
    const tbody = document.querySelector('#tabelaPagamentosRetroativa tbody');
    tbody.innerHTML = '';
    
    pagamentosVendaRetroativa.forEach((pagamento, index) => {
      const formaPagamentoTexto = {
        'dinheiro': 'Dinheiro',
        'pix_loja': 'PIX Loja',
        'pix_fabiano': 'PIX Fabiano',
        'pix_maquineta': 'PIX Maquineta',
        'pix_edfrance': 'PIX EDFrance',
        'cartao_credito': 'Cartão Crédito',
        'cartao_debito': 'Cartão Débito',
        'a_prazo': 'A Prazo'
      }[pagamento.forma_pagamento] || pagamento.forma_pagamento;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${index + 1}</td>
        <td>${formaPagamentoTexto}</td>
        <td>${formatarMoeda(pagamento.valor)}</td>
        <td>
          <button type="button" class="btn btn-sm btn-danger btn-remover-pagamento" data-index="${index}">
            <i class="fas fa-trash"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
    
    calcularTotaisRetroativa();
  }

  function calcularTotaisRetroativa() {
    const totalVenda = itensVendaRetroativa.reduce((total, item) => total + item.valor_total, 0);
    document.getElementById('totalVendaRetroativa').textContent = formatarMoeda(totalVenda);

    const totalRecebido = pagamentosVendaRetroativa
      .filter(p => p.forma_pagamento !== 'a_prazo')
      .reduce((total, pg) => total + pg.valor, 0);
    document.getElementById('totalRecebidoRetroativo').textContent = formatarMoeda(totalRecebido);

    const temDinheiro = pagamentosVendaRetroativa.some(p => p.forma_pagamento === 'dinheiro');
    const troco = temDinheiro ? totalRecebido - totalVenda : 0;
    document.getElementById('trocoRetroativo').textContent = formatarMoeda(Math.max(troco, 0));
  }

  async function carregarClientesRetroativa() {
    try {
      const response = await fetchWithErrorHandling('/admin/api/clientes/ativos');
      
      if (response.success) {
        clientesVendaRetroativa = response.clientes;
        const select = document.getElementById('clienteRetroativo');
        
        select.innerHTML = '<option value="">Selecione um cliente</option>';
        
        response.clientes.forEach(cliente => {
          const option = document.createElement('option');
          option.value = cliente.id;
          option.textContent = `${cliente.nome} - ${cliente.documento || 'Sem documento'}`;
          select.appendChild(option);
        });
        
        $(select).select2({
          placeholder: "Selecione um cliente",
          width: '100%'
        });
      }
    } catch (error) {
      console.error('Erro ao carregar clientes:', error);
      showFlashMessage('error', 'Erro ao carregar clientes');
    }
  }

  async function carregarProdutosRetroativa() {
    try {
      const response = await fetchWithErrorHandling('/admin/api/produtos/ativos');
      
      if (response.success) {
        produtosVendaRetroativa = response.produtos;
        const select = document.getElementById('produtoRetroativo');
        
        select.innerHTML = '<option value="">Selecione um produto</option>';
        
        response.produtos.forEach(produto => {
          const option = document.createElement('option');
          option.value = produto.id;
          option.textContent = `${produto.nome} - ${formatarMoeda(produto.valor_unitario)} (Estoque: ${produto.estoque_loja} ${produto.unidade})`;
          option.setAttribute('data-valor', produto.valor_unitario);
          option.setAttribute('data-unidade', produto.unidade);
          select.appendChild(option);
        });
        
        $(select).select2({
          placeholder: "Selecione um produto",
          width: '100%'
        });
      }
    } catch (error) {
      console.error('Erro ao carregar produtos:', error);
      showFlashMessage('error', 'Erro ao carregar produtos');
    }
  }

  async function carregarCaixasFechados() {
    try {
      const response = await fetchWithErrorHandling('/admin/api/caixas/fechados');
      
      if (response.success) {
        caixasFechados = response.caixas;
        const select = document.getElementById('caixaRetroativo');
        
        select.innerHTML = '<option value="">Selecione o caixa</option>';
        
        response.caixas.forEach(caixa => {
          const option = document.createElement('option');
          option.value = caixa.id;
          option.textContent = `Caixa #${caixa.id} - ${caixa.operador} (${caixa.data_abertura} até ${caixa.data_fechamento})`;
          select.appendChild(option);
        });
      }
    } catch (error) {
      console.error('Erro ao carregar caixas fechados:', error);
      showFlashMessage('error', 'Erro ao carregar caixas fechados');
    }
  }

  function adicionarProdutoRetroativa() {
    const produtoSelect = document.getElementById('produtoRetroativo');
    const quantidadeInput = document.getElementById('quantidadeRetroativa');
    
    const produtoId = produtoSelect.value;
    const quantidade = parseFloat(quantidadeInput.value);
    
    if (!produtoId || !quantidade || quantidade <= 0) {
      showFlashMessage('warning', 'Selecione um produto e informe uma quantidade válida');
      return;
    }
    
    const produto = produtosVendaRetroativa.find(p => p.id == produtoId);
    if (!produto) {
      showFlashMessage('error', 'Produto não encontrado');
      return;
    }
    
    const itemExistente = itensVendaRetroativa.find(item => item.produto_id == produtoId);
    if (itemExistente) {
      itemExistente.quantidade += quantidade;
      itemExistente.valor_total = itemExistente.quantidade * itemExistente.valor_unitario;
    } else {
      const selectedOption = produtoSelect.options[produtoSelect.selectedIndex];
      itensVendaRetroativa.push({
        produto_id: produtoId,
        nome: selectedOption.text.split(' - ')[0],
        quantidade: quantidade,
        valor_unitario: parseFloat(selectedOption.getAttribute('data-valor')),
        valor_total: quantidade * parseFloat(selectedOption.getAttribute('data-valor')),
        unidade: selectedOption.getAttribute('data-unidade')
      });
    }
    
    atualizarTabelaProdutosRetroativa();
    
    produtoSelect.value = '';
    $(produtoSelect).trigger('change');
    quantidadeInput.value = '';
    
    produtoSelect.focus();
  }

  function adicionarPagamentoRetroativo() {
    const formaSelect = document.getElementById('formaPagamentoRetroativo');
    const valorInput = document.getElementById('valorPagamentoRetroativo');
    
    const forma = formaSelect.value;
    const valor = parseFloat(valorInput.value);
    
    if (!forma || !valor || valor <= 0) {
      showFlashMessage('warning', 'Selecione uma forma de pagamento e informe um valor válido');
      return;
    }
    
    pagamentosVendaRetroativa.push({
      forma_pagamento: forma,
      valor: valor
    });
    
    atualizarTabelaPagamentosRetroativa();
    
    formaSelect.value = '';
    valorInput.value = '';
    formaSelect.focus();
  }

  async function salvarVendaRetroativa() {
    const clienteId = document.getElementById('clienteRetroativo').value;
    const caixaId = document.getElementById('caixaRetroativo').value;
    const dataEmissao = document.getElementById('dataEmissaoRetroativa').value;
    const observacao = document.getElementById('observacaoRetroativa').value;
    
    if (!clienteId) {
      showFlashMessage('warning', 'Selecione um cliente');
      return;
    }
    
    if (!caixaId) {
      showFlashMessage('warning', 'Selecione um caixa');
      return;
    }
    
    if (!dataEmissao) {
      showFlashMessage('warning', 'Informe a data da venda');
      return;
    }
    
    if (itensVendaRetroativa.length === 0) {
      showFlashMessage('warning', 'Adicione pelo menos um produto');
      return;
    }
    
    if (pagamentosVendaRetroativa.length === 0) {
      showFlashMessage('warning', 'Adicione pelo menos uma forma de pagamento');
      return;
    }
    
    const valorTotal = itensVendaRetroativa.reduce((total, item) => total + item.valor_total, 0);
    const aPrazo = pagamentosVendaRetroativa.some(p => p.forma_pagamento === 'a_prazo');
    
    const dadosVenda = {
      cliente_id: clienteId,
      caixa_id: caixaId,
      data_emissao: dataEmissao.replace('T', ' ') + ':00',
      itens: itensVendaRetroativa.map(item => ({
        produto_id: item.produto_id,
        quantidade: item.quantidade,
        valor_unitario: item.valor_unitario,
        valor_total: item.valor_total
      })),
      pagamentos: pagamentosVendaRetroativa,
      valor_total: valorTotal,
      valor_recebido: pagamentosVendaRetroativa
        .filter(p => p.forma_pagamento !== 'a_prazo')
        .reduce((total, pg) => total + pg.valor, 0),
      observacao: observacao,
      a_prazo: aPrazo
    };
    
    try {
      const response = await fetchWithErrorHandling('/admin/api/vendas/retroativa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(dadosVenda)
      });
      
      if (response.success) {
        showFlashMessage('success', 'Venda retroativa registrada com sucesso!');
        limparFormularioRetroativa();
        closeModal('modalVendaRetroativa');
        loadCaixasData();
      } else {
        showFlashMessage('error', response.message || 'Erro ao registrar venda retroativa');
      }
    } catch (error) {
      console.error('Erro ao enviar venda retroativa:', error);
      showFlashMessage('error', 'Erro ao enviar venda retroativa');
    }
  }

  async function abrirModalVendaRetroativa(caixaId = null) {
    limparFormularioRetroativa();
    await carregarClientesRetroativa();
    await carregarProdutosRetroativa();
    await carregarCaixasFechados();
    
    if (caixaId) {
      document.getElementById('caixaRetroativo').value = caixaId;
    }
    
    const now = new Date();
    document.getElementById('dataEmissaoRetroativa').value = formatarDataParaInput(now);
    openModal('modalVendaRetroativa');
  }

  function setupVendaRetroativaModal() {
    document.getElementById('btnAdicionarProdutoRetroativo').addEventListener('click', adicionarProdutoRetroativa);
    document.getElementById('btnAdicionarPagamentoRetroativo').addEventListener('click', adicionarPagamentoRetroativo);
    document.getElementById('btnSalvarVendaRetroativa').addEventListener('click', salvarVendaRetroativa);
    
    document.getElementById('quantidadeRetroativa').addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        adicionarProdutoRetroativa();
      }
    });
    
    document.getElementById('valorPagamentoRetroativo').addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        adicionarPagamentoRetroativo();
      }
    });
    
    document.addEventListener('click', function(e) {
      if (e.target.closest('.btn-remover-produto')) {
        const index = parseInt(e.target.closest('.btn-remover-produto').getAttribute('data-index'));
        itensVendaRetroativa.splice(index, 1);
        atualizarTabelaProdutosRetroativa();
      }
      
      if (e.target.closest('.btn-remover-pagamento')) {
        const index = parseInt(e.target.closest('.btn-remover-pagamento').getAttribute('data-index'));
        pagamentosVendaRetroativa.splice(index, 1);
        atualizarTabelaPagamentosRetroativa();
      }
    });
  }

  // ===== CAIXAS =====
  async function loadCaixasData() {
    try {
      const status = document.getElementById('caixaStatus')?.value;
      let url = '/admin/caixas';
      
      if (status) {
        url += `?status=${status}`;
      }
      
      const data = await fetchWithErrorHandling(url);
      
      if (data.success) {
        const caixasTable = document.querySelector('#caixasTable tbody');
        if (caixasTable) {
          caixasTable.innerHTML = '';
          
          data.data.forEach(caixa => {
            const row = document.createElement('tr');
            
            const dataAbertura = formatDateTime(caixa.data_abertura);
            const dataFechamento = caixa.data_fechamento ? formatDateTime(caixa.data_fechamento) : '-';
            
            const valorAbertura = formatarMoeda(caixa.valor_abertura);
            const valorFechamento = caixa.valor_fechamento ? formatarMoeda(caixa.valor_fechamento) : '-';
            const valorConfirmado = caixa.valor_confirmado ? formatarMoeda(caixa.valor_confirmado) : '-';
            
            let statusClass = '';
            let statusText = '';
            if (caixa.status === 'aberto') {
              statusClass = 'badge-success';
              statusText = 'Aberto';
            } else if (caixa.status === 'fechado') {
              statusClass = 'badge-primary';
              statusText = 'Fechado';
            } else if (caixa.status === 'analise') {
              statusClass = 'badge-warning';
              statusText = 'Em Análise';
            } else if (caixa.status === 'rejeitado') {
              statusClass = 'badge-danger';
              statusText = 'Rejeitado';
            }
            
            row.innerHTML = `
              <td>${caixa.id}</td>
              <td>${caixa.operador?.nome || '-'}</td>
              <td>${dataAbertura}</td>
              <td>${dataFechamento}</td>
              <td>${valorAbertura}</td>
              <td>${valorFechamento}</td>
              <td><span class="badge ${statusClass}">${statusText}</span></td>
              <td>
                <div class="table-actions">
                  <button class="btn-icon btn-info visualizar-caixa" data-id="${caixa.id}" title="Visualizar">
                    <i class="fas fa-eye"></i>
                  </button>
                  <button class="btn-icon btn-primary enviar-analise-caixa" data-id="${caixa.id}" title="Enviar para Análise">
                    <i class="fas fa-paper-plane"></i>
                  </button>
                  <button class="btn-icon btn-success aprovar-caixa" data-id="${caixa.id}" title="Aprovar">
                    <i class="fas fa-check"></i>
                  </button>
                  <button class="btn-icon btn-danger recusar-caixa" data-id="${caixa.id}" title="Recusar">
                    <i class="fas fa-times"></i>
                  </button>
                  <button class="btn-icon btn-warning reabrir-caixa" data-id="${caixa.id}" title="Reabrir">
                    <i class="fas fa-unlock"></i>
                  </button>
                  <button class="btn-icon btn-secondary venda-retroativa-caixa" data-id="${caixa.id}" title="Venda Retroativa">
                    <i class="fas fa-history"></i>
                  </button>
                </div>
              </td>
            `;
            caixasTable.appendChild(row);
          });
          
          setupCaixaActions();
        }
      }
    } catch (error) {
      console.error('Erro ao carregar caixas:', error);
      showFlashMessage('error', 'Erro ao carregar lista de caixas');
    }
  }

  function setupCaixaActions() {
    document.querySelectorAll('.visualizar-caixa').forEach(btn => {
      btn.addEventListener('click', function() {
        const caixaId = this.getAttribute('data-id');
        openVisualizarCaixaModal(caixaId);
      });
    });

    document.querySelectorAll('.enviar-analise-caixa').forEach(btn => {
      btn.addEventListener('click', async function() {
        const caixaId = this.getAttribute('data-id');
        
        try {
          const valorFechamento = prompt('Informe o valor de fechamento para análise:');
          if (!valorFechamento) return;
          
          if (isNaN(valorFechamento) || parseFloat(valorFechamento) <= 0) {
            showFlashMessage('error', 'Digite um valor válido!');
            return;
          }
          
          const observacoes = prompt('Observações (opcional):') || '';
          
          const response = await fetchWithErrorHandling(`/admin/caixas/${caixaId}/enviar_analise`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              valor_fechamento: parseFloat(valorFechamento),
              observacoes: observacoes
            })
          });
          
          if (response.success) {
            showFlashMessage('success', 'Caixa enviado para análise com sucesso');
            loadCaixasData();
          }
        } catch (error) {
          console.error('Erro ao enviar para análise:', error);
          showFlashMessage('error', error.message || 'Erro ao enviar para análise');
        }
      });
    });

    document.querySelectorAll('.aprovar-caixa').forEach(btn => {
      btn.addEventListener('click', async function() {
        const caixaId = this.getAttribute('data-id');
        
        try {
          const valorConfirmado = prompt('Valor confirmado (opcional):');
          const observacoes = prompt('Observações (opcional):') || '';
          
          if (valorConfirmado === null && observacoes === null) return;
          
          if (valorConfirmado && (isNaN(valorConfirmado) || parseFloat(valorConfirmado) <= 0)) {
            showFlashMessage('error', 'Digite um valor válido ou deixe em branco!');
            return;
          }
          
          const response = await fetchWithErrorHandling(`/admin/caixas/${caixaId}/aprovar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              valor_confirmado: valorConfirmado ? parseFloat(valorConfirmado) : null,
              observacoes: observacoes
            })
          });
          
          if (response.success) {
            showFlashMessage('success', 'Caixa aprovado com sucesso');
            loadCaixasData();
          }
        } catch (error) {
          console.error('Erro ao aprovar caixa:', error);
          showFlashMessage('error', error.message || 'Erro ao aprovar caixa');
        }
      });
    });

    document.querySelectorAll('.recusar-caixa').forEach(btn => {
      btn.addEventListener('click', async function() {
        const caixaId = this.getAttribute('data-id');
        
        try {
          const motivo = prompt('Motivo da recusa (obrigatório):');
          if (!motivo) {
            showFlashMessage('warning', 'O motivo é obrigatório');
            return;
          }
          
          const valorCorreto = prompt('Valor correto (opcional):');
          
          if (valorCorreto && (isNaN(valorCorreto) || parseFloat(valorCorreto) <= 0)) {
            showFlashMessage('error', 'Digite um valor válido ou deixe em branco!');
            return;
          }
          
          const response = await fetchWithErrorHandling(`/admin/caixas/${caixaId}/recusar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              motivo: motivo,
              valor_correto: valorCorreto ? parseFloat(valorCorreto) : null
            })
          });
          
          if (response.success) {
            showFlashMessage('success', 'Caixa recusado com sucesso');
            loadCaixasData();
          }
        } catch (error) {
          console.error('Erro ao recusar caixa:', error);
          showFlashMessage('error', error.message || 'Erro ao recusar caixa');
        }
      });
    });

    document.querySelectorAll('.reabrir-caixa').forEach(btn => {
      btn.addEventListener('click', async function() {
        const caixaId = this.getAttribute('data-id');
        
        try {
          const motivo = prompt('Motivo da reabertura (opcional):') || '';
          
          if (confirm('Tem certeza que deseja reabrir este caixa?')) {
            const response = await fetchWithErrorHandling(`/admin/caixas/${caixaId}/reabrir`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ motivo: motivo })
            });
            
            if (response.success) {
              showFlashMessage('success', 'Caixa reaberto com sucesso');
              loadCaixasData();
            }
          }
        } catch (error) {
          console.error('Erro ao reabrir caixa:', error);
          showFlashMessage('error', error.message || 'Erro ao reabrir caixa');
        }
      });
    });

    document.querySelectorAll('.venda-retroativa-caixa').forEach(btn => {
      btn.addEventListener('click', function() {
        const caixaId = this.getAttribute('data-id');
        abrirModalVendaRetroativa(caixaId);
      });
    });
  }

  async function openVisualizarCaixaModal(caixaId) {
    try {
      const response = await fetchWithErrorHandling(`/admin/caixas/${caixaId}`);
      
      if (response.success) {
        const caixa = response.data;
        
        if (document.getElementById('visualizarCaixaId')) document.getElementById('visualizarCaixaId').textContent = caixa.id;
        if (document.getElementById('visualizarCaixaOperador')) document.getElementById('visualizarCaixaOperador').textContent = caixa.operador?.nome || '-';
        if (document.getElementById('visualizarCaixaDataAbertura')) document.getElementById('visualizarCaixaDataAbertura').textContent = formatDateTime(caixa.data_abertura);
        if (document.getElementById('visualizarCaixaValorAbertura')) document.getElementById('visualizarCaixaValorAbertura').textContent = formatarMoeda(caixa.valor_abertura);
        
        const statusElement = document.getElementById('visualizarCaixaStatus');
        if (statusElement) {
          let statusText = '';
          let statusClass = '';
          
          if (caixa.status === 'aberto') {
            statusText = 'Aberto';
            statusClass = 'badge-success';
          } else if (caixa.status === 'fechado') {
            statusText = 'Fechado';
            statusClass = 'badge-primary';
          } else if (caixa.status === 'analise') {
            statusText = 'Em Análise';
            statusClass = 'badge-warning';
          } else if (caixa.status === 'rejeitado') {
            statusText = 'Rejeitado';
            statusClass = 'badge-danger';
          }
          
          statusElement.textContent = statusText;
          statusElement.className = 'badge ' + statusClass;
        }
        
        if (['fechado', 'analise', 'rejeitado'].includes(caixa.status)) {
          if (document.getElementById('visualizarCaixaDataFechamento')) document.getElementById('visualizarCaixaDataFechamento').textContent = caixa.data_fechamento ? formatDateTime(caixa.data_fechamento) : '-';
          if (document.getElementById('visualizarCaixaValorFechamento')) document.getElementById('visualizarCaixaValorFechamento').textContent = caixa.valor_fechamento ? formatarMoeda(caixa.valor_fechamento) : '-';
          if (document.getElementById('visualizarCaixaValorConfirmado')) document.getElementById('visualizarCaixaValorConfirmado').textContent = caixa.valor_confirmado ? formatarMoeda(caixa.valor_confirmado) : '-';
          
          const caixaFechamentoInfo = document.getElementById('caixaFechamentoInfo');
          if (caixaFechamentoInfo) caixaFechamentoInfo.style.display = 'block';
        } else {
          const caixaFechamentoInfo = document.getElementById('caixaFechamentoInfo');
          if (caixaFechamentoInfo) caixaFechamentoInfo.style.display = 'none';
        }
        
        if (document.getElementById('visualizarCaixaObsOperador')) document.getElementById('visualizarCaixaObsOperador').textContent = caixa.observacoes_operador || 'Nenhuma observação';
        if (document.getElementById('visualizarCaixaObsAdmin')) document.getElementById('visualizarCaixaObsAdmin').textContent = caixa.observacoes_admin || 'Nenhuma observação';
        
        await loadCaixaFinanceiro(caixaId);
        openModal('visualizarCaixaModal');
      }
    } catch (error) {
      console.error('Erro ao visualizar caixa:', error);
      showFlashMessage('error', 'Erro ao carregar dados do caixa');
    }
  }

  async function loadCaixaFinanceiro(caixaId) {
    try {
      const response = await fetchWithErrorHandling(`/admin/caixas/${caixaId}/financeiro`);
      caixaIdAtual = caixaId;

      if (response.success) {
        const tableBody = document.querySelector('#caixaFinanceiroTable tbody');
        if (tableBody) {
          tableBody.innerHTML = '';

          let totalEntradas = 0;
          let totalSaidas = 0;

          response.data.forEach(item => {
            const row = document.createElement('tr');
            const valor = parseFloat(item.valor);

            if (item.tipo === 'entrada') {
              totalEntradas += valor;
            } else {
              totalSaidas += valor;
            }

            row.innerHTML = `
              <td>${formatDateTime(item.data)}</td>
              <td><span class="badge ${item.tipo === 'entrada' ? 'badge-success' : 'badge-danger'}">${item.tipo === 'entrada' ? 'Entrada' : 'Saída'}</span></td>
              <td>${item.categoria || '-'}</td>
              <td>${formatarMoeda(valor)}</td>
              <td>${item.descricao || '-'}</td>
            `;
            tableBody.appendChild(row);
          });

          if (document.getElementById('caixaTotalEntradas')) {
            document.getElementById('caixaTotalEntradas').textContent = formatarMoeda(totalEntradas);
          }
          if (document.getElementById('caixaTotalSaidas')) {
            document.getElementById('caixaTotalSaidas').textContent = formatarMoeda(totalSaidas);
          }
          if (document.getElementById('caixaSaldo')) {
            document.getElementById('caixaSaldo').textContent = formatarMoeda(totalEntradas - totalSaidas);
          }

          const formasPagamento = response.vendas_por_forma_pagamento || {};

          document.getElementById('totalPixFabiano').textContent = formatarMoeda(formasPagamento.pix_fabiano || 0);
          document.getElementById('totalPixMaquineta').textContent = formatarMoeda(formasPagamento.pix_maquineta || 0);
          document.getElementById('totalPixEdFrance').textContent = formatarMoeda(formasPagamento.pix_edfrance || 0);
          document.getElementById('totalPixLoja').textContent = formatarMoeda(formasPagamento.pix_loja || 0);
          document.getElementById('totalDinheiro').textContent = formatarMoeda(formasPagamento.dinheiro || 0);
          document.getElementById('totalCartaoCredito').textContent = formatarMoeda(formasPagamento.cartao_credito || 0);
          document.getElementById('totalCartaoDebito').textContent = formatarMoeda(formasPagamento.cartao_debito || 0);
          document.getElementById('totalAPrazo').textContent = formatarMoeda(formasPagamento.a_prazo || 0);
        }
      }
    } catch (error) {
      console.error('Erro ao carregar financeiro do caixa:', error);
      showFlashMessage('error', 'Erro ao carregar movimentações financeiras');
    }
  }

  document.getElementById('abrirPdfCaixa').addEventListener('click', () => {
    if (caixaIdAtual) {
      const url = `/admin/caixas/${caixaIdAtual}/financeiro/pdf`;
      window.open(url, '_blank');
    } else {
      alert('Nenhum caixa selecionado');
    }
  });

  // Event Listeners para Caixas
  document.getElementById('refreshData')?.addEventListener('click', loadDashboardData);

  // ===== MOVIMENTAÇÕES =====
  async function loadMovimentacoesData() {
    try {
      const dateInicio = document.getElementById('movimentacaoDateInicio')?.value;
      const dateFim = document.getElementById('movimentacaoDateFim')?.value;
      const tipo = document.getElementById('movimentacaoTipo')?.value;
      
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
        if (table) {
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
      }
    } catch (error) {
      console.error('Erro ao carregar movimentações:', error);
      showFlashMessage('error', 'Erro ao carregar histórico de movimentações');
    }
  }

  // Event Listeners para Movimentações
  document.getElementById('filterMovimentacoes')?.addEventListener('click', loadMovimentacoesData);

  // ===== FINANCEIRO =====
  async function loadFinanceiroData() {
    try {
      const dateInicio = document.getElementById('dateInicio')?.value;
      const dateFim = document.getElementById('dateFim')?.value;
      
      let url = '/admin/financeiro';
      if (dateInicio || dateFim) {
        url += `?data_inicio=${dateInicio}&data_fim=${dateFim}`;
      }
      
      const data = await fetchWithErrorHandling(url);
      
      if (data.success) {
        const receitasValue = document.getElementById('receitasValue');
        if (receitasValue) receitasValue.textContent = data.resumo.receitas;
        
        const despesasValue = document.getElementById('despesasValue');
        if (despesasValue) despesasValue.textContent = data.resumo.despesas;
        
        const saldoValue = document.getElementById('saldoValue');
        if (saldoValue) saldoValue.textContent = data.resumo.saldo;
        
        const financeiroTable = document.querySelector('#financeiroTable tbody');
        if (financeiroTable) {
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
      }
    } catch (error) {
      console.error('Erro ao carregar dados financeiros:', error);
      showFlashMessage('error', 'Erro ao carregar dados financeiros');
    }
  }

  // Event Listeners para Financeiro
  document.getElementById('filterFinanceiro')?.addEventListener('click', loadFinanceiroData);

  // ===== USUÁRIOS =====
  async function loadUsuariosData() {
    try {
      const searchText = document.getElementById('searchUsuario')?.value.toLowerCase() || '';
      const data = await fetchWithErrorHandling('/admin/usuarios');
      
      if (data.success) {
        const usuariosTable = document.querySelector('#usuariosTable tbody');
        if (usuariosTable) {
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
      }
    } catch (error) {
      console.error('Erro ao carregar usuários:', error);
      showFlashMessage('error', 'Erro ao carregar lista de usuários');
    }
  }

  async function openEditarUsuarioModal(usuarioId = null) {
    const isEdit = usuarioId !== null;
    
    const usuarioModalTitle = document.getElementById('usuarioModalTitle');
    if (usuarioModalTitle) {
      usuarioModalTitle.textContent = isEdit ? 'Editar Usuário' : 'Cadastrar Usuário';
    }
    
    const usuarioModalSubmitText = document.getElementById('usuarioModalSubmitText');
    if (usuarioModalSubmitText) {
      usuarioModalSubmitText.textContent = isEdit ? 'Atualizar' : 'Cadastrar';
    }
    
    const senhaInput = document.getElementById('usuarioSenha');
    const confirmaSenhaInput = document.getElementById('usuarioConfirmaSenha');

    if (isEdit) {
      if (senhaInput) {
        senhaInput.required = false;
        senhaInput.placeholder = "Deixe em branco para manter a senha atual";
      }
      if (confirmaSenhaInput) {
        confirmaSenhaInput.required = false;
        confirmaSenhaInput.placeholder = "Repita a nova senha se for alterar";
      }
    } else {
      if (senhaInput) {
        senhaInput.required = true;
        senhaInput.placeholder = "";
      }
      if (confirmaSenhaInput) {
        confirmaSenhaInput.required = true;
        confirmaSenhaInput.placeholder = "";
      }
    }
    
    if (!isEdit) {
      const usuarioForm = document.getElementById('usuarioForm');
      if (usuarioForm) usuarioForm.reset();
      
      const usuarioIdField = document.getElementById('usuarioId');
      if (usuarioIdField) usuarioIdField.value = '';
    }
    
    if (isEdit) {
      try {
        const response = await fetchWithErrorHandling(`/admin/usuarios/${usuarioId}`);
        
        if (!response.success) {
          throw new Error(response.message || 'Erro ao carregar usuário');
        }

        const usuario = response.usuario;
        
        if (document.getElementById('usuarioId')) document.getElementById('usuarioId').value = usuario.id;
        if (document.getElementById('usuarioNome')) document.getElementById('usuarioNome').value = usuario.nome;
        if (document.getElementById('usuarioCpf')) document.getElementById('usuarioCpf').value = usuario.cpf;
        if (document.getElementById('usuarioPerfil')) document.getElementById('usuarioPerfil').value = usuario.tipo.toLowerCase();
        if (document.getElementById('usuarioStatus')) document.getElementById('usuarioStatus').value = usuario.status ? 'true' : 'false';
        if (document.getElementById('usuarioObservacoes')) document.getElementById('usuarioObservacoes').value = usuario.observacoes || '';
        
        if (document.getElementById('usuarioSenha')) document.getElementById('usuarioSenha').value = '';
        if (document.getElementById('usuarioConfirmaSenha')) document.getElementById('usuarioConfirmaSenha').value = '';
      } catch (error) {
        console.error('Erro ao carregar dados do usuário:', error);
        showFlashMessage('error', error.message || 'Erro ao carregar dados do usuário');
        return;
      }
    }
    
    openModal('usuarioModal');
  }

  async function openVisualizarUsuarioModal(usuarioId) {
    try {
      const response = await fetchWithErrorHandling(`/admin/usuarios/${usuarioId}`);
      
      if (response.success) {
        const usuario = response.usuario;
        
        if (document.getElementById('visualizarUsuarioNome')) document.getElementById('visualizarUsuarioNome').textContent = usuario.nome;
        if (document.getElementById('visualizarUsuarioCPF')) document.getElementById('visualizarUsuarioCPF').textContent = usuario.cpf;
        if (document.getElementById('visualizarUsuarioUltimoAcesso')) document.getElementById('visualizarUsuarioUltimoAcesso').textContent = usuario.ultimo_acesso || 'Nunca acessou';
        if (document.getElementById('visualizarUsuarioDataCadastro')) document.getElementById('visualizarUsuarioDataCadastro').textContent = usuario.data_cadastro || 'Data não disponível';
        if (document.getElementById('visualizarUsuarioObservacoes')) document.getElementById('visualizarUsuarioObservacoes').textContent = usuario.observacoes || 'Nenhuma observação';
        
        const perfilBadge = document.getElementById('visualizarUsuarioPerfil');
        if (perfilBadge) {
          perfilBadge.textContent = formatPerfil(usuario.tipo);
          perfilBadge.className = 'badge';
          perfilBadge.classList.add(`badge-${usuario.tipo.toLowerCase()}`);
        }
        
        const statusBadge = document.getElementById('visualizarUsuarioStatus');
        if (statusBadge) {
          statusBadge.textContent = usuario.status ? 'Ativo' : 'Inativo';
          statusBadge.className = 'badge';
          statusBadge.classList.add(usuario.status ? 'badge-success' : 'badge-danger');
        }

        openModal('visualizarUsuarioModal');
      }
    } catch (error) {
      console.error('Erro ao carregar dados do usuário:', error);
      showFlashMessage('error', 'Erro ao carregar dados do usuário');
    }
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
        const confirmarExclusaoTexto = document.getElementById('confirmarExclusaoTexto');
        const confirmarExclusaoBtn = document.getElementById('confirmarExclusaoBtn');
        
        if (confirmarExclusaoTexto) confirmarExclusaoTexto.textContent = `Tem certeza que deseja excluir permanentemente o usuário ${usuarioId}?`;
        if (confirmarExclusaoBtn) {
          confirmarExclusaoBtn.setAttribute('data-id', usuarioId);
          confirmarExclusaoBtn.setAttribute('data-type', 'usuario');
        }
        openModal('confirmarExclusaoModal');
      });
    });
  }

  // Event Listeners para Usuários
  document.getElementById('searchUsuario')?.addEventListener('input', loadUsuariosData);
  document.getElementById('refreshUsuarios')?.addEventListener('click', loadUsuariosData);
  document.getElementById('addUsuario')?.addEventListener('click', () => openEditarUsuarioModal());

  const usuarioForm = document.getElementById('usuarioForm');
  if (usuarioForm) {
    usuarioForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const isEdit = document.getElementById('usuarioId')?.value !== '';
      const usuarioId = document.getElementById('usuarioId')?.value || '';
      
      const formData = {
        nome: document.getElementById('usuarioNome')?.value || '',
        cpf: document.getElementById('usuarioCpf')?.value || '',
        tipo: document.getElementById('usuarioPerfil')?.value || '',
        status: document.getElementById('usuarioStatus')?.value === 'true',
        observacoes: document.getElementById('usuarioObservacoes')?.value || ''
      };
      
      const senha = document.getElementById('usuarioSenha')?.value || '';
      const confirmaSenha = document.getElementById('usuarioConfirmaSenha')?.value || '';
      
      if (senha || confirmaSenha) {
        if (senha !== confirmaSenha) {
          showFlashMessage('error', 'As senhas não coincidem');
          return;
        }
        if (senha.length > 0) {
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
  }

  // ===== DESCONTOS =====
  async function loadDescontosData() {
    try {
      const searchText = document.getElementById('searchDesconto')?.value.toLowerCase() || '';
      const data = await fetchWithErrorHandling('/admin/descontos');
      
      if (data.success) {
        const descontosTable = document.querySelector('#descontosTable tbody');
        if (descontosTable) {
          descontosTable.innerHTML = '';
          
          data.descontos.forEach(desconto => {
            if (searchText && !(desconto.identificador || '').toLowerCase().includes(searchText)) {
              return;
            }
            
            const row = document.createElement('tr');
            row.innerHTML = `
              <td>${desconto.identificador || '-'}</td>
              <td>${desconto.descricao || '-'}</td>
              <td>${desconto.quantidade_minima}</td>
              <td>${desconto.quantidade_maxima}</td>
              <td>${desconto.valor_unitario_com_desconto || '0,00'}</td>
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
      }
    } catch (error) {
      console.error('Erro ao carregar descontos:', error);
      showFlashMessage('error', 'Erro ao carregar lista de descontos');
    }
  }

  async function openEditarDescontoModal(descontoId) {
    try {
      const response = await fetchWithErrorHandling(`/admin/descontos/${descontoId}`);

      if (response.success) {
        const desconto = response.desconto;

        if (document.getElementById('descontoId')) document.getElementById('descontoId').value = desconto.id;
        if (document.getElementById('descontoProdutoId')) document.getElementById('descontoProdutoId').value = desconto.produto_id;
        if (document.getElementById('descontoIdentificador')) document.getElementById('descontoIdentificador').value = desconto.identificador;
        if (document.getElementById('descontoQuantidadeMinima')) document.getElementById('descontoQuantidadeMinima').value = desconto.quantidade_minima;
        if (document.getElementById('descontoQuantidadeMaxima')) document.getElementById('descontoQuantidadeMaxima').value = desconto.quantidade_maxima;
        if (document.getElementById('descontoValorUnitario')) document.getElementById('descontoValorUnitario').value = limparValor(desconto.valor_unitario_com_desconto);

        if (desconto.valido_ate) {
          let dataValidoAte = desconto.valido_ate;

          if (dataValidoAte.includes(' ')) {
            dataValidoAte = dataValidoAte.split(' ')[0];
          }

          if (document.getElementById('descontoValidoAte')) document.getElementById('descontoValidoAte').value = dataValidoAte;
        } else {
          if (document.getElementById('descontoValidoAte')) document.getElementById('descontoValidoAte').value = '';
        }

        if (document.getElementById('descontoDescricao')) document.getElementById('descontoDescricao').value = desconto.descricao || '';
        if (document.getElementById('descontoAtivo')) document.getElementById('descontoAtivo').value = desconto.ativo ? 'true' : 'false';

        const descontoModalTitle = document.getElementById('descontoModalTitle');
        if (descontoModalTitle) descontoModalTitle.textContent = 'Editar Desconto';
        openModal('descontoModal');
      } else {
        showFlashMessage('error', response.erro || 'Erro ao carregar dados do desconto');
      }
    } catch (error) {
      console.error('Erro ao carregar dados do desconto:', error);
      showFlashMessage('error', 'Erro ao carregar dados do desconto');
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
        const confirmarExclusaoTexto = document.getElementById('confirmarExclusaoTexto');
        const confirmarExclusaoBtn = document.getElementById('confirmarExclusaoBtn');
        
        if (confirmarExclusaoTexto) confirmarExclusaoTexto.textContent = `Tem certeza que deseja excluir este desconto?`;
        if (confirmarExclusaoBtn) {
          confirmarExclusaoBtn.setAttribute('data-id', descontoId);
          confirmarExclusaoBtn.setAttribute('data-type', 'desconto');
        }
        openModal('confirmarExclusaoModal');
      });
    });
  }

  // Event Listeners para Descontos
  document.getElementById('searchDesconto')?.addEventListener('input', loadDescontosData);
  document.getElementById('refreshDescontos')?.addEventListener('click', loadDescontosData);
  document.getElementById('addDesconto')?.addEventListener('click', () => {
    const descontoForm = document.getElementById('descontoForm');
    if (descontoForm) descontoForm.reset();
    
    if (document.getElementById('descontoId')) document.getElementById('descontoId').value = '';
    if (document.getElementById('descontoAtivo')) document.getElementById('descontoAtivo').value = 'true';
    
    const descontoModalTitle = document.getElementById('descontoModalTitle');
    if (descontoModalTitle) descontoModalTitle.textContent = 'Cadastrar Desconto';
    openModal('descontoModal');
  });

  const descontoForm = document.getElementById('descontoForm');
  if (descontoForm) {
    descontoForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const descontoId = document.getElementById('descontoId')?.value || '';
      const isEdit = descontoId !== '';
      
      const formData = {
        identificador: document.getElementById('descontoIdentificador')?.value || '',
        quantidade_minima: document.getElementById('descontoQuantidadeMinima')?.value || 0,
        quantidade_maxima: document.getElementById('descontoQuantidadeMaxima')?.value || 0,
        valor_unitario_com_desconto: document.getElementById('descontoValorUnitario')?.value || 0,
        valido_ate: document.getElementById('descontoValidoAte')?.value || null,
        descricao: document.getElementById('descontoDescricao')?.value || '',
        ativo: document.getElementById('descontoAtivo')?.value === 'true'
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
  }

  // ===== INICIALIZAÇÃO =====
  updateDateTime();
  setInterval(updateDateTime, 60000);
  
  setupModalEvents();
  setupNavigation();
  setupVendaRetroativaModal();
  setupClienteActions()
  
  document.getElementById('confirmarExclusaoBtn')?.addEventListener('click', async function() {
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
      } else if (type === 'caixa') {
        url = `/admin/caixas/${id}`;
      }
      
      if (!url) return;
      
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
        if (type === 'caixa') loadCaixasData();
      } else {
        showFlashMessage('error', response.message || `Erro ao excluir ${type}`);
      }
    } catch (error) {
      console.error(`Erro ao excluir ${type}:`, error);
      showFlashMessage('error', `Erro ao excluir ${type}`);
    }
  });
  
  async function loadInitialData() {
    try {
      await Promise.all([
        loadDashboardData()
      ]);
      
      const activeTab = document.querySelector('.sidebar-nav li.active');
      if (activeTab) {
        const tabId = activeTab.getAttribute('data-tab');
        if (tabId === 'clientes') loadClientesData();
        if (tabId === 'produtos') loadProdutosData();
        if (tabId === 'financeiro') loadFinanceiroData();
        if (tabId === 'usuarios') loadUsuariosData();
        if (tabId === 'estoque') loadMovimentacoesData();
        if (tabId === 'descontos') loadDescontosData();
        if (tabId === 'caixas') loadCaixasData();
      }
    } catch (error) {
      console.error('Erro ao carregar dados iniciais:', error);
    }
  }

  loadInitialData();
});