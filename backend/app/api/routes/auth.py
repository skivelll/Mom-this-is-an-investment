from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db_session
from app.models.user import User, UserRole
from app.schemas.auth import (
    TokenResponseSchema,
    UserLoginSchema,
    UserRegisterSchema,
    UserResponseSchema,
)

router = APIRouter(prefix="/auth", tags=["auth"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post(
    "/register",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    payload: UserRegisterSchema,
    session: DbSession,
) -> UserResponseSchema:
    email = payload.email.lower()
    username = payload.username.strip()
    existing_user = await session.scalar(
        select(User).where(or_(User.email == email, User.username == username)),
    )
    if existing_user is not None:
        raise ConflictError("User with this email or username already exists.")

    user = User(
        email=email,
        username=username,
        password_hash=hash_password(payload.password),
        role=UserRole.USER,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserResponseSchema.model_validate(user)


@router.post("/login", response_model=TokenResponseSchema)
async def login_user(
    payload: UserLoginSchema,
    session: DbSession,
) -> TokenResponseSchema:
    user = await session.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not user.is_active:
        raise UnauthorizedError("Invalid email or password.")
    if not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password.")

    return TokenResponseSchema(access_token=create_access_token(subject=str(user.id)))


@router.get("/me", response_model=UserResponseSchema)
async def get_me(current_user: CurrentUser) -> UserResponseSchema:
    return UserResponseSchema.model_validate(current_user)
