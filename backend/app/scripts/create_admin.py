from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole

DEFAULT_ADMIN_USERNAME = "admin"


@dataclass(slots=True)
class CreateAdminResult:
    action: str
    user: User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def ensure_admin_user(
    session: AsyncSession,
    *,
    email: str,
    username: str,
    password: str,
    update_existing: bool = True,
) -> CreateAdminResult:
    user = await get_user_by_email(session, email)

    if user is None:
        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return CreateAdminResult(action="created", user=user)

    if not update_existing:
        return CreateAdminResult(action="exists", user=user)

    user.username = username
    user.password_hash = hash_password(password)
    user.role = UserRole.ADMIN
    user.is_active = True

    await session.commit()
    await session.refresh(user)
    return CreateAdminResult(action="updated", user=user)


async def ensure_startup_admin_user(
    *,
    session_maker: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> CreateAdminResult | None:
    email = settings.bootstrap_admin_email.strip().lower()
    password = settings.bootstrap_admin_password
    if not email:
        raise ValueError("BOOTSTRAP_ADMIN_EMAIL must not be empty.")
    if not password:
        raise ValueError("BOOTSTRAP_ADMIN_PASSWORD must not be empty.")

    async with session_maker() as session:
        return await ensure_admin_user(
            session,
            email=email,
            username=DEFAULT_ADMIN_USERNAME,
            password=password,
            update_existing=False,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or update an admin user for Mom-this-is-an-investment.",
    )
    parser.add_argument("--email", default="admin@example.com")
    parser.add_argument("--username", default=DEFAULT_ADMIN_USERNAME)
    parser.add_argument("--password", default="admin")
    return parser.parse_args()


async def _async_main() -> int:
    get_settings()
    args = parse_args()
    async with SessionLocal() as session:
        result = await ensure_admin_user(
            session,
            email=args.email.strip().lower(),
            username=args.username.strip(),
            password=args.password,
        )

    print(
        f"Admin user {result.action}: email={result.user.email} username={result.user.username}",
    )
    return 0


def main() -> int:
    return asyncio.run(_async_main())


if __name__ == "__main__":
    raise SystemExit(main())
