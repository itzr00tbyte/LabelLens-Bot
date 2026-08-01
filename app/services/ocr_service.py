import asyncio
from dataclasses import dataclass
import logging
from typing import Optional

import numpy as np
from PIL import Image
import pytesseract

from app.config import settings

logger = logging.getLogger(__name__)

if settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


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
