from app.services.masking_service import SensitiveDataMasker


def test_tracking_number_masking():
    raw_tracking = "9748852981029384756100"
    masked = SensitiveDataMasker.mask_tracking_number(raw_tracking)
    assert masked.startswith("9748")
    assert masked.endswith("6100")
    assert "••••" in masked
    assert raw_tracking not in masked


def test_card_number_masking():
    assert SensitiveDataMasker.mask_card_number("4111222233334444") == "•••• 4444"


def test_email_masking():
    assert SensitiveDataMasker.mask_email("john.doe@example.com") == "j••••@example.com"


def test_phone_masking():
    assert SensitiveDataMasker.mask_phone("1234567890") == "••• ••• 7890"


def test_mask_extracted_fields_dict():
    fields = {
        "tracking_number": "9748852981029384756100",
        "total": "$45.00",
        "card_number": "4111222233334444"
    }
    masked = SensitiveDataMasker.mask_extracted_fields(fields)
    assert "••••" in masked["tracking_number"]
    assert masked["total"] == "$45.00"
    assert masked["card_number"] == "•••• 4444"
