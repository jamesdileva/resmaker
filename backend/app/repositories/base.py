"""Base repository with shared session handling and CRUD helpers."""

from typing import Generic, Optional, TypeVar

from sqlmodel import Session, SQLModel, select

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseRepository(Generic[ModelT]):
    """Common session-managed persistence operations for a SQLModel table."""

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, instance: ModelT) -> ModelT:
        """Persist an instance and return it refreshed."""
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def get(self, entity_id: str) -> Optional[ModelT]:
        """Fetch one record by primary key, or None if absent."""
        return self.session.get(self.model, entity_id)

    def get_multi(
        self, skip: int = 0, limit: int = 50
    ) -> list[ModelT]:
        """Return a page of records ordered by insertion."""
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.session.exec(stmt))

    def delete(self, entity_id: str) -> bool:
        """Delete by primary key; return True if a row was removed."""
        instance = self.get(entity_id)
        if instance is None:
            return False
        self.session.delete(instance)
        self.session.commit()
        return True
