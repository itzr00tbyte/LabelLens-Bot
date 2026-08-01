from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.utils.callback_data import CallbackDataHelper


# ── Field-type emoji mapping ─────────────────────────────────────────────────
# Maps lowercase field name keywords → display emoji
_FIELD_EMOJI: list[tuple[str, str]] = [
    ("carrier",            "🚚"),
    ("service",            "⚡"),
    ("tracking_number",    "🔍"),
    ("tracking",           "🔍"),
    ("recipient_name",     "👤"),
    ("recipient_address",  "📍"),
    ("recipient",          "👤"),
    ("sender_name",        "📤"),
    ("sender_address",     "📤"),
    ("sender",             "📤"),
    ("shipper",            "📤"),
    ("ship_to",            "📍"),
    ("ship_from",          "📤"),
    ("date",               "📅"),
    ("weight",             "⚖️"),
    ("total",              "💰"),
    ("subtotal",           "💳"),
    ("tax",                "🧾"),
    ("price",              "💰"),
    ("amount",             "💳"),
    ("invoice",            "🗂️"),
    ("order",              "🛒"),
    ("store",              "🏪"),
    ("merchant",           "🏪"),
    ("item",               "📦"),
    ("product",            "📦"),
    ("address",            "📍"),
    ("city",               "🏙️"),
    ("state",              "🗺️"),
    ("zip",                "📮"),
    ("phone",              "📞"),
    ("email",              "📧"),
    ("name",               "🏷️"),
    ("description",        "📝"),
    ("note",               "📝"),
    ("barcode",            "▐█"),
]


def _field_emoji(field_name: str) -> str:
    """Return the best matching emoji for a field name."""
    lower = field_name.lower()
    for keyword, emoji in _FIELD_EMOJI:
        if keyword in lower:
            return emoji
    return "✏️"


def get_result_keyboard(
    submission_id: str,
    available_fields: Optional[List[str]] = None,
    is_shipping_label: bool = False,
) -> InlineKeyboardMarkup:
    rows = []

    # ── Approve & Save — full-width, prominent ────────────────────────────────
    rows.append([
        InlineKeyboardButton(
            "👍  Approve & Save",
            callback_data=CallbackDataHelper.encode("doc:app", submission_id),
        )
    ])

    # ── Edit field buttons — field-specific emojis, 2 per row ─────────────────
    if available_fields:
        editable_fields = [
            f for f in available_fields
            if f.lower() not in ["tracking_barcode", "barcode"]
        ]
        row = []
        for field_name in editable_fields:
            emoji = _field_emoji(field_name)
            label = field_name.replace("_", " ").title()
            row.append(
                InlineKeyboardButton(
                    f"{emoji}  {label}",
                    callback_data=CallbackDataHelper.encode(
                        "doc:field", submission_id, field_name[:16]
                    ),
                )
            )
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)

    # ── Download row ──────────────────────────────────────────────────────────
    rows.append([
        InlineKeyboardButton(
            "🖼  Image",
            callback_data=CallbackDataHelper.encode("doc:down_img", submission_id),
        ),
        InlineKeyboardButton(
            "📄  PDF",
            callback_data=CallbackDataHelper.encode("doc:down_pdf", submission_id),
        ),
    ])

    # ── Upload new ────────────────────────────────────────────────────────────
    rows.append([
        InlineKeyboardButton(
            "📤  Upload New Document",
            callback_data=CallbackDataHelper.encode("upload"),
        )
    ])

    return InlineKeyboardMarkup(rows)


def get_low_confidence_keyboard(submission_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✏️  Edit Fields",
                callback_data=CallbackDataHelper.encode("doc:corr", submission_id),
            ),
        ],
        [
            InlineKeyboardButton(
                "🖼  Image",
                callback_data=CallbackDataHelper.encode("doc:down_img", submission_id),
            ),
            InlineKeyboardButton(
                "📄  PDF",
                callback_data=CallbackDataHelper.encode("doc:down_pdf", submission_id),
            ),
        ],
        [
            InlineKeyboardButton(
                "📤  Upload New Document",
                callback_data=CallbackDataHelper.encode("upload"),
            )
        ],
    ])


def get_unknown_document_keyboard(submission_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🧩  Choose Template",
                callback_data=CallbackDataHelper.encode("tpl:choose", submission_id),
            )
        ],
        [
            InlineKeyboardButton(
                "📤  New Image",
                callback_data=CallbackDataHelper.encode("upload"),
            )
        ],
    ])


def get_correction_fields_keyboard(
    submission_id: str, available_fields: List[str]
) -> InlineKeyboardMarkup:
    buttons = []
    row = []

    for field_name in available_fields:
        emoji = _field_emoji(field_name)
        label = field_name.replace("_", " ").title()
        row.append(
            InlineKeyboardButton(
                f"{emoji}  {label}",
                callback_data=CallbackDataHelper.encode(
                    "doc:field", submission_id, field_name[:16]
                ),
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(
            "✅  Done Editing",
            callback_data=CallbackDataHelper.encode("doc:rev", submission_id),
        )
    ])
    return InlineKeyboardMarkup(buttons)


def get_dropdown_options_keyboard(
    submission_id: str, field_name: str, options: List[str]
) -> InlineKeyboardMarkup:
    emoji = _field_emoji(field_name)
    buttons = []
    # 1 option per row for full-width dropdown appearance
    for idx, option in enumerate(options):
        buttons.append([
            InlineKeyboardButton(
                f"{emoji}  {option}",
                callback_data=CallbackDataHelper.encode(
                    "doc:opt", submission_id[:8], str(idx)
                ),
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            "⬅️  Back to Fields",
            callback_data=CallbackDataHelper.encode("doc:corr", submission_id),
        )
    ])
    return InlineKeyboardMarkup(buttons)


def get_confirmation_keyboard(submission_id: str) -> InlineKeyboardMarkup:
    """Shown after the user types a new value — lets them confirm or discard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅  Save Change",
                callback_data=CallbackDataHelper.encode("doc:confirm", submission_id),
            ),
            InlineKeyboardButton(
                "↩️  Go Back",
                callback_data=CallbackDataHelper.encode("doc:cancel_edit", submission_id),
            ),
        ]
    ])
