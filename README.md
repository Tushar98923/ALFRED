<div align="center">

# 🦇 A.L.F.R.E.D.

### **Autonomous Language Framework for Retrieval-Enhanced Dialogue**

A conversational AI assistant with a RAG pipeline, multi-LLM support, auto intent detection, and safe system command execution — all from one minimalist interface.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=061a23)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-FF6F00?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Gemini-API-4285F4?style=for-the-badge&logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

<br/>

*RAG pipelines · vector search · multi-LLM routing · auto intent detection · minimalist 2D geometric UI*

---

</div>

## 🧠 What is ALFRED?

**ALFRED** is a personal AI command center that combines:

1. **RAG-powered Q&A** — Upload documents (.txt, .md, .pdf, .docx, .csv) and ask questions grounded in your personal knowledge base using semantic vector search.
2. **System automation** — Describe what you want in natural language and ALFRED generates safe, sandboxed PowerShell commands.
3. **Auto intent detection** — No mode switching needed. ALFRED automatically determines if your query is a knowledge question or a system command.
4. **Multi-LLM support** — Add API keys for Gemini, OpenAI, Anthropic, LM Studio, or OpenRouter directly from the UI.

> **Think of it as Jarvis for your desktop** — voice-in, knowledge-grounded answers out, one-click command execution, and full conversation history built in.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **📚 RAG Pipeline** | Ingests documents → chunks text → embeds with Google `text-embedding-004` → stores in ChromaDB → retrieves relevant context → generates grounded answers with source citations |
| **🔀 Auto Intent Detection** | Two-stage classifier (regex heuristics + LLM fallback) auto-routes queries between knowledge Q&A and command generation |
| **🔑 Multi-LLM API Keys** | Add/manage API keys for Gemini, OpenAI, Anthropic, LM Studio, and OpenRouter from the Settings tab — no .env editing needed |
| **🖥️ Safe Command Execution** | Translates natural language to PowerShell commands with whitelist + timeout safety model |
| **💬 Persistent Conversations** | Full chat history stored in SQLite. Browse, resume, or delete past conversations |
| **📄 Document Management** | Upload, index, and delete documents from the Knowledge tab. Supports `.txt`, `.md`, `.pdf`, `.docx`, `.csv` |
| **🎤 Voice Input** | Speak naturally using Web Speech API |
| **🎨 Minimalist Geometric UI** | Clean 2D design with Inter + JetBrains Mono fonts, near-white palette, geometric motifs |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          ALFRED System                                │
│                                                                       │
│  ┌──────────────┐    ┌──────────────────┐    ┌────────────────────┐  │
│  │   React +    │───▶│  Django REST API  │───▶│   Intent Router    │  │
│  │  TypeScript  │    │   (DRF Views)    │    │                    │  │
│  │   Frontend   │◀───│                  │◀───│  ┌──────────────┐  │  │
│  │   (Vite)     │    │  Conversations   │    │  │ Knowledge    │  │  │
│  └──────┬───────┘    │  Messages DB     │    │  │ Mode (RAG)   │  │  │
│         │            │  LLM Providers   │    │  └──────────────┘  │  │
│         │            └────────┬─────────┘    │  ┌──────────────┐  │  │
│  ┌──────▼───────┐    ┌───────▼──────────┐    │  │ Command      │  │  │
│  │  Voice Input  │    │  RAG Engine      │    │  │ Mode (PS)    │  │  │
│  │  Web Speech   │    │  ChromaDB        │    │  └──────────────┘  │  │
│  └──────────────┘    │  Gemini Embed    │    └────────────────────┘  │
│                      │  Text Chunker    │                             │
│                      └──────────────────┘                             │
└──────────────────────────────────────────────────────────────────────┘
```

### RAG Pipeline Flow

```
Upload → Load File → Chunk Text → Embed (text-embedding-004) → Store (ChromaDB)
                                                                      │
Query → Embed Query → Search (cosine similarity) → Top-K Chunks ─────┘
                                                        │
                              Augmented Prompt → Gemini 1.5 Flash → Grounded Answer + Sources
