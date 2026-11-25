from typing import TypedDict, Optional, List, Dict, Any


class ComplianceState(TypedDict):
    # Input
    user_id: str
    conversation_id: str
    message: str
    history: List[Dict[str, Any]]

    # Routing & Flow Control
    intent: str  # "smalltalk", "compliance_faq", "out_of_scope", "clarification"
    extracted_keywords: List[str]
    retrieved_faqs: List[Dict[str, Any]]
    best_match_score: float

    # Output
    reply: str
    source_citation: Optional[Dict[str, Any]]
    category: Optional[str]
    is_direct_hit: bool  # True if 0 tokens consumed
    error: bool
