import asyncio
import base64
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import requests
from sqlalchemy import select

from workspace.configs.celery_config import celery_app
from workspace.configs.db_config import _get_session_factory
from workspace.configs.settings import settings
from workspace.entity.db_models import AI_Response
from workspace.services.miniO import get_minio_client, get_minio_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert financial chart analysis engine.
Return only valid JSON with asset_pair, timeframe, analysis, historical_points
and forecast_points. Use integer pixel_x/pixel_y coordinates and numeric rates."""
DEFAULT_USER_PROMPT = (
    "Analyze this financial chart, extract historical price coordinates, "
    "and compute the forecast trajectory in strict JSON format."
)

_loop: asyncio.AbstractEventLoop | None = None
_loop_pid: int | None = None


def _run(coro):
    global _loop, _loop_pid
    pid = os.getpid()
    if _loop is None or _loop.is_closed() or _loop_pid != pid:
        _loop = asyncio.new_event_loop()
        _loop_pid = pid
        asyncio.set_event_loop(_loop)
    return _loop.run_until_complete(coro)


def _get_model_url() -> str:
    url = (settings.Qwen2_5_VL_3B_Instruct_URL or "").strip()
    if not url or "replace-with" in url or not url.startswith(("http://", "https://")):
        raise ValueError(
            f"Qwen2_5_VL_3B_Instruct_URL is not configured correctly: {url!r}"
        )
    return url


async def async_save_to_miniO(
        file_bytes: bytes,
        minio_service,
        content_type: str = "image/png",
) -> str:
    digest = hashlib.sha256(file_bytes).hexdigest()
    extension = ".jpg" if content_type == "image/jpeg" else ".png"
    file_key = f"charts/{digest}{extension}"
    await minio_service.save_file(file_bytes, file_key, content_type=content_type)
    return file_key


def _post_to_model(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        url,
        json=payload,
        headers={"ngrok-skip-browser-warning": "true"},
        timeout=(10, 300),
    )
    if not response.ok:
        raise RuntimeError(f"Model server {response.status_code}: {response.text[:800]}")
    return response.json()


async def process_file(file_bytes: bytes, prompt: str) -> dict[str, Any]:
    if not file_bytes:
        raise ValueError("File cannot be empty")

    url = _get_model_url()
    user_prompt = prompt.strip() if prompt else DEFAULT_USER_PROMPT
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser instruction: {user_prompt}"
    payload = {
        "image_base64": base64.b64encode(file_bytes).decode("utf-8"),
        "max_new_tokens": 1500,
        "prompt": full_prompt,
    }
    data = await asyncio.to_thread(_post_to_model, url, payload)

    if "response" not in data:
        raise ValueError("AI response does not contain response field")
    return {
        "response": data["response"],
        "input_tokens": data.get("prompt_tokens", len(full_prompt.split())),
        "output_tokens": data.get("completion_tokens", len(str(data["response"]).split())),
    }


async def _set_task_state(task_id: str, state: str, **values: Any) -> None:
    factory = _get_session_factory()
    user_id_raw = values.pop("user_id", None)
    user_id = uuid.UUID(str(user_id_raw)) if user_id_raw else None
    file_key = values.pop("file_key", None)
    prompt = values.pop("prompt", "")

    async with factory() as session:
        result = await session.scalars(select(AI_Response).where(AI_Response.task_id == task_id))
        record = result.first()

        if record is None:
            if not user_id or not file_key:
                logger.error("Cannot create AI_Response record: missing user_id or file_key for task_id %s", task_id)
                return
            record = AI_Response(
                task_id=task_id,
                user_id=user_id,
                file_key=file_key,
                prompt=prompt,
                status=state,
            )
            session.add(record)
        else:
            record.status = state

        for key, value in values.items():
            setattr(record, key, value)

        await session.commit()


async def process_both(task_id: str, file_key: str, user_id: str, prompt: str, file_name: str) -> dict[str, Any]:
    minio_service = get_minio_service(get_minio_client())
    await _set_task_state(
        task_id, "PROCESSING", user_id=user_id, file_key=file_key, prompt=prompt,
        started_at=datetime.now(timezone.utc),
    )
    try:
        file_bytes = await minio_service.get_file(file_key)
        result = await process_file(file_bytes, prompt)
        stored_response = result["response"]
        if not isinstance(stored_response, str):
            stored_response = json.dumps(stored_response)

        await _set_task_state(
            task_id, "COMPLETED", response=stored_response, finished_at=datetime.now(timezone.utc),
        )
        return result
    except Exception as exc:
        logger.exception("Error processing AI request in celery task")
        await _set_task_state(
            task_id, "FAILED", error=str(exc), finished_at=datetime.now(timezone.utc),
        )
        raise


@celery_app.task(bind=True, name="make_request_to_custom_ai", max_retries=3, default_retry_delay=60)
def make_request_to_custom_ai(self, data_for_ai: dict[str, str]):
    try:
        return _run(process_both(
            task_id=self.request.id,
            file_key=data_for_ai["file_key"],
            user_id=data_for_ai["user_id"],
            prompt=data_for_ai.get("prompt", ""),
            file_name=data_for_ai.get("file_name", data_for_ai["file_key"]),
        ))
    except ValueError:
        raise
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)