```

---

## 📂 Project Structure

```
ALFRED/
├── backend/                        # Django REST API server
│   ├── manage.py
│   ├── config/                     # Django project settings
│   │   ├── settings.py             # Apps, CORS, media, RAG config
│   │   ├── urls.py                 # Root URL routing
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── assistant/              # Core assistant app
│   │   │   ├── models.py           # Conversation, Message, LLMProvider
│   │   │   ├── serializers.py      # DRF serializers (write-only API keys)
│   │   │   ├── views.py            # Command gen, execute, intent routing
│   │   │   └── urls.py
│   │   └── knowledge/              # Knowledge base management app
│   │       ├── models.py           # Document model (upload + status)
│   │       ├── serializers.py      # Document serializers
│   │       ├── views.py            # Upload, query, stats endpoints
│   │       └── urls.py
│   ├── rag/                        # RAG engine modules
│   │   ├── loaders.py              # File loaders (.txt .md .pdf .docx .csv)
│   │   ├── chunker.py              # Recursive text splitter
│   │   ├── embeddings.py           # Google text-embedding-004 wrapper
│   │   ├── vector_store.py         # ChromaDB persistent vector store
│   │   ├── intent.py               # Auto intent classifier
│   │   └── pipeline.py             # Ingest + query orchestrator
│   ├── chroma_data/                # ChromaDB persistent storage (gitignored)
│   └── media/                      # Uploaded documents (gitignored)
│
├── frontend/                       # React + TypeScript client
│   ├── index.html                  # SPA entry (Inter + JetBrains Mono fonts)
│   ├── vite.config.ts              # Vite dev server + API proxy
│   ├── package.json
│   └── src/
│       ├── main.tsx                # React bootstrap + CSS import
│       ├── index.css               # Minimalist geometric design system
│       ├── ui/
│       │   ├── App.tsx             # Main app (3-tab sidebar, chat, settings)
│       │   └── voice.ts            # Web Speech API
│       └── api/
│           └── client.ts           # Typed API client (all endpoints)
│
├── services/                       # Standalone service modules
│   └── voice_to_text/              # Python speech-to-text
│
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (not committed)
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.10+ | Backend runtime |
| **Node.js** | 18+ | Frontend build tooling |
| **npm** | 9+ | Package management |
| **PowerShell** | 5.1+ | Command execution (Windows) |

### 1. Clone the Repository

```bash
git clone https://github.com/Tushar98923/ALFRED.git
cd ALFRED
```

### 2. Backend Setup

```powershell
# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python backend/manage.py migrate

# Start the backend server
python backend/manage.py runserver
```

> 🟢 Backend runs on **http://127.0.0.1:8000**

### 3. Frontend Setup

Open a **second terminal**:

```powershell
# Navigate to frontend
cd frontend

# Install Node dependencies
npm install

# Start the dev server
npm run dev
```

> 🟢 Frontend runs on **http://localhost:5173** — API calls are auto-proxied to the backend.

### 4. Open in Browser

Navigate to **http://localhost:5173** and you're ready to go.

### 5. Add an LLM API Key

You have **two options**:

**Option A — From the UI (recommended):**
1. Click the **SETTINGS** tab in the sidebar
2. Click **+ Add Provider**
3. Select your provider (Gemini, OpenAI, etc.)
4. Paste your API key
5. Click **Save**, then **Activate**

**Option B — Via `.env` file:**

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
ALLOWED_ORIGINS=http://localhost:5173
```

### 6. Upload Documents (Optional)

To enable RAG-powered answers:

1. Click the **KNOWLEDGE** tab in the sidebar
2. Click **+ Upload**
3. Select a `.txt`, `.md`, `.pdf`, `.docx`, or `.csv` file
4. The document is automatically chunked, embedded, and indexed
5. Ask questions — ALFRED will ground its answers in your documents

---

## 📋 Quick Reference — Run Commands

```powershell
# Terminal 1 — Backend
pip install -r requirements.txt        # First time only
python backend/manage.py migrate       # First time only
python backend/manage.py runserver     # Start backend

# Terminal 2 — Frontend
cd frontend
npm install                            # First time only
npm run dev                            # Start frontend
```

Then open **http://localhost:5173** in your browser.

---

## 🔌 API Reference

### Assistant

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/command/` | Send a query (auto-routed to command or knowledge) |
| `POST` | `/api/execute/` | Execute a whitelisted PowerShell command |

