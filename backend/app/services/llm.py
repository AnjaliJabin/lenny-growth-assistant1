"""
LLM service: wraps Anthropic Claude and Ollama behind a unified interface.
"""
import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Lenny Growth Assistant, an expert on product management and growth strategy.
You answer questions strictly based on Lenny's Podcast transcripts provided as context.
Always cite the episode/source when you use information from it.
If the context does not contain enough information to answer, say so clearly—do not hallucinate.
Be concise, practical, and direct."""


class LLMService:
    async def complete(self, messages: list[dict], system: str = SYSTEM_PROMPT) -> str:
        if settings.LLM_PROVIDER == "anthropic":
            return await self._anthropic(messages, system)
        return await self._ollama(messages, system)

    async def _anthropic(self, messages: list[dict], system: str) -> str:
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set")
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=2048,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    async def _ollama(self, messages: list[dict], system: str) -> str:
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [{"role": "system", "content": system}] + messages,
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["message"]["content"]
        except httpx.ConnectError:
            raise RuntimeError(f"Ollama not reachable at {settings.OLLAMA_BASE_URL}. Is it running?")
        except httpx.TimeoutException:
            raise RuntimeError("Ollama request timed out after 120s")

    @property
    def provider(self) -> str:
        return settings.LLM_PROVIDER


llm_service = LLMService()
