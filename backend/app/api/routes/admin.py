from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.reference import ReferenceType
from app.models.user import User
from app.schemas.admin import (
    AttributeDefinitionCreateSchema,
    AttributeDefinitionResponseSchema,
    CategoryCreateSchema,
    CategoryResponseSchema,
    ReferenceEntityCreateSchema,
    ReferenceEntityResponseSchema,
)
from app.services.admin import (
    AdminCatalogService,
    CreateAttributeDefinitionCommand,
    CreateCategoryCommand,
    CreateReferenceEntityCommand,
)

router = APIRouter(prefix="/admin", tags=["admin"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/categories", response_model=list[CategoryResponseSchema])
async def list_categories(session: DbSession) -> list[CategoryResponseSchema]:
    service = AdminCatalogService(session)
    categories = await service.list_categories()
    return [CategoryResponseSchema.model_validate(category) for category in categories]


@router.post(
    "/categories",
    response_model=CategoryResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    payload: CategoryCreateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CategoryResponseSchema:
    service = AdminCatalogService(session)
    category = await service.create_category(
        actor=current_user,
        command=CreateCategoryCommand(
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            is_active=payload.is_active,
        ),
    )
    await session.refresh(category)
    return CategoryResponseSchema.model_validate(category)


@router.get(
    "/attributes",
    response_model=list[AttributeDefinitionResponseSchema],
)
async def list_attribute_definitions(
    session: DbSession,
    category_id: Annotated[UUID, Query()],
) -> list[AttributeDefinitionResponseSchema]:
    service = AdminCatalogService(session)
    definitions = await service.list_attributes(category_id=category_id)
    references = await service.list_references()
    reference_options_by_type: dict[ReferenceType, list[ReferenceEntityResponseSchema]] = {}
    for reference in references:
        reference_options_by_type.setdefault(reference.type, []).append(
            ReferenceEntityResponseSchema.model_validate(reference)
        )
    return [
        AttributeDefinitionResponseSchema.model_validate(definition).model_copy(
            update={
                "reference_options": reference_options_by_type.get(definition.reference_type, [])
                if definition.reference_type is not None
                else []
            }
        )
        for definition in definitions
    ]


@router.post(
    "/attributes",
    response_model=AttributeDefinitionResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_attribute_definition(
    payload: AttributeDefinitionCreateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> AttributeDefinitionResponseSchema:
    service = AdminCatalogService(session)
    definition = await service.create_attribute(
        actor=current_user,
        command=CreateAttributeDefinitionCommand(
            category_id=payload.category_id,
            code=payload.code,
            name=payload.name,
            value_type=payload.value_type,
            reference_type=payload.reference_type,
            is_required=payload.is_required,
            is_filterable=payload.is_filterable,
            is_searchable=payload.is_searchable,
            is_variant_attribute=payload.is_variant_attribute,
            sort_order=payload.sort_order,
            validation_rules=payload.validation_rules,
        ),
    )
    await session.refresh(definition)
    reference_options = []
    if definition.reference_type is not None:
        reference_options = [
            ReferenceEntityResponseSchema.model_validate(reference)
            for reference in await service.list_references(reference_type=definition.reference_type)
        ]
    return AttributeDefinitionResponseSchema.model_validate(definition).model_copy(
        update={"reference_options": reference_options}
    )


@router.get("/references", response_model=list[ReferenceEntityResponseSchema])
async def list_references(
    session: DbSession,
    reference_type: Annotated[ReferenceType | None, Query(alias="type")] = None,
) -> list[ReferenceEntityResponseSchema]:
    service = AdminCatalogService(session)
    references = await service.list_references(reference_type=reference_type)
    return [ReferenceEntityResponseSchema.model_validate(reference) for reference in references]


@router.post(
    "/references",
    response_model=ReferenceEntityResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_reference(
    payload: ReferenceEntityCreateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> ReferenceEntityResponseSchema:
    service = AdminCatalogService(session)
    reference = await service.create_reference(
        actor=current_user,
        command=CreateReferenceEntityCommand(
            type=payload.type,
            canonical_name=payload.canonical_name,
            normalized_name=payload.normalized_name,
        ),
    )
    await session.refresh(reference)
    return ReferenceEntityResponseSchema.model_validate(reference)
