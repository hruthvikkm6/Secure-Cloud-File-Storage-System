# Secure Cloud File Storage System 🚀

> FastAPI • React • TypeScript • Docker • JWT • AES-256-GCM • Argon2id

A production-grade, security-first cloud file storage platform inspired by Google Drive, built with modern backend architecture, authenticated encryption, secure decryption workflows, and a premium cyber-themed user experience.

---

## ✨ What's New

This release introduces enterprise-grade security enhancements, authenticated encryption, secure decryption tickets, brute-force protection, and a complete Cyber Aegis UI redesign.

### 🔐 Security Upgrades

- Upgraded file encryption from **AES-256-CBC** to **AES-256-GCM**
- Built-in ciphertext authentication and tamper detection
- Legacy AES-CBC file compatibility maintained
- Single-Use Secure Access Tickets (STAT)
- Eliminated password exposure in URL query strings
- Sliding-window brute-force protection
- Thread-safe ticket management
- Automatic ticket expiration and replay prevention

### 🎨 User Experience Upgrades

- Cyber-themed glassmorphism UI
- Drag-and-drop upload interface
- Real-time password strength meter
- Cryptographic telemetry HUD
- Secure inline previews
- Modern animations and micro-interactions
- Responsive dashboard redesign

---

# 🧩 Architecture Overview

The application follows a secure layered architecture.

## Frontend (React + Vite + TypeScript)

Responsible for:

- Authentication flows
- Dashboard experience
- Secure file previews
- Drag-and-drop uploads
- Password strength analysis
- Ticket-based file access

Communicates with the backend through REST APIs.

---

## Backend (FastAPI)

Responsible for:

- JWT authentication
- File encryption/decryption
- Secure ticket issuance
- Access control
- Rate limiting
- Ownership validation
- Metadata management

All APIs are exposed under:

```text
/api/v1
```

---

## Database (SQLite via SQLAlchemy)

Stores:

- User accounts
- File metadata
- Ownership information

Can be easily replaced with PostgreSQL by changing the database URL.

---

## Reverse Proxy (Nginx)

Containerized deployment includes Nginx which:

- Serves React static assets
- Proxies API traffic
- Improves deployment consistency

---

# 🔐 Security Architecture

## Authentication

- JWT Bearer Tokens
- OAuth2 Password Flow
- Argon2 Password Hashing

---

## File Encryption

### Current Encryption Standard

```text
AES-256-GCM
```

Benefits:

- Confidentiality
- Integrity
- Authentication
- Tamper Detection

Each file receives:

- Unique Salt
- Unique Nonce (IV)
- Authentication Tag

Keys are derived using:

```text
PBKDF2-HMAC-SHA256
```

---

## Legacy File Compatibility

Previously uploaded files remain accessible.

The system automatically detects encryption mode:

| IV Length | Encryption Mode |
| ---------- | ---------------- |
| 12 Bytes | AES-256-GCM |
| 16 Bytes | AES-256-CBC (Legacy) |

No migration is required.

---

## Secure Ticket Architecture (STAT)

### Previous Approach

```http
GET /files/{id}/download?password=user_password
```

This exposed passwords through:

- Browser history
- Access logs
- Reverse proxy logs
- Monitoring systems

---

### New Secure Flow

#### Step 1 — Request Ticket

```http
POST /files/{file_id}/ticket
```

Body:

```json
{
  "password": "user_password"
}
```

---

#### Step 2 — Server Validation

Server:

- Verifies password
- Derives encryption key
- Generates secure UUID ticket
- Stores ticket in memory for 60 seconds

---

#### Step 3 — Redeem Ticket

Download:

```http
GET /files/{file_id}/download?ticket_id=<uuid>
```

Preview:

```http
GET /files/{file_id}/preview?ticket_id=<uuid>
```

---

#### Step 4 — Ticket Destruction

The ticket is:

- Single-use
- Immediately deleted
- Protected against replay attacks

---

## Brute Force Protection

The ticket endpoint is protected using a sliding-window rate limiter.

Limit:

```text
10 attempts per minute
```

This significantly reduces password-guessing attacks.

---

# 🚀 Quick Start (Docker)

## Prerequisites

Install:

- Docker
- Docker Compose

---

## Configure Environment

Create environment file:

```bash
cp backend/.env.example backend/.env
```

Edit:

```env
SECRET_KEY=<your-random-secret>
```

Generate a secure key:

```bash
openssl rand -hex 32
```

---

## Build and Run

```bash
docker-compose up --build
```

---

## Access Application

Frontend:

```text
http://localhost:8080
```

Backend:

```text
http://localhost:8000
```

---

# 🧪 Local Development

## Requirements

### Backend

- Python 3.9+

### Frontend

- Node.js 18+

---

# Backend Setup

Navigate to backend:

```bash
cd backend
```

Create virtual environment:

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment file:

### Windows

```powershell
copy .env.example .env
```

### Linux/macOS

```bash
cp .env.example .env
```

Configure:

```env
SECRET_KEY=<your-secret>
```

Start FastAPI:

