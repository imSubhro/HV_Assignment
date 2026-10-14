# Product Requirements Document (PRD)

## Community Platform Backend: Authentication, Conversation Management & Investor Requests

| Field | Value |
|---|---|
| Document type | PRD + technical spec for backend/API development |
| Audience | Backend developer |
| Version | 1.0 |
| Scope | 3 modules: User Registration & Authentication, Conversation Management, Investor Request Management |
| Deliverable | REST API + PostgreSQL database + README + Swagger docs |

---

## 1. Overview

A community platform hosts **conversations** (events with speakers) and lets members submit **investor requests** (funding enquiries) that admins review. This document specifies the backend for three modules:

| # | Module | Summary |
|---|---|---|
| 1 | User Registration & Authentication | Email/password signup and login, JWT sessions, user/admin roles |
| 3 | Investor Request Management | Authenticated users submit funding requests; admins review and update status |
| 4 | Conversation Management System | Admins create, edit, schedule, publish and manage conversations with speakers; public users browse upcoming and past ones |

The goal is a clean, well-documented, easy-to-run API. No frontend is required.

---

## 2. Goals and Non-Goals

### 2.1 Goals
- Working REST APIs for all three modules, with consistent request/response and error formats.
- Secure authentication (hashed passwords, JWT) and role-based access control (RBAC).
- Relational data model with proper constraints and indexes.
- Auto-generated API docs (Swagger/OpenAPI) and a README that lets anyone run the project in under 10 minutes.

### 2.2 Non-Goals (out of scope)
- Google login 
- Email verification, forgot/reset password
- Booking, seat availability, notifications and emails
- Member profiles and networking
- Frontend / UI
- Payments

---

## 3. Recommended Tech Stack

The developer may substitute equivalents, but the structure of this PRD assumes:

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | PostgreSQL 14+ |
| ORM | SQLAlchemy 2.x (Alembic for migrations, optional but preferred) |
| Validation | Pydantic v2 |
| Password hashing | bcrypt (via `passlib` or `bcrypt`) |
| Tokens | JWT (`python-jose` or `PyJWT`), HS256 |
| Config | `.env` file via `pydantic-settings` |
| Testing | `pytest` + FastAPI `TestClient` |
| Optional | Docker + `docker-compose.yml` (API + Postgres) |

---

## 4. User Roles

| Role | Description | Permissions |
|---|---|---|
| `user` | Default role on registration | View published conversations; submit and view **own** investor requests |
| `admin` | Platform administrator | Everything a user can do, plus manage conversations and review all investor requests |

