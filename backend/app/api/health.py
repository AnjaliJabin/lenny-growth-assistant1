from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.services.llm import llm_service
from app.services.retrieval import retrieval_service
from app.core.database import engine
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    # DB check
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {e}"

    return HealthResponse(
        status="ok",
        provider=llm_service.provider,
        db=db_status,
        retrieval="ready" if retrieval_service.is_ready else "not_ready",
    )
