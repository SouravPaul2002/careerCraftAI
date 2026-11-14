# CareerCraft AI — Codebase Guide (Up to Phase 2 Completed)

This guide documents every implemented file, class, and function in **CareerCraft AI** through the completion of **Phase 1 (Project Foundation & Authentication)** and **Phase 2 (External Account Integration & Data Discovery)**.

> Empty placeholder files/directories created from [`folder_structure.txt`](folder_structure.txt) for future phases (Phases 3–10) are not listed here until implemented.

---

## 1. Root & Configuration Files

| File | Purpose |
|---|---|
| [`.gitignore`](.gitignore) | Prevents committing `.env`, virtual environments (`myenv/`), `node_modules/`, `__pycache__/`, frontend `dist/`, and temporary `storage/` files. |
| [`.vscode/settings.json`](.vscode/settings.json) | Points the editor's Python tools to `backend/myenv/Scripts/python.exe` and adds `backend` to import search paths. |
| [`pyrefly.toml`](pyrefly.toml) | Configures the Pyrefly Python type checker to use `backend/myenv`, search `backend/`, and exclude `myenv/` and `frontend/`. |
| [`helper.md`](helper.md) | Master technical blueprint and 10-phase development plan. |
| [`README.md`](README.md) | Project overview, API endpoint summary, environment variable list, and local run instructions. |
| [`backend/requirements.txt`](backend/requirements.txt) | Python dependencies grouped by role (FastAPI, SQLAlchemy/PostgreSQL, Auth, LangChain/LangGraph, RAG, MCP, Jinja2, Pytest). |
| [`backend/.env.example`](backend/.env.example) | Template for backend environment variables (`DATABASE_URL`, `SECRET_KEY`, Google & GitHub OAuth credentials, etc.). |
| [`frontend/package.json`](frontend/package.json) | Frontend dependencies (`react`, `react-dom`, `react-router-dom`), dev tools (`vite`, `typescript`), and `@rollup/wasm-node` override for Windows. |
| [`frontend/.env.example`](frontend/.env.example) | Frontend API base URL template (`VITE_API_BASE_URL=http://localhost:8000`). |
| [`frontend/tsconfig.json`](frontend/tsconfig.json) | TypeScript compiler settings (`strict: true`, `react-jsx`). |
| [`frontend/vite.config.ts`](frontend/vite.config.ts) | Vite configuration using `@vitejs/plugin-react` on port `3000`. |
| [`frontend/index.html`](frontend/index.html) | HTML root page mounting `/src/main.tsx` inside `<div id="root">`. |

---

## 2. Backend (`backend/app/`)

### A. Entrypoint & Configuration

- **[`backend/app/main.py`](backend/app/main.py)**
  - `lifespan(app)` — FastAPI startup handler that automatically runs `create_tables()` so PostgreSQL tables exist before requests arrive.
  - `app` — FastAPI instance with `CORSMiddleware` (allowing `settings.FRONTEND_URL`) and registered routers (`auth`, `google_drive`, `github`, `discovery`).
  - `read_root()` (`GET /`) — Returns welcome message with the app name.
  - `health_check()` (`GET /health`) — Basic backend liveness check (`{"status": "ok"}`).
  - `database_health_check(db)` (`GET /health/db`) — Executes `SELECT 1` via SQLAlchemy to confirm PostgreSQL connectivity.

