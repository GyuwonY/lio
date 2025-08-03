from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    애플리케이션의 설정을 관리하는 클래스.
    .env 파일에서 환경 변수를 로드합니다.
    """
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    WEAVIATE_URL: str = Field(..., env="WEAVIATE_URL")
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    GOOGLE_CLIENT_ID: str = Field(..., env="GOOGLE_CLIENT_ID")
    API_V1_STR: str = Field("/api/v1", env="API_V1_STR")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# 설정 객체 인스턴스 생성
settings = Settings()
