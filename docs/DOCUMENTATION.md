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



FLUXO DE CRIAÇÃO DA CONTA
1. Criação Automática:

Quando um usuário é criado no sistema, uma conta é automaticamente criada para ele

Relacionamento 1:1 → 1 usuário = 1 conta

A conta nasce com saldo total zero e sem saldos por forma de pagamento

FLUXO DE MOVIMENTAÇÕES
2. Para toda movimentação financeira, o fluxo é:

ENTRADA (Venda, Recebimento):

text
1. Usuário realiza ação que gera entrada (ex: venda)
2. Sistema identifica a conta do usuário
3. Sistema identifica a forma de pagamento (PIX, dinheiro, cartão)
4. REGISTRA movimentação do tipo "entrada"
5. ATUALIZA saldo total da conta (+ valor)
6. ATUALIZA saldo específico da forma de pagamento (+ valor)
SAÍDA (Despesa, Pagamento):

text
1. Usuário realiza ação que gera saída (ex: pagamento)
2. Sistema verifica se há saldo suficiente na forma de pagamento
3. Se tiver saldo: REGISTRA movimentação do tipo "saída"
4. ATUALIZA saldo total da conta (- valor)
5. ATUALIZA saldo específico da forma de pagamento (- valor)
TRANSFERÊNCIA (Entre formas de pagamento):

text
1. Usuário quer transferir valor entre formas (ex: dinheiro → PIX)
2. Sistema verifica saldo na forma de ORIGEM
3. Se tiver saldo: REGISTRA DUAS movimentações:
   - SAÍDA da forma origem
   - ENTRADA na forma destino
4. Saldo total da conta PERMANECE O MESMO
5. Saldo da forma origem DIMINUI
6. Saldo da forma destino AUMENTA
FLUXO DE CONSULTA
3. Para ver saldos:

text
1. Sistema busca a conta do usuário
2. Retorna:
   - Saldo total (soma de todas as formas)
   - Saldo individual por forma de pagamento
   - Histórico completo de movimentações
REGRAS IMPORTANTES
Toda movimentação é auditável - fica registrado quem fez, quando, quanto e por quê

Saldos são sempre calculados em tempo real - não precisa somar histórico

Uma conta pode ter saldo negativo em uma forma se houver estornos

O saldo total é a soma matemática de todos os saldos por forma

EXEMPLO PRÁTICO
text
CONTA DO JOÃO:
- Saldo total: R$ 1.500,00
- Dinheiro: R$ 500,00
- PIX: R$ 800,00  
- Cartão: R$ 200,00

João faz uma venda de R$ 100 no PIX:
1. Registra entrada de R$ 100 no PIX
2. Saldo total vai para R$ 1.600,00
3. Saldo PIX vai para R$ 900,00

João paga uma conta de R$ 200 no dinheiro:
1. Verifica se tem R$ 200 no dinheiro ✓
2. Registra saída de R$ 200 no dinheiro  
3. Saldo total vai para R$ 1.400,00
4. Saldo dinheiro vai para R$ 300,00
Resumo: Cada usuário tem UMA conta, mas essa conta tem MÚLTIPLOS "cofrinhos" (formas de pagamento) com saldos individuais, e todo movimento é registrado para auditoria.