- **[`backend/app/config/settings.py`](backend/app/config/settings.py)**
  - `class Settings(BaseSettings)` — Loads `.env` configuration into typed Python fields (`APP_NAME`, `DEBUG`, `FRONTEND_URL`, `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `TOKEN_ENCRYPTION_KEY`, `GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI`, `GITHUB_CLIENT_ID/SECRET/REDIRECT_URI`).
  - `settings` — Global `Settings()` instance imported across the backend.

---

### B. Database (`backend/app/database/`)

- **[`backend/app/database/connection.py`](backend/app/database/connection.py)**
  - Normalizes `postgresql://` URLs to `postgresql+psycopg2://` so SQLAlchemy 2.1 uses the installed `psycopg2-binary` driver.
  - `engine` — SQLAlchemy engine with `pool_pre_ping=True`.
  - `Base` — `declarative_base()` parent class inherited by all ORM models.
  - `create_tables()` — Calls `Base.metadata.create_all(bind=engine)` to create missing tables in PostgreSQL.
  - `test_connection()` — Runs `SELECT 1` directly on the engine to verify database connectivity.

- **[`backend/app/database/session.py`](backend/app/database/session.py)**
  - `SessionLocal` — SQLAlchemy `sessionmaker` factory for per-request database sessions.
  - `get_db()` — FastAPI dependency generator that opens a session, yields it to a route, and closes it safely in `finally`.

---

### C. SQLAlchemy Database Models (`backend/app/models/`)

- **[`backend/app/models/__init__.py`](backend/app/models/__init__.py)** — Imports `User`, `ExternalConnection`, and `DiscoveredItem` so `create_tables()` detects every model.
- **[`backend/app/models/user.py`](backend/app/models/user.py)**
  - `class User(Base)` (`users` table) — Stores registered accounts: `id`, `email` (unique), `full_name`, `hashed_password`, `is_active`, and `created_at`.
- **[`backend/app/models/external_connection.py`](backend/app/models/external_connection.py)**
  - `class ExternalConnection(Base)` (`external_connections` table) — Stores per-user OAuth connections (`user_id`, `provider`, `provider_account_id`, `provider_email`, `encrypted_access_token`, `encrypted_refresh_token`, `token_expires_at`, `scopes`, timestamps) with a unique `(user_id, provider)` constraint.
- **[`backend/app/models/discovered_item.py`](backend/app/models/discovered_item.py)**
  - `class DiscoveredItem(Base)` (`discovered_items` table) — Persists discovered Google Drive documents and GitHub repositories per user (`user_id`, `source_type`, `external_id`, `title`, `subtitle`, `url`, `is_relevant`, `is_selected`, `details` JSON, `discovered_at`) with a unique `(user_id, source_type, external_id)` constraint.

---

### D. Pydantic Schemas (`backend/app/schemas/`)

- **[`backend/app/schemas/__init__.py`](backend/app/schemas/__init__.py)** — Re-exports all schemas.
- **[`backend/app/schemas/user.py`](backend/app/schemas/user.py)**
  - `UserRegister` — Validates registration payload (`email`, `full_name`, `password`).
  - `UserLogin` — Validates login payload (`email`, `password`).
  - `UserResponse` — Safe user response (excludes `hashed_password`).
  - `TokenResponse` — Login response containing `access_token`, `token_type`, and `user`.
- **[`backend/app/schemas/integration.py`](backend/app/schemas/integration.py)**
  - `OAuthUrlResponse` — Returns `{ auth_url }` to start OAuth login.
  - `GoogleConnectionStatus` / `GitHubConnectionStatus` — Connection status, account email/username, granted scopes, and timestamp.
  - `DriveFileItem` / `DriveFilesResponse` — Metadata for discovered PDF/DOCX Drive files with `is_candidate_relevant` and `relevance_reason`.
  - `GitHubRepoItem` / `GitHubReposResponse` — Metadata for public GitHub repositories (`language`, `stars`, `forks`, `topics`, `is_fork`, relevance).
  - `GitHubFileItem` / `GitHubRepoFilesResponse` — Classified repository files (`documentation`, `manifest`, `source`), `has_readme`, and detected manifests.
- **[`backend/app/schemas/discovery.py`](backend/app/schemas/discovery.py)**
  - `DiscoveredSourceSummary` — Per-provider summary (`connected`, `status`, `item_count`, `error`).
  - `DiscoveredItemResponse` — Serialized `DiscoveredItem` row.
  - `DiscoveryWorkflowResponse` — Combined discovery result (`sources`, `total_items`, `selected_count`, `items`).
  - `UpdateItemSelectionRequest` — Body `{ is_selected }` to toggle review selection.

---

### E. Auth, Security & OAuth Helpers (`backend/app/auth/`)

- **[`backend/app/auth/security.py`](backend/app/auth/security.py)**
  - `hash_password(password)` — Hashes plain-text passwords with `bcrypt` and a random salt.
  - `verify_password(plain_password, hashed_password)` — Verifies login passwords with `bcrypt.checkpw` (with a safe >72-byte check).
  - `_get_fernet()` — Builds a Fernet cipher from `TOKEN_ENCRYPTION_KEY` (or derives a 32-byte key from `SECRET_KEY`).
  - `encrypt_token(plain_token)` / `decrypt_token(encrypted_token)` — Encrypts OAuth tokens before saving to PostgreSQL and decrypts them when calling external APIs.

- **[`backend/app/auth/jwt.py`](backend/app/auth/jwt.py)**
  - `create_access_token(data)` — Signs a JWT with an expiration timestamp (`ACCESS_TOKEN_EXPIRE_MINUTES`).
  - `decode_access_token(token)` — Verifies and decodes a JWT using `SECRET_KEY`, returning `None` if invalid or expired.

- **[`backend/app/auth/oauth.py`](backend/app/auth/oauth.py)**
  - `create_oauth_state(user_id, provider)` / `verify_oauth_state(state, expected_provider)` — Generates and verifies short-lived (10-minute) signed JWT `state` tokens for OAuth CSRF protection.
  - `build_google_auth_url(state)` — Builds Google consent URL (`drive.readonly` + `userinfo.email`, `access_type=offline`, `prompt=consent`).
  - `exchange_google_code(code)` — Exchanges Google authorization code for access & refresh tokens.
  - `refresh_google_access_token(refresh_token)` — Requests a new Google access token using a stored refresh token.
  - `get_google_user_info(access_token)` — Fetches the connected Google account ID and email.
  - `build_github_auth_url(state)` — Builds GitHub OAuth URL (`read:user`, `public_repo`).
  - `exchange_github_code(code)` — Exchanges GitHub authorization code for an access token (`Accept: application/json`).
  - `get_github_user_info(access_token)` — Fetches the connected GitHub user's ID and `login` username.

---

### F. Services (`backend/app/services/`)

- **[`backend/app/services/google_drive_service.py`](backend/app/services/google_drive_service.py)**
  - `get_google_connection(user_id, db)` / `save_google_connection(...)` / `disconnect_google_connection(user_id, db)` — CRUD for encrypted Google Drive connections.
  - `_refresh_connection_token(connection, db)` & `_get_valid_access_token(connection, db)` — Decrypts the token and automatically refreshes it via Google if near/past expiration.
  - `classify_drive_file(raw_file)` — Accepts strictly **PDF** (`application/pdf`) and **DOCX** (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`) MIME types and flags filename matches (`resume`, `cv`, `cover`, `portfolio`, etc.).
  - `fetch_relevant_drive_files(user_id, db)` — Queries Google Drive API v3 for non-trashed PDF/DOCX files (retrying once on 401 if a refresh token exists) and sorts relevant files first.

- **[`backend/app/services/github_service.py`](backend/app/services/github_service.py)**
  - `_github_headers(access_token)` — Builds GitHub REST API v3 headers.
  - `get_github_connection(user_id, db)` / `save_github_connection(...)` / `disconnect_github_connection(user_id, db)` — CRUD for encrypted GitHub connections.
  - `classify_github_repo(raw_repo)` — Converts repo metadata and marks original (non-fork) repositories with language/description as candidate-relevant.
  - `fetch_authorized_repositories(user_id, db)` — Fetches strictly **public** repositories (`visibility=public`) and sorts original projects first.
  - `classify_repo_file(path, size_bytes)` — Categorizes repo files into `documentation` (`README*`, `docs/*.md`), `manifest` (`package.json`, `requirements.txt`, `pyproject.toml`, `Dockerfile`, etc.), or `source` code, while skipping `node_modules/`, `myenv/`, `venv/`, `.git/`, `dist/`, etc.
  - `fetch_repository_relevant_files(user_id, owner, repo, db)` — Validates repo slug and public visibility, inspects the default branch Git tree in one API call, handles empty repos (`409`), and returns categorized files + manifest summary.

- **[`backend/app/services/discovery_service.py`](backend/app/services/discovery_service.py)**
  - `_upsert_discovered_item(...)` — Inserts or updates `DiscoveredItem` rows while preserving the user's manual `is_selected` choice across re-scans.
  - `_remove_stale_items(...)` — Deletes items that disappeared from a source when a scan succeeds.
  - `_discover_google_drive(user_id, db)` — Runs Drive PDF/DOCX discovery and isolates any API error into a `DiscoveredSourceSummary`.
  - `_discover_github(user_id, db)` — Runs GitHub public repo discovery and inspects files/manifests for up to the top 5 candidate-relevant repos.
  - `run_candidate_discovery(user_id, db)` — Orchestrates Drive + GitHub discovery together and persists results.
  - `get_saved_discovery(user_id, db, sources)` — Loads persisted `DiscoveredItem` rows and source statuses from PostgreSQL.
  - `update_discovered_item_selection(user_id, item_id, is_selected, db)` — Updates `is_selected` for an item owned by the current user (`404` otherwise).

---

### G. API Dependencies & Routes (`backend/app/api/`)

- **[`backend/app/api/dependencies.py`](backend/app/api/dependencies.py)**
  - `get_current_user(credentials, db)` — Extracts `Authorization: Bearer <token>`, decodes the JWT, checks the user exists and is active in PostgreSQL, and raises `401 Unauthorized` on invalid/missing tokens.

- **[`backend/app/api/routes/auth.py`](backend/app/api/routes/auth.py)** (`/api/auth`)
  - `register_user()` (`POST /register`) — Validates input, checks duplicate email, hashes password, and creates the `User`.
  - `login_user()` (`POST /login`) — Verifies credentials and returns JWT `access_token` + `user`.
  - `get_me()` (`GET /me`) — Protected endpoint returning the current `User`.

- **[`backend/app/api/routes/google_drive.py`](backend/app/api/routes/google_drive.py)** (`/api/integrations/google`)
  - `get_google_auth_url()` (`GET /auth-url`) — *(Protected)* Returns Google OAuth URL with signed `state`.
  - `google_oauth_callback()` (`GET /callback`) — Validates `state`, exchanges code, saves encrypted tokens, and redirects to `/dashboard?google=connected` (or `?google=error`).
  - `get_google_status()` (`GET /status`) — *(Protected)* Returns connection status and Google email.
  - `disconnect_google()` (`DELETE /disconnect`) — *(Protected)* Deletes stored Google tokens.
  - `list_google_drive_files()` (`GET /files`) — *(Protected)* Returns authorized PDF and DOCX metadata.

- **[`backend/app/api/routes/github.py`](backend/app/api/routes/github.py)** (`/api/integrations/github`)
  - `get_github_auth_url()` (`GET /auth-url`) — *(Protected)* Returns GitHub OAuth URL (`public_repo`, `read:user`) with signed `state`.
  - `github_oauth_callback()` (`GET /callback`) — Validates `state`, exchanges code, saves encrypted token + username, and redirects to `/dashboard?github=connected`.
  - `get_github_status()` (`GET /status`) — *(Protected)* Returns connection status and GitHub username.
  - `disconnect_github()` (`DELETE /disconnect`) — *(Protected)* Deletes stored GitHub token.
  - `list_github_repos()` (`GET /repos`) — *(Protected)* Lists authorized public repositories.
  - `list_github_repo_files()` (`GET /repos/{owner}/{repo}/files`) — *(Protected)* Inspects relevant files inside a public repository.

- **[`backend/app/api/routes/discovery.py`](backend/app/api/routes/discovery.py)** (`/api/discovery`)
  - `start_candidate_discovery()` (`POST /run`) — *(Protected)* Runs unified candidate discovery across Drive & GitHub.
  - `list_discovered_items()` (`GET /items`) — *(Protected)* Returns saved discovered items.
  - `toggle_discovered_item()` (`PATCH /items/{item_id}`) — *(Protected)* Selects/deselects a discovered item for review.

---

## 3. Frontend (`frontend/src/`)

### A. Entry, Routing & Styling

- [`frontend/src/vite-env.d.ts`](frontend/src/vite-env.d.ts) — Adds TypeScript types for `import.meta.env`.
- [`frontend/src/main.tsx`](frontend/src/main.tsx) — Mounts `<App />` and loads `index.css`.
- [`frontend/src/index.css`](frontend/src/index.css) — Clean CSS styling for auth cards, dashboard layout, integration panels, status badges, and discovery lists.
- **[`frontend/src/App.tsx`](frontend/src/App.tsx)**
  - `App()` — Wraps the app in `<AuthProvider>` and `<BrowserRouter>`, defining `/login`, `/register`, protected `/dashboard`, and fallback redirects.

### B. Types (`frontend/src/types/`)

- [`frontend/src/types/auth.ts`](frontend/src/types/auth.ts) — `User`, `RegisterRequest`, `LoginRequest`, `LoginResponse`.
- [`frontend/src/types/integration.ts`](frontend/src/types/integration.ts) — `GoogleConnectionStatus`, `DriveFileItem`, `DriveFilesResponse`, `GitHubConnectionStatus`, `GitHubRepoItem`, `GitHubReposResponse`, `GitHubFileItem`, `GitHubRepoFilesResponse`.
- [`frontend/src/types/discovery.ts`](frontend/src/types/discovery.ts) — `DiscoveredSourceSummary`, `DiscoveredItem`, `DiscoveryWorkflowResponse`.

### C. API Services (`frontend/src/services/`)

- **[`frontend/src/services/authService.ts`](frontend/src/services/authService.ts)** — `registerUser()`, `loginUser()`, `getCurrentUser()` (calls `/api/auth/*` via `fetch`).
- **[`frontend/src/services/googleDriveService.ts`](frontend/src/services/googleDriveService.ts)** — `getGoogleAuthUrl()`, `getGoogleStatus()`, `disconnectGoogleDrive()`, `fetchGoogleDriveFiles()`.
- **[`frontend/src/services/githubService.ts`](frontend/src/services/githubService.ts)** — `getGitHubAuthUrl()`, `getGitHubStatus()`, `disconnectGitHub()`, `fetchGitHubRepos()`, `fetchGitHubRepoFiles()`.
- **[`frontend/src/services/discoveryService.ts`](frontend/src/services/discoveryService.ts)** — `getDiscoveredItems()`, `runCandidateDiscovery()`, `updateDiscoveredItemSelection()`.

### D. Auth State & Hooks (`frontend/src/contexts/` & `frontend/src/hooks/`)

- **[`frontend/src/contexts/AuthContext.tsx`](frontend/src/contexts/AuthContext.tsx)**
  - `AuthContext` & `AuthProvider()` — Manages `user`, `token` (stored in `localStorage` under `careercraft_access_token`), and `isLoading`. Automatically restores the session on page refresh via `getCurrentUser()`, and exposes `login()`, `register()`, and `logout()`.
- **[`frontend/src/hooks/useAuth.ts`](frontend/src/hooks/useAuth.ts)**
  - `useAuth()` — Hook for reading `AuthContext` inside components and pages.

### E. Components, Layout & Pages (`frontend/src/components/`, `layouts/`, `pages/`)

- **[`frontend/src/components/ProtectedRoute.tsx`](frontend/src/components/ProtectedRoute.tsx)** — `ProtectedRoute()` waits while session check finishes, redirects unauthenticated users to `/login`, or renders protected content.
- **[`frontend/src/components/GoogleDriveCard.tsx`](frontend/src/components/GoogleDriveCard.tsx)** — `GoogleDriveCard()` displays Google Drive OAuth status, handles `?google=connected` / `?google=error` callback query params, connects/disconnects Drive, and lists PDF/DOCX files.
- **[`frontend/src/components/GitHubCard.tsx`](frontend/src/components/GitHubCard.tsx)** — `GitHubCard()` displays GitHub OAuth status, connects/disconnects GitHub, lists public repositories, and lets you inspect README/manifest/source files per repo.
- **[`frontend/src/components/DiscoveryCard.tsx`](frontend/src/components/DiscoveryCard.tsx)** — `DiscoveryCard()` loads saved discoveries, runs the combined discovery workflow (`POST /api/discovery/run`), and lets you check/uncheck items (`PATCH /api/discovery/items/{id}`) to review before Phase 3.
- **[`frontend/src/layouts/DashboardLayout.tsx`](frontend/src/layouts/DashboardLayout.tsx)** — `DashboardLayout()` renders the top navigation bar (brand, user name/email, **Log out** button) and main page container.
- **[`frontend/src/pages/LoginPage.tsx`](frontend/src/pages/LoginPage.tsx)** — `LoginPage()` provides the sign-in form and redirects to `/dashboard`.
- **[`frontend/src/pages/RegisterPage.tsx`](frontend/src/pages/RegisterPage.tsx)** — `RegisterPage()` provides the registration form and redirects to `/login` with a confirmation message.
- **[`frontend/src/pages/DashboardPage.tsx`](frontend/src/pages/DashboardPage.tsx)** — `DashboardPage()` renders the welcome account summary, `<GoogleDriveCard />`, `<GitHubCard />`, `<DiscoveryCard />`, and upcoming Phase 3–9 cards.

