from typing import Any, Dict, List, Optional
from app.database.models import Submission
from app.services.masking_service import SensitiveDataMasker
from app.utils.telegram_formatting import escape_html


# ─────────────────────────────────────────────
# BRAND CONSTANTS
# ─────────────────────────────────────────────
_BRAND = "𝐋𝐚𝐛𝐞𝐥𝐋𝐞𝐧𝐬"
_DIVIDER = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
_DIVIDER_HEAVY = "━━━━━━━━━━━━━━━━━━━━━"
_DIVIDER_LIGHT = "· · · · · · · · · · · · ·"
_CORNER_L = "╭"
_CORNER_R = "╮"
_CORNER_BL = "╰"
_CORNER_BR = "╯"
_VBAR = "│"

# Animated loading bar frames — cycle these per-stage
_LOADING_BARS = [
    "🌀  [ ▱▱▱▱▱▱▱▱▱▱ ]  0%",
    "🌀  [ ▰▱▱▱▱▱▱▱▱▱ ] 10%",
    "⚡  [ ▰▰▱▱▱▱▱▱▱▱ ] 20%",
    "⚡  [ ▰▰▰▱▱▱▱▱▱▱ ] 35%",
    "🧠  [ ▰▰▰▰▰▱▱▱▱▱ ] 50%",
    "🧠  [ ▰▰▰▰▰▰▰▱▱▱ ] 70%",
    "🎨  [ ▰▰▰▰▰▰▰▰▰▱ ] 90%",
    "✨  [ ▰▰▰▰▰▰▰▰▰▰ ] 100%",
]

# Confidence tier styling
def _conf_bar(pct: int) -> str:
    filled = round(pct / 10)
    empty = 10 - filled
    if pct >= 80:
        block = "█"
        badge = "🔥 High Match"
    elif pct >= 55:
        block = "▓"
        badge = "⚡ Medium Match"
    else:
        block = "░"
        badge = "⚠️ Low Match"
    return f"{block * filled}{'▒' * empty} <b>{pct}%</b> <i>({badge})</i>"


