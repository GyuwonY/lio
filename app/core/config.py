from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from google.cloud import secretmanager
from google.api_core.exceptions import NotFound

class Settings(BaseSettings):
    # Environment settings
    APP_ENV: str = Field("local", env="APP_ENV")  # local or production
    GCP_PROJECT_ID: Optional[str] = Field(None, env="GCP_PROJECT_ID")

    # Database and Services
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    WEAVIATE_URL: str = Field(..., env="WEAVIATE_URL")
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    GOOGLE_API_KEY: str = Field(..., env="GOOGLE_API_KEY")

    # JWT Settings
    ACCESS_TOKEN_SECRET_KEY: str = Field(..., env="ACCESS_TOKEN_SECRET_KEY")
    REFRESH_TOKEN_SECRET_KEY: str = Field(..., env="REFRESH_TOKEN_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(
        60 * 24 * 7, env="REFRESH_TOKEN_EXPIRE_MINUTES"
    )

    # Google Auth
    GOOGLE_CLIENT_ID: str = Field(..., env="GOOGLE_CLIENT_ID")

    # API
    API_V1_STR: str = Field("/api/v1", env="API_V1_STR")

    def model_post_init(self, __context) -> None:
        if self.APP_ENV == "production":
            if not self.GCP_PROJECT_ID:
                raise ValueError(
                    "GCP_PROJECT_ID must be set in production environment."
                )


            client = secretmanager.SecretManagerServiceClient()

            # Settings 모델의 필드를 순회하며 시크릿을 가져옴
            for field_name in self.model_fields.keys():
                # 이미 값이 설정된 필드는 건너뛰기 (환경변수 우선)
                if getattr(self, field_name) is not None and field_name not in [
                    "GCP_PROJECT_ID",
                    "APP_ENV",
                ]:
                    continue

                secret_name = f"projects/{self.GCP_PROJECT_ID}/secrets/{field_name}/versions/latest"
                try:
                    response = client.access_secret_version(name=secret_name)
                    secret_value = response.payload.data.decode("UTF-8")
                    setattr(self, field_name, secret_value)
                except NotFound:
                    # 시크릿이 없어도 에러를 발생시키지 않고 넘어감 (선택적 설정일 수 있음)
                    print(
                        f"Warning: Secret '{field_name}' not found in GCP Secret Manager."
                    )
                except Exception as e:
                    print(f"Error fetching secret '{field_name}': {e}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 설정 객체 인스턴스 생성
settings = Settings()
