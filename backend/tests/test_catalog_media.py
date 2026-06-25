from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import CatalogItem
from app.models.media import CatalogMedia
from app.models.user import User
from app.models.variant import CatalogVariant

pytestmark = pytest.mark.asyncio


async def test_catalog_media_requires_moderator_role(
    client: AsyncClient,
    user: User,
    catalog_item: CatalogItem,
) -> None:
    token = await _login(client, email=user.email, password="password123")

    response = await client.post(
        "/api/v1/media/catalog",
        headers=_auth(token),
        json={
            "catalog_item_id": str(catalog_item.id),
            "object_key": f"catalog/{uuid4().hex}.jpg",
            "original_filename": "cover.jpg",
            "mime_type": "image/jpeg",
            "size_bytes": 100,
        },
    )

    assert response.status_code == 403


async def test_catalog_media_primary_fallback_and_soft_delete(
    client: AsyncClient,
    db_session: AsyncSession,
    senior_moderator: User,
    catalog_item: CatalogItem,
    catalog_variant: CatalogVariant,
) -> None:
    token = await _login(client, email=senior_moderator.email, password="password123")
    item_object_key = f"catalog/{uuid4().hex}.jpg"
    variant_object_key = f"catalog/{uuid4().hex}.webp"

    item_media_response = await client.post(
        "/api/v1/media/catalog",
        headers=_auth(token),
        json={
            "catalog_item_id": str(catalog_item.id),
            "object_key": item_object_key,
            "original_filename": "item-cover.jpg",
            "mime_type": "image/jpeg",
            "size_bytes": 100,
            "is_primary": True,
        },
    )
    assert item_media_response.status_code == 201
    item_media_id = item_media_response.json()["id"]

    variant_response_with_fallback = await client.get(
        f"/api/v1/catalog/variants/{catalog_variant.id}",
    )
    assert variant_response_with_fallback.status_code == 200
    assert variant_response_with_fallback.json()["primary_image_url"].endswith(item_object_key)

    variant_media_response = await client.post(
        "/api/v1/media/catalog",
        headers=_auth(token),
        json={
            "catalog_item_id": str(catalog_item.id),
            "catalog_variant_id": str(catalog_variant.id),
            "object_key": variant_object_key,
            "original_filename": "variant-cover.webp",
            "mime_type": "image/webp",
            "size_bytes": 200,
            "is_primary": True,
        },
    )
    assert variant_media_response.status_code == 201
    variant_media_id = variant_media_response.json()["id"]

    variant_response_with_override = await client.get(
        f"/api/v1/catalog/variants/{catalog_variant.id}",
    )
    assert variant_response_with_override.status_code == 200
    assert variant_response_with_override.json()["primary_image_url"].endswith(variant_object_key)

    delete_response = await client.delete(
        f"/api/v1/media/catalog/{variant_media_id}",
        headers=_auth(token),
    )
    assert delete_response.status_code == 204

    deleted_media = await db_session.scalar(
        select(CatalogMedia).where(CatalogMedia.id == variant_media_id)
    )
    assert deleted_media is not None
    assert deleted_media.deleted_at is not None

    list_response = await client.get(
        "/api/v1/media/catalog",
        params={"catalog_item_id": str(catalog_item.id)},
    )
    assert list_response.status_code == 200
    listed_ids = {media["id"] for media in list_response.json()}
    assert item_media_id in listed_ids
    assert variant_media_id not in listed_ids


async def _login(client: AsyncClient, *, email: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
