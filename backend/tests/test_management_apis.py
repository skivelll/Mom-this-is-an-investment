from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole

pytestmark = pytest.mark.asyncio


async def test_admin_collection_and_wishlist_apis(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    suffix = uuid4().hex
    password = "password123"

    admin = User(
        email=f"admin-{suffix}@example.com",
        username=f"admin-{suffix}",
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
        is_active=True,
    )
    senior = User(
        email=f"senior-mgmt-{suffix}@example.com",
        username=f"senior-mgmt-{suffix}",
        password_hash=hash_password(password),
        role=UserRole.SENIOR_MODERATOR,
        is_active=True,
    )
    user = User(
        email=f"collector-{suffix}@example.com",
        username=f"collector-{suffix}",
        password_hash=hash_password(password),
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add_all([admin, senior, user])
    await db_session.commit()

    admin_token = await _login(client, email=admin.email, password=password)
    senior_token = await _login(client, email=senior.email, password=password)
    user_token = await _login(client, email=user.email, password=password)

    category_response = await client.post(
        "/api/v1/admin/categories",
        headers=_auth(admin_token),
        json={
            "name": f"Test Figures {suffix}",
            "slug": f"test-figures-{suffix}",
            "description": "Test category",
        },
    )
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    attribute_response = await client.post(
        "/api/v1/admin/attributes",
        headers=_auth(admin_token),
        json={
            "category_id": category_id,
            "code": f"variant_{suffix[:8]}",
            "name": "Variant",
            "value_type": "text",
            "is_variant_attribute": True,
        },
    )
    assert attribute_response.status_code == 201

    reference_response = await client.post(
        "/api/v1/admin/references",
        headers=_auth(admin_token),
        json={
            "type": "manufacturer",
            "canonical_name": f"Maker {suffix}",
            "normalized_name": f"maker {suffix}",
        },
    )
    assert reference_response.status_code == 201

    item_response = await client.post(
        "/api/v1/catalog/items",
        headers=_auth(senior_token),
        json={
            "category_id": category_id,
            "canonical_title": f"Test Figure {suffix}",
            "normalized_title": f"test figure {suffix}",
        },
    )
    assert item_response.status_code == 201
    item_id = item_response.json()["id"]

    variant_response = await client.post(
        "/api/v1/catalog/variants",
        headers=_auth(senior_token),
        json={
            "catalog_item_id": item_id,
            "canonical_title": f"Test Figure {suffix} Regular",
            "normalized_title": f"test figure {suffix} regular",
            "sku": f"MGMT-{suffix}",
        },
    )
    assert variant_response.status_code == 201
    variant_id = variant_response.json()["id"]

    collection_response = await client.post(
        "/api/v1/collections",
        headers=_auth(user_token),
        json={"name": f"My shelf {suffix}", "visibility": "private"},
    )
    assert collection_response.status_code == 201
    collection_id = collection_response.json()["id"]

    collection_item_response = await client.post(
        f"/api/v1/collections/{collection_id}/items",
        headers=_auth(user_token),
        json={
            "catalog_variant_id": variant_id,
            "condition": "new",
            "quantity": 1,
            "purchase_price": "19.99",
            "purchase_currency": "USD",
        },
    )
    assert collection_item_response.status_code == 201
    assert collection_item_response.json()["catalog_variant_id"] == variant_id

    wishlist_response = await client.post(
        "/api/v1/wishlist",
        headers=_auth(user_token),
        json={
            "catalog_variant_id": variant_id,
            "priority": 5,
            "target_price": "15.00",
            "currency": "USD",
        },
    )
    assert wishlist_response.status_code == 201
    assert wishlist_response.json()["status"] == "active"

    list_collections_response = await client.get(
        "/api/v1/collections",
        headers=_auth(user_token),
    )
    assert list_collections_response.status_code == 200
    assert any(item["id"] == collection_id for item in list_collections_response.json())


async def _login(client: AsyncClient, *, email: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
