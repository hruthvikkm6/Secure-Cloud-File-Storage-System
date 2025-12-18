# Mini Google Drive 🚀

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-05998B?logo=fastapi&logoColor=white)](#)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)](#)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6?logo=typescript&logoColor=white)](#)
[![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker&logoColor=white)](#)
[![JWT](https://img.shields.io/badge/Auth-JWT-000000?logo=jsonwebtokens&logoColor=white)](#)
[![Security](https://img.shields.io/badge/Security-Argon2%20%7C%20AES--CBC-8A2BE2)](#)

A production‑minded, minimal, and secure file storage app—think “mini Google Drive”—built with a modern stack:

- FastAPI + SQLAlchemy (Python) for a blazing‑fast, typed API
- React + Vite (TypeScript) for a crisp UX
- JWT auth, Argon2 password hashing, and server‑side file encryption (AES‑CBC with PBKDF2)
- Dockerized with Nginx reverse proxy for a one‑command spin‑up


## ✨ Highlights

- Clean architecture with clear separation of concerns (API → Services → DB → Schemas)
- End‑to‑end auth using OAuth2 password flow and JWT bearer tokens
- Server‑side file encryption using a per‑file salt and IV
- Simple, documented API with ready‑to‑copy curl examples
- Dev experience: hot reload for both backend and frontend, Vite proxy for zero‑CORS friction


## 🧩 Architecture

```
+---------------------+        /api/v1        +--------------------+        +----------------------+
|   React (Vite)      |  ───────────────────▶ |    FastAPI         |  ───▶  |  SQLite (SQLAlchemy) |
|   - Auth pages       |                      |    - Auth, Files    |        +----------------------+
|   - Dashboard        | ◀─────────────────── |    - JWT Security   |
+---------------------+     JSON (Axios)      +--------------------+
         │                                                     
         │ (Docker)                                            
         ▼                                                     
+---------------------+   reverse proxy + static               
|      Nginx          |  ─────────────────────────────────────▶ Serves SPA and proxies /api → backend
+---------------------+
```

Request flow (upload):
1) User logs in → receives JWT
2) User selects file + enters password → POST /files/upload (multipart)
3) Backend derives key (PBKDF2), encrypts with AES‑CBC (per‑file salt + IV), stores encrypted bytes
4) User can list files under their account


## 🖼️ Demo & Screens

- Dashboard and upload flow
- Auth screens (Login / Register)

Tip: Add your screenshots or a short GIF under `docs/` and link them here:

```
/docs/demo.gif
/docs/screen-dashboard.png
/docs/screen-login.png
```


## 🚀 Quick Start (Docker)

1) Copy and edit environment file:
```
cp backend/.env.example backend/.env
# Edit backend/.env and set a strong SECRET_KEY (e.g. `openssl rand -hex 32`)
```

2) Build and run:
```
docker-compose up --build
```

- Frontend: http://localhost:8080
- Backend (direct): http://localhost:8000 (also proxied from the frontend container under `/api`)

Data persistence: a Docker volume holds `mini_google_drive.db` (SQLite) across restarts.


## 🧪 Local Development (no Docker)

Backend:
```
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
# Edit backend/.env → set SECRET_KEY
uvicorn backend.app.main:app --reload --port 8000
```

Frontend:
```
cd frontend
npm install
npm run dev   # http://localhost:8080
```
Vite dev server proxies `/api` → `http://127.0.0.1:8000` (see `frontend/vite.config.ts`).


## ⚙️ Configuration (backend/.env)

- DATABASE_URL = `sqlite:///./mini_google_drive.db` (default)
- SECRET_KEY = JWT signing key (required)
- ALGORITHM = `HS256` (default)
- ACCESS_TOKEN_EXPIRE_MINUTES = `30` (default)


## 📚 API Reference (Base: `/api/v1`)

Auth
- Register
```
POST /register
Content-Type: application/json
{
  "email": "user@example.com",
  "password": "strong_pw"
}
```
- Login
```
POST /login
Content-Type: application/x-www-form-urlencoded
username=user@example.com&password=strong_pw
```
Response:
```
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Files (requires `Authorization: Bearer <jwt>`)
- List files
```
GET /files
```
- Upload file (server‑side encryption using user‑provided password)
```
POST /files/upload
Content-Type: multipart/form-data
- file: <binary>
- password: <your login password>
```


## 🔐 Security & Privacy

- Password hashing: Argon2 (resistant to GPU cracking)
- Auth: OAuth2 password flow with JWT bearer tokens
- File encryption: AES‑CBC with per‑file IV and salt; keys derived via PBKDF2‑HMAC‑SHA256
- Secrets: loaded from `backend/.env` (do not commit your real secrets)
- Note: Download/decryption endpoints are intentionally not included yet to keep scope focused. See Roadmap.


## ⚡ Performance & DX

- FastAPI + Uvicorn for high throughput
- Minimal I/O on upload path; encryption done in‑memory
- Vite dev server for instant HMR, Axios interceptors for token attachment
- Nginx serves static SPA and proxies API in production containers


## 🗂️ Project Structure

```
backend/
  app/
    api/v1/        # REST endpoints (auth, files)
    core/          # security & settings
    db/            # SQLAlchemy engine & models
    schemas/       # Pydantic request/response models
    services/      # business logic (auth, file)
frontend/
  src/
    pages/         # Login, Register, Dashboard
    components/    # Navbar, shared UI
    services/      # Axios instance & helpers
```


## 🧠 Design Decisions

- Server‑side encryption ensures sensitive content never hits disk unencrypted
- Per‑file salt + IV prevents key/IV reuse and supports strong cryptographic hygiene
- JWT over cookies keeps the SPA stateless and simplifies deployment via Nginx
- SQLite by default for simplicity; easily swap to Postgres via `DATABASE_URL`


## 🧭 Roadmap

- File download + decryption flow (with secure password handling)
- File metadata (size, MIME), preview support, folders/tags
- Pagination and search on the files list
- Postgres support and migrations
- Automated tests (pytest) for auth and file flows
- CI pipeline and container vulnerability scanning


## 🧪 Testing

Scaffold exists under `backend/tests/`. To start adding tests:
```
pip install pytest
pytest backend/tests -q
```


## 🧩 Troubleshooting

- 401 errors on files endpoints → Ensure token is stored in `localStorage` and attached as `Authorization: Bearer <token>`
- Login failing → Must send `username` and `password` as `application/x-www-form-urlencoded`
- Dev CORS issues → Use `npm run dev` (Vite proxy handles `/api`)
- Rebuild containers after dependency changes → `docker-compose build --no-cache && docker-compose up`


## 🙌 Contributing

Issues and PRs are welcome. Ideas from the Roadmap section are great places to start.


## 📄 License

This project is provided as‑is for educational purposes. Add your preferred license (e.g., MIT) to the repository root.
