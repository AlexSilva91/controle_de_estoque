document.addEventListener('DOMContentLoaded', () => {
  const tabela = document.querySelector('#tabela tbody');
  const totalEl = document.getElementById('total');
  const produtoEl = document.getElementById('produto');
  const dataInicioEl = document.getElementById('data_inicio');
  const dataFimEl = document.getElementById('data_fim');
  const btnAplicar = document.getElementById('btnAplicar');
  const btnLimpar = document.getElementById('btnLimpar');
  const prevPageBtn = document.getElementById('prevPage');
  const nextPageBtn = document.getElementById('nextPage');
  const paginaAtualEl = document.getElementById('paginaAtual');
  const totalPaginasEl = document.getElementById('totalPaginas');

  let paginaAtual = 1;
  let totalPaginas = 1;

  function parseNumber(str) {
    if (!str) return 0;
    return parseFloat(str.replace(',', '.')) || 0;
  }

  async function fetchLotes(pagina = 1) {
    let params = new URLSearchParams();
    params.append('pagina', pagina);

    if (produtoEl.value) {
      params.append('produto_id', produtoEl.value);
    }
    
    // Adiciona horário ao enviar data_inicio
    if (dataInicioEl.value) {
      const dataInicio = dataInicioEl.value + ' 00:00:00';
      params.append('data_inicio', dataInicio);
      console.log('Data início enviada:', dataInicio);
    }
    
    // Adiciona horário ao enviar data_fim
    if (dataFimEl.value) {
      const dataFim = dataFimEl.value + ' 23:59:59';
      params.append('data_fim', dataFim);
      console.log('Data fim enviada:', dataFim);
    }

    try {
      const url = '/admin/api/lotes?' + params.toString();
      console.log('URL requisitada:', url);
      
      const response = await fetch(url);
      const data = await response.json();
      
      console.log('Dados recebidos da API:', data);

      const lotesArray = Array.isArray(data.lotes) ? data.lotes : [];
      renderLotes(lotesArray);

      // Atualiza paginação
      paginaAtual = data.paginacao?.pagina_atual || 1;
      totalPaginas = data.paginacao?.total_paginas || 1;
      paginaAtualEl.textContent = paginaAtual;
      totalPaginasEl.textContent = totalPaginas;

      prevPageBtn.disabled = paginaAtual <= 1;
      nextPageBtn.disabled = paginaAtual >= totalPaginas;

    } catch (err) {
      console.error('Erro ao buscar lotes:', err);
    }
  }

  function renderLotes(lotes) {
    tabela.innerHTML = '';
    
    if (lotes.length === 0) {
      tabela.innerHTML = `
        <tr>
          <td colspan="7" class="empty-state">
            Nenhum lote encontrado com os filtros aplicados
          </td>
        </tr>
      `;
      totalEl.textContent = '0';
      return;
    }
    
    lotes.forEach(lote => {
      const quantidade_inicial = parseNumber(lote.quantidade_inicial);
      const quantidade_disponivel = parseNumber(lote.quantidade_disponivel);
      const valor_unitario = parseNumber(lote.valor_unitario_compra);

      // Formata a data com hora
      const dataEntrada = new Date(lote.data_entrada);
      const dataFormatada = dataEntrada.toLocaleDateString('pt-BR') + ' ' + 
                            dataEntrada.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

      // Badge de status colorido
      const statusBadge = lote.status === 'ativo' 
        ? '<span style="color: var(--success-color); font-weight: 600;">✓ Ativo</span>'
        : '<span style="color: var(--text-muted); font-weight: 600;">✗ Inativo</span>';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${dataFormatada}</td>
        <td style="font-weight: 500;">${lote.produto_nome || '—'}</td>
        <td>${quantidade_inicial.toFixed(2)}</td>
        <td><strong style="color: var(--secondary-color);">${quantidade_disponivel.toFixed(2)}</strong></td>
        <td style="color: var(--warning-color);">R$ ${valor_unitario.toFixed(2)}</td>
        <td>${statusBadge}</td>
        <td style="color: var(--text-muted); font-style: italic;">${lote.observacao || '—'}</td>
      `;
      tabela.appendChild(tr);
    });
    totalEl.textContent = lotes.length;
  }

  btnAplicar.addEventListener('click', () => fetchLotes(1));

  btnLimpar.addEventListener('click', () => {
    produtoEl.value = '';
    dataInicioEl.value = '';
    dataFimEl.value = '';
    fetchLotes(1);
  });

  prevPageBtn.addEventListener('click', () => {
    if (paginaAtual > 1) fetchLotes(paginaAtual - 1);
  });

  nextPageBtn.addEventListener('click', () => {
    if (paginaAtual < totalPaginas) fetchLotes(paginaAtual + 1);
  });

  // Carrega dados iniciais
  fetchLotes(1);
});