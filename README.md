
# Sistema de Gestão de Vendas e Caixa

Este projeto é um sistema web para gerenciamento de vendas, clientes, produtos e controle de caixa, desenvolvido com front-end em HTML, CSS, JavaScript e back-end em Flask (Python). 

## Funcionalidades

- Visualização e atualização dinâmica do saldo do caixa.
- Cadastro, edição e busca de clientes.
- Listagem e atualização dinâmica de produtos com estoque.
- Registro de vendas com múltiplos produtos e métodos de pagamento.
- Controle de caixa com opção para fechamento.
- Notificações para feedbacks de operações.
- Interface com abas para melhor organização das funcionalidades.

## Tecnologias Utilizadas

- **Front-end:** HTML5, CSS3, JavaScript (ES6)
- **Back-end:** Python 3.x com Flask
- **APIs:** Endpoints REST para clientes, produtos, vendas e saldo
- **Outros:** Fetch API para comunicação assíncrona, FontAwesome para ícones

## Estrutura do Projeto

```
/
├── app/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   ├── __init__.py
│   ├── routes.py
│   └── ...
├── README.md
├── requirements.txt
└── run.py
```

## Como Executar o Projeto

### Pré-requisitos

- Python 3.x instalado
- Ambiente virtual configurado (recomendado)
- Instalar dependências do projeto

### Passos

1. Clone o repositório:
```bash
git clone https://github.com/seu_usuario/seu_repositorio.git
cd seu_repositorio
```

2. Crie e ative um ambiente virtual:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate   # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute o servidor Flask:
```bash
flask run
```

5. Acesse no navegador:
```
http://127.0.0.1:5000/
```

## Uso

- Utilize as abas para navegar entre clientes, produtos e vendas.
- Cadastre e edite clientes usando o modal disponível.
- Adicione produtos na venda, defina quantidades e selecione o cliente e forma de pagamento.
- Registre vendas e acompanhe o saldo do caixa em tempo real.
- Feche o caixa ao final do expediente para registrar o encerramento.

## Endpoints Disponíveis

- `GET /operador/api/saldo` - Obtém o saldo atual do caixa.
- `GET /operador/api/clientes` - Lista todos os clientes.
- `POST /operador/api/clientes` - Cria um novo cliente.
- `PUT /operador/api/clientes/<id>` - Atualiza um cliente existente.
- `GET /operador/api/produtos` - Lista todos os produtos.
- `POST /operador/api/vendas` - Registra uma nova venda.
- `POST /operador/api/fechar-caixa` - Realiza o fechamento do caixa.

## Considerações Finais

Este sistema é uma base para gerenciamento de vendas e controle de caixa simples, com possibilidade de expansão para novas funcionalidades conforme necessidade.

## Contato

Para dúvidas ou sugestões, abra uma issue ou entre em contato:

- Email: alexalves9164@gmail.com
- GitHub: https://github.com/AlexSilva91/

---

**Licença:** MIT License

