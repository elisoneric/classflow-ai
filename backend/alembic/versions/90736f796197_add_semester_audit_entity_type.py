"""add semester audit entity type

Revision ID: 90736f796197
Revises: 8bbc33ee90c8
Create Date: 2026-08-05 11:24:35.822342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90736f796197'
down_revision: Union[str, Sequence[str], None] = '8bbc33ee90c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres enums aren't diffed by autogenerate — added by hand.
    op.execute("ALTER TYPE audit_entity_type ADD VALUE IF NOT EXISTS 'SEMESTER'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums; downgrading this is not supported.
    pass
