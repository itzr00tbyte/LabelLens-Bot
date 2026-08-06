import asyncio
import logging
import os
import signal
import sys
import warnings

# Ensure project root directory is in sys.path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import BotCommand
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.bot.handlers.admin import approve_command, disapprove_command, users_command
from app.bot.handlers.callbacks import handle_callback_query
from app.bot.handlers.corrections import (
    WAITING_FOR_CONFIRMATION,
    WAITING_FOR_CORRECTION_VALUE,
    cancel_correction,
    handle_confirmation,
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
        BotCommand("start", "Start & main menu"),
        BotCommand("upload", "Upload new document"),
        BotCommand("history", "View saved documents"),
        BotCommand("help", "Help & guide"),
    ]
    try:
        await application.bot.set_my_commands(commands)
    except Exception as e:
        logger.warning(f"Could not set bot commands: {e}")


def build_application() -> Application:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in environment!")
        sys.exit(1)

    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=60.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )
    app = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .request(request)
        .build()
    )

    # Conversation handler for field correction flow
    # per_message=False is intentional: tracks state per user+chat, not per button.
    warnings.filterwarnings("ignore", message=".*per_message=False.*", category=UserWarning)
    correction_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_correction_flow, pattern="^doc:corr:"),
            CallbackQueryHandler(select_field_to_correct, pattern="^doc:field:"),
        ],
        states={
            WAITING_FOR_CORRECTION_VALUE: [
                CallbackQueryHandler(select_field_to_correct, pattern="^doc:field:"),
                CallbackQueryHandler(handle_dropdown_option, pattern="^doc:opt:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_correction_input),
            ],
            WAITING_FOR_CONFIRMATION: [
                CallbackQueryHandler(handle_confirmation, pattern="^doc:confirm:"),
                CallbackQueryHandler(handle_confirmation, pattern="^doc:cancel_edit:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_correction)],
        per_message=False,
        allow_reentry=True,  # allow clicking edit buttons after a session ends
    )

    app.add_handler(correction_handler)

    # Admin Commands
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("disapprove", disapprove_command))
    app.add_handler(CommandHandler("revoke", disapprove_command))
    app.add_handler(CommandHandler("users", users_command))

    # Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("privacy", privacy_command))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    # Document & Photo Upload Handler
    app.add_handler(
        MessageHandler(filters.PHOTO | filters.Document.ALL, handle_document_upload)
    )

    # Callback Query Handlers
    app.add_handler(CallbackQueryHandler(handle_history_pagination, pattern="^page:his:"))
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    app.add_error_handler(global_error_handler)

    return app


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)


async def main() -> None:
    setup_logging()

    # Only print colorama banner in non-production environments
    if settings.ENVIRONMENT != "production":
        from colorama import Fore, Style  # type: ignore[import-untyped]
        print(
            f"\n{Fore.CYAN}{Style.BRIGHT}"
            "===========================================================\n"
            "         🚀 LABELLENS TELEGRAM BOT INITIALIZING           \n"
            "===========================================================\n"
            f"{Style.RESET_ALL}"
        )

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
    if application.updater:
        await application.updater.start_polling()

    # Keep running until SIGTERM / SIGINT / KeyboardInterrupt
    stop_event = asyncio.Event()

    def _handle_signal(sig: int) -> None:
        logger.info(f"Received signal {signal.Signals(sig).name}, shutting down...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _handle_signal, sig)

    try:
        await stop_event.wait()
    finally:
        logger.info("Stopping bot...")
        if application.updater:
            await application.updater.stop()
        await application.stop()
        await application.shutdown()
        logger.info("Bot stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
