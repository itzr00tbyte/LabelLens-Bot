import io
import os
import pytest
from PIL import Image

from app.services.file_service import FileService
from app.services.image_replacement import ImageReplacementService
from app.services.validation_service import ValidationService
from app.templates.schemas import ImageRegionConfig


def test_file_service_save_and_load(tmp_path):
    # Test image bytes save
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    valid, doc_id, file_path, ext = FileService.validate_and_save_upload(raw_bytes, "test.png")
    assert valid is True
    assert doc_id is not None
    assert os.path.exists(file_path)

    loaded_images = FileService.load_images_from_file(file_path, ext)
    assert len(loaded_images) == 1
    assert loaded_images[0].size == (100, 100)


def test_image_replacement_modes():
    logo = Image.new("RGBA", (200, 100), color=(255, 0, 0, 255))
    region = ImageRegionConfig(
        id="logo",
        label="Test Logo",
        x=10,
        y=10,
        width=100,
        height=100,
        mode="contain"
    )

    # Contain mode
    processed_contain = ImageReplacementService.process_replacement_image(logo, region)
    assert processed_contain.size == (100, 100)

    # Fill mode
    region.mode = "fill"
    processed_fill = ImageReplacementService.process_replacement_image(logo, region)
    assert processed_fill.size == (100, 100)

    # Fit mode
    region.mode = "fit"
    processed_fit = ImageReplacementService.process_replacement_image(logo, region)
    assert processed_fit.size[0] <= 100 and processed_fit.size[1] <= 100


def test_validation_financial_totals():
    valid_fields = {
        "subtotal": "$100.00",
        "tax": "$10.00",
        "shipping": "$5.00",
        "discount": "$5.00",
        "total": "$110.00"
    }
    is_valid, msg = ValidationService.validate_financial_totals(valid_fields)
    assert is_valid is True

    invalid_fields = {
        "subtotal": "$100.00",
        "tax": "$10.00",
        "total": "$200.00"
    }
    is_valid, msg = ValidationService.validate_financial_totals(invalid_fields)
    assert is_valid is False
    assert "mismatch" in msg.lower()


def test_document_integrity_watermark():
    img = Image.new("RGB", (800, 1200), color=(255, 255, 255))
    watermarked = ValidationService.apply_recreated_watermark(img)
    assert watermarked.size == (800, 1200)
