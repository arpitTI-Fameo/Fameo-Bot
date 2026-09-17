"""
Generic async CRUD repository base.

Provides common database operations — domain repositories inherit and extend.
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar, Sequence

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic async repository providing CRUD operations.

    Subclasses set `model_class` and add domain-specific queries.
    """

    model_class: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        """Fetch a single entity by primary key."""
        return await self.session.get(self.model_class, entity_id)

    async def get_many(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        order_by: Any = None,
        filters: list[Any] | None = None,
    ) -> Sequence[ModelT]:
        """Fetch multiple entities with pagination and optional filtering."""
        stmt = select(self.model_class)

        if filters:
            for f in filters:
                stmt = stmt.where(f)

        if order_by is not None:
            stmt = stmt.order_by(order_by)
        else:
            # Default: newest first if model has created_at
            if hasattr(self.model_class, "created_at"):
                stmt = stmt.order_by(self.model_class.created_at.desc())  # type: ignore[union-attr]

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, filters: list[Any] | None = None) -> int:
        """Count entities with optional filtering."""
        stmt = select(func.count()).select_from(self.model_class)
        if filters:
            for f in filters:
                stmt = stmt.where(f)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, entity: ModelT) -> ModelT:
        """Add a new entity to the session."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def create_many(self, entities: list[ModelT]) -> list[ModelT]:
        """Add multiple entities."""
        self.session.add_all(entities)
        await self.session.flush()
        return entities

    async def update(self, entity: ModelT, **values: Any) -> ModelT:
        """Update entity attributes."""
        for key, value in values.items():
            setattr(entity, key, value)
        await self.session.flush()
        return entity

    async def delete(self, entity: ModelT) -> None:
        """Delete an entity."""
        await self.session.delete(entity)
        await self.session.flush()

    async def delete_by_id(self, entity_id: uuid.UUID) -> bool:
        """Delete an entity by ID. Returns True if deleted."""
        stmt = delete(self.model_class).where(
            self.model_class.id == entity_id  # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0  # type: ignore[union-attr]

    async def exists(self, entity_id: uuid.UUID) -> bool:
        """Check if entity exists."""
        stmt = select(func.count()).select_from(self.model_class).where(
            self.model_class.id == entity_id  # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0
