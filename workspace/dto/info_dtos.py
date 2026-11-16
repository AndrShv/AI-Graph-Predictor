from uuid import UUID

from pydantic import BaseModel, EmailStr

from workspace.entity.enums import Roles


class InfoRequest(BaseModel):
    id: UUID

class InfoResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    created_at: str


class UpdateUserRequest(BaseModel):
    username: str
    email: EmailStr
    role: str
    password:str
    updated_at: str

class UpdateUserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: Roles
    created_at: str
    updated_at: str