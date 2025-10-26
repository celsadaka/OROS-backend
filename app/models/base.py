from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column
from sqlalchemy import DateTime, func

class Base(DeclarativeBase):
    """Base class that all ORM models will inherit from."""

    # automatically name the table after the class name (lowercase)
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    # timestamp columns shared across all tables
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
