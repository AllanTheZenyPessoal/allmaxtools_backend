# 🧪 Testes Unitários - Prototype API

Este diretório contém os testes unitários para todos os endpoints da API Prototype.

## 📋 Estrutura dos Testes

```
testes/
├── __init__.py                  # Inicializador do pacote
├── conftest.py                  # Fixtures compartilhadas e configurações
├── test_health.py               # Testes dos endpoints root, health e config
├── test_token.py                # Testes dos endpoints de geração de token
├── test_user.py                 # Testes dos endpoints de usuário
├── test_address.py              # Testes dos endpoints de endereço
├── test_company.py              # Testes dos endpoints de empresa
├── test_branch.py               # Testes dos endpoints de filial
├── test_business_partner.py     # Testes dos endpoints de parceiro de negócios
├── test_freight.py              # Testes dos endpoints de frete
├── test_payment_method.py       # Testes dos endpoints de método de pagamento
├── test_payment_term.py         # Testes dos endpoints de condição de pagamento
├── test_utilization.py          # Testes dos endpoints de utilização
└── test_sales_order.py          # Testes dos endpoints de pedido de venda
```

## 🚀 Como Executar os Testes

### Pré-requisitos

Instale as dependências de teste:

```bash
pip install pytest pytest-cov httpx
```

### Executar todos os testes

```bash
cd backend
pytest testes/ -v
```

### Executar testes de um arquivo específico

```bash
pytest testes/test_user.py -v
```

### Executar testes de uma classe específica

```bash
pytest testes/test_user.py::TestUserLogin -v
```

### Executar um teste específico

```bash
pytest testes/test_user.py::TestUserLogin::test_login_with_valid_credentials -v
```

### Executar com cobertura de código

```bash
pytest testes/ --cov=app --cov-report=html -v
```

O relatório de cobertura será gerado na pasta `htmlcov/`.

### Executar em modo verboso com print

```bash
pytest testes/ -v -s
```

## 📊 Fixtures Disponíveis

As fixtures estão definidas em `conftest.py` e são automaticamente injetadas nos testes.

### Fixtures de Banco de Dados

| Fixture | Descrição |
|---------|-----------|
| `test_db` | Sessão de banco de dados SQLite em memória |
| `client` | Cliente de teste FastAPI |

### Fixtures de Autenticação

| Fixture | Descrição |
|---------|-----------|
| `mock_token` | Token JWT mockado para testes |
| `auth_headers` | Headers de autenticação com Bearer token |

### Fixtures de Usuários

| Fixture | Descrição |
|---------|-----------|
| `superadmin_user` | Usuário superadmin no banco de testes |
| `admin_user` | Usuário admin no banco de testes |
| `regular_user` | Usuário regular no banco de testes |

### Fixtures de Dados Mockados

| Fixture | Descrição |
|---------|-----------|
| `mock_address` | Endereço mockado |
| `mock_company` | Empresa mockada |
| `mock_branch` | Filial mockada |
| `mock_business_partner` | Parceiro de negócios mockado |
| `mock_freight` | Frete mockado |
| `mock_payment_method` | Método de pagamento mockado |
| `mock_payment_term` | Condição de pagamento mockada |
| `mock_utilization` | Utilização mockada |
| `mock_sales_order` | Pedido de venda mockado |

### Fixtures de Payloads

| Fixture | Descrição |
|---------|-----------|
| `address_payload` | Payload para criação de endereço |
| `company_payload` | Payload para criação de empresa |
| `branch_payload` | Payload para criação de filial |
| `business_partner_payload` | Payload para criação de parceiro |
| `freight_payload` | Payload para criação de frete |
| `payment_method_payload` | Payload para criação de método de pagamento |
| `payment_term_payload` | Payload para criação de condição de pagamento |
| `utilization_payload` | Payload para criação de utilização |
| `user_payload` | Payload para criação de usuário |
| `sales_order_payload` | Payload para criação de pedido |

