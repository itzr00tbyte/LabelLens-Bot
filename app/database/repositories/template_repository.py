from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import TemplateModel


class TemplateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_key(self, template_key: str) -> Optional[TemplateModel]:
        stmt = select(TemplateModel).where(TemplateModel.template_key == template_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_templates(self) -> List[TemplateModel]:
        stmt = (
            select(TemplateModel)
            .where(TemplateModel.enabled.is_(True))
            .order_by(TemplateModel.priority.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        template_key: str,
        name: str,
        category: str,
        configuration_json: Dict[str, Any],
        version: int = 1,
        enabled: bool = True,
        priority: int = 100,
    ) -> TemplateModel:
        template = await self.get_by_key(template_key)
        now = datetime.now(timezone.utc)
        if template:
            template.name = name
            template.category = category
            template.version = version
            template.enabled = enabled
            template.priority = priority
            template.configuration_json = configuration_json
            template.updated_at = now
        else:
            template = TemplateModel(
                template_key=template_key,
                name=name,
                category=category,
                version=version,
                enabled=enabled,
                priority=priority,
                configuration_json=configuration_json,
                created_at=now,
                updated_at=now,
            )
            self.session.add(template)
        await self.session.flush()
        return template

    async def set_enabled(self, template_key: str, enabled: bool) -> bool:
        template = await self.get_by_key(template_key)
        if not template:
            return False
        template.enabled = enabled
        await self.session.flush()
        return True

    async def set_priority(self, template_key: str, priority: int) -> bool:
        template = await self.get_by_key(template_key)
        if not template:
            return False
        template.priority = priority
        await self.session.flush()
        return True
