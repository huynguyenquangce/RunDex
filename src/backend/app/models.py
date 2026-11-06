from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
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
            "|| coalesce(venue, '') || ' ' || coalesce(organizer, '')))",
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


SOURCE_KINDS = ("sitemap", "listing_page", "event_page")
PROPOSAL_KINDS = ("create", "update")
PROPOSAL_STATUSES = ("pending", "auto_applied", "approved", "rejected", "superseded")


class Source(Base):
    """A registered place to look for events (see config/sources.yaml)."""

    __tablename__ = "sources"
    __table_args__ = (
        CheckConstraint(_in_list("kind", SOURCE_KINDS), name="ck_sources_kind"),
        CheckConstraint("tier BETWEEN 1 AND 3", name="ck_sources_tier"),
        CheckConstraint("refresh_days > 0", name="ck_sources_refresh_days"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20))
    url: Mapped[str] = mapped_column(Text)
    tier: Mapped[int] = mapped_column(SmallInteger)
    url_include: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, server_default="true")
    refresh_days: Mapped[int] = mapped_column(Integer, server_default="7")
    notes: Mapped[str | None] = mapped_column(Text)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RawDocument(Base):
    """A fetched page. Unchanged content (same hash) is not extracted twice."""

    __tablename__ = "raw_documents"
    __table_args__ = (
        UniqueConstraint("url", "content_hash", name="uq_raw_documents_url_hash"),
        Index("ix_raw_documents_source_url", "source_id", "url", "fetched_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    http_status: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text)
    etag: Mapped[str | None] = mapped_column(Text)
    last_modified: Mapped[str | None] = mapped_column(Text)


class ChangeProposal(Base):
    """One proposed change to the catalog, with where it came from and why it was (not) applied."""

    __tablename__ = "change_proposals"
    __table_args__ = (
        CheckConstraint(_in_list("kind", PROPOSAL_KINDS), name="ck_change_proposals_kind"),
        CheckConstraint(_in_list("status", PROPOSAL_STATUSES), name="ck_change_proposals_status"),
        CheckConstraint("tier BETWEEN 1 AND 3", name="ck_change_proposals_tier"),
        Index("ix_change_proposals_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    kind: Mapped[str] = mapped_column(String(10))
    # NULL for a "create" proposal until the event exists.
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    raw_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("raw_documents.id", ondelete="SET NULL")
    )
    field: Mapped[str | None] = mapped_column(String(60))
    old_value: Mapped[object | None] = mapped_column(JSONB)
    new_value: Mapped[object] = mapped_column(JSONB)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    evidence: Mapped[str | None] = mapped_column(Text)
    tier: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(15), server_default="pending")
    reason: Mapped[str | None] = mapped_column(Text)
    decided_by: Mapped[str | None] = mapped_column(String(80))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    """Append-only record of every change applied to the catalog."""

    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_event_id", "event_id"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actor: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(40))
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"))
    proposal_id: Mapped[int | None] = mapped_column(
        ForeignKey("change_proposals.id", ondelete="SET NULL")
    )
    details: Mapped[object | None] = mapped_column(JSONB)