## 🔧 Configuração dos Testes

Os testes utilizam:
- **SQLite em memória**: Banco de dados isolado para cada teste
- **FastAPI TestClient**: Cliente HTTP para requisições de teste
- **Fixtures do pytest**: Dados mockados injetados automaticamente

## 📝 Convenções de Nomenclatura

- Arquivos de teste: `test_<nome_do_módulo>.py`
- Classes de teste: `Test<NomeDaFuncionalidade>`
- Métodos de teste: `test_<descrição_do_teste>`

## ✅ Endpoints Testados

| Módulo | Endpoints Testados |
|--------|-------------------|
| Root | `GET /`, `GET /health`, `GET /config` |
| Token | `POST /token_generate/` |
| User | `POST /auth/login/`, `POST /auth/register/`, `GET /user/read/{id}`, `POST /user/create/`, `PUT /user/update/{id}`, `DELETE /user/delete/{id}` |
| Address | `GET /address/read/{id}`, `POST /address/create/`, `PUT /address/update/{id}`, `DELETE /address/delete/{id}` |
| Company | `POST /company/save/`, `GET /company/{id}`, `GET /companies/`, `PUT /company/update/{id}`, `DELETE /company/delete/{id}`, `POST /company/user_to_company/` |
| Branch | `GET /branch/read/{id}`, `GET /branch/list/{company_id}`, `POST /branch/create/`, `PUT /branch/update/{id}`, `DELETE /branch/delete/{id}` |
| Business Partner | `GET /businnespartner/read/{id}`, `GET /businnespartner/list/{data}`, `POST /businnespartner/create/`, `PUT /businnespartner/update/{id}`, `DELETE /businnespartner/delete/{id}` |
| Freight | `GET /freight/read/{id}`, `GET /freight/list/{company_id}`, `POST /freight/create/`, `PUT /freight/update/{id}`, `DELETE /freight/delete/{id}` |
| Payment Method | `GET /paymentmethod/read/{id}`, `GET /paymentmethod/list/{company_id}`, `POST /paymentmethod/create/`, `PUT /paymentmethod/update/{id}`, `DELETE /paymentmethod/delete/{id}` |
| Payment Term | `GET /paymentterm/read/{id}`, `GET /paymentterm/list/{company_id}`, `POST /paymentterm/create/`, `PUT /paymentterm/update/{id}`, `DELETE /paymentterm/delete/{id}` |
| Utilization | `GET /utilization/read/{id}`, `GET /utilization/list/{company_id}`, `POST /utilization/create/`, `PUT /utilization/update/{id}`, `DELETE /utilization/delete/{id}` |
| Sales Order | `GET /salesorder/{id}`, `GET /salesorder/list/`, `POST /salesorder/save/`, `PUT /salesorder/update/{id}`, `DELETE /salesorder/delete/{id}` |

## 🎯 Cenários de Teste Cobertos

Para cada endpoint, os seguintes cenários são testados:

1. ✅ Requisição sem token de autenticação (espera 401)
2. ✅ Requisição com token válido
3. ✅ Requisição para recurso inexistente (espera 404)
4. ✅ Requisição com dados inválidos (espera 422)
5. ✅ Requisição com campos faltando
6. ✅ Filtros e parâmetros de query (quando aplicável)

## 🔍 Dicas para Debugging

Para ver mais detalhes durante os testes:

```bash
# Ver output de print
pytest -v -s

# Parar no primeiro erro
pytest -x

# Executar últimos testes que falharam
pytest --lf

# Executar testes que correspondem a um padrão
pytest -k "login or register"
```

## 📈 Relatório de Cobertura

Gere um relatório detalhado de cobertura:

```bash
pytest testes/ --cov=app --cov-report=html --cov-report=term-missing
```

Isso criará:
- Relatório no terminal com linhas não cobertas
- Relatório HTML em `htmlcov/index.html`