```bash
uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

---

# Frontend Setup

Open a new terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Run development server:

```bash
npm run dev
```

Frontend:

```text
http://localhost:8080
```

---

## Development Proxy

Vite automatically proxies:

```text
/api
```

to:

```text
http://127.0.0.1:8000
```

No CORS configuration is required during development.

---

# ⚙️ Configuration

Example `.env`

```env
DATABASE_URL=sqlite:///./mini_google_drive.db

SECRET_KEY=your-secret-key

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

# 📚 API Reference

Base URL:

```text
/api/v1
```

---

# Authentication

## Register

```http
POST /register
```

Request:

```json
{
  "email": "user@example.com",
  "password": "strong_password"
}
```

---

## Login

```http
POST /login
```

Content-Type:

```text
application/x-www-form-urlencoded
```

Body:

```text
username=user@example.com
password=strong_password
```

Response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

---

# File Operations

All file endpoints require:

```http
Authorization: Bearer <JWT>
```

---

## List Files

```http
GET /files
```

---

## Upload File

```http
POST /files/upload
```

Form Data:

```text
file=<binary>
password=<encryption_password>
```

Encryption:

```text
AES-256-GCM
```

---

## Request Decryption Ticket

```http
POST /files/{file_id}/ticket
```

Request:

```json
{
  "password": "your_password"
}
```

Response:

```json
{
  "ticket_id": "uuid"
}
```

---

## Download File

```http
GET /files/{file_id}/download?ticket_id=<uuid>
```

Returns decrypted file attachment.

---

## Preview File

```http
GET /files/{file_id}/preview?ticket_id=<uuid>
```

Supported types:

- PNG
- JPG
- JPEG
- PDF

Returns decrypted inline preview.

---

## Delete File

```http
DELETE /files/{file_id}
```

Removes:

- File metadata
- Encrypted storage object

---

# 🔐 Security Features

### Authentication

- JWT Authentication
- Argon2 Password Hashing

### Encryption

- AES-256-GCM
- PBKDF2-HMAC-SHA256
- Per-file Salt
- Per-file Nonce
- Authentication Tags

### Access Protection

- Ownership Enforcement
- Single-Use Decryption Tickets
- Ticket Expiration
- Replay Attack Prevention

### Rate Limiting

```text
10 decryption attempts/minute
```

### Secure Previews

Supported:

- PNG
- JPG
- JPEG
- PDF

---

# 🎨 User Interface Features

## Cyber Aegis Dashboard

Features:

- Glassmorphism design
- Neon cyber styling
- Responsive layout

---

## Drag & Drop Uploads

Supports:

- Dragging files directly onto upload zone
- Visual hover feedback
- Animated upload states

---

## Password Strength Meter

Provides instant feedback:

```text
Weak → Medium → Strong
```

---

## Cryptographic Telemetry HUD

Displays active security mechanisms:

- AES-256-GCM
- Argon2id
- PBKDF2-HMAC
- KDF Iterations
- Single-Use Tickets
- Storage utilization

---

## Secure Inline Preview Modal

Files are:

- Decrypted in memory
- Converted into Blob URLs
- Rendered securely

Supported:

- PDF
- PNG
- JPG
- JPEG

---

# 🗂️ Project Structure

```text
backend/
│
├── app/
│   ├── api/v1/
│   ├── core/
│   ├── db/
│   ├── schemas/
│   └── services/
│
frontend/
│
├── src/
│   ├── pages/
│   ├── components/
│   ├── services/
│   └── assets/
│
docker-compose.yml
```

---

# 🧪 Manual Testing Guide

## Upload

1. Login
2. Open Dashboard
3. Upload file
4. Enter encryption password

Expected:

```text
File uploads successfully.
```

---

## Download

1. Click Download
2. Enter password

Expected:

```text
Ticket issued
File downloaded successfully
```

Wrong password:

```text
400 Bad Request
```

---

## Preview

1. Click Preview
2. Enter password

Expected:

```text
Preview opens successfully
```

Unsupported type:

```text
415 Unsupported Media Type
```

---

## Delete

1. Click Delete
2. Confirm action

Expected:

```text
File removed successfully
```

---

# ⚡ Troubleshooting

### 401 Unauthorized

Verify:

```http
Authorization: Bearer <token>
```

---

### 400 Bad Request

Possible causes:

- Incorrect password
- Expired ticket
- Corrupted file

---

### 429 Too Many Requests

Triggered by:

```text
More than 10 decryption attempts/minute
```

Wait before retrying.

---

### 415 Unsupported Media Type

Preview supports only:

```text
PNG
JPG
JPEG
PDF
```

---

### Docker Rebuild

```bash
docker-compose build --no-cache
docker-compose up
```

---

# 🧭 Roadmap

- Client-side encryption
- PostgreSQL support
- Alembic migrations
- Search and filtering
- File thumbnails
- Pagination
- Shared links
- MFA Authentication
- Audit logging
- Automated test suite

---

# 🙌 Contributing

Issues and Pull Requests are welcome.

Security improvements, bug fixes, and feature enhancements are encouraged.

---

# 👤 Author

**Hruthvik K M**

### LinkedIn

https://www.linkedin.com/in/hruthvikkm/

### GitHub

https://github.com/hruthvikkm6

### Project Repository

https://github.com/hruthvikkm6/Secure-Cloud-File-Storage-System

---

## ⭐ Support

If you found this project useful, consider giving the repository a star.