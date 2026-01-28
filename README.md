# 🧾 Sistema de Gestão de Vendas e Caixa

Sistema web completo para **gerenciamento de vendas, clientes, produtos e controle de caixa**, desenvolvido em **Flask (Python)** com front-end em **HTML, CSS e JavaScript**.  
Projetado para uso em lojas e pequenos comércios, oferece controle financeiro, relatórios e interface responsiva.

---

## 📦 Funcionalidades Principais

- 💰 **Controle de Caixa**
  - Abertura, fechamento e saldo em tempo real.
  - Registro automático de movimentações financeiras.
  - Controle de permissões para operadores e administradores.

- 👥 **Gestão de Clientes**
  - Cadastro, edição e busca.
  - Histórico de vendas por cliente.

- 📦 **Gestão de Produtos e Estoque**
  - Cadastro e atualização de produtos.
  - Controle de estoque com atualização automática por venda.

- 🧾 **Vendas**
  - Registro de múltiplos produtos por venda.
  - Suporte a várias formas de pagamento (Dinheiro, Pix, Cartão, etc.).
  - Emissão de comprovantes e integração futura com NFC-e.

- 🔔 **Notificações**
  - Feedback visual para ações (cadastro, erro, sucesso).
  - Sistema de abas para navegação fluida entre módulos.

---

## 🧰 Tecnologias Utilizadas

