import re
from typing import Any, Dict, Optional

from app.services.validation_service import ValidationService
from app.templates.schemas import FieldExtractionRule, TemplateDefinition


class FieldExtractionService:
    @staticmethod
    def extract_fields(
        template: TemplateDefinition, ocr_text: str
    ) -> Dict[str, Any]:
        extracted: Dict[str, Any] = {}
        lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]

        for field_name, rule in template.fields.items():
            val = FieldExtractionService._extract_single_field(rule, ocr_text, lines)
            if val:
                if rule.normalize:
                    val = ValidationService.apply_normalization(val, rule.normalize)
                extracted[field_name] = val

        return extracted

    @staticmethod
    def _extract_single_field(
        rule: FieldExtractionRule, ocr_text: str, lines: list[str]
    ) -> Optional[str]:
        rule_type = rule.type.lower()

        if rule_type == "constant":
            return rule.value

        elif rule_type == "regex" and rule.patterns:
            for pattern in rule.patterns:
                try:
                    match = re.search(pattern, ocr_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        # Return capture group 1 if available, else group 0
                        if match.groups():
                            return match.group(1).strip()
                        return match.group(0).strip()
                except Exception:
                    continue

        elif rule_type == "anchored_text" and rule.anchor:
            anchor_upper = rule.anchor.upper()
            for idx, line in enumerate(lines):
                if anchor_upper in line.upper():
                    # Check if text is on same line after anchor
                    pos = line.upper().find(anchor_upper) + len(anchor_upper)
                    remainder = line[pos:].strip(" :.-")
                    if remainder and len(remainder) > 1:
                        return remainder
                    # Otherwise look at next non-empty line
                    if idx + 1 < len(lines):
                        return lines[idx + 1].strip()

        elif rule_type == "anchored_block" and rule.anchor:
            anchor_upper = rule.anchor.upper()
            for idx, line in enumerate(lines):
                if anchor_upper in line.upper():
                    block_lines = lines[idx + 1 : idx + 4]
                    if block_lines:
                        return ", ".join(block_lines)

        return None
