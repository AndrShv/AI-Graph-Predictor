from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr

from workspace.entity.enums import Roles


class RegisterRequest(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    password: str

class RegisterResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: Roles = Roles.USER