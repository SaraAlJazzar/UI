
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '703414e4cef9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'settings' not in inspector.get_table_names():
        op.create_table('settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('api_key', sa.String(length=255), nullable=True),
            sa.Column('model', sa.String(length=100), nullable=False),
            sa.Column('language', sa.String(length=10), nullable=False),
            sa.Column('context_messages', sa.Integer(), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('settings')
