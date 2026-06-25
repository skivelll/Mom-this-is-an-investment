from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.collections import ItemCondition
from app.models.user import User, UserRole

pytestmark = pytest.mark.asyncio


async def test_owner_can_update_collection_item(
    client: AsyncClient,
    test_data: Any,
) -> None:
    token = await _login(client, email=test_data.user.email)

    response = await client.patch(
        f"/api/v1/collections/items/{test_data.collection_item.id}",
        headers=_auth(token),
        json={
            "condition": "opened",
            "quantity": 3,
            "purchase_price": "19.99",
            "purchase_currency": "USD",
            "purchase_date": "2026-01-02",
            "comment": "Updated comment",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["condition"] == "opened"
    assert payload["quantity"] == 3
    assert payload["purchase_price"] == "19.99"
    assert payload["purchase_currency"] == "USD"
    assert payload["purchase_date"] == "2026-01-02"
    assert payload["comment"] == "Updated comment"


async def test_other_user_cannot_update_collection_item(
    client: AsyncClient,
    db_session: AsyncSession,
    test_data: Any,
) -> None:
    suffix = uuid4().hex
    other = User(
        email=f"other-{suffix}@example.com",
        username=f"other-{suffix}",
        password_hash=hash_password("password123"),
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(other)
    await db_session.flush()
    token = await _login(client, email=other.email)

    response = await client.patch(
        f"/api/v1/collections/items/{test_data.collection_item.id}",
        headers=_auth(token),
        json={"quantity": 2},
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"quantity": 0}, "quantity"),
        ({"purchase_price": "-1.00"}, "purchase_price"),
        ({"purchase_currency": "usd"}, "purchase_currency"),
        ({"purchase_currency": "US1"}, "purchase_currency"),
    ],
)
async def test_invalid_collection_item_update_is_rejected(
    client: AsyncClient,
    test_data: Any,
    payload: dict[str, object],
    field: str,
) -> None:
    token = await _login(client, email=test_data.user.email)

    response = await client.patch(
        f"/api/v1/collections/items/{test_data.collection_item.id}",
        headers=_auth(token),
        json=payload,
    )

    assert response.status_code == 422
    assert field in response.text


async def test_partial_patch_does_not_clear_other_fields(
    client: AsyncClient,
    db_session: AsyncSession,
    test_data: Any,
) -> None:
    test_data.collection_item.condition = ItemCondition.NEW
    test_data.collection_item.quantity = 1
    test_data.collection_item.purchase_price = Decimal("12.50")
    test_data.collection_item.purchase_currency = "USD"
    test_data.collection_item.comment = "Keep me"
    await db_session.flush()
    token = await _login(client, email=test_data.user.email)

    response = await client.patch(
        f"/api/v1/collections/items/{test_data.collection_item.id}",
        headers=_auth(token),
        json={"quantity": 4},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["quantity"] == 4
    assert payload["condition"] == "new"
    assert payload["purchase_price"] == "12.50"
    assert payload["purchase_currency"] == "USD"
    assert payload["comment"] == "Keep me"


async def test_empty_patch_returns_current_item(
    client: AsyncClient,
    test_data: Any,
) -> None:
    token = await _login(client, email=test_data.user.email)

    response = await client.patch(
        f"/api/v1/collections/items/{test_data.collection_item.id}",
        headers=_auth(token),
        json={},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(test_data.collection_item.id)


async def test_missing_collection_item_returns_404(
    client: AsyncClient,
    test_data: Any,
) -> None:
    token = await _login(client, email=test_data.user.email)

    response = await client.patch(
        f"/api/v1/collections/items/{uuid4()}",
        headers=_auth(token),
        json={"quantity": 2},
    )

    assert response.status_code == 404


async def test_collection_contents_return_user_facing_item_titles(
    client: AsyncClient,
    test_data: Any,
) -> None:
    token = await _login(client, email=test_data.user.email)

    response = await client.get(
        "/api/v1/collections/items",
        headers=_auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["collection_name"] == test_data.collection.name
    assert payload[0]["item_title"] == test_data.catalog_item.canonical_title
    assert payload[0]["variant_title"] == test_data.catalog_variant.canonical_title
    assert payload[0]["variant_label"] == test_data.catalog_variant.canonical_title


async def test_tests_use_test_database(db_session: AsyncSession) -> None:
    database_name = await db_session.scalar(text("select current_database()"))
    assert database_name is not None
    assert "test" in database_name


async def _login(client: AsyncClient, *, email: str, password: str = "password123") -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
