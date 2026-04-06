"""add vector chunks table

Revision ID: 94f0959cac43
Revises: d69326dbb6e2
Create Date: 2026-04-06 16:59:08.081231

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision: str = '94f0959cac43'
down_revision: Union[str, Sequence[str], None] = 'd69326dbb6e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 先建立新的向量表
    op.create_table('document_chunks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=True),
    sa.Column('chunk_index', sa.Integer(), nullable=True, comment='切片序号'),
    sa.Column('text_content', sa.Text(), nullable=True, comment='切片物理文本'),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=1536), nullable=True, comment='高维数学坐标'),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_chunks_id'), 'document_chunks', ['id'], unique=False)
    
    # 2. 【核心修复】必须先解除 documents 表对外键的依赖！
    op.drop_constraint('documents_owner_id_fkey', 'documents', type_='foreignkey')
    op.drop_column('documents', 'owner_id')

    # 3. 然后再放心大胆地删除 users 表
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')

    # 4. 其他常规字段更新
    op.alter_column('analysis_results', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=True,
               existing_server_default=sa.text('now()'))
    op.drop_constraint('analysis_results_document_id_fkey', 'analysis_results', type_='foreignkey')
    op.create_foreign_key(None, 'analysis_results', 'documents', ['document_id'], ['id'], ondelete='CASCADE')
    op.alter_column('documents', 'title',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.alter_column('documents', 'filename',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.alter_column('documents', 'file_path',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.alter_column('documents', 'language',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=True)
    op.alter_column('documents', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=True,
               existing_server_default=sa.text('now()'))
    op.create_index(op.f('ix_documents_title'), 'documents', ['title'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 【核心修复】回退时，必须先重建 users 表，才能往 documents 里加外键
    op.create_table('users',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('username', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('hashed_password', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='users_pkey')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.add_column('documents', sa.Column('owner_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('documents_owner_id_fkey', 'documents', 'users', ['owner_id'], ['id'])
    
    op.drop_index(op.f('ix_documents_title'), table_name='documents')
    op.alter_column('documents', 'created_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True,
               existing_server_default=sa.text('now()'))
    op.alter_column('documents', 'language',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=20),
               existing_nullable=True)
    op.alter_column('documents', 'file_path',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.alter_column('documents', 'filename',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.alter_column('documents', 'title',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.drop_constraint('analysis_results_document_id_fkey', 'analysis_results', type_='foreignkey')
    op.create_foreign_key('analysis_results_document_id_fkey', 'analysis_results', 'documents', ['document_id'], ['id'])
    op.alter_column('analysis_results', 'created_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True,
               existing_server_default=sa.text('now()'))
    op.drop_index(op.f('ix_document_chunks_id'), table_name='document_chunks')
    op.drop_table('document_chunks')