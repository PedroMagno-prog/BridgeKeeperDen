from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, model_validator
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Aplicação ──────────────────────────────────────────────────────────────
    APP_NAME: str = "BridgeKeeper Den"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"

    # ── API ────────────────────────────────────────────────────────────────────
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # ── Auth / JWT ─────────────────────────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 horas

    # ── Banco de dados: partes individuais (desenvolvimento local) ─────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "bridgekeeper"

    # ── Banco de dados: URL completa opcional (nuvem) ──────────────────────────
    # Se DATABASE_URL for fornecida (ex: Neon, Supabase, Render), ela tem
    # prioridade. O prefixo é sanitizado automaticamente para asyncpg.
    DATABASE_URL: Optional[str] = None

    @model_validator(mode="after")
    def _resolve_database_url(self) -> "Settings":
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            # Normaliza prefixos comuns fornecidos por provedores de nuvem
            for old_prefix in ("postgres://", "postgresql://"):
                if url.startswith(old_prefix):
                    url = "postgresql+asyncpg://" + url[len(old_prefix):]
                    break
            
            # Converte sslmode= para ssl= (exigência do driver asyncpg)
            if "sslmode=" in url:
                url = url.replace("sslmode=", "ssl=")
                
            self.DATABASE_URL = url
        else:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self


settings = Settings()