- Public registration **always** creates a `user`. The `role` field in the signup body must be ignored.
- The first admin is created by a **seed script** (`python -m app.scripts.seed_admin`) using `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `.env`.

---

## 5. Data Model

Use UUID primary keys (or auto-increment integers, as long as it is consistent). All tables have `created_at` and `updated_at` (UTC timestamps).

### 5.1 `users`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| full_name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(255) | NOT NULL, UNIQUE (stored lowercase) |
| password_hash | VARCHAR(255) | NOT NULL |
| role | ENUM(`user`,`admin`) | NOT NULL, default `user` |
| is_active | BOOLEAN | NOT NULL, default `true` |
| created_at, updated_at | TIMESTAMPTZ | NOT NULL |

### 5.2 `conversations`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| title | VARCHAR(200) | NOT NULL |
| description | TEXT | NOT NULL |
| scheduled_at | TIMESTAMPTZ | NOT NULL (start time) |
| duration_minutes | INTEGER | NOT NULL, > 0 |
| mode | ENUM(`online`,`offline`) | NOT NULL |
| location_or_link | VARCHAR(500) | NOT NULL (venue address or meeting URL) |
| capacity | INTEGER | NULL, > 0 if present (informational only; no booking logic in this scope) |
| cover_image_url | VARCHAR(500) | NULL |
| status | ENUM(`draft`,`published`,`cancelled`) | NOT NULL, default `draft` |
| created_by | UUID | FK → users.id |
| created_at, updated_at | TIMESTAMPTZ | NOT NULL |

Indexes: `(status, scheduled_at)`.

### 5.3 `conversation_speakers`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| conversation_id | UUID | FK → conversations.id, ON DELETE CASCADE |
| name | VARCHAR(100) | NOT NULL |
| designation | VARCHAR(150) | NULL |
| bio | TEXT | NULL |
| photo_url | VARCHAR(500) | NULL |
| display_order | INTEGER | NOT NULL, default 0 |

### 5.4 `investor_requests`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL |
| full_name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(255) | NOT NULL |
| phone | VARCHAR(20) | NULL |
| company_name | VARCHAR(200) | NOT NULL |
| funding_stage | ENUM(`idea`,`pre_seed`,`seed`,`series_a`,`series_b_plus`) | NOT NULL |
| funding_amount | NUMERIC(14,2) | NOT NULL, > 0 |
| currency | CHAR(3) | NOT NULL, default `INR` (ISO 4217) |
| description | TEXT | NOT NULL (business/funding need, min 20 chars) |
| status | ENUM(`pending`,`under_review`,`approved`,`rejected`) | NOT NULL, default `pending` |
| admin_notes | TEXT | NULL |
| reviewed_by | UUID | FK → users.id, NULL |
| reviewed_at | TIMESTAMPTZ | NULL |
| created_at, updated_at | TIMESTAMPTZ | NOT NULL |

Indexes: `(user_id)`, `(status, created_at)`.

### 5.5 `investor_request_status_history` (for status tracking)

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| request_id | UUID | FK → investor_requests.id, ON DELETE CASCADE |
| from_status | ENUM (same as above) | NULL for first entry |
| to_status | ENUM (same as above) | NOT NULL |
| changed_by | UUID | FK → users.id |
| note | TEXT | NULL |
| changed_at | TIMESTAMPTZ | NOT NULL |

A history row is written when a request is created (`from_status = NULL`, `to_status = pending`) and on every status change.

### 5.6 Entity relationships

```
users 1 ──< conversations (created_by)
conversations 1 ──< conversation_speakers
users 1 ──< investor_requests (user_id)
investor_requests 1 ──< investor_request_status_history
```

---

## 6. API Conventions

- **Base path:** `/api/v1`
- **Format:** JSON only, `Content-Type: application/json`
- **Auth:** `Authorization: Bearer <access_token>`
- **Timestamps:** ISO 8601 in UTC, e.g. `2026-11-20T14:30:00Z`
- **IDs:** UUID strings

### 6.1 Standard error format

All errors return this shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": [{ "field": "email", "issue": "Invalid email format" }]
  }
}
```

| HTTP | `code` | When |
|---|---|---|
| 400 | `BAD_REQUEST` | Malformed request or invalid state transition |
| 401 | `UNAUTHORIZED` | Missing, invalid or expired token; wrong credentials |
| 403 | `FORBIDDEN` | Authenticated but lacks the role/ownership |
| 404 | `NOT_FOUND` | Resource does not exist (or is hidden from this user) |
| 409 | `CONFLICT` | Duplicate resource (e.g. email already registered) |
| 422 | `VALIDATION_ERROR` | Field validation failed |
| 500 | `INTERNAL_ERROR` | Unexpected server error (never leak stack traces) |

### 6.2 Standard pagination (all list endpoints)

Query params: `page` (default 1, min 1), `page_size` (default 10, min 1, max 50).

```json
{
  "items": [],
  "page": 1,
  "page_size": 10,
  "total_items": 42,
  "total_pages": 5
}
```

---

## 7. Module 1: User Registration & Authentication

### 7.1 Functional requirements
- FR-1.1: A visitor can register with full name, email and password.
- FR-1.2: A registered user can log in and receive a JWT access token.
- FR-1.3: A logged-in user can fetch their own profile.
- FR-1.4: Protected endpoints reject missing/invalid/expired tokens.
- FR-1.5: Admin-only endpoints reject non-admin users with 403.
- FR-1.6: Inactive users (`is_active = false`) cannot log in.

### 7.2 Endpoints

#### `POST /api/v1/auth/register` (public)

