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


import shutil

# Prevent OpenMP thread contention on Linux multi-core servers
if "OMP_NUM_THREADS" not in os.environ:
    os.environ["OMP_NUM_THREADS"] = "2"


def _autodetect_tesseract() -> Optional[str]:
    # 1. Use explicitly configured TESSERACT_CMD if valid on disk
    if settings.TESSERACT_CMD:
        if os.path.exists(settings.TESSERACT_CMD):
            return settings.TESSERACT_CMD
        found_cmd = shutil.which(settings.TESSERACT_CMD)
        if found_cmd:
            return found_cmd

    # 2. Check system PATH for 'tesseract' or 'tesseract.exe'
    system_tesseract = shutil.which("tesseract") or shutil.which("tesseract.exe")
    if system_tesseract and os.path.exists(system_tesseract):
        logger.info(f"Auto-detected Tesseract executable in PATH at: {system_tesseract}")
        return system_tesseract

    # 3. Linux standard installation paths
    if sys.platform.startswith("linux"):
        possible_linux_paths = [
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/snap/bin/tesseract",
            "/usr/bin/tesseract-ocr",
        ]
        for p in possible_linux_paths:
            if os.path.exists(p):
                logger.info(f"Auto-detected Linux Tesseract executable at: {p}")
                return p

    # 4. Windows RDP standard paths
    if sys.platform == "win32":
        possible_win_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
            r"C:\ProgramData\chocolatey\bin\tesseract.exe",
        ]
        for p in possible_win_paths:
            if p and os.path.exists(p):
                logger.info(f"Auto-detected Windows Tesseract executable at: {p}")
                return p

    # 5. macOS standard paths
    possible_unix_paths = [
        "/opt/homebrew/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/usr/bin/tesseract",
    ]
    for p in possible_unix_paths:
        if os.path.exists(p):
            return p

    return None


tesseract_path = _autodetect_tesseract()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    logger.info(f"Configured Tesseract CMD: {tesseract_path}")
else:
    logger.warning(
        "Tesseract OCR binary not found in standard paths or PATH. "
        "Please install Tesseract OCR and set TESSERACT_CMD in .env if needed."
    )


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
        executing tasks in parallel for optimal throughput on multi-core Linux systems.
        """
        loop = asyncio.get_running_loop()
        
        if preprocessed_img is not None:
            preproc_pil = Image.fromarray(preprocessed_img)
            # Parallel execution on threadpool executor for ~50% speedup
            result_raw, result_preproc = await asyncio.gather(
                loop.run_in_executor(None, OCRService._run_tesseract, image),
                loop.run_in_executor(None, OCRService._run_tesseract, preproc_pil)
            )
            # Pick result with higher text length / coverage
            if len(result_preproc.text.strip()) > len(result_raw.text.strip()):
                return result_preproc
            return result_raw

        return await loop.run_in_executor(None, OCRService._run_tesseract, image)

    @staticmethod
    def _run_tesseract(image: Image.Image) -> OCRResult:
        try:
            # Custom config for better character recognition
            custom_config = r"--oem 3 --psm 6"
            raw_text = pytesseract.image_to_string(image, config=custom_config)
            text = raw_text if isinstance(raw_text, str) else str(raw_text)
            
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
