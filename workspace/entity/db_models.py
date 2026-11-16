import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    func,
    UUID,
    DateTime,
    Boolean,
    Enum as SQLEnum,
    String, TEXT)

from sqlalchemy.orm import Mapped, mapped_column

from workspace.configs.db_config import Base
from workspace.entity.enums import Roles


class AI_Response(Base):
    __tablename__ = "ai_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )

    prompt: Mapped[str] = mapped_column(TEXT, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    task_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    file_key: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    response: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


class DBUser(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )

    username: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), index=True, unique=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[Roles] = mapped_column(
        SQLEnum(Roles, native_enum=False), nullable=False, index=True, default=Roles.USER
    )


    reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
