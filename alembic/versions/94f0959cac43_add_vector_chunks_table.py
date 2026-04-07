"""add vector chunks table

Revision ID: 94f0959cac43
Revises: d69326dbb6e2
Create Date: 2024-05-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy # 必须引入 pgvector

# revision identifiers, used by Alembic.
revision = '94f0959cac43'
down_revision = 'd69326dbb6e2'
branch_labels = None
depends_on = None

def upgrade():
    # 【核心破局军令】：在建表前，强制开启 PostgreSQL 的向量插件！
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')

    op.create_table('document_chunks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=True),
    sa.Column('chunk_index', sa.Integer(), nullable=True),
    sa.Column('text_content', sa.Text(), nullable=True),
    # 【口径修正】：对齐本地神兵的 768 维
    sa.Column('embedding', pgvector.sqlalchemy.Vector(dim=768), nullable=True),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_chunks_id'), 'document_chunks', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_document_chunks_id'), table_name='document_chunks')
    op.drop_table('document_chunks')
    # 回退时卸载插件
    op.execute('DROP EXTENSION IF EXISTS vector;')