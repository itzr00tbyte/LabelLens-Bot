from datetime import datetime, timezone
import hashlib
import logging
from typing import Any, Dict, Optional, Tuple

from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import Submission, SubmissionStatus
from app.database.repositories import (
    AuditRepository,
    SubmissionRepository,
    UserRepository,
)
from app.services.extraction_service import FieldExtractionService
from app.services.image_service import ImageProcessingService
from app.services.ocr_service import OCRService
from app.services.template_matcher import MatchResult, TemplateMatcher

logger = logging.getLogger(__name__)


class SubmissionService:
    ALLOWED_TRANSITIONS = {
        SubmissionStatus.UPLOADED: [SubmissionStatus.PROCESSING, SubmissionStatus.FAILED],
        SubmissionStatus.PROCESSING: [SubmissionStatus.MATCHED, SubmissionStatus.NEEDS_REVIEW, SubmissionStatus.FAILED],
        SubmissionStatus.MATCHED: [SubmissionStatus.NEEDS_REVIEW, SubmissionStatus.APPROVED, SubmissionStatus.REJECTED, SubmissionStatus.FAILED],
        SubmissionStatus.NEEDS_REVIEW: [SubmissionStatus.MATCHED, SubmissionStatus.APPROVED, SubmissionStatus.REJECTED, SubmissionStatus.FAILED],
        SubmissionStatus.APPROVED: [SubmissionStatus.DELETED],
        SubmissionStatus.REJECTED: [SubmissionStatus.DELETED, SubmissionStatus.NEEDS_REVIEW],
        SubmissionStatus.FAILED: [SubmissionStatus.PROCESSING, SubmissionStatus.DELETED],
        SubmissionStatus.DELETED: [],
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.sub_repo = SubmissionRepository(session)
        self.audit_repo = AuditRepository(session)
        self.matcher = TemplateMatcher()

    async def process_document_submission(
        self,
        submission_id: str,
        image_bytes: bytes,
        status_update_callback: Optional[Any] = None,
    ) -> Tuple[Submission, MatchResult]:
        submission = await self.sub_repo.get_by_id(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found.")

        await self._transition_status(submission, SubmissionStatus.PROCESSING, "Started processing document")

        try:
            # 1. Preparing image
            if status_update_callback:
                await status_update_callback("🖼 Preparing image...")
            
            file_hash = hashlib.sha256(image_bytes).hexdigest()
            submission.file_hash = file_hash
            
            image = ImageProcessingService.load_image(image_bytes)
            resized_image = ImageProcessingService.resize_max_dim(image)
            preprocessed_np = ImageProcessingService.preprocess_for_ocr(resized_image)

            # 2. Reading text
            if status_update_callback:
                await status_update_callback("🔍 Reading text...")
                
            ocr_res = await OCRService.extract_text(resized_image, preprocessed_np)
            submission.ocr_text = ocr_res.text if settings.STORE_OCR_TEXT else None
            submission.ocr_confidence = ocr_res.confidence

            if not ocr_res.text or len(ocr_res.text.strip()) < 5:
                await self._transition_status(
                    submission, SubmissionStatus.FAILED, "OCR yielded insufficient text"
                )
                return submission, MatchResult(template=None, score=0.0)

            # 3. Matching template
            if status_update_callback:
                await status_update_callback("🧩 Matching template...")

            match_res = self.matcher.match(ocr_res.text, ocr_res.confidence)

            # 4. Extracting fields
            if status_update_callback:
                await status_update_callback("✅ Preparing result...")

            if match_res.template:
                extracted = FieldExtractionService.extract_fields(match_res.template, ocr_res.text)
                submission.template_id = match_res.template.id
                submission.document_category = match_res.template.category
                submission.match_confidence = match_res.score
                submission.extracted_fields = extracted

                target_status = (
                    SubmissionStatus.MATCHED
                    if match_res.score >= settings.LOW_CONFIDENCE_THRESHOLD
                    else SubmissionStatus.NEEDS_REVIEW
                )
                await self._transition_status(
                    submission, target_status, f"Matched template {match_res.template.id} with score {match_res.score}"
                )
            else:
                submission.match_confidence = match_res.score
                submission.document_category = "unknown"
                await self._transition_status(
                    submission, SubmissionStatus.NEEDS_REVIEW, "No confident template match"
                )

            await self.session.commit()
            return submission, match_res

        except Exception as e:
            logger.error(f"Error processing submission {submission_id}: {e}", exc_info=True)
            await self._transition_status(submission, SubmissionStatus.FAILED, f"Exception: {str(e)}")
            await self.session.commit()
            raise

    async def approve_submission(self, submission_id: str, user_id: int) -> Submission:
        submission = await self.sub_repo.get_by_id(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found.")
        await self._verify_ownership_or_admin(submission, user_id)
        await self._transition_status(submission, SubmissionStatus.APPROVED, f"Approved by user {user_id}")
        await self.session.commit()
        return submission

    async def reject_submission(self, submission_id: str, user_id: int) -> Submission:
        submission = await self.sub_repo.get_by_id(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found.")
        await self._verify_ownership_or_admin(submission, user_id)
        await self._transition_status(submission, SubmissionStatus.REJECTED, f"Rejected by user {user_id}")
        await self.session.commit()
        return submission

    async def update_corrected_field(
        self, submission_id: str, user_id: int, field_name: str, new_value: str
    ) -> Submission:
        submission = await self.sub_repo.get_by_id(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found.")
        await self._verify_ownership_or_admin(submission, user_id)

        corrected = dict(submission.corrected_fields or {})
        corrected[field_name] = new_value
        submission.corrected_fields = corrected
        submission.updated_at = datetime.now(timezone.utc)

        await self.audit_repo.log_action(
            user_id=user_id,
            submission_id=submission_id,
            action="field_corrected",
            metadata_json={"field": field_name, "value": new_value},
        )
        await self.session.commit()
        return submission

    async def apply_manual_template(
        self, submission_id: str, user_id: int, template_id: str
    ) -> Tuple[Submission, MatchResult]:
        submission = await self.sub_repo.get_by_id(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found.")
        await self._verify_ownership_or_admin(submission, user_id)

        template = self.matcher.loader.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found.")

        ocr_text = submission.ocr_text or ""
        extracted = FieldExtractionService.extract_fields(template, ocr_text)

        submission.template_id = template.id
        submission.document_category = template.category
        submission.extracted_fields = extracted
        submission.match_confidence = 1.0  # Manually set by user

        await self._transition_status(
            submission, SubmissionStatus.MATCHED, f"Manually set template {template.id} by user {user_id}"
        )
        await self.session.commit()

        match_res = MatchResult(template=template, score=1.0, matched_signals=["manual_selection"])
        return submission, match_res

    async def _transition_status(
        self, submission: Submission, new_status: SubmissionStatus, reason: str
    ) -> None:
        current = submission.status
        allowed = self.ALLOWED_TRANSITIONS.get(current, [])
        if new_status not in allowed and current != new_status:
            raise ValueError(f"Invalid state transition from {current.value} to {new_status.value}")

        submission.status = new_status
        submission.updated_at = datetime.now(timezone.utc)
        if new_status == SubmissionStatus.APPROVED:
            submission.approved_at = datetime.now(timezone.utc)
        elif new_status == SubmissionStatus.REJECTED:
            submission.rejected_at = datetime.now(timezone.utc)

        await self.audit_repo.log_action(
            user_id=submission.user_id,
            submission_id=submission.id,
            action=f"status_changed:{new_status.value}",
            metadata_json={"from": current.value, "to": new_status.value, "reason": reason},
        )

    async def _verify_ownership_or_admin(self, submission: Submission, user_id: int) -> None:
        user = await self.user_repo.session.get(submission.user.__class__, user_id)
        if not user:
            raise PermissionError("User not found.")
        if submission.user_id != user.id and user.role != "admin":
            raise PermissionError("Access denied: You do not own this submission.")
