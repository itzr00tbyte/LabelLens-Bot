from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image
import numpy as np
import pytesseract

from app.config import settings
from app.services.ocr_service import _autodetect_tesseract

# Configure Tesseract path
t_cmd = _autodetect_tesseract()
if t_cmd:
    pytesseract.pytesseract.tesseract_cmd = t_cmd


@dataclass
class TokenBBox:
    text: str
    x: int
    y: int
    w: int
    h: int
    conf: float
    norm_x: float  # Normalized 0.0 - 1.0
    norm_y: float  # Normalized 0.0 - 1.0
    norm_w: float
    norm_h: float


@dataclass
class ImageDimensions:
    width: int
    height: int
    aspect_ratio: float


@dataclass
class SpatialScanResult:
    filename: str
    dimensions: ImageDimensions
    total_tokens: int
    average_confidence: float
    tokens: List[TokenBBox]
    field_bboxes: Dict[str, Dict[str, Any]]
    scanned_at: str


class SpatialScanner:
    @staticmethod
    def scan_image(
        image_input: Any,
        filename: str = "document.png",
        extracted_fields: Optional[Dict[str, Any]] = None
    ) -> SpatialScanResult:
        """
        Performs high-precision spatial scan on an image, extracting image dimensions (receipt size),
        bounding box coordinates (x, y, w, h), normalized positions, and field bounding boxes.
        """
        if isinstance(image_input, (str, os.PathLike)):
            img = Image.open(image_input)
            filename = os.path.basename(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            img = Image.fromarray(image_input)

        img_w, img_h = img.size
        dimensions = ImageDimensions(
            width=img_w,
            height=img_h,
            aspect_ratio=round(img_w / float(img_h), 4) if img_h > 0 else 0.0
        )

        custom_config = r"--oem 3 --psm 6"
        data = pytesseract.image_to_data(
            img, config=custom_config, output_type=pytesseract.Output.DICT
        )

        tokens: List[TokenBBox] = []
        confidences: List[float] = []

        total_entries = len(data.get("text", []))
        for i in range(total_entries):
            txt = str(data["text"][i]).strip()
            conf_val = data["conf"][i]

            # Filter valid text entries
            if not txt:
                continue

            try:
                conf = float(conf_val)
            except (ValueError, TypeError):
                conf = 0.0

            if conf < 0:
                conf = 0.0

            x = int(data["left"][i])
            y = int(data["top"][i])
            w = int(data["width"][i])
            h = int(data["height"][i])

            norm_x = round(x / float(img_w), 4) if img_w > 0 else 0.0
            norm_y = round(y / float(img_h), 4) if img_h > 0 else 0.0
            norm_w = round(w / float(img_w), 4) if img_w > 0 else 0.0
            norm_h = round(h / float(img_h), 4) if img_h > 0 else 0.0

            token = TokenBBox(
                text=txt,
                x=x,
                y=y,
                w=w,
                h=h,
                conf=round(conf, 2),
                norm_x=norm_x,
                norm_y=norm_y,
                norm_w=norm_w,
                norm_h=norm_h
            )
            tokens.append(token)
            confidences.append(conf)

        avg_conf = (sum(confidences) / len(confidences)) if confidences else 0.0

        # Compute field bounding boxes if extracted fields are provided
        field_bboxes: Dict[str, Dict[str, Any]] = {}
        if extracted_fields:
            for field_name, value in extracted_fields.items():
                val_str = str(value).strip()
                if not val_str:
                    continue

                bbox = SpatialScanner._find_text_bbox(val_str, tokens)
                if bbox:
                    field_bboxes[field_name] = {
                        "value": val_str,
                        "bbox": bbox
                    }

        return SpatialScanResult(
            filename=filename,
            dimensions=dimensions,
            total_tokens=len(tokens),
            average_confidence=round(avg_conf, 2),
            tokens=tokens,
            field_bboxes=field_bboxes,
            scanned_at=datetime.now(timezone.utc).isoformat()
        )

    @staticmethod
    def _find_text_bbox(search_text: str, tokens: List[TokenBBox]) -> Optional[Dict[str, Any]]:
        """
        Locates the bounding box region for a target text string within tokens.
        """
        search_clean = search_text.upper().replace(" ", "")
        matching_tokens: List[TokenBBox] = []

        # Find tokens that form the search string
        for t in tokens:
            t_clean = t.text.upper().replace(" ", "")
            if t_clean in search_clean or search_clean in t_clean:
                matching_tokens.append(t)

        if not matching_tokens:
            return None

        min_x = min(t.x for t in matching_tokens)
        min_y = min(t.y for t in matching_tokens)
        max_x = max(t.x + t.w for t in matching_tokens)
        max_y = max(t.y + t.h for t in matching_tokens)

        return {
            "x": min_x,
            "y": min_y,
            "w": max_x - min_x,
            "h": max_y - min_y,
            "tokens_count": len(matching_tokens)
        }
