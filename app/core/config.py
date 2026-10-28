from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Taller Mecánico API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    POSTGRES_HOST: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_PORT: int = 5432
    POOL_SIZE: int = 10

    DEBUG: bool = False
    SQL_ECHO: bool = False
    DATABASE_URL: str | None = None

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    SECRET_KEY: str = Field(min_length=1)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    BCRYPT_ROUNDS: int = 12

    FIRST_ADMIN_EMAIL: str = "admin@taller.com"
    FIRST_ADMIN_PASSWORD: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validar_componentes(self) -> "Settings":
        if self.DATABASE_URL:
            return self
        faltantes = [
            nombre
            for nombre in (
                "POSTGRES_HOST",
                "POSTGRES_USER",
                "POSTGRES_PASSWORD",
                "POSTGRES_DB",
            )
            if not getattr(self, nombre)
        ]
        if faltantes:
            raise ValueError(
                "Faltan variables de base de datos: " + ", ".join(faltantes)
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid"
    )


settings = Settings()