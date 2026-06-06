from celery import Celery  # type: ignore[import-untyped]

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "iems_erp",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_default_queue="iems-default",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    imports=("app.workers.archive_exports",),
)


def healthcheck() -> str:
    return "ok"


celery_app.task(name="iems.healthcheck")(healthcheck)
