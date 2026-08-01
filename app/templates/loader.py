import json
import logging
import os
from typing import Dict, List, Optional

import yaml

from app.config import settings
from app.templates.schemas import TemplateDefinition

logger = logging.getLogger(__name__)


class TemplateLoader:
    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = templates_dir or settings.TEMPLATES_DIR
        self._templates: Dict[str, TemplateDefinition] = {}
        self.reload_templates()

    def reload_templates(self) -> None:
        self._templates.clear()
        if not os.path.exists(self.templates_dir):
            logger.warning(f"Templates directory '{self.templates_dir}' does not exist.")
            return

        for filename in os.listdir(self.templates_dir):
            filepath = os.path.join(self.templates_dir, filename)
            if not os.path.isfile(filepath):
                continue

            try:
                data = None
                if filename.endswith(".json"):
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                elif filename.endswith((".yaml", ".yml")):
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                if data:
                    tpl = TemplateDefinition.model_validate(data)
                    if tpl.enabled:
                        self._templates[tpl.id] = tpl
                        logger.info(f"Loaded template: '{tpl.id}' ({tpl.name})")
            except Exception as e:
                logger.error(f"Failed to load template from '{filepath}': {e}")

    def get_template(self, template_id: str) -> Optional[TemplateDefinition]:
        return self._templates.get(template_id)

    def list_templates(self) -> List[TemplateDefinition]:
        return sorted(self._templates.values(), key=lambda t: t.priority, reverse=True)


default_template_loader = TemplateLoader()
