# Mini Google Drive 🚀

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-05998B?logo=fastapi&logoColor=white)](#)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)](#)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6?logo=typescript&logoColor=white)](#)
[![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker&logoColor=white)](#)
[![JWT](https://img.shields.io/badge/Auth-JWT-000000?logo=jsonwebtokens&logoColor=white)](#)
[![Security](https://img.shields.io/badge/Security-Argon2%20%7C%20AES--CBC-8A2BE2)](#)

A production‑minded, secure file storage app — a "mini Google Drive" — built with a modern stack:

- FastAPI + SQLAlchemy (Python) for a typed, high‑performance API
- React + Vite (TypeScript) for a crisp UX
- JWT auth, Argon2 password hashing, and server‑side file encryption (AES‑CBC via PBKDF2‑derived keys)
- Dockerized with Nginx reverse proxy for one‑command spin‑up

## ✨ Highlights

- Clean, layered architecture (API → Services → DB → Schemas)
- End‑to‑end JWT auth using OAuth2 password flow
- Server‑side file encryption with per‑file salt and IV
- New: Download, Delete, and Preview (image/pdf) with ownership checks
- Dev experience: hot reloads, Vite proxy for zero‑CORS friction

## 🧩 Architecture Overview

The application follows a simple and practical client–server architecture.

- **Frontend (React + Vite)**  
  Handles authentication flows (login/register) and the user dashboard.  
  Communicates with the backend using JSON over REST APIs.

- **Backend (FastAPI)**  
  Exposes versioned REST endpoints under `/api/v1`.  
  Responsible for authentication, file operations, encryption/decryption, and access control using JWT.

- **Database (SQLite via SQLAlchemy)**  
  Stores user data and file metadata.  
  Designed so it can be easily swapped with PostgreSQL by changing the database URL.

- **Reverse Proxy (Nginx, Dockerized)**  
  Serves the frontend build as static files and proxies `/api` requests to the FastAPI backend.

This separation keeps the system modular, easy to test, and production-ready.

### Request Flow (Upload / Download)

1. User logs in and receives a JWT access token.
2. Frontend sends API requests with the token in the Authorization header.
3. Backend validates ownership and permissions.
4. Files are encrypted/decrypted on demand before storage or download.


## 🖼️ Demo & Screens

Add screenshots or a short GIF under `docs/` and link them here:

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
- Backend (direct): http://localhost:8000

Data persistence: a Docker volume holds `mini_google_drive.db` (SQLite) across restarts.

## 🧪 Local Development (no Docker)

Backend:
```
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
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

## ✅ Features

- Register and login with JWT bearer tokens
- Secure upload with server‑side AES‑CBC encryption (key via PBKDF2)
- Per‑user file listing
- Download decrypted file on demand (password required)
- Delete file (DB record + encrypted content)
- Preview inline for safe types: PNG, JPG/JPEG, PDF (password required)

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

Files (Authorization: `Bearer <jwt>`)
- List files
```
GET /files
```

- Upload (encrypts with AES‑CBC; per‑file salt + IV)
```
POST /files/upload
Content-Type: multipart/form-data
- file: <binary>
- password: <your login password>
```

- Download (decrypts on demand; sends as attachment)
```
GET /files/{file_id}/download?password=<your login password>
```

- Preview (decrypts on demand; inline response)
```
GET /files/{file_id}/preview?password=<your login password>
# Only for: image/png, image/jpeg, application/pdf (.png/.jpg/.jpeg/.pdf)
```

- Delete (removes DB record and encrypted content)
```
DELETE /files/{file_id}
```

### Curl examples

Assuming `TOKEN` contains the JWT access token.

List
```
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/files
```

Download
```
curl -L -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/files/123/download?password=your_password" \
  -o downloaded.bin
```

Preview (opens if you paste into browser); with curl, you’ll just receive the bytes
```
curl -L -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/files/123/preview?password=your_password" \
  -o preview.bin
```

Delete
```
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/files/123
```

## 🔐 Security Notes

- Password hashing: Argon2
- Auth: JWT bearer tokens signed with `SECRET_KEY`
- File encryption: AES‑CBC with per‑file IV and salt; keys derived via PBKDF2‑HMAC‑SHA256
- Decryption is on demand in memory and streamed as needed
- Preview is restricted to safe types (png, jpg/jpeg, pdf)

Note: For simplicity and minimal changes, the download/preview password is passed via query string. In production, consider POSTing a short‑lived decryption token or using a form body to avoid logging sensitive data in URLs.

## 🧠 Design Decisions

- Additive changes only: upload and auth logic untouched; DB schema unchanged
- Ownership is enforced on every file operation; non‑owners receive 403
- SQLite by default; can be swapped with Postgres by changing `DATABASE_URL`
- Nginx serves SPA and proxies API in containerized deployment

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

## 🧪 Manual Testing Guide

1) Upload
- Login, go to Dashboard, upload a file; enter your password when prompted for encryption.

2) Download
- In Dashboard, click Download → enter the same password you used for encryption.
- Expected: Browser downloads decrypted file. Wrong password → `400` with clear error.

3) Preview
- Supported: .png, .jpg/.jpeg, .pdf
- Click Preview → enter password.
- Expected: Opens a new tab displaying the file inline. Unsupported type → `415` error.

4) Delete
- Click Delete → confirm.
- Expected: File disappears from the list; API returns success message.

## ⚡ Troubleshooting

- 401 on any file endpoint → Ensure the Authorization header includes a valid `Bearer` token.
- 400 on download/preview → Wrong password or corrupted file.
- 415 on preview → File type not supported for inline preview.
- CORS/dev proxy → Use `npm run dev`; Vite proxy forwards `/api` to the backend.
- Rebuild containers after dependency changes → `docker-compose build --no-cache && docker-compose up`.

## 🧭 Roadmap

- Optional secure download tokens to avoid password in query
- Client‑side encryption flow
- File metadata (size, type), preview thumbnails
- Pagination and search
- Postgres + Alembic migrations
- Automated test suite (pytest) for auth and file flows

## 🙌 Contributing

Issues and PRs are welcome. Roadmap items are great places to start.

