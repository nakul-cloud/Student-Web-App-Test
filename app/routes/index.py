from fastapi import APIRouter
from app.routes.auth_routes import router as auth_router
from app.routes.ingest_routes import router as ingest_router
from app.chatbot.router import router as chatbot_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(ingest_router)
api_router.include_router(chatbot_router)
