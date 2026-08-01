import re
from typing import Any, Optional


class ValidationService:
    @staticmethod
    def normalize_tracking_number(raw_value: str) -> str:
        """Removes spaces, hyphens, and non-alphanumeric chars from tracking numbers."""
        if not raw_value:
            return ""
        # If it contains digits only with spaces/hyphens (e.g. 9748 8529 81), remove spaces
        cleaned = re.sub(r"[\s-]+", "", raw_value.strip())
        return cleaned.upper()

    @staticmethod
    def normalize_currency(raw_value: str) -> Optional[str]:
        if not raw_value:
            return None
        match = re.search(r"(\d+(?:\.\d{2})?)", raw_value.replace(",", ""))
        if match:
            try:
                val = float(match.group(1))
                return f"${val:.2f}"
            except ValueError:
                pass
        return None

    @staticmethod
    def normalize_date(raw_value: str) -> Optional[str]:
        if not raw_value:
            return None
        # Extract standard date patterns MM/DD/YYYY or YYYY-MM-DD
        match = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b", raw_value)
        if match:
            return match.group(1)
        return raw_value.strip()

    @staticmethod
    def apply_normalization(value: str, norm_type: Optional[str]) -> str:
        if not value or not norm_type:
            return value.strip() if isinstance(value, str) else value
            
        norm_type = norm_type.lower()
        if norm_type == "digits_only":
            return re.sub(r"\D", "", value)
        elif norm_type == "currency":
            res = ValidationService.normalize_currency(value)
            return res if res else value.strip()
        elif norm_type == "date":
            res = ValidationService.normalize_date(value)
            return res if res else value.strip()
        elif norm_type == "uppercase":
            return re.sub(r"\s+", "", value.strip().upper())
        return value.strip()
