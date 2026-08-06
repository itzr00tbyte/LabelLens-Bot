from app.services.template_matcher import TemplateMatcher
from app.services.extraction_service import FieldExtractionService


def test_usps_ground_advantage_matching(template_loader, sample_usps_ocr_text):
    matcher = TemplateMatcher(template_loader=template_loader)
    result = matcher.match(sample_usps_ocr_text, ocr_confidence=0.95)

    assert result.template is not None
    assert result.template.id == "usps_ground_advantage"
    assert result.score >= 0.70
    assert "required:USPS" in result.matched_signals
    assert "required:GROUND ADVANTAGE" in result.matched_signals


def test_generic_receipt_matching(template_loader):
    ocr_text = """
    WELCOME TO STORE
    123 MAIN ST
    SUBTOTAL: $18.50
    TAX: $1.50
    TOTAL: $20.00
    THANK YOU FOR SHOPPING!
    """
    matcher = TemplateMatcher(template_loader=template_loader)
    result = matcher.match(ocr_text, ocr_confidence=0.90)

    assert result.template is not None
    assert result.template.id == "generic_receipt"
    assert result.score >= 0.60


def test_excluded_keyword_penalty(template_loader):
    ocr_text = """
    USPS GROUND ADVANTAGE
    TRACKING: 94001234567890
    FEDEX EXPRESS CARRIER
    """
    matcher = TemplateMatcher(template_loader=template_loader)
    score, matched, missing = matcher.score_template(
        template_loader.get_template("usps_ground_advantage"),
        ocr_text.upper(),
        0.95
    )
    assert score == 0.0


def test_fedex_ground_matching_and_extraction(template_loader):
    ocr_text = """
    FROM: (495) 448-8572
    GRACE HAYNES
    553 WILLOW ROW
    FALMOUTH ME 04106
    US
    TO BLACK MAGIC FIREARMS LLC
    233 CAVANAUGH DR
    COMMERCIAL POINT OH 43116
    (123) 456-7890 REF:
    INV:
    PO: DEPT:
    CAD: 22192929/WSXI3200
    FedEx Ground
    G
    TRK# 8748 3562 4920
    43116
    9632 0019 6 (000 000 0000) 3 00 8748 3562 4920
    """
    matcher = TemplateMatcher(template_loader=template_loader)
    result = matcher.match(ocr_text, ocr_confidence=0.95)

    assert result.template is not None
    assert result.template.id == "fedex_ground"
    assert result.score >= 0.70

    fields = FieldExtractionService.extract_fields(result.template, ocr_text)
    assert fields.get("carrier") == "FedEx"
    assert fields.get("service") == "FedEx Ground"
    assert fields.get("tracking_number") == "874835624920"


def test_fedex_home_delivery_matching_and_extraction(template_loader):
    ocr_text = """
    FROM: (418) 207-3434
    MANUEL ALVAREZ
    188 ROLLING OAK AVENUE
    ALEXANDRIA VA 22303
    US
    TO BLACK MAGIC FIREARMS LLC
    233 CAVANAUGH DR
    COMMERCIAL POINT OH 43116
    (123) 456-7890 REF:
    INV:
    PO: DEPT:
    CAD: 254315616/WSXI3200
    FedEx Home Delivery
    H
    TRK# 8748 3562 4920
    43116
    9632 0019 6 (000 000 0000) 3 00 8748 3562 4920
    """
    matcher = TemplateMatcher(template_loader=template_loader)
    result = matcher.match(ocr_text, ocr_confidence=0.95)

    assert result.template is not None
    assert result.template.id == "fedex_home_delivery"
    assert result.score >= 0.70

    fields = FieldExtractionService.extract_fields(result.template, ocr_text)
    assert fields.get("carrier") == "FedEx"
    assert fields.get("service") == "FedEx Home Delivery"
    assert fields.get("tracking_number") == "874835624920"


def test_fedex_ground_return_matching_and_extraction(template_loader):
    ocr_text = """
    FROM: (995) 974-4788
    SYLVIA SALAZAR
    387 WINDING CHESTNUT ROW
    SHORELINE WA 98117
    US
    TO BLACK MAGIC FIREARMS LLC
    233 CAVANAUGH DR
    COMMERCIAL POINT OH 43116
    (123) 456-7890 REF:
    INV:
    PO: DEPT:
    CAD: 279333518/WSXI3200
    RMA: 998877
    FedEx Ground
    G
    TRK# 8748 3562 4920
    RETURN
    43116
    9632 0019 6 (000 000 0000) 3 00 8748 3562 4920
    """
    matcher = TemplateMatcher(template_loader=template_loader)
    result = matcher.match(ocr_text, ocr_confidence=0.95)

    assert result.template is not None
    assert result.template.id == "fedex_ground_return"
    assert result.score >= 0.70

    fields = FieldExtractionService.extract_fields(result.template, ocr_text)
    assert fields.get("carrier") == "FedEx"
    assert fields.get("service") == "FedEx Ground Return"
    assert fields.get("tracking_number") == "874835624920"
    assert fields.get("rma_number") == "998877"


def test_ups_ground_matching_and_extraction(template_loader):
    ocr_text = """
    MALLORY MATTHEWS 1 LBS 1 OF 1
    97 QUIET MEADOW LANE
    WEST VALLEY CITY UT 84120
    SHIP TO:
    9139050316
    TARGET
    10900 STADIUM PKWY
    KANSAS CITY KS 66111
    KS 662 9-25
    UPS GROUND
    TRACKING #: 1Z AG5 938 90 1093 5288
    BILLING: P/P
    Reference No.1: 31600330192
    Reference No.2: 08598248511459
    """
    matcher = TemplateMatcher(template_loader=template_loader)
    result = matcher.match(ocr_text, ocr_confidence=0.95)

    assert result.template is not None
    assert result.template.id == "ups_ground"
    assert result.score >= 0.70

    fields = FieldExtractionService.extract_fields(result.template, ocr_text)
    assert fields.get("carrier") == "UPS"
    assert fields.get("service") == "UPS Ground"
    assert fields.get("tracking_number") == "1ZAG59389010935288"
    assert fields.get("reference_1") == "31600330192"
    assert fields.get("reference_2") == "08598248511459"
