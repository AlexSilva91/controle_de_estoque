document.addEventListener('DOMContentLoaded', function() {
  // ===== VARIÁVEIS GLOBAIS =====
  let produtosVendaRetroativa = [];
  let clientesVendaRetroativa = [];
  let caixasFechados = [];
  let itensVendaRetroativa = [];
  let pagamentosVendaRetroativa = [];
  let vendasDespesasChart, formasPagamentoChart, caixasChart, vendasDiariasChart, produtosMaiorFluxoChart;
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
  document.addEventListener('keydown', function(e) {
    // Fechar modal quando a tecla ESC for pressionada
    if (e.key === 'Escape' || e.keyCode === 27) {
      const modaisAbertos = document.querySelectorAll('.modal[style*="display: flex"]');
      
      // Fechar todos os modais abertos
      modaisAbertos.forEach(modal => {
        closeModal(modal.id);
      });
      
      // Prevenir comportamento padrão se necessário
      e.preventDefault();
    }
  });
  function openModal(modalElement) {
      if (typeof modalElement === 'string') {
          modalElement = document.getElementById(modalElement);
      }
      if (!modalElement) {
          console.error('Modal não encontrado');
          return;
      }
      modalElement.style.display = 'flex';
      document.body.style.overflow = 'hidden';
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
    document.querySelector('.sidebar-nav li[data-tab="contas-receber"]').addEventListener('click', function(e) {
        e.preventDefault();
        openModal('contasReceberModal');
        loadContasReceber();
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
        if (tabId === 'relatorio-saidas') loadRelatorioSaidasData();
        if (tabId === 'contas-receber') loadContasReceber();
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
      if (produtosMaiorFluxoChart) produtosMaiorFluxoChart.destroy();

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
            labels: vendasDiariasData.vendas_mensais_caixa.map(c => c.data_abertura),
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
        // Gráfico de Produtos com Maior Fluxo
        const produtosFluxoData = await fetchWithErrorHandling('/admin/dashboard/produtos-maior-fluxo');
        if (produtosFluxoData.success) {
            const produtosFluxoCtx = document.getElementById('ProdutosMaiorFluxoChart').getContext('2d');
            
            // Calcular margem de lucro para cada produto
            const margensLucro = produtosFluxoData.valores_venda.map((venda, index) => {
                const compra = produtosFluxoData.valores_compra[index] || 0;
                return venda - compra;
            });
        
            // Calcular percentual de margem para tooltip
            const percentuaisMargem = produtosFluxoData.valores_venda.map((venda, index) => {
                const compra = produtosFluxoData.valores_compra[index] || 0;
                return compra > 0 ? ((venda - compra) / compra * 100).toFixed(2) : '∞';
            });
            
            // Destruir gráfico anterior se existir
            if (produtosMaiorFluxoChart) {
                produtosMaiorFluxoChart.destroy();
            }
            
            // Verificar tamanho da tela para ajustes específicos
            const isMobile = window.innerWidth <= 768;
            const isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
            
            produtosMaiorFluxoChart = new Chart(produtosFluxoCtx, {
                type: 'bar',
                data: {
                    labels: produtosFluxoData.produtos,
                    datasets: [
                        {
                            label: 'Valor de Venda (R$)',
                            data: produtosFluxoData.valores_venda,
                            backgroundColor: 'rgba(76, 175, 80, 0.8)',
                            borderColor: 'rgb(76, 175, 80)',
                            borderWidth: 1,
                            order: 1,
                            barPercentage: isMobile ? 0.4 : 0.7,
                            categoryPercentage: isMobile ? 0.6 : 0.8,
                            borderRadius: 4,
                            hoverBackgroundColor: 'rgba(76, 175, 80, 1)'
                        },
                        {
                            label: 'Valor de Compra (R$)',
                            data: produtosFluxoData.valores_compra,
                            backgroundColor: 'rgba(244, 67, 54, 0.8)',
                            borderColor: 'rgb(244, 67, 54)',
                            borderWidth: 1,
                            order: 2,
                            barPercentage: isMobile ? 0.4 : 0.7,
                            categoryPercentage: isMobile ? 0.6 : 0.8,
                            borderRadius: 4,
                            hoverBackgroundColor: 'rgba(244, 67, 54, 1)'
                        },
                        {
                            label: 'Margem de Lucro (R$)',
                            data: margensLucro,
                            backgroundColor: 'rgba(33, 150, 243, 0.9)',
                            borderColor: 'rgb(33, 150, 243)',
                            borderWidth: 3,
                            type: 'line',
                            order: 0,
                            pointStyle: 'circle',
                            pointRadius: isMobile ? 3 : 6,
                            pointHoverRadius: isMobile ? 5 : 8,
                            pointBackgroundColor: 'rgb(33, 150, 243)',
                            pointBorderColor: '#ffffff',
                            pointBorderWidth: 2,
                            tension: 0.3,
                            fill: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                        padding: {
                            top: 20,
                            right: isMobile ? 10 : 20,
                            bottom: isMobile ? 15 : 25,
                            left: isMobile ? 10 : 20
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: '#e0e0e0',
                                boxWidth: 16,
                                padding: 20,
                                font: {
                                    size: isMobile ? 10 : 14,
                                    weight: '500'
                                },
                                usePointStyle: true,
                                pointStyle: 'rectRounded'
                            }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'rgba(30, 30, 46, 0.95)',
                            titleColor: '#ffffff',
                            bodyColor: '#e0e0e0',
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            borderWidth: 1,
                            cornerRadius: 6,
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${formatMoney(context.raw)}`;
                                },
                                afterLabel: function(context) {
                                    if (context.dataset.label === 'Margem de Lucro (R$)') {
                                        return `Margem Percentual: ${percentuaisMargem[context.dataIndex]}%`;
                                    }
                                    return null;
                                }
                            },
                            titleFont: {
                                size: isMobile ? 12 : 14,
                                weight: 'bold'
                            },
                            bodyFont: {
                                size: isMobile ? 11 : 13
                            },
                            padding: 12,
                            boxWidth: 12,
                            boxHeight: 12,
                            displayColors: true
                        },
                        title: {
                            display: true,
                            text: 'Top 10 Produtos - Maior Fluxo (Últimos 30 Dias)',
                            color: '#e0e0e0',
                            font: {
                                size: isMobile ? 14 : 18,
                                weight: '600'
                            },
                            padding: {
                                top: 5,
                                bottom: isMobile ? 15 : 25
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)',
                                drawBorder: false
                            },
                            ticks: {
                                callback: function(value) {
                                    return formatMoney(value);
                                },
                                color: '#e0e0e0',
                                font: {
                                    size: isMobile ? 10 : 12
                                },
                                maxTicksLimit: isMobile ? 5 : 7,
                                padding: 10
                            },
                            title: {
                                display: true,
                                text: 'Valores em Reais (R$)',
                                color: '#e0e0e0',
                                font: {
                                    size: isMobile ? 11 : 13,
                                    weight: '500'
                                },
                                padding: {
                                    top: 10,
                                    bottom: 10
                                }
                            }
                        },
                        x: {
                            grid: {
                                display: false,
                                drawBorder: false
                            },
                            ticks: {
                                color: '#e0e0e0',
                                maxRotation: isMobile ? 60 : 45,
                                minRotation: isMobile ? 60 : 45,
                                font: {
                                    size: isMobile ? 10 : 12
                                },
                                padding: 8,
                                callback: function(value, index) {
                                    const label = this.getLabelForValue(value);
                                    if (isMobile && label.length > 12) {
                                        return label.substring(0, 10) + '...';
                                    }
                                    return label;
                                }
                            }
                        }
                    },
                    interaction: {
                        mode: 'index',
                        intersect: false
                    },
                    animation: {
                        duration: 800,
                        easing: 'easeOutQuart'
                    }
                }
            });
            
            // Adicionar event listener para redimensionamento da janela - CORRIGIDO
            let resizeTimeout;
            window.addEventListener('resize', function() {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(function() {
                    // Apenas atualizar o gráfico existente, não recriar
                    if (produtosMaiorFluxoChart) {
                        produtosMaiorFluxoChart.resize();
                        produtosMaiorFluxoChart.update();
                    }
                }, 250);
            });
        }
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
                  <button class="btn-icon btn-info detalhes-cliente" data-id="${cliente.id}" title="Detalhes">
                    <i class="fas fa-eye"></i>
                  </button>
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
  async function openDetalhesClienteModal(clienteId) {
      const content = document.getElementById('detalhesClienteContent');
      if (content) content.innerHTML = '<p class="loading-text">Carregando dados...</p>';

      try {
          const response = await fetchWithErrorHandling(`/admin/clientes/${clienteId}/detalhes`);
          if (!response.success) {
              showFlashMessage('error', response.message || 'Erro ao carregar detalhes');
              return;
          }

          const c = response.cliente;

          // HTML com seções retráteis
          let html = `
              <div class="details-main-info">
                  <h3 class="section-title">Informações do Cliente</h3>
                  <div class="details-grid">
                      <div class="detail-item">
                          <label>Nome:</label>
                          <div class="value">${c.nome || '-'}</div>
                      </div>
                      <div class="detail-item">
                          <label>Documento:</label>
                          <div class="value">${c.documento || '-'}</div>
                      </div>
                      <div class="detail-item">
                          <label>Telefone:</label>
                          <div class="value">${c.telefone || '-'}</div>
                      </div>
                      <div class="detail-item">
                          <label>Email:</label>
                          <div class="value">${c.email || '-'}</div>
                      </div>
                      <div class="detail-item full-width">
                          <label>Endereço:</label>
                          <div class="value">${c.endereco || '-'}</div>
                      </div>
                      <div class="detail-item">
                          <label>Total de Compras:</label>
                          <div class="value">${response.total_compras}</div>
                      </div>
                      <div class="detail-item">
                          <label>Valor Total:</label>
                          <div class="value monetary">R$ ${response.valor_total_compras.toFixed(2)}</div>
                      </div>
                  </div>
              </div>

              <!-- Produtos Comprados -->
              <div class="collapsible-section">
                  <button class="collapsible btn btn-outline">
                      <i class="fas fa-shopping-bag"></i> Produtos Comprados (${response.produtos_comprados.length})
                      <i class="fas fa-chevron-down toggle-icon"></i>
                  </button>
                  <div class="collapsible-content" style="display:none;">
                      <div class="details-table-container">
                          <table class="table compact-table">
                              <thead>
                                  <tr>
                                      <th>Produto</th><th>Qtd</th><th>Un</th><th>Valor Unit.</th><th>Valor Total</th><th>Data</th>
                                  </tr>
                              </thead>
                              <tbody>
                                  ${response.produtos_comprados.map(p => `
                                      <tr>
                                          <td>${p.nome}</td>
                                          <td>${p.quantidade}</td>
                                          <td>${p.unidade}</td>
                                          <td class="monetary">R$ ${p.valor_unitario.toFixed(2)}</td>
                                          <td class="monetary">R$ ${p.valor_total.toFixed(2)}</td>
                                          <td>${new Date(p.data_compra).toLocaleDateString()}</td>
                                      </tr>
                                  `).join('')}
                              </tbody>
                          </table>
                      </div>
                  </div>
              </div>

              <!-- Top Produtos Mais Comprados -->
              <div class="collapsible-section">
                  <button class="collapsible btn btn-outline">
                      <i class="fas fa-trophy"></i> Top Produtos Mais Comprados (${response.produtos_mais_comprados.length})
                      <i class="fas fa-chevron-down toggle-icon"></i>
                  </button>
                  <div class="collapsible-content" style="display:none;">
                      <div class="details-table-container">
                          <table class="table compact-table">
                              <thead>
                                  <tr>
                                      <th>Produto</th><th>Quantidade Total</th><th>Unidade</th><th>Vezes Comprado</th>
                                  </tr>
                              </thead>
                              <tbody>
                                  ${response.produtos_mais_comprados.map(p => `
                                      <tr>
                                          <td>${p.nome}</td>
                                          <td>${p.quantidade_total}</td>
                                          <td>${p.unidade}</td>
                                          <td>${p.vezes_comprado}x</td>
                                      </tr>
                                  `).join('')}
                              </tbody>
                          </table>
                      </div>
                  </div>
              </div>

              <!-- Contas em Aberto -->
              <div class="collapsible-section">
                  <button class="collapsible btn btn-outline">
                      <i class="fas fa-clock"></i> Contas em Aberto (${response.contas_abertas.length})
                      <i class="fas fa-chevron-down toggle-icon"></i>
                  </button>
                  <div class="collapsible-content" style="display:none;">
                      ${response.contas_abertas.length ? `
                          <div class="details-table-container">
                              <table class="table compact-table">
                                  <thead>
                                      <tr>
                                          <th>Descrição</th><th>Vencimento</th><th>Valor em Aberto</th>
                                      </tr>
                                  </thead>
                                  <tbody>
                                      ${response.contas_abertas.map(ca => `
                                          <tr>
                                              <td>${ca.descricao}</td>
                                              <td>${new Date(ca.data_vencimento).toLocaleDateString()}</td>
                                              <td class="monetary">R$ ${ca.valor_aberto.toFixed(2)}</td>
                                          </tr>
                                      `).join('')}
                                  </tbody>
                              </table>
                          </div>
                      ` : '<p class="no-data-message">Nenhuma conta em aberto</p>'}
                  </div>
              </div>

              <!-- Contas Quitadas -->
              <div class="collapsible-section">
                  <button class="collapsible btn btn-outline">
                      <i class="fas fa-check-circle"></i> Contas Quitadas (${response.contas_quitadas.length})
                      <i class="fas fa-chevron-down toggle-icon"></i>
                  </button>
                  <div class="collapsible-content" style="display:none;">
                      ${response.contas_quitadas.length ? `
                          <div class="details-table-container">
                              <table class="table compact-table">
                                  <thead>
                                      <tr>
                                          <th>Descrição</th><th>Data de Pagamento</th><th>Valor Original</th>
                                      </tr>
                                  </thead>
                                  <tbody>
                                      ${response.contas_quitadas.map(cq => `
                                          <tr>
                                              <td>${cq.descricao}</td>
                                              <td>${new Date(cq.data_pagamento || cq.data_vencimento).toLocaleDateString()}</td>
                                              <td class="monetary">R$ ${cq.valor_original.toFixed(2)}</td>
                                          </tr>
                                      `).join('')}
                                  </tbody>
                              </table>
                          </div>
                      ` : '<p class="no-data-message">Nenhuma conta quitada</p>'}
                  </div>
              </div>
          `;

          content.innerHTML = html;

          // Ativar colapsáveis
          document.querySelectorAll('.collapsible').forEach(btn => {
              btn.addEventListener('click', function() {
                  this.classList.toggle('active');
                  const contentDiv = this.nextElementSibling;
                  const toggleIcon = this.querySelector('.toggle-icon');
                  
                  if (contentDiv.style.display === 'block') {
                      contentDiv.style.display = 'none';
                      toggleIcon.classList.remove('rotated');
                  } else {
                      contentDiv.style.display = 'block';
                      toggleIcon.classList.add('rotated');
                  }
              });
          });

          openModal('detalhesClienteModal');

      } catch (err) {
          console.error(err);
          showFlashMessage('error', 'Erro ao carregar detalhes do cliente');
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

    openModal(document.getElementById('clienteModal'));

  }

  function setupClienteActions() {
    document.querySelectorAll('.detalhes-cliente').forEach(btn => {
      btn.addEventListener('click', function() {
        const clienteId = this.getAttribute('data-id');
        openDetalhesClienteModal(clienteId);
      });
    });

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
        const incluirInativos = document.getElementById('mostrarInativos')?.checked ? 'true' : 'false';
        
        const data = await fetchWithErrorHandling(`/admin/produtos?incluir_inativos=${incluirInativos}`);
        
        if (data.success) {
          const produtosTable = document.querySelector('#produtosTable tbody');
          if (produtosTable) {
            produtosTable.innerHTML = '';
            
            data.produtos.forEach(produto => {
              if (searchText && !produto.nome.toLowerCase().includes(searchText)) return;
              
              const row = document.createElement('tr');
              // Adicione classe e atributo data-id para identificar a linha
              row.className = 'produto-row clickable-row';
              row.setAttribute('data-id', produto.id);
              row.setAttribute('data-produto', JSON.stringify(produto));
              
              row.innerHTML = `
                <td>${produto.codigo}</td>
                <td>${produto.nome} ${!produto.ativo ? '<span class="badge badge-danger">Inativo</span>' : ''}</td>
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
            setupRowClickEvents(); // Nova função para configurar clicks nas linhas
          }
        }
      } catch (error) {
        console.error('Erro ao carregar produtos:', error);
        showFlashMessage('error', 'Erro ao carregar lista de produtos');
      }
    }
  
  // recarregar lista ao clicar no refresh ou trocar checkbox
  document.getElementById('mostrarInativos').addEventListener('change', loadProdutosData);

  function setupRowClickEvents() {
  document.querySelectorAll('.produto-row.clickable-row').forEach(row => {
    row.addEventListener('click', function(e) {
      // Previne a abertura do modal se o clique foi em um botão de ação
      if (e.target.closest('.table-actions') || 
          e.target.tagName === 'BUTTON' || 
          e.target.closest('button')) {
        return;
      }
      
      const produtoId = this.getAttribute('data-id');
      openEditarProdutoModal(produtoId);
    });
  });
  }

  function setupProdutoActions() {
    // Previne a propagação do evento de clique para a linha quando clicar nos botões
    document.querySelectorAll('.table-actions button').forEach(btn => {
      btn.addEventListener('click', function(e) {
        e.stopPropagation(); // Impede que o evento chegue à linha
      });
    });

    document.querySelectorAll('.editar-produto').forEach(btn => {
      btn.addEventListener('click', async function(e) {
        const produtoId = this.getAttribute('data-id');
        await openEditarProdutoModal(produtoId);
      });
    });

    document.querySelectorAll('.remover-produto').forEach(btn => {
      btn.addEventListener('click', function(e) {
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
      btn.addEventListener('click', function(e) {
        const produtoId = this.getAttribute('data-id');
        openTransferenciaModal(produtoId);
      });
    });
    document.getElementById('btnRelatorioProdutos').addEventListener('click', () => {
      const searchText = document.getElementById('searchProduto')?.value || '';
      const incluirInativos = document.getElementById('mostrarInativos')?.checked ? 'true' : 'false';
      
      const url = `/admin/produtos/pdf?search=${encodeURIComponent(searchText)}&incluir_inativos=${incluirInativos}`;
      window.open(url, '_blank');
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

  // Função para abrir o modal de transferência
  async function openTransferenciaModal(produtoId) {
      try {
          const response = await fetchWithErrorHandling(`/admin/produtos/${produtoId}`);
          if (response.success) {
              const produto = response.produto;
              
              // Preencher campos básicos
              document.getElementById('transferenciaProdutoId').value = produtoId;
              document.getElementById('transferenciaProdutoNome').textContent = produto.nome;
              document.getElementById('transferenciaUnidadeAtual').textContent = produto.unidade;
              document.getElementById('transferenciaValorUnitarioDestino').value = produto.valor_unitario;
              
              // Resetar campos de conversão
              document.getElementById('transferenciaConverter').checked = false;
              document.getElementById('camposConversao').style.display = 'none';
              document.getElementById('transferenciaUnidadeDestino').value = '';
              document.getElementById('transferenciaQuantidadeDestino').value = '';
              document.getElementById('transferenciaFatorConversao').value = '';
              
              // Atualizar estoque disponível
              updateEstoqueDisponivel();
              
              openModal('transferenciaModal');
          }
      } catch (error) {
          console.error('Erro ao abrir modal de transferência:', error);
          showFlashMessage('error', 'Erro ao carregar dados do produto');
      }
  }

  // Alternar visibilidade dos campos de conversão
  document.getElementById('transferenciaConverter').addEventListener('change', function() {
      const camposConversao = document.getElementById('camposConversao');
      camposConversao.style.display = this.checked ? 'block' : 'none';
      
      if (this.checked) {
          // Preencher informações de unidade
          const unidadeOrigem = document.getElementById('transferenciaUnidadeAtual').textContent;
          document.getElementById('unidadeOrigemTexto').textContent = unidadeOrigem;
      }
  });

  // Atualizar informações quando selecionar unidade de destino
  document.getElementById('transferenciaUnidadeDestino').addEventListener('change', function() {
      const unidadeDestino = this.value;
      document.getElementById('unidadeDestinoTexto').textContent = unidadeDestino;
      calcularConversao();
  });

  // Calcular conversão quando alterar quantidade ou fator
  document.getElementById('transferenciaQuantidade').addEventListener('input', calcularConversao);
  document.getElementById('transferenciaFatorConversao').addEventListener('input', calcularConversao);

  // Função para calcular a conversão
  function calcularConversao() {
      const produtoId = document.getElementById('transferenciaProdutoId').value;
      const quantidadeOrigem = parseFloat(document.getElementById('transferenciaQuantidade').value) || 0;
      const unidadeOrigem = document.getElementById('transferenciaUnidadeAtual').textContent;
      const unidadeDestino = document.getElementById('transferenciaUnidadeDestino').value;
      const fatorPersonalizado = parseFloat(document.getElementById('transferenciaFatorConversao').value);
      
      if (!unidadeDestino || quantidadeOrigem <= 0) return;
      
      // Buscar informações do produto para obter fatores de conversão padrão
      fetchWithErrorHandling(`/admin/produtos/${produtoId}`)
          .then(response => {
              if (response.success) {
                  const produto = response.produto;
                  let fatorConversao = 1;
                  
                  // Calcular fator de conversão
                  if (fatorPersonalizado && fatorPersonalizado > 0) {
                      fatorConversao = fatorPersonalizado;
                  } else {
                      // Usar fatores padrão do produto
                      fatorConversao = calcularFatorPadrao(produto, unidadeOrigem, unidadeDestino);
                  }
                  
                  // Calcular quantidade de destino
                  const quantidadeDestino = quantidadeOrigem * fatorConversao;
                  document.getElementById('transferenciaQuantidadeDestino').value = quantidadeDestino.toFixed(3);
                  
                  // Exibir informações da conversão
                  document.getElementById('infoConversao').textContent = 
                      `1 ${unidadeOrigem} = ${fatorConversao} ${unidadeDestino}`;
              }
          })
          .catch(error => {
              console.error('Erro ao calcular conversão:', error);
          });
  }

  // Função para calcular fator de conversão padrão baseado nas propriedades do produto
  function calcularFatorPadrao(produto, unidadeOrigem, unidadeDestino) {
      // Se for a mesma unidade, fator é 1
      if (unidadeOrigem === unidadeDestino) return 1;
      
      // Converter para kg primeiro, depois para a unidade de destino
      let quantidadeEmKg = 0;
      
      // Converter unidade de origem para kg
      switch(unidadeOrigem) {
          case 'kg':
              quantidadeEmKg = 1;
              break;
          case 'saco':
              quantidadeEmKg = produto.peso_kg_por_saco || 50; // Valor padrão 50kg se não definido
              break;
          case 'pacote':
              // Primeiro converter saco para kg, depois dividir por pacotes por saco
              const kgPorSaco = produto.peso_kg_por_saco || 50;
              quantidadeEmKg = kgPorSaco / (produto.pacotes_por_saco || 10);
              break;
          case 'fardo':
              // Primeiro converter saco para kg, depois dividir por pacotes por fardo e por pacotes por saco
              const kgPorSacoFardo = produto.peso_kg_por_saco || 50;
              const pacotesPorFardo = produto.pacotes_por_fardo || 5;
              quantidadeEmKg = kgPorSacoFardo / (produto.pacotes_por_saco || 10) / pacotesPorFardo;
              break;
          case 'unidade':
              // Para unidade, assumimos 1kg por unidade (ajustar conforme necessário)
              quantidadeEmKg = 1;
              break;
      }
      
      // Converter de kg para unidade de destino
      switch(unidadeDestino) {
          case 'kg':
              return 1 / quantidadeEmKg;
          case 'saco':
              return 1 / (quantidadeEmKg * (produto.peso_kg_por_saco || 50));
          case 'pacote':
              const kgPorSacoPacote = produto.peso_kg_por_saco || 50;
              const pacotesPorSaco = produto.pacotes_por_saco || 10;
              return 1 / (quantidadeEmKg * kgPorSacoPacote / pacotesPorSaco);
          case 'fardo':
              const kgPorSacoFardo = produto.peso_kg_por_saco || 50;
              const pacotesPorSacoFardo = produto.pacotes_por_saco || 10;
              const pacotesPorFardo = produto.pacotes_por_fardo || 5;
              return 1 / (quantidadeEmKg * kgPorSacoFardo / pacotesPorSacoFardo / pacotesPorFardo);
          case 'unidade':
              return 1 / quantidadeEmKg; // Assumindo 1kg por unidade
      }
      
      return 1; // Fallback
  }

  // Enviar formulário de transferência
  document.getElementById('transferenciaForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const produtoId = document.getElementById('transferenciaProdutoId').value;
      const converterUnidade = document.getElementById('transferenciaConverter').checked;
      const dados = {
          produto_id: produtoId,
          estoque_origem: document.getElementById('transferenciaOrigem').value,
          estoque_destino: document.getElementById('transferenciaDestino').value,
          quantidade: parseFloat(document.getElementById('transferenciaQuantidade').value),
          valor_unitario_destino: parseFloat(document.getElementById('transferenciaValorUnitarioDestino').value),
          observacao: document.getElementById('transferenciaObservacao').value,
          converter_unidade: converterUnidade
      };
      
      // Adicionar dados de conversão se aplicável
      if (converterUnidade) {
          dados.unidade_destino = document.getElementById('transferenciaUnidadeDestino').value;
          dados.quantidade_destino = parseFloat(document.getElementById('transferenciaQuantidadeDestino').value);
          dados.fator_conversao = parseFloat(document.getElementById('transferenciaFatorConversao').value) || null;
      }
      
      try {
          const response = await fetchWithErrorHandling('/admin/transferencias', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify(dados)
          });
          
          if (response.success) {
              showFlashMessage('success', response.message);
              closeModal('transferenciaModal');
              // Recarregar dados da página se necessário
              if (typeof carregarDados === 'function') {
                  carregarDados();
              }
          } else {
              showFlashMessage('error', response.message);
          }
      } catch (error) {
          console.error('Erro ao realizar transferência:', error);
          showFlashMessage('error', 'Erro ao realizar transferência');
      }
  });

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
  document.addEventListener('DOMContentLoaded', function() {
      // Registrar eventos após o DOM estar totalmente carregado
      const refreshButton = document.getElementById('refreshProdutos');
      if (refreshButton) {
          refreshButton.addEventListener('click', function(e) {
              e.preventDefault();
              console.log('Botão refresh clicado!'); // Debug
              loadProdutosData();
          });
      }
  });
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
  
  document.getElementById("btnEntradaEstoque").addEventListener("click", () => {
    openModal("entradaEstoqueModal");
  });

  document.getElementById("entradaEstoqueForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const produtoId = document.getElementById("editarProdutoForm").getAttribute("data-produto-id");

    const payload = {
      estoque_loja: document.getElementById("entradaLoja").value || 0,
      estoque_deposito: document.getElementById("entradaDeposito").value || 0,
      estoque_fabrica: document.getElementById("entradaFabrica").value || 0,
      valor_unitario_compra: document.getElementById("entradaValorCompra").value || null,
      valor_unitario: document.getElementById("editValor").value, // fallback
    };

    try {
      const response = await fetch(`/admin/produtos/${produtoId}/entrada-estoque`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();

      if (result.success) {
        showFlashMessage("success", result.message);
        closeModal("entradaEstoqueModal");
        // Atualiza modal de edição para refletir novos estoques
        await openEditarProdutoModal(produtoId);
      } else {
        showFlashMessage("error", result.message);
      }
    } catch (err) {
      console.error(err);
      showFlashMessage("error", "Erro ao registrar entrada de estoque");
    }
  });

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
        'pix_edfrance': 'PIX Edfranci',
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

  // Funções auxiliares para formatação
  function formatarData(dataString) {
      if (!dataString) return '-';
      const date = new Date(dataString);
      return date.toLocaleDateString('pt-BR');
  }

  // Funções auxiliares para formatação
  function formatarStatus(status) {
      const statusMap = {
          'pendente': 'Pendente',
          'atrasado': 'Atrasado',
          'quitado': 'Quitado',
          'paid': 'Quitado',       // Para compatibilidade
          'pending': 'Pendente',   // Para compatibilidade
          'overdue': 'Atrasado'    // Para compatibilidade
      };
      return statusMap[status.toLowerCase()] || status;
  }

  function getStatusBadgeClass(status) {
      const normalizedStatus = status.toLowerCase();
      const classMap = {
          'pendente': 'badge-warning',
          'pending': 'badge-warning',
          'atrasado': 'badge-danger',
          'overdue': 'badge-danger',
          'quitado': 'badge-success',
          'paid': 'badge-success'
      };
      return classMap[normalizedStatus] || 'badge-secondary';
  }

  // Configurar datas padrão (30 dias atrás até hoje)
  function setupContasReceberDates() {
      const hoje = new Date();
      const trintaDiasAtras = new Date();
      trintaDiasAtras.setDate(hoje.getDate() - 30);
      
      document.getElementById('contasReceberDataFim').valueAsDate = hoje;
      document.getElementById('contasReceberDataInicio').valueAsDate = trintaDiasAtras;
  }

  // Event Listeners
  document.addEventListener('DOMContentLoaded', function() {
      if (document.getElementById('contas-receber')) {
          setupContasReceberDates();
          loadContasReceber();
      }
  });

  document.getElementById('filtrarContasReceber')?.addEventListener('click', loadContasReceber);

  // Event listener para abrir modal de detalhes
  document.addEventListener('click', function(e) {
      if (e.target.closest('.btn-detalhes-conta')) {
          const contaId = e.target.closest('.btn-detalhes-conta').getAttribute('data-id');
          abrirModalDetalhesConta(contaId);
      }
  });

  // Função para abrir modal de detalhes da conta
  async function abrirModalDetalhesConta(contaId) {
      try {
          // Fazer a requisição para obter os detalhes da conta
          const response = await fetchWithErrorHandling(`/admin/contas-receber/${contaId}/detalhes`);
          
          if (response) {
              // 1. Preencher informações básicas da conta
              document.getElementById('detalheClienteNome').textContent = response.cliente || '-';
              document.getElementById('detalheClienteDocumento').textContent = response.cliente_documento || '-';
              document.getElementById('detalheDescricao').textContent = response.descricao || '-';
              document.getElementById('detalheValorTotal').textContent = formatarMoeda(response.valor_original);
              document.getElementById('detalheValorPendente').textContent = formatarMoeda(response.valor_aberto);
              
              // 2. Determinar o status para exibição
              const hoje = new Date();
              const dataVencimento = new Date(response.data_vencimento.split('/').reverse().join('-'));
              let statusExibicao = response.status.toLowerCase();
              
              // Se não estiver quitado, verificar se está atrasado
              if (statusExibicao !== 'quitado') {
                  statusExibicao = dataVencimento >= hoje ? 'pendente' : 'atrasado';
              }
              
              // Atualizar o elemento de status no modal
              const statusElement = document.getElementById('detalheStatus');
              statusElement.textContent = formatarStatus(statusExibicao);
              statusElement.className = 'value badge ' + getStatusBadgeClass(statusExibicao);
              
              // 3. Preencher a lista de pagamentos realizados
              const pagamentosTbody = document.getElementById('detalhePagamentos');
              pagamentosTbody.innerHTML = '';
              
              if (response.pagamentos && response.pagamentos.length > 0) {
                  response.pagamentos.forEach(pagamento => {
                      const tr = document.createElement('tr');
                      tr.innerHTML = `
                          <td>${pagamento.data_pagamento}</td>
                          <td>${formatarMoeda(pagamento.valor_pago)}</td>
                          <td>${formatarFormaPagamento(pagamento.forma_pagamento)}</td>
                          <td>${pagamento.observacoes || '-'}</td>
                      `;
                      pagamentosTbody.appendChild(tr);
                  });
              } else {
                  pagamentosTbody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhum pagamento registrado</td></tr>';
              }
              
              // 4. Preencher o select de caixas disponíveis
              const caixaSelect = document.getElementById('caixaPagamento');
              caixaSelect.innerHTML = '<option value="">Selecione</option>';
              
              if (response.caixas && response.caixas.length > 0) {
                  response.caixas.forEach(caixa => {
                      const option = document.createElement('option');
                      option.value = caixa.id;
                      
                      // Formatando a data de abertura para exibição
                      const dataAbertura = caixa.data_abertura.split('-').reverse().join('/');
                      option.textContent = `${dataAbertura} - ${caixa.operador} (${caixa.status})`;
                      
                      // Selecionar automaticamente o caixa aberto do usuário atual, se existir
                      if (caixa.status.toLowerCase() === 'aberto') {
                          option.selected = true;
                      }
                      
                      caixaSelect.appendChild(option);
                  });
              }
              
              // 5. Configurar o formulário de pagamento
              document.getElementById('contaIdPagamento').value = contaId;
              
              // Definir data atual como padrão para pagamento
              const hojeISO = new Date().toISOString().split('T')[0];
              document.getElementById('dataPagamento').value = hojeISO;
              
              // Limpar campos do formulário
              document.getElementById('valorPagamento').value = '';
              document.getElementById('observacaoPagamento').value = '';
              
              // 6. Habilitar/desabilitar botões conforme o status
              const btnPagarTotal = document.getElementById('btnPagarTotal');
              if (response.valor_aberto <= 0 || statusExibicao === 'quitado') {
                  btnPagarTotal.disabled = true;
                  btnPagarTotal.classList.add('disabled');
              } else {
                  btnPagarTotal.disabled = false;
                  btnPagarTotal.classList.remove('disabled');
              }
              
              // 7. Abrir o modal
              openModal('detalhesContaModal');
          }
      } catch (error) {
          console.error('Erro ao abrir detalhes da conta:', error);
          showFlashMessage('error', 'Erro ao carregar detalhes da conta');
      }
  }

  // Event listeners para os botões de pagamento
  document.getElementById('formPagamentoConta')?.addEventListener('submit', function(e) {
      e.preventDefault();
      const contaId = document.getElementById('contaIdPagamento').value;
      const valor = parseFloat(document.getElementById('valorPagamento').value);
      
      if (contaId && valor) {
          registrarPagamento(contaId, valor);
      }
  });

  document.getElementById('btnPagarTotal')?.addEventListener('click', function() {
      const contaId = document.getElementById('contaIdPagamento').value;
      const valorPendenteText = document.getElementById('detalheValorPendente').textContent;
      const valorPendente = parseFloat(valorPendenteText.replace(/[^\d,]/g, '').replace(',', '.'));
      
      if (contaId && valorPendente > 0) {
          // Preencher o valor total no campo
          document.getElementById('valorPagamento').value = valorPendente.toFixed(2);
          
          // Registrar o pagamento
          registrarPagamento(contaId, valorPendente, true);
      }
  });

  // Função para atualizar a lista de pagamentos
  async function atualizarListaPagamentos(contaId) {
      try {
          const response = await fetchWithErrorHandling(`/admin/contas-receber/${contaId}/detalhes`);
          
          if (response && response.pagamentos) {
              const pagamentosTbody = document.getElementById('detalhePagamentos');
              pagamentosTbody.innerHTML = '';
              
              if (response.pagamentos.length > 0) {
                  response.pagamentos.forEach(pagamento => {
                      const tr = document.createElement('tr');
                      tr.innerHTML = `
                          <td>${pagamento.data_pagamento}</td>
                          <td>${formatarMoeda(pagamento.valor_pago)}</td>
                          <td>${pagamento.forma_pagamento}</td>
                          <td>${pagamento.observacoes || '-'}</td>
                      `;
                      pagamentosTbody.appendChild(tr);
                  });
              } else {
                  pagamentosTbody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhum pagamento registrado</td></tr>';
              }
          }
      } catch (error) {
          console.error('Erro ao atualizar lista de pagamentos:', error);
      }
  }
  async function loadRelatorioSaidasData() {
      try {
          // Mostrar loading
          const tbody = document.querySelector('#tabelaRelatorio tbody');
          tbody.innerHTML = '<tr><td colspan="9" class="text-center"><div class="spinner-border" role="status"><span class="sr-only">Carregando...</span></div></td></tr>';
          
          // Obter valores dos filtros
          const dataInicio = document.getElementById('relatorioDataInicio').value;
          const dataFim = document.getElementById('relatorioDataFim').value;
          const produtoNome = document.getElementById('relatorioProdutoNome').value;
          const produtoCodigo = document.getElementById('relatorioProdutoCodigo').value;
          
          // Construir parâmetros da URL
          const params = new URLSearchParams();
          if (dataInicio) params.append('data_inicio', dataInicio);
          if (dataFim) params.append('data_fim', dataFim);
          if (produtoNome) params.append('produto_nome', produtoNome);
          if (produtoCodigo) params.append('produto_codigo', produtoCodigo);
          
          // Limite padrão de 50 itens
          params.append('limite', 50);
          
          // Fazer a requisição
          const response = await fetchWithErrorHandling(`/admin/relatorios/vendas-produtos?${params.toString()}`);
          
          if (response) {
              // Atualizar metadados
              atualizarMetadadosRelatorio(response.meta);
              
              // Preencher tabela
              preencherTabelaRelatorio(response.dados);
          }
      } catch (error) {
          console.error('Erro ao carregar relatório:', error);
          const tbody = document.querySelector('#tabelaRelatorio tbody');
          tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">Erro ao carregar dados do relatório</td></tr>';
          showFlashMessage('error', 'Erro ao carregar relatório de saídas');
      }
  }

  function atualizarMetadadosRelatorio(meta) {
      if (!meta) return;
      
      // Formatar período - CORREÇÃO: Usar UTC para evitar problemas de fuso horário
      const inicio = new Date(meta.data_inicio + 'T00:00:00Z'); // Adiciona horário e UTC
      const fim = new Date(meta.data_fim + 'T23:59:59Z'); // Adiciona horário e UTC
      
      // Ajusta para o fuso horário local apenas para exibição
      const inicioLocal = new Date(inicio.getTime() + inicio.getTimezoneOffset() * 60000);
      const fimLocal = new Date(fim.getTime() + fim.getTimezoneOffset() * 60000);
      
      document.getElementById('relatorioPeriodoTexto').innerHTML = 
          `${inicioLocal.toLocaleDateString('pt-BR')}<br>${fimLocal.toLocaleDateString('pt-BR')}`;
            
      // Atualizar totais
      document.getElementById('relatorioTotalProdutos').textContent = meta.total_produtos;
      document.getElementById('relatorioTotalQuantidade').textContent = meta.total_quantidade_vendida;
      document.getElementById('relatorioTotalValor').textContent = formatarMoeda(meta.total_valor_vendido);
      document.getElementById('relatorioEstoqueCritico').textContent = meta.produtos_estoque_critico;
      document.getElementById('relatorioCustoTotal').textContent = formatCurrency(meta.total_custo);
      document.getElementById('relatorioLucroBruto').textContent = formatCurrency(meta.lucro_bruto);
      document.getElementById('relatorioLucroLiquido').textContent = formatCurrency(meta.lucro_liquido);
  }

  function preencherTabelaRelatorio(dados) {
      const tbody = document.querySelector('#tabelaRelatorio tbody');
      
      if (!dados || dados.length === 0) {
          tbody.innerHTML = '<tr><td colspan="10" class="text-center">Nenhum dado encontrado para os filtros selecionados</td></tr>';
          return;
      }
      
      tbody.innerHTML = '';
      
      dados.forEach(item => {
          const tr = document.createElement('tr');
          
          if (item.status_estoque === 'CRÍTICO') {
              tr.classList.add('table-warning');
          }
          
          tr.innerHTML = `
              <td>${item.produto_id}</td>
              <td>
                  <strong>${item.produto_nome}</strong><br>
                  <small class="text-muted">${item.produto_codigo || 'Sem código'}</small>
              </td>
              <td>${item.unidade}</td>
              <td>${item.quantidade_vendida.toFixed(2)}</td>
              <td>${formatarMoeda(item.valor_total_vendido)}</td>
              <td>
                  ${item.estoque_atual_loja.toFixed(2)}
                  <div class="progress mt-1" style="height: 5px;">
                      <div class="progress-bar ${item.percentual_estoque < 100 ? 'bg-danger' : 'bg-success'}" 
                          role="progressbar" 
                          style="width: ${Math.min(item.percentual_estoque, 100)}%" 
                          aria-valuenow="${item.percentual_estoque}" 
                          aria-valuemin="0" 
                          aria-valuemax="100">
                      </div>
                  </div>
              </td>
              <td>${item.estoque_minimo.toFixed(2)}</td>
              <td>
                  <span class="badge ${item.status_estoque === 'CRÍTICO' ? 'badge-danger' : 'badge-success'}">
                      ${item.status_estoque}
                  </span>
              </td>
              <td>${item.dias_restantes ? `${item.dias_restantes} dias` : 'N/A'}</td>
              <td class="text-center">
                  <button class="btn btn-sm btn-outline-primary btn-detalhes" 
                          data-produto-id="${item.produto_id}"
                          title="Ver detalhes">
                      <i class="fas fa-eye"></i>
                  </button>
              </td>
          `;
          
          tbody.appendChild(tr);
      });
      
      // Evento do botão de detalhes
      document.querySelectorAll('.btn-detalhes').forEach(btn => {
          btn.addEventListener('click', function() {
              const produtoId = this.getAttribute('data-produto-id');
              abrirModalDetalhesProduto(produtoId); // Chama a rota /detalhes
          });
      });
  }
  // Adicione esta função no seu arquivo JavaScript existente
  async function exportarRelatorioPDF() {
      try {
          // Obter valores dos filtros atuais
          const dataInicio = document.getElementById('relatorioDataInicio').value;
          const dataFim = document.getElementById('relatorioDataFim').value;
          const produtoNome = document.getElementById('relatorioProdutoNome').value;
          const produtoCodigo = document.getElementById('relatorioProdutoCodigo').value;
          
          // Construir parâmetros
          const params = new URLSearchParams();
          if (dataInicio) params.append('data_inicio', dataInicio);
          if (dataFim) params.append('data_fim', dataFim);
          if (produtoNome) params.append('produto_nome', produtoNome);
          if (produtoCodigo) params.append('produto_codigo', produtoCodigo);
          
          // Gerar PDF em nova guia
          window.open(`/admin/relatorios/vendas-produtos/pdf?${params.toString()}`, '_blank');
          
      } catch (error) {
          console.error('Erro ao gerar PDF:', error);
          showFlashMessage('error', 'Erro ao gerar relatório em PDF');
      }
  }

  // Adicione este event listener no DOMContentLoaded ou onde você configura os eventos
  document.getElementById('btnExportarPDF')?.addEventListener('click', exportarRelatorioPDF);
  async function abrirModalDetalhesProduto(produtoId) {
      try {
          // Obter valores dos filtros atuais
          const dataInicio = document.getElementById('relatorioDataInicio').value;
          const dataFim = document.getElementById('relatorioDataFim').value;
          
          // Construir parâmetros
          const params = new URLSearchParams();
          params.append('produto_id', produtoId);
          if (dataInicio) params.append('data_inicio', dataInicio);
          if (dataFim) params.append('data_fim', dataFim);
          
          // Mostrar modal de loading
          const modal = document.getElementById('detalhesSaidaModal');
          const modalBody = modal.querySelector('.modal-body');
          modalBody.innerHTML = '<div class="text-center p-4"><div class="spinner-border" role="status"><span class="sr-only">Carregando...</span></div></div>';
          openModal('detalhesSaidaModal');
          
          // Fazer requisição
          const response = await fetchWithErrorHandling(`/admin/relatorios/vendas-produtos/detalhes?${params.toString()}`);
          
          if (response && response.success) {
              const produto = response.produto;
              const historico = response.historico;
              
              // Preencher modal
              modalBody.innerHTML = `
                  <div class="detalhes-produto-header">
                      <h4>${produto.produto_nome}</h4>
                      <p class="text-muted">Código: ${produto.produto_codigo || 'N/A'} | Categoria: ${produto.produto_tipo || 'N/A'}</p>
                      <div class="row mb-3">
                          <div class="col-md-4">
                              <div class="card card-sm">
                                  <div class="card-body">
                                      <h6>Estoque Atual</h6>
                                      <h3 class="text-primary">${produto.estoque_atual_loja} ${produto.unidade}</h3>
                                  </div>
                              </div>
                          </div>
                          <div class="col-md-4">
                              <div class="card card-sm">
                                  <div class="card-body">
                                      <h6>Estoque Mínimo</h6>
                                      <h3 class="${produto.status_estoque === 'CRÍTICO' ? 'text-danger' : 'text-success'}">${produto.estoque_minimo} ${produto.unidade}</h3>
                                  </div>
                              </div>
                          </div>
                          <div class="col-md-4">
                              <div class="card card-sm">
                                  <div class="card-body">
                                      <h6>Dias Restantes</h6>
                                      <h3>${produto.dias_restantes || 'N/A'}</h3>
                                  </div>
                              </div>
                          </div>
                      </div>
                  </div>
                  
                  <div class="historico-vendas">
                      <h5>Histórico de Vendas</h5>
                      <div class="table-responsive">
                          <table class="table table-sm table-hover">
                              <thead>
                                  <tr>
                                      <th>Data</th>
                                      <th>Cliente</th>
                                      <th>Quantidade</th>
                                      <th>Valor Unitário</th>
                                      <th>Valor Total</th>
                                  </tr>
                              </thead>
                              <tbody>
                                  ${historico.map(item => `
                                      <tr>
                                          <td>${formatarData(item.data_emissao)}</td>
                                          <td>${item.cliente_nome || 'Consumidor'}</td>
                                          <td>${item.quantidade}</td>
                                          <td>${formatarMoeda(item.valor_unitario)}</td>
                                          <td>${formatarMoeda(item.valor_total)}</td>
                                      </tr>
                                  `).join('')}
                              </tbody>
                          </table>
                      </div>
                  </div>
              `;
          } else {
              modalBody.innerHTML = `<div class="alert alert-danger">${response.message || 'Erro ao carregar detalhes'}</div>`;
          }
      } catch (error) {
          console.error('Erro ao carregar detalhes:', error);
          const modalBody = document.querySelector('#modalDetalhesProduto .modal-body');
          modalBody.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
      }
  }

  function exportarRelatorioProduto(produtoId = null) {
      // Obter valores dos filtros
      const dataInicio = document.getElementById('relatorioDataInicio').value;
      const dataFim = document.getElementById('relatorioDataFim').value;
      const produtoNome = document.getElementById('relatorioProdutoNome').value;
      const produtoCodigo = document.getElementById('relatorioProdutoCodigo').value;
      const categoria = document.getElementById('relatorioCategoria').value;
      
      // Construir parâmetros
      const params = new URLSearchParams();
      if (produtoId) params.append('produto_id', produtoId);
      if (dataInicio) params.append('data_inicio', dataInicio);
      if (dataFim) params.append('data_fim', dataFim);
      if (produtoNome) params.append('produto_nome', produtoNome);
      if (produtoCodigo) params.append('produto_codigo', produtoCodigo);
      if (categoria) params.append('categoria', categoria);
      
      // Abrir link de download
      window.open(`/relatorios/vendas-produtos/exportar?${params.toString()}`, '_blank');
  }
  // Funções auxiliares
  function formatarMoeda(valor) {
      return new Intl.NumberFormat('pt-BR', { 
          style: 'currency', 
          currency: 'BRL' 
      }).format(valor || 0);
  }

  function formatarData(dataString) {
      if (!dataString) return '-';
      const date = new Date(dataString);
      return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  }

  // Event Listeners
  document.addEventListener('DOMContentLoaded', function() {
      // Definir datas padrão (últimos 30 dias)
      const hoje = new Date();
      const trintaDiasAtras = new Date();
      trintaDiasAtras.setDate(hoje.getDate() - 30);
      
      document.getElementById('relatorioDataFim').valueAsDate = hoje;
      document.getElementById('relatorioDataInicio').valueAsDate = trintaDiasAtras;
      
      // Carregar categorias
      loadCategoriasProdutos();
      
      // Carregar dados iniciais
      loadRelatorioSaidasData();
  });

  document.getElementById('filtrarRelatorio').addEventListener('click', loadRelatorioSaidasData);
  document.getElementById('atualizarRelatorio').addEventListener('click', loadRelatorioSaidasData);

  // Permitir filtrar com Enter nos campos de texto
  [document.getElementById('relatorioProdutoNome'), document.getElementById('relatorioProdutoCodigo')].forEach(input => {
      if (input) {
          input.addEventListener('keypress', function(e) {
              if (e.key === 'Enter') {
                  loadRelatorioSaidasData();
              }
          });
      }
  });
  // ===== CAIXAS =====
  // Função para carregar a lista de operadores
    async function loadOperadores() {
        try {
            console.log('Iniciando loadOperadores...');
            
            // Aguarda um pouco para garantir que o DOM esteja pronto
            await new Promise(resolve => setTimeout(resolve, 100));
            
            const select = document.getElementById('caixaOperador');
            console.log('Elemento caixaOperador:', select);
            
            if (!select) {
                console.error('Elemento caixaOperador não encontrado!');
                return;
            }
            
            const response = await fetch('/admin/usuarios/operadores');
            const data = await response.json();
            
            console.log('Dados recebidos da API:', data);
            
            if (data.success) {
                // Limpa opções existentes (exceto a primeira "Todos")
                select.innerHTML = '<option value="">Todos</option>';
                
                // Adiciona os operadores
                data.data.forEach(operador => {
                    const option = document.createElement('option');
                    option.value = operador.id;
                    option.textContent = operador.nome;
                    select.appendChild(option);
                });
                
                console.log(`Operadores carregados: ${data.data.length}`);
            }
        } catch (error) {
            console.error('Erro ao carregar operadores:', error);
        }
    }

    // Modifique a função loadCaixasData para incluir o filtro de operador
    async function loadCaixasData() {
        try {
            const status = document.getElementById('caixaStatus')?.value || '';
            const operadorId = document.getElementById('caixaOperador')?.value || '';
            const dataInicio = document.getElementById('caixaDataInicio')?.value || '';
            const dataFim = document.getElementById('caixaDataFim')?.value || '';
        
            console.log('Filtros aplicados:', { status, operadorId, dataInicio, dataFim });
        
            // Monta query string dinamicamente
            const params = new URLSearchParams();
            if (status) params.append('status', status);
            if (operadorId) params.append('operador_id', operadorId);
            if (dataInicio) params.append('data_inicio', dataInicio);
            if (dataFim) params.append('data_fim', dataFim);
        
            let url = '/admin/caixas';
            if ([...params].length > 0) {
                url += `?${params.toString()}`;
            }
        
            console.log('URL da requisição:', url);
        
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
                        } else if (caixa.status === 'analise' || caixa.status === 'em_analise') {
                            statusClass = 'badge-warning';
                            statusText = 'Em Análise';
                        } else if (caixa.status === 'rejeitado' || caixa.status === 'recusado') {
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
                                    <button class="btn-icon btn-warning reabrir-caixa" data-id="${caixa.id}" title="Reabrir Caixa">
                                        <i class="fas fa-unlock"></i>
                                    </button>
                                    <button class="btn-icon btn-danger fechar-caixa" data-id="${caixa.id}" title="Fechar Caixa">
                                        <i class="fas fa-lock"></i>
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

    // Atualize o evento de refresh para limpar também o filtro de operador
    document.getElementById('refreshCaixas')?.addEventListener('click', () => {
        document.getElementById('caixaStatus').value = '';
        document.getElementById('caixaOperador').value = '';
        document.getElementById('caixaDataInicio').value = '';
        document.getElementById('caixaDataFim').value = '';
        loadCaixasData();
    });

    // Função para inicializar tudo quando a página carregar
    function initializeCaixasPage() {
        console.log('Inicializando página de caixas...');
        
        // Carrega os operadores primeiro
        loadOperadores().then(() => {
            // Depois carrega os caixas
            loadCaixasData();
        });
    }

    // Aguarda o DOM estar completamente carregado
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeCaixasPage);
    } else {
        initializeCaixasPage();
    }
  // Eventos de filtro
  document.getElementById('filterCaixas')?.addEventListener('click', () => {
    loadCaixasData();
  });
  
  document.getElementById('refreshCaixas')?.addEventListener('click', () => {
        document.getElementById('caixaStatus').value = '';
        document.getElementById('caixaOperador').value = '';
        document.getElementById('caixaDataInicio').value = '';
        document.getElementById('caixaDataFim').value = '';
    loadCaixasData();
  });
  
  // Evento para gerar PDF
  document.getElementById('gerarPdfCaixas')?.addEventListener('click', () => {
      gerarPdfCaixas();
  });
  
  async function gerarPdfCaixas() {
      try {
          const status = document.getElementById('caixaStatus')?.value || '';
          const dataInicio = document.getElementById('caixaDataInicio')?.value || '';
          const dataFim = document.getElementById('caixaDataFim')?.value || '';
          const operadorId = document.getElementById('caixaOperador')?.value || '';
          
          // Montar query string com os filtros atuais
          const params = new URLSearchParams();
          if (status) params.append('status', status);
          if (dataInicio) params.append('data_inicio', dataInicio);
          if (dataFim) params.append('data_fim', dataFim);
          if (operadorId) params.append('operador_id', operadorId);
          
          let url = '/admin/caixas/pdf';
          if ([...params].length > 0) {
              url += `?${params.toString()}`;
          }
          
          // Abrir PDF em nova aba
          window.open(url, '_blank');
          
      } catch (error) {
          console.error('Erro ao gerar PDF:', error);
          showFlashMessage('error', 'Erro ao gerar PDF');
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
    
    document.querySelectorAll('.fechar-caixa').forEach(btn => {
      btn.addEventListener('click', function() {
        const caixaId = this.getAttribute('data-id');

        // Criar modal com CSS inline baseado no style.txt
        const modalHtml = `
          <div id="fecharCaixaModal" style="
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            display: flex; justify-content: center; align-items: center;
            background: rgba(0,0,0,0.7);
            z-index: 9999;
          ">
            <div style="
              background-color: #1e293b; /* var(--card-bg) */
              padding: 24px; /* var(--space-lg) */
              border-radius: 8px; /* var(--border-radius) */
              width: 360px;
              max-width: 90%;
              box-shadow: 0 10px 15px rgba(0,0,0,0.3); /* var(--shadow-lg) */
              display: flex;
              flex-direction: column;
              gap: 16px; /* var(--space-md) */
              color: #f8f9fa; /* var(--text-primary) */
              font-family: 'Montserrat', sans-serif;
            ">
              <h3 style="
                font-size: 18px; /* var(--font-size-lg) */
                font-weight: 600; /* var(--font-weight-semibold) */
                background: linear-gradient(135deg, #6c5ce7, #5649c0); /* var(--gradient-primary) */
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 16px;
              ">Fechar Caixa #${caixaId}</h3>

              <input id="valorFechamentoInput" type="number" placeholder="0" min="0" step="0.01" style="
                width: 100%;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #2d3748; /* var(--border-color) */
                background-color: #0f3460; /* var(--bg-tertiary) */
                color: #f8f9fa; /* var(--text-primary) */
              " />

              <textarea id="observacoesInput" placeholder="Observações (opcional)" style="
                width: 100%;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #2d3748;
                background-color: #0f3460;
                color: #f8f9fa;
                min-height: 80px;
                resize: vertical;
              "></textarea>

              <div style="
                display: flex;
                justify-content: flex-end;
                gap: 10px;
              ">
                <button id="fecharCaixaConfirm" style="
                  padding: 8px 16px;
                  background: linear-gradient(135deg, #6c5ce7, #5649c0); /* var(--gradient-primary) */
                  color: #fff;
                  border: none;
                  border-radius: 6px;
                  cursor: pointer;
                  font-weight: 500;
                ">Fechar</button>

                <button id="fecharCaixaCancel" style="
                  padding: 8px 16px;
                  background: linear-gradient(135deg, #d63031, #b02324); /* var(--danger-color/dark) */
                  color: #fff;
                  border: none;
                  border-radius: 6px;
                  cursor: pointer;
                  font-weight: 500;
                ">Cancelar</button>
              </div>
            </div>
          </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const modal = document.getElementById('fecharCaixaModal');
        const valorInput = document.getElementById('valorFechamentoInput');
        const observacoesInput = document.getElementById('observacoesInput');
        const btnConfirm = document.getElementById('fecharCaixaConfirm');
        const btnCancel = document.getElementById('fecharCaixaCancel');

        btnCancel.addEventListener('click', () => modal.remove());

        btnConfirm.addEventListener('click', async () => {
          let valor = parseFloat(valorInput.value);
          if (isNaN(valor)) valor = 0; // assume zero se vazio
          const observacoes = observacoesInput.value || '';

          try {
            const response = await fetchWithErrorHandling(`/admin/caixas/${caixaId}/fechar`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ valor_fechamento: valor, observacoes })
            });
            if (response.success) {
              showFlashMessage('success', 'Caixa fechado com sucesso');
              loadCaixasData();
              modal.remove();
            }
          } catch (err) {
            console.error(err);
            showFlashMessage('error', 'Erro ao fechar caixa');
          }
        });
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
        openModal(document.getElementById('visualizarCaixaModal'));
      }
    } catch (error) {
      console.error('Erro ao visualizar caixa:', error);
      showFlashMessage('error', 'Erro ao carregar dados do caixa');
    }
  }

function openEstornarVendaModal(vendaId, valor, data, cliente, descricao) {
    // Preencher os dados da venda no modal
    document.getElementById('estornoVendaId').value = vendaId;
    document.getElementById('estornoVendaValor').textContent = formatarMoeda(valor);
    document.getElementById('estornoVendaData').textContent = formatDateTime(data);
    document.getElementById('estornoVendaCliente').textContent = cliente || 'Não informado';
    document.getElementById('estornoVendaDescricao').textContent = descricao || 'Não informado';
    
    // Limpar o campo de motivo
    document.getElementById('motivoEstorno').value = '';
    
    // Abrir o modal
    openModal(document.getElementById('estornarVendaModal'));
}

// Função para processar o estorno
async function processarEstorno() {
    const vendaId = document.getElementById('estornoVendaId').value;
    const motivoEstorno = document.getElementById('motivoEstorno').value.trim();
    
    if (!motivoEstorno) {
        showFlashMessage('error', 'Por favor, informe o motivo do estorno');
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetchWithErrorHandling(`/admin/caixa/venda/${vendaId}/estornar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                motivo_estorno: motivoEstorno
            })
        });
        
        if (response.success) {
            showFlashMessage('success', response.message || 'Venda estornada com sucesso');
            closeModal(document.getElementById('estornarVendaModal'));
            
            // Recarregar os dados do caixa
            if (caixaIdAtual) {
                await loadCaixaFinanceiro(caixaIdAtual);
            }
        } else {
            showFlashMessage('error', response.message || 'Erro ao estornar venda');
        }
    } catch (error) {
        console.error('Erro ao estornar venda:', error);
        showFlashMessage('error', 'Erro ao processar estorno');
    } finally {
        showLoading(false);
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
                
                response.data.forEach(item => {
                    const row = document.createElement('tr');
                    const valor = parseFloat(item.valor);

                    // Verificar se é uma venda que pode ser estornada
                    const isVendaEstornavel = item.tipo === 'entrada' && item.nota_fiscal_id;
                    
                    // Format payment methods as tags
                    const paymentTags = item.formas_pagamento && item.formas_pagamento.length > 0 
                        ? item.formas_pagamento.map(p => `<span class="badge badge-info">${p}</span>`).join(' ') 
                        : '-';

                    row.innerHTML = `
                        <td>${formatDateTime(item.data)}</td>
                        <td><span class="badge ${item.tipo === 'entrada' ? 'badge-success' : 'badge-danger'}">${item.tipo === 'entrada' ? 'Entrada' : 'Saída'}</span></td>
                        <td>${item.categoria || '-'}</td>
                        <td>${formatarMoeda(valor)}</td>
                        <td>
                            ${item.descricao || '-'}
                            ${item.cliente_nome ? `<br><small>Cliente: ${item.cliente_nome}</small>` : ''}
                            ${paymentTags !== '-' ? `<br><small>Pagamento: ${paymentTags}</small>` : ''}
                            ${item.nota_fiscal_id ? `
                                <br>
                                <button class="btn btn-sm btn-info btn-editar-pagamento" data-venda-id="${item.nota_fiscal_id}">
                                    <i class="fas fa-edit"></i> Editar Pagamentos
                                </button>
                                <button class="btn btn-sm btn-danger btn-estornar-venda" 
                                        data-venda-id="${item.nota_fiscal_id}"
                                        data-valor="${valor}"
                                        data-data="${item.data}"
                                        data-cliente="${item.cliente_nome || ''}"
                                        data-descricao="${item.descricao || ''}">
                                    <i class="fas fa-undo"></i> Estornar
                                </button>
                            ` : ''}
                        </td>
                    `;
                    
                    // Adicionar eventos aos botões de editar pagamento
                    row.querySelectorAll('.btn-editar-pagamento').forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            const vendaId = btn.getAttribute('data-venda-id');
                            openEditarFormasPagamentoModal(vendaId);
                        });
                    });
                    
                    // Adicionar eventos aos botões de estornar
                    row.querySelectorAll('.btn-estornar-venda').forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            const vendaId = btn.getAttribute('data-venda-id');
                            const valor = btn.getAttribute('data-valor');
                            const data = btn.getAttribute('data-data');
                            const cliente = btn.getAttribute('data-cliente');
                            const descricao = btn.getAttribute('data-descricao');
                            openEstornarVendaModal(vendaId, valor, data, cliente, descricao);
                        });
                    });
                    
                    // Adiciona evento de clique para abrir detalhes da venda
                    if (item.nota_fiscal_id) {
                        row.style.cursor = 'pointer';
                        row.classList.add('clickable-row');
                        row.addEventListener('click', () => {
                            openDetalhesVendaModal(item.nota_fiscal_id);
                        });
                    }
                    
                    tableBody.appendChild(row);
                });

                // USE OS TOTAIS DO BACKEND (response.totais) EM VEZ DE CALCULAR NOVAMENTE
                if (document.getElementById('caixaTotalEntradas')) {
                    document.getElementById('caixaTotalEntradas').textContent = formatarMoeda(response.totais.entradas);
                }
                if (document.getElementById('caixaTotalSaidas')) {
                    document.getElementById('caixaTotalSaidas').textContent = formatarMoeda(response.totais.saidas);
                }
                if (document.getElementById('caixaSaldo')) {
                    document.getElementById('caixaSaldo').textContent = formatarMoeda(response.totais.saldo);
                }
                if (document.getElementById('caixaValorFisico')) {
                    document.getElementById('caixaValorFisico').textContent = formatarMoeda(response.totais.valor_fisico || 0);
                }
                if (document.getElementById('caixaValorDigital')) {
                    document.getElementById('caixaValorDigital').textContent = formatarMoeda(response.totais.valor_digital || 0);
                }
                if (document.getElementById('caixaAPrazo')) {
                    document.getElementById('caixaAPrazo').textContent = formatarMoeda(response.totais.a_prazo || 0);
                }
                if(document.getElementById('totalAPrazoRecebido')){
                    document.getElementById('totalAPrazoRecebido').textContent = formatarMoeda(response.totais.contas_prazo_recebidas || 0);
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

                // Adiciona eventos de clique para os cards de formas de pagamento
                addFormaPagamentoClickEvents(caixaId);
            }
        }
    } catch (error) {
        console.error('Erro ao carregar financeiro do caixa:', error);
        showFlashMessage('error', 'Erro ao carregar movimentações financeiras');
    }
}
function showLoading(show) {
    const loadingElement = document.getElementById('loadingOverlay');
    if (loadingElement) {
        loadingElement.style.display = show ? 'flex' : 'none';
    }
}
window.addEventListener('load', function() {
    // Adicionar event listener para o botão de confirmar estorno no modal
    const btnConfirmarEstorno = document.getElementById('btnConfirmarEstorno');
    if (btnConfirmarEstorno) {
        btnConfirmarEstorno.addEventListener('click', processarEstorno);
    }
    
    // Adicionar event listener para o campo de motivo (submeter com Enter)
    const motivoEstornoInput = document.getElementById('motivoEstorno');
    if (motivoEstornoInput) {
        motivoEstornoInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                processarEstorno();
            }
        });
    }
});
// Função para adicionar eventos de clique aos cards de formas de pagamento
function addFormaPagamentoClickEvents(caixaId) {
    const formasPagamentoIds = [
        'totalPixFabiano', 'totalPixMaquineta', 'totalPixEdFrance', 
        'totalPixLoja', 'totalDinheiro', 'totalCartaoCredito', 
        'totalCartaoDebito', 'totalAPrazo'
    ];

    const formaPagamentoMap = {
        'totalPixFabiano': 'pix_fabiano',
        'totalPixMaquineta': 'pix_maquineta',
        'totalPixEdFrance': 'pix_edfrance',
        'totalPixLoja': 'pix_loja',
        'totalDinheiro': 'dinheiro',
        'totalCartaoCredito': 'cartao_credito',
        'totalCartaoDebito': 'cartao_debito',
        'totalAPrazo': 'a_prazo'
    };

    formasPagamentoIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            // Encontra o elemento pai (total-item) para tornar clicável
            const card = element.closest('.total-item');
            if (card) {
                card.style.cursor = 'pointer';
                card.classList.add('clickable-card');
                card.addEventListener('click', () => {
                    const formaPagamento = formaPagamentoMap[id];
                    openVendasFormaPagamentoModal(caixaId, formaPagamento);
                });
            }
        }
    });
}

