# Product Requirements Document — Lenny Growth Assistant

## Forward Deployment Brief

### User and Problem

**Primary user**: Product managers, growth leads, and founders at early-to-mid-stage B2B SaaS companies who regularly consume Lenny's Podcast for strategic guidance.

**Job to be done**: Get fast, grounded answers to product and growth questions without scrubbing through hours of podcast audio or searching transcripts manually. Produce polished written content (essays, docs) that can be shared with teams immediately.

**Pain removed**:
- Hours spent re-listening to episodes to find a specific framework
- Generic AI answers not grounded in trusted sources
- Context-switching between research and writing tools

### Success Metrics

1. **Primary**: Answer grounding rate — ≥90% of assistant responses cite at least one transcript source (measurable via `sources` field in DB)
2. **Secondary**: Session completion rate — users who send ≥3 messages per session (indicates the assistant is useful enough to continue)
3. **Operational**: P95 response latency ≤8s on Ollama (local), ≤3s on Claude

### Assumptions

1. Users are internal team members, not public — no auth/rate-limiting required for MVP
2. Transcripts are plain `.txt` files; no PDF parsing or audio transcription needed
3. "Local demo" means Ollama running on the evaluator's machine, not a containerized GPU
4. PostgreSQL is available (Supabase/Railway for cloud, local Docker for demo)
5. The evaluator has sufficient RAM to run `llama3.2` (8B, ~5GB VRAM or 8GB RAM)
6. Ship 30 for 30 essays are the primary long-form content output; other formats are secondary

### Scope

**Included**:
- Conversational RAG over Lenny's transcripts
- Session persistence in PostgreSQL
- Ship 30 for 30 essay skill
- Markdown and HTML artifact generation + in-app viewer
- Ollama (local) + Anthropic (cloud) LLM toggle
- FAISS vector index with sentence-transformers embeddings
- FastAPI backend with structured errors and health endpoint
- React frontend with sidebar, chat, artifact viewer

**Excluded**:
- User authentication (out of scope for internal tool MVP)
- Real-time streaming responses (adds complexity; polling is sufficient for demo)
- Automatic transcript fetching/scraping (legal/ToS risk; manual ingestion documented)
- Mobile-native app (responsive web is sufficient)
- Multi-user isolation (single-tenant for demo)

### Risks and Trade-offs

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Hallucination on thin context | Medium | Explicit system prompt instructs model to acknowledge gaps; sources displayed |
| Ollama latency (>15s on slow hardware) | Medium | 120s timeout; loading indicator; documented hardware requirements |
| HTML artifact XSS | High without mitigation | DOMPurify sanitization + sandboxed iframe (no scripts, no forms) |
| FAISS index stale after new transcripts | Low | Documented rebuild process; startup auto-loads cached index |
| Anthropic API cost overrun | Low | Haiku model selected (cheapest); no streaming (single call per turn) |
| Small transcript corpus (5 episodes) | Medium | Sample episodes cover core topics; ingestion is self-serve |

---

## User Flows

### Flow 1: Grounded Q&A
1. User opens app → welcome screen
2. User types question or clicks suggestion chip
3. Backend retrieves top-5 transcript chunks via FAISS
4. LLM generates answer grounded in context
5. Response displays with source episode tags
6. User asks follow-up → session context preserved

### Flow 2: Ship 30 Essay
1. User types "write a ship 30 essay about [topic]"
2. Intent detected → Ship 30 skill activated
3. RAG retrieves relevant chunks
4. LLM generates ~1,250-word essay with Ship 30 structure
5. Essay displayed in chat + "View Markdown Artifact" button appears
6. User clicks → Artifact Viewer opens beside chat

### Flow 3: Artifact Generation
1. User requests "generate a markdown doc about onboarding"
2. Intent detected → artifact skill activated
3. Document generated and rendered in Artifact Viewer
4. HTML artifacts rendered in sandboxed iframe

---

## Acceptance Criteria

- [ ] Chat responds with grounded answers citing episode sources
- [ ] Sessions persist across page refresh (stored in PostgreSQL)
- [ ] Ship 30 essays are ~1,250 words with hook, insights, takeaway
- [ ] Artifact Viewer renders Markdown and HTML beside chat
- [ ] HTML artifacts are sanitized (no script execution)
- [ ] LLM provider switches via `.env` without code changes
- [ ] `/health` endpoint reports DB, retrieval, and provider status
- [ ] All tests pass (`pytest -v`)
- [ ] App starts with `docker compose up --build`

---

## Implementation Plan

| Phase | Tasks | Status |
|-------|-------|--------|
| 1 | FastAPI skeleton, DB models, health endpoint | ✅ |
| 2 | FAISS retrieval service, transcript ingestion | ✅ |
| 3 | LLM service (Ollama + Anthropic), agent routing | ✅ |
| 4 | Chat API with session persistence | ✅ |
| 5 | React frontend: sidebar, chat, input | ✅ |
| 6 | Artifact Viewer with DOMPurify + sandboxed iframe | ✅ |
| 7 | Docker Compose, .env.example, README | ✅ |
| 8 | Tests, docs (PRD, architecture, design) | ✅ |
