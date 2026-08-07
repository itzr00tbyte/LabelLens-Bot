import os
from typing import Any, Dict, Optional, Tuple
from PIL import Image, ImageOps

from app.templates.schemas import ImageRegionConfig


class ImageReplacementService:
    @staticmethod
    def process_replacement_image(
        replacement_img: Image.Image,
        region: ImageRegionConfig,
    ) -> Image.Image:
        """
        Resizes and fits a replacement logo or image into the target region box (x, y, w, h).
        Supports modes:
        - "fit": Resizes image to fit entirely inside bounding box preserving aspect ratio.
        - "fill": Resizes and crops image to fill the target bounding box completely.
        - "contain": Centers image inside target box with transparent padding.
        """
        target_w = max(1, region.width)
        target_h = max(1, region.height)
        mode = (region.mode or "contain").lower()

        # Convert image to RGBA to preserve transparency
        if replacement_img.mode != "RGBA":
            src = replacement_img.convert("RGBA")
        else:
            src = replacement_img.copy()

        src_w, src_h = src.size

        if mode == "fill":
            # Scale to cover then center crop
            scale = max(target_w / float(src_w), target_h / float(src_h))
            new_w, new_h = max(1, int(src_w * scale)), max(1, int(src_h * scale))
            resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)
            # Center crop
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            cropped = resized.crop((left, top, left + target_w, top + target_h))
            return cropped

        elif mode == "fit":
            # Scale to fit inside target box
            scale = min(target_w / float(src_w), target_h / float(src_h))
            new_w, new_h = max(1, int(src_w * scale)), max(1, int(src_h * scale))
            resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)
            return resized

        else:  # "contain"
            # Scale to fit inside target box and center within target canvas
            scale = min(target_w / float(src_w), target_h / float(src_h))
            new_w, new_h = max(1, int(src_w * scale)), max(1, int(src_h * scale))
            resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

            canvas = Image.new("RGBA", (target_w, target_h), (255, 255, 255, 0))
            offset_x = (target_w - new_w) // 2
            offset_y = (target_h - new_h) // 2
            canvas.paste(resized, (offset_x, offset_y), resized)
            return canvas

    @staticmethod
    def overlay_replacements_on_canvas(
        canvas: Image.Image,
        image_regions: Dict[str, ImageRegionConfig],
        replacements: Dict[str, Image.Image],
    ) -> Image.Image:
        """Overlays processed replacement images onto the document canvas at configured region coordinates."""
        output = canvas.copy().convert("RGBA")

        for region_id, region in image_regions.items():
            if region_id in replacements:
                repl_img = replacements[region_id]
                processed = ImageReplacementService.process_replacement_image(repl_img, region)
                output.paste(processed, (region.x, region.y), processed)

        return output.convert("RGB")
