# Agent Transcripts

This folder contains logs from the AI-assisted development session used to build the Lenny Growth Assistant.

---

## Session 1 — Architecture Planning

**Prompt**: Design a FastAPI + PostgreSQL + FAISS + React architecture for a RAG-based podcast assistant with Ollama and Anthropic support.

**Output**: Defined the component boundaries:
- `retrieval.py` owns all FAISS logic (chunking, embedding, indexing, search)
- `llm.py` owns provider abstraction (Ollama/Anthropic behind one interface)
- `agent.py` owns intent routing and prompt assembly
- `chat.py` owns HTTP layer and DB persistence

**Decision**: Keep agent routing simple (keyword-based intent detection) rather than using a full tool-calling framework. Rationale: the three skills (QA, Ship30, artifact) have clear, non-overlapping triggers. A classifier adds latency and complexity without meaningful benefit at this scope.

---

## Session 2 — Retrieval Service

**Prompt**: Implement FAISS-based retrieval with sentence-transformers, chunking with overlap, and persistent index caching.

**First attempt**: Used `IndexFlatL2` with raw embeddings.

**Problem**: L2 distance on non-normalized vectors gave inconsistent ranking when chunk lengths varied significantly.

**Fix**: Switched to `IndexFlatIP` (inner product) with L2-normalized embeddings, which is equivalent to cosine similarity. Added `faiss.normalize_L2()` on both index embeddings and query embeddings.

**Result**: Retrieval quality improved noticeably on short queries like "PMF" vs longer queries.

---

## Session 3 — LLM Service

**Prompt**: Build a unified LLM interface supporting Ollama and Anthropic with graceful error handling.

**Issue**: Ollama's `/api/chat` endpoint returns different error shapes depending on whether the model is missing vs the server is down.

**Fix**: Catch `httpx.ConnectError` separately from `httpx.HTTPStatusError`. Return user-friendly messages for each case. Added 120s timeout (Ollama on CPU can be slow for long outputs).

**Anthropic note**: Used `AsyncAnthropic` client to keep the entire request path async. Avoided the sync client which would block the event loop.

---

## Session 4 — Ship 30 Skill

**Prompt**: Encode Ship 30 for 30 writing principles into a system prompt rather than relying on a one-off instruction.

**Research**: Read the Ship 30 for 30 guide. Key principles:
- Hook in first 1-2 sentences (curiosity gap or bold claim)
- Short paragraphs (1-3 sentences)
- Bold the single most important sentence per section
- Numbered insights (not generic advice)
- Specific, actionable takeaway
- ~1,250 words

**Decision**: Encode these as explicit rules in `SHIP30_SYSTEM` prompt rather than injecting them into the user message. This keeps the user message clean and ensures the rules apply consistently regardless of how the user phrases the request.

---

## Session 5 — Artifact Security

**Prompt**: Implement secure HTML artifact rendering.

**First attempt**: Rendered HTML directly in a `<div>` using `dangerouslySetInnerHTML`.

**Problem**: This allows arbitrary script execution and CSS injection.

**Fix**: Two-layer approach:
1. DOMPurify strips dangerous tags and attributes before the HTML is written
2. Sandboxed iframe (`sandbox="allow-same-origin"`) prevents script execution even if DOMPurify misses something

**Trade-off**: `allow-same-origin` is needed for CSS to render correctly. Without it, stylesheets don't apply. The risk is that same-origin scripts could access parent window — mitigated by DOMPurify removing all `<script>` tags first.

---

## Session 6 — Frontend State Management

**Prompt**: Build React state management for sessions, messages, and optimistic updates.

**Decision**: Used a single `useChat` hook rather than a state management library (Redux, Zustand). Rationale: the state is simple (sessions list, active session, messages array, loading flag). A hook is sufficient and avoids a dependency.

**Optimistic updates**: User messages are added to the UI immediately before the API call completes. If the call fails, the optimistic message is removed and an error is shown. This makes the UI feel responsive even on slow Ollama responses.

---

## Failed Attempts

### Attempt: Streaming responses
Tried implementing SSE streaming from FastAPI to React. Abandoned because:
- Ollama's streaming format differs from Anthropic's
- Adds significant complexity to both backend and frontend
- Loading indicator (bouncing dots) provides sufficient UX feedback for demo purposes
- Can be added as a future enhancement

### Attempt: LangChain for RAG
Initially considered LangChain for the retrieval pipeline. Abandoned because:
- Adds ~15 transitive dependencies
- The retrieval logic is simple enough to implement directly (FAISS + sentence-transformers)
- Direct implementation is easier to debug and explain to a client engineer
- Avoids LangChain's frequent breaking changes

### Attempt: Alembic migrations
Set up Alembic for schema migrations. Removed for demo simplicity — `Base.metadata.create_all()` on startup is sufficient for a fresh deployment. Noted in README as a production enhancement.
