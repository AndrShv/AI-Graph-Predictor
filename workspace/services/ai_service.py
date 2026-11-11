import asyncio
import os

from workspace.configs.celery_config import celery_app


async def process_file(file_path: str):
    """Process a file saved by the API before it was sent to Celery."""
    # TODO: add the custom AI request here.
    return file_path

@celery_app.task(bind=True, name="make_request_to_custom_ai", max_retries=3, default_retry_delay=60)
def make_request_to_custom_ai(self, file_path: str):
    try:
        return asyncio.run(process_file(file_path))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


