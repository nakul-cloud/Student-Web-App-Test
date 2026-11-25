from typing import Any
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

from app.config.settings import settings
from app.utils.logger import logger


class LLMFactory:
    """
    Dynamic resilient LLM provider factory with primary & fallback models:
    Primary: Groq (openai/gpt-oss-120b)
    Fallback: Groq (qwen/qwen-2.5-32b)
    Emergency Backup: OpenAI (gpt-4o-mini)
    """

    @staticmethod
    def get_primary_llm(temperature: float = 0.2, max_tokens: int = 700) -> BaseChatModel:
        if settings.groq_api_key:
            return ChatGroq(
                model=settings.groq_primary_model,
                groq_api_key=settings.groq_api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=25,
            )
        return LLMFactory.get_emergency_llm(temperature, max_tokens)

    @staticmethod
    def get_fallback_llm(temperature: float = 0.2, max_tokens: int = 700) -> BaseChatModel:
        if settings.groq_api_key:
            return ChatGroq(
                model=settings.groq_fallback_model,
                groq_api_key=settings.groq_api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=25,
            )
        return LLMFactory.get_emergency_llm(temperature, max_tokens)

    @staticmethod
    def get_emergency_llm(temperature: float = 0.2, max_tokens: int = 700) -> BaseChatModel:
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=25,
        )


async def invoke_with_fallback(messages: list) -> str:
    """Tries primary Groq model -> fallback Groq Qwen model -> emergency OpenAI."""
    # 1. Primary
    try:
        llm = LLMFactory.get_primary_llm()
        logger.info(f"[LLM] Trying primary model: {settings.groq_primary_model}")
        res = await llm.ainvoke(messages)
        return str(res.content).strip()
    except Exception as e_primary:
        logger.warning(f"[LLM] Primary model failed: {e_primary}. Trying fallback: {settings.groq_fallback_model}")

    # 2. Fallback
    try:
        fallback_llm = LLMFactory.get_fallback_llm()
        res = await fallback_llm.ainvoke(messages)
        logger.info("[LLM] Fallback model succeeded.")
        return str(res.content).strip()
    except Exception as e_fallback:
        logger.warning(f"[LLM] Fallback model failed: {e_fallback}. Trying emergency backup OpenAI.")

    # 3. Emergency Backup
    backup_llm = LLMFactory.get_emergency_llm()
    res = await backup_llm.ainvoke(messages)
    return str(res.content).strip()
