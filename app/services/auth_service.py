import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.user import User
from app.schemas.chat import RegisterRequest, LoginRequest
from app.exceptions.custom_exceptions import AppError


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise AppError("Token has expired", status_code=401)
    except jwt.InvalidTokenError:
        raise AppError("Invalid authentication token", status_code=401)


async def register_user(req: RegisterRequest, db: AsyncSession) -> User:
    existing = await db.scalar(select(User).where(User.email == req.email))
    if existing:
        raise AppError("Email already registered", status_code=400)
    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name or "GIFT City Officer"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(req: LoginRequest, db: AsyncSession) -> User:
    user = await db.scalar(select(User).where(User.email == req.email))
    if not user or not verify_password(req.password, user.hashed_password):
        raise AppError("Invalid email or password", status_code=401)
    return user
