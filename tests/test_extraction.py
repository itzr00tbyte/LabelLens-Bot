from app.services.extraction_service import FieldExtractionService
from app.services.validation_service import ValidationService


def test_usps_field_extraction(template_loader, sample_usps_ocr_text):
    tpl = template_loader.get_template("usps_ground_advantage")
    extracted = FieldExtractionService.extract_fields(tpl, sample_usps_ocr_text)

    assert extracted.get("carrier") == "USPS"
    assert extracted.get("service") == "Ground Advantage"
    # Verify tracking number is normalized to digits without spaces
    tracking_no = extracted.get("tracking_number")
    assert tracking_no is not None
    assert " " not in tracking_no
    assert tracking_no == "9748852981029384756100"


def test_validation_currency():
    assert ValidationService.normalize_currency("TOTAL $24.50") == "$24.50"
    assert ValidationService.normalize_currency("19.99") == "$19.99"
    assert ValidationService.normalize_currency("invalid") is None


def test_validation_tracking_number():
    assert ValidationService.normalize_tracking_number("9748 8529 81") == "9748852981"
    assert ValidationService.normalize_tracking_number(" 1Z-999-999 ") == "1Z999999"