Request:
```json
{
  "full_name": "Asha Verma",
  "email": "asha@example.com",
  "password": "StrongPass@123"
}
```

Rules:
- `full_name`: 2-100 chars.
- `email`: valid format; lowercased and trimmed before saving; must be unique.
- `password`: min 8 chars, with at least 1 uppercase, 1 lowercase, 1 digit.
- Any `role` field in the body is ignored.

Response `201 Created`:
```json
{
  "id": "b3f1c0a2-...",
  "full_name": "Asha Verma",
  "email": "asha@example.com",
  "role": "user",
  "created_at": "2026-10-14T09:00:00Z"
}
```
Errors: `409` (email exists), `422` (validation).

#### `POST /api/v1/auth/login` (public)

Request:
```json
{ "email": "asha@example.com", "password": "StrongPass@123" }
```

Response `200 OK`:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": { "id": "b3f1c0a2-...", "full_name": "Asha Verma", "email": "asha@example.com", "role": "user" }
}
```
Errors: `401` with a **generic** message ("Invalid email or password") for both unknown email and wrong password. Do not reveal which one failed.

#### `GET /api/v1/auth/me` (any logged-in user)

Response `200 OK`: the user object (`id`, `full_name`, `email`, `role`, `created_at`).

#### `PATCH /api/v1/users/{user_id}/role` (admin only, optional)

Request: `{ "role": "admin" }`. Response `200` with the updated user. Admin cannot demote themselves (return `400`).

### 7.3 Security requirements
- Hash passwords with bcrypt (cost factor ≥ 12). Never store or log plain passwords.
- JWT payload: `sub` (user id), `role`, `exp`, `iat`. Signed with `JWT_SECRET` from `.env`. Default expiry 60 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- Never return `password_hash` in any response.
- Implement reusable dependencies: `get_current_user`, `require_admin`.
- Enable CORS with a configurable allow-list.
- Use parameterized queries only (the ORM handles this).

### 7.4 Acceptance criteria
- [ ] Registering the same email twice returns 409 (case-insensitive).
- [ ] Weak password returns 422 with field-level details.
- [ ] Login with wrong password returns 401 with the generic message.
- [ ] `/auth/me` with no or an expired token returns 401.
- [ ] A `user` token calling any `/admin/*` route returns 403.
- [ ] Sending `"role": "admin"` during register still creates a `user`.

---

## 8. Module 4: Conversation Management System

### 8.1 Functional requirements
- FR-4.1: Admin can create a conversation (starts as `draft`) with title, description, schedule, mode, location/link and a list of speakers.
- FR-4.2: Admin can edit any field, including the schedule and the speakers list.
- FR-4.3: Admin can publish a draft, unpublish it back to draft, or cancel it.
- FR-4.4: Admin can delete a conversation.
- FR-4.5: Admin can list all conversations with filters (any status).
- FR-4.6: Public/users can list **published** conversations, filtered as **upcoming** or **past**, and view details.
- FR-4.7: Draft conversations are never visible through public endpoints (they return 404).

### 8.2 Business rules
- `scheduled_at` must be in the future when **creating** or **publishing** a conversation.
- Cannot edit `scheduled_at` of a `cancelled` conversation (400).
- Status transitions:

| From | Allowed to |
|---|---|
| `draft` | `published`, `cancelled` |
| `published` | `draft` (unpublish), `cancelled` |
| `cancelled` | none (terminal) |

- **Upcoming** = `status = published` AND `scheduled_at >= now`. Sorted by `scheduled_at` ascending.
- **Past** = `status = published` AND `scheduled_at < now`. Sorted by `scheduled_at` descending.
- Speakers: max 10 per conversation. On update, if `speakers` is provided it **replaces** the full list; if omitted, speakers are unchanged.

### 8.3 Endpoints

#### Public (no auth required)

**`GET /api/v1/conversations`**

Query params: `when` (`upcoming` | `past`, default `upcoming`), `mode` (`online` | `offline`, optional), `search` (case-insensitive match on title, optional), `page`, `page_size`.

Response `200 OK`:
```json
{
  "items": [
    {
      "id": "7c2d...",
      "title": "Founders & Funding: Early-Stage Lessons",
      "description": "An open conversation on ...",
      "scheduled_at": "2026-11-20T14:30:00Z",
      "duration_minutes": 90,
      "mode": "online",
      "location_or_link": "https://meet.example.com/abc",
      "capacity": 100,
      "cover_image_url": null,
      "status": "published",
      "speakers": [
        { "id": "a1...", "name": "Rohan Mehta", "designation": "Partner, XYZ Ventures", "bio": "...", "photo_url": null, "display_order": 0 }
      ]
    }
  ],
  "page": 1, "page_size": 10, "total_items": 1, "total_pages": 1
}
```

**`GET /api/v1/conversations/{id}`**: returns one **published** conversation (same shape as above). `404` if not found or not published.

#### Admin (JWT with role `admin`)

**`POST /api/v1/admin/conversations`**: create (status forced to `draft`).

Request:
```json
{
  "title": "Founders & Funding: Early-Stage Lessons",
  "description": "An open conversation on ...",
  "scheduled_at": "2026-11-20T14:30:00Z",
  "duration_minutes": 90,
  "mode": "online",
  "location_or_link": "https://meet.example.com/abc",
  "capacity": 100,
  "cover_image_url": null,
  "speakers": [
    { "name": "Rohan Mehta", "designation": "Partner, XYZ Ventures", "bio": "...", "photo_url": null }
  ]
}
```
Response `201 Created`: full conversation object. `display_order` is assigned from array order.

**`GET /api/v1/admin/conversations`**: list all, with filters `status` (`draft`|`published`|`cancelled`), `when` (`upcoming`|`past`), `search`, plus pagination.

**`GET /api/v1/admin/conversations/{id}`**: get one in any status.

**`PATCH /api/v1/admin/conversations/{id}`**: partial update. Any field from the create body may be sent. `status` is **not** changed here (use the action endpoints below).

**`POST /api/v1/admin/conversations/{id}/publish`**: draft → published. Validates that `scheduled_at` is in the future.

**`POST /api/v1/admin/conversations/{id}/unpublish`**: published → draft.

**`POST /api/v1/admin/conversations/{id}/cancel`**: draft/published → cancelled.

**`DELETE /api/v1/admin/conversations/{id}`**: hard delete (speakers cascade). Response `204 No Content`.

All action endpoints return the updated conversation object. Invalid transitions return `400 BAD_REQUEST` with a clear message (e.g. "Cannot publish a cancelled conversation").

### 8.4 Validation summary

| Field | Rule |
|---|---|
| title | 3-200 chars |
| description | min 10 chars |
| scheduled_at | valid ISO datetime, future on create/publish |
| duration_minutes | integer 15-480 |
| mode | `online` or `offline` |
| location_or_link | required; must be a valid URL if `mode = online` |
| capacity | optional integer ≥ 1 |
| speakers | 0-10 items; each `name` required (2-100 chars) |

### 8.5 Acceptance criteria
- [ ] Newly created conversations are `draft` and invisible on public endpoints.
- [ ] After publish, the conversation appears in `GET /conversations?when=upcoming`.
- [ ] A published conversation whose `scheduled_at` has passed appears under `when=past`.
- [ ] Publishing with a past `scheduled_at` returns 400.
- [ ] Cancelled conversations cannot be published or rescheduled.
- [ ] Updating `speakers` replaces the old list; omitting it leaves the list intact.
- [ ] A normal `user` token on any `/admin/conversations*` route returns 403.

---

## 9. Module 3: Investor Request Management

### 9.1 Functional requirements
- FR-3.1: A logged-in user can submit an investor/funding request via a form payload.
- FR-3.2: The request is stored with status `pending` and a history entry.
- FR-3.3: A user can list and view **only their own** requests, and see the current status.
- FR-3.4: Admin can list all requests with filters (status, funding stage, date range, search) and pagination.
- FR-3.5: Admin can view any request, including its status history.
- FR-3.6: Admin can move a request through its status workflow and add notes.
- FR-3.7: Every status change is recorded in the history table with who changed it and when.

### 9.2 Status workflow

```
pending ──> under_review ──> approved
   │              │
   │              └────────> rejected
   ├───────────────────────> approved
   └───────────────────────> rejected
```

| From | Allowed to |
|---|---|
| `pending` | `under_review`, `approved`, `rejected` |
| `under_review` | `approved`, `rejected` |
| `approved` | none (terminal) |
| `rejected` | none (terminal) |

Invalid transitions return `400 BAD_REQUEST`. Setting `rejected` **requires** `admin_notes` (the reason).

### 9.3 Endpoints

#### User endpoints (JWT required)

**`POST /api/v1/investor-requests`**

Request:
```json
{
  "full_name": "Asha Verma",
  "email": "asha@example.com",
  "phone": "+919876543210",
  "company_name": "GreenLoop Pvt Ltd",
  "funding_stage": "seed",
  "funding_amount": 5000000,
  "currency": "INR",
  "description": "We are building a recycling marketplace and are raising seed funding to ..."
}
```

Validation:

| Field | Rule |
|---|---|
| full_name | 2-100 chars |
| email | valid email |
| phone | optional; 10-15 digits, optional leading `+` |
| company_name | 2-200 chars |
| funding_stage | one of `idea`, `pre_seed`, `seed`, `series_a`, `series_b_plus` |
| funding_amount | number > 0 |
| currency | 3-letter ISO code, default `INR` |
| description | 20-2000 chars |

Response `201 Created`:
```json
{
  "id": "e9a4...",
  "status": "pending",
  "full_name": "Asha Verma",
  "company_name": "GreenLoop Pvt Ltd",
  "funding_stage": "seed",
  "funding_amount": 5000000,
  "currency": "INR",
  "created_at": "2026-10-14T09:30:00Z"
}
```

**`GET /api/v1/investor-requests/me`**: list the caller's own requests (paginated, newest first, optional `status` filter).

**`GET /api/v1/investor-requests/{id}`**: owner or admin only. A non-owner, non-admin gets `404` (not 403, to avoid leaking which IDs exist). Response includes `status_history`.

#### Admin endpoints (role `admin`)

**`GET /api/v1/admin/investor-requests`**

Query params: `status`, `funding_stage`, `from_date`, `to_date` (filter on `created_at`), `search` (company name or full name), `page`, `page_size`. Sorted by `created_at` descending.

**`GET /api/v1/admin/investor-requests/{id}`**: full detail including `admin_notes`, `reviewed_by`, `reviewed_at`, `status_history`.

**`PATCH /api/v1/admin/investor-requests/{id}/status`**

Request:
```json
{ "status": "under_review", "admin_notes": "Reviewing financials, will respond within a week." }
```

Behavior: validates the transition, updates `status`, `admin_notes`, `reviewed_by` and `reviewed_at`, and inserts a history row, all in **one database transaction**.

Response `200 OK`:
```json
{
  "id": "e9a4...",
  "status": "under_review",
  "admin_notes": "Reviewing financials, will respond within a week.",
  "reviewed_by": "1d7f...",
  "reviewed_at": "2026-10-15T10:00:00Z",
  "status_history": [
    { "from_status": null, "to_status": "pending", "changed_by": "b3f1...", "note": null, "changed_at": "2026-10-14T09:30:00Z" },
    { "from_status": "pending", "to_status": "under_review", "changed_by": "1d7f...", "note": "Reviewing financials, will respond within a week.", "changed_at": "2026-10-15T10:00:00Z" }
  ]
}
```

### 9.4 Acceptance criteria
- [ ] Submitting without a token returns 401.
- [ ] A new request has `status = pending` and exactly one history row.
- [ ] User A cannot read User B's request (404).
- [ ] `GET /investor-requests/me` returns only the caller's requests.
- [ ] Admin list filters (status, stage, date range, search) work and combine.
- [ ] `approved → pending` returns 400.
- [ ] `rejected` without `admin_notes` returns 422/400.
- [ ] Each status change creates a history row with the correct admin id.
- [ ] A normal `user` token on `/admin/investor-requests*` returns 403.

---

## 10. Non-Functional Requirements

| Area | Requirement |
|---|---|
| Performance | List endpoints respond in < 500 ms for 10k rows (indexes in section 5) |
| Security | Hashed passwords, JWT, RBAC, input validation, no stack traces in responses, secrets only in `.env` |
| Reliability | Multi-table writes (request + history) run in a single transaction |
| Consistency | All timestamps UTC; same error and pagination format everywhere |
| Observability | Basic request logging (method, path, status, duration); never log passwords or tokens |
| Docs | Swagger UI at `/docs` with request/response examples; README (see section 12) |

---

## 11. Suggested Project Structure

```
community-backend/
├── app/
│   ├── main.py                 # FastAPI app, routers, CORS, error handlers
│   ├── core/
│   │   ├── config.py           # Settings from .env
│   │   ├── security.py         # hashing, JWT create/verify
│   │   └── errors.py           # custom exceptions + handlers
│   ├── db/
│   │   ├── session.py          # engine, SessionLocal, get_db
│   │   └── base.py
│   ├── models/                 # user.py, conversation.py, investor_request.py
│   ├── schemas/                # Pydantic request/response models
│   ├── api/
│   │   ├── deps.py             # get_current_user, require_admin
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── conversations.py          # public routes
│   │       ├── admin_conversations.py
│   │       ├── investor_requests.py      # user routes
│   │       └── admin_investor_requests.py
│   ├── services/               # business logic (status transitions, queries)
│   └── scripts/seed_admin.py
├── alembic/                    # migrations (optional)
├── tests/
├── .env.example
├── docker-compose.yml          # optional
├── requirements.txt
└── README.md
```

Keep route handlers thin: validation in schemas, business rules (status transitions, upcoming/past logic) in `services/`.

### Environment variables (`.env.example`)

```
DATABASE_URL=postgresql://user:password@localhost:5432/community_db
JWT_SECRET=change-me-to-a-long-random-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:3000
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=ChangeMe@123
```

---

## 12. Deliverables

1. Source code in a Git repository with clear, incremental commits.
2. `README.md` containing:
   - Project description and features implemented
   - Tech stack
   - Setup steps (install, create DB, run migrations, seed admin, start server)
   - Environment variables table
   - How to run tests
   - List of endpoints (or link to `/docs`)
   - Assumptions and future improvements (Google login, email verification, booking, notifications)
3. `.env.example` (no real secrets committed).
4. A Postman collection or Swagger docs covering every endpoint.
5. Tests for the acceptance criteria in sections 7.4, 8.5 and 9.4 (at least the critical paths).

---

## 13. Suggested Build Order

| Step | Task | Done when |
|---|---|---|
| 1 | Project setup, config, DB connection, base models, error handlers | App boots and `/docs` loads |
| 2 | **Auth module**: register, login, `/me`, `get_current_user`, `require_admin`, seed admin | Section 7.4 passes |
| 3 | **Conversations (admin)**: create, update, list, get, publish/unpublish/cancel, delete | Admin flow works end to end |
| 4 | **Conversations (public)**: upcoming/past list and detail | Section 8.5 passes |
| 5 | **Investor requests (user)**: submit, my list, detail | User flow works |
| 6 | **Investor requests (admin)**: list/filter, detail, status change with history | Section 9.4 passes |
| 7 | Tests, README, Postman/Swagger examples, final cleanup | All deliverables in section 12 done |

---

## 14. Out of Scope: Future Enhancements

- Google / social login
- Email verification and password reset
- Conversation booking with seat availability and cancellations
- Email notifications and reminders (booking, status updates, investor enquiries)
- Member profiles and networking
- Refresh tokens and token revocation

---

## 15. Assumptions

- Investor requests require a logged-in user (so every request is tied to an account and ownership checks are possible).
- Conversation `capacity` is informational only; there is no booking or seat tracking in this scope.
- Hard delete is acceptable for conversations; investor requests are never deleted.
- A single admin role is enough; there are no finer-grained permissions.
