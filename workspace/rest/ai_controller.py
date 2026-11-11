import logging
import os
import tempfile

from fastapi import APIRouter, UploadFile, File
from starlette import status

from workspace.services.ai_service import make_request_to_custom_ai

ai_router = APIRouter(prefix="/api/ai", tags=["AI"])
logger = logging.getLogger(__name__)


@ai_router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_graph(file: UploadFile = File(...)):
    logger.info("Received async graph analysis request for file: %s", file.filename)
    if file is None:
        logger.error("No file provided for analysis.")
        return {"error": "No file provided."}
    file_suffix = os.path.splitext(file.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as temporary_file:
        temporary_file.write(await file.read())
        file_path = temporary_file.name

    created_task = make_request_to_custom_ai.delay(file_path)
    return {"task_id": created_task.id, "status": "accepted"}
