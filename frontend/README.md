# TenantFlow frontend

Next.js frontend for the TenantFlow Django REST API.

## Setup

```powershell
npm install
Copy-Item .env.example .env.local
npm run dev
```

The default API base URL is `http://127.0.0.1:8000`. Change `NEXT_PUBLIC_API_BASE_URL` in `.env.local` when the backend runs elsewhere.

## Authentication

The existing backend returns JWT strings in JSON and does not issue HttpOnly authentication cookies. The frontend therefore keeps the access and refresh tokens in browser `sessionStorage`, attaches the access token centrally, refreshes once after a `401`, retries the original request, and clears the session if refresh fails. `sessionStorage` limits persistence to the current browser tab, but JavaScript-readable storage remains exposed if an XSS vulnerability exists. A future HttpOnly-cookie strategy requires an intentional backend contract change.

Registration creates a company and administrator but does not authenticate them. Successful registration redirects to sign-in. `/api/auth/me/` is the authoritative source for current user, role, and company information.

## Checks

```powershell
npm run typecheck
npm run lint
npm run build
```

`npm audit` checks the installed dependency tree for published security advisories. This repository does not currently include an automated frontend test suite.

## Full-stack development

Start PostgreSQL first, followed by Redis when background assignment notifications are needed. Apply Django migrations and start the API, then start the Celery worker, and finally start this Next.js application. The complete backend setup, including PostgreSQL and Redis configuration, is in [`../backend/README.md`](../backend/README.md).
