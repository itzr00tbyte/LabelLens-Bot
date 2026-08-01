import io
import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.bot.keyboards.result import (
    get_result_keyboard,
    get_unknown_document_keyboard,
)
from app.bot.keyboards.templates import get_templates_selection_keyboard
from app.bot.messages.renderers import MessageRenderer
from app.bot.middleware.access_control import ensure_user
from app.database.repositories import SubmissionRepository, UserRepository
from app.database.session import get_db_session
from app.services.image_generator import ReceiptImageGenerator
from app.services.submission_service import SubmissionService
from app.templates.loader import default_template_loader
from app.utils.callback_data import CallbackDataHelper

logger = logging.getLogger(__name__)


async def handle_callback_query(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed or not tg_id:
        await query.answer("⛔ Access denied.", show_alert=True)
        return

    # Answer query immediately to resolve loading indicator
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Could not answer callback query: {e}")
    cb = CallbackDataHelper.decode(query.data)

    try:
        if cb.action == "menu:main":
            name = update.effective_user.first_name if update.effective_user else ""
            await query.edit_message_text(
                MessageRenderer.render_start_message(name),
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard(is_admin=is_admin),
            )
            return

        elif cb.action == "upload":
            await query.edit_message_text(
                MessageRenderer.render_upload_instructions(),
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard(is_admin=is_admin),
            )
            return

        elif cb.action == "help":
            await query.edit_message_text(
                MessageRenderer.render_help_message(),
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard(is_admin=is_admin),
            )
            return

        elif cb.action == "privacy":
            await query.edit_message_text(
                MessageRenderer.render_privacy_message(),
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard(is_admin=is_admin),
            )
            return

        submission_id = cb.target_id
        if not submission_id:
            return

        async with get_db_session() as session:
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(tg_id)
            if not db_user:
                return

            service = SubmissionService(session)

            if cb.action == "doc:app":
                submission = await service.approve_submission(submission_id, db_user.id)
                await query.edit_message_text(
                    f"✅ <b>Submission Approved</b>\n\nThank you! Submission <code>{submission.id[:8]}</code> has been saved to your history.",
                    parse_mode="HTML",
                    reply_markup=get_main_menu_keyboard(is_admin=is_admin),
                )

            elif cb.action == "doc:rej":
                submission = await service.reject_submission(submission_id, db_user.id)
                await query.edit_message_text(
                    f"❌ <b>Submission Rejected</b>\n\nSubmission <code>{submission.id[:8]}</code> was discarded.",
                    parse_mode="HTML",
                    reply_markup=get_main_menu_keyboard(is_admin=is_admin),
                )

            elif cb.action == "doc:det":
                sub_repo = SubmissionRepository(session)
                sub = await sub_repo.get_by_id(submission_id)
                if not sub:
                    return
                doc_name = sub.template_id or sub.document_category
                text = MessageRenderer.render_details_screen(
                    document_type=doc_name,
                    confidence=sub.match_confidence,
                    extracted_fields=sub.extracted_fields,
                    corrected_fields=sub.corrected_fields,
                )
                is_shipping = "shipping_label" in sub.document_category
                kb = get_result_keyboard(submission_id, is_shipping_label=is_shipping)
                await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)

            elif cb.action == "doc:trk":
                sub_repo = SubmissionRepository(session)
                sub = await sub_repo.get_by_id(submission_id)
                if not sub:
                    return
                fields = sub.corrected_fields or sub.extracted_fields or {}
                trk_no = fields.get("tracking_number", "N/A")
                carrier = fields.get("carrier", sub.document_category.upper())
                service_name = fields.get("service", "Standard")
                text = MessageRenderer.render_tracking_details(trk_no, carrier, service_name)
                is_shipping = "shipping_label" in sub.document_category
                kb = get_result_keyboard(submission_id, is_shipping_label=is_shipping)
                await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)

            elif cb.action == "doc:down_img":
                sub_repo = SubmissionRepository(session)
                sub = await sub_repo.get_by_id(submission_id)
                if not sub or not update.effective_chat:
                    return

                merged_fields = dict(sub.extracted_fields or {})
                merged_fields.update(sub.corrected_fields or {})

                doc_name = sub.template_id or sub.document_category
                is_shipping = "shipping_label" in sub.document_category
                img = ReceiptImageGenerator.generate_receipt_image(doc_name, merged_fields, is_shipping=is_shipping)
                img_bytes = ReceiptImageGenerator.get_image_bytes(img, format="PNG")

                file_buf = io.BytesIO(img_bytes)
                file_buf.name = f"Receipt_{submission_id[:8]}.png"

                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=file_buf,
                    filename=f"Receipt_{submission_id[:8]}.png",
                    caption=f"🖼 <b>Here is your updated receipt image file:</b> <code>Receipt_{submission_id[:8]}.png</code>",
                    parse_mode="HTML",
                )

            elif cb.action == "doc:down_pdf":
                sub_repo = SubmissionRepository(session)
                sub = await sub_repo.get_by_id(submission_id)
                if not sub or not update.effective_chat:
                    return

                merged_fields = dict(sub.extracted_fields or {})
                merged_fields.update(sub.corrected_fields or {})

                doc_name = sub.template_id or sub.document_category
                is_shipping = "shipping_label" in sub.document_category
                img = ReceiptImageGenerator.generate_receipt_image(doc_name, merged_fields, is_shipping=is_shipping)
                pdf_bytes = ReceiptImageGenerator.get_pdf_bytes(img)

                file_buf = io.BytesIO(pdf_bytes)
                file_buf.name = f"Receipt_{submission_id[:8]}.pdf"

                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=file_buf,
                    filename=f"Receipt_{submission_id[:8]}.pdf",
                    caption=f"📄 <b>Here is your updated receipt PDF document:</b> <code>Receipt_{submission_id[:8]}.pdf</code>",
                    parse_mode="HTML",
                )

            elif cb.action == "doc:rev":
                sub_repo = SubmissionRepository(session)
                sub = await sub_repo.get_by_id(submission_id)
                if not sub:
                    return
                doc_name = sub.template_id or sub.document_category
                is_shipping = "shipping_label" in sub.document_category
                merged = dict(sub.extracted_fields or {})
                merged.update(sub.corrected_fields or {})
                text = MessageRenderer.render_final_updated_receipt(
                    document_type=doc_name,
                    confidence=sub.match_confidence,
                    extracted_fields=sub.extracted_fields,
                    corrected_fields=sub.corrected_fields,
                )
                kb = get_result_keyboard(submission_id, available_fields=list(merged.keys()), is_shipping_label=is_shipping)
                await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)

            elif cb.action == "tpl:choose":
                templates = default_template_loader.list_templates()
                kb = get_templates_selection_keyboard(submission_id, templates, page=0)
                await query.edit_message_text(
                    "🧩 <b>Select Document Template</b>\n\nChoose the template that best matches your uploaded document:",
                    parse_mode="HTML",
                    reply_markup=kb,
                )

            elif cb.action == "tpl:pg":
                page = int(cb.extra or "0")
                templates = default_template_loader.list_templates()
                kb = get_templates_selection_keyboard(submission_id, templates, page=page)
                await query.edit_message_text(
                    "🧩 <b>Select Document Template</b>\n\nChoose the template that best matches your uploaded document:",
                    parse_mode="HTML",
                    reply_markup=kb,
                )

            elif cb.action == "tpl:sel":
                template_id = cb.extra
                if not template_id:
                    return
                sub, match_res = await service.apply_manual_template(
                    submission_id, db_user.id, template_id
                )
                doc_name = match_res.template.name if match_res.template else template_id
                is_shipping = "shipping_label" in sub.document_category
                text = MessageRenderer.render_result_summary(
                    document_type=doc_name,
                    confidence=sub.match_confidence,
                    extracted_fields=sub.extracted_fields,
                    corrected_fields=sub.corrected_fields,
                )
                kb = get_result_keyboard(submission_id, is_shipping_label=is_shipping)
                await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)

    except Exception as e:
        logger.error(f"Callback error for user {tg_id}: {e}", exc_info=True)
