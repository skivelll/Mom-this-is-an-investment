from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.action import ModerationAction, ModerationActionType
from app.models.item import CatalogItem, CatalogStatus
from app.models.request import CatalogRequest, CatalogRequestStatus
from app.models.user import User, UserRole
from app.models.variant import CatalogVariant
from app.models.wishlist import WishlistItem, WishlistStatus
from app.repositories.catalog import CatalogItemRepository, CatalogVariantRepository
from app.repositories.moderation import (
    CatalogRequestRepository,
    ModerationActionRepository,
)
from app.repositories.wishlist import WishlistRepository

MODERATION_ROLES = {
    UserRole.MODERATOR,
    UserRole.SENIOR_MODERATOR,
    UserRole.ADMIN,
}
SENIOR_MODERATION_ROLES = {
    UserRole.SENIOR_MODERATOR,
    UserRole.ADMIN,
}
PROCESSABLE_REQUEST_STATUSES = {
    CatalogRequestStatus.PENDING,
    CatalogRequestStatus.IN_REVIEW,
    CatalogRequestStatus.NEEDS_INFORMATION,
}


@dataclass(slots=True)
class WishlistDraft:
    target_price: Decimal | None = None
    currency: str | None = None
    source_url: str | None = None
    priority: int = 0
    comment: str | None = None


@dataclass(slots=True)
class CreateCatalogRequestCommand:
    category_id: UUID
    raw_title: str
    description: str | None = None
    source_url: str | None = None
    proposed_data: dict[str, Any] | None = None
    wishlist: WishlistDraft | None = None


@dataclass(slots=True)
class CreatedCatalogRequest:
    request: CatalogRequest
    wishlist_item: WishlistItem | None


@dataclass(slots=True)
class CatalogItemDraft:
    category_id: UUID
    canonical_title: str
    normalized_title: str
    description: str | None = None
    release_year: int | None = None
    status: CatalogStatus = CatalogStatus.ACTIVE


@dataclass(slots=True)
class CatalogVariantDraft:
    canonical_title: str
    normalized_title: str
    sku: str | None = None
    barcode: str | None = None
    release_date: date | None = None
    status: CatalogStatus = CatalogStatus.ACTIVE


@dataclass(slots=True)
class ApproveCatalogRequestCommand:
    request_id: UUID
    existing_catalog_item_id: UUID | None = None
    existing_variant_id: UUID | None = None
    new_catalog_item: CatalogItemDraft | None = None
    new_variant: CatalogVariantDraft | None = None
    comment: str | None = None
    payload: dict[str, Any] | None = None


@dataclass(slots=True)
class RejectCatalogRequestCommand:
    request_id: UUID
    reason: str
    comment: str | None = None
    payload: dict[str, Any] | None = None


@dataclass(slots=True)
class MarkDuplicateCatalogRequestCommand:
    request_id: UUID
    existing_variant_id: UUID
    comment: str | None = None
    payload: dict[str, Any] | None = None


