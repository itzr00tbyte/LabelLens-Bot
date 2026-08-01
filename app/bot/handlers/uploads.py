import logging
import os
from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards.result import (
    get_low_confidence_keyboard,
    get_result_keyboard,
    get_unknown_document_keyboard,
)
from app.bot.messages.renderers import MessageRenderer
from app.bot.middleware.access_control import ensure_user
from app.bot.middleware.rate_limit import global_rate_limiter
from app.config import settings
from app.database.repositories import SubmissionRepository, UserRepository
from app.database.session import get_db_session
from app.services.submission_service import SubmissionService
from app.utils.file_validation import FileValidator
from app.utils.identifiers import generate_error_reference

logger = logging.getLogger(__name__)


async def handle_document_upload(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed or not tg_id or not update.message:
        return

    if global_rate_limiter.is_rate_limited(tg_id):
        await update.message.reply_html(
            "⚠️ <b>Rate Limit Exceeded</b>\n\nYou are uploading too quickly. Please wait a minute before uploading another document."
        )
        return

    photo = update.message.photo[-1] if update.message.photo else None
    document = update.message.document if update.message.document else None

    if not photo and not document:
        await update.message.reply_html(
            "⚠️ <b>Unsupported File</b>\n\nPlease upload a JPG, PNG, WEBP, or supported PDF image file."
        )
        return

    status_msg = await update.message.reply_html(
        MessageRenderer.render_processing_stage("📥 Receiving document...")
    )

    file_obj = None
    original_filename = "upload.jpg"
    try:
        if photo:
            file_obj = await context.bot.get_file(photo.file_id)
            original_filename = f"photo_{photo.file_id[:8]}.jpg"
        elif document:
            file_obj = await context.bot.get_file(document.file_id)
            original_filename = document.file_name or "document.bin"

        file_bytes = await file_obj.download_as_bytearray()
        
        valid, ext_or_err = FileValidator.validate_file_bytes(file_bytes, original_filename)
        if not valid:
            await status_msg.edit_text(
                f"⚠️ <b>Validation Failed</b>\n\n{ext_or_err}",
                parse_mode="HTML"
            )
            return

        async with get_db_session() as session:
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(tg_id)
            if not db_user:
                await status_msg.edit_text("❌ User not found.")
                return

            sub_repo = SubmissionRepository(session)
            submission = await sub_repo.create(
                user_id=db_user.id,
                telegram_file_id=file_obj.file_id,
                original_filename=original_filename,
            )
            submission_id = submission.id
            await session.commit()

        # Define stage update helper for continuous message edits
        async def stage_callback(stage_text: str):
            try:
                await status_msg.edit_text(
                    MessageRenderer.render_processing_stage(stage_text),
                    parse_mode="HTML"
                )
            except Exception:
                pass

        async with get_db_session() as session:
            service = SubmissionService(session)
            submission, match_res = await service.process_document_submission(
                submission_id, bytes(file_bytes), status_update_callback=stage_callback
            )

            doc_type = match_res.template.name if match_res.template else "Unknown Document"
            is_shipping = (
                match_res.template is not None
                and "shipping_label" in match_res.template.category
            )

            if match_res.template and match_res.score >= settings.LOW_CONFIDENCE_THRESHOLD:
                text = MessageRenderer.render_result_summary(
                    document_type=doc_type,
                    confidence=match_res.score,
                    extracted_fields=submission.extracted_fields,
                    corrected_fields=submission.corrected_fields,
                )
                kb = get_result_keyboard(submission_id, is_shipping_label=is_shipping)
            elif match_res.template and match_res.score >= settings.MIN_TEMPLATE_CONFIDENCE:
                text = MessageRenderer.render_low_confidence(doc_type, match_res.score)
                kb = get_low_confidence_keyboard(submission_id)
            else:
                text = MessageRenderer.render_unknown_document()
                kb = get_unknown_document_keyboard(submission_id)

            await status_msg.edit_text(text, parse_mode="HTML", reply_markup=kb)

    except Exception as e:
        logger.error(f"Error handling upload for user {tg_id}: {e}", exc_info=True)
        ref_id = generate_error_reference()
        err_html = MessageRenderer.render_error_message(ref_id)
        try:
            await status_msg.edit_text(err_html, parse_mode="HTML")
        except Exception:
            await update.message.reply_html(err_html)
