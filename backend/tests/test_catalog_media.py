from __future__ import annotations

from io import BytesIO
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import CatalogItem
from app.models.media import CatalogMedia, CatalogMediaProcessingStatus
from app.models.user import User
from app.models.variant import CatalogVariant
from app.services.media import _build_derivatives

pytestmark = pytest.mark.asyncio


def test_media_derivatives_are_webp_and_do_not_upscale() -> None:
    from PIL import Image  # type: ignore[import-not-found]

    source = BytesIO()
    Image.new("RGB", (32, 16), color=(255, 0, 0)).save(source, format="PNG")

    width, height, derivatives = _build_derivatives(
        original=source.getvalue(),
        object_key="catalog/test.png",
    )

    assert (width, height) == (32, 16)
    assert set(derivatives) == {
        "catalog/test.png.thumbnail.webp",
        "catalog/test.png.card.webp",
        "catalog/test.png.full.webp",
    }
    for body in derivatives.values():
        with Image.open(BytesIO(body)) as derivative:
            assert derivative.format == "WEBP"
            assert derivative.size == (32, 16)


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
    monkeypatch: pytest.MonkeyPatch,
    senior_moderator: User,
    catalog_item: CatalogItem,
    catalog_variant: CatalogVariant,
) -> None:
    _disable_media_processing(monkeypatch)
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
    await _mark_ready(db_session, item_media_id)

    variant_response_with_fallback = await client.get(
        f"/api/v1/catalog/variants/{catalog_variant.id}",
    )
    assert variant_response_with_fallback.status_code == 200
    assert variant_response_with_fallback.json()["primary_image_url"].endswith(
        f"{item_object_key}.card.webp"
    )

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
    await _mark_ready(db_session, variant_media_id)

    variant_response_with_override = await client.get(
        f"/api/v1/catalog/variants/{catalog_variant.id}",
    )
    assert variant_response_with_override.status_code == 200
    assert variant_response_with_override.json()["primary_image_url"].endswith(
        f"{variant_object_key}.card.webp"
    )

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


async def test_catalog_media_auto_primary_and_promotes_next_on_delete(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    senior_moderator: User,
    catalog_item: CatalogItem,
) -> None:
    _disable_media_processing(monkeypatch)
    token = await _login(client, email=senior_moderator.email, password="password123")
    first_key = f"catalog/{uuid4().hex}.jpg"
    second_key = f"catalog/{uuid4().hex}.png"

    first_response = await client.post(
        "/api/v1/media/catalog",
        headers=_auth(token),
        json={
            "catalog_item_id": str(catalog_item.id),
            "object_key": first_key,
            "original_filename": "first.jpg",
            "mime_type": "image/jpeg",
            "size_bytes": 100,
        },
    )
    assert first_response.status_code == 201
    assert first_response.json()["is_primary"] is True
    first_id = first_response.json()["id"]
    await _mark_ready(db_session, first_id)

    second_response = await client.post(
        "/api/v1/media/catalog",
        headers=_auth(token),
        json={
            "catalog_item_id": str(catalog_item.id),
            "object_key": second_key,
            "original_filename": "second.png",
            "mime_type": "image/png",
            "size_bytes": 100,
            "sort_order": 2,
        },
    )
    assert second_response.status_code == 201
    assert second_response.json()["is_primary"] is False
    second_id = second_response.json()["id"]
    await _mark_ready(db_session, second_id)

    delete_response = await client.delete(
        f"/api/v1/media/catalog/{first_id}",
        headers=_auth(token),
    )
    assert delete_response.status_code == 204

    second_media = await db_session.scalar(select(CatalogMedia).where(CatalogMedia.id == second_id))
    assert second_media is not None
    assert second_media.is_primary is True
    assert second_media.processing_status == CatalogMediaProcessingStatus.READY


async def test_catalog_media_confirm_starts_pending_processing(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    senior_moderator: User,
    catalog_item: CatalogItem,
) -> None:
    called: list[str] = []

    async def fake_process(media_id: object) -> None:
        called.append(str(media_id))

    monkeypatch.setattr("app.api.routes.media.process_catalog_media", fake_process)
    token = await _login(client, email=senior_moderator.email, password="password123")
    response = await client.post(
        "/api/v1/media/catalog",
        headers=_auth(token),
        json={
            "catalog_item_id": str(catalog_item.id),
            "object_key": f"catalog/{uuid4().hex}.png",
            "original_filename": "processing.png",
            "mime_type": "image/png",
            "size_bytes": 100,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["processing_status"] == "pending"
    assert payload["thumbnail_object_key"] is None
    assert called == [payload["id"]]


async def _login(client: AsyncClient, *, email: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _disable_media_processing(monkeypatch: pytest.MonkeyPatch) -> None:
    async def noop(media_id: object) -> None:
        _ = media_id

    monkeypatch.setattr("app.api.routes.media.process_catalog_media", noop)


async def _mark_ready(db_session: AsyncSession, media_id: str) -> None:
    media = await db_session.get(CatalogMedia, UUID(media_id))
    assert media is not None
    media.processing_status = CatalogMediaProcessingStatus.READY
    media.card_object_key = f"{media.object_key}.card.webp"
    await db_session.flush()
