import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


async def override_get_db():
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "provider" in data


@pytest.mark.asyncio
async def test_create_session(client):
    resp = await client.post("/api/sessions", json={"title": "Test Session"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Session"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_sessions(client):
    await client.post("/api/sessions", json={"title": "S1"})
    await client.post("/api/sessions", json={"title": "S2"})
    resp = await client.get("/api/sessions")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_get_messages_empty(client):
    sess = (await client.post("/api/sessions", json={})).json()
    resp = await client.get(f"/api/sessions/{sess['id']}/messages")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_chat_creates_session_and_messages(client):
    with patch(
        "app.api.chat.run_chat",
        new=AsyncMock(return_value=("Test reply", [{"episode": "ep1", "file": "ep1.txt", "score": 0.9}], None)),
    ):
        resp = await client.post("/api/chat", json={"message": "What is product-market fit?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"]["role"] == "assistant"
    assert data["message"]["content"] == "Test reply"
    assert data["session_id"]


@pytest.mark.asyncio
async def test_chat_with_existing_session(client):
    sess = (await client.post("/api/sessions", json={"title": "Existing"})).json()
    with patch("app.api.chat.run_chat", new=AsyncMock(return_value=("Reply", [], None))):
        resp = await client.post("/api/chat", json={"message": "Hello", "session_id": sess["id"]})
    assert resp.status_code == 200
    assert resp.json()["session_id"] == sess["id"]


@pytest.mark.asyncio
async def test_chat_invalid_session(client):
    resp = await client.post("/api/chat", json={"message": "Hi", "session_id": "nonexistent-id"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_session(client):
    sess = (await client.post("/api/sessions", json={})).json()
    resp = await client.delete(f"/api/sessions/{sess['id']}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_chat_llm_error_returns_503(client):
    with patch("app.api.chat.run_chat", new=AsyncMock(side_effect=RuntimeError("Ollama not reachable"))):
        resp = await client.post("/api/chat", json={"message": "test"})
    assert resp.status_code == 503


def test_retrieval_returns_empty_when_not_ready():
    from app.services.retrieval import RetrievalService
    svc = RetrievalService()
    results = svc.retrieve("growth loops")
    assert results == []


def test_intent_detection():
    from app.services.agent import _detect_intent
    assert _detect_intent("write a ship 30 essay about retention") == "ship30"
    assert _detect_intent("generate html artifact for onboarding") == "artifact_html"
    assert _detect_intent("generate markdown doc about activation") == "artifact_md"
    assert _detect_intent("what is product market fit?") == "qa"


def test_context_block_empty():
    from app.services.agent import _build_context_block
    result = _build_context_block([])
    assert "No relevant" in result


def test_context_block_with_chunks():
    from app.services.agent import _build_context_block
    chunks = [{"text": "hello world", "episode": "ep1", "source": "ep1.txt", "score": 0.9}]
    result = _build_context_block(chunks)
    assert "ep1" in result
    assert "hello world" in result
