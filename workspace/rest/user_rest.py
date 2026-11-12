import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from workspace.configs.db_config import get_db
from workspace.dto.info_dtos import InfoResponse, UpdateUserResponse, UpdateUserRequest
from workspace.dto.login_dtos import LoginResponse, LoginRequest
from workspace.dto.register_dtos import RegisterRequest, RegisterResponse
from workspace.entity.db_models import DBUser
from workspace.entity.enums import Roles
from workspace.exceptions import UserAlreadyExistsException, InsufficientCredentialsException, UserNotFoundException
from workspace.repos.user_repo import UserRepo
from workspace.services.security_service import hash_password, verify_password, get_current_user
from workspace.utils.jwt_util import JwtUtil

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

        new_user = DBUser(
            id=uuid.uuid4(),
            email=data.email,
            password=hashed_password,
            username=data.username,
        )
        created_user = await user_repo.create_user(new_user)
        logger.info("user registered successfully")
        return created_user


@auth_router.post("/login", response_model=LoginResponse)
async def login( data: LoginRequest, user_repo: UserRepo = Depends(get_user_repository)):

    user = await user_repo.get_user_by_email(data.email)
    if not user or not verify_password(data.password, str(user.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    roles = getattr(user, "roles", ["USER"])

    jwt_token = JwtUtil.generate_token(
        user_id=user.id,
        email=user.email,
        roles=roles,
    )

    return {"token": jwt_token, "token_type": "bearer"}


@auth_router.get("/me", response_model=InfoResponse)
async def get_me(current_user: DBUser = Depends(get_current_user)):
    logger.info(f"current_user_id: {current_user.id}")
    return InfoResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=str(current_user.role),
        created_at=str(current_user.created_at),
    )



@auth_router.get("/{user_id}", response_model=InfoResponse)
async def get_user_by_id(user_id: uuid.UUID,
                         current_user: DBUser = Depends(get_current_user),
                         user_repo: UserRepo= Depends(get_user_repository),
                         ):
    logger.info(f"user_id: {user_id}, requester_id: {current_user.id}")
    if current_user.role != Roles.ADMIN.value:
        logger.warning(f"User {current_user.id} tried to access admin endpoint")
        raise InsufficientCredentialsException

    my_info = await user_repo.get_user_by_id(user_id)
    if my_info is None:
        logger.warning("user not found")
        raise UserNotFoundException

    return InfoResponse(
        id=uuid.UUID(str(my_info.id)),
        username=str(my_info.username),
        email=str(my_info.email),
        role=str(my_info.role),
        created_at=str(my_info.created_at),
    )


@auth_router.put("/{user_id}", response_model=UpdateUserResponse)
async def update_user_by_id(user_id: uuid.UUID,request: UpdateUserRequest,
                            current_user: DBUser = Depends(get_current_user),
                            user_repo: UserRepo = Depends(get_user_repository)
):
    logger.info(f"user_id: {user_id}")
    logger.info(f"current_user_id: {current_user.id}, current_user_role: {current_user.role}" )
    user = await user_repo.get_user_by_id(user_id)
    if user is None:
        logger.warning("user not found")
        raise UserNotFoundException
    if user_id != current_user.id and current_user.role != Roles.ADMIN.value:
        logger.warning("User has not enough authorities")
        raise InsufficientCredentialsException
    if request.username is not None:
        user.username = request.username

    if request.email is not None:
        user.email = request.email

    if request.password is not None:
        user.password = hash_password(request.password)

    if request.role is not None and current_user.role == Roles.ADMIN.value:
        try:
            user.role = Roles(request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {request.role}",
            )

    updated_user = await user_repo.update_user(user)
    logger.info("user updated successfully")
    return updated_user





