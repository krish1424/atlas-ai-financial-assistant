from telegram import Update
from telegram.ext import ContextTypes

from app.ai.agent import AtlasAgent
from app.ai.memory import ConversationMessage
from app.database.database import SessionLocal
from app.services import ConversationService, UserService


# Create one Atlas agent instance and reuse it.
atlas_agent = AtlasAgent()


async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle the /start command and register the Telegram user."""

    if update.effective_user is None or update.message is None:
        return

    telegram_user = update.effective_user

    db = SessionLocal()

    try:
        UserService.get_or_create_user(
            db=db,
            telegram_user_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
        )

        db.commit()

        await update.message.reply_text(
            f"Hello {telegram_user.first_name}! 👋\n\n"
            "I'm Atlas, your AI financial assistant.\n\n"
            "I'm ready to help you research companies, "
            "understand financial information, analyze documents, "
            "and answer your financial questions.\n\n"
            "Just send me a message."
        )

    except Exception:
        db.rollback()

        await update.message.reply_text(
            "Sorry, I couldn't initialize your Atlas account. "
            "Please try again."
        )

        raise

    finally:
        db.close()


async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle normal text messages and send them to Atlas AI."""

    if update.effective_user is None or update.message is None:
        return

    if not update.message.text:
        return

    telegram_user = update.effective_user
    user_text = update.message.text.strip()

    if not user_text:
        return

    db = SessionLocal()

    try:
        # ---------------------------------------------------------
        # 1. Get or create the Atlas user
        # ---------------------------------------------------------

        user = UserService.get_or_create_user(
            db=db,
            telegram_user_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
        )

        # ---------------------------------------------------------
        # 2. Get or create the active conversation
        # ---------------------------------------------------------

        conversation = ConversationService.get_or_create_conversation(
            db=db,
            user_id=user.id,
        )

        # ---------------------------------------------------------
        # 3. Get previous conversation history
        # ---------------------------------------------------------

        history = ConversationService.get_history(
            db=db,
            conversation_id=conversation.id,
        )

        conversation_history = [
            ConversationMessage(
                role=message.role,
                content=message.content,
            )
            for message in history
        ]

        # ---------------------------------------------------------
        # 4. Save the user's message
        # ---------------------------------------------------------

        ConversationService.add_message(
            db=db,
            conversation_id=conversation.id,
            user_id=user.id,
            role="user",
            content=user_text,
        )

        # ---------------------------------------------------------
        # 5. Send request to Atlas AI / Gemini
        # ---------------------------------------------------------

        agent_response = await atlas_agent.process(
            user_message=user_text,
            conversation_history=conversation_history,
        )

        assistant_text = agent_response.message

        # ---------------------------------------------------------
        # 6. Save Atlas's response
        # ---------------------------------------------------------

        ConversationService.add_message(
            db=db,
            conversation_id=conversation.id,
            user_id=user.id,
            role="assistant",
            content=assistant_text,
        )

        db.commit()

        # ---------------------------------------------------------
        # 7. Send response back to Telegram
        # ---------------------------------------------------------

        await update.message.reply_text(
            assistant_text
        )

    except Exception:
        db.rollback()

        await update.message.reply_text(
            "Sorry, something went wrong while processing "
            "your request. Please try again."
        )

        raise

    finally:
        db.close()