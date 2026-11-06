from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.regions import Region
from app.deps import get_db, get_today
from app.schemas import EventDetail, EventPage
from app.services import events as service

router = APIRouter(prefix="/v1/events", tags=["events"])

DistanceBucket = Literal["5", "10", "21", "42", "ultra"]


@router.get("", response_model=EventPage, summary="List events")
def list_events(
    db: Annotated[Session, Depends(get_db)],
    today: Annotated[date, Depends(get_today)],
    q: Annotated[
        str | None,
        Query(max_length=100, description="Search text; diacritics and case are ignored"),
    ] = None,
    event_type: Annotated[Literal["road", "trail", "mixed"] | None, Query(alias="type")] = None,
    distance: Annotated[
        list[DistanceBucket] | None,
        Query(description="Distance buckets (km): 5, 10, 21, 42, ultra (50 and above)"),
    ] = None,
    region: Region | None = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    open_only: bool = False,
    include_past: bool = False,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> EventPage:
    decoded = None
    if cursor is not None:
        try:
            decoded = service.decode_cursor(cursor)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid cursor") from exc
    filters = service.EventFilters(
        q=q,
        event_type=event_type,
        distances=list(distance or []),
        region=region,
        date_from=from_date,
        date_to=to_date,
        open_only=open_only,
        include_past=include_past,
    )
    rows, next_cursor, total, last_updated = service.list_events(db, filters, today, limit, decoded)
    return EventPage(
        items=[service.to_summary(row, today) for row in rows],
        next_cursor=next_cursor,
        total=total,
        last_updated_at=last_updated,
    )


@router.get("/{slug}", response_model=EventDetail, summary="Get one event")
def get_event(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    today: Annotated[date, Depends(get_today)],
) -> EventDetail:
    event = service.get_event_by_slug(db, slug)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return service.to_detail(event, today)
