from app.workers.celery_app import celery_app


def test_celery_app_uses_iems_namespace() -> None:
    assert celery_app.main == "iems_erp"
    assert celery_app.conf.task_default_queue == "iems-default"
