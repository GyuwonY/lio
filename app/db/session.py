from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import Auth

from app.core.config import settings

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


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


weaviate_client = weaviate.WeaviateAsyncClient(
    connection_params=ConnectionParams.from_params(
        http_host=settings.WEAVIATE_HOST,
        http_port=settings.WEAVIATE_PORT,
        http_secure=False,
        grpc_host=settings.WEAVIATE_HOST,
        grpc_port=50051,
        grpc_secure=False,
    ),
    auth_client_secret=Auth.api_key(settings.WEAVIATE_API_KEY),
)
