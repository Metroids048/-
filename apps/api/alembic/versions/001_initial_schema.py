"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-06-07
"""

from alembic import op

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # P0 uses SQLModel metadata.create_all in app startup; this revision documents the baseline.
    pass


def downgrade() -> None:
    pass
