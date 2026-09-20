# Manual Test Plan — Lenny Growth Assistant

## Setup
1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `npm run dev`
3. Ensure Ollama is running with `llama3.2` pulled
4. Open `http://localhost:5173`

---

## Test Cases

### TC-01: Welcome Screen
- **Action**: Open app with no sessions
- **Expected**: Welcome screen with icon, title, subtitle, and suggestion chips visible

### TC-02: New Chat via Suggestion Chip
- **Action**: Click "What is product-market fit and how do I measure it?"
- **Expected**: Text populates input; user can edit before sending

### TC-03: Grounded Q&A
- **Action**: Send "What is product-market fit?"
- **Expected**: Response cites at least one episode (source tags visible below message)

### TC-04: Session Persistence
- **Action**: Send a message, refresh the page, click the session in sidebar
- **Expected**: Previous messages reload correctly

### TC-05: Ship 30 Essay
- **Action**: Send "Write a Ship 30 essay about growth loops"
- **Expected**: ~1,250-word essay with hook, numbered insights, takeaway; "View Markdown Artifact" button appears

### TC-06: Markdown Artifact Viewer
- **Action**: Click "View Markdown Artifact" button
- **Expected**: Artifact panel opens to the right; essay renders with proper headings and formatting

### TC-07: HTML Artifact
- **Action**: Send "Generate an HTML artifact about onboarding best practices"
- **Expected**: HTML artifact renders in sandboxed iframe; no script execution

### TC-08: HTML Security
- **Action**: If possible, prompt the model to include `<script>alert('xss')</script>` in HTML output
- **Expected**: No alert fires; script tag stripped by DOMPurify

### TC-09: Follow-up Questions
- **Action**: Ask "What is PMF?" then follow up with "How did Superhuman measure it?"
- **Expected**: Second response references Superhuman context from the conversation

### TC-10: Provider Badge
- **Action**: Check sidebar
- **Expected**: Provider badge shows "🦙 Ollama (local)" when `LLM_PROVIDER=ollama`

### TC-11: Delete Session
- **Action**: Hover over a session, click ×
- **Expected**: Session removed from list; if active, chat clears

### TC-12: Health Endpoint
- **Action**: GET `http://localhost:8000/health`
- **Expected**: `{"status":"ok","provider":"ollama","db":"ok","retrieval":"ready"}`

### TC-13: Empty Retrieval Graceful Handling
- **Action**: Ask a question completely unrelated to product/growth (e.g., "What is the capital of France?")
- **Expected**: Model acknowledges limited context; does not hallucinate transcript content

### TC-14: Ollama Unavailable
- **Action**: Stop Ollama, send a message
- **Expected**: Error banner: "Ollama not reachable at http://localhost:11434. Is it running?"

### TC-15: Invalid Session ID
- **Action**: POST `/api/chat` with `session_id: "fake-id"`
- **Expected**: HTTP 404 with `{"detail": "Session not found"}`
