import asyncio
import logging

import requests

from workspace.configs.celery_config import celery_app
from workspace.services.miniO import MiniO_Service as miniO_service

logger = logging.getLogger(__name__)

CLOUD_URL = "https://knox-exopoditic-azalea.ngrok-free.dev/generate-cloud"

prompt =  ""

async def async_save_to_miniO(file_bytes: bytes):
    file_key = "file_" + str(file_bytes.__hash__()) + ".png"

    await miniO_service.uplaod_file(file_bytes, file_key)

async def process_file(file_bytes: bytes):
    logger.info("Processing file of size: %d bytes", len(file_bytes))
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("File cannot be empty")



    try:
        response = requests.post(
            CLOUD_URL,
            json={"image": file_bytes, "max_new_tokens": 1000},
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        if "response" not in data:
            raise KeyError(f"Response missing 'response' key. Available keys: {list(data.keys())}")
        return {
        "response": data["response"],
        "input_tokens": data.get("prompt_tokens", len(prompt.split())),
        "output_tokens": data.get("completion_tokens", len(data["response"].split()))
    }

    except Exception as e:
        logger.error(f"Ошибка при запросе к модели: {e}")
        raise


@celery_app.task(bind=True, name="make_request_to_custom_ai", max_retries=3, default_retry_delay=60)
def make_request_to_custom_ai(self, file_bytes: bytes):
    try:
        return asyncio.run(process_file(file_bytes), async_save_to_miniO(file_bytes))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
