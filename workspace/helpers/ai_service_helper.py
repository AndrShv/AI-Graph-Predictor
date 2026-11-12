import asyncio

from workspace.dto.ai_request import AI_Request
from workspace.services.ai_service import async_save_to_miniO, process_file


async def process_both(data: AI_Request):
    await asyncio.gather(
        async_save_to_miniO(data.file),
        process_file(data.file, str(data.file_name), str(data.file_path))
    )