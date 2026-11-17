import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from workspace.entity.db_models import DBUser


class UserRepo:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_user_by_id(self, user_id: uuid.UUID) -> DBUser | None:
        result = await self.db_session.scalars(
            select(DBUser).where(DBUser.id == user_id)
        )
        return result.first()

    async def get_user_by_email(self, email: str) -> Optional[DBUser]:
        result = await self.db_session.scalars(
            select(DBUser).where(DBUser.email == email)
        )
        return result.first()

    async def create_user(self, user: DBUser) -> DBUser:
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user

    async def update_user(self, user: DBUser) -> DBUser:
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user

    async def delete(self, user: DBUser) -> None:
        await self.db_session.delete(user)
        await self.db_session.commit()


