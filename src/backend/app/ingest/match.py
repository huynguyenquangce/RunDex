"""Find the existing catalog event a candidate refers to."""

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ingest.normalize import EventData
from app.models import Event

NAME_SIMILARITY = 0.55
DATE_WINDOW = timedelta(days=2)


def find_match(session: Session, data: EventData) -> Event | None:
    exact = session.scalar(select(Event).where(Event.slug == data.slug))
    if exact is not None:
        return exact
    folded_name = func.lower(func.f_unaccent(data.name))
    similarity = func.similarity(func.lower(func.f_unaccent(Event.name)), folded_name)
    query = (
        select(Event)
        .where(
            similarity >= NAME_SIMILARITY,
            Event.start_date.between(data.start_date - DATE_WINDOW, data.start_date + DATE_WINDOW),
        )
        .order_by(similarity.desc())
        .limit(1)
    )
    return session.scalar(query)