| Camada | Tecnologias |
| --- | --- |
| **🎨 Front-end** | ![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white) ![CSS3](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white) ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black) |
| **⚙️ Back-end** | ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white) |
| **🗄️ Banco de Dados** | ![MySQL](https://img.shields.io/badge/MySQL-4479A1?logo=mysql&logoColor=white) |
| **🔌 APIs** | ![REST](https://img.shields.io/badge/REST-009688?logo=fastapi&logoColor=white) Flask Blueprint (`operador`, `admin`, `auth`, `fiscal`) |
| **🧩 Outros** | ![Fetch API](https://img.shields.io/badge/Fetch_API-303030?logo=javascript&logoColor=white) ![Jinja2](https://img.shields.io/badge/Jinja2-B41717?logo=jinja&logoColor=white) ![ReportLab](https://img.shields.io/badge/ReportLab-FF6F00?logo=python&logoColor=white) ![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white) ![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white) |

---

## 🗂️ Estrutura do Projeto

```bash
controle_de_estoque
├─ README.md
├─ app
│  ├─ __init__.py
│  ├─ bot
│  │  ├─ __init__.py
│  │  └─ bot_movimentacao.py
│  ├─ database.py
│  ├─ decorators
│  │  ├─ __init__.py
│  │  └─ decorators.py
│  ├─ init_db.py
│  ├─ integrations
│  │  ├─ __init__.py
│  │  └─ fiscal_api
│  │     ├─ __init__.py
│  │     ├─ client.py
│  │     └─ service.py
│  ├─ models
│  │  ├─ __init__.py
│  │  ├─ audit_events.py
│  │  ├─ audit_mixin.py
│  │  ├─ base.py
│  │  ├─ entities.py
│  │  └─ fiscal_models.py
│  ├─ routes
│  │  ├─ __init__.py
│  │  ├─ admin.py
│  │  ├─ admin_fiscal.py
│  │  ├─ auth.py
│  │  ├─ home.py
│  │  └─ operador.py
│  ├─ schemas.py
│  ├─ services
│  │  ├─ cliente_fiscal_crud.py
│  │  ├─ crud.py
│  │  └─ fiscal_crud.py
│  ├─ static
│  │  ├─ assets
│  │  │  ├─ clients_icon.png
│  │  │  ├─ clients_icon2.png
│  │  │  ├─ logo.jpeg
│  │  │  ├─ logo1.ico
│  │  │  ├─ logo1.jpeg
│  │  │  ├─ logo2.jpeg
│  │  │  ├─ logout.png
│  │  │  ├─ money_icon.png
│  │  │  ├─ product_icon.png
│  │  │  ├─ product_icon2.png
│  │  │  ├─ products_icon.png
│  │  │  ├─ sales_icon.png
│  │  │  └─ user_icon.png
│  │  ├─ css
│  │  │  ├─ formas_pagamento.css
│  │  │  ├─ lotes.css
│  │  │  ├─ style.css
│  │  │  ├─ style_dashboard_fiscal.css
│  │  │  ├─ style_login.css
│  │  │  └─ styles_operador.css
│  │  └─ js
│  │     ├─ auditoria.js
│  │     ├─ dashboard_fiscal.js
│  │     ├─ lotes.js
│  │     ├─ script.js
│  │     ├─ script_contas_usuario.js
│  │     ├─ script_formas_pagamento.js
│  │     ├─ script_login.js
│  │     ├─ script_lotes.js
│  │     └─ script_operador.js
│  ├─ templates
│  │  ├─ auditoria.html
│  │  ├─ contas_usuario.html
│  │  ├─ dashboard_admin.html
│  │  ├─ dashboard_fiscal.html
│  │  ├─ dashboard_operador.html
│  │  ├─ errors
│  │  │  ├─ 400.html
│  │  │  ├─ 403.html
│  │  │  ├─ 404.html
│  │  │  ├─ 500.html
│  │  │  └─ 503.html
│  │  ├─ financeiro_historico.html
│  │  ├─ formas_pagamento.html
│  │  ├─ login.html
│  │  ├─ lotes.html
│  │  ├─ produtos_unidade.html
│  │  ├─ relatorio_contasReceber.html
│  │  └─ upload_xml.html
│  └─ utils
│     ├─ audit.py
│     ├─ calcularNOvoValor.py
│     ├─ conversor_unidade.py
│     ├─ converter_endereco.py
│     ├─ fiscal
│     │  ├─ __init__.py
│     │  ├─ helpers.py
│     │  └─ nfe_template.py
│     ├─ format_data_moeda.py
│     ├─ nfce.py
│     ├─ preparar_notas.py
│     ├─ signature.py
│     └─ upload.py
├─ backup_db.py
├─ config.py
├─ docs
│  └─ DOCUMENTACAO_TECNICA.md
├─ requirements.txt
├─ run.py
└─ wsgi.py
```

---

## ⚙️ Instalação e Execução

### ✅ Pré-requisitos

- Python 3.8+
- Ambiente virtual configurado
- Dependências listadas em `requirements.txt`

### 🚀 Passos de Execução

1. **Clone o repositório**

   ```bash
   git clone git@github.com:AlexSilva91/controle_de_estoque.git
   cd controle_de_estoque
   ```

2. **Crie e ative um ambiente virtual**

   ```bash
   python3 -m venv venv
   source venv/bin/activate     # Linux/macOS
   venv\Scripts\activate      # Windows
   ```

3. **Instale as dependências**

   ```bash
   pip install -r requirements.txt
   ```

4. **Execute o servidor**

   ```bash
   flask run # ou python3 wsgi.py
   ```

5. **Acesse no navegador**

   ```bash
   http://127.0.0.1:5000/
   ```

---

## 🧭 Uso do Sistema

1. **Login:** Acesse com credenciais de operador ou administrador.  
2. **Navegação:** Utilize as abas da interface para acessar Clientes, Produtos e Caixa.  
3. **Clientes:** Cadastre, edite e busque clientes com feedback visual.  
4. **Produtos:** Gerencie estoque e preços.  
5. **Vendas:** Adicione produtos à venda, selecione o cliente e forma de pagamento.  
6. **Caixa:** Monitore o saldo em tempo real e feche o caixa ao final do expediente.  

---

## 🧩 Boas Práticas e Padrões Adotados

- **Blueprints Flask:** organização modular de rotas e lógicas.  
- **ORM SQLAlchemy:** abstração de banco relacional com mapeamento de entidades.  
- **Fetch API:** comunicação assíncrona com endpoints REST.  
- **Design Responsivo:** interface adaptável via CSS modular.  
- **Separação de Responsabilidades:** camadas independentes (rotas, modelos, utilitários).

---

## 🧪 Extensões Futuras

- Integração com **NFC-e (Nota Fiscal de Consumidor Eletrônica)**.  
- Geração de **relatórios em PDF** para vendas e movimentações.  
- Módulo de **controle de estoque automatizado**.  
- Dashboards com **gráficos interativos**.  
- Sistema de **autorização por níveis de acesso** (RBAC).  

---

## 📞 Contato

- **Autor:** Alex da Silva Alves
- **Email:** <alexalves9164@gmail.com>  
- **GitHub:** [github.com/AlexSilva91](https://github.com/AlexSilva91)

---

## ⚖️ Licença

Distribuído sob a **MIT License**.  
Você pode usar, modificar e distribuir livremente com os devidos créditos.