// Função para abrir modal de vendas por forma de pagamento
async function openVendasFormaPagamentoModal(caixaId, formaPagamento) {
    try {
        const response = await fetchWithErrorHandling(`/admin/caixas/${caixaId}/vendas-por-pagamento?forma_pagamento=${formaPagamento}`);
        
        if (response.success) {
            const modal = document.getElementById('vendasFormaPagamentoModal');
            const tableBody = document.querySelector('#vendasFormaPagamentoTable tbody');
            const titulo = document.getElementById('vendasFormaPagamentoTitulo');
            
            // Atualiza título do modal
            titulo.textContent = `Vendas - ${formatFormaPagamento(formaPagamento)}`;
            
            // Limpa tabela
            tableBody.innerHTML = '';
            
            // Preenche tabela com vendas
            response.vendas.forEach(venda => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDateTime(venda.data_emissao)}</td>
                    <td>${venda.id}</td>
                    <td>${venda.cliente_nome || 'Não informado'}</td>
                    <td>${formatarMoeda(venda.valor_total)}</td>
                    <td>${formatarMoeda(venda.valor_pago)}</td>
                    <td>
                        <button class="btn-view-venda" data-venda-id="${venda.id}">
                            <i class="fas fa-eye"></i> Ver Detalhes
                        </button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
            
            // Adiciona eventos de clique para os botões de visualização
            document.querySelectorAll('.btn-view-venda').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const vendaId = btn.getAttribute('data-venda-id');
                    openDetalhesVendaModal(vendaId);
                });
            });
            // botão PDF
            const btnExportarPdf = document.getElementById('btnExportarPdf');
            btnExportarPdf.onclick = () => {
                const url = `/admin/caixas/${caixaId}/vendas-por-pagamento/pdf?forma_pagamento=${formaPagamento}`;
                window.open(url, '_blank');
            };

            // Abre o modal
            openModal(modal);
        } else {
            showFlashMessage('error', response.error || 'Erro ao carregar vendas');
        }
    } catch (error) {
        console.error('Erro ao abrir modal de vendas:', error);
        showFlashMessage('error', 'Erro ao carregar vendas');
    }
}
// Configurar botão de PDF de movimentações
document.getElementById('abrirPdfMovimentacoes')?.addEventListener('click', function() {
    if (caixaIdAtual) {
        const url = `/admin/caixas/${caixaIdAtual}/financeiro/movimentacoes/pdf`;
        window.open(url, '_blank');
    } else {
        showFlashMessage('error', 'Nenhum caixa selecionado');
    }
});
// Função para abrir modal de detalhes da venda
async function openDetalhesVendaModal(vendaId) {
    try {
        const response = await fetchWithErrorHandling(`/admin/vendas/${vendaId}/detalhes`);
        
        if (response.success) {
            const modal = document.getElementById('detalhesVendaModal');
            const venda = response.venda;
            
            // Preenche informações básicas
            document.getElementById('detalheNotaFiscalId').textContent = venda.id;
            document.getElementById('detalheDataVenda').textContent = formatDateTime(venda.data_emissao);
            document.getElementById('detalheCliente').textContent = venda.cliente_nome || 'Não informado';
            document.getElementById('detalheValorTotal').textContent = formatarMoeda(venda.valor_total);
            
            // Preence informações de desconto
            const desconto = venda.valor_desconto > 0 
                ? `${formatarMoeda(venda.valor_desconto)} (${venda.tipo_desconto || 'N/A'})`
                : 'Nenhum';
            document.getElementById('detalheDesconto').textContent = desconto;
            
            // Preenche formas de pagamento
            const formasPagamento = venda.pagamentos.map(p => 
                `${p.forma_pagamento}: ${formatarMoeda(p.valor)}`
            ).join(', ');
            document.getElementById('detalheFormasPagamento').textContent = formasPagamento || 'Nenhuma';
            
            // Preenche tabela de produtos
            const produtosTable = document.querySelector('#detalhesProdutosTable tbody');
            produtosTable.innerHTML = '';
            
            venda.itens.forEach(item => {
                const row = document.createElement('tr');
                const descontoInfo = item.desconto_aplicado > 0 
                    ? `${formatarMoeda(item.desconto_aplicado)} (${item.tipo_desconto || 'N/A'})`
                    : 'Nenhum';
                
                row.innerHTML = `
                    <td>${item.produto_nome}</td>
                    <td>${item.quantidade}</td>
                    <td>${item.unidade_medida}</td>
                    <td>${formatarMoeda(item.valor_unitario)}</td>
                    <td>${descontoInfo}</td>
                    <td>${formatarMoeda(item.valor_total)}</td>
                `;
                produtosTable.appendChild(row);
            });
            
            // Atualiza título do modal
            document.getElementById('detalhesVendaTitulo').textContent = `Detalhes da Venda #${venda.id}`;
            
            // Abre o modal
            openModal(modal);
        } else {
            showFlashMessage('error', response.error || 'Erro ao carregar detalhes da venda');
        }
    } catch (error) {
        console.error('Erro ao abrir modal de detalhes:', error);
        showFlashMessage('error', 'Erro ao carregar detalhes da venda');
    }
}

