from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "IEMS ERP API"
    app_version: str = "0.1.0"
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    allowed_email_domain: str = Field(
        default="iemsnewdelhi.com",
        validation_alias="ALLOWED_EMAIL_DOMAIN",
    )
    director_email: str = Field(
        default="director@iemsnewdelhi.com",
        validation_alias="DIRECTOR_EMAIL",
    )
    supabase_url: str | None = Field(default=None, validation_alias="SUPABASE_URL")
    supabase_jwt_secret: str | None = Field(default=None, validation_alias="SUPABASE_JWT_SECRET")
    supabase_service_role_key: str | None = Field(
        default=None,
        validation_alias="SUPABASE_SERVICE_ROLE_KEY",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
