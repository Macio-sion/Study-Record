from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache



class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    main_model: str = "qwen2.5:7b-instruct-q4_K_M"

    chat_model: str = "qwen3.5:0.8b"

    base_url: str | None = None

    local_base_url: str = "http://localhost:11434"

    temperature: float = 0.7

    model_provider: str = "ollama"

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0

    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    postgres_db: str = "resume_agent"
    postgres_user: str = "postgres"
    postgres_password: str = "root"

    # 鉴权（JWT）
    jwt_secret: str = "resume-agent-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 天

    # 上传文件在 Redis 中的暂存时长（秒）
    file_ttl_seconds: int = 3600

    # 跨域（前端 Vite 开发服务器）
    cors_origins: str = "*"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"host={self.postgres_host} port={self.postgres_port} "
            f"dbname={self.postgres_db} user={self.postgres_user} "
            f"password={self.postgres_password}"
        )

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
   
if __name__ == "__main__":
    settings1 = get_settings()
    settings2 = get_settings()
    print(settings1 is settings2)  # True
    print(settings1.model_name)  # qwen2.5:7b-instruct-q4_K_M
    print(settings1.model_provider)  # ollama
    