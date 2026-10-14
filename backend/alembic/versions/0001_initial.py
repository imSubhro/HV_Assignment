"""initial schema

Revision ID: d2b54423a089
Revises: 
Create Date: 2026-10-14 20:20:57.095815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2b54423a089'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('full_name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.Enum('user', 'admin', name='user_role'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('conversations',
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('mode', sa.Enum('online', 'offline', name='conversation_mode'), nullable=False),
    sa.Column('location_or_link', sa.String(length=500), nullable=False),
    sa.Column('capacity', sa.Integer(), nullable=True),
    sa.Column('cover_image_url', sa.String(length=500), nullable=True),
    sa.Column('status', sa.Enum('draft', 'published', 'cancelled', name='conversation_status'), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversations_status_scheduled_at', 'conversations', ['status', 'scheduled_at'], unique=False)
    op.create_table('investor_requests',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('full_name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('company_name', sa.String(length=200), nullable=False),
    sa.Column('funding_stage', sa.Enum('idea', 'pre_seed', 'seed', 'series_a', 'series_b_plus', name='funding_stage'), nullable=False),
    sa.Column('funding_amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'under_review', 'approved', 'rejected', name='investor_request_status'), nullable=False),
    sa.Column('admin_notes', sa.Text(), nullable=True),
    sa.Column('reviewed_by', sa.Uuid(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_investor_requests_status_created_at', 'investor_requests', ['status', 'created_at'], unique=False)
    op.create_index('ix_investor_requests_user_id', 'investor_requests', ['user_id'], unique=False)
    op.create_table('conversation_speakers',
    sa.Column('conversation_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('designation', sa.String(length=150), nullable=True),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.Column('photo_url', sa.String(length=500), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_speakers_conversation_id'), 'conversation_speakers', ['conversation_id'], unique=False)
    op.create_table('investor_request_status_history',
    sa.Column('request_id', sa.Uuid(), nullable=False),
    sa.Column('from_status', sa.Enum('pending', 'under_review', 'approved', 'rejected', name='investor_request_status'), nullable=True),
    sa.Column('to_status', sa.Enum('pending', 'under_review', 'approved', 'rejected', name='investor_request_status'), nullable=False),
    sa.Column('changed_by', sa.Uuid(), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['request_id'], ['investor_requests.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_investor_request_status_history_request_id'), 'investor_request_status_history', ['request_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_investor_request_status_history_request_id'), table_name='investor_request_status_history')
    op.drop_table('investor_request_status_history')
    op.drop_index(op.f('ix_conversation_speakers_conversation_id'), table_name='conversation_speakers')
    op.drop_table('conversation_speakers')
    op.drop_index('ix_investor_requests_user_id', table_name='investor_requests')
    op.drop_index('ix_investor_requests_status_created_at', table_name='investor_requests')
    op.drop_table('investor_requests')
    op.drop_index('ix_conversations_status_scheduled_at', table_name='conversations')
    op.drop_table('conversations')
    op.drop_table('users')
