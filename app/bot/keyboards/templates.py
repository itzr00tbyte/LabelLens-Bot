from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.templates.schemas import TemplateDefinition
from app.utils.callback_data import CallbackDataHelper


def get_templates_selection_keyboard(
    submission_id: str, templates: List[TemplateDefinition], page: int = 0, per_page: int = 6
) -> InlineKeyboardMarkup:
    total = len(templates)
    start_idx = page * per_page
    page_templates = templates[start_idx : start_idx + per_page]

    rows = []
    # 2 buttons per row
    row = []
    for tpl in page_templates:
        row.append(
            InlineKeyboardButton(
                tpl.name, callback_data=CallbackDataHelper.encode("tpl:sel", submission_id, tpl.id)
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    nav_row = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=CallbackDataHelper.encode("tpl:pg", submission_id, str(page - 1)))
        )
    if start_idx + per_page < total:
        nav_row.append(
            InlineKeyboardButton("Next ➡️", callback_data=CallbackDataHelper.encode("tpl:pg", submission_id, str(page + 1)))
        )
    if nav_row:
        rows.append(nav_row)

    rows.append([
        InlineKeyboardButton("⬅️ Back", callback_data=CallbackDataHelper.encode("doc:rev", submission_id))
    ])
    return InlineKeyboardMarkup(rows)
