from datetime import date, datetime, time

from pydantic import BaseModel


class DistanceBrief(BaseModel):
    label: str
    distance_km: float


class DistanceOut(DistanceBrief):
    start_time: time | None = None
    fee_vnd: int | None = None
    elevation_gain_m: int | None = None
    cutoff_minutes: int | None = None
    registration_deadline: date | None = None


class EventSummary(BaseModel):
    slug: str
    name: str
    organizer: str | None = None
    event_type: str
    start_date: date
    end_date: date | None = None
    province: str | None = None
    venue: str | None = None
    # Effective status: stored status adjusted for deadlines and past events.
    status: str
    closing_soon: bool
    days_left: int | None = None
    verified: bool
    last_verified_at: datetime | None = None
    distances: list[DistanceBrief]


class EventDetail(EventSummary):
    description: str | None = None
    map_url: str | None = None
    registration_url: str | None = None
    registration_deadline: date | None = None
    source_name: str | None = None
    source_url: str | None = None
    distances: list[DistanceOut]


class EventPage(BaseModel):
    items: list[EventSummary]
    next_cursor: str | None = None
    total: int
    last_updated_at: datetime | None = None
