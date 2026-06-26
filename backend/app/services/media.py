from __future__ import annotations

from collections.abc import Mapping
from io import BytesIO
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.media import CatalogMedia, CatalogMediaProcessingStatus
from app.services.storage import S3Storage

DERIVATIVE_SIZES = {
    "thumbnail": 240,
    "card": 640,
    "full": 1600,
}


async def primary_image_urls_by_variant(
    session: AsyncSession,
    *,
    variant_item_ids: Mapping[UUID, UUID],
) -> dict[UUID, str]:
    if not variant_item_ids:
        return {}

    storage = S3Storage(get_settings())
    variant_urls = await _primary_variant_image_urls(
        session,
        storage=storage,
        variant_ids=set(variant_item_ids),
    )
    missing_item_ids = {
        item_id
        for variant_id, item_id in variant_item_ids.items()
        if variant_id not in variant_urls
    }
    if not missing_item_ids:
        return variant_urls

    item_urls = await _primary_item_image_urls(
        session,
        storage=storage,
        item_ids=missing_item_ids,
    )
    for variant_id, item_id in variant_item_ids.items():
        if variant_id not in variant_urls and item_id in item_urls:
            variant_urls[variant_id] = item_urls[item_id]
    return variant_urls


async def _primary_variant_image_urls(
    session: AsyncSession,
    *,
    storage: S3Storage,
    variant_ids: set[UUID],
) -> dict[UUID, str]:
    result = await session.execute(
        select(CatalogMedia)
        .where(
            CatalogMedia.catalog_variant_id.in_(variant_ids),
            CatalogMedia.is_primary.is_(True),
            CatalogMedia.processing_status == CatalogMediaProcessingStatus.READY,
            CatalogMedia.deleted_at.is_(None),
        )
        .order_by(CatalogMedia.sort_order.asc(), CatalogMedia.created_at.asc())
    )
    urls: dict[UUID, str] = {}
    for media in result.scalars().all():
        if media.catalog_variant_id is not None and media.catalog_variant_id not in urls:
            urls[media.catalog_variant_id] = storage.public_url(_public_media_key(media))
    return urls


async def _primary_item_image_urls(
    session: AsyncSession,
    *,
    storage: S3Storage,
    item_ids: set[UUID],
) -> dict[UUID, str]:
    result = await session.execute(
        select(CatalogMedia)
        .where(
            CatalogMedia.catalog_item_id.in_(item_ids),
            CatalogMedia.catalog_variant_id.is_(None),
            CatalogMedia.is_primary.is_(True),
            CatalogMedia.processing_status == CatalogMediaProcessingStatus.READY,
            CatalogMedia.deleted_at.is_(None),
        )
        .order_by(CatalogMedia.sort_order.asc(), CatalogMedia.created_at.asc())
    )
    urls: dict[UUID, str] = {}
    for media in result.scalars().all():
        if media.catalog_item_id not in urls:
            urls[media.catalog_item_id] = storage.public_url(_public_media_key(media))
    return urls


async def process_catalog_media(media_id: UUID) -> None:
    settings = get_settings()
    storage = S3Storage(settings)
    async with SessionLocal() as session:
        try:
            async with session.begin():
                media = await session.get(CatalogMedia, media_id)
                if media is None or media.deleted_at is not None:
                    return
                media.processing_status = CatalogMediaProcessingStatus.PROCESSING
                media.processing_error = None

            original = storage.read_object(media.object_key)
            width, height, derivatives = _build_derivatives(
                original=original,
                object_key=media.object_key,
            )
            for key, body in derivatives.items():
                storage.write_object(
                    object_key=key,
                    body=body,
                    content_type="image/webp",
                )

            async with session.begin():
                media = await session.get(CatalogMedia, media_id)
                if media is None or media.deleted_at is not None:
                    return
                media.width = width
                media.height = height
                media.thumbnail_object_key = _derivative_key(media.object_key, "thumbnail")
                media.card_object_key = _derivative_key(media.object_key, "card")
                media.full_object_key = _derivative_key(media.object_key, "full")
                media.processing_status = CatalogMediaProcessingStatus.READY
                media.processing_error = None
                if media.is_primary:
                    await _unset_other_primary_for_ready_media(session, media)
        except Exception as exc:  # noqa: BLE001
            async with session.begin():
                media = await session.get(CatalogMedia, media_id)
                if media is None:
                    return
                media.processing_status = CatalogMediaProcessingStatus.FAILED
                media.processing_error = str(exc)[:2000]


async def _unset_other_primary_for_ready_media(
    session: AsyncSession,
    media: CatalogMedia,
) -> None:
    statement = select(CatalogMedia).where(
        CatalogMedia.id != media.id,
        CatalogMedia.catalog_item_id == media.catalog_item_id,
        CatalogMedia.catalog_variant_id == media.catalog_variant_id,
        CatalogMedia.is_primary.is_(True),
        CatalogMedia.processing_status == CatalogMediaProcessingStatus.READY,
    )
    result = await session.execute(statement)
    for other in result.scalars().all():
        other.is_primary = False


def _build_derivatives(*, original: bytes, object_key: str) -> tuple[int, int, dict[str, bytes]]:
    from PIL import Image, ImageOps  # type: ignore[import-not-found]

    Image.MAX_IMAGE_PIXELS = 40_000_000
    with Image.open(BytesIO(original)) as image:
        image.verify()

    with Image.open(BytesIO(original)) as image:
        transposed = ImageOps.exif_transpose(image)
        transposed.load()
        normalized = _without_exif(transposed)
        width, height = normalized.size
        derivatives = {
            _derivative_key(object_key, name): _render_webp(normalized, max_size)
            for name, max_size in DERIVATIVE_SIZES.items()
        }
    return width, height, derivatives


def _without_exif(image: Any) -> Any:
    if image.mode in {"RGBA", "LA"}:
        return image.copy()
    if image.mode != "RGB":
        return image.convert("RGB")
    return image.copy()


def _render_webp(image: Any, max_size: int) -> bytes:
    from PIL import Image

    derivative = image.copy()
    derivative.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    output = BytesIO()
    derivative.save(output, format="WEBP", quality=85, method=6)
    return output.getvalue()


def _derivative_key(object_key: str, name: str) -> str:
    return f"{object_key}.{name}.webp"


def _public_media_key(media: CatalogMedia) -> str:
    return (
        media.card_object_key
        or media.full_object_key
        or media.thumbnail_object_key
        or media.object_key
    )
