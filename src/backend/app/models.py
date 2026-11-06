from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

EVENT_TYPES = ("road", "trail", "mixed")
EVENT_STATUSES = (
    "scheduled",
    "registration_open",
    "registration_closed",
    "postponed",
    "cancelled",
    "completed",
)


def _in_list(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(_in_list("event_type", EVENT_TYPES), name="ck_events_event_type"),
        CheckConstraint(_in_list("status", EVENT_STATUSES), name="ck_events_status"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_events_dates"),
        Index("ix_events_start_date_id", "start_date", "id"),
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    organizer: Mapped[str | None] = mapped_column(String(200))
    event_type: Mapped[str] = mapped_column(String(10))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    province: Mapped[str | None] = mapped_column(String(100))
    venue: Mapped[str | None] = mapped_column(String(200))
    map_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), server_default="scheduled")
    registration_url: Mapped[str | None] = mapped_column(Text)
    registration_deadline: Mapped[date | None] = mapped_column(Date)
    source_name: Mapped[str | None] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(Text)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Diacritic-insensitive, lowercase text used by search (see migration 0001).
    search_text: Mapped[str] = mapped_column(
        Text,
        Computed(
            "lower(f_unaccent(name || ' ' || coalesce(province, '') || ' ' "
            "|| coalesce(organizer, '')))",
            persisted=True,
        ),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    distances: Mapped[list["Distance"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="Distance.distance_km.desc()",
    )


class Distance(Base):
    __tablename__ = "distances"
    __table_args__ = (
        UniqueConstraint("event_id", "label", name="uq_distances_event_label"),
        CheckConstraint("distance_km > 0", name="ck_distances_distance_km"),
        Index("ix_distances_event_id", "event_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(40))
    distance_km: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    start_time: Mapped[time | None] = mapped_column(Time)
    fee_vnd: Mapped[int | None] = mapped_column(Integer)
    elevation_gain_m: Mapped[int | None] = mapped_column(Integer)
    cutoff_minutes: Mapped[int | None] = mapped_column(Integer)
    registration_deadline: Mapped[date | None] = mapped_column(Date)

    event: Mapped[Event] = relationship(back_populates="distances")
