# 🧠 Documentação Técnica — Sistema Cavalcanti Rações

## 📋 Sumário
1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Modelos ORM (SQLAlchemy)](#modelos-orm-sqlalchemy)
   - [Usuário (`Usuario`)](#usuário-usuario)
   - [Caixa (`Caixa`)](#caixa-caixa)
   - [Conta e Movimentação Financeira](#conta-e-movimentação-financeira)
   - [Produtos, Lotes e Estoque](#produtos-lotes-e-estoque)
   - [Nota Fiscal e Itens](#nota-fiscal-e-itens)
   - [Clientes e Contas a Receber](#clientes-e-contas-a-receber)
   - [Financeiro e Logs](#financeiro-e-logs)
4. [Rotas Administrativas (Blueprint `admin_bp`)](#rotas-administrativas-blueprint-admin_bp)
   - [Dashboard](#dashboard)
   - [Controle de Caixa](#controle-de-caixa)
   - [Gestão de Clientes](#gestão-de-clientes)
5. [Classes Utilitárias e Configuração](#classes-utilitárias-e-configuração)

---

## 📘 Visão Geral
Sistema ERP desenvolvido em **Flask + SQLAlchemy**, com foco em controle financeiro e estoque.

Principais módulos:
- Controle de vendas e notas fiscais
- Gerenciamento de caixas e aprovação administrativa
- Controle de produtos e estoque
- Contas a receber e pagamentos
- Geração de relatórios PDF via **ReportLab**

---

## ⚙️ Arquitetura do Sistema
- **Backend:** Flask + SQLAlchemy  
- **Banco:** PostgreSQL/MySQL (compatível)  
- **ORM Base:** `Base` herdada de `declarative_base()`  
- **Autenticação:** Flask-Login  
- **Enumerações:** modelam estados e tipos de operação (e.g. `StatusCaixa`, `TipoMovimentacao`, `FormaPagamento`)  
- **Relações:** 1:1, 1:N e N:N com `back_populates` e `cascade`

---

## 🧩 Modelos ORM (SQLAlchemy)

### Usuário (`Usuario`)
Representa operadores e administradores do sistema.

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id` | `Integer` | Identificador único |
| `nome` | `String(100)` | Nome completo |
| `cpf` | `String(14)` | Único por usuário |
| `senha_hash` | `Text` | Hash da senha |
| `tipo` | `Enum(TipoUsuario)` | `admin` ou `operador` |
| `ultimo_acesso` | `DateTime` | Último login registrado |
| `status` | `Boolean` | Ativo/Inativo |
| `conta` | relação 1:1 com `Conta` |
| `caixas_operados` / `caixas_analisados` | relacionamento duplo com `Caixa` |

---

### Caixa (`Caixa`)
Controla sessões de caixa com aprovação e histórico.

| Campo | Tipo | Descrição |
|--------|------|-----------|
| `status` | `Enum(StatusCaixa)` | aberto, em_analise, fechado, recusado |
| `valor_abertura` | `DECIMAL(12,2)` | Valor inicial |
| `valor_fechamento` | `DECIMAL(12,2)` | Valor declarado no fechamento |
| `valor_confirmado` | `DECIMAL(12,2)` | Valor após auditoria |
| `operador_id` | FK → `Usuario` | Operador responsável |
| `administrador_id` | FK → `Usuario` | Aprovador do fechamento |

#### Métodos principais
- `fechar_caixa()`: marca como `em_analise` e cria lançamento financeiro pendente  
- `aprovar_fechamento()`: confirma e registra valor validado  
- `rejeitar_fechamento()`: retorna status para `recusado` e remove lançamento  
- `reabrir_caixa()`: permite nova sessão a partir de um caixa fechado

---

### Conta e Movimentação Financeira

#### `Conta`
Gerencia saldo total e por forma de pagamento.

```python
class Conta(Base):
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    saldo_total = Column(DECIMAL(12, 2), default=0.00)
```

#### `SaldoFormaPagamento`
Subdivisão de saldo por tipo de pagamento.

```python
class SaldoFormaPagamento(Base):
    conta_id = Column(Integer, ForeignKey("contas.id"))
    forma_pagamento = Column(Enum(FormaPagamento))
    saldo = Column(DECIMAL(12, 2), default=0.00)
```

#### `MovimentacaoConta`
Histórico de entradas e saídas associadas à conta.

---

### Produtos, Lotes e Estoque

#### `Produto`
Define as propriedades dos produtos cadastrados.

- Campos: `codigo`, `nome`, `unidade`, `valor_unitario`, `estoque_loja/deposito/fabrica`
- Método: `gerar_codigo_sequencial()` para preenchimento automático de lacunas numéricas

#### `LoteEstoque`
Controla quantidades, datas e custos de entrada de mercadorias.

---

### Nota Fiscal e Itens

#### `NotaFiscal`
Registra operações de venda.

- Campos: `cliente_id`, `operador_id`, `caixa_id`, `valor_total`, `status`
- Método: `obter_vendas_do_dia()` retorna notas emitidas no dia corrente

#### `NotaFiscalItem`
Detalhes individuais de cada produto faturado.

---

### Clientes e Contas a Receber

#### `Cliente`
Dados cadastrais e relacionamentos com notas e contas.

#### `ContaReceber`
Gerencia cobranças, status e pagamentos associados.

```python
def registrar_pagamento(self, valor_pago, forma_pagamento, caixa_id=None, observacoes=None):
    # Atualiza valores e gera movimentação financeira
```

---

### Financeiro e Logs

#### `Financeiro`
Centraliza todas as transações financeiras.

| Campo | Tipo | Descrição |
|--------|------|-----------|
| `tipo` | `Enum(TipoMovimentacao)` | entrada/saída |
| `categoria` | `Enum(CategoriaFinanceira)` | tipo de operação |
| `valor` | `DECIMAL(12,2)` | valor movimentado |
| `descricao` | `Text` | observação |
| `data` | `DateTime` | registro temporal |

#### `AuditLog`
Log de auditoria das tabelas principais (insert/update/delete).

---

## 🔐 Rotas Administrativas (Blueprint `admin_bp`)

### Dashboard
| Rota | Método | Descrição |
|-------|--------|------------|
| `/dashboard` | GET | Página principal |
| `/dashboard/metrics` | GET | Resumo financeiro e estoque |
| `/dashboard/vendas-diarias` | GET | Gráfico de vendas diárias |
| `/dashboard/vendas-mensais` | GET | Dados mensais de vendas/despesas |
| `/dashboard/movimentacoes` | GET | Últimas movimentações |
| `/dashboard/produtos-maior-fluxo` | GET | Top 10 produtos mais vendidos |

### Controle de Caixa
| Rota | Método | Descrição |
|-------|--------|------------|
| `/caixa/abrir` | POST | Abertura de caixa |
| `/caixa/fechar` | POST | Envio para análise |
| `/caixa/status` | GET | Consulta caixa atual |
| `/caixa/historico` | GET | Histórico completo |

### Gestão de Clientes
| Rota | Método | Descrição |
|-------|--------|------------|
| `/clientes` | GET | Listagem |
| `/clientes/<id>` | PUT | Atualização |
| `/clientes/<id>/detalhes` | GET | Histórico detalhado |

---

## ⚙️ Classes Utilitárias e Configuração

### `Configuracao`
Define parâmetros globais do sistema.

```python
class Configuracao(Base):
    permitir_venda_sem_estoque = Column(Boolean, default=False)
```

Método `get_config(session)` garante a persistência de uma configuração padrão.

---

© 2025 Cavalcanti Rações — Documento gerado automaticamente a partir do código-fonte.
