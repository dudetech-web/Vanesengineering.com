"""create progress table

Revision ID: 01
Revises: 
Create Date: 2025-08-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'progress',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('sheet_cutting_area', sa.Float(), nullable=True, default=0),
        sa.Column('fabrication_area', sa.Float(), nullable=True, default=0),
        sa.Column('dispatch_area', sa.Float(), nullable=True, default=0),
        sa.ForeignKeyConstraint(['project_id'], ['project.id']),
    )


def downgrade():
    op.drop_table('progress')
