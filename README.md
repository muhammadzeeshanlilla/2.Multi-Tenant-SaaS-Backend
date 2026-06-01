# TenantFlow Backend API

A **Multi-Tenant SaaS Backend System** built with **Django REST Framework**.  
Multiple companies share the same backend while keeping their data completely separate and secure.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Main Features](#3-main-features)
4. [Project Architecture](#4-project-architecture)
5. [Folder Structure](#5-folder-structure)
6. [Database Design](#6-database-design)
7. [Role Permissions](#7-role-permissions)
8. [Tenant Isolation](#8-tenant-isolation)
9. [API Endpoints](#9-api-endpoints)
10. [API Response Format](#10-api-response-format)
11. [Installation Guide](#11-installation-guide)
12. [Admin Panel](#12-admin-panel)
13. [Swagger Documentation](#13-swagger-documentation)
14. [Postman Collection](#14-postman-collection)
15. [Testing Flow](#15-testing-flow)
16. [Example API Requests](#16-example-api-requests)
17. [Soft Delete](#17-soft-delete)
18. [Audit Logging](#18-audit-logging)
19. [Rate Limiting](#19-rate-limiting)
20. [Security Highlights](#20-security-highlights)
21. [Future Improvements](#21-future-improvements)
22. [Project Status](#22-project-status)
23. [Author](#23-author)

---

## 1. Project Overview

Most SaaS platforms serve multiple companies using one backend system.

**Example:**

```
Company A → ABC Software House
Company B → XYZ Software House

Both companies use:
  - Same Django backend
  - Same PostgreSQL database
  - Same API endpoints

But each company can only access its own:
  - Users
  - Projects
  - Tasks
  - Audit logs
```

> A user from Company A can **never** access Company B data.

**Main Purpose:**

- Multiple companies can register
- Each company gets its own admin user
- Admins can manage users
- Admins and managers can manage projects and tasks
- Employees can view only assigned projects/tasks
- All important actions are logged
- Company data is fully isolated

---

## 2. Tech Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | Django |
| API Framework | Django REST Framework |
| Database | PostgreSQL |
| Authentication | JWT using SimpleJWT |
| API Documentation | Swagger using drf-spectacular |
| Testing Tool | Postman |
| Rate Limiting | DRF Throttling |
| Language | Python |
| Version Control | Git & GitHub |
| Operating System | Linux Ubuntu |

---

## 3. Main Features

### Authentication
- Company registration
- Initial admin creation
- Login with email and password
- JWT access token & refresh token
- Current user profile API

### Company Management
- Register company
- Create first company admin automatically
- Each company has a unique identity

### User Management
- Admin can create, update, soft delete, and restore users
- Admin can create managers and employees
- Users are linked to a company

### Role-Based Access Control

Three roles are available:

- `ADMIN`
- `MANAGER`
- `EMPLOYEE`

### Project Management
- Create, view, update, soft delete, and restore projects
- Assign users to projects

### Task Management
- Create, view, update, soft delete, and restore tasks
- Assign tasks to users
- Update task status

### Tenant Isolation
All queries are filtered using `request.user.company`. Company A users cannot access Company B data.

### Audit Logging
Tracks: user login/created/updated/deleted/restored, project created/updated/deleted/restored/assigned, task created/updated/deleted/restored/status changed.

### Rate Limiting

| Scope | Limit |
|-------|-------|
| Authenticated user | 1000/day |
| Anonymous | 100/day |
| Login | 5/minute |
| Company register | 3/hour |

---

## 4. Project Architecture

```
Client / Postman / Swagger
        |
        v
Django REST Framework API
        |
        |-- JWT Authentication
        |-- Role-Based Permissions
        |-- Tenant Isolation
        |-- User Management
        |-- Project Management
        |-- Task Management
        |-- Audit Logging
        |-- Rate Limiting
        |
        v
PostgreSQL Database
```

---

## 5. Folder Structure

```
tenantflow-backend/
│
├── apps/
│   ├── accounts/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── user_urls.py
│   │   └── permissions.py
│   │
│   ├── companies/
│   │   ├── models.py
│   │   └── admin.py
│   │
│   ├── projects/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── tasks/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── audit/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── utils.py
│   │
│   └── common/
│       ├── models.py
│       └── throttling.py
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── postman/
│   └── TenantFlow_Backend_API.postman_collection.json
│
├── manage.py
├── requirements.txt
├── README.md
├── .env
└── .gitignore
```

---

## 6. Database Design

### Main Tables

**Company** — Stores company/tenant information.

| Field | Type |
|-------|------|
| id | PK |
| name | string |
| slug | string |
| email | string |
| phone | string |
| address | string |
| is_active | boolean |
| created_at | datetime |
| updated_at | datetime |

**User** — Stores users of each company.

| Field | Type |
|-------|------|
| id | PK |
| company | FK |
| username | string |
| email | string |
| password | string |
| role | ADMIN / MANAGER / EMPLOYEE |
| is_active | boolean |
| is_deleted | boolean |
| created_at | datetime |
| updated_at | datetime |

**Project** — Stores projects of each company.

| Field | Type |
|-------|------|
| id | PK |
| company | FK |
| name | string |
| description | text |
| status | PLANNING / ACTIVE / COMPLETED / CANCELLED |
| start_date | date |
| end_date | date |
| created_by | FK (User) |
| is_deleted | boolean |
| created_at | datetime |
| updated_at | datetime |

**ProjectMember** — Stores which users are assigned to a project.

| Field | Type |
|-------|------|
| id | PK |
| company | FK |
| project | FK |
| user | FK |
| created_at | datetime |

**Task** — Stores tasks under projects.

| Field | Type |
|-------|------|
| id | PK |
| company | FK |
| project | FK |
| title | string |
| description | text |
| assigned_to | FK (User) |
| status | PENDING / IN_PROGRESS / COMPLETED |
| priority | LOW / MEDIUM / HIGH / URGENT |
| due_date | date |
| created_by | FK (User) |
| is_deleted | boolean |
| created_at | datetime |
| updated_at | datetime |

**AuditLog** — Stores important system actions.

| Field | Type |
|-------|------|
| id | PK |
| company | FK |
| user | FK |
| action | string |
| object_type | string |
| object_id | integer |
| description | text |
| ip_address | string |
| created_at | datetime |

### Relationships

```
Company  1 ──── many  Users
Company  1 ──── many  Projects
Company  1 ──── many  Tasks
Company  1 ──── many  AuditLogs

User     1 ──── many  Created Projects
User     1 ──── many  Created Tasks
User     1 ──── many  Assigned Tasks
User     1 ──── many  AuditLogs

Project  1 ──── many  Tasks
Project many ── many  Users  (through ProjectMember)
```

---

## 7. Role Permissions

| Feature | Admin | Manager | Employee |
|---------|-------|---------|----------|
| Register company | ✅ | ❌ | ❌ |
| Login | ✅ | ✅ | ✅ |
| View own profile | ✅ | ✅ | ✅ |
| Create users | ✅ | ❌ | ❌ |
| View company users | ✅ | ❌ | ❌ |
| Update users | ✅ | ❌ | ❌ |
| Delete users | ✅ | ❌ | ❌ |
| Restore users | ✅ | ❌ | ❌ |
| Create project | ✅ | ✅ | ❌ |
| View all company projects | ✅ | ✅ | ❌ |
| View assigned projects | ✅ | ✅ | ✅ |
| Update project | ✅ | ✅ | ❌ |
| Delete project | ✅ | ✅ | ❌ |
| Restore project | ✅ | ✅ | ❌ |
| Assign users to project | ✅ | ✅ | ❌ |
| Create task | ✅ | ✅ | ❌ |
| View all company tasks | ✅ | ✅ | ❌ |
| View assigned tasks | ✅ | ✅ | ✅ |
| Update task | ✅ | ✅ | ❌ |
| Update own task status | ✅ | ✅ | ✅ |
| Delete task | ✅ | ✅ | ❌ |
| Restore task | ✅ | ✅ | ❌ |
| View audit logs | ✅ | ❌ | ❌ |

---

## 8. Tenant Isolation

Tenant isolation is implemented by linking every record to a company. The backend automatically uses `request.user.company` — the frontend never sends `company_id`.

```python
Project.objects.filter(company=request.user.company)
Task.objects.filter(company=request.user.company)
User.objects.filter(company=request.user.company)
AuditLog.objects.filter(company=request.user.company)
```

**❌ Wrong — never send company_id from client:**
```json
{
  "company_id": 1,
  "name": "Project A"
}
```

**✅ Correct:**
```json
{
  "name": "Project A"
}
```

---

## 9. API Endpoints

### Auth APIs
```
POST  /api/auth/company-register/
POST  /api/auth/login/
POST  /api/auth/token/refresh/
GET   /api/auth/me/
```

### User APIs
```
GET    /api/users/
POST   /api/users/
GET    /api/users/{id}/
PATCH  /api/users/{id}/
DELETE /api/users/{id}/
POST   /api/users/{id}/restore/
```

### Project APIs
```
GET    /api/projects/
POST   /api/projects/
GET    /api/projects/{id}/
PATCH  /api/projects/{id}/
DELETE /api/projects/{id}/
POST   /api/projects/{id}/restore/
POST   /api/projects/{id}/assign-users/
```

### Task APIs
```
GET    /api/tasks/
POST   /api/tasks/
GET    /api/tasks/{id}/
PATCH  /api/tasks/{id}/
DELETE /api/tasks/{id}/
POST   /api/tasks/{id}/restore/
PATCH  /api/tasks/{id}/status/
```

### Audit APIs
```
GET /api/audit-logs/
```

### Documentation APIs
```
GET /api/schema/
GET /api/docs/
```

---

## 10. API Response Format

**Success Response**
```json
{
  "success": true,
  "message": "Project created successfully.",
  "data": {}
}
```

**Error Response**
```json
{
  "success": false,
  "message": "Project creation failed.",
  "errors": {}
}
```

**List Response**
```json
{
  "success": true,
  "message": "Projects fetched successfully.",
  "count": 10,
  "data": []
}
```

---

## 11. Installation Guide

### Step 1: Clone Repository
```bash
git clone <your-repository-url>
cd tenantflow-backend
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Requirements
```bash
pip install -r requirements.txt
```

### Step 4: Create `.env` File

Create `.env` in the root folder:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=tenantflow_db
DB_USER=tenantflow_user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432
```

> Do **not** push `.env` to GitHub.

### Step 5: Create PostgreSQL Database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE tenantflow_db;
CREATE USER tenantflow_user WITH PASSWORD 'your-db-password';
GRANT ALL PRIVILEGES ON DATABASE tenantflow_db TO tenantflow_user;

\c tenantflow_db

GRANT ALL ON SCHEMA public TO tenantflow_user;
ALTER SCHEMA public OWNER TO tenantflow_user;

\q
```

### Step 6: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 7: Create Superuser
```bash
python manage.py createsuperuser
```

### Step 8: Run Server
```bash
python manage.py runserver
```

Server runs at: `http://127.0.0.1:8000/`

---

## 12. Admin Panel

```
http://127.0.0.1:8000/admin/
```

View and manage: Users, Companies, Projects, Project Members, Tasks, Audit Logs.

---

## 13. Swagger Documentation

```
http://127.0.0.1:8000/api/docs/
```

Schema URL:
```
http://127.0.0.1:8000/api/schema/
```

---

## 14. Postman Collection

Collection file:
```
postman/TenantFlow_Backend_API.postman_collection.json
```

Covers: Auth APIs, User APIs, Project APIs, Task APIs, Audit APIs, Tenant isolation, Soft delete, Rate limiting.

---

## 15. Testing Flow

Recommended testing order:

1. Register Company A
2. Login Company A Admin
3. Create Manager
4. Create Employee
5. Create Project
6. Assign Manager and Employee to Project
7. Create Task under Project
8. Assign Task to Employee
9. Login Employee
10. Employee views assigned tasks
11. Employee updates own task status
12. Check Audit Logs as Admin
13. Soft delete task / project / user
14. Restore deleted data
15. Register Company B
16. Test that Company B cannot access Company A data

---

## 16. Example API Requests

### Company Register
```http
POST /api/auth/company-register/
```
```json
{
  "company_name": "ABC Software House",
  "company_email": "company@abc.com",
  "phone": "03001234567",
  "address": "Rawalpindi, Pakistan",
  "username": "abc_admin",
  "email": "admin@abc.com",
  "password": "Admin@12345",
  "confirm_password": "Admin@12345"
}
```

### Login
```http
POST /api/auth/login/
```
```json
{
  "email": "admin@abc.com",
  "password": "Admin@12345"
}
```

Response includes `access` and `refresh` tokens. Use the access token in all protected API calls:
```
Authorization: Bearer your_access_token
```

### Create User
```http
POST /api/users/
```
```json
{
  "username": "manager1",
  "email": "manager1@abc.com",
  "password": "Manager@12345",
  "confirm_password": "Manager@12345",
  "role": "MANAGER",
  "is_active": true
}
```

The user is automatically created inside the logged-in admin's company.

### Create Project
```http
POST /api/projects/
```
```json
{
  "name": "Website Development Project",
  "description": "Build company website backend and APIs",
  "status": "ACTIVE",
  "start_date": "2026-06-01",
  "end_date": "2026-06-20"
}
```

### Assign Users to Project
```http
POST /api/projects/{project_id}/assign-users/
```
```json
{
  "user_ids": [3, 4]
}
```

### Create Task
```http
POST /api/tasks/
```
```json
{
  "project_id": 1,
  "title": "Design homepage",
  "description": "Create homepage UI design",
  "assigned_to_id": 4,
  "status": "PENDING",
  "priority": "HIGH",
  "due_date": "2026-06-10"
}
```

### Update Task Status
```http
PATCH /api/tasks/{task_id}/status/
```
```json
{
  "status": "IN_PROGRESS"
}
```

---

## 17. Soft Delete

Records are never permanently deleted. Instead, they are marked as:

```python
is_deleted = True
```

Deleted records do not appear in normal list APIs. Restore APIs are available for Users, Projects, and Tasks.

---

## 18. Audit Logging

Each audit log entry stores:

- Company
- User
- Action
- Object type & ID
- Description
- IP address
- Timestamp

Only **Admin** can view audit logs.

---

## 19. Rate Limiting

| Scope | Limit |
|-------|-------|
| Authenticated user | 1000/day |
| Anonymous | 100/day |
| Login | 5/minute |
| Company register | 3/hour |

Protects against brute-force login attacks, fake company registrations, API abuse, and server overload.

---

## 20. Security Highlights

- JWT authentication
- Role-based permissions
- Company-level tenant isolation
- Object-level access filtering
- Soft delete
- Audit logging
- Rate limiting
- Environment variables for secrets
- PostgreSQL database
- No hardcoded `company_id`

---

## 21. Future Improvements

- Email notifications
- Celery background jobs
- Docker support
- Cloud server deployment
- Automated tests
- Frontend dashboard
- Advanced reporting
- Team invitations
- Password reset
- Two-factor authentication

---

## 22. Project Status

| Feature | Status |
|---------|--------|
| Company Registration | ✅ Completed |
| JWT Authentication | ✅ Completed |
| User Management | ✅ Completed |
| Project Management | ✅ Completed |
| Task Management | ✅ Completed |
| Audit Logging | ✅ Completed |
| Soft Delete | ✅ Completed |
| Tenant Isolation | ✅ Completed |
| Rate Limiting | ✅ Completed |
| Swagger Documentation | ✅ Completed |
| Postman Collection | ✅ Completed |

---

## 23. Author

| | |
|---|---|
| **Developer** | Muhammad Zeeshan |
| **Project** | TenantFlow Backend API |
| **Type** | Multi-Tenant SaaS Backend |
| **Stack** | Django REST Framework + PostgreSQL + JWT |
