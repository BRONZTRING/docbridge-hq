from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 数据库物理坐标：注意此处的 5433 端口，正是吾等在 Canvas 中开辟的新城门
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://docbridge_admin:docbridge_password@127.0.0.1:5433/docbridge_db"

# 铸造异步引擎 (echo=True 意为在终端打印底层 SQL 语句，方便统帅监军，生产环境可关闭)
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# 建立异步会话加工厂
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# 确立数据模型基类，日后所有的 Schema (如 User, Document) 皆以此为宗
Base = declarative_base()

# 定义神经探针：供 FastAPI 路由在每次请求时获取数据库会话，用完即焚（释放）
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session