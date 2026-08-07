import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from PIL import Image

from app.config import settings
from app.templates.schemas import TemplateDefinition, FieldExtractionRule, ImageRegionConfig
from app.templates.loader import default_template_loader

logger = logging.getLogger(__name__)


def compute_phash(image: Image.Image) -> str:
    """Computes a 64-bit perceptual hash (pHash) for template image matching."""
    try:
        img = image.convert("L").resize((32, 32), Image.Resampling.LANCZOS)
        import numpy as np
        pixels = np.array(img, dtype=float)
        # Compute mean
        mean = pixels.mean()
        # Binary array
        bits = pixels > mean
        # Convert 1024 bits to 16 hex chars (64 bits sampling)
        sampled = bits[:8, :8].flatten()
        return "".join(["1" if b else "0" for b in sampled])
    except Exception:
        return "0" * 64


class TemplateRegistry:
    def __init__(self, samples_dir: Optional[str] = None):
        self.samples_dir = samples_dir or settings.SAMPLES_DIR
        self._samples_templates: Dict[str, TemplateDefinition] = {}
        self.auto_register_samples()

    def auto_register_samples(self) -> None:
        """
        Scans SAMPLES_DIR subdirectories and auto-registers reference image templates.
        Adding a new image to Samples/ automatically registers it without core code changes.
        """
        self._samples_templates.clear()
        if not os.path.exists(self.samples_dir):
            logger.warning(f"Samples directory '{self.samples_dir}' does not exist.")
            return

        for root, dirs, files in os.walk(self.samples_dir):
            if "spatial_scans" in root:
                continue
            for f in files:
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    img_path = os.path.join(root, f)
                    rel_dir = os.path.basename(root).lower()

                    try:
                        with Image.open(img_path) as img:
                            w, h = img.size

                        template_id = f"sample_{rel_dir}_{os.path.splitext(f)[0]}".replace(" ", "_").replace("(", "").replace(")", "").lower()
                        category = "shipping_label" if rel_dir in ["fedx", "ups", "usps"] else "store_receipt"
                        name = f"{rel_dir.upper()} Sample ({f})"

                        # Default rules based on carrier category
                        req_kw = [rel_dir.upper()] if rel_dir in ["fedx", "ups", "usps"] else []
                        is_official = rel_dir in ["fedx", "ups", "usps"]

                        tpl = TemplateDefinition(
                            id=template_id,
                            name=name,
                            category=category,
                            version=1,
                            priority=50,
                            enabled=True,
                            reference_image_path=img_path,
                            width=w,
                            height=h,
                            required_keywords=req_kw,
                            minimum_score=0.65,
                            is_official_carrier=is_official,
                            image_regions={
                                "logo": ImageRegionConfig(
                                    id="logo",
                                    label="Company Logo",
                                    x=35,
                                    y=25,
                                    width=200,
                                    height=100,
                                    mode="contain"
                                )
                            }
                        )
                        self._samples_templates[tpl.id] = tpl
                    except Exception as exc:
                        logger.error(f"Error registering sample image {img_path}: {exc}")

        logger.info(f"Auto-registered {len(self._samples_templates)} sample image templates from {self.samples_dir}")

    def get_all_templates(self) -> List[TemplateDefinition]:
        """Returns union of JSON template definitions and auto-registered Samples templates."""
        json_templates = default_template_loader.list_templates()
        combined = {t.id: t for t in json_templates}
        for sample_tpl in self._samples_templates.values():
            if sample_tpl.id not in combined:
                combined[sample_tpl.id] = sample_tpl
        return sorted(combined.values(), key=lambda t: t.priority, reverse=True)


template_registry = TemplateRegistry()
