from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, model_validator

from workspace.entity.enums import Roles


class RegisterRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    email: EmailStr
    password: str

    @model_validator(mode="before")
    @classmethod
    def map_username_to_name(cls, values: dict) -> dict:
        if isinstance(values, dict):
            if values.get("username") and not values.get("name"):
                values["name"] = values["username"]
            elif values.get("name") and not values.get("username"):
                values["username"] = values["name"]
        return values


class RegisterResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: Roles = Roles.USER