// Função auxiliar para formatar o nome da forma de pagamento
function formatFormaPagamento(forma) {
    const formatMap = {
        'pix_fabiano': 'PIX Fabiano',
        'pix_maquineta': 'PIX Maquineta',
        'pix_edfrance': 'PIX Edfranci',
        'pix_loja': 'PIX Loja',
        'dinheiro': 'Dinheiro',
        'cartao_credito': 'Cartão Crédito',
        'cartao_debito': 'Cartão Débito',
        'a_prazo': 'A Prazo'
    };
    
    return formatMap[forma] || forma;
}

document.getElementById('abrirPdfCaixa').addEventListener('click', () => {
    if (caixaIdAtual) {
        const url = `/admin/caixas/${caixaIdAtual}/financeiro/pdf`;
        window.open(url, '_blank');
    } else {
        alert('Nenhum caixa selecionado');
    }
});

// Adiciona estilos CSS para indicar elementos clicáveis
const style = document.createElement('style');
style.textContent = `
    .clickable-row:hover {
        background-color: #f8f9fa !important;
        box-shadow: 0 0 5px rgba(0,0,0,0.1);
    }
    
    .clickable-card:hover {
        background-color: #f0f8ff !important;
        transform: translateY(-2px);
        transition: all 0.2s ease;
    }
    
    .btn-view-venda {
        background: #007bff;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 3px;
        cursor: pointer;
        font-size: 12px;
    }
    
    .btn-view-venda:hover {
        background: #0056b3;
    }
`;
document.head.appendChild(style);

