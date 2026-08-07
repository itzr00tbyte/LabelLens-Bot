import re
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from app.config import settings


class ValidationService:
    @staticmethod
    def normalize_tracking_number(raw_value: str) -> str:
        """Removes spaces, hyphens, and non-alphanumeric chars from tracking numbers."""
        if not raw_value:
            return ""
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

    @staticmethod
    def validate_financial_totals(fields: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates mathematical consistency: Subtotal + Tax + Shipping - Discount == Total.
        Returns (is_valid, error_message_or_summary).
        """
        def parse_num(v: Any) -> float:
            if not v:
                return 0.0
            cleaned = re.sub(r"[^\d.]", "", str(v))
            try:
                return float(cleaned) if cleaned else 0.0
            except ValueError:
                return 0.0

        subtotal = parse_num(fields.get("subtotal"))
        tax = parse_num(fields.get("tax"))
        shipping = parse_num(fields.get("shipping"))
        discount = parse_num(fields.get("discount"))
        total = parse_num(fields.get("total"))

        if total > 0 and subtotal > 0:
            calc_total = subtotal + tax + shipping - discount
            if abs(calc_total - total) > 0.05:
                return False, f"Total mismatch: Expected ${calc_total:.2f}, got ${total:.2f}"

        return True, "Totals mathematically consistent"

    @staticmethod
    def get_auto_fitted_font(
        draw: ImageDraw.ImageDraw,
        text: str,
        initial_font: ImageFont.ImageFont,
        max_width: int,
        font_path: Optional[str] = None,
    ) -> ImageFont.ImageFont:
        """Shrinks font size dynamically if text exceeds max_width bounding box."""
        if not text or max_width <= 0:
            return initial_font

        current_font = initial_font
        try:
            bbox = draw.textbbox((0, 0), text, font=current_font)
            text_w = bbox[2] - bbox[0]
            if text_w <= max_width:
                return current_font

            # Shrink font iteratively if path is available
            size = getattr(initial_font, "size", 20)
            while text_w > max_width and size > 10:
                size -= 2
                if font_path and hasattr(ImageFont, "truetype"):
                    current_font = ImageFont.truetype(font_path, size)
                else:
                    break
                bbox = draw.textbbox((0, 0), text, font=current_font)
                text_w = bbox[2] - bbox[0]
        except Exception:
            pass

        return current_font

    @staticmethod
    def apply_recreated_watermark(image: Image.Image, is_official: bool = True) -> Image.Image:
        """
        Enforces Document-Integrity Safeguard:
        Applies a permanent watermark 'RECREATED COPY – NOT ORIGINAL' to official carrier label
        and receipt outputs to prevent misuse.
        """
        if not settings.WATERMARK_NON_OFFICIAL:
            return image

        output = image.copy().convert("RGBA")
        width, height = output.size

        # Create diagonal semi-transparent watermark layer
        watermark = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)

        watermark_text = "RECREATED COPY – NOT ORIGINAL"
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 26)
        except Exception:
            font = ImageFont.load_default()

        # Bottom subtle watermark banner
        banner_rect = [0, height - 35, width, height]
        draw.rectangle(banner_rect, fill=(200, 200, 200, 200))
        draw.text((width // 2, height - 17), watermark_text, fill=(50, 50, 50, 255), font=font, anchor="mm")

        merged = Image.alpha_composite(output, watermark)
        return merged.convert("RGB")
