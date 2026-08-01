import pytest
from app.utils.callback_data import CallbackDataHelper


def test_callback_encoding_decoding():
    encoded = CallbackDataHelper.encode("doc:app", "sub_12345")
    assert encoded == "doc:app:sub_12345"

    parsed = CallbackDataHelper.decode(encoded)
    assert parsed.action == "doc:app"
    assert parsed.target_id == "sub_12345"
    assert parsed.extra is None


def test_callback_length_limit():
    long_id = "a" * 60
    with pytest.raises(ValueError, match="exceeds 64 bytes limit"):
        CallbackDataHelper.encode("doc:app", long_id)