let vendaEmEdicao = null;
let formasPagamentoEditadas = [];

// ===== FUNÇÕES PARA EDIÇÃO DE FORMAS DE PAGAMENTO =====

// Função para abrir o modal de edição de formas de pagamento
async function openEditarFormasPagamentoModal(vendaId) {
    try {
        // Busca os detalhes da venda
        const response = await fetchWithErrorHandling(`/admin/vendas/${vendaId}/detalhes`);
        
        if (response.success) {
            vendaEmEdicao = response.venda;
            formasPagamentoEditadas = [...vendaEmEdicao.pagamentos];
            
            // Atualiza o modal
            document.getElementById('editarPagamentoVendaId').textContent = vendaId;
            document.getElementById('totalVendaValor').textContent = formatarMoeda(vendaEmEdicao.valor_total);
            
            // Renderiza as formas de pagamento atuais
            renderFormasPagamento();
            
            // Calcula totais
            calcularTotaisPagamentos();
            
            // Abre o modal
            const modal = document.getElementById('editarFormasPagamentoModal');
            openModal(modal);
        } else {
            showFlashMessage('error', response.error || 'Erro ao carregar detalhes da venda');
        }
    } catch (error) {
        console.error('Erro ao abrir modal de edição:', error);
        showFlashMessage('error', 'Erro ao carregar detalhes da venda');
    }
}