class MessageRenderer:

    # ─── WELCOME / START ──────────────────────────────────────────────────────

    @staticmethod
    def render_start_message(display_name: Optional[str] = None) -> str:
        name = escape_html(display_name or "there")
        return (
            f"╭───── ✨ ✦ <b>{_BRAND}</b> ✦ ✨ ─────╮\n"
            f"\n"
            f"👋  <b>Welcome, {name}!</b>\n"
            f"\n"
            f"⚡  <b>AI-Powered Document Engine</b>\n"
            f"Send any photo or document and watch the AI\n"
            f"extract, edit, and re-render high-res labels!\n"
            f"\n"
            f"{_DIVIDER}\n"
            f"\n"
            f"  🧾  <b>Receipts</b>  ·  💳  <b>Invoices</b>  ·  📦  <b>Labels</b>\n"
            f"\n"
            f"{_DIVIDER}\n"
            f"\n"
            f"🚀  Tap <b>Upload Document</b> below or drop\n"
            f"     a photo right here to start!\n"
            f"\n"
            f"╰────────────────────────────╯"
        )

    # ─── HELP ────────────────────────────────────────────────────────────────

    @staticmethod
    def render_help_message() -> str:
        return (
            f"╭──── ❓ Help Guide ────╮\n"
            f"\n"
            f"<b>How to use {_BRAND}:</b>\n"
            f"\n"
            f"  <b>1.</b>  📤  Send any photo or file\n"
            f"  <b>2.</b>  🔍  AI scans &amp; identifies the doc\n"
            f"  <b>3.</b>  📋  Review extracted fields\n"
            f"  <b>4.</b>  ✏️  Edit any field if needed\n"
            f"  <b>5.</b>  ✅  Approve to save to history\n"
            f"\n"
            f"{_DIVIDER}\n"
            f"\n"
            f"📁  <b>Supported formats</b>\n"
            f"     JPG  ·  PNG  ·  WEBP  ·  PDF\n"
            f"\n"
            f"📦  <b>Document types</b>\n"
            f"     Receipts  ·  Invoices\n"
            f"     Shipping labels (USPS / UPS / FedEx)\n"
            f"\n"
            f"╰─────────────────────╯"
        )

    # ─── PRIVACY ─────────────────────────────────────────────────────────────

    @staticmethod
    def render_privacy_message() -> str:
        return (
            f"╭──── 🔒 Privacy Policy ────╮\n"
            f"\n"
            f"  🛡  <b>Your data is protected</b>\n"
            f"\n"
            f"  ✅  Files processed and deleted instantly\n"
            f"  ✅  Tracking numbers &amp; cards are masked\n"
            f"  ✅  Only approved docs saved to history\n"
            f"  ✅  Delete your submissions anytime\n"
            f"\n"
            f"{_DIVIDER}\n"
            f"\n"
            f"  <i>We never sell or share your data.</i>\n"
            f"\n"
            f"╰─────────────────────╯"
        )

    # ─── UPLOAD PROMPT ───────────────────────────────────────────────────────

    @staticmethod
    def render_upload_instructions() -> str:
        return (
            f"╭──── 📤 Upload ────╮\n"
            f"\n"
            f"Drop your document here or send it\n"
            f"as a <b>photo</b> or <b>file attachment</b>.\n"
            f"\n"
            f"{_DIVIDER}\n"
            f"\n"
            f"  💡 <b>Tips for best results:</b>\n"
            f"  ·  Good lighting, no dark shadows\n"
            f"  ·  Text clearly visible &amp; in focus\n"
            f"  ·  Avoid extreme angles\n"
            f"\n"
            f"╰─────────────────╯"
        )

    # ─── ANIMATED PROCESSING STAGES ──────────────────────────────────────────

    @staticmethod
    def render_processing_stage(stage_message: str, step: int = 0) -> str:
        """
        Progressive animated loader with custom progress bars and frame icons.
        """
        bar = _LOADING_BARS[min(step, len(_LOADING_BARS) - 1)]
        return (
            f"╭────── ⚡ <b>AI Processing Engine</b> ──────╮\n"
            f"\n"
            f"  <code>{bar}</code>\n"
            f"\n"
            f"  {stage_message}\n"
            f"\n"
            f"╰──────────────────────────────────╯"
        )

    @staticmethod
    def render_processing_stage_1() -> str:
        return MessageRenderer.render_processing_stage("📥  <b>Receiving file from Telegram…</b>", step=1)

    @staticmethod
    def render_processing_stage_2() -> str:
        return MessageRenderer.render_processing_stage("⚡  <b>Running Neural OCR Text Engine…</b>", step=3)

    @staticmethod
    def render_processing_stage_3() -> str:
        return MessageRenderer.render_processing_stage("🧠  <b>Matching Template Geometry…</b>", step=5)

    @staticmethod
    def render_processing_stage_4() -> str:
        return MessageRenderer.render_processing_stage("🎨  <b>Rendering High-Res Preview Graphic…</b>", step=7)

    # ─── RESULT SUMMARY ──────────────────────────────────────────────────────

    @staticmethod
    def render_result_summary(
        document_type: str,
        confidence: float,
        extracted_fields: Dict[str, Any],
        corrected_fields: Dict[str, Any],
    ) -> str:
        conf_pct = round(confidence * 100)
        bar = _conf_bar(conf_pct)
        doc_label = escape_html(document_type.replace("_", " ").title())

        lines = [
            f"╭──── ✅ Document Scanned ────╮",
            f"",
            f"  📄  <b>{doc_label}</b>",
            f"",
            f"  <b>Confidence</b>",
            f"  {bar}",
            f"",
            f"{_DIVIDER}",
            f"",
            f"  <b>Extracted Fields</b>",
            f"",
        ]

        merged_fields = dict(extracted_fields or {})
        merged_fields.update(corrected_fields or {})

        for k, val in merged_fields.items():
            label = escape_html(k.replace("_", " ").title())
            value = escape_html(str(val))
            is_corrected = k in (corrected_fields or {})
            marker = "  ✏️" if is_corrected else ""
            lines.append(f"  {_VBAR}  <b>{label}</b>{marker}")
            lines.append(f"  {_VBAR}  <code>{value}</code>")
            lines.append(f"  {_VBAR}")

        if not merged_fields:
            lines.append(f"  <i>No fields could be extracted.</i>")

        lines.append(f"")
        lines.append(f"<i>Review the fields below or tap ✏️ Edit to correct.</i>")
        lines.append(f"")
        lines.append(f"╰─────────────────────╯")

        return "\n".join(lines)

    # ─── FINAL UPDATED RECEIPT ───────────────────────────────────────────────

    @staticmethod
    def render_final_updated_receipt(
        document_type: str,
        confidence: float,
        extracted_fields: Dict[str, Any],
        corrected_fields: Dict[str, Any],
    ) -> str:
        doc_label = escape_html(document_type.replace("_", " ").title())
        conf_pct = round(confidence * 100)

        lines = [
            f"╭────── 🧾 <b>Document Verified</b> ──────╮",
            f"",
            f"  ✨  <b>{doc_label}</b>",
            f"  📊  AI Confidence: <b>{conf_pct}%</b>",
            f"",
            f"{_DIVIDER_HEAVY}",
            f"",
        ]

        merged_fields = dict(extracted_fields or {})
        merged_fields.update(corrected_fields or {})

        for k, val in merged_fields.items():
            label = escape_html(k.replace("_", " ").title())
            value = escape_html(str(val))
            is_corrected = k in (corrected_fields or {})
            marker = " <i>⚡ (edited)</i>" if is_corrected else ""
            lines.append(f"  📌  <b>{label}</b>{marker}")
            lines.append(f"  <code>{value}</code>")
            lines.append(f"")

        if not merged_fields:
            lines.append(f"  <i>No fields found.</i>")
            lines.append(f"")

        lines.append(f"{_DIVIDER_HEAVY}")
        lines.append(f"")
        lines.append(f"  👍 <i>Tap <b>Approve & Save</b> or edit fields below.</i>")
        lines.append(f"")
        lines.append(f"╰──────────────────────────────────╯")

        return "\n".join(lines)

    # ─── DETAILS SCREEN ──────────────────────────────────────────────────────

    @staticmethod
    def render_details_screen(
        document_type: str,
        confidence: float,
        extracted_fields: Dict[str, Any],
        corrected_fields: Dict[str, Any],
    ) -> str:
        conf_pct = round(confidence * 100)
        bar = _conf_bar(conf_pct)
        doc_label = escape_html(document_type.replace("_", " ").title())

        lines = [
            f"╭──── 🔎 Field Inspector ────╮",
            f"",
            f"  📄  <b>{doc_label}</b>",
            f"  {bar}",
            f"",
            f"{_DIVIDER}",
            f"",
        ]

        merged_fields = dict(extracted_fields or {})
        merged_fields.update(corrected_fields or {})

        for k, val in merged_fields.items():
            label = escape_html(k.replace("_", " ").title())
            raw_val = escape_html(str(val)) if val is not None else "<i>—</i>"
            is_corrected = k in (corrected_fields or {})
            source = "  <i>✏️ User Edit</i>" if is_corrected else "  <i>🤖 AI Extracted</i>"
            lines.append(f"  <b>{label}</b>")
            lines.append(f"  {raw_val}")
            lines.append(f"{source}")
            lines.append(f"")

        lines.append(f"╰─────────────────────╯")
        return "\n".join(lines)

    # ─── TRACKING DETAILS ────────────────────────────────────────────────────

    @staticmethod
    def render_tracking_details(tracking_number: str, carrier: str, service: str) -> str:
        masked_tracking = SensitiveDataMasker.mask_tracking_number(tracking_number)
        return (
            f"╭──── 📦 Tracking Info ────╮\n"
            f"\n"
            f"  🚚  <b>{escape_html(carrier)}</b>\n"
            f"  📋  {escape_html(service)}\n"
            f"\n"
            f"{_DIVIDER}\n"
            f"\n"
            f"  <b>Tracking Number</b>\n"
            f"  <code>{escape_html(masked_tracking)}</code>\n"
            f"\n"
            f"  <b>Full (Raw)</b>\n"
            f"  <code>{escape_html(tracking_number)}</code>\n"
            f"\n"
            f"{_DIVIDER}\n"
            f"\n"
            f"  <i>Visit the carrier's site for live tracking.</i>\n"
            f"\n"
            f"╰─────────────────────╯"
        )

    # ─── LOW CONFIDENCE ──────────────────────────────────────────────────────

    @staticmethod
    def render_low_confidence(document_type: str, confidence: float) -> str:
        conf_pct = round(confidence * 100)
        doc_label = escape_html(document_type.replace("_", " ").title())
        return (
            f"╭──── ⚠️ Low Confidence ────╮\n"
            f"\n"
            f"  I think this might be:\n"
            f"  📄  <b>{doc_label}</b>\n"
            f"\n"
            f"  Confidence: <b>{conf_pct}%</b>\n"
            f"  <code>{'░' * round(conf_pct / 10)}{'▒' * (10 - round(conf_pct / 10))}</code>\n"
            f"\n"
            f"{_DIVIDER}\n"
            f"\n"
            f"  Select the correct template below\n"
            f"  or proceed with the best match.\n"
            f"\n"
            f"╰─────────────────────╯"
        )

    # ─── UNKNOWN DOCUMENT ────────────────────────────────────────────────────

    @staticmethod
    def render_unknown_document() -> str:
        return (
            f"╭──── 🧩 Not Identified ────╮\n"
            f"\n"
            f"  I couldn't match this document\n"
            f"  to any known template.\n"
            f"\n"
            f"{_DIVIDER}\n"
            f"\n"
            f"  <b>Try one of these:</b>\n"
            f"  ·  Select a template manually below\n"
            f"  ·  Upload a clearer image\n"
            f"  ·  Ensure text is fully visible\n"
            f"\n"
            f"╰─────────────────────╯"
        )

    # ─── HISTORY LIST ────────────────────────────────────────────────────────

    @staticmethod
    def render_history_list(
        submissions: List[Submission], total_count: int, page: int, per_page: int
    ) -> str:
        if not submissions:
            return (
                f"╭──── 📋 My Documents ────╮\n"
                f"\n"
                f"  <i>No saved submissions yet.</i>\n"
                f"\n"
                f"  Upload your first document to\n"
                f"  start building your history.\n"
                f"\n"
                f"╰─────────────────────╯"
            )

        total_pages = max(1, (total_count + per_page - 1) // per_page)
        lines = [
            f"╭──── 📋 My Documents ────╮",
            f"",
            f"  Page <b>{page + 1}</b> of <b>{total_pages}</b>  ·  <b>{total_count}</b> total",
            f"",
            f"{_DIVIDER}",
            f"",
        ]

        for idx, sub in enumerate(submissions, start=(page * per_page) + 1):
            doc_name = sub.template_id or sub.document_category.replace("_", " ").title()
            status_val = sub.status.value.replace("_", " ").title()
            date_str = sub.created_at.strftime("%d %b %Y")

            # Status badge
            status_icon = {"Approved": "✅", "Pending": "⏳", "Rejected": "❌"}.get(status_val, "📄")

            fields = sub.corrected_fields or sub.extracted_fields or {}
            masked_fields = SensitiveDataMasker.mask_extracted_fields(fields)

            primary_id = ""
            if "tracking_number" in masked_fields:
                primary_id = f"📦 {masked_fields['tracking_number']}"
            elif "total" in masked_fields:
                primary_id = f"💰 {masked_fields['total']}"
            elif "invoice_number" in masked_fields:
                primary_id = f"🔢 {masked_fields['invoice_number']}"

            lines.append(f"  <b>{idx}.</b>  {status_icon}  <b>{escape_html(doc_name)}</b>")
            if primary_id:
                lines.append(f"       <code>{escape_html(primary_id)}</code>")
            lines.append(f"       📅 {date_str}  ·  {escape_html(status_val)}")
            lines.append(f"")

        lines.append(f"╰─────────────────────╯")
        return "\n".join(lines)

    # ─── ERROR ───────────────────────────────────────────────────────────────

    @staticmethod
    def render_error_message(ref_id: str, message: Optional[str] = None) -> str:
        err_msg = escape_html(message) if message else "The document could not be processed."
        return (
            f"╭──── ❌ Processing Error ────╮\n"
            f"\n"
            f"  Something went wrong while\n"
            f"  handling your document.\n"
            f"\n"
            f"{_DIVIDER}\n"
            f"\n"
            f"  <b>Details</b>\n"
            f"  {err_msg}\n"
            f"\n"
            f"  <b>Reference ID</b>\n"
            f"  <code>{ref_id}</code>\n"
            f"\n"
            f"  <i>Share this ID if you contact support.</i>\n"
            f"\n"
            f"╰─────────────────────╯"
        )
