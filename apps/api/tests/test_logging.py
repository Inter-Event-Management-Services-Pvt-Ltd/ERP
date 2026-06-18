import logging

from app.core.logging import configure_logging


def test_configure_logging_keeps_http_client_logs_visible() -> None:
    configure_logging("INFO")

    assert logging.getLogger("httpx").getEffectiveLevel() == logging.INFO
    assert logging.getLogger("httpcore").getEffectiveLevel() == logging.INFO
    assert logging.getLogger("iems.api.access").getEffectiveLevel() == logging.INFO
    assert logging.getLogger("iems.api.supabase").getEffectiveLevel() == logging.INFO
