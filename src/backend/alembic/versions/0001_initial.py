"""initial schema: events and distances

Revision ID: 0001
Revises:
Create Date: 2026-11-06
"""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

EVENT_TYPES = "('road', 'trail', 'mixed')"
EVENT_STATUSES = (
    "('scheduled', 'registration_open', 'registration_closed', "
    "'postponed', 'cancelled', 'completed')"
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    # unaccent() is not IMMUTABLE; this wrapper is, so it can back a generated column.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text
        AS $$ SELECT public.unaccent('public.unaccent', $1) $$
        LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
        """
    )

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("organizer", sa.String(200)),
        sa.Column("event_type", sa.String(10), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date()),
        sa.Column("province", sa.String(100)),
        sa.Column("venue", sa.String(200)),
        sa.Column("map_url", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("registration_url", sa.Text()),
        sa.Column("registration_deadline", sa.Date()),
        sa.Column("source_name", sa.String(200)),
        sa.Column("source_url", sa.Text()),
        sa.Column("last_verified_at", sa.DateTime(timezone=True)),
        sa.Column(
            "search_text",
            sa.Text(),
            sa.Computed(
                "lower(f_unaccent(name || ' ' || coalesce(province, '') || ' ' "
                "|| coalesce(venue, '') || ' ' || coalesce(organizer, '')))",
                persisted=True,
            ),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("slug", name="uq_events_slug"),
        sa.CheckConstraint(f"event_type IN {EVENT_TYPES}", name="ck_events_event_type"),
        sa.CheckConstraint(f"status IN {EVENT_STATUSES}", name="ck_events_status"),
        sa.CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_events_dates"),
    )
    op.create_index("ix_events_start_date_id", "events", ["start_date", "id"])
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_status", "events", ["status"])
    op.execute("CREATE INDEX ix_events_search_trgm ON events USING gin (search_text gin_trgm_ops)")

    op.create_table(
        "distances",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "event_id",
            sa.BigInteger(),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(40), nullable=False),
        sa.Column("distance_km", sa.Numeric(6, 2), nullable=False),
        sa.Column("start_time", sa.Time()),
        sa.Column("fee_vnd", sa.Integer()),
        sa.Column("elevation_gain_m", sa.Integer()),
        sa.Column("cutoff_minutes", sa.Integer()),
        sa.Column("registration_deadline", sa.Date()),
        sa.UniqueConstraint("event_id", "label", name="uq_distances_event_label"),
        sa.CheckConstraint("distance_km > 0", name="ck_distances_distance_km"),
    )
    op.create_index("ix_distances_event_id", "distances", ["event_id"])


def downgrade() -> None:
    op.drop_table("distances")
    op.drop_table("events")
    op.execute("DROP FUNCTION IF EXISTS f_unaccent(text)")
