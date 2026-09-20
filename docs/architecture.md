# Architecture — Lenny Growth Assistant

## Database Schema

```sql
-- sessions
CREATE TABLE sessions (
    id          VARCHAR(36) PRIMARY KEY,
    title       VARCHAR(255) DEFAULT 'New Chat',
    user_metadata JSON DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- messages
CREATE TABLE messages (
    id          VARCHAR(36) PRIMARY KEY,
    session_id  VARCHAR(36) REFERENCES sessions(id) ON DELETE CASCADE,
    role        VARCHAR(20),          -- 'user' | 'assistant'
    content     TEXT,
    sources     JSON DEFAULT '[]',    -- [{episode, file, score}]
    artifact    JSON,                 -- {type, content} | null
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

---

## API Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/health` | — | `{status, provider, db, retrieval}` |
| POST | `/api/sessions` | `{title?, user_metadata?}` | Session |
| GET | `/api/sessions` | — | Session[] |
| GET | `/api/sessions/{id}/messages` | — | Message[] |
| DELETE | `/api/sessions/{id}` | — | 204 |
| POST | `/api/chat` | `{message, session_id?}` | `{session_id, message, provider}` |

### Error Format
```json
{"detail": "Human-readable error message"}
```

---

## Component Boundaries

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py       # Pydantic settings, env vars
│   │   ├── database.py     # SQLAlchemy async engine, session factory
│   │   └── logging.py      # Structured JSON logger
│   ├── models/
│   │   ├── db.py           # SQLAlchemy ORM models
│   │   └── schemas.py      # Pydantic request/response models
│   ├── services/
│   │   ├── retrieval.py    # FAISS index, chunking, embedding, search
│   │   ├── llm.py          # Anthropic + Ollama unified interface
│   │   └── agent.py        # Intent routing, prompt assembly, skill dispatch
│   ├── api/
│   │   ├── chat.py         # /api/sessions, /api/chat routes
│   │   └── health.py       # /health route
│   └── main.py             # FastAPI app, CORS, lifespan
```

---

## Ingestion / Retrieval Flow

```
data/transcripts/*.txt
        │
        ▼
RetrievalService.build_index()
  1. Read each .txt file
  2. Split into 600-word chunks (80-word overlap)
  3. Embed with sentence-transformers (all-MiniLM-L6-v2)
  4. Normalize L2, add to FAISS IndexFlatIP
  5. Persist index.faiss + chunks.pkl to data/vector_index/
        │
        ▼ (on startup)
RetrievalService.load_index()
  - Loads cached index if present, else builds
        │
        ▼ (on each chat request)
RetrievalService.retrieve(query, top_k=5)
  1. Embed query
  2. Cosine similarity search (inner product on normalized vectors)
  3. Return top-5 chunks with source metadata
```

---

## Agent Routing

```
POST /api/chat
  │
  ├── load session history (last 20 messages)
  ├── save user message
  │
  ▼
agent.run_chat(message, history)
  │
  ├── _detect_intent(message)
  │     ├── "ship30"       → keywords: ship 30, atomic essay, essay about
  │     ├── "artifact_html"→ keywords: html artifact, generate html
  │     ├── "artifact_md"  → keywords: markdown doc, generate markdown, artifact
  │     └── "qa"           → default
  │
  ├── retrieval_service.retrieve(message)  ← always runs
  │
  ├── intent == "ship30"      → _run_ship30()   → artifact={type:markdown}
  ├── intent == "artifact_*"  → _run_artifact() → artifact={type:html|markdown}
  └── intent == "qa"          → _run_qa()       → artifact=None
  │
  ▼
llm_service.complete(messages, system)
  ├── provider == "anthropic" → Anthropic SDK
  └── provider == "ollama"    → httpx POST /api/chat
```

---

## Model Toggle

`LLM_PROVIDER` env var controls routing in `llm_service.complete()`:
- `ollama`: POST to `OLLAMA_BASE_URL/api/chat` with `OLLAMA_MODEL`
- `anthropic`: Anthropic SDK with `ANTHROPIC_MODEL`

No application code changes required. Provider shown in UI sidebar badge.

**Fallback behavior**:
- Ollama unreachable → `RuntimeError` → HTTP 503 with message
- Missing Anthropic key → `ValueError` → HTTP 503
- Model timeout → `RuntimeError` → HTTP 503

---

## Security

### HTML Artifact Rendering
Generated HTML is treated as untrusted. Two-layer defense:

1. **DOMPurify** (client-side): Strips `<script>`, `<object>`, `<embed>`, `<form>`, `<input>` tags and event handler attributes (`onerror`, `onclick`, etc.) before writing to iframe
2. **Sandboxed iframe**: `sandbox="allow-same-origin"` — permits CSS/layout rendering but blocks JavaScript execution, form submission, navigation, and popups

What the viewer **permits**: HTML structure, inline CSS, text, images (data URIs)
What the viewer **blocks**: Script execution, external resource loading, form submission, navigation

### Other Security Considerations
- No secrets in source code; `.env` in `.gitignore`
- CORS restricted to configured origins
- Pydantic validation on all inputs (max lengths, pattern matching)
- SQL injection prevented by SQLAlchemy ORM (parameterized queries)

---

## Deployment Topology

```
┌─────────────────────────────────────────────┐
│  Docker Compose (local)                     │
│                                             │
│  ┌──────────┐   ┌──────────┐   ┌────────┐  │
│  │ frontend │   │ backend  │   │   db   │  │
│  │ nginx:80 │──►│ uvicorn  │──►│postgres│  │
│  │ port 3000│   │ port 8000│   │port5432│  │
│  └──────────┘   └──────────┘   └────────┘  │
│                      │                      │
└──────────────────────┼──────────────────────┘
                       │ host.docker.internal
                       ▼
              ┌─────────────────┐
              │  Ollama (host)  │
              │  port 11434     │
              └─────────────────┘
```

For cloud deployment: replace Ollama with Anthropic API, use Supabase/Railway for PostgreSQL, deploy backend to Railway/Render, frontend to Vercel/Netlify.
