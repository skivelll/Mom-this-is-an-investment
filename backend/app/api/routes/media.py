from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.db.session import get_db_session
from app.models.media import CatalogMedia, CatalogMediaType
from app.models.user import User, UserRole
from app.schemas.media import (
    CatalogMediaConfirmSchema,
    CatalogMediaResponseSchema,
    CatalogMediaUpdateSchema,
    CatalogMediaUploadRequestSchema,
    CatalogMediaUploadResponseSchema,
)
from app.services.storage import S3Storage

router = APIRouter(prefix="/media/catalog", tags=["catalog media"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]

MEDIA_MANAGER_ROLES = {UserRole.MODERATOR, UserRole.SENIOR_MODERATOR, UserRole.ADMIN}


@router.post("/upload-url", response_model=CatalogMediaUploadResponseSchema)
async def create_catalog_media_upload_url(
    payload: CatalogMediaUploadRequestSchema,
    current_user: CurrentUser,
) -> CatalogMediaUploadResponseSchema:
    _ensure_media_manager(current_user)
    storage = S3Storage(get_settings())
    try:
        upload = storage.create_presigned_upload(
            original_filename=payload.original_filename,
            mime_type=payload.mime_type,
            size_bytes=payload.size_bytes,
        )
    except ValueError as exc:
        raise BadRequestError(str(exc)) from exc
    return CatalogMediaUploadResponseSchema(
        object_key=upload.object_key,
        upload_url=upload.upload_url,
        public_url=upload.public_url,
        headers=upload.headers,
        expires_in=upload.expires_in,
    )


@router.post("", response_model=CatalogMediaResponseSchema, status_code=status.HTTP_201_CREATED)
async def confirm_catalog_media_upload(
    payload: CatalogMediaConfirmSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CatalogMediaResponseSchema:
    _ensure_media_manager(current_user)
    settings = get_settings()
    if payload.mime_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise BadRequestError("Unsupported media type.")
    if payload.size_bytes > settings.media_max_upload_size_bytes:
        raise BadRequestError("File is too large.")

    async with session.begin():
        media = CatalogMedia(
            catalog_item_id=payload.catalog_item_id,
            catalog_variant_id=payload.catalog_variant_id,
            object_key=payload.object_key,
            original_filename=payload.original_filename,
            mime_type=payload.mime_type,
            size_bytes=payload.size_bytes,
            width=payload.width,
            height=payload.height,
            media_type=CatalogMediaType.IMAGE,
            is_primary=payload.is_primary,
            sort_order=payload.sort_order,
            alt_text=payload.alt_text,
        )
        session.add(media)
        await session.flush()
        if media.is_primary:
            await _unset_other_primary(session, media)

    await session.refresh(media)
    return _media_response(media)


@router.get("", response_model=list[CatalogMediaResponseSchema])
async def list_catalog_media(
    session: DbSession,
    catalog_item_id: Annotated[UUID | None, Query()] = None,
    catalog_variant_id: Annotated[UUID | None, Query()] = None,
) -> list[CatalogMediaResponseSchema]:
    statement = (
        select(CatalogMedia)
        .where(CatalogMedia.deleted_at.is_(None))
        .order_by(
            CatalogMedia.is_primary.desc(),
            CatalogMedia.sort_order.asc(),
            CatalogMedia.created_at.asc(),
        )
    )
    if catalog_item_id is not None:
        statement = statement.where(CatalogMedia.catalog_item_id == catalog_item_id)
    if catalog_variant_id is not None:
        statement = statement.where(CatalogMedia.catalog_variant_id == catalog_variant_id)
    result = await session.execute(statement)
    return [_media_response(media) for media in result.scalars().all()]


@router.patch("/{media_id}", response_model=CatalogMediaResponseSchema)
async def update_catalog_media(
    media_id: UUID,
    payload: CatalogMediaUpdateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CatalogMediaResponseSchema:
    _ensure_media_manager(current_user)
    async with session.begin():
        media = await session.get(CatalogMedia, media_id)
        if media is None or media.deleted_at is not None:
            raise NotFoundError("Catalog media was not found.")
        if payload.sort_order is not None:
            media.sort_order = payload.sort_order
        if payload.alt_text is not None:
            media.alt_text = payload.alt_text
        if payload.is_primary is not None:
            media.is_primary = payload.is_primary
            if media.is_primary:
                await _unset_other_primary(session, media)
        await session.flush()
    await session.refresh(media)
    return _media_response(media)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_catalog_media(
    media_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> Response:
    _ensure_media_manager(current_user)
    async with session.begin():
        media = await session.get(CatalogMedia, media_id)
        if media is None or media.deleted_at is not None:
            raise NotFoundError("Catalog media was not found.")
        media.deleted_at = datetime.now(UTC)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _unset_other_primary(session: AsyncSession, media: CatalogMedia) -> None:
    statement = select(CatalogMedia).where(
        CatalogMedia.id != media.id,
        CatalogMedia.catalog_item_id == media.catalog_item_id,
        CatalogMedia.catalog_variant_id == media.catalog_variant_id,
        CatalogMedia.is_primary.is_(True),
    )
    result = await session.execute(statement)
    for other in result.scalars().all():
        other.is_primary = False


def _media_response(media: CatalogMedia) -> CatalogMediaResponseSchema:
    return CatalogMediaResponseSchema(
        id=media.id,
        catalog_item_id=media.catalog_item_id,
        catalog_variant_id=media.catalog_variant_id,
        object_key=media.object_key,
        url=S3Storage(get_settings()).public_url(media.object_key),
        original_filename=media.original_filename,
        mime_type=media.mime_type,
        size_bytes=media.size_bytes,
        width=media.width,
        height=media.height,
        media_type=media.media_type,
        is_primary=media.is_primary,
        sort_order=media.sort_order,
        alt_text=media.alt_text,
        created_at=media.created_at,
        updated_at=media.updated_at,
    )


def _ensure_media_manager(user: User) -> None:
    if not user.is_active or user.role not in MEDIA_MANAGER_ROLES:
        raise ForbiddenError("Moderator permissions are required.")
