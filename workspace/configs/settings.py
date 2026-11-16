import secrets
from pathlib import Path
from typing import Optional, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / "proprts.env"


class Settings(BaseSettings):
    DEBUG: bool = False
    PROJECT_NAME: str = "ML Service Example"
    PORT: int = 8001
    LOG_LEVEL: str = "INFO"
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=("proprts.env", str(ENV_PATH)),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # --- PostgreSQL ---
    POSTGRES_USER: str = "root"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ml_service"
    DATABASE_URL: Optional[str] = None

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            if "?ssl=disable" not in url and "localhost" in url:
                url += "?ssl=disable"
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            f"?ssl=disable"
        )

    # --- RabbitMQ ---
    CLOUDAMQP_URL: Optional[str] = None
    RABBITMQ_URL: Optional[str] = None
    RABBIT_HOST: str = "localhost"
    RABBIT_PORT: int = 5672
    RABBIT_USERNAME: str = ""
    RABBIT_PASSWORD: str = ""
    MAIN_QUEUE_NAME: str = "ml.queue.main.queue"

    @property
    def rabbitmq_url(self) -> str:
        if self.CLOUDAMQP_URL:
            return self.CLOUDAMQP_URL
        if self.RABBITMQ_URL:
            return self.RABBITMQ_URL

        auth = ""
        if self.RABBIT_USERNAME or self.RABBIT_PASSWORD:
            auth = f"{self.RABBIT_USERNAME}:{self.RABBIT_PASSWORD}@"

        return f"amqp://{auth}{self.RABBIT_HOST}:{self.RABBIT_PORT}/"

    # --- Redis ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"rediss://default:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def celery_result_backend(self) -> str:
        scheme = "rediss" if self.REDIS_PASSWORD and self.REDIS_HOST not in {"localhost", "127.0.0.1", "redis"} else "redis"
        if self.REDIS_PASSWORD:
            return f"{scheme}://default:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/1"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"





    # --- Security & JWT ---
    JWT_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MS: int = 86400000
    JWT_REFRESH_EXPIRATION_MS: int = 172800000
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # --- MinIO ---
    MINIO_URL: str = "http://localhost:9000"
    MINIO_INTERNAL_ENDPOINT: str = "http://minio-s3:9000"
    MINIO_PUBLIC_ENDPOINT: str = "http://192.168.3.118:9090"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = "clothings"

    # --- Object Storage ---
    # Used for Cloudflare R2 in production and MinIO locally.
    ACCESS_KEY: str = ""
    SECRET_KEY: str = ""
    CLOUDFLARE_R2_ENDPOINT: str = ""
    USE_CLOUDFLARE_R2: bool = False

    def get_public_minio_url(self, image_key: str) -> str:
        if self.USE_CLOUDFLARE_R2 and self.ACCESS_KEY and self.SECRET_KEY:
            endpoint = self.CLOUDFLARE_R2_ENDPOINT.rstrip('/')
            bucket = self.MINIO_BUCKET.rstrip('/')
            key = image_key.lstrip('/')
            return f"{endpoint}/{bucket}/{key}"

        endpoint = self.MINIO_PUBLIC_ENDPOINT.rstrip('/')
        bucket = self.MINIO_BUCKET.rstrip('/')
        key = image_key.lstrip('/')
        return f"{endpoint}/{bucket}/{key}"

    def security_warnings(self) -> List[str]:
        warnings: List[str] = []

        if len(self.JWT_SECRET) < 32:
            warnings.append("JWT_SECRET is too short")

        if self.POSTGRES_PASSWORD == "":
            warnings.append("POSTGRES_PASSWORD is empty")

        if self.RABBIT_USERNAME == "" or self.RABBIT_PASSWORD == "":
            warnings.append("RabbitMQ credentials are empty")

        if self.USE_CLOUDFLARE_R2:
            if self.ACCESS_KEY == "" or self.SECRET_KEY == "":
                warnings.append("Cloudflare R2 credentials are empty")
        elif self.MINIO_ACCESS_KEY == "" or self.MINIO_SECRET_KEY == "":
            warnings.append("MinIO credentials are empty")



        return warnings
settings = Settings()
