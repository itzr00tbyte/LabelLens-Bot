from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.utils.callback_data import CallbackDataHelper


def get_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧩 Templates", callback_data=CallbackDataHelper.encode("adm:tpl")),
            InlineKeyboardButton("📥 Submissions", callback_data=CallbackDataHelper.encode("adm:subs")),
        ],
        [
            InlineKeyboardButton("📊 Statistics", callback_data=CallbackDataHelper.encode("adm:stats")),
            InlineKeyboardButton("⚠️ Failed Scans", callback_data=CallbackDataHelper.encode("adm:failed")),
        ],
        [
            InlineKeyboardButton("📤 Export CSV", callback_data=CallbackDataHelper.encode("adm:export")),
            InlineKeyboardButton("👥 Users", callback_data=CallbackDataHelper.encode("adm:users")),
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data=CallbackDataHelper.encode("menu:main"))
        ],
    ])
