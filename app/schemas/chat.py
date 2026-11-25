from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)
    full_name: Optional[str] = "GIFT City Executive"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: Optional[str] = None


class MessageHistory(BaseModel):
    role: str
    content: str
    source_citation: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None


class SourceCitation(BaseModel):
    faq_id: int
    question: str
    category: str
    reference: str
    page_number: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    source_citation: Optional[SourceCitation] = None
    category: Optional[str] = "General"
    is_direct_hit: bool = False
    error: bool = False


class ConversationSummary(BaseModel):
    id: str
    title: str
    category: str
    created_at: str
    updated_at: str
