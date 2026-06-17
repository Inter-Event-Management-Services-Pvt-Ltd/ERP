import logging

from app.core.logging import configure_logging


def test_configure_logging_suppresses_noisy_http_client_logs() -> None:
    configure_logging("INFO")

    assert logging.getLogger("httpx").level >= logging.WARNING
    assert logging.getLogger("httpcore").level >= logging.WARNING
    assert logging.getLogger("iems.api.access").getEffectiveLevel() == logging.INFO
    assert logging.getLogger("iems.api.supabase").getEffectiveLevel() == logging.INFO
