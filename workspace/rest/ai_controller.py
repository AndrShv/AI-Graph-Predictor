import logging

from uuid import UUID

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from workspace.helpers.file_validator import validate_file, validate_image_bytes
from workspace.configs.db_config import get_db
from workspace.entity.db_models import AI_Response
from workspace.services.ai_service import (
    async_save_to_miniO,
    make_request_to_custom_ai,
)
from workspace.services.miniO import get_minio_client, get_minio_service
from workspace.services.security_service import check_if_user_has_authentication

ai_router = APIRouter(prefix="/api/ai", tags=["AI"])
logger = logging.getLogger(__name__)




@ai_router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_graph(
    file: UploadFile = File(...),
    prompt: str = Form(default=""),
    auth_check: dict = Depends(check_if_user_has_authentication),
):
    logger.info("Received async graph analysis request for file: %s", file.filename)
    user_id = auth_check.get("sub") or auth_check.get("userId")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in authentication payload",
        )

    try:
        validate_file(file)
        file_bytes = await file.read()
        validate_image_bytes(file_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    try:
        file_key = await async_save_to_miniO(
            file_bytes,
            get_minio_service(get_minio_client()),
            content_type=file.content_type or "application/octet-stream",
        )
        created_task = make_request_to_custom_ai.delay({
            "file_key": file_key,
            "file_name": str(file.filename),
            "user_id": str(user_id),
            "prompt": prompt,
        })
    except Exception as exc:
        logger.exception("Failed to enqueue AI task")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to store file or enqueue analysis task",
        ) from exc
    return {
        "task_id": created_task.id,
        "status": "accepted",
        "message": "Your request is being processed. You can check the status using the task ID.",
    }


@ai_router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    auth_check: dict = Depends(check_if_user_has_authentication),
    db: AsyncSession = Depends(get_db),
):
    raw_user_id = auth_check.get("sub") or auth_check.get("userId")
    try:
        user_id = UUID(str(raw_user_id))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user identity") from exc

    result = await db.scalars(
        select(AI_Response).where(
            AI_Response.task_id == task_id,
            AI_Response.user_id == user_id,
        )
    )
    task = result.first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return {
        "task_id": task.task_id,
        "status": task.status,
        "file_key": task.file_key,
        "response": task.response,
        "error": task.error,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "finished_at": task.finished_at,
    }
