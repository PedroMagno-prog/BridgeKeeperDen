import json
from typing import List, Optional, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Aplicação ──────────────────────────────────────────────────────────────
    APP_NAME: str = "BridgeKeeper Den"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"

    # ── API ────────────────────────────────────────────────────────────────────
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(origin).strip().rstrip("/") for origin in parsed if origin]
                except Exception:
                    pass
            return [origin.strip().rstrip("/") for origin in v_str.split(",") if origin.strip()]
        elif isinstance(v, list):
            return [str(origin).strip().rstrip("/") for origin in v if origin]
        return v

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
    # Se DATABASE_URL for fornecida (ex: Neon, Supabase, Render, CockroachDB), ela tem
    # prioridade. O prefixo é sanitizado automaticamente para o driver async correto.
    DATABASE_URL: Optional[str] = None

    @model_validator(mode="after")
    def _resolve_database_url(self) -> "Settings":
        if self.DATABASE_URL:
            url = str(self.DATABASE_URL).strip()
            
            # Se a string veio vazia ou com espaços
            if not url:
                self.DATABASE_URL = (
                    f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                    f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
                )
                return self

            # Identifica se a conexão é com cluster CockroachDB
            is_cockroach = (
                "cockroach" in url.lower() 
                or ":26257" in url 
                or url.startswith("cockroachdb")
            )

            # Remove qualquer prefixo existente para re-adicionar o driver async correto
            for old_prefix in (
                "cockroachdb+asyncpg://",
                "cockroachdb://",
                "postgresql+asyncpg://",
                "postgresql://",
                "postgres://",
            ):
                if url.startswith(old_prefix):
                    url = url[len(old_prefix):]
                    break

            # Converte sslmode= para ssl= (exigência do driver asyncpg)
            if "sslmode=" in url:
                url = url.replace("sslmode=", "ssl=")

            if is_cockroach:
                self.DATABASE_URL = "cockroachdb+asyncpg://" + url
            else:
                self.DATABASE_URL = "postgresql+asyncpg://" + url
        else:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self


settings = Settings()
