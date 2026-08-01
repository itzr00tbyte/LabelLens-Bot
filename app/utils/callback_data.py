from typing import NamedTuple, Optional, Union


class ParsedCallback(NamedTuple):
    action: str
    target_id: Optional[str] = None
    extra: Optional[str] = None


class CallbackDataHelper:
    ACTIONS = [
        "doc:app", "doc:corr", "doc:field", "doc:opt", "doc:down", "doc:down_img", "doc:down_pdf",
        "doc:rescan", "doc:rej", "doc:det", "doc:trk", "doc:rev", "doc:confirm", "doc:cancel_edit",
        "tpl:choose", "tpl:sel", "tpl:pg", "page:his", "menu:main", "menu:admin",
        "adm:tpl", "adm:subs", "adm:stats", "adm:failed", "adm:export", "adm:users",
        "upload", "help", "privacy"
    ]

    @staticmethod
    def encode(action: str, target_id: Optional[Union[str, int]] = None, extra: Optional[Union[str, int]] = None) -> str:
        parts = [action]
        if target_id is not None:
            parts.append(str(target_id))
        if extra is not None:
            parts.append(str(extra))
        data = ":".join(parts)
        if len(data.encode("utf-8")) > 64:
            raise ValueError(f"Callback data exceeds 64 bytes limit: {data}")
        return data

    @classmethod
    def decode(cls, data: str) -> ParsedCallback:
        if not data:
            return ParsedCallback(action="")
        
        # Match longest matching action prefix
        matched_action = None
        for action in sorted(cls.ACTIONS, key=len, reverse=True):
            if data == action or data.startswith(action + ":"):
                matched_action = action
                break

        if matched_action:
            remainder = data[len(matched_action):].lstrip(":")
            parts = remainder.split(":") if remainder else []
            target_id = parts[0] if len(parts) > 0 else None
            extra = parts[1] if len(parts) > 1 else None
            return ParsedCallback(action=matched_action, target_id=target_id, extra=extra)

        # Fallback for dynamic actions
        parts = data.split(":")
        return ParsedCallback(action=parts[0], target_id=parts[1] if len(parts) > 1 else None, extra=parts[2] if len(parts) > 2 else None)

