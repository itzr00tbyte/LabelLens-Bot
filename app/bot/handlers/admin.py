import csv
from io import StringIO
import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards.admin import get_admin_dashboard_keyboard
from app.bot.middleware.access_control import ensure_user
from app.database.repositories import SubmissionRepository, TemplateRepository
from app.database.session import get_db_session
from app.templates.loader import default_template_loader
from app.utils.callback_data import CallbackDataHelper

logger = logging.getLogger(__name__)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed or not is_admin:
        if update.message:
            await update.message.reply_text("⛔ Unauthorized: Admin access required.")
        return

    text = "🔐 <b>Admin Dashboard</b>\n\nSelect an administrative action from below:"
    kb = get_admin_dashboard_keyboard()
    if update.message:
        await update.message.reply_html(text, reply_markup=kb)


async def handle_admin_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    allowed, is_admin, tg_id = await ensure_user(update)
    if not allowed or not is_admin:
        await query.answer("⛔ Admin access required.", show_alert=True)
        return

    await query.answer()
    cb = CallbackDataHelper.decode(query.data)

    async with get_db_session() as session:
        sub_repo = SubmissionRepository(session)
        tpl_repo = TemplateRepository(session)

        if cb.action == "menu:admin":
            text = "🔐 <b>Admin Dashboard</b>\n\nSelect an administrative action from below:"
            await query.edit_message_text(
                text, parse_mode="HTML", reply_markup=get_admin_dashboard_keyboard()
            )

        elif cb.action == "adm:stats":
            stats = await sub_repo.get_stats()
            text = (
                "📊 <b>Processing Statistics</b>\n\n"
                f"• <b>Total Submissions:</b> {stats['total']}\n"
                f"• <b>Approved:</b> {stats['approved']}\n"
                f"• <b>Rejected:</b> {stats['rejected']}\n"
                f"• <b>Failed:</b> {stats['failed']}\n"
                f"• <b>Pending Review:</b> {stats['pending']}\n"
            )
            await query.edit_message_text(
                text, parse_mode="HTML", reply_markup=get_admin_dashboard_keyboard()
            )

        elif cb.action == "adm:tpl":
            templates = default_template_loader.list_templates()
            lines = ["🧩 <b>Loaded Document Templates</b>\n"]
            for tpl in templates:
                status_icon = "🟢" if tpl.enabled else "🔴"
                lines.append(
                    f"{status_icon} <b>{tpl.name}</b> (<code>{tpl.id}</code>)\n"
                    f"Priority: {tpl.priority} | Min Score: {tpl.minimum_score}"
                )
            await query.edit_message_text(
                "\n".join(lines),
                parse_mode="HTML",
                reply_markup=get_admin_dashboard_keyboard(),
            )

        elif cb.action == "adm:failed":
            failed_items = await sub_repo.get_failed_or_low_confidence(limit=5)
            if not failed_items:
                await query.edit_message_text(
                    "⚠️ <b>Failed / Low-Confidence Scans</b>\n\nNo failed or low-confidence scans found.",
                    parse_mode="HTML",
                    reply_markup=get_admin_dashboard_keyboard(),
                )
                return

            lines = ["⚠️ <b>Recent Failed / Low-Confidence Scans</b>\n"]
            for item in failed_items:
                lines.append(
                    f"• <code>{item.id[:8]}</code> | Category: {item.document_category} | "
                    f"Conf: {int(item.match_confidence * 100)}% | Status: {item.status.value}"
                )
            await query.edit_message_text(
                "\n".join(lines),
                parse_mode="HTML",
                reply_markup=get_admin_dashboard_keyboard(),
            )

        elif cb.action == "adm:export":
            approved_subs = await sub_repo.get_all_approved(limit=500)
            if not approved_subs:
                await query.edit_message_text(
                    "📤 <b>Export CSV</b>\n\nNo approved records found to export.",
                    parse_mode="HTML",
                    reply_markup=get_admin_dashboard_keyboard(),
                )
                return

            s = StringIO()
            writer = csv.writer(s)
            writer.writerow([
                "SubmissionID", "UserID", "Category", "TemplateID",
                "Confidence", "ApprovedAt", "ExtractedFields"
            ])
            for sub in approved_subs:
                writer.writerow([
                    sub.id, sub.user_id, sub.document_category, sub.template_id,
                    sub.match_confidence, sub.approved_at, str(sub.corrected_fields or sub.extracted_fields)
                ])

            csv_bytes = s.getvalue().encode("utf-8")
            s.close()

            if update.effective_chat:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=csv_bytes,
                    filename="approved_submissions_export.csv",
                    caption="📤 Approved Submissions Export",
                )
