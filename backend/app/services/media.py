from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.media import CatalogMedia
from app.services.storage import S3Storage


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
            CatalogMedia.deleted_at.is_(None),
        )
        .order_by(CatalogMedia.sort_order.asc(), CatalogMedia.created_at.asc())
    )
    urls: dict[UUID, str] = {}
    for media in result.scalars().all():
        if media.catalog_variant_id is not None and media.catalog_variant_id not in urls:
            urls[media.catalog_variant_id] = storage.public_url(media.object_key)
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
            CatalogMedia.deleted_at.is_(None),
        )
        .order_by(CatalogMedia.sort_order.asc(), CatalogMedia.created_at.asc())
    )
    urls: dict[UUID, str] = {}
    for media in result.scalars().all():
        if media.catalog_item_id not in urls:
            urls[media.catalog_item_id] = storage.public_url(media.object_key)
    return urls
