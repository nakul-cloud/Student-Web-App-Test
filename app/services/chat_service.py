import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Conversation, Message
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.redis_service import (
    get_session_history,
    save_session_turn,
    get_last_category,
    is_followup_question,
)
from app.ai.graph.builder import compliance_agent_graph
from app.utils.logger import logger


async def ensure_guest_user(db: AsyncSession, user_id: str) -> None:
    """Ensures guest evaluator account exists in PostgreSQL."""
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        guest = User(
            id=user_id,
            email="guest.evaluator@giftcity.in",
            hashed_password="guest",
            full_name="Guest Evaluator (GIFT City IFSC)"
        )
        db.add(guest)
        await db.commit()


async def process_chat(req: ChatRequest, user_id: str, db: AsyncSession) -> ChatResponse:
    await ensure_guest_user(db, user_id)

    # 1. Resolve or create active conversation session
    conv_id = req.conversation_id
    conversation: Conversation | None = None

    if conv_id:
        conversation = await db.scalar(
            select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user_id)
        )

    if not conversation:
        conv_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conv_id,
            user_id=user_id,
            title=req.message[:50].strip(),
            category="General",
        )
        db.add(conversation)
        await db.commit()
    else:
        conv_id = conversation.id

    # 2. Fetch context from Redis hot memory (last 10 turns)
    cached_history = await get_session_history(user_id, conv_id)
    last_cat = await get_last_category(user_id, conv_id)

    # 3. Invoke LangGraph Engine
    graph_res = await compliance_agent_graph.ainvoke({
        "user_id": user_id,
        "conversation_id": conv_id,
        "message": req.message,
        "history": cached_history,
    })

    reply = graph_res.get("reply", "I am unable to answer at this moment.")
    source = graph_res.get("source_citation")
    current_cat = graph_res.get("category", "General")
    is_direct = graph_res.get("is_direct_hit", False)

    # 4. Save to Redis Session Buffer
    await save_session_turn(
        user_id=user_id,
        conversation_id=conv_id,
        user_message=req.message,
        assistant_reply=reply,
        source_citation=source,
        category=current_cat,
    )

    # 5. Smart Persistence Rule:
    # "after asking any question if user is asking follow up question then dont save,
    # only after asking different question then only save"
    is_followup = is_followup_question(last_cat, current_cat, req.message)

    if not is_followup:
        # A distinct/new question: commit to PostgreSQL for long-term history
        logger.info(f"[DB Persistence] Saving distinct question & answer to PostgreSQL for conv_id={conv_id}")
        user_msg_db = Message(
            conversation_id=conv_id,
            role="user",
            content=req.message,
        )
        assistant_msg_db = Message(
            conversation_id=conv_id,
            role="assistant",
            content=reply,
            source_citation=source,
        )
        conversation.category = current_cat
        if conversation.title == "New Compliance Inquiry" or len(conversation.title) < 5:
            conversation.title = req.message[:50]

        db.add(user_msg_db)
        db.add(assistant_msg_db)
        await db.commit()
    else:
        logger.info(f"[DB Persistence] Skipping DB write: message is a follow-up query on '{last_cat}'")

    return ChatResponse(
        conversation_id=conv_id,
        reply=reply,
        source_citation=source,
        category=current_cat,
        is_direct_hit=is_direct,
        error=False,
    )


async def get_user_conversations(user_id: str, db: AsyncSession):
    """Retrieves list of stored user conversations from PostgreSQL."""
    res = await db.scalars(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "category": c.category or "General",
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M"),
            "updated_at": c.updated_at.strftime("%Y-%m-%d %H:%M"),
        }
        for c in res.all()
    ]


async def get_conversation_messages(user_id: str, conversation_id: str, db: AsyncSession):
    """Loads historical messages for a conversation from PostgreSQL."""
    res = await db.scalars(
        select(Message)
        .join(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .order_by(Message.created_at.asc())
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "source_citation": m.source_citation,
            "created_at": m.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for m in res.all()
    ]