class CatalogRequestService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._requests = CatalogRequestRepository(session)
        self._actions = ModerationActionRepository(session)
        self._wishlist = WishlistRepository(session)
        self._items = CatalogItemRepository(session)
        self._variants = CatalogVariantRepository(session)

    async def create_request(
        self,
        *,
        user: User,
        command: CreateCatalogRequestCommand,
    ) -> CreatedCatalogRequest:
        if not user.is_active:
            raise ForbiddenError("Inactive users cannot create catalog requests.")

        async with self._session.begin():
            request = await self._requests.create(
                CatalogRequest(
                    created_by_id=user.id,
                    category_id=command.category_id,
                    raw_title=command.raw_title,
                    description=command.description,
                    source_url=command.source_url,
                    proposed_data=command.proposed_data,
                    status=CatalogRequestStatus.PENDING,
                ),
            )

            wishlist_item: WishlistItem | None = None
            if command.wishlist is not None:
                wishlist_item = await self._wishlist.create(
                    WishlistItem(
                        user_id=user.id,
                        catalog_variant_id=None,
                        catalog_request_id=request.id,
                        target_price=command.wishlist.target_price,
                        currency=command.wishlist.currency,
                        source_url=command.wishlist.source_url,
                        priority=command.wishlist.priority,
                        status=WishlistStatus.PENDING_MODERATION,
                        comment=command.wishlist.comment,
                    ),
                )

        return CreatedCatalogRequest(request=request, wishlist_item=wishlist_item)

    async def approve_request(
        self,
        *,
        moderator: User,
        command: ApproveCatalogRequestCommand,
    ) -> CatalogRequest:
        self._ensure_senior_moderator(moderator)

        async with self._session.begin():
            request = await self._get_processable_request_for_update(command.request_id)
            item, variant = await self._resolve_approval_target(
                moderator=moderator,
                command=command,
            )

            request.status = CatalogRequestStatus.APPROVED
            request.approved_catalog_item_id = item.id
            request.approved_variant_id = variant.id
            request.moderated_by_id = moderator.id
            request.rejection_reason = None

            await self._actions.create(
                ModerationAction(
                    request_id=request.id,
                    moderator_id=moderator.id,
                    action=ModerationActionType.APPROVE,
                    comment=command.comment,
                    payload=command.payload,
                ),
            )
            await self._wishlist.relink_request_items_to_variant(
                request_id=request.id,
                variant_id=variant.id,
            )

        return request

    async def reject_request(
        self,
        *,
        moderator: User,
        command: RejectCatalogRequestCommand,
    ) -> CatalogRequest:
        self._ensure_moderator(moderator)

        async with self._session.begin():
            request = await self._get_processable_request_for_update(command.request_id)
            request.status = CatalogRequestStatus.REJECTED
            request.rejection_reason = command.reason
            request.moderated_by_id = moderator.id

            await self._actions.create(
                ModerationAction(
                    request_id=request.id,
                    moderator_id=moderator.id,
                    action=ModerationActionType.REJECT,
                    comment=command.comment,
                    payload=command.payload,
                ),
            )
            await self._wishlist.reject_request_items(request.id)

        return request

    async def mark_duplicate(
        self,
        *,
        moderator: User,
        command: MarkDuplicateCatalogRequestCommand,
    ) -> CatalogRequest:
        self._ensure_moderator(moderator)

        async with self._session.begin():
            request = await self._get_processable_request_for_update(command.request_id)
            variant = await self._variants.get_by_id(command.existing_variant_id)
            if variant is None:
                raise NotFoundError("Catalog variant was not found.")

            request.status = CatalogRequestStatus.DUPLICATE
            request.approved_catalog_item_id = variant.catalog_item_id
            request.approved_variant_id = variant.id
            request.moderated_by_id = moderator.id

            await self._actions.create(
                ModerationAction(
                    request_id=request.id,
                    moderator_id=moderator.id,
                    action=ModerationActionType.MARK_DUPLICATE,
                    comment=command.comment,
                    payload=command.payload,
                ),
            )
            await self._wishlist.relink_request_items_to_variant(
                request_id=request.id,
                variant_id=variant.id,
            )

        return request

    async def _resolve_approval_target(
        self,
        *,
        moderator: User,
        command: ApproveCatalogRequestCommand,
    ) -> tuple[CatalogItem, CatalogVariant]:
        variant = await self._resolve_existing_variant(command.existing_variant_id)
        if variant is not None:
            item = await self._items.get_by_id(variant.catalog_item_id)
            if item is None:
                raise ConflictError("Catalog variant points to a missing catalog item.")
            if (
                command.existing_catalog_item_id is not None
                and command.existing_catalog_item_id != item.id
            ):
                raise ConflictError("Catalog variant does not belong to catalog item.")
            return item, variant

        item = await self._resolve_catalog_item(moderator=moderator, command=command)
        if command.new_variant is None:
            raise ConflictError("New variant data or existing variant id is required.")

        variant = await self._variants.create(
            CatalogVariant(
                catalog_item_id=item.id,
                canonical_title=command.new_variant.canonical_title,
                normalized_title=command.new_variant.normalized_title,
                sku=command.new_variant.sku,
                barcode=command.new_variant.barcode,
                release_date=command.new_variant.release_date,
                status=command.new_variant.status,
                created_by_id=moderator.id,
                updated_by_id=moderator.id,
            ),
        )
        return item, variant

    async def _resolve_catalog_item(
        self,
        *,
        moderator: User,
        command: ApproveCatalogRequestCommand,
    ) -> CatalogItem:
        if command.existing_catalog_item_id is not None:
            item = await self._items.get_by_id(command.existing_catalog_item_id)
            if item is None:
                raise NotFoundError("Catalog item was not found.")
            return item

        if command.new_catalog_item is None:
            raise ConflictError("New catalog item data or existing catalog item id is required.")

        return await self._items.create(
            CatalogItem(
                category_id=command.new_catalog_item.category_id,
                canonical_title=command.new_catalog_item.canonical_title,
                normalized_title=command.new_catalog_item.normalized_title,
                description=command.new_catalog_item.description,
                release_year=command.new_catalog_item.release_year,
                status=command.new_catalog_item.status,
                created_by_id=moderator.id,
                updated_by_id=moderator.id,
            ),
        )

    async def _resolve_existing_variant(
        self,
        variant_id: UUID | None,
    ) -> CatalogVariant | None:
        if variant_id is None:
            return None

        variant = await self._variants.get_by_id(variant_id)
        if variant is None:
            raise NotFoundError("Catalog variant was not found.")
        return variant

    async def _get_processable_request_for_update(
        self,
        request_id: UUID,
    ) -> CatalogRequest:
        request = await self._requests.get_by_id_for_update(request_id)
        if request is None:
            raise NotFoundError("Catalog request was not found.")
        if request.status not in PROCESSABLE_REQUEST_STATUSES:
            raise ConflictError("Catalog request status does not allow this action.")
        return request

    def _ensure_moderator(self, user: User) -> None:
        if not user.is_active or user.role not in MODERATION_ROLES:
            raise ForbiddenError("Moderator permissions are required.")

    def _ensure_senior_moderator(self, user: User) -> None:
        if not user.is_active or user.role not in SENIOR_MODERATION_ROLES:
            raise ForbiddenError("Senior moderator permissions are required.")
