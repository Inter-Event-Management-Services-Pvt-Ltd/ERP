from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
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
    allowed_email_domains: str | None = Field(
        default=None,
        validation_alias="ALLOWED_EMAIL_DOMAINS",
    )
    cors_allowed_origins: str = Field(
        default="http://localhost:3000",
        validation_alias="CORS_ALLOWED_ORIGINS",
    )
    enable_api_docs: bool = Field(default=False, validation_alias="ENABLE_API_DOCS")
    director_email: str = Field(
        default="director@iemsnewdelhi.com",
        validation_alias="DIRECTOR_EMAIL",
    )
    supabase_url: str | None = Field(default=None, validation_alias="SUPABASE_URL")
    supabase_jwt_audience: str = Field(
        default="authenticated",
        validation_alias="SUPABASE_JWT_AUDIENCE",
    )
    supabase_jwt_secret: str | None = Field(default=None, validation_alias="SUPABASE_JWT_SECRET")
    supabase_jwt_secret_file: str | None = Field(
        default=None,
        validation_alias="SUPABASE_JWT_SECRET_FILE",
    )
    supabase_auth_issuer_override: str | None = Field(
        default=None,
        validation_alias="SUPABASE_AUTH_ISSUER",
    )
    supabase_auth_issuer_aliases: str | None = Field(
        default=None,
        validation_alias="SUPABASE_AUTH_ISSUER_ALIASES",
    )
    supabase_jwks_url_override: str | None = Field(
        default=None,
        validation_alias="SUPABASE_JWKS_URL",
    )
    supabase_service_role_key: str | None = Field(
        default=None,
        validation_alias="SUPABASE_SERVICE_ROLE_KEY",
    )
    supabase_service_role_key_file: str | None = Field(
        default=None,
        validation_alias="SUPABASE_SERVICE_ROLE_KEY_FILE",
    )
    supabase_request_timeout_seconds: float = Field(
        default=5.0,
        validation_alias="SUPABASE_REQUEST_TIMEOUT_SECONDS",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    rate_limit_enabled: bool = Field(default=True, validation_alias="RATE_LIMIT_ENABLED")
    rate_limit_window_seconds: int = Field(
        default=60,
        validation_alias="RATE_LIMIT_WINDOW_SECONDS",
    )
    rate_limit_default_requests: int = Field(
        default=120,
        validation_alias="RATE_LIMIT_DEFAULT_REQUESTS",
    )
    rate_limit_auth_requests: int = Field(
        default=30,
        validation_alias="RATE_LIMIT_AUTH_REQUESTS",
    )
    rate_limit_upload_requests: int = Field(
        default=20,
        validation_alias="RATE_LIMIT_UPLOAD_REQUESTS",
    )
    rate_limit_export_requests: int = Field(
        default=10,
        validation_alias="RATE_LIMIT_EXPORT_REQUESTS",
    )
    rate_limit_admin_requests: int = Field(
        default=60,
        validation_alias="RATE_LIMIT_ADMIN_REQUESTS",
    )
    rate_limit_trust_proxy_headers: bool = Field(
        default=True,
        validation_alias="RATE_LIMIT_TRUST_PROXY_HEADERS",
    )
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="CELERY_BROKER_URL",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        validation_alias="CELERY_RESULT_BACKEND",
    )
    signed_url_ttl_seconds: int = Field(default=900, validation_alias="SIGNED_URL_TTL_SECONDS")
    archive_export_ttl_hours: int = Field(default=24, validation_alias="ARCHIVE_EXPORT_TTL_HOURS")
    max_upload_bytes: int = Field(default=104_857_600, validation_alias="MAX_UPLOAD_BYTES")
    allowed_upload_mime_types: str = Field(
        default=(
            "application/pdf,image/jpeg,image/png,text/plain,"
            "application/msword,"
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
            "application/vnd.ms-excel,"
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        validation_alias="ALLOWED_UPLOAD_MIME_TYPES",
    )
    project_documents_bucket: str = Field(
        default="project-documents",
        validation_alias="PROJECT_DOCUMENTS_BUCKET",
    )
    generated_archives_bucket: str = Field(
        default="generated-archives",
        validation_alias="GENERATED_ARCHIVES_BUCKET",
    )
    module_projects_enabled: bool = Field(
        default=True,
        validation_alias="MODULE_PROJECTS_ENABLED",
    )
    module_documents_enabled: bool = Field(
        default=True,
        validation_alias="MODULE_DOCUMENTS_ENABLED",
    )
    module_archive_exports_enabled: bool = Field(
        default=True,
        validation_alias="MODULE_ARCHIVE_EXPORTS_ENABLED",
    )
    module_physical_archive_enabled: bool = Field(
        default=True,
        validation_alias="MODULE_PHYSICAL_ARCHIVE_ENABLED",
    )
    module_attendance_enabled: bool = Field(
        default=True,
        validation_alias="MODULE_ATTENDANCE_ENABLED",
    )
    module_leave_enabled: bool = Field(default=True, validation_alias="MODULE_LEAVE_ENABLED")
    module_tasks_enabled: bool = Field(default=True, validation_alias="MODULE_TASKS_ENABLED")
    module_calendar_enabled: bool = Field(
        default=True,
        validation_alias="MODULE_CALENDAR_ENABLED",
    )
    module_approvals_enabled: bool = Field(
        default=True,
        validation_alias="MODULE_APPROVALS_ENABLED",
    )
    module_director_dashboard_enabled: bool = Field(
        default=True,
        validation_alias="MODULE_DIRECTOR_DASHBOARD_ENABLED",
    )
    module_admin_enabled: bool = Field(default=True, validation_alias="MODULE_ADMIN_ENABLED")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @model_validator(mode="after")
    def load_file_backed_secrets(self) -> "Settings":
        if self.supabase_jwt_secret is None or self.supabase_jwt_secret.strip() == "":
            self.supabase_jwt_secret = _read_secret_file(self.supabase_jwt_secret_file)
        if (
            self.supabase_service_role_key is None
            or self.supabase_service_role_key.strip() == ""
        ):
            self.supabase_service_role_key = _read_secret_file(
                self.supabase_service_role_key_file,
            )
        return self

    @property
    def supabase_auth_issuer(self) -> str | None:
        if self.supabase_auth_issuer_override is not None:
            return self.supabase_auth_issuer_override.rstrip("/")
        if self.supabase_url is None:
            return None
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    @property
    def supabase_jwks_url(self) -> str | None:
        if self.supabase_jwks_url_override is not None:
            return self.supabase_jwks_url_override.rstrip("/")
        if self.supabase_auth_issuer is None:
            return None
        return f"{self.supabase_auth_issuer}/.well-known/jwks.json"

    @property
    def supabase_auth_issuer_list(self) -> tuple[str, ...]:
        issuers: list[str] = []
        if self.supabase_auth_issuer is not None:
            issuers.append(self.supabase_auth_issuer)
        issuers.extend(_csv_values(self.supabase_auth_issuer_aliases))
        return tuple(dict.fromkeys(issuer.rstrip("/") for issuer in issuers))

    @property
    def allowed_email_domain_list(self) -> tuple[str, ...]:
        configured_domains = _csv_values(self.allowed_email_domains)
        fallback_domains = _csv_values(self.allowed_email_domain)
        domains = configured_domains or fallback_domains
        return tuple(domain.lower().lstrip("@") for domain in domains)

    @property
    def cors_allowed_origin_list(self) -> tuple[str, ...]:
        return _csv_values(self.cors_allowed_origins)

    @property
    def expose_api_docs(self) -> bool:
        return self.enable_api_docs or self.app_env.lower() in {"development", "local", "test"}

    @property
    def allowed_upload_mime_type_set(self) -> frozenset[str]:
        return frozenset(_csv_values(self.allowed_upload_mime_types))

    @property
    def module_flags(self) -> dict[str, bool]:
        return {
            "projects": self.module_projects_enabled,
            "documents": self.module_documents_enabled,
            "archive_exports": self.module_archive_exports_enabled,
            "physical_archive": self.module_physical_archive_enabled,
            "attendance": self.module_attendance_enabled,
            "leave": self.module_leave_enabled,
            "tasks": self.module_tasks_enabled,
            "calendar": self.module_calendar_enabled,
            "approvals": self.module_approvals_enabled,
            "director_dashboard": self.module_director_dashboard_enabled,
            "admin": self.module_admin_enabled,
        }


def _csv_values(raw_value: str | None) -> tuple[str, ...]:
    if raw_value is None:
        return ()
    return tuple(value.strip() for value in raw_value.split(",") if value.strip())


def _read_secret_file(path_value: str | None) -> str | None:
    if path_value is None or path_value.strip() == "":
        return None
    secret_value = Path(path_value).read_text(encoding="utf-8").strip()
    if not secret_value:
        raise ValueError(f"Secret file is empty: {path_value}")
    return secret_value


@lru_cache
def get_settings() -> Settings:
    return Settings()
