"""
finLine Authentication API

JWT-based authentication with bcrypt password hashing.
Ported and simplified from finForge.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from config import get_settings
from database import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_last_login,
)
from models.schemas import UserCreate, UserResponse, Token

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ============================================================
# Password Utilities
# ============================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    hash_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hash_bytes)


# ============================================================
# JWT Utilities
# ============================================================

def create_access_token(user_id: str, email: str) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================
# Dependencies
# ============================================================

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """Get current authenticated user from token."""
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    return user


# Type alias for dependency injection
CurrentUser = Annotated[dict, Depends(get_current_user)]


# ============================================================
# Endpoints
# ============================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    logger.info(f"Registration attempt for email: {user_data.email}")

    # Check if user exists
    existing = await get_user_by_email(user_data.email)
    if existing:
        logger.warning(f"Registration failed - email already exists: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user_id = str(uuid4())
    password_hash = hash_password(user_data.password)

    user = await create_user(user_id, user_data.email, password_hash)
    logger.info(f"User registered successfully: {user_data.email}")

    return UserResponse(
        id=user["id"],
        email=user["email"],
        is_active=True,
        created_at=user["created_at"],
        last_login=None
    )


@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Login and get access token."""
    logger.info(f"Login attempt for email: {form_data.username}")

    user = await get_user_by_email(form_data.username)
    if not user:
        logger.warning(f"Login failed - user not found: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user["password_hash"]):
        logger.warning(f"Login failed - invalid password: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        logger.warning(f"Login failed - account disabled: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )

    # Update last login
    await update_user_last_login(user["id"])

    # Generate tokens
    access_token = create_access_token(user["id"], user["email"])
    refresh_token = create_refresh_token(user["id"])

    logger.info(f"Login successful: {form_data.username}")
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Get current user info."""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        is_active=current_user.get("is_active", True),
        created_at=current_user["created_at"],
        last_login=current_user.get("last_login")
    )


class RefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshRequest):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = create_access_token(user["id"], user["email"])
    new_refresh_token = create_refresh_token(user["id"])

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )
