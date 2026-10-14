# Community Platform Backend

REST API for a community platform with three modules:

1. **User Registration & Authentication** — email/password signup and login, JWT sessions, `user`/`admin` roles
2. **Conversation Management** — admins create, schedule, publish and cancel conversations with speakers; the public browses published ones (upcoming/past)
3. **Investor Request Management** — logged-in users submit funding requests; admins review them through a status workflow with full history

Built to the PRD in [`../prd.md`](../prd.md). No frontend — API only.

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | PostgreSQL 14+ (Docker image: 16) |
| ORM | SQLAlchemy 2.x + Alembic migrations |
| Validation | Pydantic v2 |
| Password hashing | bcrypt (cost factor 12) |
| Tokens | JWT (PyJWT, HS256) |
| Config | `.env` via `pydantic-settings` |
| Tests | pytest + FastAPI `TestClient` |
| Docs | Swagger UI at `/docs`, ReDoc at `/redoc` |

## Quick start (under 10 minutes)

All commands from the `backend/` directory.

```powershell
# 1. Install dependencies (use a venv if you prefer)
pip install -r requirements.txt

# 2. Configure
copy .env.example .env        # Windows: copy / PowerShell: Copy-Item .env.example .env
# edit .env: set a long random JWT_SECRET (32+ chars)

# 3. Start PostgreSQL (host port 5433 to avoid clashing with a local PG on 5432)
docker compose up -d

# 4. Apply migrations
python -m alembic upgrade head

# 5. Seed the first admin (uses ADMIN_EMAIL / ADMIN_PASSWORD from .env)
python -m app.scripts.seed_admin

# 6. Run the API
python -m uvicorn app.main:app --reload
```

Open:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health

No Docker? Use any PostgreSQL 14+, create a database, and point `DATABASE_URL` at it.

## Environment variables

| Variable | Example | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://user:password@localhost:5433/community_db` | SQLAlchemy connection string |
| `JWT_SECRET` | long random string (32+ chars) | HS256 signing key — never commit a real one |
| `JWT_ALGORITHM` | `HS256` | Token signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access-token lifetime |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated allow-list |
| `ADMIN_EMAIL` | `admin@example.com` | Email used by the seed script |
| `ADMIN_PASSWORD` | `ChangeMe@123` | Password used by the seed script (min 8 chars) |

`.env` is git-ignored. Only `.env.example` is committed.

## Authentication

- `POST /api/v1/auth/register` → creates a **user** always (any `role` in the body is ignored)
- `POST /api/v1/auth/login` → returns `{access_token, token_type, expires_in, user}`
- Send `Authorization: Bearer <token>` on protected routes
- Roles: `user` (default) and `admin` (only created via the seed script or an admin role change)

### Trying it in Swagger UI

1. Log in via `POST /auth/login` (Try it out → Execute) and copy `access_token`
2. Click **Authorize** at the top of the page
3. Paste the token into the `Bearer` field and click **Authorize**
4. All protected endpoints now send the token automatically

### Trying it from PowerShell

```powershell
$login = curl.exe -s -X POST http://127.0.0.1:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"admin@example.com\",\"password\":\"ChangeMe@123\"}'
$token = ($login | ConvertFrom-Json).access_token
$H = @{ Authorization = "Bearer $token" }

Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/me -Headers $H
Invoke-RestMethod http://127.0.0.1:8000/api/v1/admin/conversations -Headers $H
```

## Endpoints

Base path: `/api/v1`. Full details and schemas in `/docs`.

### Auth & users
| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/auth/register` | public | Register (always creates `user`) |
| POST | `/auth/login` | public | Login → JWT |
| GET | `/auth/me` | logged-in | Own profile |
| PATCH | `/users/{user_id}/role` | admin | Change a user's role (no self-demotion) |

### Conversations
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/conversations` | public | Published conversations (`when`, `mode`, `search`, pagination) |
| GET | `/conversations/{id}` | public | One published conversation (404 otherwise) |
| POST | `/admin/conversations` | admin | Create (always starts as `draft`) |
| GET | `/admin/conversations` | admin | List all, any status |
| GET | `/admin/conversations/{id}` | admin | Get any status |
| PATCH | `/admin/conversations/{id}` | admin | Partial update (status unchanged) |
| POST | `/admin/conversations/{id}/publish` | admin | draft → published |
| POST | `/admin/conversations/{id}/unpublish` | admin | published → draft |
| POST | `/admin/conversations/{id}/cancel` | admin | draft/published → cancelled |
| DELETE | `/admin/conversations/{id}` | admin | Hard delete (204) |

### Investor requests
| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/investor-requests` | logged-in | Submit a funding request (`pending` + history row) |
| GET | `/investor-requests/me` | logged-in | Own requests only |
| GET | `/investor-requests/{id}` | owner/admin | Detail incl. status history (404 for strangers) |
| GET | `/admin/investor-requests` | admin | All requests (status, stage, dates, search) |
| GET | `/admin/investor-requests/{id}` | admin | Full detail incl. review metadata |
| PATCH | `/admin/investor-requests/{id}/status` | admin | Status transition + history row |

## Conventions

**Errors** — every error uses one envelope:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": [{ "field": "email", "issue": "Invalid email format" }]
  }
}
```
Codes: `400 BAD_REQUEST`, `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 NOT_FOUND`, `409 CONFLICT`, `422 VALIDATION_ERROR`, `500 INTERNAL_ERROR`.

**Pagination** — all list endpoints accept `page` (default 1) and `page_size` (default 10, max 50):
```json
{ "items": [], "page": 1, "page_size": 10, "total_items": 42, "total_pages": 5 }
```

**Business rules**
- Conversations: `scheduled_at` must be future on create/publish; cancelled is terminal; `speakers` (max 10) is replaced only when sent; drafts are never publicly visible
- Investor requests: `pending → under_review → approved|rejected` (also `pending → approved|rejected`); `approved`/`rejected` are terminal; rejecting requires `admin_notes`; every change writes a history row in the same transaction

## Running tests

```powershell
python -m pytest -q
```

The suite (40 tests) covers the acceptance criteria of the PRD: auth (7.4), conversations (8.5) and investor requests (9.4). It creates/uses a separate database `community_test_db` on the same Postgres instance, applies migrations, and truncates tables between tests — nothing touches `community_db`.

## Project structure

```
backend/
├── app/
│   ├── main.py                 # app factory, CORS, request logging, error handlers
│   ├── core/                   # config, security (bcrypt/JWT), error envelope
│   ├── db/                     # engine, session, declarative base
│   ├── models/                 # users, conversations, speakers, investor requests, history
│   ├── schemas/                # Pydantic request/response models
│   ├── api/deps.py             # get_current_user, require_admin (HTTPBearer)
│   ├── api/v1/                 # route modules + router
│   ├── services/               # business rules (transitions, upcoming/past, history)
│   └── scripts/seed_admin.py
├── alembic/                    # migrations (versions/0001_initial.py)
├── tests/                      # pytest suite + conftest fixtures
├── docker-compose.yml          # Postgres 16 on port 5433
├── .env.example
├── requirements.txt
└── pytest.ini
```

## Assumptions & out of scope

Per the PRD: no Google login, no email verification / password reset, no booking or seat tracking (conversation `capacity` is informational), no notifications, no payments, no refresh tokens. Investor requests are never deleted; conversations are hard-deleted. A single `admin` role is enough.

Possible next steps: refresh tokens with revocation, email notifications for investor-request status changes, conversation booking with seat counts, member profiles.
