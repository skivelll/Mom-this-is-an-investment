from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.category import Category
from app.models.user import User, UserRole
from app.models.wishlist import WishlistItem, WishlistStatus

pytestmark = pytest.mark.asyncio


async def test_user_request_approve_relinks_wishlist(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    suffix = uuid4().hex
    password = "password123"

    user = User(
        email=f"user-{suffix}@example.com",
        username=f"user-{suffix}",
        password_hash=hash_password(password),
        role=UserRole.USER,
        is_active=True,
    )
    senior = User(
        email=f"senior-{suffix}@example.com",
        username=f"senior-{suffix}",
        password_hash=hash_password(password),
        role=UserRole.SENIOR_MODERATOR,
        is_active=True,
    )
    category = Category(
        name=f"Figures {suffix}",
        slug=f"figures-{suffix}",
        description="Test figures category",
        is_active=True,
    )
    db_session.add_all([user, senior, category])
    await db_session.commit()

    user_token = await _login(client, email=user.email, password=password)
    senior_token = await _login(client, email=senior.email, password=password)

    create_response = await client.post(
        "/api/v1/catalog-requests",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "category_id": str(category.id),
            "raw_title": "Funko Pop Spider-Man #79 Metallic",
            "description": "Please add this missing variant.",
            "wishlist": {
                "target_price": "25.00",
                "currency": "USD",
                "priority": 10,
                "comment": "Need it for the shelf.",
            },
        },
    )
    assert create_response.status_code == 201
    created_payload = create_response.json()
    request_id = created_payload["request"]["id"]
    wishlist_id = created_payload["wishlist_item"]["id"]
    assert created_payload["request"]["status"] == "pending"
    assert created_payload["wishlist_item"]["status"] == "pending_moderation"
    assert created_payload["wishlist_item"]["catalog_request_id"] == request_id
    assert created_payload["wishlist_item"]["catalog_variant_id"] is None
    pending_wishlist_response = await client.get(
        "/api/v1/wishlist/detailed",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert pending_wishlist_response.status_code == 200
    pending_wishlist = pending_wishlist_response.json()
    assert pending_wishlist[0]["item_title"] == "Funko Pop Spider-Man #79 Metallic"
    assert pending_wishlist[0]["status"] == "pending_moderation"

    approve_response = await client.post(
        f"/api/v1/moderation/catalog-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {senior_token}"},
        json={
            "new_catalog_item": {
                "category_id": str(category.id),
                "canonical_title": "Funko Pop Spider-Man #79",
                "normalized_title": "funko pop spider man 79",
                "description": "Spider-Man collectible figure.",
            },
            "new_variant": {
                "canonical_title": "Funko Pop Spider-Man #79 Metallic",
                "normalized_title": "funko pop spider man 79 metallic",
                "sku": f"SMOKE-{suffix}",
            },
            "comment": "Approved from integration test.",
        },
    )
    assert approve_response.status_code == 200
    approved_payload = approve_response.json()
    assert approved_payload["status"] == "approved"
    assert approved_payload["approved_catalog_item_id"] is not None
    assert approved_payload["approved_variant_id"] is not None

    wishlist = await db_session.scalar(select(WishlistItem).where(WishlistItem.id == wishlist_id))
    assert wishlist is not None
    assert wishlist.catalog_request_id is None
    assert str(wishlist.catalog_variant_id) == approved_payload["approved_variant_id"]
    assert wishlist.status == WishlistStatus.ACTIVE

    active_wishlist_response = await client.get(
        "/api/v1/wishlist/detailed",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert active_wishlist_response.status_code == 200
    active_wishlist = active_wishlist_response.json()
    assert active_wishlist[0]["item_title"] == "Funko Pop Spider-Man #79"
    assert active_wishlist[0]["variant_label"] == "Funko Pop Spider-Man #79 Metallic"
    assert active_wishlist[0]["catalog_request_id"] is None
    assert active_wishlist[0]["catalog_variant_id"] == approved_payload["approved_variant_id"]


async def test_register_login_and_me(client: AsyncClient) -> None:
    suffix = uuid4().hex

    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"new-user-{suffix}@example.com",
            "username": f"new-user-{suffix}",
            "password": "password123",
        },
    )
    assert register_response.status_code == 201
    assert register_response.json()["role"] == "user"

    token = await _login(
        client,
        email=f"new-user-{suffix}@example.com",
        password="password123",
    )
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == f"new-user-{suffix}@example.com"


async def _login(client: AsyncClient, *, email: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    return str(payload["access_token"])
