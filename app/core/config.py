from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Server Settings
    SERVER_ENV: str = "development"
    SERVER_PORT: int = 3000
    SERVER_HOST: str = "0.0.0.0"
    SERVER_ADDRESS: str = "http://localhost:3000"
    SERVER_DOCUMENT_PATH: str = "api"
    SERVER_TIMEZONE: str = "Asia/Ho_Chi_Minh"
    SERVER_DEFAULT_ADMIN_USERNAME: str = "admin"
    SERVER_DEFAULT_ADMIN_PASSWORD: str = "admin"

    # JWT Settings
    JWT_SECRET: str = "super_secret_jwt_key_change_in_prod"
    JWT_EXP: int = 86400  # 1 day in seconds
    JWT_REFRESH_SECRET: str = "super_secret_refresh_jwt_key"
    JWT_REFRESH_EXP: int = 604800  # 7 days in seconds
    JWT_ALGORITHM: str = "HS256"

    # PostgreSQL Database Settings
    SQL_TYPE: str = "postgres"
    SQL_HOST: str = "localhost"
    SQL_PORT: int = 5432
    SQL_USER: str = "postgres"
    SQL_PASSWORD: str = "postgres"
    SQL_SCHEMA: str = "public"
    SQL_DB: str = "aisoft_db"
    SQL_MAX_POOL: int = 20

    @property
    def postgres_async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.SQL_USER}:{self.SQL_PASSWORD}"
            f"@{self.SQL_HOST}:{self.SQL_PORT}/{self.SQL_DB}"
        )

    # MongoDB Settings
    MONGODB_URI: Optional[str] = None
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_USER: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None
    MONGODB_NAME: str = "aisoft_mongo"

    @property
    def mongo_async_url(self) -> str:
        if self.MONGODB_URI:
            return self.MONGODB_URI
        if self.MONGODB_USER and self.MONGODB_PASSWORD:
            return f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_NAME}?authSource=admin"
        return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_NAME}"

    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # MinIO Settings
    MINIO_ENDPOINT: str = "localhost"
    MINIO_PORT: int = 9000
    MINIO_USE_SSL: bool = False
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "aisoft-files"

    # Keycloak / SSO
    KEYCLOAK_AUTHORITY: Optional[str] = None
    KEYCLOAK_CLIENT_ID: Optional[str] = None
    KEYCLOAK_SECRET: Optional[str] = None
    SSO_JWKS_URI: Optional[str] = None  # Override auto-generated JWKS URI nếu cần

    # OneSignal
    ONE_SIGNAL_APP_ID: Optional[str] = None
    ONE_SIGNAL_API_KEY: Optional[str] = None

    # Microservices & Messaging
    MICROSERVICE_GRPC_HOST: str = "0.0.0.0"
    MICROSERVICE_GRPC_PORT: int = 3001
    MICROSERVICE_RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"


settings = Settings()
