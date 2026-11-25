from langgraph.graph import StateGraph, START, END
from app.config.settings import settings
from app.ai.graph.state import ComplianceState
from app.ai.graph.nodes import (
    intent_router_node,
    smalltalk_node,
    clarification_node,
    gibberish_node,
    guardrail_blocked_node,
    fallback_node,
    qdrant_retrieval_node,
    direct_return_node,
    answer_synthesizer_node,
)


def route_intent(state: ComplianceState) -> str:
    return state.get("intent", "compliance_faq")


def route_retrieval(state: ComplianceState) -> str:
    faqs = state.get("retrieved_faqs", [])
    best_score = state.get("best_match_score", 0.0)
    if not faqs or best_score < settings.retrieval_min_threshold:
        return "fallback"

    top_source = str(faqs[0].get("source") or "").lower()
    is_pdf_chunk = ".pdf" in top_source

    # Only curated FAQs bypass LLM via direct_return; PDF chunks always route through synthesizer
    if not is_pdf_chunk and best_score >= settings.direct_hit_threshold:
        return "direct_return"

    return "synthesizer"


def build_compliance_graph():
    """Builds and compiles the StateGraph workflow."""
    workflow = StateGraph(ComplianceState)

    # 1. Add Nodes
    workflow.add_node("intent_router", intent_router_node)
    workflow.add_node("smalltalk", smalltalk_node)
    workflow.add_node("clarification", clarification_node)
    workflow.add_node("gibberish", gibberish_node)
    workflow.add_node("guardrail_blocked", guardrail_blocked_node)
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("qdrant_retrieval", qdrant_retrieval_node)
    workflow.add_node("direct_return", direct_return_node)
    workflow.add_node("synthesizer", answer_synthesizer_node)

    # 2. Add Edges & Conditional Routes
    workflow.add_edge(START, "intent_router")

    workflow.add_conditional_edges(
        "intent_router",
        route_intent,
        {
            "smalltalk": "smalltalk",
            "clarification": "clarification",
            "gibberish": "gibberish",
            "guardrail_blocked": "guardrail_blocked",
            "out_of_scope": "fallback",
            "compliance_faq": "qdrant_retrieval",
        }
    )

    workflow.add_conditional_edges(
        "qdrant_retrieval",
        route_retrieval,
        {
            "fallback": "fallback",
            "direct_return": "direct_return",
            "synthesizer": "synthesizer",
        }
    )

    # Terminal edges
    workflow.add_edge("smalltalk", END)
    workflow.add_edge("clarification", END)
    workflow.add_edge("gibberish", END)
    workflow.add_edge("guardrail_blocked", END)
    workflow.add_edge("fallback", END)
    workflow.add_edge("direct_return", END)
    workflow.add_edge("synthesizer", END)

    return workflow.compile()


compliance_agent_graph = build_compliance_graph()
