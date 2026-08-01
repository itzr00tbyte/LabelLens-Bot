from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Submission, SubmissionStatus


class SubmissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        telegram_file_id: str,
        original_filename: Optional[str] = None,
        file_hash: Optional[str] = None,
    ) -> Submission:
        submission = Submission(
            user_id=user_id,
            telegram_file_id=telegram_file_id,
            original_filename=original_filename,
            file_hash=file_hash,
            status=SubmissionStatus.UPLOADED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(submission)
        await self.session.flush()
        return submission

    async def get_by_id(self, submission_id: str) -> Optional[Submission]:
        stmt = select(Submission).where(Submission.id == submission_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        submission_id: str,
        status: SubmissionStatus,
        **extra_fields: Any
    ) -> Optional[Submission]:
        submission = await self.get_by_id(submission_id)
        if not submission:
            return None
        
        submission.status = status
        now = datetime.now(timezone.utc)
        submission.updated_at = now
        
        if status == SubmissionStatus.APPROVED:
            submission.approved_at = now
        elif status == SubmissionStatus.REJECTED:
            submission.rejected_at = now
            
        for key, value in extra_fields.items():
            if hasattr(submission, key):
                setattr(submission, key, value)
                
        await self.session.flush()
        return submission

    async def get_user_submissions(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Submission], int]:
        count_stmt = select(func.count(Submission.id)).where(Submission.user_id == user_id)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            select(Submission)
            .where(Submission.user_id == user_id)
            .order_by(Submission.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    async def get_failed_or_low_confidence(
        self, threshold: float = 0.82, limit: int = 20, offset: int = 0
    ) -> List[Submission]:
        stmt = (
            select(Submission)
            .where(
                (Submission.status == SubmissionStatus.FAILED)
                | (Submission.match_confidence < threshold)
            )
            .order_by(Submission.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_stats(self) -> Dict[str, Any]:
        total_stmt = select(func.count(Submission.id))
        total = (await self.session.execute(total_stmt)).scalar_one()

        approved_stmt = select(func.count(Submission.id)).where(Submission.status == SubmissionStatus.APPROVED)
        approved = (await self.session.execute(approved_stmt)).scalar_one()

        rejected_stmt = select(func.count(Submission.id)).where(Submission.status == SubmissionStatus.REJECTED)
        rejected = (await self.session.execute(rejected_stmt)).scalar_one()

        failed_stmt = select(func.count(Submission.id)).where(Submission.status == SubmissionStatus.FAILED)
        failed = (await self.session.execute(failed_stmt)).scalar_one()

        return {
            "total": total,
            "approved": approved,
            "rejected": rejected,
            "failed": failed,
            "pending": total - (approved + rejected + failed)
        }

    async def get_all_approved(self, limit: int = 500) -> List[Submission]:
        stmt = (
            select(Submission)
            .where(Submission.status == SubmissionStatus.APPROVED)
            .order_by(Submission.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
