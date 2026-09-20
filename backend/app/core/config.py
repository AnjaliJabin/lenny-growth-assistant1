from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    LLM_PROVIDER: Literal["anthropic", "ollama"] = "ollama"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/lenny_assistant"

    SECRET_KEY: str = "change_me"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_INDEX_PATH: str = "./data/vector_index"
    TRANSCRIPTS_PATH: str = "./data/transcripts"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
