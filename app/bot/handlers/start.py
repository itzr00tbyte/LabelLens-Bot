import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.bot.messages.renderers import MessageRenderer
from app.bot.middleware.access_control import ensure_user, render_access_denied_message

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed:
        if update.message:
            await update.message.reply_html(render_access_denied_message(tg_id))
        return

    name = update.effective_user.first_name if update.effective_user else ""
    text = MessageRenderer.render_start_message(name)
    kb = get_main_menu_keyboard(is_admin=is_admin)

    if update.message:
        await update.message.reply_html(text, reply_markup=kb)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed:
        if update.message:
            await update.message.reply_html(render_access_denied_message(tg_id))
        return
    text = MessageRenderer.render_help_message()
    kb = get_main_menu_keyboard(is_admin=is_admin)
    if update.message:
        await update.message.reply_html(text, reply_markup=kb)


async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed:
        if update.message:
            await update.message.reply_html(render_access_denied_message(tg_id))
        return
    text = MessageRenderer.render_privacy_message()
    kb = get_main_menu_keyboard(is_admin=is_admin)
    if update.message:
        await update.message.reply_html(text, reply_markup=kb)


async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed:
        if update.message:
            await update.message.reply_html(render_access_denied_message(tg_id))
        return
    text = MessageRenderer.render_upload_instructions()
    if update.message:
        await update.message.reply_html(text)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("🚫 Operation cancelled.", reply_markup=get_main_menu_keyboard())
