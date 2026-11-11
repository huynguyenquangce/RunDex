"""sources.extractor: which extractor reads a source's pages (ai | jsonld)

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-11
"""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sources", sa.Column("extractor", sa.String(10), nullable=False, server_default="ai")
    )


def downgrade() -> None:
    op.drop_column("sources", "extractor")
