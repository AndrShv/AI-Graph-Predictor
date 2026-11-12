from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    token: str
    token_type: str


class OAuthExchangeRequest(BaseModel):
    code: str