// Função para renderizar as formas de pagamento
function renderFormasPagamento() {
    const container = document.getElementById('formasPagamentoAtuais');
    container.innerHTML = '';
    
    formasPagamentoEditadas.forEach((pagamento, index) => {
        const item = document.createElement('div');
        item.className = 'forma-pagamento-item';
        item.innerHTML = `
            <span class="badge badge-info">${formatFormaPagamento(pagamento.forma_pagamento)}</span>
            <span class="forma-pagamento-valor">${formatarMoeda(pagamento.valor)}</span>
            <button class="btn-remover-forma" data-index="${index}">
                <i class="fas fa-times"></i>
            </button>
        `;
        container.appendChild(item);
    });
    
    // Adiciona eventos de clique para os botões de remover
    document.querySelectorAll('.btn-remover-forma').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = parseInt(e.currentTarget.getAttribute('data-index'));
            formasPagamentoEditadas.splice(index, 1);
            renderFormasPagamento();
            calcularTotaisPagamentos();
        });
    });
}

// Função para calcular totais dos pagamentos
function calcularTotaisPagamentos() {
    const totalPagamentos = formasPagamentoEditadas.reduce((sum, pagamento) => sum + pagamento.valor, 0);
    const totalVenda = vendaEmEdicao.valor_total;
    
    document.getElementById('totalPagamentosValor').textContent = formatarMoeda(totalPagamentos);
    
    // Verifica se há diferença
    const diferencaContainer = document.getElementById('diferencaContainer');
    const diferencaValor = document.getElementById('diferencaValor');
    
    if (Math.abs(totalPagamentos - totalVenda) > 0.01) {
        const diferenca = totalVenda - totalPagamentos;
        diferencaValor.textContent = formatarMoeda(diferenca);
        diferencaValor.className = `total-value ${diferenca < 0 ? 'negative' : 'positive'}`;
        diferencaContainer.style.display = 'block';
    } else {
        diferencaContainer.style.display = 'none';
    }
}

