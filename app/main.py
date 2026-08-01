import asyncio
import logging
import sys

from telegram import BotCommand
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.bot.handlers.admin import admin_command, handle_admin_callback
from app.bot.handlers.callbacks import handle_callback_query
from app.bot.handlers.corrections import (
    WAITING_FOR_CORRECTION_VALUE,
    cancel_correction,
    handle_dropdown_option,
    process_correction_input,
    select_field_to_correct,
    start_correction_flow,
)
from app.bot.handlers.history import handle_history_pagination, history_command
from app.bot.handlers.start import (
    cancel_command,
    help_command,
    privacy_command,
    start_command,
    upload_command,
)
from app.bot.handlers.uploads import handle_document_upload
from app.config import settings
from app.database.session import init_db
from app.logging_config import setup_logging
from app.templates.loader import default_template_loader

logger = logging.getLogger(__name__)


async def setup_bot_commands(application: Application) -> None:
    commands = [
        BotCommand("start", "Open the main menu"),
        BotCommand("upload", "Upload a receipt or document"),
        BotCommand("cancel", "Cancel current operation"),
    ]
    try:
        await application.bot.set_my_commands(commands)
    except Exception as e:
        logger.warning(f"Could not set bot commands: {e}")


def build_application() -> Application:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in environment!")
        sys.exit(1)

    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    app = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .request(request)
        .build()
    )

    # Conversation handler for field correction flow
    correction_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_correction_flow, pattern="^doc:corr:")
        ],
        states={
            WAITING_FOR_CORRECTION_VALUE: [
                CallbackQueryHandler(select_field_to_correct, pattern="^doc:field:"),
                CallbackQueryHandler(handle_dropdown_option, pattern="^doc:opt:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_correction_input),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_correction)],
        per_message=False,
    )

    app.add_handler(correction_handler)

    # Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("privacy", privacy_command))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("admin", admin_command))

    # Document & Photo Upload Handler
    app.add_handler(
        MessageHandler(filters.PHOTO | filters.Document.ALL, handle_document_upload)
    )

    # Admin Callback Handler
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^adm:"))

    # Callback Query Handlers
    app.add_handler(CallbackQueryHandler(handle_history_pagination, pattern="^page:his:"))
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    return app


async def main() -> None:
    setup_logging()
    logger.info("Initializing database...")
    await init_db()

    logger.info("Loading document templates...")
    default_template_loader.reload_templates()

    logger.info("Building Telegram application...")
    application = build_application()

    logger.info("Setting bot command menus...")
    await setup_bot_commands(application)

    logger.info("Starting bot polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Keep running until interrupted
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping bot...")
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
