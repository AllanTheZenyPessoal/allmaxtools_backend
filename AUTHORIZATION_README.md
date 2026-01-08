# Sistema de Autorização - Prototype

## Visão Geral

Este sistema implementa um controle de acesso baseado em **roles** (papéis) e **permissões** granulares, com isolamento por empresa.

## Hierarquia de Roles

1. **superadmin** (Nível 3) - Acesso total ao sistema
2. **admin** (Nível 2) - Gerencia usuários da própria empresa
3. **user** (Nível 1) - Acesso limitado por permissões

## Regras de Negócio

### Superadmin
- ✅ Criar empresas
- ✅ Criar usuários admin vinculados a empresas
- ✅ Gerenciar telas e permissões base
- ✅ Ignora restrições de empresa
- ✅ Ignora verificações de permissões

### Admin
- ✅ Gerenciar usuários **apenas da própria empresa**
- ✅ Atribuir permissões de telas/botões para usuários
- ✅ Precisa ter permissões específicas para cada ação
- ❌ Não pode acessar outras empresas

### User
- ✅ Acessa **apenas o que o admin liberou**
- ✅ Restrito à própria empresa
- ✅ Cada ação requer permissão específica

## Estrutura do Banco

### Tabelas Principais
```sql
user (id_user, username, email, password, role, company_id, active, ...)
company (id_company, razao_social, cnpj, email, ...)
screen (id_screen, name, description, route, active, ...)
permission (id_permission, key, name, description, screen_id, active, ...)
user_permission (user_id, permission_id, granted_by, granted_at, ...)
```

## JWT Token

### Payload do Token
```json
{
  "sub": "user@email.com",
  "username": "username",
  "id_user": 123,
  "role": "admin",
  "company_id": 1,
  "exp": 1234567890
}
```

## Endpoints

### 🔐 Autenticação (Públicos)
- `POST /auth/login/` - Login com email/senha
- `POST /auth/register/` - Registro de usuário

### 👑 Gerenciamento (Superadmin)
- `POST /companies/` - Criar empresa
- `POST /users/admin/` - Criar usuário admin
- `POST /screens/` - Criar tela
- `POST /permissions/` - Criar permissão

### 👥 Usuários (Admin + Permissões)
- `POST /user/create/` - Criar usuário (requer `user.create`)
- `GET /user/read/{id}` - Visualizar usuário (requer `user.read`)
- `GET /user/list/` - Listar usuários (requer `user.list`)
- `PUT /user/update/{id}` - Editar usuário (requer `user.update`)
- `DELETE /user/delete/{id}` - Excluir usuário (requer `user.delete`)

### 🔑 Permissões (Admin)
- `POST /users/{id}/permissions/` - Atribuir permissões
- `GET /users/{id}/permissions/` - Ver permissões do usuário
- `GET /me/` - Informações do usuário atual
- `GET /me/permissions/` - Minhas permissões

## Permissões Padrão

### Usuários
- `user.create` - Criar usuários
- `user.read` - Visualizar usuários
- `user.update` - Editar usuários
- `user.delete` - Excluir usuários
- `user.list` - Listar usuários

### Empresas
- `company.create` - Criar empresas
- `company.read` - Visualizar empresas
- `company.update` - Editar empresas
- `company.delete` - Excluir empresas
- `company.list` - Listar empresas

### Sistema
- `dashboard.view` - Acessar dashboard
- `reports.view` - Visualizar relatórios
- `reports.export` - Exportar relatórios
- `permission.assign` - Atribuir permissões

## Instalação

### 1. Executar Migration SQL
```bash
# Executar no container Docker
docker exec -it prototype-backend-1 sqlite3 prototype.db < create_authorization_tables.sql
```

### 2. Popular Dados Iniciais
```bash
# Executar no container Docker
docker exec -it prototype-backend-1 python setup_authorization.py
```

### 3. Incluir Rotas no Main
```python
from routes.authorization import router as auth_router

app.include_router(auth_router, prefix="/authorization")
```

## Exemplos de Uso

### 1. Login como Superadmin
```bash
curl -X POST http://localhost:8181/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "superadmin@gmail.com", "password": "123123123"}'
```

### 2. Criar Empresa (Superadmin)
```bash
curl -X POST http://localhost:8181/authorization/companies/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "razao_social": "Nova Empresa LTDA",
    "nome_fantasia": "Nova Empresa",
    "cnpj": "98.765.432/0001-10",
    "email": "contato@novaempresa.com",
    "phone": "+55 11 99999-1111",
    "active": true
  }'
```

### 3. Criar Admin (Superadmin)
```bash
curl -X POST http://localhost:8181/authorization/users/admin/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_nova_empresa",
    "email": "admin@novaempresa.com",
    "password": "admin123",
    "phone": "+55 11 98888-1111",
    "role": "admin",
    "company_id": 2
  }'
```

### 4. Atribuir Permissões (Admin)
```bash
curl -X POST http://localhost:8181/authorization/users/5/permissions/ \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 5,
    "permission_keys": ["user.read", "user.list", "dashboard.view"]
  }'
```

### 5. Listar Usuários (User com Permissão)
```bash
curl -X GET http://localhost:8181/user/list/ \
  -H "Authorization: Bearer {user_token}"
```

## Fluxo de Trabalho

1. **Superadmin** cria empresas e admins
2. **Admin** cria usuários comuns e atribui permissões
3. **User** acessa apenas recursos permitidos
4. Sistema **automaticamente filtra** dados por empresa
5. Permissões são **verificadas em cada endpoint**

## Segurança

- ✅ Passwords hasheados com bcrypt
- ✅ JWT com expiração
- ✅ Validação de roles em cada endpoint
- ✅ Isolamento por empresa
- ✅ Verificação granular de permissões
- ✅ Logs de quem concedeu permissões

## Usuários de Exemplo

Após executar `setup_authorization.py`:

- **Superadmin**: `superadmin@gmail.com` / `123123123`
- **Admin**: `admin@exemplo.com` / `admin123`
- **User**: `user@exemplo.com` / `user123`

Empresa: "Empresa Exemplo LTDA" (ID: 1)
