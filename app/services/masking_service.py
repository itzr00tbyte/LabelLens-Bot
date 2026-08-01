import re
from typing import Any, Dict


class SensitiveDataMasker:
    @staticmethod
    def mask_tracking_number(tracking_no: str) -> str:
        if not tracking_no:
            return ""
        clean = tracking_no.replace(" ", "")
        if len(clean) <= 8:
            return clean[:2] + " •••• " + clean[-2:]
        prefix = clean[:4]
        suffix = clean[-4:]
        middle_length = len(clean) - 8
        blocks = (middle_length // 4) + 1
        masked_middle = " ".join(["••••"] * min(blocks, 3))
        return f"{prefix} {masked_middle} {suffix}"

    @staticmethod
    def mask_card_number(card_no: str) -> str:
        if not card_no:
            return ""
        clean = re.sub(r"\D", "", card_no)
        if len(clean) >= 4:
            return f"•••• {clean[-4:]}"
        return "••••"

    @staticmethod
    def mask_phone(phone: str) -> str:
        if not phone:
            return ""
        clean = re.sub(r"\D", "", phone)
        if len(clean) >= 4:
            return f"••• ••• {clean[-4:]}"
        return "••• ••• ••••"

    @staticmethod
    def mask_email(email: str) -> str:
        if not email or "@" not in email:
            return email or ""
        name, domain = email.split("@", 1)
        if len(name) <= 1:
            masked_name = name + "••••"
        else:
            masked_name = name[0] + "••••"
        return f"{masked_name}@{domain}"

    @classmethod
    def mask_extracted_fields(cls, fields: Dict[str, Any]) -> Dict[str, Any]:
        masked = dict(fields)
        for key, val in masked.items():
            if not isinstance(val, str):
                continue
            key_lower = key.lower()
            if "tracking" in key_lower:
                masked[key] = cls.mask_tracking_number(val)
            elif "card" in key_lower or "account" in key_lower:
                masked[key] = cls.mask_card_number(val)
            elif "phone" in key_lower:
                masked[key] = cls.mask_phone(val)
            elif "email" in key_lower:
                masked[key] = cls.mask_email(val)
        return masked
