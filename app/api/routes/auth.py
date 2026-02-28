"""Authentication routes — login, token refresh."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.auth import PasswordHasher, Role, TokenManager

router = APIRouter()

_settings = get_settings()
# In-memory user store (will be replaced by DB in production)
_password_hasher = PasswordHasher(secret_key=_settings.auth_secret_key or "dev-only-secret")
_token_manager = TokenManager(secret_key=_settings.jwt_secret_key or "dev-only-jwt-secret")


class LoginRequest(BaseModel):
    """Login credentials."""

    email: str
    password: str
    workspace_id: str = Field(default="default")


class TokenResponse(BaseModel):
    """Access + refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Refresh token exchange."""

    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    """Authenticate user and return JWT tokens.

    NOTE: This is a stub. In production, validate against DB.
    """
    # Stub: accept any credentials in dev mode
    # Real implementation will query UserModel from DB
    access = _token_manager.create_access_token(
        user_id=request.email,
        workspace_id=request.workspace_id,
        role=Role.EDITOR,
    )
    refresh = _token_manager.create_refresh_token(
        user_id=request.email,
        workspace_id=request.workspace_id,
        role=Role.EDITOR,
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest) -> TokenResponse:
    """Exchange a refresh token for a new access token."""
    payload = _token_manager.verify_token(request.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    if payload.token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expected a refresh token",
        )

    access = _token_manager.create_access_token(
        user_id=payload.user_id,
        workspace_id=payload.workspace_id,
        role=payload.role,
    )
    refresh = _token_manager.create_refresh_token(
        user_id=payload.user_id,
        workspace_id=payload.workspace_id,
        role=payload.role,
    )
    return TokenResponse(access_token=access, refresh_token=refresh)
