import asyncio
import base64
import logging

import requests

from workspace.configs.celery_config import celery_app
from workspace.dto.ai_dto import AI_Request
from workspace.services.miniO import get_minio_client, get_minio_service

logger = logging.getLogger(__name__)

CLOUD_URL = "https://knox-exopoditic-azalea.ngrok-free.dev/generate-qwen2.5-vl"
SYSTEM_PROMPT = """
You are an expert quantitative financial analyst and computer vision chart-digitization engine.
Your task is to analyze the provided financial chart image, digitize visible price action, and generate a forecast trajectory based on the user's request.

CRITICAL RULES:
1. Output MUST be strictly valid JSON matching the exact schema below. Do NOT wrap the JSON in markdown code blocks (no ```json or ```), and do NOT include any conversational text before or after the JSON.
2. Pixel Coordinates System:
   - Origin (0, 0) is at the TOP-LEFT corner of the image.
   - X increases to the right; Y increases downwards.
   - All `pixel_x` and `pixel_y` values must be integers within the provided image dimensions (`width` x `height`).
   - `forecast_pixels` MUST start seamlessly from the last visible price point on the chart and extend into the future/right area.
3. Digitization (`historical_points`):
   - Extract key turning points, highs, lows, and regular intervals along the visible price curve.
   - Map them accurately to the chart's Y-axis (price/rate) and X-axis (timestamp/label). If exact timestamps are obscured, infer logical sequential labels.

REQUIRED JSON SCHEMA:
{
  "asset_pair": "string (e.g., 'USD/EUR' or 'UNKNOWN')",
  "timeframe": "string (e.g., '1H', '1D', or 'UNKNOWN')",
  "analysis": {
    "trend": "BULLISH | BEARISH | SIDEWAYS",
    "support_levels": [float],
    "resistance_levels": [float],
    "summary": "string (detailed technical reasoning based on chart patterns, indicators, and user prompt)"
  },
  "historical_points": [
    {
      "timestamp": "string",
      "rate": float,
      "pixel_x": int,
      "pixel_y": int
    }
  ],
  "forecast_points": [
    {
      "timestamp": "string",
      "predicted_rate": float,
      "pixel_x": int,
      "pixel_y": int
    }
  ]
}
""".strip()

DEFAULT_USER_PROMPT = "Analyze this financial chart, extract dense historical price coordinates, and compute the forecast trajectory in strict JSON format."


async def async_save_to_miniO(file_bytes: bytes, minio_service):
    file_key = "file_" + str(hash(file_bytes)) + ".png"
    await minio_service.save_file(file_bytes, file_key)
    return file_key


async def process_file(file_bytes: bytes, file_name: str, file_path: str, prompt: str) -> dict:
    logger.info(f"Processing file: {file_name} at path: {file_path}")
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("File cannot be empty")

    user_prompt = prompt.strip() if prompt else DEFAULT_USER_PROMPT
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser instruction: {user_prompt}"

    try:
        encoded_image = base64.b64encode(file_bytes).decode('utf-8')

        response = requests.post(
            CLOUD_URL,
            json={
                "image_base64": encoded_image,
                "max_new_tokens": 1500,
                "prompt": full_prompt
            },
            timeout=90
        )

        response.raise_for_status()
        data = response.json()
        if "response" not in data:
            raise KeyError(f"Response missing 'response' key. Available keys: {list(data.keys())}")
        return {
            "response": data["response"],
            "input_tokens": data.get("prompt_tokens", len(full_prompt.split())),
            "output_tokens": data.get("completion_tokens", len(data["response"].split()))
        }

    except Exception as e:
        logger.error(f"Ошибка при запросе к модели: {e}")
        raise


async def process_both(data: AI_Request):
    get_file, get_file_name, get_file_path = data.file, str(data.file_name), str(data.file_path)
    user_prompt = data.prompt.strip() if data.prompt else DEFAULT_USER_PROMPT
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser instruction: {user_prompt}"

    await asyncio.gather(
        async_save_to_miniO(get_file, get_minio_service(get_minio_client())),
        process_file(get_file, get_file_name, get_file_path, full_prompt)
    )



@celery_app.task(bind=True, name="make_request_to_custom_ai", max_retries=3, default_retry_delay=60)
def make_request_to_custom_ai(self, data_for_ai: AI_Request):
    try:
        return asyncio.run(process_both(data_for_ai))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
