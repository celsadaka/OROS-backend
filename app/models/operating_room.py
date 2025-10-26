from __future__ import annotations
from sqlalchemy import String, Integer, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum
from typing import Optional


# Define possible room statuses
class RoomStatus(str, enum.Enum):
    available = "available"
    occupied = "occupied"
    maintenance = "maintenance"


class operating_rooms(Base):
    """Operating Room model — represents hospital operating rooms."""

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    room_number: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    room_name: Mapped[Optional[str]] = mapped_column(String(120))
    capacity: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[RoomStatus] = mapped_column(Enum(RoomStatus), default=RoomStatus.available)
    location: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationship — one room can have many surgeries
    surgeries = relationship("surgeries", back_populates="operating_room")

    def __repr__(self) -> str:
        return f"<OperatingRoom(id={self.id}, number={self.room_number}, status={self.status})>"
