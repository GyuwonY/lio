from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import weaviate

from app.core.config import settings

# 1. SQLAlchemy (MySQL) 비동기 설정
# ---------------------------------
# 비동기 데이터베이스 엔진 생성
async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

# 비동기 데이터베이스 세션 생성기
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# ORM 모델의 기본이 될 Base 클래스
Base = declarative_base()


# 2. Weaviate 비동기 설정
# ---------------------------------
# Weaviate 클라이언트 생성 (v4에서는 기본적으로 비동기 지원)
# Weaviate 설정은 라이브러리 버전에 따라 달라질 수 있습니다.
# 여기서는 v3 기준 동기 클라이언트를 사용하되, 호출부에서 비동기 처리합니다.
weaviate_client = weaviate.Client(settings.WEAVIATE_URL)


# 3. FastAPI 비동기 의존성 함수
# ---------------------------------
async def get_db() -> AsyncSession:
    """
    API 라우터에서 사용할 비동기 데이터베이스 세션 의존성.
    """
    async with AsyncSessionLocal() as session:
        yield session
