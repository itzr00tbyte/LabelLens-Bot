import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.bot.messages.renderers import MessageRenderer
from app.bot.middleware.access_control import ensure_user, render_access_denied_message
from app.database.repositories import SubmissionRepository, UserRepository
from app.database.session import get_db_session
from app.utils.callback_data import CallbackDataHelper

logger = logging.getLogger(__name__)


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed or not tg_id:
        if update.message:
            await update.message.reply_html(render_access_denied_message(tg_id))
        return

    await render_history_page(update, context, page=0, is_admin=is_admin, tg_id=tg_id)


async def handle_history_pagination(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed or not tg_id:
        await query.answer("Access denied.")
        return

    await query.answer()
    cb = CallbackDataHelper.decode(query.data)
    page = int(cb.target_id or "0")

    await render_history_page(
        update, context, page=page, is_admin=is_admin, tg_id=tg_id, is_callback=True
    )


async def render_history_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int,
    is_admin: bool,
    tg_id: int,
    is_callback: bool = False,
) -> None:
    per_page = 5
    async with get_db_session() as session:
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_telegram_id(tg_id)
        if not db_user:
            return

        sub_repo = SubmissionRepository(session)
        items, total = await sub_repo.get_user_submissions(
            db_user.id, limit=per_page, offset=page * per_page
        )

        text = MessageRenderer.render_history_list(
            items, total_count=total, page=page, per_page=per_page
        )

        rows = []
        nav_row = []
        if page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    "⬅️ Previous",
                    callback_data=CallbackDataHelper.encode("page:his", str(page - 1)),
                )
            )
        if (page + 1) * per_page < total:
            nav_row.append(
                InlineKeyboardButton(
                    "Next ➡️",
                    callback_data=CallbackDataHelper.encode("page:his", str(page + 1)),
                )
            )
        if nav_row:
            rows.append(nav_row)

        rows.append([
            InlineKeyboardButton(
                "🏠 Main Menu", callback_data=CallbackDataHelper.encode("menu:main")
            )
        ])
        kb = InlineKeyboardMarkup(rows)

        if is_callback and update.callback_query:
            await update.callback_query.edit_message_text(
                text, parse_mode="HTML", reply_markup=kb
            )
        elif update.message:
            await update.message.reply_html(text, reply_markup=kb)
