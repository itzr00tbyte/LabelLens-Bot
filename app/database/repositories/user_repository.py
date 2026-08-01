from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database.models import User, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            # Update info if changed
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if display_name and user.display_name != display_name:
                user.display_name = display_name
                updated = True
            user.last_active_at = datetime.now(timezone.utc)
            if updated:
                await self.session.flush()
            return user

        role = UserRole.ADMIN if telegram_id in settings.ADMIN_TELEGRAM_IDS else UserRole.USER
        user = User(
            telegram_id=telegram_id,
            username=username,
            display_name=display_name,
            role=role,
            created_at=datetime.now(timezone.utc),
            last_active_at=datetime.now(timezone.utc),
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_last_active(self, telegram_id: int) -> None:
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(last_active_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)

    async def set_blocked(self, telegram_id: int, is_blocked: bool) -> bool:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return False
        user.is_blocked = is_blocked
        await self.session.flush()
        return True

    async def list_users(self, limit: int = 50, offset: int = 0) -> List[User]:
        stmt = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
