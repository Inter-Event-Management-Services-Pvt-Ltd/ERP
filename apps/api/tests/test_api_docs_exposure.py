from app.core.config import Settings
from app.main import docs_url, openapi_url, redoc_url


def test_api_docs_enabled_by_default_for_development() -> None:
    settings = Settings(APP_ENV="development")

    assert settings.expose_api_docs is True


def test_api_docs_disabled_by_default_for_staging_and_production() -> None:
    assert Settings(APP_ENV="staging").expose_api_docs is False
    assert Settings(APP_ENV="production").expose_api_docs is False


def test_api_docs_can_be_explicitly_enabled_for_non_production_debugging() -> None:
    settings = Settings(APP_ENV="staging", ENABLE_API_DOCS=True)

    assert settings.expose_api_docs is True


def test_current_test_app_keeps_docs_available_for_local_contract_debugging() -> None:
    assert docs_url == "/docs"
    assert redoc_url == "/redoc"
    assert openapi_url == "/openapi.json"
