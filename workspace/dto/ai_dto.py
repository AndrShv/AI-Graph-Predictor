from pydantic import BaseModel


class AI_Request(BaseModel):
    file: bytes
    file_name: str
    file_path: str
    prompt: str