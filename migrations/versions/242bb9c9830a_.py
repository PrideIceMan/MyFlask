"""empty message

Revision ID: 242bb9c9830a
Revises: 
Create Date: 2019-08-22 22:18:04.261018

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '242bb9c9830a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_testcase_scenes_timestamp'), 'testcase_scenes', ['timestamp'], unique=False)
    op.create_index(op.f('ix_variables_timestamp'), 'variables', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_variables_timestamp'), table_name='variables')
    op.drop_index(op.f('ix_testcase_scenes_timestamp'), table_name='testcase_scenes')
    # ### end Alembic commands ###