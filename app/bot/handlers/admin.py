import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.bot.middleware.access_control import ensure_user
from app.database.repositories import UserRepository
from app.database.session import get_db_session

logger = logging.getLogger(__name__)


async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command: /approve <telegram_id>"""
    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed or not is_admin:
        if update.message:
            await update.message.reply_html("⛔ <b>Unauthorized:</b> Admin access required.")
        return

    if not context.args or not context.args[0].isdigit():
        if update.message:
            await update.message.reply_html(
                "💡 <b>Usage:</b> <code>/approve &lt;telegram_id&gt;</code>\n"
                "Example: <code>/approve 123456789</code>"
            )
        return

    target_id = int(context.args[0])

    async with get_db_session() as session:
        repo = UserRepository(session)
        user = await repo.approve_user(target_id)

    logger.info("Admin %s approved user %s", tg_id, target_id)
    if update.message:
        await update.message.reply_html(
            f"✅ <b>User Approved!</b>\n\n"
            f"  🆔  <b>Telegram ID:</b> <code>{target_id}</code>\n"
            f"  👤  <b>Name:</b> {user.display_name or 'N/A'}\n"
            f"  🏷️  <b>Status:</b> Approved & Allowed"
        )


async def disapprove_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command: /disapprove <telegram_id> or /revoke <telegram_id>"""
    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed or not is_admin:
        if update.message:
            await update.message.reply_html("⛔ <b>Unauthorized:</b> Admin access required.")
        return

    if not context.args or not context.args[0].isdigit():
        if update.message:
            await update.message.reply_html(
                "💡 <b>Usage:</b> <code>/disapprove &lt;telegram_id&gt;</code>\n"
                "Example: <code>/disapprove 123456789</code>"
            )
        return

    target_id = int(context.args[0])

    async with get_db_session() as session:
        repo = UserRepository(session)
        user = await repo.disapprove_user(target_id)

    logger.info("Admin %s disapproved user %s", tg_id, target_id)
    if update.message:
        await update.message.reply_html(
            f"🚫 <b>User Disapproved!</b>\n\n"
            f"  🆔  <b>Telegram ID:</b> <code>{target_id}</code>\n"
            f"  👤  <b>Name:</b> {user.display_name or 'N/A'}\n"
            f"  🏷️  <b>Status:</b> Revoked & Disapproved"
        )


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command: /users - Lists registered users and approval status"""
    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed or not is_admin:
        if update.message:
            await update.message.reply_html("⛔ <b>Unauthorized:</b> Admin access required.")
        return

    async with get_db_session() as session:
        repo = UserRepository(session)
        users = await repo.list_users(limit=50)

    if not users:
        if update.message:
            await update.message.reply_html("📋 <b>User List</b>\n\nNo registered users found.")
        return

    lines = [
        "╭──────── 📋 <b>User Directory</b> ────────╮",
        "",
        f"  Total Users: <b>{len(users)}</b>",
        "",
    ]

    for user in users:
        if user.role.value == "admin":
            badge = "👑 Admin"
        elif user.is_approved:
            badge = "✅ Approved"
        else:
            badge = "⏳ Pending/Disapproved"

        name_str = f" ({user.display_name})" if user.display_name else ""
        lines.append(f"  • <code>{user.telegram_id}</code>{name_str} — {badge}")

    lines.append("")
    lines.append("╰──────────────────────────────────╯")

    if update.message:
        await update.message.reply_html("\n".join(lines))
