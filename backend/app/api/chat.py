from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.db import Session, Message
from app.models.schemas import (
    SessionCreate, SessionResponse, MessageResponse, ChatRequest, ChatResponse
)
from app.services.agent import run_chat
from app.services.llm import llm_service
from app.core.logging import get_logger
import uuid

router = APIRouter(prefix="/api", tags=["chat"])
logger = get_logger(__name__)


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = Session(id=str(uuid.uuid4()), title=body.title, user_metadata=body.user_metadata)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).order_by(Session.updated_at.desc()).limit(50))
    return result.scalars().all()


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    return result.scalars().all()


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")
    await db.delete(session)
    await db.commit()


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    # Get or create session
    if body.session_id:
        result = await db.execute(select(Session).where(Session.id == body.session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(404, "Session not found")
    else:
        session = Session(id=str(uuid.uuid4()), title=body.message[:60])
        db.add(session)
        await db.flush()

    # Load history
    hist_result = await db.execute(
        select(Message).where(Message.session_id == session.id).order_by(Message.created_at).limit(20)
    )
    history = [{"role": m.role, "content": m.content} for m in hist_result.scalars().all()]

    # Save user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        session_id=session.id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)

    # Run agent
    try:
        reply_text, sources, artifact = await run_chat(body.message, history)
    except RuntimeError as e:
        logger.error(f'"LLM error: {e}"')
        raise HTTPException(503, str(e))
    except Exception as e:
        logger.error(f'"Unexpected error: {e}"')
        raise HTTPException(500, "Internal error")

    # Save assistant message
    assistant_msg = Message(
        id=str(uuid.uuid4()),
        session_id=session.id,
        role="assistant",
        content=reply_text,
        sources=sources,
        artifact=artifact,
    )
    db.add(assistant_msg)

    # Update session title if new
    if session.title == "New Chat" or not body.session_id:
        session.title = body.message[:60]

    await db.commit()
    await db.refresh(assistant_msg)

    return ChatResponse(
        session_id=session.id,
        message=MessageResponse.model_validate(assistant_msg),
        provider=llm_service.provider,
    )
