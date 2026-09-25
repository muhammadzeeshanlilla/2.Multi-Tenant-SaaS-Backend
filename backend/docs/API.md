# TenantFlow API contract

Base URL in local development: `http://127.0.0.1:8000`

Protected endpoints require:

```http
Authorization: Bearer <access-token>
Content-Type: application/json
```

## Authentication

| Method | Endpoint | Authentication | Request | Success | Common errors |
|---|---|---|---|---|---|
| POST | `/api/auth/company-register/` | Public | `company_name`, `company_email`, optional `phone`/`address`, `username`, `email`, `password`, `confirm_password` | `201`; company and initial Admin | `400` validation, duplicate identity, or weak password; `429` throttled |
| POST | `/api/auth/login/` | Public | `email`, `password` | `200`; `data.user` and `data.tokens.access/refresh` | `400` invalid credentials/inactive account; `429` throttled |
| POST | `/api/auth/token/refresh/` | Public refresh token | `refresh` | `200`; new `access` and, because rotation is enabled, `refresh` | `401` invalid, expired, or blacklisted token |
| POST | `/api/auth/logout/` | Access token | `refresh` | `200`; submitted refresh token blacklisted | `400` malformed/wrong-user refresh; `401` invalid access token |
| GET | `/api/auth/me/` | Access token | None | `200`; current user, role, and company | `401` invalid token or inactive company |

An access token is valid for 60 minutes. Refresh tokens are valid for seven days and rotate on refresh. Logging out revokes the submitted refresh token, not already-issued access tokens.

## Users

Admins have full tenant-scoped user management. Managers may list non-deleted users in their own company solely to support project membership selection. User detail and every mutation remain Admin-only. Employees cannot access the user API.

| Method | Endpoint | Roles | Request | Result |
|---|---|---|---|---|
| GET | `/api/users/` | Admin, Manager | Pagination parameters | Non-deleted users in the caller's company |
| POST | `/api/users/` | Admin | `username`, `email`, `password`, `confirm_password`, `role` (`MANAGER` or `EMPLOYEE`), optional `is_active` | Creates user in Admin's company |
| GET | `/api/users/{id}/` | Admin | None | Tenant-scoped user |
| PUT/PATCH | `/api/users/{id}/` | Admin | Supported user fields; optional validated `password` | Updates non-Admin user |
| DELETE | `/api/users/{id}/` | Admin | None | Soft deletes non-Admin user |
| POST | `/api/users/{id}/restore/` | Admin | None | Restores tenant user |

Cross-tenant IDs resolve as `404`. Admins cannot delete themselves or modify/delete an Admin through this API.

## Projects

Admin and Manager users manage all projects in their company. Employees can only list/retrieve projects to which they belong.

| Method | Endpoint | Roles | Request | Result |
|---|---|---|---|---|
| GET | `/api/projects/` | All roles | `page`, `page_size`, optional `status` | Tenant/assignment-scoped projects |
| POST | `/api/projects/` | Admin, Manager | `name`, optional `description`, `status`, `start_date`, `end_date` | Creates project |
| GET | `/api/projects/{id}/` | All roles subject to scope | None | Project and active members |
| PUT/PATCH | `/api/projects/{id}/` | Admin, Manager | Project fields | Updates project; date range is validated |
| DELETE | `/api/projects/{id}/` | Admin, Manager | None | Soft deletes project |
| POST | `/api/projects/{id}/restore/` | Admin, Manager | None | Restores project only |
| POST | `/api/projects/{id}/assign-users/` | Admin, Manager | `user_ids: [integer]` | Atomically replaces active project membership; an empty list clears membership |

Valid project statuses: `PLANNING`, `ACTIVE`, `COMPLETED`, `CANCELLED`.

## Tasks

Admin and Manager users manage tasks in their company. Employees see only assigned tasks and may update only their assigned task status.

| Method | Endpoint | Roles | Request | Result |
|---|---|---|---|---|
| GET | `/api/tasks/` | All roles | `page`, `page_size`; optional `status`, `project`, `assignee` | Tenant/assignment-scoped tasks |
| POST | `/api/tasks/` | Admin, Manager | `project_id`, `title`, optional `description`, `assigned_to_id`, `status`, `priority`, `due_date` | Creates task |
| GET | `/api/tasks/{id}/` | All roles subject to scope | None | Task details |
| PUT/PATCH | `/api/tasks/{id}/` | Admin, Manager | Task fields | Updates task using final-state membership validation |
| DELETE | `/api/tasks/{id}/` | Admin, Manager | None | Soft deletes task |
| POST | `/api/tasks/{id}/restore/` | Admin, Manager | None | Restores task if its project is active |
| PATCH | `/api/tasks/{id}/status/` | Admin, Manager, assigned Employee | `status` | Updates status |

Valid statuses: `PENDING`, `IN_PROGRESS`, `COMPLETED`. Valid priorities: `LOW`, `MEDIUM`, `HIGH`, `URGENT`.

`assigned_to_id` omitted during PATCH preserves the current assignee. Explicit `null` removes the assignment. Numeric IDs must identify an active member of the final project.

## Audit logs — Admin only

| Method | Endpoint | Request | Result |
|---|---|---|---|
| GET | `/api/audit-logs/` | `page`, `page_size`, optional `action` | Read-only logs for the Admin's company |

Managers and Employees receive `403`. No create, update, delete, or detail audit endpoint exists.

## Pagination response

List endpoints return:

```json
{
  "success": true,
  "message": "Projects fetched successfully.",
  "count": 25,
  "next": "http://127.0.0.1:8000/api/projects/?page=2",
  "previous": null,
  "data": []
}
```

`page_size` defaults to 20 and is capped at 100.

## Error handling

- Custom business responses normally include `success`, `message`, and `errors`.
- DRF authentication, permission, throttling, malformed pagination, and schema-level validation errors may use DRF's standard `detail` or field-error format.
- `400`: invalid request/business validation.
- `401`: missing, invalid, expired, or blacklisted token.
- `403`: authenticated user lacks the required role.
- `404`: object does not exist within the caller's permitted tenant scope.
- `429`: rate limit exceeded.