### Conversations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/conversations/` | List all conversations |
| `GET` | `/api/conversations/:id/` | Get conversation with messages |
| `POST` | `/api/conversations/` | Create a new conversation |
| `DELETE` | `/api/conversations/:id/` | Delete a conversation |

### Knowledge Base

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/knowledge/upload/` | Upload a document (multipart) |
| `GET` | `/api/knowledge/documents/` | List all documents |
| `DELETE` | `/api/knowledge/documents/:id/` | Delete a document + its vectors |
| `POST` | `/api/knowledge/query/` | Direct RAG query |
| `GET` | `/api/knowledge/stats/` | Knowledge base stats |

### LLM Providers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/providers/` | List configured providers |
| `POST` | `/api/providers/` | Add a new provider |
| `PATCH` | `/api/providers/:id/` | Update a provider |
| `DELETE` | `/api/providers/:id/` | Delete a provider |
| `POST` | `/api/providers/:id/activate/` | Set as the active provider |
| `GET` | `/api/providers/available/` | List supported provider types |

### Response Examples

**`POST /api/command/` → Knowledge mode:**
```json
{
  "mode": "knowledge",
  "answer": "Based on your documents, the key findings are...",
  "sources": [
    { "name": "research_paper.pdf", "score": 0.92 },
    { "name": "notes.md", "score": 0.78 }
  ],
  "chunks_retrieved": 3,
  "conversation_id": 42
}
```

**`POST /api/command/` → Command mode:**
```json
{
  "mode": "command",
  "command": "mkdir C:\\Users\\you\\Desktop\\Reports",
  "conversation_id": 42
}
```

---

## 🛡️ Safety Model

- ✅ **Whitelist-only execution** — only pre-approved commands: `echo`, `mkdir`, `ls`, `dir`, `copy`, `move`, `type`, `del`, `rmdir`, etc.
- ✅ **Non-interactive mode** — `-NoProfile -NonInteractive -ExecutionPolicy Bypass`
- ✅ **15-second timeout** — commands that hang are killed automatically
- ✅ **Review-before-execute** — generated commands are shown for approval before running
- ✅ **API key security** — keys are write-only (never returned in API responses, only masked)

---

## 🧩 Tech Stack

<div align="center">

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 · TypeScript 5 · Vite 5 |
| **Design** | Minimalist 2D Geometric · Inter · JetBrains Mono |
| **Backend** | Django 5.1 · Django REST Framework · SQLite |
| **RAG** | ChromaDB · Google text-embedding-004 · Recursive Chunker |
| **LLM APIs** | Google Gemini · OpenAI · Anthropic · LM Studio · OpenRouter |
| **Intent** | Regex Heuristics + LLM Classifier |
| **Voice** | Web Speech API |
| **Execution** | PowerShell (sandboxed, whitelisted) |
| **Platform** | Windows 10/11 |

</div>

---

## 🗺️ Roadmap

- [x] **RAG pipeline** — document ingestion, chunking, embedding, vector search, grounded generation
- [x] **Auto intent detection** — automatic routing between command and knowledge modes
- [x] **Multi-LLM API key management** — add/switch providers from the UI
- [x] **Persistent conversations** — full chat history with browse and delete
- [x] **Document management UI** — upload, index, and manage knowledge base files
- [x] **Minimalist geometric redesign** — clean 2D aesthetic with geometric motifs
- [ ] **TTS voice replies** — speak responses back to the user
- [ ] **Conversation search** — full-text search across all past conversations
- [ ] **Expanded command catalog** — more whitelisted commands with confirmation dialogs
- [ ] **Multi-user support** — authentication and per-user knowledge bases
- [ ] **Plugin system** — third-party extensions for new knowledge sources

---

## 🤝 Contributing

Contributions are welcome! Whether it's bug fixes, new features, or documentation improvements:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feat/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feat/amazing-feature`)
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ☕ and curiosity.**

*Python · Django · React · RAG · ChromaDB · Gemini · Vector Search*

</div>
