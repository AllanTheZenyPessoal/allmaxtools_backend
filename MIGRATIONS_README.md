# Alembic Migrations - Guia de Uso

Este projeto utiliza **Alembic** para gerenciar migrações de banco de dados com SQLAlchemy.

## Estrutura

```
backend/
├── alembic.ini              # Configuração principal do Alembic
├── run_migrations.py        # Script helper para rodar migrations
└── alembic/
    ├── env.py               # Configuração do ambiente (carrega models e DB URL)
    ├── script.py.mako       # Template para novas migrations
    ├── README               # Documentação básica
    └── versions/            # Arquivos de migration
        └── 001_initial_baseline.py
```

## Variáveis de Ambiente

Configure as seguintes variáveis (ou use os defaults):

| Variável | Default | Descrição |
|----------|---------|-----------|
| DATABASE_USERNAME | root | Usuário do banco |
| DATABASE_PASSWORD | 123 | Senha do banco |
| DATABASE_HOST | localhost | Host do banco |
| DATABASE_PORT | 3306 | Porta do banco |
| DATABASE | prototype | Nome do banco |

## Comandos Básicos

### Navegar para o diretório backend

```bash
cd backend
```

### Verificar estado atual

```bash
alembic current
```

### Criar nova migration (auto-detecta mudanças nos models)

```bash
alembic revision --autogenerate -m "descrição das mudanças"
```

### Aplicar todas as migrations pendentes

```bash
alembic upgrade head
```

### Aplicar uma migration específica

```bash
alembic upgrade <revision_id>
```

### Reverter última migration

```bash
alembic downgrade -1
```

### Reverter para uma versão específica

```bash
alembic downgrade <revision_id>
```

### Ver histórico de migrations

```bash
alembic history
```

### Marcar DB existente como atualizado (sem executar migrations)

```bash
alembic stamp head
```

## Usando o Script Helper

O `run_migrations.py` facilita a execução em ambientes como Docker:

```bash
# Aplicar todas as migrations
python run_migrations.py upgrade head

# Reverter uma migration
python run_migrations.py downgrade -1

# Ver estado atual
python run_migrations.py current

# Marcar como head (para DBs existentes)
python run_migrations.py stamp head
```

## Workflow em Desenvolvimento

1. **Modificar models** em `app/database/db_models.py`

2. **Gerar migration**:
   ```bash
   alembic revision --autogenerate -m "add new column to users"
   ```

3. **Revisar o arquivo gerado** em `alembic/versions/`

4. **Aplicar a migration**:
   ```bash
   alembic upgrade head
   ```

## Workflow em Produção

### Opção 1: Job de migração separado (Recomendado)

Execute as migrations como um job/step separado antes do deploy:

```bash
# Em um container/job dedicado
alembic upgrade head
```

### Opção 2: Script de startup

```python
# No início da aplicação (cuidado com múltiplas réplicas!)
from run_migrations import run_upgrade
run_upgrade("head")
```

### Docker Compose

Adicione um serviço de migration:

```yaml
services:
  migration:
    build: ./backend
    command: python run_migrations.py upgrade head
    environment:
      - DATABASE_HOST=mysql
      - DATABASE_PASSWORD=secret
    depends_on:
      - mysql
```

### Kubernetes Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
spec:
  template:
    spec:
      containers:
      - name: migration
        image: your-backend-image
        command: ["python", "run_migrations.py", "upgrade", "head"]
        env:
        - name: DATABASE_HOST
          value: "mysql-service"
      restartPolicy: Never
```

## Primeiros Passos com DB Existente

Se você já tem um banco de dados com tabelas:

1. **Marque o estado atual como baseline**:
   ```bash
   alembic stamp head
   ```

2. A partir de agora, novas mudanças nos models serão detectadas

## Boas Práticas

1. **Sempre revise migrations auto-geradas** antes de aplicar
2. **Teste em staging** antes de produção
3. **Faça backup** antes de migrations destrutivas
4. **Não edite migrations já aplicadas** em produção
5. **Mudanças destrutivas em etapas**:
   - Adicionar coluna nullable → popular dados → tornar NOT NULL
6. **Use nomes descritivos** nas migrations

## Troubleshooting

### "Target database is not up to date"

```bash
alembic stamp head  # Marca o estado atual
```

### "Can't locate revision"

Verifique se a pasta `versions/` contém os arquivos de migration.

### Conflito de migrations

Se duas branches criaram migrations, resolva o conflito:
```bash
alembic merge heads -m "merge migrations"
```
