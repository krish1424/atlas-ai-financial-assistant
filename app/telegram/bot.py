from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config.settings import get_settings
from app.telegram.handlers import (
    clear_handler,
    document_handler,
    message_handler,
    start_handler,
)


def create_bot_application() -> Application:
    """Create and configure the Telegram bot application."""

    settings = get_settings()

    if not settings.telegram_bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start_handler,
        )
    )

    application.add_handler(
        CommandHandler(
            "clear",
            clear_handler,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.Document.PDF,
            document_handler,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler,
        )
    )

    return application


def run_bot() -> None:
    """Start the Telegram bot using polling."""

    application = create_bot_application()

    print("Atlas Telegram bot is starting...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    run_bot()