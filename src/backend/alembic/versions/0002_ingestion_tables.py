"""ingestion tables: sources, raw_documents, change_proposals, audit_log

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-06
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("tier", sa.SmallInteger(), nullable=False),
        sa.Column("url_include", sa.Text()),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("refresh_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("notes", sa.Text()),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "kind IN ('sitemap', 'listing_page', 'event_page')", name="ck_sources_kind"
        ),
        sa.CheckConstraint("tier BETWEEN 1 AND 3", name="ck_sources_tier"),
        sa.CheckConstraint("refresh_days > 0", name="ck_sources_refresh_days"),
    )

    op.create_table(
        "raw_documents",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "source_id",
            sa.String(80),
            sa.ForeignKey("sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column(
            "fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("http_status", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("etag", sa.Text()),
        sa.Column("last_modified", sa.Text()),
        sa.UniqueConstraint("url", "content_hash", name="uq_raw_documents_url_hash"),
    )
    op.create_index(
        "ix_raw_documents_source_url", "raw_documents", ["source_id", "url", "fetched_at"]
    )

    op.create_table(
        "change_proposals",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("event_id", sa.BigInteger(), sa.ForeignKey("events.id", ondelete="CASCADE")),
        sa.Column(
            "source_id",
            sa.String(80),
            sa.ForeignKey("sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "raw_document_id",
            sa.BigInteger(),
            sa.ForeignKey("raw_documents.id", ondelete="SET NULL"),
        ),
        sa.Column("field", sa.String(60)),
        sa.Column("old_value", postgresql.JSONB()),
        sa.Column("new_value", postgresql.JSONB(), nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2)),
        sa.Column("evidence", sa.Text()),
        sa.Column("tier", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.String(15), nullable=False, server_default="pending"),
        sa.Column("reason", sa.Text()),
        sa.Column("decided_by", sa.String(80)),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("kind IN ('create', 'update')", name="ck_change_proposals_kind"),
        sa.CheckConstraint(
            "status IN ('pending', 'auto_applied', 'approved', 'rejected', 'superseded')",
            name="ck_change_proposals_status",
        ),
        sa.CheckConstraint("tier BETWEEN 1 AND 3", name="ck_change_proposals_tier"),
    )
    op.create_index("ix_change_proposals_status", "change_proposals", ["status"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("actor", sa.String(80), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("event_id", sa.BigInteger(), sa.ForeignKey("events.id", ondelete="SET NULL")),
        sa.Column(
            "proposal_id",
            sa.BigInteger(),
            sa.ForeignKey("change_proposals.id", ondelete="SET NULL"),
        ),
        sa.Column("details", postgresql.JSONB()),
    )
    op.create_index("ix_audit_log_event_id", "audit_log", ["event_id"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("change_proposals")
    op.drop_table("raw_documents")
    op.drop_table("sources")
