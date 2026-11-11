import logging

from fastapi import APIRouter, UploadFile, File
from starlette import status

from workspace.helpers.file_validator import validate_file, validate_image_bytes
from workspace.services.ai_service import make_request_to_custom_ai

ai_router = APIRouter(prefix="/api/ai", tags=["AI"])
logger = logging.getLogger(__name__)


@ai_router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_graph(file: UploadFile = File(...)):
    logger.info("Received async graph analysis request for file: %s", file.filename)
    try:
        validate_file(file)
        file_bytes = await file.read()
        validate_image_bytes(file_bytes)
    except ValueError as exc:
        logger.warning("Invalid uploaded file: %s", exc)
        return {"error": str(exc)}

    created_task = make_request_to_custom_ai.delay(file_bytes)
    return {
        "task_id": created_task.id,
        "status": "accepted"
    }
