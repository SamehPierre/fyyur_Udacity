"""empty message

Revision ID: 9ec04d294d43
Revises: a6d2a2618cc4
Create Date: 2020-09-18 20:25:33.915828

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9ec04d294d43'
down_revision = 'a6d2a2618cc4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('artists', sa.Column('seeking_description', sa.String(), nullable=True))
    op.add_column('artists', sa.Column('seeking_venue', sa.Boolean(), nullable=False))
    op.add_column('venues', sa.Column('seeking_description', sa.String(), nullable=True))
    op.add_column('venues', sa.Column('seeking_talent', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venues', 'seeking_talent')
    op.drop_column('venues', 'seeking_description')
    op.drop_column('artists', 'seeking_venue')
    op.drop_column('artists', 'seeking_description')
    # ### end Alembic commands ###