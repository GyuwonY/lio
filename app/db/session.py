from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings
import redis.asyncio as redis

# PostgreSQL (SQLAlchemy)
async_engine = create_async_engine(
    settings.DATABASE_URL, pool_pre_ping=True, echo=False
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
Base = declarative_base()

# Redis
redis_pool = redis.ConnectionPool.from_url(
    f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_URL}:6379/0",
    encoding="utf-8",
    decode_responses=True,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


async def get_redis_client() -> redis.Redis:
    return redis.Redis(connection_pool=redis_pool)


async def close_redis_pool():
    await redis_pool.disconnect()
