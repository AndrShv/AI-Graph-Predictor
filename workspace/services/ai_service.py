import asyncio

from workspace.configs.celery_config import celery_app


async def process_file(file_bytes: bytes):
    """Process uploaded file bytes and optionally send them to MinIO/AI."""
    # TODO: use file_bytes in the custom AI request or MiniO_Service.uplaod_file().
    return len(file_bytes)

@celery_app.task(bind=True, name="make_request_to_custom_ai", max_retries=3, default_retry_delay=60)
def make_request_to_custom_ai(self, file_bytes: bytes):
    try:
        return asyncio.run(process_file(file_bytes))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


