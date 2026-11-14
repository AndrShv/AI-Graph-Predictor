import logging

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from starlette import status

from workspace.dto.ai_dto import AI_Request
from workspace.helpers.file_validator import validate_file, validate_image_bytes
from workspace.services.ai_service import make_request_to_custom_ai
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

    ai_request = AI_Request(
        file=file_bytes,
        file_name=str(file.filename),
        file_path=str(file.filename),
        prompt=prompt,
    )

    created_task = make_request_to_custom_ai.delay(ai_request)
    return {
        "task_id": created_task.id,
        "status": "accepted",
        "message": "Your request is being processed. You can check the status using the task ID.",
    }
