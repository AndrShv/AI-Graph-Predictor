from celery import Celery

from workspace.configs.settings import settings
celery_app = Celery(
    'tasks',
    broker=settings.rabbitmq_url,
    backend=settings.celery_result_backend,
    include=['workspace.services.ai_service'],
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Europe/Kyiv',
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

