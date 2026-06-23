from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import ModerationAction
from app.models.request import CatalogRequest, CatalogRequestStatus


class CatalogRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, request: CatalogRequest) -> CatalogRequest:
        self._session.add(request)
        await self._session.flush()
        return request

    async def get_by_id(self, request_id: UUID) -> CatalogRequest | None:
        return await self._session.get(CatalogRequest, request_id)

    async def get_by_id_for_user(
        self,
        *,
        request_id: UUID,
        user_id: UUID,
    ) -> CatalogRequest | None:
        statement = select(CatalogRequest).where(
            CatalogRequest.id == request_id,
            CatalogRequest.created_by_id == user_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, request_id: UUID) -> CatalogRequest | None:
        statement = select(CatalogRequest).where(CatalogRequest.id == request_id).with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        status: CatalogRequestStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CatalogRequest]:
        statement = (
            select(CatalogRequest)
            .where(CatalogRequest.created_by_id == user_id)
            .order_by(CatalogRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            statement = statement.where(CatalogRequest.status == status)

        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def list_queue(
        self,
        *,
        status: CatalogRequestStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CatalogRequest]:
        statement = select(CatalogRequest).order_by(CatalogRequest.created_at.asc())
        if status is not None:
            statement = statement.where(CatalogRequest.status == status)
        statement = statement.limit(limit).offset(offset)

        result = await self._session.execute(statement)
        return list(result.scalars().all())


class ModerationActionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, action: ModerationAction) -> ModerationAction:
        self._session.add(action)
        await self._session.flush()
        return action
