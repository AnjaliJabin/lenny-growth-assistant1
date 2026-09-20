# Lenny Growth Assistant

An AI-powered conversational assistant grounded in Lenny's Podcast transcripts. Ask product and growth questions, generate Ship 30 for 30 essays, and create rendered Markdown/HTML artifacts — all backed by a local or cloud LLM.

---

## Architecture Overview

```
┌─────────────┐     HTTP      ┌──────────────────────────────────────┐
│  React/Vite │ ◄──────────► │  FastAPI Backend                     │
│  Frontend   │              │  ├── /api/sessions  (CRUD)            │
│  Port 5173  │              │  ├── /api/chat      (agent entry)     │
└─────────────┘              │  └── /health                         │
                             └──────────┬───────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
             PostgreSQL          FAISS Index          LLM Provider
             (sessions +         (transcript          Ollama (local)
              messages)           embeddings)         or Anthropic
```

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | Backend |
| Node.js | 18+ | Frontend |
| PostgreSQL | 14+ | Or use Docker |
| Ollama | latest | For local LLM demo |
| Docker + Compose | optional | One-command startup |

---

## Quick Start (Docker)

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd lenny-growth-assistant

# 2. Copy and configure environment
cp backend/.env.example backend/.env
# Edit backend/.env — set LLM_PROVIDER=ollama (default)

# 3. Start Ollama separately (must run on host)
ollama pull llama3.2
ollama serve

# 4. Launch everything
docker compose up --build

# App: http://localhost:3000
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

---

## Manual Setup (No Docker)

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DATABASE_URL and LLM settings

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### Database

```bash
# Option A: Local PostgreSQL
createdb lenny_assistant

# Option B: Docker only the DB
docker run -d -p 5432:5432 \
  -e POSTGRES_DB=lenny_assistant \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  postgres:16-alpine
```

Tables are created automatically on first startup via SQLAlchemy.

---

## Environment Variables

See `backend/.env.example` for all variables. Key ones:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | No | `ollama` | `ollama` or `anthropic` |
| `ANTHROPIC_API_KEY` | If cloud | — | Your Anthropic key |
| `ANTHROPIC_MODEL` | No | `claude-3-5-haiku-20241022` | Claude model |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | No | `llama3.2` | Model pulled in Ollama |
| `DATABASE_URL` | Yes | — | PostgreSQL async URL |
| `CORS_ORIGINS` | No | `http://localhost:3000,...` | Allowed origins |

---

## Switching LLM Provider

Edit `backend/.env`:

```bash
# Use local Ollama
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2

# Use Anthropic Claude
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-haiku-20241022
```

No code changes needed. The active provider is shown in the sidebar badge.

---

## Transcript Ingestion

Place `.txt` transcript files in `data/transcripts/`. Five sample episodes are included.

To rebuild the vector index:

```bash
cd backend
python -c "from app.services.retrieval import retrieval_service; retrieval_service.build_index()"
```

The index is cached in `data/vector_index/` and loaded automatically on startup.

---

## Running Tests

```bash
cd backend
pip install aiosqlite pytest-asyncio
pytest -v
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (DB, LLM, retrieval) |
| POST | `/api/sessions` | Create session |
| GET | `/api/sessions` | List sessions |
| GET | `/api/sessions/{id}/messages` | Get messages |
| DELETE | `/api/sessions/{id}` | Delete session |
| POST | `/api/chat` | Send message, get AI reply |

Interactive docs: `http://localhost:8000/docs`

---

## Troubleshooting

**Ollama not reachable**
```bash
ollama serve          # start the daemon
ollama pull llama3.2  # pull the model
curl http://localhost:11434/api/tags  # verify
```

**Database connection error**
- Check `DATABASE_URL` in `.env`
- Ensure PostgreSQL is running: `pg_isready -h localhost`

**Empty retrieval results**
- Confirm `.txt` files exist in `data/transcripts/`
- Delete `data/vector_index/` and restart to rebuild

**Frontend can't reach backend**
- Vite proxies `/api` and `/health` to `localhost:8000`
- Ensure backend is running on port 8000

---

## Extending the System

- **Add transcripts**: Drop `.txt` files in `data/transcripts/`, delete the index, restart
- **Add a new skill**: Add intent detection in `agent.py` `_detect_intent()`, add a handler function
- **Change embedding model**: Update `EMBEDDING_MODEL` in `.env`, rebuild index
- **Add streaming**: Replace `llm_service.complete()` with a streaming variant and use FastAPI `StreamingResponse`
