import io
import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.bot.keyboards.result import (
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

WAITING_FOR_CORRECTION_VALUE = 1

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
    if not query or not query.data:
        return ConversationHandler.END

    allowed, _, tg_id = await ensure_user(update)
    if not allowed or not tg_id:
        await query.answer("Access denied.")
        return ConversationHandler.END

    await query.answer()
    cb = CallbackDataHelper.decode(query.data)
    submission_id = cb.target_id

    if not submission_id:
        return ConversationHandler.END

    async with get_db_session() as session:
        repo = SubmissionRepository(session)
        sub = await repo.get_by_id(submission_id)
        if not sub:
            return ConversationHandler.END

        merged = dict(sub.extracted_fields or {})
        merged.update(sub.corrected_fields or {})

        available_fields = list(merged.keys()) if merged else ["merchant_name", "service", "total", "subtotal", "tax", "transaction_date", "address"]

        context.user_data["editing_submission_id"] = submission_id
        context.user_data["editing_submission_fields"] = merged

        kb = get_correction_fields_keyboard(submission_id, available_fields)
        await query.edit_message_text(
            "✏️ <b>Select a field to edit live:</b>",
            parse_mode="HTML",
            reply_markup=kb,
        )

    return WAITING_FOR_CORRECTION_VALUE


async def select_field_to_correct(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    await query.answer()
    cb = CallbackDataHelper.decode(query.data)
    submission_id = context.user_data.get("editing_submission_id") or cb.target_id
    field_key = cb.extra

    if not field_key:
        return ConversationHandler.END

    # Resolve full field name if key was truncated for callback safety
    fields_dict = context.user_data.get("editing_submission_fields") or {}
    full_field_name = field_key
    for original_key in fields_dict.keys():
        if original_key.startswith(field_key) or field_key.startswith(original_key):
            full_field_name = original_key
            break

    context.user_data["editing_submission_id"] = submission_id
    context.user_data["editing_field_name"] = full_field_name

    label = full_field_name.replace("_", " ").title()
    field_lower = full_field_name.lower()

    # Check if field has predefined drop down selection keyboard
    if any(kw in field_lower for kw in ["service", "shipping_type", "mail_class", "delivery_type"]):
        options = SERVICE_DROPDOWN_OPTIONS
        context.user_data["editing_dropdown_options"] = options
        kb = get_dropdown_options_keyboard(submission_id, full_field_name, options)
        await query.edit_message_text(
            f"📦 <b>Select {label}:</b>\n\nChoose an option from the list below:",
            parse_mode="HTML",
            reply_markup=kb,
        )
        return WAITING_FOR_CORRECTION_VALUE
    elif "carrier" in field_lower:
        options = CARRIER_DROPDOWN_OPTIONS
        context.user_data["editing_dropdown_options"] = options
        kb = get_dropdown_options_keyboard(submission_id, full_field_name, options)
        await query.edit_message_text(
            f"🚚 <b>Select Carrier:</b>\n\nChoose a carrier from the list below:",
            parse_mode="HTML",
            reply_markup=kb,
        )
        return WAITING_FOR_CORRECTION_VALUE

    is_address = any(kw in field_lower for kw in ["address", "ship_to", "ship_from", "recipient", "sender", "location"])

    if is_address:
        prompt_text = (
            f"✏️ <b>Edit Address:</b> {label}\n\n"
            "Send a <b>5-digit US Zip Code</b> (e.g. <code>90210</code>, <code>10001</code>, <code>30301</code>) to generate a realistic random address, or type a custom address:"
        )
    else:
        prompt_text = f"✏️ <b>Edit Field:</b> {label}\n\nPlease reply with the new value for <b>{label}</b> (or /cancel):"

    await query.edit_message_text(
        prompt_text,
        parse_mode="HTML",
    )
    return WAITING_FOR_CORRECTION_VALUE


async def handle_dropdown_option(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    await query.answer()
    cb = CallbackDataHelper.decode(query.data)
    opt_idx_str = cb.extra

    submission_id = context.user_data.get("editing_submission_id")
    field_name = context.user_data.get("editing_field_name")
    options = context.user_data.get("editing_dropdown_options", [])

    if not submission_id or not field_name or not opt_idx_str or not opt_idx_str.isdigit():
        return ConversationHandler.END

    opt_idx = int(opt_idx_str)
    if opt_idx < 0 or opt_idx >= len(options):
        return ConversationHandler.END

    selected_value = options[opt_idx]

    allowed, _, tg_id = await ensure_user(update)
    if not allowed or not tg_id:
        return ConversationHandler.END

    async with get_db_session() as session:
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_telegram_id(tg_id)
        if not db_user:
            return ConversationHandler.END

        service = SubmissionService(session)
        sub = await service.update_corrected_field(
            submission_id, db_user.id, field_name, selected_value
        )

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
        kb = get_result_keyboard(submission_id, available_fields=list(merged_fields.keys()), is_shipping_label=is_shipping)

        # Generate updated receipt image
        img = ReceiptImageGenerator.generate_receipt_image(doc_name, merged_fields, is_shipping=is_shipping)
        img_bytes = ReceiptImageGenerator.get_image_bytes(img, format="PNG")

        if update.effective_chat:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(img_bytes),
                caption=f"✅ <b>Field Updated!</b> Set <b>{field_name.replace('_', ' ').title()}</b> to <code>{selected_value}</code>.\n\n" + text,
                parse_mode="HTML",
                reply_markup=kb,
            )

    context.user_data.pop("editing_submission_id", None)
    context.user_data.pop("editing_field_name", None)
    context.user_data.pop("editing_dropdown_options", None)
    return ConversationHandler.END


async def process_correction_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not update.message or not update.message.text:
        return WAITING_FOR_CORRECTION_VALUE

    allowed, _, tg_id = await ensure_user(update)
    if not allowed or not tg_id:
        return ConversationHandler.END

    submission_id = context.user_data.get("editing_submission_id")
    field_name = context.user_data.get("editing_field_name")
    new_raw_value = update.message.text.strip()

    if not submission_id or not field_name:
        await update.message.reply_text("Session expired. Please try uploading your document again.")
        return ConversationHandler.END

    # Check if this is an address field for zip code random generation
    is_address = any(kw in field_name.lower() for kw in ["address", "ship_to", "ship_from", "recipient", "sender", "location"])
    if is_address:
        normalized_value = AddressGenerator.generate_from_input(new_raw_value)
    elif "tracking" in field_name.lower():
        normalized_value = ValidationService.normalize_tracking_number(new_raw_value)
    elif "total" in field_name.lower() or "price" in field_name.lower() or "subtotal" in field_name.lower() or "tax" in field_name.lower():
        curr = ValidationService.normalize_currency(new_raw_value)
        normalized_value = curr if curr else new_raw_value
    else:
        normalized_value = new_raw_value

    async with get_db_session() as session:
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_telegram_id(tg_id)
        if not db_user:
            return ConversationHandler.END

        service = SubmissionService(session)
        sub = await service.update_corrected_field(
            submission_id, db_user.id, field_name, normalized_value
        )

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
        kb = get_result_keyboard(submission_id, available_fields=list(merged_fields.keys()), is_shipping_label=is_shipping)

        # Generate updated receipt image
        img = ReceiptImageGenerator.generate_receipt_image(doc_name, merged_fields, is_shipping=is_shipping)
        img_bytes = ReceiptImageGenerator.get_image_bytes(img, format="PNG")

        if update.effective_chat:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(img_bytes),
                caption=f"✅ <b>Field Updated!</b> <b>{field_name.replace('_', ' ').title()}</b> set to <code>{normalized_value}</code>.\n\n" + text,
                parse_mode="HTML",
                reply_markup=kb,
            )

    # Clear user data state
    context.user_data.pop("editing_submission_id", None)
    context.user_data.pop("editing_field_name", None)
    return ConversationHandler.END


async def cancel_correction(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data.pop("editing_submission_id", None)
    context.user_data.pop("editing_field_name", None)
    if update.message:
        await update.message.reply_text("🚫 Field correction cancelled.")
    return ConversationHandler.END
