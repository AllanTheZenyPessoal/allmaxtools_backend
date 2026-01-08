# Copilot Instructions - AllMaxTools Backend

## Project Overview
FastAPI backend for AllMaxTools, a multi-tenant business management system with role-based access control (RBAC) and company isolation. Uses MySQL (production) with SQLAlchemy ORM and Alembic migrations.

## Architecture

### Layered Structure (Routes → Endpoints → Database)
- **`app/routes/`** - FastAPI routers: request validation, auth dependencies, HTTP responses
- **`app/endpoint/`** - Business logic: CRUD operations, company filtering, permission checks
- **`app/database/`** - SQLAlchemy models (`db_models.py`) and Pydantic schemas (`base_models.py`)

### Authorization System (3-tier hierarchy)
```
superadmin (level 3) → Full system access, cross-company
admin (level 2)      → Manages users within own company only
user (level 1)       → Limited by explicit permissions (user_permissions table)
```
- Token payload includes: `id_user`, `role`, `company_id` (see `token_utils/apikey_generator.py`)
- Use `verify_token` dependency for basic auth, `require_permission("resource.action")` for granular control
- Company isolation: non-superadmin queries MUST filter by `current_user.company_id`

## Key Patterns

### Adding a New Endpoint
1. Create Pydantic models in `app/database/base_models.py`
2. Add SQLAlchemy model in `app/database/db_models.py` (PascalCase columns match DB)
3. Create business logic in `app/endpoint/<resource>.py`
4. Add router in `app/routes/<resource>.py` with proper dependencies
5. Register router in `app/main.py`

### Route Pattern Example
```python
@router.post("/resource/save/", status_code=status.HTTP_201_CREATED)
async def create_resource(
    data: base_models.ResourceCreateRequest,
    db: db_dependency,
    current_user: Annotated[dict, Depends(verify_token)]
):
    return await createResource(data, db, current_user)
```

### Company Isolation Pattern (CRITICAL)
```python
# In endpoint logic - always filter by company for non-superadmin
if user_role != "superadmin" and user_company_id:
    query = query.filter(Model.CompanyId == user_company_id)
```

## Database Conventions
- Table names: PascalCase (`SalesOrder`, `BusinessPartner`)
- Column names: PascalCase in DB, mapped via `Column("DBColumnName", ...)` 
- Pydantic fields: snake_case - mapping done in endpoint layer
- ForeignKeys currently removed for simplicity (referenced via int columns)

## Commands (Docker-first approach)

### Development Workflow
```bash
# Start all services (recommended)
docker-compose up -d

# Start with build (after dependency/Docker changes)
docker-compose up -d --build

# View logs (useful for debugging)
docker-compose logs -f api      # API logs only
docker-compose logs -f mysql    # MySQL logs only
docker-compose logs -f          # All logs

# Stop services
docker-compose down

# Reset database (removes all data)
docker-compose down -v
```

**Services:**
| Service | Container | Port | URL | Description |
|---------|-----------|------|-----|-------------|
| api | allmaxtools-api | 8181 | http://localhost:8181 | FastAPI backend |
| mysql | allmaxtools-mysql | 3307 | localhost:3307 | MySQL 8.2 database |

### Database Operations
```bash
# Access MySQL CLI
docker exec -it allmaxtools-mysql mysql -u root -p123 prototype

# Run migrations inside container
docker exec -it allmaxtools-api alembic upgrade head

# Create new migration (after model changes)
docker exec -it allmaxtools-api alembic revision --autogenerate -m "description"

# Rollback migration
docker exec -it allmaxtools-api alembic downgrade -1
```

### Testing
```bash
# Run tests inside container
docker exec -it allmaxtools-api pytest
docker exec -it allmaxtools-api pytest --cov=app
docker exec -it allmaxtools-api pytest -v

# Or with uv (faster)
docker exec -it allmaxtools-api uv run pytest
```

### Local Development (without Docker)
```bash
# Only if you prefer local development
uv pip install -r requirements.txt
cd app
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Quick Start (Docker)

1. **Start the project:**
   ```bash
   docker-compose up -d
   ```

2. **Run initial migrations:**
   ```bash
   docker exec -it allmaxtools-api alembic upgrade head
   ```

3. **Access the API:**
   - API: http://localhost:8181
   - Docs: http://localhost:8181/docs
   - Health: http://localhost:8181/health

## Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_USERNAME | root | MySQL user |
| DATABASE_PASSWORD | 123 | MySQL password |
| DATABASE_HOST | prototype-mysql-1 | MySQL host |
| DATABASE_PORT | 3306 | MySQL port |
| DATABASE | prototype | Database name |

## Testing Auth
1. Generate token: `POST /token_generate/` with `username` (email) and `password`
2. Use `Authorization: Bearer <token>` header
3. API docs at `/docs` - interactive testing available
