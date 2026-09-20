# Design — Lenny Growth Assistant

## UI/UX Principles

1. **Grounding over generation**: Every answer surfaces its source. Users should never wonder "where did this come from?"
2. **Minimal friction**: Suggestion chips let users start immediately without knowing what to ask
3. **Side-by-side artifacts**: Artifacts open beside the chat, not replacing it — users keep context while reading the output
4. **Dark, focused interface**: Reduces eye strain for long research sessions; keeps attention on content

---

## Information Architecture

```
App
├── Sidebar (persistent)
│   ├── Logo + branding
│   ├── New Chat button
│   ├── Provider badge (Ollama / Claude)
│   ├── Session list (scrollable, most recent first)
│   └── Footer attribution
│
├── Chat Area (main)
│   ├── Welcome screen (empty state)
│   ├── Message thread
│   │   ├── User messages (right-aligned, purple)
│   │   ├── Assistant messages (left-aligned, dark card)
│   │   │   ├── Markdown-rendered content
│   │   │   ├── Source tags (episode citations)
│   │   │   └── "View Artifact" button (when applicable)
│   │   └── Loading indicator (bouncing dots)
│   ├── Error banner (dismissible)
│   └── Input area
│       ├── Suggestion chips
│       ├── Textarea (auto-resize)
│       └── Send button
│
└── Artifact Viewer (conditional, right panel)
    ├── Header (type label + close button)
    └── Body
        ├── Sandboxed iframe (HTML artifacts)
        └── Rendered Markdown (markdown artifacts)
```

---

## Key Interaction States

| State | Visual Treatment |
|-------|-----------------|
| Empty / new chat | Centered welcome with icon, title, subtitle |
| Loading response | Three bouncing dots in assistant bubble position |
| Error | Red-bordered banner with ⚠️ icon and message |
| Artifact available | Purple-bordered "View Artifact" button below message |
| Artifact open | App splits into 3 columns: sidebar / chat / artifact |
| Active session | Left border accent on sidebar item |
| Provider: Ollama | 🦙 badge in sidebar |
| Provider: Claude | ☁️ badge in sidebar |

---

## Responsive Behavior

- **≥1024px**: Full 3-column layout (sidebar + chat + artifact when open)
- **768–1023px**: Sidebar collapses; hamburger menu (future enhancement); artifact overlays
- **<768px**: Single column; sidebar hidden; artifact takes bottom half of screen

---

## Accessibility

- Semantic HTML: `<aside>`, `<main>`, `<nav>`, `<button>` used correctly
- `aria-label` on icon-only buttons (send, close, delete)
- `aria-live="polite"` on message thread for screen reader announcements
- `aria-current="page"` on active session
- `role="alert"` on error banner
- Keyboard navigation: Enter to send, Tab through sessions and buttons
- Color contrast: text on dark backgrounds meets WCAG AA (4.5:1 minimum)
- Focus indicators preserved (browser default + custom outline on textarea)

---

## Design Decisions

**Why dark theme?**
Research sessions are long. Dark backgrounds reduce eye strain and keep focus on text content. The purple accent (`#7c6af7`) provides sufficient contrast without being harsh.

**Why suggestion chips?**
New users don't know what the assistant can do. Chips demonstrate the three core skills (Q&A, Ship 30, artifact) without requiring documentation.

**Why side-by-side artifact viewer instead of modal?**
Modals interrupt context. Users often want to reference the conversation while reading an artifact (e.g., checking which episode a claim came from). Side-by-side preserves both.

**Why sandboxed iframe for HTML artifacts?**
Generated HTML is untrusted. An iframe with `sandbox="allow-same-origin"` renders CSS and layout while blocking JavaScript execution. Combined with DOMPurify, this prevents XSS even if the LLM generates malicious markup.

**Why ReactMarkdown for assistant messages?**
LLMs naturally produce Markdown. Rendering it properly (headers, bold, code blocks, lists) dramatically improves readability of structured answers and essays.

**Why auto-resize textarea?**
Long prompts (e.g., pasting context) shouldn't require horizontal scrolling. The textarea grows up to 160px then scrolls internally.
