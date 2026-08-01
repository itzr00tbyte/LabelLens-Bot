from typing import Dict, List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.utils.callback_data import CallbackDataHelper


def get_result_keyboard(
    submission_id: str,
    available_fields: Optional[List[str]] = None,
    is_shipping_label: bool = False,
) -> InlineKeyboardMarkup:
    rows = []

    if available_fields:
        # Exclude tracking barcode from direct field editing
        editable_fields = [f for f in available_fields if f.lower() not in ["tracking_barcode", "barcode"]]
        row = []
        for field_name in editable_fields:
            label = field_name.replace("_", " ").title()
            row.append(
                InlineKeyboardButton(
                    f"✏️ {label}",
                    callback_data=CallbackDataHelper.encode("doc:field", submission_id, field_name[:16])
                )
            )
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)

    rows.append([
        InlineKeyboardButton("🖼 Download Image", callback_data=CallbackDataHelper.encode("doc:down_img", submission_id)),
        InlineKeyboardButton("📄 Download PDF", callback_data=CallbackDataHelper.encode("doc:down_pdf", submission_id)),
    ])
    rows.append([
        InlineKeyboardButton("📤 Upload New", callback_data=CallbackDataHelper.encode("upload")),
    ])
    return InlineKeyboardMarkup(rows)


def get_low_confidence_keyboard(submission_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Edit Fields", callback_data=CallbackDataHelper.encode("doc:corr", submission_id)),
        ],
        [
            InlineKeyboardButton("🖼 Download Image", callback_data=CallbackDataHelper.encode("doc:down_img", submission_id)),
            InlineKeyboardButton("📄 Download PDF", callback_data=CallbackDataHelper.encode("doc:down_pdf", submission_id)),
        ],
        [
            InlineKeyboardButton("📤 Upload New", callback_data=CallbackDataHelper.encode("upload")),
        ]
    ])


def get_unknown_document_keyboard(submission_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧩 Choose Template", callback_data=CallbackDataHelper.encode("tpl:choose", submission_id))
        ],
        [
            InlineKeyboardButton("📤 New Image", callback_data=CallbackDataHelper.encode("upload")),
        ]
    ])


def get_correction_fields_keyboard(
    submission_id: str, available_fields: List[str]
) -> InlineKeyboardMarkup:
    buttons = []
    row = []

    # All extracted fields are editable
    for field_name in available_fields:
        label = field_name.replace("_", " ").title()
        row.append(
            InlineKeyboardButton(
                f"✏️ {label}",
                callback_data=CallbackDataHelper.encode("doc:field", submission_id, field_name[:16])
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("✅ Done Editing", callback_data=CallbackDataHelper.encode("doc:rev", submission_id))
    ])
    return InlineKeyboardMarkup(buttons)


def get_dropdown_options_keyboard(
    submission_id: str, field_name: str, options: List[str]
) -> InlineKeyboardMarkup:
    buttons = []
    # 1 option per row for full-width drop down appearance
    for idx, option in enumerate(options):
        buttons.append([
            InlineKeyboardButton(
                option,
                callback_data=CallbackDataHelper.encode("doc:opt", submission_id[:8], str(idx))
            )
        ])
    buttons.append([
        InlineKeyboardButton("⬅️ Back to Fields", callback_data=CallbackDataHelper.encode("doc:corr", submission_id))
    ])
    return InlineKeyboardMarkup(buttons)
