    const API_BASE_URL = '/admin';
    let paginaAtual = 1;
    let debounceTimer;
    let produtosSelecionados = [];

    document.addEventListener('DOMContentLoaded', function() {
        configurarBuscaRealTime();
        configurarFiltros();
        carregarLotes();
    });

    function configurarBuscaRealTime() {
        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');

        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            clearTimeout(debounceTimer);
            if (query.length < 2) { searchResults.style.display = 'none'; return; }

            debounceTimer = setTimeout(() => {
                fetch(`${API_BASE_URL}/produtos?search=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.success && data.produtos.length > 0) {
                            exibirResultadosBusca(data.produtos);
                        } else {
                            searchResults.innerHTML = '<div class="search-item">Nenhum produto encontrado</div>';
                            searchResults.style.display = 'block';
                        }
                    })
                    .catch(err => console.error('Erro na busca:', err));
            }, 300);
        });

        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) searchResults.style.display = 'none';
        });
    }

    function exibirResultadosBusca(produtos) {
        const searchResults = document.getElementById('search-results');
        searchResults.innerHTML = '';
        produtos.forEach(produto => {
            const jaSelecionado = produtosSelecionados.some(p => p.id === produto.id);
            const div = document.createElement('div');
            div.className = 'search-item';
            div.style.opacity = jaSelecionado ? '0.5' : '1';
            div.innerHTML = `<span class="item-nome">${produto.nome} ${jaSelecionado ? '(Adicionado)' : ''}</span><span class="item-info">${produto.tipo}</span>`;
            if (!jaSelecionado) div.onclick = () => adicionarProduto(produto);
            searchResults.appendChild(div);
        });
        searchResults.style.display = 'block';
    }

    function adicionarProduto(produto) {
        produtosSelecionados.push(produto);
        renderizarBadges();
        document.getElementById('search-input').value = '';
        document.getElementById('search-results').style.display = 'none';
        paginaAtual = 1;
        carregarLotes();
    }

    function removerProduto(id) {
        produtosSelecionados = produtosSelecionados.filter(p => p.id !== id);
        renderizarBadges();
        paginaAtual = 1;
        carregarLotes();
    }

    function renderizarBadges() {
        const container = document.getElementById('selected-products-container');
        container.innerHTML = '';
        produtosSelecionados.forEach(p => {
            const badge = document.createElement('div');
            badge.className = 'selected-product-badge';
            badge.innerHTML = `<strong>${p.nome}</strong><button onclick="removerProduto(${p.id})">&times;</button>`;
            container.appendChild(badge);
        });
    }

    function configurarFiltros() {
        document.getElementById('btnAplicar').onclick = () => { paginaAtual = 1; carregarLotes(); };
        document.getElementById('btnLimpar').onclick = () => {
            produtosSelecionados = []; renderizarBadges();
            document.getElementById('data_inicio').value = '';
            document.getElementById('data_fim').value = '';
            paginaAtual = 1; carregarLotes();
        };
        document.getElementById('prevPage').onclick = () => { if (paginaAtual > 1) { paginaAtual--; carregarLotes(); } };
        document.getElementById('nextPage').onclick = () => {
            const total = parseInt(document.getElementById('totalPaginas').textContent);
            if (paginaAtual < total) { paginaAtual++; carregarLotes(); }
        };
    }

    // FUNÇÃO DE BUSCA PARALELA (SIMULANDO MULTITHREADING)
    async function carregarLotes() {
        const dataInicioInput = document.getElementById('data_inicio').value;
        const dataFimInput = document.getElementById('data_fim').value;
        const loading = document.getElementById('loading');
        
        loading.style.display = 'flex';

        try {
            let allLotes = [];
            let totalLotesCount = 0;
            let maxPaginas = 1;

            // REMOVA a conversão UTC e envie com horários
            let dataInicio = dataInicioInput ? `${dataInicioInput} 00:00:00` : '';
            let dataFim = dataFimInput ? `${dataFimInput} 23:59:59` : '';

            // Se não houver produtos selecionados, busca todos
            if (produtosSelecionados.length === 0) {
                const res = await fetch(`${API_BASE_URL}/api/lotes?pagina=${paginaAtual}&data_inicio=${dataInicio}&data_fim=${dataFim}`);
                const data = await res.json();
                allLotes = data.lotes;
                totalLotesCount = data.paginacao.total_lotes;
                maxPaginas = data.paginacao.total_paginas;
            } else {
                // BUSCA SIMULTÂNEA (PARALELA) PARA CADA PRODUTO
                const promises = produtosSelecionados.map(p => 
                    fetch(`${API_BASE_URL}/api/lotes?produto_id=${p.id}&pagina=${paginaAtual}&data_inicio=${dataInicio}&data_fim=${dataFim}`)
                    .then(r => r.json())
                );

                const results = await Promise.all(promises);
                
                // Unifica os resultados de todas as buscas
                results.forEach(data => {
                    if (data.lotes) allLotes = allLotes.concat(data.lotes);
                    totalLotesCount += data.paginacao.total_lotes;
                    if (data.paginacao.total_paginas > maxPaginas) maxPaginas = data.paginacao.total_paginas;
                });

                // Ordena por data de entrada (mais recente primeiro)
                allLotes.sort((a, b) => new Date(b.data_entrada) - new Date(a.data_entrada));
            }

            renderizarTabela(allLotes);
            atualizarPaginacao({
                pagina_atual: paginaAtual,
                total_paginas: maxPaginas,
                total_lotes: totalLotesCount,
                tem_anterior: paginaAtual > 1,
                tem_proxima: paginaAtual < maxPaginas
            });
        } catch (err) {
            console.error('Erro ao carregar lotes:', err);
        } finally {
            loading.style.display = 'none';
        }
    }

    function renderizarTabela(lotes) {
        const tbody = document.querySelector('#tabela tbody');
        tbody.innerHTML = lotes.length === 0 ? '<tr><td colspan="7" style="text-align:center; padding: 40px;">Nenhum lote encontrado</td></tr>' : '';
        lotes.forEach(lote => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${formatarData(lote.data_entrada)}</td>
                <td>${lote.produto_nome || 'N/A'}</td>
                <td>${formatarNumero(lote.quantidade_inicial)}</td>
                <td>${formatarNumero(lote.quantidade_disponivel)}</td>
                <td>R$ ${formatarNumero(lote.valor_unitario_compra)}</td>
                <td><span class="badge ${lote.status}">${lote.status}</span></td>
                <td>${lote.observacao || ''}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function atualizarPaginacao(pag) {
        document.getElementById('paginaAtual').textContent = pag.pagina_atual;
        document.getElementById('totalPaginas').textContent = pag.total_paginas;
        document.getElementById('prevPage').disabled = !pag.tem_anterior;
        document.getElementById('nextPage').disabled = !pag.tem_proxima;
    }

    function formatarData(iso) {
        const d = new Date(iso);
        return d.toLocaleDateString('pt-BR') + ' ' + d.toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit'});
    }

    function formatarNumero(v) {
        return (parseFloat(v) || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }