"""
Agent service: routes user intent to the right skill and builds prompts.
Skills: general_qa, ship30, artifact_markdown, artifact_html
"""
from app.services.llm import llm_service
from app.services.retrieval import retrieval_service
from app.core.logging import get_logger

logger = get_logger(__name__)

SHIP30_SYSTEM = """You are a writing coach trained in the Ship 30 for 30 methodology.
Write a ~1,250-word atomic essay using ONLY the provided transcript context.
Structure:
1. Hook (1-2 punchy sentences that create curiosity or tension)
2. Problem/Insight (what most people get wrong)
3. Core argument with 3-5 specific, numbered insights from the transcripts
4. Practical takeaway (what the reader should do Monday morning)
Rules:
- Use short paragraphs (1-3 sentences max)
- Bold the single most important sentence per section
- Use bullet points for lists
- Every claim must trace back to a named episode/source
- End with one memorable, quotable sentence
Do NOT hallucinate. If context is thin, say so and work with what you have."""

ARTIFACT_SYSTEM = """You are a technical writer. Generate a complete, well-structured document.
For Markdown: use proper headings, tables, code blocks where relevant.
For HTML: output a complete self-contained HTML snippet with inline CSS (no external dependencies).
Ground all content in the provided transcript context. Cite sources inline."""


def _build_context_block(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant transcript context found."
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[Source {i}: {c['episode']}]\n{c['text']}")
    return "\n\n---\n\n".join(parts)


def _extract_sources(chunks: list[dict]) -> list[dict]:
    seen = set()
    sources = []
    for c in chunks:
        key = c["episode"]
        if key not in seen:
            seen.add(key)
            sources.append({"episode": c["episode"], "file": c["source"], "score": round(c["score"], 3)})
    return sources


async def run_chat(
    user_message: str,
    history: list[dict],
) -> tuple[str, list[dict], dict | None]:
    """
    Returns (reply_text, sources, artifact_or_None)
    """
    intent = _detect_intent(user_message)
    logger.info(f'"intent={intent} query={user_message[:60]}"')

    chunks = retrieval_service.retrieve(user_message)
    context = _build_context_block(chunks)
    sources = _extract_sources(chunks)

    if intent == "ship30":
        reply = await _run_ship30(user_message, context, history)
        artifact = {"type": "markdown", "content": reply}
        return reply, sources, artifact

    if intent in ("artifact_md", "artifact_html"):
        art_type = "html" if intent == "artifact_html" else "markdown"
        reply = await _run_artifact(user_message, context, history, art_type)
        artifact = {"type": art_type, "content": reply}
        return reply, sources, artifact

    # General QA
    reply = await _run_qa(user_message, context, history)
    return reply, sources, None


def _detect_intent(msg: str) -> str:
    lower = msg.lower()
    if any(k in lower for k in ["ship 30", "ship30", "atomic essay", "write an essay", "essay about"]):
        return "ship30"
    if any(k in lower for k in ["html artifact", "html page", "generate html", "create html", "build html"]):
        return "artifact_html"
    if any(k in lower for k in ["markdown doc", "generate markdown", "create a doc", "write a doc", "artifact"]):
        return "artifact_md"
    return "qa"


async def _run_qa(query: str, context: str, history: list[dict]) -> str:
    messages = history[-6:] + [{
        "role": "user",
        "content": f"Context from Lenny's transcripts:\n{context}\n\nQuestion: {query}"
    }]
    return await llm_service.complete(messages)


async def _run_ship30(topic: str, context: str, history: list[dict]) -> str:
    messages = history[-4:] + [{
        "role": "user",
        "content": f"Transcript context:\n{context}\n\nWrite a Ship 30 for 30 essay about: {topic}"
    }]
    return await llm_service.complete(messages, system=SHIP30_SYSTEM)


async def _run_artifact(topic: str, context: str, history: list[dict], art_type: str) -> str:
    fmt = "HTML with inline CSS" if art_type == "html" else "Markdown"
    messages = history[-4:] + [{
        "role": "user",
        "content": f"Transcript context:\n{context}\n\nGenerate a {fmt} document about: {topic}"
    }]
    return await llm_service.complete(messages, system=ARTIFACT_SYSTEM)
