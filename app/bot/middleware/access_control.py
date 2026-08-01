from typing import Tuple
from telegram import Update
from app.config import settings
from app.database.repositories import UserRepository
from app.database.session import get_db_session


async def ensure_user(update: Update) -> Tuple[bool, bool, Optional[int]]:
    """
    Checks if user is registered, not blocked, and returns (is_allowed, is_admin, telegram_id).
    """
    tg_user = update.effective_user
    if not tg_user:
        return False, False, None

    async with get_db_session() as session:
        repo = UserRepository(session)
        user = await repo.get_or_create(
            telegram_id=tg_user.id,
            username=tg_user.username,
            display_name=tg_user.full_name,
        )
        
        if user.is_blocked:
            return False, False, tg_user.id

        is_admin = (user.role == "admin") or (tg_user.id in settings.ADMIN_TELEGRAM_IDS)
        return True, is_admin, tg_user.id
