import os
import secrets
import tempfile
from typing import Tuple, Union

from app.config import settings


class FileValidator:
    # Magic bytes signatures for supported images
    MAGIC_BYTES = {
        "jpg": [b"\xFF\xD8\xFF"],
        "png": [b"\x89PNG\r\n\x1a\n"],
        "webp": [b"RIFF"],
        "pdf": [b"%PDF"],
    }

    @classmethod
    def validate_file_bytes(cls, file_bytes: Union[bytes, bytearray], filename: str = "") -> Tuple[bool, str]:
        if not file_bytes:
            return False, "File is empty."

        if len(file_bytes) > settings.max_upload_bytes:
            return False, f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_MB} MB."

        # Check signature magic bytes
        matched_ext = None
        for ext, sigs in cls.MAGIC_BYTES.items():
            for sig in sigs:
                if file_bytes.startswith(sig):
                    matched_ext = ext
                    break
            if matched_ext:
                break

        if not matched_ext:
            return False, "Unsupported file format. Please upload a valid JPG, PNG, WEBP, or PDF image."

        return True, matched_ext

    @staticmethod
    def create_safe_temp_file(file_bytes: Union[bytes, bytearray], ext: str) -> str:
        temp_dir = tempfile.gettempdir()
        safe_name = f"doc_{secrets.token_hex(12)}.{ext}"
        filepath = os.path.join(temp_dir, safe_name)
        with open(filepath, "wb") as f:
            f.write(file_bytes)
        return filepath

    @staticmethod
    def cleanup_temp_file(filepath: str) -> None:
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass
