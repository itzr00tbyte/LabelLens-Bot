from typing import Any, Dict, List, Optional
from app.database.models import Submission
from app.services.masking_service import SensitiveDataMasker
from app.utils.telegram_formatting import bold, code, escape_html, italic


class MessageRenderer:
    @staticmethod
    def render_start_message(display_name: Optional[str] = None) -> str:
        name = escape_html(display_name or "there")
        return (
            f"👋 <b>Welcome to Receipt Scanner</b>, {name}!\n\n"
            "Upload a receipt, invoice, or shipping label as a photo or image file.\n\n"
            "The bot will identify the document, extract useful information, and let you review the result before saving it."
        )

    @staticmethod
    def render_help_message() -> str:
        return (
            "❓ <b>Help & Instructions</b>\n\n"
            "<b>How to use Receipt Scanner:</b>\n"
            "1. Tap <b>📤 Upload Document</b> or send any photo/image.\n"
            "2. Wait for the automated processing and OCR scan.\n"
            "3. Review detected fields and confidence score.\n"
            "4. Tap <b>✅ Approve</b> to save or <b>✏️ Correct</b> to adjust any field.\n\n"
            "<b>Supported file types:</b> JPG, PNG, WEBP, PDF."
        )

    @staticmethod
    def render_privacy_message() -> str:
        return (
            "🔒 <b>Privacy Information</b>\n\n"
            "• We prioritize data protection and confidentiality.\n"
            "• Uploaded image files are processed temporarily and deleted.\n"
            "• Sensitive details (tracking numbers, payment cards) are masked by default.\n"
            "• Only approved submissions are stored in your user history.\n"
            "• You can delete your submissions at any time."
        )

    @staticmethod
    def render_upload_instructions() -> str:
        return (
            "📤 <b>Upload Document</b>\n\n"
            "Please send a photo or document file containing a receipt, invoice, or shipping label.\n\n"
            "<i>Tips for best results:</i>\n"
            "• Ensure good lighting\n"
            "• Avoid dark shadows\n"
            "• Keep the text in focus"
        )

    @staticmethod
    def render_processing_stage(stage_message: str) -> str:
        return (
            "⏳ <b>Processing your document...</b>\n\n"
            f"{stage_message}"
        )

    @staticmethod
    def render_result_summary(
        document_type: str,
        confidence: float,
        extracted_fields: Dict[str, Any],
        corrected_fields: Dict[str, Any],
    ) -> str:
        conf_pct = int(round(confidence * 100))
        lines = [
            "✅ <b>Document Detected</b>\n",
            f"<b>Type:</b> {escape_html(document_type)}",
            f"<b>Confidence:</b> {conf_pct}%\n",
            "<b>Extracted Information:</b>"
        ]

        merged_fields = dict(extracted_fields or {})
        merged_fields.update(corrected_fields or {})

        # Display ALL extracted fields directly on the summary screen
        for k, val in merged_fields.items():
            label = k.replace("_", " ").title()
            is_corrected = k in (corrected_fields or {})
            marker = " ✏️" if is_corrected else ""
            lines.append(f"• <b>{escape_html(label)}:</b> <code>{escape_html(str(val))}</code>{marker}")

        if not merged_fields:
            lines.append("• <i>No specific fields extracted.</i>")

        lines.append("\nPlease review all details or tap ✏️ Edit Fields to make changes.")
        return "\n".join(lines)

    @staticmethod
    def render_final_updated_receipt(
        document_type: str,
        confidence: float,
        extracted_fields: Dict[str, Any],
        corrected_fields: Dict[str, Any],
    ) -> str:
        doc_label = document_type.replace("_", " ").title()
        lines = [
            "🧾 <b>UPDATED RECEIPT SUMMARY</b>\n",
            f"<b>Type:</b> {escape_html(doc_label)}",
            "━━━━━━━━━━━━━━━━━━━━━"
        ]

        merged_fields = dict(extracted_fields or {})
        merged_fields.update(corrected_fields or {})

        for k, val in merged_fields.items():
            label = k.replace("_", " ").title()
            is_corrected = k in (corrected_fields or {})
            marker = " ✏️" if is_corrected else ""
            lines.append(f"• <b>{escape_html(label)}:</b> <code>{escape_html(str(val))}</code>{marker}")

        if not merged_fields:
            lines.append("• <i>No specific fields found.</i>")

        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        lines.append("\n✨ <i>Receipt updated live with all your edits.</i>")
        return "\n".join(lines)

    @staticmethod
    def render_details_screen(
        document_type: str,
        confidence: float,
        extracted_fields: Dict[str, Any],
        corrected_fields: Dict[str, Any],
    ) -> str:
        conf_pct = int(round(confidence * 100))
        lines = [
            "🔎 <b>Detailed Field Inspection</b>\n",
            f"<b>Document Type:</b> {escape_html(document_type)}",
            f"<b>Confidence:</b> {conf_pct}%\n",
            "<b>All Extracted Fields:</b>"
        ]

        merged_fields = dict(extracted_fields or {})
        merged_fields.update(corrected_fields or {})

        for k, val in merged_fields.items():
            label = k.replace("_", " ").title()
            is_corrected = k in (corrected_fields or {})
            marker = " (User Corrected ✏️)" if is_corrected else ""
            lines.append(f"• <b>{escape_html(label)}:</b> {escape_html(val)}{marker}")

        return "\n".join(lines)

    @staticmethod
    def render_tracking_details(tracking_number: str, carrier: str, service: str) -> str:
        masked_tracking = SensitiveDataMasker.mask_tracking_number(tracking_number)
        return (
            "📦 <b>Tracking Information</b>\n\n"
            f"<b>Carrier:</b> {escape_html(carrier)}\n"
            f"<b>Service:</b> {escape_html(service)}\n"
            f"<b>Tracking Number:</b> {escape_html(masked_tracking)}\n"
            f"<b>Full Number (Raw):</b> <code>{escape_html(tracking_number)}</code>\n\n"
            "<i>Note: Check official carrier tracking portal for real-time transit status.</i>"
        )

    @staticmethod
    def render_low_confidence(document_type: str, confidence: float) -> str:
        conf_pct = int(round(confidence * 100))
        return (
            "⚠️ <b>Possible Match</b>\n\n"
            "I found a likely document type, but the confidence is lower than usual.\n\n"
            f"<b>Possible type:</b> {escape_html(document_type)}\n"
            f"<b>Confidence:</b> {conf_pct}%"
        )

    @staticmethod
    def render_unknown_document() -> str:
        return (
            "🧩 <b>Document Type Not Identified</b>\n\n"
            "Choose the closest template manually or upload a clearer image."
        )

    @staticmethod
    def render_history_list(
        submissions: List[Submission], total_count: int, page: int, per_page: int
    ) -> str:
        if not submissions:
            return "📋 <b>My Submissions</b>\n\n<i>You have no saved submissions yet.</i>"

        lines = ["📋 <b>My Submissions</b>\n"]
        for idx, sub in enumerate(submissions, start=(page * per_page) + 1):
            doc_name = sub.template_id or sub.document_category.replace("_", " ").title()
            status_str = sub.status.value.replace("_", " ").title()
            date_str = sub.created_at.strftime("%d %b %Y")
            
            # Primary identifier (tracking number or total)
            primary_id = ""
            fields = sub.corrected_fields or sub.extracted_fields or {}
            masked_fields = SensitiveDataMasker.mask_extracted_fields(fields)
            if "tracking_number" in masked_fields:
                primary_id = f"Tracking: {masked_fields['tracking_number']}"
            elif "total" in masked_fields:
                primary_id = f"Total: {masked_fields['total']}"
            elif "invoice_number" in masked_fields:
                primary_id = f"Invoice: {masked_fields['invoice_number']}"

            lines.append(f"<b>{idx}. {escape_html(doc_name)}</b>")
            if primary_id:
                lines.append(escape_html(primary_id))
            lines.append(f"Status: {escape_html(status_str)}")
            lines.append(f"Date: {date_str}\n")

        return "\n".join(lines)

    @staticmethod
    def render_error_message(ref_id: str, message: Optional[str] = None) -> str:
        err_msg = escape_html(message) if message else "The document could not be processed."
        return (
            "❌ <b>Processing Failed</b>\n\n"
            f"{err_msg}\n\n"
            f"Reference: <code>{ref_id}</code>"
        )
