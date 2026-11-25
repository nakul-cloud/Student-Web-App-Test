from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.schemas.chat import RegisterRequest, LoginRequest, TokenResponse
from app.services.auth_service import register_user, authenticate_user, create_access_token
from app.utils.limiter import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("15/minute")
async def register(request: Request, req: RegisterRequest, db: AsyncSession = Depends(get_db_session)):
    user = await register_user(req, db)
    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
async def login(request: Request, req: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    user = await authenticate_user(req, db)
    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
    )


@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(db: AsyncSession = Depends(get_db_session)):
    """1-Click Demo login for exam evaluators and interviewers."""
    demo_email = "assessor@giftcity-comply.in"
    demo_req = LoginRequest(email=demo_email, password="password123")
    try:
        user = await authenticate_user(demo_req, db)
    except Exception:
        # Create demo user on the fly if not exists
        user = await register_user(
            RegisterRequest(
                email=demo_email,
                password="password123",
                full_name="Assessor (GIFT City IFSC)"
            ),
            db
        )
    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
    )
