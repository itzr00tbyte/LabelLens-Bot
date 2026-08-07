import io
import os
import secrets
import uuid
from typing import List, Tuple, Union
from PIL import Image

from app.config import settings
from app.utils.file_validation import FileValidator


class FileService:
    @staticmethod
    def ensure_storage_dirs() -> None:
        """Creates storage directories if missing."""
        base_dir = settings.STORAGE_DIR
        for sub in ["originals", "processed", "generated", "temp"]:
            os.makedirs(os.path.join(base_dir, sub), exist_ok=True)

    @classmethod
    def validate_and_save_upload(
        cls, file_bytes: bytes, filename: str = ""
    ) -> Tuple[bool, str, str, str]:
        """
        Validates file magic bytes & size limit.
        Saves original file to storage/originals/{doc_id}_{filename}.
        Returns (is_valid, document_id, file_path, mime_type_or_extension).
        """
        cls.ensure_storage_dirs()
        is_valid, ext = FileValidator.validate_file_bytes(file_bytes, filename)
        if not is_valid:
            return False, "", "", ext

        doc_id = str(uuid.uuid4())
        safe_name = os.path.basename(filename) or f"upload.{ext}"
        target_name = f"{doc_id}_{safe_name}"
        file_path = os.path.join(settings.STORAGE_DIR, "originals", target_name)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        return True, doc_id, file_path, ext

    @classmethod
    def load_images_from_file(cls, file_path: str, ext: str) -> List[Image.Image]:
        """
        Loads Pillow Images from uploaded file. Supports multi-page PDFs as well as image formats.
        Returns list of PIL Image objects (one per page for PDFs).
        """
        ext_lower = ext.lower().lstrip(".")
        if ext_lower == "pdf":
            return cls.convert_pdf_to_images(file_path)

        # Single image format
        img = Image.open(file_path)
        img.load()
        return [img]

    @classmethod
    def convert_pdf_to_images(cls, pdf_path: str, dpi: int = 300) -> List[Image.Image]:
        """Converts PDF pages into PIL Image objects using PyMuPDF (fitz) or pdf2image fallback."""
        images: List[Image.Image] = []

        # 1. Try PyMuPDF (fitz)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            scale = dpi / 72.0
            matrix = fitz.Matrix(scale, scale)
            for page in doc:
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            doc.close()
            if images:
                return images
        except Exception:
            pass

        # 2. Try pdf2image
        try:
            from pdf2image import convert_from_path
            converted = convert_from_path(pdf_path, dpi=dpi)
            if converted:
                return converted
        except Exception:
            pass

        # 3. Fallback: Pillow PDF opener
        try:
            with Image.open(pdf_path) as pdf_img:
                n_pages = getattr(pdf_img, "n_frames", 1)
                for page_idx in range(n_pages):
                    pdf_img.seek(page_idx)
                    page_copy = pdf_img.convert("RGB")
                    images.append(page_copy)
            if images:
                return images
        except Exception:
            pass

        raise ValueError(f"Could not convert PDF at {pdf_path} to image.")
