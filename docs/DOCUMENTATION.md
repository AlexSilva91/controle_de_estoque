# 📦 Script de Alterações no Banco de Dados

Este documento descreve todas as modificações realizadas nas tabelas do banco de dados, atualizando valores possíveis de colunas `ENUM` e definindo valores padrão quando aplicável.

---

## 1️⃣ **Tabela `caixas`** — Coluna `status`
```sql
ALTER TABLE caixas 
MODIFY COLUMN status ENUM('aberto', 'fechado', 'em_analise', 'recusado') NOT NULL DEFAULT 'aberto';
2️⃣ Tabela usuarios — Coluna tipo
sql
Copy
Edit
ALTER TABLE usuarios 
MODIFY COLUMN tipo ENUM('admin', 'operador') NOT NULL;
3️⃣ Tabela movimentacoes_estoque — Coluna tipo
sql
Copy
Edit
ALTER TABLE movimentacoes_estoque 
MODIFY COLUMN tipo ENUM('entrada', 'saida', 'saida_estorno', 'transferencia') NOT NULL;
4️⃣ Tabela notas_fiscais — Coluna status
sql
Copy
Edit
ALTER TABLE notas_fiscais 
MODIFY COLUMN status ENUM('emitida', 'cancelada') NOT NULL DEFAULT 'emitida';
5️⃣ Tabela financeiro — Coluna categoria
sql
Copy
Edit
ALTER TABLE financeiro 
MODIFY COLUMN categoria ENUM(
    'venda',
    'compra',
    'despesa',
    'estorno',
    'salario',
    'outro',
    'abertura_caixa',
    'fechamento_caixa'
) NOT NULL;
6️⃣ Tabela financeiro — Coluna tipo
sql
Copy
Edit
ALTER TABLE financeiro 
MODIFY COLUMN tipo ENUM('entrada', 'saida', 'saida_estorno', 'transferencia') NOT NULL;
7️⃣ Tabela pagamentos_nota_fiscal — Coluna forma_pagamento
sql
Copy
Edit
ALTER TABLE pagamentos_nota_fiscal 
MODIFY COLUMN forma_pagamento ENUM(
    'pix_fabiano',
    'pix_maquineta',
    'pix_edfrance',
    'pix_loja',
    'dinheiro',
    'cartao_credito',
    'cartao_debito',
    'a_prazo'
) NOT NULL;
8️⃣ Tabela produtos — Coluna unidade
sql
Copy
Edit
ALTER TABLE produtos 
MODIFY COLUMN unidade ENUM('kg', 'saco', 'unidade', 'fardo', 'pacote') NOT NULL DEFAULT 'kg';
9️⃣ Tabela descontos — Coluna tipo
sql
Copy
Edit
ALTER TABLE descontos 
MODIFY COLUMN tipo ENUM('fixo', 'percentual') NOT NULL;
🔟 Tabela contas_receber — Coluna status
sql
Copy
Edit
ALTER TABLE contas_receber 
MODIFY COLUMN status ENUM('pendente', 'parcial', 'quitado') NOT NULL DEFAULT 'pendente';
1️⃣1️⃣ Tabela pagamentos_contas_receber — Coluna forma_pagamento
sql
Copy
Edit
ALTER TABLE pagamentos_contas_receber 
MODIFY COLUMN forma_pagamento ENUM(
    'pix_fabiano',
    'pix_maquineta',
    'pix_edfrance',
    'pix_loja',
    'dinheiro',
    'cartao_credito',
    'cartao_debito',
    'a_prazo'
) NOT NULL;
📜 Script Completo em Sequência
sql
Copy
Edit
ALTER TABLE caixas 
MODIFY COLUMN status ENUM('aberto', 'fechado', 'em_analise', 'recusado') NOT NULL DEFAULT 'aberto';

ALTER TABLE usuarios 
MODIFY COLUMN tipo ENUM('admin', 'operador') NOT NULL;

ALTER TABLE movimentacoes_estoque 
MODIFY COLUMN tipo ENUM('entrada', 'saida', 'saida_estorno', 'transferencia') NOT NULL;

ALTER TABLE notas_fiscais 
MODIFY COLUMN status ENUM('emitida', 'cancelada') NOT NULL DEFAULT 'emitida';

ALTER TABLE financeiro 
MODIFY COLUMN categoria ENUM('venda', 'compra', 'despesa', 'estorno', 'salario', 'outro', 'abertura_caixa', 'fechamento_caixa') NOT NULL;

ALTER TABLE financeiro 
MODIFY COLUMN tipo ENUM('entrada', 'saida', 'saida_estorno', 'transferencia') NOT NULL;

ALTER TABLE pagamentos_nota_fiscal 
MODIFY COLUMN forma_pagamento ENUM('pix_fabiano', 'pix_maquineta', 'pix_edfrance', 'pix_loja', 'dinheiro', 'cartao_credito', 'cartao_debito', 'a_prazo') NOT NULL;

ALTER TABLE produtos 
MODIFY COLUMN unidade ENUM('kg', 'saco', 'unidade', 'fardo', 'pacote') NOT NULL DEFAULT 'kg';

ALTER TABLE descontos 
MODIFY COLUMN tipo ENUM('fixo', 'percentual') NOT NULL;

ALTER TABLE contas_receber 
MODIFY COLUMN status ENUM('pendente', 'parcial', 'quitado') NOT NULL DEFAULT 'pendente';

ALTER TABLE pagamentos_contas_receber 
MODIFY COLUMN forma_pagamento ENUM('pix_fabiano', 'pix_maquineta', 'pix_edfrance', 'pix_loja', 'dinheiro', 'cartao_credito', 'cartao_debito', 'a_prazo') NOT NULL;
