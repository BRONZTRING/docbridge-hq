import asyncio
from logging.config import fileConfig
import sys
import os

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 【法阵核心1】：将大本营根目录加入系统路径，确保能顺利导入 app 模块
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 【法阵核心2】：导入统帅的数据库配置与阵法基类
from app.database import SQLALCHEMY_DATABASE_URL
from app.models import Base

# 获取 Alembic 配置对象
config = context.config

# 【法阵核心3】：将 database.py 中的物理坐标强行注入 Alembic，省去修改 alembic.ini 的繁琐
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 【法阵核心4】：告诉 Alembic 去扫描统帅的蓝图
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()