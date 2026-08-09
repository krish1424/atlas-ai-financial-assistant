import os
import tempfile
from pathlib import Path
from uuid import uuid4

from telegram import Update
from telegram.ext import ContextTypes

from app.ai.agent import AtlasAgent
from app.ai.memory import ConversationMessage
from app.database.database import SessionLocal
from app.services import ConversationService, UserService
from app.services.document_service import DocumentAnalysisService


# ---------------------------------------------------------
# Shared Atlas instances
# ---------------------------------------------------------

atlas_agent = AtlasAgent()

document_service = DocumentAnalysisService(
    agent=atlas_agent,
)


# ---------------------------------------------------------
# Telegram user state keys
# ---------------------------------------------------------

DOCUMENT_PATH_KEY = "active_document_path"
DOCUMENT_NAME_KEY = "active_document_name"


# ---------------------------------------------------------
# Temporary document helper
# ---------------------------------------------------------

def _remove_active_document(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Delete the currently active temporary PDF
    and clear its Telegram user state.
    """

    document_path = context.user_data.get(
        DOCUMENT_PATH_KEY
    )

    if document_path:
        try:
            path = Path(document_path)

            if path.exists():
                path.unlink()

        except OSError:
            pass

    context.user_data.pop(
        DOCUMENT_PATH_KEY,
        None,
    )

    context.user_data.pop(
        DOCUMENT_NAME_KEY,
        None,
    )


# ---------------------------------------------------------
# /start
# ---------------------------------------------------------

async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle /start and register the Telegram user.
    """

    if (
        update.effective_user is None
        or update.message is None
    ):
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
            "I can help you research companies, "
            "analyze financial information, review "
            "financial documents, and answer questions.\n\n"
            "You can upload a PDF financial report "
            "and ask questions about it.\n\n"
            "Send /clear when you want to leave "
            "document mode."
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


# ---------------------------------------------------------
# /clear
# ---------------------------------------------------------

async def clear_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Clear the active document and start a fresh conversation.

    The previous conversation remains stored in the database.
    """

    if (
        update.effective_user is None
        or update.message is None
    ):
        return

    telegram_user = update.effective_user

    # -----------------------------------------------------
    # Remove the currently active temporary PDF
    # -----------------------------------------------------

    _remove_active_document(context)

    db = SessionLocal()

    try:
        # -------------------------------------------------
        # Get or create the Atlas user
        # -------------------------------------------------

        user = UserService.get_or_create_user(
            db=db,
            telegram_user_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
        )

        # -------------------------------------------------
        # Create a completely new conversation.
        #
        # The previous conversation is NOT deleted.
        # It remains stored in the database.
        # -------------------------------------------------

        ConversationService.create_conversation(
            db=db,
            user_id=user.id,
            title="Atlas Conversation",
        )

        db.commit()

        await update.message.reply_text(
            "🧹 Document mode cleared.\n\n"
            "I've also started a fresh conversation, "
            "so your next question won't use the previous "
            "document's context.\n\n"
            "You're back in normal Atlas mode."
        )

    except Exception:
        db.rollback()

        await update.message.reply_text(
            "Sorry, I couldn't clear the current context. "
            "Please try again."
        )

        raise

    finally:
        db.close()


# ---------------------------------------------------------
# PDF document handler
# ---------------------------------------------------------

async def document_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle PDF uploads.

    The PDF is downloaded to a temporary location and
    becomes the user's active document.
    """

    if (
        update.effective_user is None
        or update.message is None
        or update.message.document is None
    ):
        return

    telegram_user = update.effective_user
    telegram_document = update.message.document

    filename = (
        telegram_document.file_name
        or "uploaded_document.pdf"
    )

    # -----------------------------------------------------
    # Only accept PDF files
    # -----------------------------------------------------

    if not filename.lower().endswith(".pdf"):
        await update.message.reply_text(
            "Please upload a PDF file. "
            "Atlas currently supports PDF documents."
        )
        return

    # -----------------------------------------------------
    # Remove previous active document
    # -----------------------------------------------------

    _remove_active_document(context)

    temporary_directory = (
        Path(tempfile.gettempdir())
        / "atlas_ai_documents"
    )

    temporary_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = (
        temporary_directory
        / f"{telegram_user.id}_{uuid4().hex}.pdf"
    )

    try:
        # -------------------------------------------------
        # Download PDF from Telegram
        # -------------------------------------------------

        telegram_file = await context.bot.get_file(
            telegram_document.file_id
        )

        await telegram_file.download_to_drive(
            custom_path=str(temporary_path)
        )

        # -------------------------------------------------
        # Store active document state
        # -------------------------------------------------

        context.user_data[
            DOCUMENT_PATH_KEY
        ] = str(temporary_path)

        context.user_data[
            DOCUMENT_NAME_KEY
        ] = filename

        await update.message.reply_text(
            f"📄 Received `{filename}`.\n\n"
            "The document is ready.\n\n"
            "What would you like me to analyze?\n\n"
            "Examples:\n"
            "• What is the company's revenue?\n"
            "• What are the main financial risks?\n"
            "• Summarize the financial performance.\n"
            "• What recommendations are given in the report?\n\n"
            "Send /clear when you're finished with "
            "this document."
        )

    except Exception:
        _remove_active_document(context)

        await update.message.reply_text(
            "Sorry, I couldn't process that PDF. "
            "Please try uploading it again."
        )

        raise


# ---------------------------------------------------------
# Normal text message handler
# ---------------------------------------------------------

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle normal text messages.

    If a PDF is active, the message is treated as a
    question about that document.

    Otherwise it is handled normally by Atlas.
    """

    if (
        update.effective_user is None
        or update.message is None
    ):
        return

    if not update.message.text:
        return

    telegram_user = update.effective_user
    user_text = update.message.text.strip()

    if not user_text:
        return

    # -----------------------------------------------------
    # Check whether a document is active
    # -----------------------------------------------------

    active_document_path = context.user_data.get(
        DOCUMENT_PATH_KEY
    )

    db = SessionLocal()

    try:
        # -------------------------------------------------
        # 1. Get or create Atlas user
        # -------------------------------------------------

        user = UserService.get_or_create_user(
            db=db,
            telegram_user_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
        )

        # -------------------------------------------------
        # 2. Get or create conversation
        # -------------------------------------------------

        conversation = (
            ConversationService.get_or_create_conversation(
                db=db,
                user_id=user.id,
            )
        )

        # -------------------------------------------------
        # 3. Get previous conversation history
        # -------------------------------------------------

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

        # -------------------------------------------------
        # 4. Save user's message
        # -------------------------------------------------

        ConversationService.add_message(
            db=db,
            conversation_id=conversation.id,
            user_id=user.id,
            role="user",
            content=user_text,
        )

        # -------------------------------------------------
        # 5A. Active document mode
        # -------------------------------------------------

        if active_document_path:

            if not os.path.exists(
                active_document_path
            ):
                _remove_active_document(
                    context
                )

                raise FileNotFoundError(
                    "The active document is no longer available."
                )

            await update.message.reply_text(
                "🔎 Analyzing your document..."
            )

            result = (
                await document_service.analyze_pdf(
                    file_path=active_document_path,
                    question=user_text,
                )
            )

            assistant_text = result.answer

        # -------------------------------------------------
        # 5B. Normal Atlas mode
        # -------------------------------------------------

        else:

            agent_response = await atlas_agent.process(
                user_message=user_text,
                conversation_history=conversation_history,
            )

            assistant_text = agent_response.message

        # -------------------------------------------------
        # 6. Save Atlas response
        # -------------------------------------------------

        ConversationService.add_message(
            db=db,
            conversation_id=conversation.id,
            user_id=user.id,
            role="assistant",
            content=assistant_text,
        )

        db.commit()

        # -------------------------------------------------
        # 7. Send response to Telegram
        # -------------------------------------------------

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