from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.middlewares.auth_deps import get_current_user_id
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import (
    process_chat,
    get_user_conversations,
    get_conversation_messages,
)

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

@router.get("/", include_in_schema=False)
async def serve_chat_ui() -> RedirectResponse:
    """Redirect to the modular React frontend."""
    return RedirectResponse(url="/frontend/", status_code=302)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
) -> ChatResponse:
    return await process_chat(req, user_id, db)


@router.get("/sessions")
async def list_sessions(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    return await get_user_conversations(user_id, db)


@router.get("/sessions/{conversation_id}/messages")
async def get_session_history(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    return await get_conversation_messages(user_id, conversation_id, db)


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db_session)):
    services = {"status": "healthy", "postgres": "ok", "redis": "ok", "qdrant": "ok"}
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
    except Exception as e:
        services["postgres"] = f"unhealthy: {e}"
        services["status"] = "degraded"

    try:
        from app.config.redis import get_redis
        r = await get_redis()
        await r.ping()
    except Exception as e:
        services["redis"] = f"unhealthy: {e}"
        services["status"] = "degraded"

    try:
        from app.providers.qdrant_provider import get_qdrant_client
        q = get_qdrant_client()
        await q.get_collections()
    except Exception as e:
        services["qdrant"] = f"unhealthy: {e}"
        services["status"] = "degraded"

    return {
        "service": "ComplyADI Regulatory FAQ Assistant",
        "jurisdiction": "GIFT City IFSC, Gujarat, India",
        "diagnostics": services,
    }
