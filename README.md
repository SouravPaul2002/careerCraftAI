# CareerCraft AI

Multi-Agent AI Job Application Assistant built with FastAPI, React + TypeScript, PostgreSQL, LangGraph, ChromaDB, and MCP.

## Current Progress

### Phase 1 — Project Foundation & Authentication (Complete)
- **Frontend:** React + TypeScript (Vite), React Router protected routes (`/dashboard`), `/register`, `/login`, and initial dashboard.
- **Backend:** FastAPI + CORS, PostgreSQL + SQLAlchemy ORM, `bcrypt` password hashing, JWT Bearer authentication.
- **Model (`users`):** `id`, `email`, `full_name`, `hashed_password`, `is_active`, `created_at`.

### Phase 2 · Step 1 — Google Drive Integration (Complete)
- **OAuth 2.0:** Read-only Google Drive consent flow (`drive.readonly` + `userinfo.email`) protected with signed `state`.
- **Encrypted Token Storage (`external_connections`):** Stores `encrypted_access_token` and `encrypted_refresh_token` encrypted with Fernet in PostgreSQL, isolated per user (`user_id` + `provider`).
- **Document Discovery:** Retrieves authorized Drive metadata filtered strictly to **PDF** and **DOCX** files (`trashed = false`) and highlights candidate-relevant files.
- **Automatic Refresh:** Refreshes expired Google access tokens automatically when `refresh_token` is present.

### Phase 2 · Step 2 — GitHub Integration (Complete)
- **OAuth 2.0:** GitHub OAuth flow (`read:user`, `public_repo` scopes) for public repositories only.
- **Encrypted Token Storage (`external_connections`):** Stores encrypted GitHub access token and username per user.
- **Repository & File Discovery:** Retrieves authorized public repositories (`visibility=public`) and inspects repo trees to identify documentation (`README`, `docs/*.md`), dependency manifests (`package.json`, `requirements.txt`, `pyproject.toml`, etc.), and source files while ignoring `node_modules`, `venv`, and build folders.

### Phase 2 · Step 3 — Initial Candidate Data Discovery (Complete)
- **Discovery Workflow (`discovered_items`):** Collects Drive PDF/DOCX metadata and GitHub public repositories (including README/manifest inspection for top projects) in one workflow, persists discovered items per user in PostgreSQL, and preserves review selections (`is_selected`) across re-scans.
- **Review UI:** Dashboard **Initial Candidate Data Discovery** panel lets the user run discovery, inspect collected metadata, and check/uncheck items before Phase 3 RAG ingestion.

### API Endpoints
- `GET /` — API welcome message
- `GET /health` — Backend health check
- `GET /health/db` — PostgreSQL connection check
- `POST /api/auth/register` — Register a new user
- `POST /api/auth/login` — Authenticate and receive a JWT access token
- `GET /api/auth/me` — Protected endpoint returning the signed-in user
- `GET /api/integrations/google/auth-url` — *(Protected)* Get Google OAuth consent URL
- `GET /api/integrations/google/callback` — OAuth callback storing encrypted tokens and redirecting to dashboard
- `GET /api/integrations/google/status` — *(Protected)* Check Google Drive connection status
- `DELETE /api/integrations/google/disconnect` — *(Protected)* Disconnect Google Drive
- `GET /api/integrations/google/files` — *(Protected)* Retrieve authorized PDF & DOCX file metadata
- `GET /api/integrations/github/auth-url` — *(Protected)* Get GitHub OAuth authorization URL
- `GET /api/integrations/github/callback` — GitHub OAuth callback storing encrypted token and redirecting to dashboard
- `GET /api/integrations/github/status` — *(Protected)* Check GitHub connection status
- `DELETE /api/integrations/github/disconnect` — *(Protected)* Disconnect GitHub
- `GET /api/integrations/github/repos` — *(Protected)* Retrieve authorized public repositories
- `GET /api/integrations/github/repos/{owner}/{repo}/files` — *(Protected)* Identify relevant documentation, manifests, and source files
- `POST /api/discovery/run` — *(Protected)* Run candidate discovery across connected accounts and persist results
- `GET /api/discovery/items` — *(Protected)* Fetch saved discovered items and source statuses
- `PATCH /api/discovery/items/{item_id}` — *(Protected)* Toggle `is_selected` on a discovered item

### Environment Variables (`backend/.env`)
See [`backend/.env.example`](backend/.env.example):
- `APP_NAME`, `DEBUG`, `FRONTEND_URL`
- `DATABASE_URL`
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `TOKEN_ENCRYPTION_KEY` *(optional; derived from `SECRET_KEY` if blank)*
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI`

---

## Running Locally

### 1. Backend
From `backend/`:
```powershell
.\myenv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`

### 2. Frontend
From `frontend/`:
```powershell
npm.cmd run dev
```
- App URL: `http://localhost:3000`
