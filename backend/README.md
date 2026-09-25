# TenantFlow Backend API

TenantFlow is a multi-tenant SaaS backend built with Django REST Framework. Multiple companies share one application and database while users, projects, tasks, and audit logs remain isolated by company.

## Technology

- Python and Django 6
- Django REST Framework
- PostgreSQL
- SimpleJWT access/refresh authentication and refresh-token blacklisting
- Celery with Redis for assignment-notification jobs
- django-cors-headers for browser access
- drf-spectacular for OpenAPI and Swagger UI

## Architecture

The main domain objects are:

- `Company`: tenant identity and active/inactive state.
- `User`: belongs to a company and has an Admin, Manager, or Employee role.
- `Project`: belongs to a company and has a creator.
- `ProjectMember`: tenant-validated link between a project and an assigned user.
- `Task`: belongs to a company and project, with optional assignee and creator.
- `AuditLog`: tenant-scoped record of authentication and business actions.

Tenant safety is enforced in several layers:

- API querysets always begin with the authenticated user's company.
- Foreign-key IDs submitted through APIs are restricted to the same company.
- Model validation rejects inconsistent task and project-membership relationships outside serializers.
- Employees see only assigned projects and tasks.
- Inactive companies cannot log in or use existing access tokens.
- Tasks below soft-deleted projects are hidden and cannot be restored until the project is restored.

## Roles

| Capability | Admin | Manager | Employee |
|---|---:|---:|---:|
| List tenant users for project membership | Yes | Yes | No |
| Manage company users | Yes | No | No |
| Manage projects and memberships | Yes | Yes | No |
| View all company projects | Yes | Yes | No |
| View assigned projects | Yes | Yes | Yes |
| Manage tasks | Yes | Yes | No |
| Update assigned task status | Yes | Yes | Yes |
| View audit logs | Yes | No | No |

All role and tenant rules are enforced by the backend.

## Local setup

### 1. Create a Python environment

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and replace development placeholders:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Never commit `.env` or real credentials.

### 3. Prepare PostgreSQL

Create a dedicated development database and user:

```sql
CREATE DATABASE tenantflow_db;
CREATE USER tenantflow_user WITH PASSWORD 'replace-this-development-password';
GRANT ALL PRIVILEGES ON DATABASE tenantflow_db TO tenantflow_user;
\c tenantflow_db
GRANT ALL ON SCHEMA public TO tenantflow_user;
```

Run all migrations, including SimpleJWT blacklist tables:

```bash
python manage.py migrate
python manage.py check
```

### 4. Start Redis and Celery

Background notifications are optional in local development. To run without Redis or Celery, set:

```dotenv
BACKGROUND_JOBS_ENABLED=False
```

The primary database transaction still commits normally, and the post-commit publisher skips notification jobs without contacting Redis.

In an environment where Redis and a Celery worker are intentionally available, set `BACKGROUND_JOBS_ENABLED=True`. Run Redis locally using your operating system's Redis package or another trusted local Redis installation. The default broker is `redis://localhost:6379/0`.

Start a Celery worker from `backend/`:

```bash
celery -A config worker --loglevel=info
```

On Windows, a local development worker may require:

```powershell
celery -A config worker --loglevel=info --pool=solo
```

Assignment email publishing is non-critical: publishing occurs after database commit, and broker failure is logged without rolling back a successful API operation.

### 5. Start Django

```bash
python manage.py runserver
```

- API root paths: `http://127.0.0.1:8000/api/`
- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- Django admin: `http://127.0.0.1:8000/admin/`

## Environment variables

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Required Django signing secret |
| `ENVIRONMENT` | `development` or `production` |
| `DEBUG` | Explicit debug mode flag; defaults to `False` |
| `ALLOWED_HOSTS` | Comma-separated accepted host names |
| `CORS_ALLOWED_ORIGINS` | Comma-separated browser frontend origins |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted HTTPS origins when needed |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL credentials |
| `DB_HOST`, `DB_PORT` | PostgreSQL host and port |
| `CELERY_BROKER_URL` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | Celery result backend URL |
| `BACKGROUND_JOBS_ENABLED` | Enables post-commit Celery publishing; use `False` for local development without Redis |
| `EMAIL_BACKEND` | Django email backend; console backend is the local default |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS` | SMTP transport settings |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP credentials when SMTP is enabled |
| `DEFAULT_FROM_EMAIL` | Notification sender address |
| `SECURE_SSL_REDIRECT` | Production HTTPS redirect |
| `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` | Secure-cookie flags |
| `SECURE_HSTS_SECONDS` | Production HSTS duration |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` | Optional HSTS controls |

Production security defaults activate when `ENVIRONMENT=production`; deployment-specific hosts and origins must still be supplied explicitly.

## Authentication flow

1. Register a company and initial administrator.
2. Log in with administrator email/password.
3. Send the access token as `Authorization: Bearer <access-token>`.
4. Refresh using `/api/auth/token/refresh/`.
5. Log out by sending the refresh token to `/api/auth/logout/` while authenticated. That refresh token is blacklisted; access tokens expire naturally.

No credentials are created automatically. For local demonstrations, register a disposable company through the registration endpoint using a non-production password such as `Demo-Admin-7x!`.

## Pagination and filters

User, project, task, and audit-log lists use page-number pagination. The default size is 20, and clients may request up to 100 with `page_size`.

```json
{
  "success": true,
  "message": "Tasks fetched successfully.",
  "count": 42,
  "next": "http://127.0.0.1:8000/api/tasks/?page=2",
  "previous": null,
  "data": []
}
```

Supported filters:

- Projects: `status`
- Tasks: `status`, `project`, `assignee` (`null` selects unassigned tasks)
- Audit logs: `action`

Every filter is applied after tenant and role restrictions.

## API documentation

The complete frontend-oriented contract is in [docs/API.md](docs/API.md). Interactive documentation is generated from the same code at `/api/docs/`.

The sanitized Postman collection is at [postman/tenantflow_user.postman_collection.json](postman/tenantflow_user.postman_collection.json). It uses collection variables and contains no real credentials or JWTs.

## Tests and checks

With the PostgreSQL test user allowed to create a test database:

```bash
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py spectacular --validate --file openapi.yaml
python -m pip check
```

Tests cover tenant boundaries, roles, inactive-company handling, JWT logout/blacklisting, registration rollback, password validation, audit isolation, soft-delete integrity, background-publisher failures, CORS, schema paths, pagination, and filters.

## Soft deletion and audit logs

Users, projects, and tasks are soft deleted and can be restored through their documented restore actions. Deleted records are excluded from normal queries. Restoring a project does not automatically restore its deleted tasks.

Audit logs record login/logout and user, project, and task mutations. Only company Admin users may read their own tenant's audit records. There is no audit-log write API.
