from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(
        self,
        action: str,
        user_id: Optional[int] = None,
        submission_id: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        log_entry = AuditLog(
            user_id=user_id,
            submission_id=submission_id,
            action=action,
            metadata_json=metadata_json,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(log_entry)
        await self.session.flush()
        return log_entry

    async def get_logs_for_submission(self, submission_id: str) -> List[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.submission_id == submission_id)
            .order_by(AuditLog.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
