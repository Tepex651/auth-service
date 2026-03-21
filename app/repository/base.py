from collections.abc import Sequence

from sqlalchemy import UnaryExpression, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute


class BaseRepository[T: DeclarativeBase]:
    model: type[T] | None = None

    def __init__(self, session) -> None:
        self._session = session
        self._sortable_fields = self._build_sortable_fields() if self.model else {}

    @property
    def session(self) -> AsyncSession:
        try:
            return self._session
        except LookupError as err:
            raise RuntimeError("DB session is not set in context") from err

    def _build_sortable_fields(self) -> dict[str, InstrumentedAttribute]:
        fields: dict[str, InstrumentedAttribute] = {}

        for attr_name in dir(self.model):
            attr = getattr(self.model, attr_name, None)

            if isinstance(attr, InstrumentedAttribute):
                fields[attr_name] = attr

        return fields

    def _get_sort_expression(self, sort_by: str, sort_order: str) -> UnaryExpression:
        if not self._sortable_fields:
            raise RuntimeError("Sorting not available: repository has no model")

        if sort_by not in self._sortable_fields:
            raise ValueError(f"Invalid sort field: {sort_by}")

        column = self._sortable_fields[sort_by]

        if sort_order == "desc":
            return desc(column)

        return asc(column)

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "asc",
    ) -> tuple[Sequence[T], int]:
        if self.model is None:
            raise ValueError("Repository model is not set")

        order_expr = self._get_sort_expression(sort_by, sort_order)

        stmt = select(self.model).order_by(order_expr).limit(limit).offset(offset)

        count_stmt = select(func.count()).select_from(self.model)

        result = await self.session.execute(stmt)
        count = await self.session.scalar(count_stmt)

        return result.scalars().all(), count or 0
