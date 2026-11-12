from uuid import UUID
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import InvalidTokenError
from starlette import status

from workspace.configs.settings import settings

security_bearer = HTTPBearer()

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def filter_request(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> UUID:
    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        raw_user_id: Optional[str] = (
            payload.get("sub") or payload.get("user_id") or payload.get("userId")
        )
        if raw_user_id is None:
            raise credentials_exception
        return UUID(str(raw_user_id))
    except (InvalidTokenError, ValueError):
        raise credentials_exception

