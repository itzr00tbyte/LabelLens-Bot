import io
import logging
from telegram import Update, Message
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from app.bot.keyboards.result import (
    get_confirmation_keyboard,
    get_correction_fields_keyboard,
    get_dropdown_options_keyboard,
    get_result_keyboard,
)
from app.bot.messages.renderers import MessageRenderer
from app.bot.middleware.access_control import ensure_user
from app.database.repositories import SubmissionRepository, UserRepository
from app.database.session import get_db_session
from app.services.image_generator import ReceiptImageGenerator
from app.services.submission_service import SubmissionService
from app.services.validation_service import ValidationService
from app.utils.address_generator import AddressGenerator
from app.utils.callback_data import CallbackDataHelper

logger = logging.getLogger(__name__)


def _is_photo_message(message: Message) -> bool:
    """Return True if the Telegram message is a photo or media (not plain text)."""
    return bool(message.photo or message.document or message.sticker or message.animation)


async def _safe_edit(query, text: str, parse_mode: str = "HTML", reply_markup=None) -> None:
    """
    Edit message text or caption depending on the underlying message type.

    Telegram does NOT allow edit_message_text on a photo/document message —
    those require edit_message_caption instead. Calling the wrong method raises
    a BadRequest that silently kills the interaction and leaves the buttons broken.
    This helper automatically picks the correct Telegram API call.
    """
    msg = query.message
    if msg and _is_photo_message(msg):
        logger.debug(
            "_safe_edit: message_id=%s is photo/media → using edit_message_caption",
            msg.message_id,
        )
        await query.edit_message_caption(
            caption=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
    else:
        await query.edit_message_text(
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )

WAITING_FOR_CORRECTION_VALUE = 1
WAITING_FOR_CONFIRMATION = 2

SERVICE_DROPDOWN_OPTIONS = [
    "Ground Advantage",
    "Ground Advantage Returns",
    "Ground Advantage Hazmat",
    "Priority Mail",
    "Priority Mail Express",
    "UPS Ground",
    "FedEx Express",
]

CARRIER_DROPDOWN_OPTIONS = [
    "USPS",
    "UPS",
    "FedEx",
    "DHL",
]


async def start_correction_flow(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        logger.warning("start_correction_flow: missing query or user_data")
        return ConversationHandler.END

    allowed, _, tg_id = await ensure_user(update)
    if not allowed or not tg_id:
        await query.answer("Access denied.")
        logger.warning("start_correction_flow: access denied for query data=%s", query.data)
        return ConversationHandler.END

    await query.answer()
    cb = CallbackDataHelper.decode(query.data)
    submission_id = cb.target_id
    logger.info(
        "start_correction_flow: user=%s submission=%s",
        tg_id, submission_id,
    )

    if not submission_id:
        logger.warning("start_correction_flow: no submission_id in callback data=%s", query.data)
        return ConversationHandler.END

    try:
        async with get_db_session() as session:
            repo = SubmissionRepository(session)
            sub = await repo.get_by_id(submission_id)
            if not sub:
                logger.warning("start_correction_flow: submission %s not found", submission_id)
                return ConversationHandler.END

            merged = dict(sub.extracted_fields or {})
            merged.update(sub.corrected_fields or {})

            available_fields = (
                list(merged.keys())
                if merged
                else ["merchant_name", "service", "total", "subtotal", "tax", "transaction_date", "address"]
            )

            context.user_data["editing_submission_id"] = submission_id
            context.user_data["editing_submission_fields"] = merged

            kb = get_correction_fields_keyboard(submission_id, available_fields)
            await _safe_edit(
                query,
                "✏️ <b>Select a field to edit live:</b>",
                reply_markup=kb,
            )
            logger.debug(
                "start_correction_flow: showed %d editable fields for submission=%s",
                len(available_fields), submission_id,
            )
    except Exception:
        logger.exception(
            "start_correction_flow: error for user=%s submission=%s",
            tg_id, submission_id,
        )
        return ConversationHandler.END

    return WAITING_FOR_CORRECTION_VALUE


async def select_field_to_correct(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        logger.warning("select_field_to_correct: missing query or user_data")
        return ConversationHandler.END

    await query.answer()
    cb = CallbackDataHelper.decode(query.data)
    submission_id = context.user_data.get("editing_submission_id") or cb.target_id
    field_key = cb.extra

    logger.info(
        "select_field_to_correct: submission=%s field_key=%s msg_type=%s",
        submission_id, field_key,
        "photo" if (query.message and _is_photo_message(query.message)) else "text",
    )

    if not field_key or not submission_id:
        logger.warning(
            "select_field_to_correct: missing field_key=%s or submission_id=%s",
            field_key, submission_id,
        )
        return ConversationHandler.END

    # Resolve full field name if key was truncated for callback safety
    fields_dict = context.user_data.get("editing_submission_fields")
    if not fields_dict:
        logger.debug(
            "select_field_to_correct: no cached fields — fetching from DB for submission=%s",
            submission_id,
        )
        try:
            async with get_db_session() as session:
                sub_repo = SubmissionRepository(session)
                sub = await sub_repo.get_by_id(submission_id)
                if sub:
                    fields_dict = dict(sub.extracted_fields or {})
                    fields_dict.update(sub.corrected_fields or {})
                    context.user_data["editing_submission_fields"] = fields_dict
                else:
                    logger.warning(
                        "select_field_to_correct: submission %s not found in DB", submission_id
                    )
        except Exception:
            logger.exception(
                "select_field_to_correct: DB error fetching submission=%s", submission_id
            )

    fields_dict = fields_dict or {}
    full_field_name = field_key
    for original_key in fields_dict.keys():
        if original_key.startswith(field_key) or field_key.startswith(original_key):
            full_field_name = original_key
            break

    logger.debug(
        "select_field_to_correct: resolved field_key=%r → full_field_name=%r",
        field_key, full_field_name,
    )

    context.user_data["editing_submission_id"] = submission_id
    context.user_data["editing_field_name"] = full_field_name

    label = full_field_name.replace("_", " ").title()
    field_lower = full_field_name.lower()

    try:
        # Check if field has predefined drop down selection keyboard
        if any(kw in field_lower for kw in ["service", "shipping_type", "mail_class", "delivery_type"]):
            options = SERVICE_DROPDOWN_OPTIONS
            context.user_data["editing_dropdown_options"] = options
            kb = get_dropdown_options_keyboard(submission_id, full_field_name, options)
            await _safe_edit(
                query,
                f"📦 <b>Select {label}:</b>\n\nChoose an option from the list below:",
                reply_markup=kb,
            )
            return WAITING_FOR_CORRECTION_VALUE

        elif "carrier" in field_lower:
            options = CARRIER_DROPDOWN_OPTIONS
            context.user_data["editing_dropdown_options"] = options
            kb = get_dropdown_options_keyboard(submission_id, full_field_name, options)
            await _safe_edit(
                query,
                "🚚 <b>Select Carrier:</b>\n\nChoose a carrier from the list below:",
                reply_markup=kb,
            )
            return WAITING_FOR_CORRECTION_VALUE

        _PURE_ADDRESS_SLUGS = {"ship_to", "ship_from", "location", "delivery_location"}
        is_address = "address" in field_lower or field_lower in _PURE_ADDRESS_SLUGS

        if is_address:
            prompt_text = (
                f"✏️ <b>Edit Address:</b> {label}\n\n"
                "Send a <b>5-digit US Zip Code</b> (e.g. <code>90210</code>, <code>10001</code>, <code>30301</code>) "
                "to generate a realistic random address, or type a custom address:"
            )
        else:
            prompt_text = (
                f"✏️ <b>Edit Field:</b> {label}\n\n"
                f"Please reply with the new value for <b>{label}</b> (or /cancel):"
            )

        await _safe_edit(query, prompt_text)
        logger.debug(
            "select_field_to_correct: prompted user for field=%s in submission=%s",
            full_field_name, submission_id,
        )
    except Exception:
        logger.exception(
            "select_field_to_correct: error presenting field=%s for submission=%s",
            full_field_name, submission_id,
        )
        return ConversationHandler.END

    return WAITING_FOR_CORRECTION_VALUE


async def handle_dropdown_option(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        logger.warning("handle_dropdown_option: missing query or user_data")
        return ConversationHandler.END

    await query.answer()
    cb = CallbackDataHelper.decode(query.data)
    opt_idx_str = cb.extra

    submission_id = context.user_data.get("editing_submission_id")
    field_name = context.user_data.get("editing_field_name")
    options = context.user_data.get("editing_dropdown_options", [])

    logger.info(
        "handle_dropdown_option: submission=%s field=%s opt_idx=%s",
        submission_id, field_name, opt_idx_str,
    )

    if not submission_id or not field_name or not opt_idx_str or not opt_idx_str.isdigit():
        logger.warning(
            "handle_dropdown_option: invalid state — submission=%s field=%s opt_idx=%s",
            submission_id, field_name, opt_idx_str,
        )
        return ConversationHandler.END

    opt_idx = int(opt_idx_str)
    if opt_idx < 0 or opt_idx >= len(options):
        logger.warning(
            "handle_dropdown_option: opt_idx=%d out of range (options=%d)", opt_idx, len(options)
        )
        return ConversationHandler.END

    selected_value = options[opt_idx]
    logger.info(
        "handle_dropdown_option: selected value=%r for field=%s — awaiting confirmation",
        selected_value, field_name,
    )

    # Store as pending; wait for Confirm / Cancel
    context.user_data["pending_field_value"] = selected_value
    context.user_data.pop("editing_dropdown_options", None)

    label = field_name.replace("_", " ").title()
    kb = get_confirmation_keyboard(submission_id)
    await _safe_edit(
        query,
        f"╭──── ✏️ Confirm Edit ────╮\n"
        f"\n"
        f"  📌  <b>Field</b>\n"
        f"  <code>{label}</code>\n"
        f"\n"
        f"  🔄  <b>New Value</b>\n"
        f"  <code>{selected_value}</code>\n"
        f"\n"
        f"╰─────────────────────╯\n"
        f"\n"
        f"<i>Tap <b>Save Change</b> to apply, or <b>Go Back</b> to discard.</i>",
        reply_markup=kb,
    )
    return WAITING_FOR_CONFIRMATION


async def process_correction_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not update.message or not update.message.text or context.user_data is None:
        return WAITING_FOR_CORRECTION_VALUE

    allowed, _, tg_id = await ensure_user(update)
    if not allowed or not tg_id:
        logger.warning("process_correction_input: access denied")
        return ConversationHandler.END

    submission_id = context.user_data.get("editing_submission_id")
    field_name = context.user_data.get("editing_field_name")
    new_raw_value = update.message.text.strip()

    logger.info(
        "process_correction_input: user=%s submission=%s field=%s raw_value=%r",
        tg_id, submission_id, field_name, new_raw_value,
    )

    if not submission_id or not field_name:
        await update.message.reply_text("Session expired. Please try uploading your document again.")
        logger.warning(
            "process_correction_input: session expired for user=%s (no submission_id or field_name)",
            tg_id,
        )
        return ConversationHandler.END

    # Normalize the value based on field type.
    # IMPORTANT: check for "address" substring FIRST so that recipient_name / sender_name
    # do NOT get treated as address fields (they contain "recipient"/"sender" but not "address").
    _lower = field_name.lower()
    _PURE_ADDRESS_SLUGS = {"ship_to", "ship_from", "location", "delivery_location"}
    is_address = "address" in _lower or _lower in _PURE_ADDRESS_SLUGS
    if is_address:
        normalized_value = AddressGenerator.generate_from_input(new_raw_value)
        logger.debug(
            "process_correction_input: address field raw=%r → normalized=%r",
            new_raw_value, normalized_value,
        )
    elif "tracking" in field_name.lower():
        normalized_value = ValidationService.normalize_tracking_number(new_raw_value)
        logger.debug(
            "process_correction_input: tracking field raw=%r → normalized=%r",
            new_raw_value, normalized_value,
        )
    elif any(kw in field_name.lower() for kw in ["total", "price", "subtotal", "tax"]):
        curr = ValidationService.normalize_currency(new_raw_value)
        normalized_value = curr if curr else new_raw_value
        logger.debug(
            "process_correction_input: currency field raw=%r → normalized=%r",
            new_raw_value, normalized_value,
        )
    else:
        normalized_value = new_raw_value

    # Store as pending; show Confirm / Cancel instead of saving immediately
    context.user_data["pending_field_value"] = normalized_value

    label = field_name.replace("_", " ").title()
    kb = get_confirmation_keyboard(submission_id)
    await update.message.reply_html(
        f"╭──── ✏️ Confirm Edit ────╮\n"
        f"\n"
        f"  📌  <b>Field</b>\n"
        f"  <code>{label}</code>\n"
        f"\n"
        f"  🔄  <b>New Value</b>\n"
        f"  <code>{normalized_value}</code>\n"
        f"\n"
        f"╰─────────────────────╯\n"
        f"\n"
        f"<i>Tap <b>Save Change</b> to apply, or <b>Go Back</b> to discard.</i>",
        reply_markup=kb,
    )
    logger.debug(
        "process_correction_input: showing confirm/cancel for field=%s value=%r",
        field_name, normalized_value,
    )
    return WAITING_FOR_CONFIRMATION


async def handle_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handles ✅ Confirm and ❌ Cancel after the user types a new field value."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        logger.warning("handle_confirmation: missing query or user_data")
        return ConversationHandler.END

    await query.answer()
    cb = CallbackDataHelper.decode(query.data)
    submission_id = context.user_data.get("editing_submission_id") or cb.target_id
    field_name = context.user_data.get("editing_field_name")
    pending_value = context.user_data.get("pending_field_value")

    logger.info(
        "handle_confirmation: action=%s submission=%s field=%s pending=%r",
        cb.action, submission_id, field_name, pending_value,
    )

    allowed, _, tg_id = await ensure_user(update)
    if not allowed or not tg_id:
        logger.warning("handle_confirmation: access denied")
        return ConversationHandler.END

    try:
        async with get_db_session() as session:
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(tg_id)
            if not db_user or not submission_id:
                logger.warning(
                    "handle_confirmation: DB user or submission_id missing (user=%s sub=%s)",
                    tg_id, submission_id,
                )
                return ConversationHandler.END

            service = SubmissionService(session)

            if cb.action == "doc:confirm" and field_name and pending_value is not None:
                # Show live animated saving transition
                try:
                    await _safe_edit(
                        query,
                        f"╭────── ⚡ <b>Saving & Re-rendering</b> ──────╮\n"
                        f"\n"
                        f"  <code>🎨  [ ▰▰▰▰▰▰▰▰▰▱ ] 90%</code>\n"
                        f"\n"
                        f"  Generating updated high-res label graphic…\n"
                        f"\n"
                        f"╰──────────────────────────────────╯"
                    )
                except Exception:
                    pass

                # ✅ Save the pending value
                sub = await service.update_corrected_field(
                    submission_id, db_user.id, field_name, pending_value
                )
                caption_prefix = (
                    f"✨ ✦ <b>SAVED & RE-RENDERED!</b> ✦ ✨\n"
                    f"📌 <b>{field_name.replace('_', ' ').title()}</b> → <code>{pending_value}</code>\n\n"
                )
                logger.info(
                    "handle_confirmation: confirmed — saved field=%s value=%r for submission=%s",
                    field_name, pending_value, submission_id,
                )
            else:
                # ❌ Discard — re-fetch unchanged submission
                from app.database.repositories import SubmissionRepository
                sub_repo = SubmissionRepository(session)
                sub = await sub_repo.get_by_id(submission_id)
                if not sub:
                    logger.warning("handle_confirmation: submission %s not found on cancel", submission_id)
                    return ConversationHandler.END
                caption_prefix = "↩️ <b>Edit Cancelled. No changes made.</b>\n\n"
                logger.info(
                    "handle_confirmation: cancelled — discarding pending value for field=%s submission=%s",
                    field_name, submission_id,
                )

            # Build and send the updated (or unchanged) receipt photo
            doc_name = sub.template_id or sub.document_category
            is_shipping = "shipping_label" in sub.document_category
            merged_fields = dict(sub.extracted_fields or {})
            merged_fields.update(sub.corrected_fields or {})

            text = MessageRenderer.render_final_updated_receipt(
                document_type=doc_name,
                confidence=sub.match_confidence,
                extracted_fields=sub.extracted_fields,
                corrected_fields=sub.corrected_fields,
            )
            kb = get_result_keyboard(
                submission_id,
                available_fields=list(merged_fields.keys()),
                is_shipping_label=is_shipping,
            )

            img = ReceiptImageGenerator.generate_receipt_image(doc_name, merged_fields, is_shipping=is_shipping)
            img_bytes = ReceiptImageGenerator.get_image_bytes(img, format="PNG")

            if update.effective_chat:
                # Native chat action
                try:
                    await context.bot.send_chat_action(
                        chat_id=update.effective_chat.id, action="upload_photo"
                    )
                except Exception:
                    pass

                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=io.BytesIO(img_bytes),
                    caption=caption_prefix + text,
                    parse_mode="HTML",
                    reply_markup=kb,
                )
    except Exception:
        logger.exception(
            "handle_confirmation: error processing action=%s for submission=%s user=%s",
            cb.action, submission_id, tg_id,
        )
        return ConversationHandler.END

    # Clear all editing state
    for key in ("editing_submission_id", "editing_field_name", "pending_field_value",
                "editing_dropdown_options", "editing_submission_fields"):
        context.user_data.pop(key, None)
    return ConversationHandler.END


async def cancel_correction(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    tg_id = update.effective_user.id if update.effective_user else "unknown"
    submission_id = context.user_data.get("editing_submission_id") if context.user_data else None
    logger.info(
        "cancel_correction: user=%s cancelled correction for submission=%s", tg_id, submission_id
    )
    if context.user_data is not None:
        context.user_data.pop("editing_submission_id", None)
        context.user_data.pop("editing_field_name", None)
    if update.message:
        await update.message.reply_text("🚫 Field correction cancelled.")
    return ConversationHandler.END
