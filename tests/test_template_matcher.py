from app.services.template_matcher import TemplateMatcher


def test_usps_ground_advantage_matching(template_loader, sample_usps_ocr_text):
    matcher = TemplateMatcher(template_loader=template_loader)
    result = matcher.match(sample_usps_ocr_text, ocr_confidence=0.95)

    assert result.template is not None
    assert result.template.id == "usps_ground_advantage"
    assert result.score >= 0.72
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
    # Excluded keyword "FEDEX" in USPS template should result in 0 score for USPS template
    score, matched, missing = matcher.score_template(
        template_loader.get_template("usps_ground_advantage"),
        ocr_text.upper(),
        0.95
    )
    assert score == 0.0
