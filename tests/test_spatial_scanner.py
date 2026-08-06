import pytest
from PIL import Image, ImageDraw
from app.services.spatial_scanner import SpatialScanner, SpatialScanResult


def test_spatial_scanner_dimensions():
    # Create test image (300x400)
    img = Image.new("RGB", (300, 400), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "TEST OCR SPATIAL TEXT", fill="black")

    res = SpatialScanner.scan_image(img, filename="test_img.png")

    assert isinstance(res, SpatialScanResult)
    assert res.dimensions.width == 300
    assert res.dimensions.height == 400
    assert res.dimensions.aspect_ratio == 0.75
    assert res.filename == "test_img.png"


def test_find_text_bbox():
    from app.services.spatial_scanner import TokenBBox

    tokens = [
        TokenBBox("TRACKING", 10, 50, 80, 20, 95.0, 0.1, 0.1, 0.2, 0.05),
        TokenBBox("1Z1234567890", 100, 50, 150, 20, 98.0, 0.3, 0.1, 0.4, 0.05)
    ]

    bbox = SpatialScanner._find_text_bbox("1Z1234567890", tokens)
    assert bbox is not None
    assert bbox["x"] == 100
    assert bbox["y"] == 50
    assert bbox["w"] == 150
    assert bbox["h"] == 20
