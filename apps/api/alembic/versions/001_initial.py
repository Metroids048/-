"""initial schema via SQLModel metadata

Revision ID: 001_initial
"""

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from apps.api.alpha_sim.database import init_db

    init_db()


def downgrade() -> None:
    pass
