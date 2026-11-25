import re
from typing import Dict, Any, List
from qdrant_client.models import Filter, FieldCondition, MatchText
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.ai.graph.state import ComplianceState
from app.ai.prompts.loader import load_prompt, load_response
from app.providers.qdrant_provider import get_qdrant_client
from app.providers.llm_provider import invoke_with_fallback
from app.config.settings import settings
from app.utils.guardrails import is_gibberish, check_guardrails
from app.utils.logger import logger


def _static_node_response(template_key: str, category: str) -> Dict[str, Any]:
    """Shared helper to build zero-token static node responses dynamically from responses.json."""
    reply = load_response(
        template_key,
        company_name=settings.compliance_company_name,
        jurisdiction=settings.compliance_jurisdiction,
    )
    return {
        "reply": reply,
        "source_citation": None,
        "category": category,
        "is_direct_hit": True,
        "error": False,
    }


def _build_citation(faq: Dict[str, Any]) -> Dict[str, Any]:
    """Builds a structured citation dictionary including extracted page number if present."""
    ref = str(faq.get("source") or "")
    page_match = re.search(r"\((Page\s*\d+)\)", ref, re.IGNORECASE)
    return {
        "faq_id": faq["id"],
        "question": faq["question"],
        "category": faq["category"],
        "reference": ref,
        "page_number": page_match.group(1) if page_match else None,
    }


def intent_router_node(state: ComplianceState) -> Dict[str, Any]:
    msg = state["message"].strip()
    lower = msg.lower()

    # 1. Gibberish / keyboard smash check (0 tokens)
    if is_gibberish(msg):
        logger.info("[Guardrail] Gibberish detected, routing to gibberish_node.")
        return {"intent": "gibberish"}

    # 2. Smalltalk / Greeting / Polite Vocabulary check (0 LLM tokens)
    clean_lower = re.sub(r"[!?.,]+$", "", lower).strip()
    if any(
        clean_lower == phrase or clean_lower.startswith(phrase + " ")
        for phrase in settings.smalltalk_vocab
    ):
        logger.info(f"[Intent Router] Matched smalltalk vocab: '{clean_lower}' (0 tokens).")
        return {"intent": "smalltalk"}

    # 3. Safety Guardrails: Prompt Injection & Off-Topic check (0 tokens)
    blocked, reason = check_guardrails(msg)
    if blocked:
        logger.info(f"[Guardrail] Blocked request ({reason}).")
        return {"intent": "guardrail_blocked"}

    # 4. Keyword extraction & vague-query check (driven by settings)
    stop_set = set(settings.stopwords)
    words = [w for w in re.split(r"\W+", lower) if len(w) > 2 and w not in stop_set]
    if not words and lower not in settings.short_compliance_terms:
        return {"intent": "clarification"}

    return {"intent": "compliance_faq", "extracted_keywords": words}


def gibberish_node(state: ComplianceState) -> Dict[str, Any]:
    return _static_node_response("gibberish", "Gibberish")


def guardrail_blocked_node(state: ComplianceState) -> Dict[str, Any]:
    return _static_node_response("guardrail_blocked", "Guardrail")


def smalltalk_node(state: ComplianceState) -> Dict[str, Any]:
    return _static_node_response("smalltalk", "Smalltalk")


def clarification_node(state: ComplianceState) -> Dict[str, Any]:
    return _static_node_response("clarification", "Clarification")


def fallback_node(state: ComplianceState) -> Dict[str, Any]:
    return _static_node_response("fallback", "Unknown")


async def qdrant_retrieval_node(state: ComplianceState) -> Dict[str, Any]:
    client = get_qdrant_client()
    query = state["message"].strip()
    words = state.get("extracted_keywords") or [w for w in re.split(r"\W+", query.lower()) if len(w) > 2]

    should_conditions = []
    for w in words[:settings.retrieval_scan_limit]:
        should_conditions.append(FieldCondition(key="keywords", match=MatchText(text=w)))
        should_conditions.append(FieldCondition(key="question", match=MatchText(text=w)))
        should_conditions.append(FieldCondition(key="answer", match=MatchText(text=w)))

    matched_faqs: List[Dict[str, Any]] = []

    try:
        scroll_res, _ = await client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=Filter(should=should_conditions) if should_conditions else None,
            limit=settings.retrieval_scan_limit,
            with_payload=True,
        )

        for point in scroll_res:
            p = point.payload or {}
            combined = (p.get("question", "") + " " + p.get("keywords", "") + " " + p.get("answer", "")).lower()
            overlap = sum(1 for w in words if w in combined)
            score = round(overlap / max(len(words), 1), 2)
            matched_faqs.append({
                "id": p.get("id"),
                "category": p.get("category"),
                "question": p.get("question"),
                "answer": p.get("answer"),
                "source": p.get("source"),
                "score": score,
            })

        matched_faqs.sort(key=lambda x: x["score"], reverse=True)
    except Exception as e:
        logger.error(f"[Vectorless RAG] Qdrant search exception: {e}")

    best_score = matched_faqs[0]["score"] if matched_faqs else 0.0
    return {
        "retrieved_faqs": matched_faqs[:settings.retrieval_top_k],
        "best_match_score": best_score,
    }


def direct_return_node(state: ComplianceState) -> Dict[str, Any]:
    best = state["retrieved_faqs"][0]
    return {
        "reply": best["answer"],
        "source_citation": _build_citation(best),
        "category": best["category"],
        "is_direct_hit": True,
        "error": False,
    }


async def answer_synthesizer_node(state: ComplianceState) -> Dict[str, Any]:
    faqs = state["retrieved_faqs"]
    if not faqs:
        return fallback_node(state)

    top_faq = faqs[0]
    context_text = "\n\n".join([
        f"[Document Source: {f['source']} | Topic: {f['category']}]\nContext: {f['answer']}"
        for f in faqs
    ])

    system_prompt = load_prompt(
        "compliance_system.txt",
        company_name=settings.compliance_company_name,
        jurisdiction=settings.compliance_jurisdiction,
        context=context_text,
    )

    messages = [SystemMessage(content=system_prompt)]
    for h in state.get("history", [])[-settings.llm_history_window:]:
        if h.get("role") == "user":
            messages.append(HumanMessage(content=h.get("content", "")))
        elif h.get("role") == "assistant":
            messages.append(AIMessage(content=h.get("content", "")))

    messages.append(HumanMessage(content=state["message"]))

    try:
        reply_content = await invoke_with_fallback(messages)
        return {
            "reply": reply_content,
            "source_citation": _build_citation(top_faq),
            "category": top_faq["category"],
            "is_direct_hit": False,
            "error": False,
        }
    except Exception as e:
        logger.error(f"[LangGraph Synthesizer] LLM invoke failed: {e}")
        return {
            "reply": f"{top_faq['answer']}\n\n*(Directly retrieved from official GIFT City documentation)*",
            "source_citation": _build_citation(top_faq),
            "category": top_faq["category"],
            "is_direct_hit": True,
            "error": False,
        }
