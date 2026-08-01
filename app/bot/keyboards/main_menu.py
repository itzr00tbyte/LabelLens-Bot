from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.utils.callback_data import CallbackDataHelper


def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                "🚀  Upload Document",
                callback_data=CallbackDataHelper.encode("upload"),
            )
        ],
        [
            InlineKeyboardButton(
                "❓  Help Guide",
                callback_data=CallbackDataHelper.encode("help"),
            ),
            InlineKeyboardButton(
                "🔒  Privacy Policy",
                callback_data=CallbackDataHelper.encode("privacy"),
            ),
        ],
    ]
    return InlineKeyboardMarkup(buttons)
