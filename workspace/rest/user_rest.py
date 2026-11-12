import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from workspace.configs.db_config import get_db
from workspace.dto.register_dtos import RegisterRequest, RegisterResponse
from workspace.exceptions import UserAlreadyExistsException
from workspace.repos.user_repo import UserRepo

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)
def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepo:
    return UserRepo(db)

@auth_router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, user_repo: UserRepo = Depends(get_user_repository)):
    logger.info("Received registration request for email: %s", data.email)
    check_if_user_exists = await user_repo.get_user_by_email(data.email)
    if check_if_user_exists:
        logger.warning("Registration failed: User with email %s already exists", data.email)
        raise UserAlreadyExistsException
    else:
        hashed_password = hash_password(data.password)



