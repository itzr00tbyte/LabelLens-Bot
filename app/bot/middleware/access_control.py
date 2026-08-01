from typing import Optional, Tuple
from telegram import Update
from app.config import settings
from app.database.models import UserRole
from app.database.repositories import UserRepository
from app.database.session import get_db_session


async def ensure_user(update: Update) -> Tuple[bool, bool, Optional[int]]:
    """
    Checks if user is registered, approved, and returns (is_allowed, is_admin, telegram_id).
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

        is_admin = (user.role == UserRole.ADMIN) or (tg_user.id in settings.ADMIN_TELEGRAM_IDS)

        if is_admin:
            # Admins are always approved and allowed
            if not getattr(user, "is_approved", True):
                user.is_approved = True
                user.is_blocked = False
                await session.flush()
            return True, True, tg_user.id

        if getattr(user, "is_blocked", False):
            return False, False, tg_user.id

        # Non-admin user must be explicitly approved
        is_approved = getattr(user, "is_approved", False)
        return is_approved, False, tg_user.id


def render_access_denied_message(telegram_id: Optional[int]) -> str:
    tg_id_str = str(telegram_id) if telegram_id else "Unknown"
    return (
        f"╭────── ⛔ <b>Access Restricted</b> ──────╮\n"
        f"\n"
        f"  🆔  <b>Your Telegram ID</b>\n"
        f"  <code>{tg_id_str}</code>\n"
        f"\n"
        f"  🔒  <b>Approval Required</b>\n"
        f"  You must be approved by an administrator\n"
        f"  before using this bot.\n"
        f"\n"
        f"  💡  <b>Admin Command:</b>\n"
        f"  An admin can approve you by running:\n"
        f"  <code>/approve {tg_id_str}</code>\n"
        f"\n"
        f"╰──────────────────────────────────╯"
    )
