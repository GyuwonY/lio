from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Environment settings
    APP_ENV: str = Field("local", env="APP_ENV")  # local or production
    GCP_PROJECT_ID: str = Field(..., env="GCP_PROJECT_ID")
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")

    # Database and Services
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field(..., env="REDIS_URL")
    REDIS_PASSWORD: str = Field(..., env="REDIS_PASSWORD")

    # JWT Settings
    ACCESS_TOKEN_SECRET_KEY: str = Field(..., env="ACCESS_TOKEN_SECRET_KEY")
    REFRESH_TOKEN_SECRET_KEY: str = Field(..., env="REFRESH_TOKEN_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        60 * 24 * 30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(
        60 * 24 * 14, env="REFRESH_TOKEN_EXPIRE_MINUTES"
    )

    # Google Auth
    GOOGLE_CLIENT_ID: str = Field(..., env="GOOGLE_CLIENT_ID")

    # GCS
    GCS_BUCKET_NAME: str = Field(..., env="GCS_BUCKET_NAME")
    GOOGLE_BUCKET_CREDENTIALS: str = Field(..., env="GOOGLE_BUCKET_CREDENTIALS")

    # Firebase
    FIREBASE_CREDENTIALS: str = Field(..., env="FIREBASE_CREDENTIALS")

    # API
    API_V1_STR: str = Field("/api/v1", env="API_V1_STR")

    # Model
    EMBEDDING_MODEL: str = Field("gemini-embedding-001", env="EMBEDDING_MODEL")
    PDF_PARSING_LLM_MODEL: str = Field(
        "gemini-2.5-flash-lite", env="PDF_PARSING_LLM_MODEL"
    )
    GENERATE_QNA_LLM_MODEL: str = Field(
        "gemini-2.5-flash", env="GENERATE_QNA_LLM_MODEL"
    )
    QUERY_GENERATION_LLM_MODEL: str = Field(
        "gemini-2.5-flash-lite", env="GENERATE_QNA_LLM_MODEL"
    )
    CHAT_LLM_MODEL: str = Field("gemini-2.5-flash", env="CHAT_LLM_MODEL")
    SUMMARIZE_LLM_MODEL: str = Field("gemini-2.5-flash-lite", env="SUMMARIZE_LLM_MODEL")

    LANGCHAIN_TRACING_V2: str = Field(..., env="LANGCHAIN_TRACING_V2")
    LANGCHAIN_API_KEY: str = Field(..., env="LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT: str = Field(..., env="LANGCHAIN_PROJECT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 설정 객체 인스턴스 생성
settings = Settings()
