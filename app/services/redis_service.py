import json
from typing import Any
from app.config.redis import get_redis
from app.utils.logger import logger

SESSION_TTL_SECONDS = 7200  # 2 hours


def build_session_key(user_id: str, conversation_id: str) -> str:
    return f"user:{user_id}:session:{conversation_id}"


def is_followup_question(last_category: str | None, current_category: str | None, message: str) -> bool:
    """
    Evaluates if user's message is a follow-up query on the existing topic
    or a brand-new compliance subject requiring permanent Postgres persistence.
    """
    clean_msg = message.strip().lower()
    
    # Common follow-up prefixes
    followup_starters = [
        "and", "also", "what about", "how about", "tell me more",
        "can you explain", "so", "then", "why", "who", "where",
        "what if", "does it", "is it", "more details", "thanks", "ok"
    ]
    if any(clean_msg.startswith(prefix) for prefix in followup_starters):
        return True

    # Short pronoun-heavy question
    words = clean_msg.split()
    if len(words) <= 6 and any(w in words for w in ["it", "this", "that", "they", "them", "these"]):
        return True

    # If category changed distinctly (e.g., Tax -> AML)
    if last_category and current_category and last_category != current_category and current_category != "General":
        return False

    return False


async def get_session_history(user_id: str, conversation_id: str) -> list[dict[str, Any]]:
    """Retrieves ongoing chat context list from Redis."""
    try:
        r = await get_redis()
        key = build_session_key(user_id, conversation_id)
        raw = await r.get(key)
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning(f"[Redis] Error reading session history: {e}")
    return []


async def save_session_turn(
    user_id: str,
    conversation_id: str,
    user_message: str,
    assistant_reply: str,
    source_citation: dict | None,
    category: str | None,
) -> None:
    """Appends turn to Redis and refreshes TTL."""
    try:
        r = await get_redis()
        key = build_session_key(user_id, conversation_id)
        history = await get_session_history(user_id, conversation_id)

        history.append({"role": "user", "content": user_message})
        history.append({
            "role": "assistant",
            "content": assistant_reply,
            "source_citation": source_citation,
            "category": category,
        })

        # Keep last 10 messages for token budget
        history = history[-10:]

        await r.setex(key, SESSION_TTL_SECONDS, json.dumps(history))
        # Store metadata for topic transition checks
        meta_key = f"user:{user_id}:meta:{conversation_id}"
        await r.setex(meta_key, SESSION_TTL_SECONDS, json.dumps({"last_category": category or "General"}))
    except Exception as e:
        logger.error(f"[Redis] Error saving session turn: {e}")


async def get_last_category(user_id: str, conversation_id: str) -> str | None:
    try:
        r = await get_redis()
        meta_key = f"user:{user_id}:meta:{conversation_id}"
        raw = await r.get(meta_key)
        if raw:
            data = json.loads(raw)
            return data.get("last_category")
    except Exception:
        pass
    return None