// Função para adicionar nova forma de pagamento
function adicionarNovaFormaPagamento() {
    const formaSelect = document.getElementById('novaFormaPagamento');
    const valorInput = document.getElementById('novoValorPagamento');
    
    const forma = formaSelect.value;
    let valor = parseFloat(valorInput.value) || 0;
    
    if (!forma) {
        showFlashMessage('error', 'Selecione uma forma de pagamento');
        return;
    }
    
    // Se não foi informado valor, calcula automaticamente para distribuir igualmente
    if (valor <= 0) {
        const totalAtual = formasPagamentoEditadas.reduce((sum, p) => sum + p.valor, 0);
        const restante = vendaEmEdicao.valor_total - totalAtual;
        
        if (restante <= 0) {
            showFlashMessage('error', 'O valor total já foi distribuído entre as formas de pagamento');
            return;
        }
        
        valor = restante;
    }
    
    // Adiciona a nova forma de pagamento
    formasPagamentoEditadas.push({
        forma_pagamento: forma,
        valor: valor
    });
    
    // Limpa os campos
    formaSelect.value = '';
    valorInput.value = '';
    
    // Atualiza a interface
    renderFormasPagamento();
    calcularTotaisPagamentos();
}

// Função para salvar as alterações
async function salvarFormasPagamento() {
    try {
        // Verifica se a soma dos pagamentos corresponde ao valor total
        const totalPagamentos = formasPagamentoEditadas.reduce((sum, pagamento) => sum + pagamento.valor, 0);
        
        if (Math.abs(totalPagamentos - vendaEmEdicao.valor_total) > 0.01) {
            if (!confirm('A soma dos pagamentos não corresponde ao valor total da venda. Deseja continuar mesmo assim?')) {
                return;
            }
        }
        
        // Envia as alterações para o servidor
        const response = await fetchWithErrorHandling(`/admin/vendas/${vendaEmEdicao.id}/atualizar-pagamentos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                pagamentos: formasPagamentoEditadas
            })
        });
        
        if (response.success) {
            showFlashMessage('success', 'Formas de pagamento atualizadas com sucesso!');
            
            // Fecha o modal
            closeModal(document.getElementById('editarFormasPagamentoModal'));
            
            // Recarrega os dados do caixa
            if (caixaIdAtual) {
                await loadCaixaFinanceiro(caixaIdAtual);
            }
        } else {
            showFlashMessage('error', response.error || 'Erro ao atualizar formas de pagamento');
        }
    } catch (error) {
        console.error('Erro ao salvar formas de pagamento:', error);
        showFlashMessage('error', 'Erro ao atualizar formas de pagamento');
    }
}

// Função auxiliar para formatar o nome da forma de pagamento
function formatFormaPagamento(forma) {
    const formatMap = {
        'pix_fabiano': 'PIX Fabiano',
        'pix_maquineta': 'PIX Maquineta',
        'pix_edfrance': 'PIX Edfranci',
        'pix_loja': 'PIX Loja',
        'dinheiro': 'Dinheiro',
        'cartao_credito': 'Cartão Crédito',
        'cartao_debito': 'Cartão Débito',
        'a_prazo': 'A Prazo'
    };
    
    return formatMap[forma] || forma;
}

function setupFormasPagamentoEvents() {
    // Adiciona eventos aos botões do modal
    const adicionarBtn = document.getElementById('adicionarFormaPagamento');
    const salvarBtn = document.getElementById('salvarFormasPagamento');
    const valorInput = document.getElementById('novoValorPagamento');
    
    if (adicionarBtn) {
        adicionarBtn.addEventListener('click', adicionarNovaFormaPagamento);
    }
    
    if (salvarBtn) {
        salvarBtn.addEventListener('click', salvarFormasPagamento);
    }
    
    // Permite pressionar Enter no campo de valor
    if (valorInput) {
        valorInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                adicionarNovaFormaPagamento();
            }
        });
    }
}

  // Event Listeners para Caixas
  document.getElementById('refreshData')?.addEventListener('click', loadDashboardData);
  // Variáveis globais
  let contasReceberData = [];
  let caixasAbertos = [];

  // Função para abrir o modal de contas a receber
  function openContasReceberModal() {
      loadContasReceber();
      carregarCaixasAbertos();
      openModal('contasReceberModal');
  }

  // Função para carregar as contas a receber
  async function loadContasReceber() {
      try {
          const dataInicio = document.getElementById('contasReceberDataInicio')?.value || '';
          const dataFim = document.getElementById('contasReceberDataFim')?.value || '';
          const status = document.getElementById('contasReceberStatus')?.value || '';
          
          const params = new URLSearchParams();
          if (dataInicio) params.append('data_emissao_inicio', dataInicio);
          if (dataFim) params.append('data_emissao_fim', dataFim);
          if (status) params.append('status', status);
          
          const response = await fetch(`/admin/contas-receber?${params.toString()}`);
          
          if (!response.ok) {
              throw new Error('Erro na requisição');
          }
          
          const data = await response.json();
          
          if (data && data.contas && data.contas.length > 0) {
              contasReceberData = data.contas;
              atualizarTabelaContasReceber();
          } else {
              contasReceberData = [];
              atualizarTabelaContasReceber();
              showFlashMessage('warning', 'Nenhuma conta encontrada com os filtros aplicados');
          }
      } catch (error) {
          console.error('Erro ao carregar contas a receber:', error);
          showFlashMessage('error', 'Erro ao carregar contas a receber');
      }
  }

  document.addEventListener('DOMContentLoaded', function() {
      const btnFiltrar = document.getElementById('filtrarContasReceber');
      if (btnFiltrar) {
          btnFiltrar.addEventListener('click', loadContasReceber);
      }
  });

  // Função para gerar PDF da conta
  async function gerarPDFConta(contaId) {
      try {
          // Mostrar indicador de carregamento (opcional)
          const btnPDF = document.querySelector(`button[data-pdf-id="${contaId}"]`);
          if (btnPDF) {
              const originalHTML = btnPDF.innerHTML;
              btnPDF.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
              btnPDF.disabled = true;
              
              // Restaurar botão após um tempo
              setTimeout(() => {
                  btnPDF.innerHTML = originalHTML;
                  btnPDF.disabled = false;
              }, 3000);
          }
          
          // Fazer requisição para gerar o PDF
          const response = await fetch(`/admin/contas-receber/${contaId}/pdf`);
          
          if (!response.ok) {
              throw new Error('Erro ao gerar PDF');
          }
          
          // Criar blob com o PDF
          const pdfBlob = await response.blob();
          
          // Criar URL temporária para o blob
          const pdfUrl = window.URL.createObjectURL(pdfBlob);
          
          // Abrir em nova guia
          window.open(pdfUrl, '_blank');
          
          // Limpar URL temporária após um tempo
          setTimeout(() => {
              window.URL.revokeObjectURL(pdfUrl);
          }, 1000);
          
      } catch (error) {
          console.error('Erro ao gerar PDF:', error);
          showFlashMessage('error', 'Erro ao gerar PDF da conta');
      }
  }

  // Função para atualizar a tabela de contas a receber
  function atualizarTabelaContasReceber() {
      const tbody = document.querySelector('#tabelaContasReceber tbody');
      if (!tbody) return;
      
      tbody.innerHTML = '';
      
      if (contasReceberData.length === 0) {
          tbody.innerHTML = '<tr><td colspan="11" class="text-center">Nenhuma conta encontrada</td></tr>';
          return;
      }
      
      contasReceberData.forEach(conta => {
          const tr = document.createElement('tr');
          
          // Determinar status e classe CSS
          let statusClass, statusText;
          const hoje = new Date();
          const vencimento = new Date(conta.data_vencimento);
          
          if (conta.status === 'quitado') {
              statusClass = 'badge-success';
              statusText = 'Quitado';
          } else if (conta.status === 'parcial') {
              statusClass = 'badge-info';
              statusText = 'Parcial';
          } else if (vencimento < hoje) {
              statusClass = 'badge-danger';
              statusText = 'Atrasado';
          } else {
              statusClass = 'badge-warning';
              statusText = 'Pendente';
          }
          
          tr.innerHTML = `
              <td>${conta.id}</td>
              <td>${conta.cliente.nome}</td>
              <td>${conta.cliente.documento || ''}</td>
              <td>${conta.descricao || '-'}</td>
              <td>${formatarMoeda(conta.valor_original)}</td>
              <td>${formatarMoeda(conta.valor_aberto)}</td>
              <td>${formatarData(conta.data_emissao)}</td>
              <td>${formatarData(conta.data_vencimento)}</td>
              <td><span class="badge ${statusClass}">${statusText}</span></td>
              <td>
                  <button class="btn btn-sm btn-info btn-detalhes-conta" data-id="${conta.id}" title="Detalhes">
                      <i class="fas fa-eye"></i>
                  </button>
                  <button class="btn btn-sm btn-danger btn-pdf-conta" data-pdf-id="${conta.id}" title="Gerar PDF">
                      <i class="fas fa-file-pdf"></i>
                  </button>
              </td>
          `;
          
          tbody.appendChild(tr);
      });
      
      // Adicionar eventos aos botões de detalhes
      document.querySelectorAll('.btn-detalhes-conta').forEach(btn => {
          btn.addEventListener('click', function() {
              const contaId = this.getAttribute('data-id');
              abrirModalDetalhesConta(contaId);
          });
      });
      
      // Adicionar eventos aos botões de PDF
      document.querySelectorAll('.btn-pdf-conta').forEach(btn => {
          btn.addEventListener('click', function() {
              const contaId = this.getAttribute('data-pdf-id');
              gerarPDFConta(contaId);
          });
      });
  }
  // Função para formatar data (dd/mm/aaaa)
  function formatarData(dataString) {
      if (!dataString) return '-';
      const date = new Date(dataString);
      return date.toLocaleDateString('pt-BR');
  }

  async function abrirModalDetalhesConta(contaId) {
      try {
          const response = await fetchWithErrorHandling(`/admin/contas-receber/${contaId}/detalhes`);
          
          if (response) {
              const conta = response;
              
              // Preencher detalhes básicos
              document.getElementById('contaIdPagamento').value = conta.id;
              document.getElementById('detalheClienteNome').textContent = conta.cliente;
              document.getElementById('detalheClienteDocumento').textContent = conta.cliente_documento || 'Não informado';
              document.getElementById('detalheDescricao').textContent = conta.descricao || 'Sem descrição';
              document.getElementById('detalheValorTotal').textContent = formatarMoeda(conta.valor_original);
              document.getElementById('detalheValorPendente').textContent = formatarMoeda(conta.valor_aberto);
              
              // Status
              const statusElement = document.getElementById('detalheStatus');
              if (statusElement) {
                  if (conta.status === 'quitado') {
                      statusElement.textContent = 'Quitado';
                      statusElement.className = 'value badge badge-success';

                      // Ocultar área de pagamento
                      const pagamentoSection = document.getElementById('areaPagamento');
                      if (pagamentoSection) pagamentoSection.style.display = 'none';

                  } else if (conta.status === 'parcial') {
                      statusElement.textContent = 'Parcial';
                      statusElement.className = 'value badge badge-info';

                      // Mostrar área de pagamento
                      const pagamentoSection = document.getElementById('areaPagamento');
                      if (pagamentoSection) pagamentoSection.style.display = '';

                  } else {
                      const hoje = new Date();
                      const vencimento = new Date(conta.data_vencimento);
                      
                      if (vencimento < hoje) {
                          statusElement.textContent = 'Atrasado';
                          statusElement.className = 'value badge badge-danger';
                      } else {
                          statusElement.textContent = 'Pendente';
                          statusElement.className = 'value badge badge-warning';
                      }

                      // Mostrar área de pagamento
                      const pagamentoSection = document.getElementById('areaPagamento');
                      if (pagamentoSection) pagamentoSection.style.display = '';
                  }
              }
              
              // Preencher pagamentos
              const pagamentosTbody = document.getElementById('detalhePagamentos');
              if (pagamentosTbody) {
                  pagamentosTbody.innerHTML = '';
                  
                  if (conta.pagamentos && conta.pagamentos.length > 0) {
                      conta.pagamentos.forEach(pag => {
                          const tr = document.createElement('tr');
                          tr.innerHTML = `
                              <td>${pag.data_pagamento}</td>
                              <td>${formatarMoeda(pag.valor_pago)}</td>
                              <td>${formatarFormaPagamento(pag.forma_pagamento)}</td>
                              <td>${pag.observacoes || '-'}</td>
                          `;
                          pagamentosTbody.appendChild(tr);
                      });
                  } else {
                      pagamentosTbody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhum pagamento registrado</td></tr>';
                  }
              } else {
                  console.error('Elemento detalhePagamentos não encontrado');
              }

              // Preencher select de caixas
              const selectCaixa = document.getElementById('caixaPagamento');
              if (selectCaixa) {
                  selectCaixa.innerHTML = '<option value="">Selecione</option>';

                  if (conta.caixas && conta.caixas.length > 0) {
                      conta.caixas.forEach(caixa => {
                          const option = document.createElement('option');
                          option.value = caixa.id;
                          option.textContent = `Caixa ${caixa.id} - ${caixa.operador} - ${formatarData(caixa.data_abertura)} (${caixa.status})`;
                          selectCaixa.appendChild(option);
                      });
                  } else {
                      const option = document.createElement('option');
                      option.value = '';
                      option.textContent = 'Nenhum caixa disponível';
                      selectCaixa.appendChild(option);
                  }
              }
              
              // Definir data atual como padrão
              const hoje = new Date();
              const dataPagamentoInput = document.getElementById('dataPagamento');
              if (dataPagamentoInput) {
                  dataPagamentoInput.value = hoje.toISOString().split('T')[0];
              }
              
              // Definir valor pendente como valor padrão
              const valorPagamentoInput = document.getElementById('valorPagamento');
              if (valorPagamentoInput) {
                  valorPagamentoInput.value = conta.valor_aberto;
              }
              setupPagamentoButtons();
              openModal('detalhesContaModal');
          }
      } catch (error) {
          console.error('Erro ao carregar detalhes da conta:', error);
          showFlashMessage('error', 'Erro ao carregar detalhes da conta');
      }
  }

  // Função para formatar forma de pagamento
  function formatarFormaPagamento(forma) {
      const formas = {
          'dinheiro': 'Dinheiro',
          'pix_loja': 'PIX Loja',
          'pix_fabiano': 'PIX Fabiano',
          'pix_maquineta': 'PIX Maquineta',
          'pix_edfrance': 'PIX Edfranci',
          'cartao_credito': 'Cartão Crédito',
          'cartao_debito': 'Cartão Débito',
          'a_prazo': 'A Prazo'
      };
      
      return formas[forma] || forma;
  }

  // Função para carregar caixas abertos no select
  async function carregarCaixasAbertos() {
      try {
          const response = await fetchWithErrorHandling('/admin/api/caixas/abertos');
          
          if (response && response.caixas) {
              caixasAbertos = response.caixas;
              const select = document.getElementById('caixaPagamento');
              
              if (select) {
                  select.innerHTML = '<option value="">Selecione</option>';
                  
                  caixasAbertos.forEach(caixa => {
                      const option = document.createElement('option');
                      option.value = caixa.id;
                      option.textContent = `Caixa #${caixa.id} - ${caixa.operador} (${formatarData(caixa.data_abertura)})`;
                      select.appendChild(option);
                  });
              }
          }
      } catch (error) {
          console.error('Erro ao carregar caixas abertos:', error);
      }
  }

  // Função para registrar pagamento
  let pagamentoEmProcesso = false;

  async function registrarPagamento(contaId, valor, pagarTotal = false) {
      if (pagamentoEmProcesso) return; // impede execução duplicada
      pagamentoEmProcesso = true;

      try {
          const dataPagamento = document.getElementById('dataPagamento').value;
          const formaPagamento = document.getElementById('formaPagamento').value;
          const caixaPagamento = document.getElementById('caixaPagamento').value;
          const observacaoPagamento = document.getElementById('observacaoPagamento').value;

          // Validações
          if (!dataPagamento) {
              showFlashMessage('error', 'Informe a data do pagamento');
              pagamentoEmProcesso = false;
              return;
          }
          if (!formaPagamento) {
              showFlashMessage('error', 'Selecione a forma de pagamento');
              pagamentoEmProcesso = false;
              return;
          }
          if (valor <= 0 || isNaN(valor)) {
              showFlashMessage('error', 'Informe um valor válido');
              pagamentoEmProcesso = false;
              return;
          }

          const response = await fetchWithErrorHandling(`/admin/contas-receber/${contaId}/pagar`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  valor_pago: valor,
                  forma_pagamento: formaPagamento,
                  caixa_id: caixaPagamento || null,
                  observacoes: observacaoPagamento || '',
                  data_pagamento: dataPagamento
              })
          });

          if (response && response.success) {
              showFlashMessage('success', 'Pagamento registrado com sucesso');

              document.getElementById('detalheValorPendente').textContent = formatarMoeda(response.valor_aberto);

              const statusElement = document.getElementById('detalheStatus');
              if (statusElement) {
                  statusElement.textContent = response.status === 'quitado' ? 'Quitado' : 'Pendente';
                  statusElement.className = 'value badge ' + (response.status === 'quitado' ? 'badge-success' : 'badge-warning');
              }

              await atualizarListaPagamentos(contaId);

              if (pagarTotal) {
                  closeModal('detalhesContaModal');
                  loadContasReceber();
              }
          }
      } catch (error) {
          console.error('Erro ao registrar pagamento:', error);
          showFlashMessage('error', error.message || 'Erro ao registrar pagamento');
      } finally {
          pagamentoEmProcesso = false;
      }
  }

  // Evento submit do formulário de pagamento
  document.getElementById('formPagamentoConta')?.addEventListener('submit', function(e) {
      e.preventDefault();
      const contaId = document.getElementById('contaIdPagamento').value;
      const valor = parseFloat(document.getElementById('valorPagamento').value);
      if (contaId && valor) {
          registrarPagamento(contaId, valor);
      }
  });

  // Corrigido: prevenir submit duplo quando clicar em "Pagar Total"
  document.getElementById('btnPagarTotal')?.addEventListener('click', function(e) {
      e.preventDefault(); // impede que o botão envie o form automaticamente
      const contaId = document.getElementById('contaIdPagamento').value;
      const valorPendenteText = document.getElementById('detalheValorPendente').textContent;
      const valorPendente = parseFloat(valorPendenteText.replace(/[^\d,]/g, '').replace(',', '.'));
      
      if (contaId && valorPendente > 0) {
          document.getElementById('valorPagamento').value = valorPendente.toFixed(2);
          registrarPagamento(contaId, valorPendente, true);
      }
  });


  // Função para atualizar a lista de pagamentos
  async function atualizarListaPagamentos(contaId) {
      try {
          const response = await fetchWithErrorHandling(`/admin/contas-receber/${contaId}/detalhes`);
          
          if (response && response.pagamentos) {
              const tbody = document.getElementById('detalhePagamentos');
              if (tbody) {
                  tbody.innerHTML = '';
                  
                  response.pagamentos.forEach(pag => {
                      const tr = document.createElement('tr');
                      tr.innerHTML = `
                          <td>${pag.data_pagamento}</td>
                          <td>${formatarMoeda(pag.valor_pago)}</td>
                          <td>${formatarFormaPagamento(pag.forma_pagamento)}</td>
                          <td>${pag.observacoes || '-'}</td>
                      `;
                      tbody.appendChild(tr);
                  });
              }
          }
      } catch (error) {
          console.error('Erro ao atualizar lista de pagamentos:', error);
      }
  }

  // Event Listeners
  document.addEventListener('DOMContentLoaded', function() {
      // Adicionar item ao menu sidebar
      const financeiroNavItem = document.querySelector('.sidebar-nav li[data-tab="financeiro"]');
      if (financeiroNavItem) {
          const contasReceberItem = document.createElement('li');
          contasReceberItem.innerHTML = `
              <a href="#contas-receber" class="nav-link">
                  <i class="fas fa-hand-holding-usd"></i>
                  <span class="nav-text">Contas a Receber</span>
              </a>
          `;
          financeiroNavItem.parentNode.insertBefore(contasReceberItem, financeiroNavItem.nextSibling);
          
          // Adicionar evento de clique
          contasReceberItem.addEventListener('click', function(e) {
              e.preventDefault();
              openContasReceberModal();
          });
      }
      
      // Filtro
      document.getElementById('btnFiltrarContas')?.addEventListener('click', loadContasReceber);
      
      // Formulário de pagamento
      document.getElementById('formPagamentoConta')?.addEventListener('submit', function(e) {
          e.preventDefault();
          const contaId = document.getElementById('contaIdPagamento').value;
          const valor = parseFloat(document.getElementById('valorPagamento').value);
          registrarPagamento(contaId, valor);
      });
      
      // Botão pagar total
      document.getElementById('btnPagarTotal')?.addEventListener('click', function() {
          const contaId = document.getElementById('contaIdPagamento').value;
          const valorPendenteText = document.getElementById('detalheValorPendente').textContent;
          const valorPendente = parseFloat(valorPendenteText.replace(/[^\d,]/g, '').replace(',', '.'));
          
          if (confirm(`Confirmar pagamento total de ${valorPendenteText}?`)) {
              document.getElementById('valorPagamento').value = valorPendente;
              registrarPagamento(contaId, valorPendente, true);
          }
      });
      
      // Permitir filtrar com Enter nos campos de texto
      document.getElementById('filtroClienteNome')?.addEventListener('keypress', function(e) {
          if (e.key === 'Enter') {
              loadContasReceber();
          }
      });
      
      document.getElementById('filtroClienteDocumento')?.addEventListener('keypress', function(e) {
          if (e.key === 'Enter') {
              loadContasReceber();
          }
      });
      // Adicione isso no final do arquivo, dentro do DOMContentLoaded
      document.addEventListener('DOMContentLoaded', function() {
          // Formulário de pagamento
          const formPagamento = document.getElementById('formPagamentoConta');
          if (formPagamento) {
              formPagamento.addEventListener('submit', function(e) {
                  e.preventDefault();
                  const contaId = document.getElementById('contaIdPagamento').value;
                  const valor = parseFloat(document.getElementById('valorPagamento').value);
                  
                  if (isNaN(valor) || valor <= 0) {
                      showFlashMessage('error', 'Informe um valor válido');
                      return;
                  }
                  
                  const valorPendenteText = document.getElementById('detalheValorPendente').textContent;
                  const valorPendente = parseFloat(valorPendenteText.replace(/[^\d,]/g, '').replace(',', '.'));
                  
                  if (valor > valorPendente) {
                      showFlashMessage('error', 'Valor informado é maior que o valor pendente');
                      return;
                  }
                  
                  registrarPagamento(contaId, valor);
              });
          }
          
          // Botão de pagar total
          const btnPagarTotal = document.getElementById('btnPagarTotal');
          if (btnPagarTotal) {
              btnPagarTotal.addEventListener('click', function() {
                  const contaId = document.getElementById('contaIdPagamento').value;
                  const valorPendenteText = document.getElementById('detalheValorPendente').textContent;
                  const valorPendente = parseFloat(valorPendenteText.replace(/[^\d,]/g, '').replace(',', '.'));
                  
                  if (confirm(`Confirmar pagamento total de ${valorPendenteText}?`)) {
                      document.getElementById('valorPagamento').value = valorPendente;
                      registrarPagamento(contaId, valorPendente, true);
                  }
              });
          }
      });
  });
  // Adicione esta função para configurar os eventos dos botões de pagamento
  function setupPagamentoButtons() {
      // Botão Pagamento Parcial
      const btnParcial = document.querySelector('#formPagamentoConta button[type="submit"]');
      if (btnParcial) {
          btnParcial.addEventListener('click', function(e) {
              e.preventDefault();
              openModal('modalPagamentoParcial');
          });
      }

      // Confirmar pagamento parcial
      const btnConfirmarParcial = document.getElementById('btnConfirmarParcial');
      if (btnConfirmarParcial) {
          btnConfirmarParcial.addEventListener('click', function() {
              const contaId = document.getElementById('contaIdPagamento').value;
              const valor = parseFloat(document.getElementById('valorParcialInput').value);
              const valorPendenteText = document.getElementById('detalheValorPendente').textContent;
              const valorPendente = parseFloat(valorPendenteText.replace(/[^\d,]/g, '').replace(',', '.'));

              if (isNaN(valor) || valor <= 0) {
                  showFlashMessage('error', 'Informe um valor válido');
                  return;
              }
              if (valor > valorPendente) {
                  showFlashMessage('error', 'Valor informado é maior que o pendente');
                  return;
              }

              closeModal('modalPagamentoParcial');
              registrarPagamento(contaId, valor);
          });
      }

      // Botão Pagar Total (sem alterações)
      const btnPagarTotal = document.getElementById('btnPagarTotal');
      if (btnPagarTotal) {
          btnPagarTotal.addEventListener('click', function() {
              const contaId = document.getElementById('contaIdPagamento').value;
              const valorPendenteText = document.getElementById('detalheValorPendente').textContent;
              const valorPendente = parseFloat(valorPendenteText.replace(/[^\d,]/g, '').replace(',', '.'));

              if (confirm(`Confirmar pagamento total de ${valorPendenteText}?`)) {
                  document.getElementById('valorPagamento').value = valorPendente;
                  registrarPagamento(contaId, valorPendente, true);
              }
          });
      }
  }

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
            row.classList.add('desconto-row');
            row.setAttribute('data-id', desconto.id);
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
          
          // Adiciona evento de clique nas linhas da tabela
          document.querySelectorAll('.desconto-row').forEach(row => {
            row.addEventListener('click', function(e) {
              // Evita abrir o modal se o clique foi em um botão de ação
              if (!e.target.closest('.table-actions')) {
                const descontoId = this.getAttribute('data-id');
                openProdutosDescontoModal(descontoId);
              }
            });
          });
        }
      }
    } catch (error) {
      console.error('Erro ao carregar descontos:', error);
      showFlashMessage('error', 'Erro ao carregar lista de descontos');
    }
  }

  async function openProdutosDescontoModal(descontoId) {
    try {
      // Busca os dados do desconto
      const responseDesconto = await fetchWithErrorHandling(`/admin/descontos/${descontoId}`);
      
      if (responseDesconto.success) {
        const desconto = responseDesconto.desconto;
        
        // Preenche as informações do desconto
        document.getElementById('descontoInfoIdentificador').textContent = desconto.identificador || '-';
        document.getElementById('descontoInfoDescricao').textContent = desconto.descricao || '-';
        document.getElementById('descontoInfoValidade').textContent = desconto.valido_ate || '-';
        
        const statusElement = document.getElementById('descontoInfoStatus');
        statusElement.textContent = desconto.ativo ? 'Ativo' : 'Inativo';
        statusElement.className = desconto.ativo ? 'badge badge-success' : 'badge badge-danger';
        
        // Busca os produtos associados a este desconto
        const responseProdutos = await fetchWithErrorHandling(`/admin/descontos/${descontoId}/produtos`);
        
        const tableBody = document.querySelector('#produtosDescontoTable tbody');
        tableBody.innerHTML = '';
        
        if (responseProdutos.success && responseProdutos.produtos && responseProdutos.produtos.length > 0) {
          responseProdutos.produtos.forEach(produto => {
            const row = document.createElement('tr');
            row.innerHTML = `
              <td>${produto.codigo || '-'}</td>
              <td>${produto.nome || '-'}</td>
              <td>${produto.tipo || '-'}</td>
              <td><span class="badge ${produto.ativo ? 'badge-success' : 'badge-danger'}">${produto.ativo ? 'Ativo' : 'Inativo'}</span></td>
            `;
            tableBody.appendChild(row);
          });
        } else {
          tableBody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhum produto associado a este desconto</td></tr>';
        }
        
        // Atualiza o título do modal
        document.getElementById('produtosDescontoModalTitle').textContent = `Produtos do Desconto: ${desconto.identificador}`;
        
        // Abre o modal
        openModal('produtosDescontoModal');
      } else {
        showFlashMessage('error', responseDesconto.erro || 'Erro ao carregar dados do desconto');
      }
    } catch (error) {
      console.error('Erro ao carregar produtos do desconto:', error);
      showFlashMessage('error', 'Erro ao carregar produtos do desconto');
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
  setupClienteActions();
  setupFormasPagamentoEvents();
  
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
        if (tabId === 'relatorio-saidas') {
          loadRelatorioSaidasData();
          loadCategoriasProdutos();
        }
        if (tabId === 'contas-receber') loadContasReceber();
      }
    } catch (error) {
      console.error('Erro ao carregar dados iniciais:', error);
    }
  }

  loadInitialData();
});