import asyncio
from dataclasses import dataclass
import logging
from typing import Optional

import numpy as np
from PIL import Image
import pytesseract

from app.config import settings

import os
import sys

logger = logging.getLogger(__name__)


def _autodetect_tesseract() -> Optional[str]:
    # 1. Use explicitly configured TESSERACT_CMD if valid
    if settings.TESSERACT_CMD and os.path.exists(settings.TESSERACT_CMD):
        return settings.TESSERACT_CMD

    # 2. Windows RDP standard paths
    if sys.platform == "win32":
        possible_win_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for p in possible_win_paths:
            if os.path.exists(p):
                logger.info(f"Auto-detected Windows Tesseract executable at: {p}")
                return p

    # 3. macOS / Linux standard paths
    possible_unix_paths = [
        "/opt/homebrew/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/usr/bin/tesseract",
    ]
    for p in possible_unix_paths:
        if os.path.exists(p):
            return p

    return settings.TESSERACT_CMD


tesseract_path = _autodetect_tesseract()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path


@dataclass
class OCRResult:
    text: str
    confidence: float
    raw_data: Optional[dict] = None


class OCRService:
    @staticmethod
    async def extract_text(
        image: Image.Image,
        preprocessed_img: Optional[np.ndarray] = None
    ) -> OCRResult:
        """
        Runs Tesseract OCR asynchronously on PIL image and preprocessed numpy image,
        combining outputs for highest coverage and accuracy.
        """
        loop = asyncio.get_running_loop()
        
        # Execute OCR in threadpool executor since pytesseract is blocking
        result_raw = await loop.run_in_executor(
            None, OCRService._run_tesseract, image
        )
        
        if preprocessed_img is not None:
            preproc_pil = Image.fromarray(preprocessed_img)
            result_preproc = await loop.run_in_executor(
                None, OCRService._run_tesseract, preproc_pil
            )
            # Pick result with higher text length / confidence
            if len(result_preproc.text.strip()) > len(result_raw.text.strip()):
                return result_preproc

        return result_raw

    @staticmethod
    def _run_tesseract(image: Image.Image) -> OCRResult:
        try:
            # Custom config for better character recognition
            custom_config = r"--oem 3 --psm 6"
            text = pytesseract.image_to_string(image, config=custom_config)
            
            data = pytesseract.image_to_data(
                image, config=custom_config, output_type=pytesseract.Output.DICT
            )
            
            confidences = [
                float(c) for c in data.get("conf", []) if isinstance(c, (int, float, str)) and str(c).replace(".", "", 1).isdigit() and float(c) >= 0
            ]
            
            avg_conf = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0
            
            return OCRResult(text=text or "", confidence=round(avg_conf, 2), raw_data=data)
        except Exception as e:
            logger.error(f"Error during Tesseract OCR execution: {e}")
            return OCRResult(text="", confidence=0.0)
