"""Add users table and user_id to contacts

Revision ID: 3a1b2c3d4e5f
Revises: 2cbb5becc45f
Create Date: 2026-06-23 22:36:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '2cbb5becc45f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='False'),
        sa.Column('verification_token', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )

    # Drop unique constraints on contacts
    op.drop_constraint('contacts_email_key', 'contacts', type_='unique')
    op.drop_constraint('contacts_phone_key', 'contacts', type_='unique')

    # Add user_id column to contacts
    op.add_column('contacts', sa.Column('user_id', sa.Integer(), nullable=False, server_default='0'))

    # Create foreign key
    op.create_foreign_key('fk_contacts_user_id', 'contacts', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key
    op.drop_constraint('fk_contacts_user_id', 'contacts', type_='foreignkey')

    # Drop user_id column from contacts
    op.drop_column('contacts', 'user_id')

    # Restore unique constraints
    op.create_unique_constraint('contacts_email_key', 'contacts', ['email'])
    op.create_unique_constraint('contacts_phone_key', 'contacts', ['phone'])

    # Drop users table
    op.drop_table('users')