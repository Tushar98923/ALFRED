ALFRED: Windows Voice Assistant

Badges
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.x-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.x-red)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=061a23)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-API-4285F4?logo=google&logoColor=white)
![PowerShell](https://img.shields.io/badge/PowerShell-7-5391FE?logo=powershell&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)

Overview
- Modern chat-style assistant for Windows that turns natural language into safe PowerShell commands.
- React + TypeScript frontend (Vite), Django REST backend, Gemini for command generation.
- Features: voice input, chat history, safe command execution sandbox, dark/light mode.

Tech stack
- Backend: Django, Django REST Framework, `google-generativeai`, `django-cors-headers`, `python-dotenv`
- Frontend: React 18, TypeScript, Vite (dev proxy to backend)
- Platform: Windows (PowerShell execution with whitelist + timeout)

Architecture
- `backend/`
  - `config/`: Django settings, urls, wsgi
  - `apps/assistant/`: models, serializers, views, urls
- `frontend/`
  - `src/ui`: app components (chat, history, voice)
  - `src/api`: simple fetch client

API
- `POST /api/command/` → { command, conversation_id }
- `POST /api/execute/` → { returncode, stdout, stderr }
- `GET /api/conversations/` → list of conversations with messages

Environment
- Create an `.env` at repo root (or export env vars) with:
  - `GOOGLE_API_KEY=your_key_here` (preferred by SDK) or `GEMINI_API_KEY=your_key_here`
  - `ALLOWED_ORIGINS=http://localhost:5173`
  - Optional: `DJANGO_SECRET_KEY`, `DEBUG=1`, `ALLOWED_HOSTS=localhost,127.0.0.1`

Getting started
1) Backend
   - Create/activate venv
   - `pip install -r ALFRED/requirements.txt`
   - `python backend/manage.py migrate`
   - `python backend/manage.py runserver`
2) Frontend
   - `cd frontend && npm install && npm run dev`
   - Visit the Vite URL (usually http://localhost:5173)

Run it yourself (fresh clone)
1) Clone
   - `git clone <this-repo-url> && cd <repo-folder>`
2) Python env (Windows PowerShell)
   - `python -m venv .venv`
   - `.\.venv\Scripts\Activate.ps1`
   - `pip install -r ALFRED/requirements.txt`
3) Environment
   - Create `.env` in the repo root with:
     - `GOOGLE_API_KEY=your_api_key` (or `GEMINI_API_KEY=...`)
     - `ALLOWED_ORIGINS=http://localhost:5173`
     - Optional: `DJANGO_SECRET_KEY=change-me`, `DEBUG=1`, `ALLOWED_HOSTS=localhost,127.0.0.1`
4) Database and backend
   - `python backend/manage.py migrate`
   - `python backend/manage.py runserver`
   - Backend runs on `http://127.0.0.1:8000`
5) Frontend
   - Open a new terminal
   - `cd frontend`
   - `npm install`
   - `npm run dev`
   - Open the printed local URL (usually `http://localhost:5173`)

Notes
- The frontend proxies `/api/*` to the Django server (see `frontend/vite.config.ts`).
- PowerShell commands are executed via a whitelist for safety.
- To change ports or origins, update `.env` and `vite.config.ts`.

Safety model
- Only a small whitelist of PowerShell commands is executable (`echo`, `mkdir`, `ls`, etc.).
- All executions are non-interactive with a short timeout.

Roadmap
- Conversation rename/delete, search
- TTS voice reply
- Expanded safe command catalog and confirmations

