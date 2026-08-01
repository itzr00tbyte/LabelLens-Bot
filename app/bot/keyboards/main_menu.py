from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.utils.callback_data import CallbackDataHelper


def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("📤 Upload Document", callback_data=CallbackDataHelper.encode("upload"))
        ]
    ]
    return InlineKeyboardMarkup(buttons)
