from app.utils.file_validation import FileValidator


def test_valid_jpeg_magic_bytes():
    jpeg_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01" + b"\x00" * 100
    valid, ext = FileValidator.validate_file_bytes(jpeg_bytes)
    assert valid is True
    assert ext == "jpg"


def test_valid_png_magic_bytes():
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    valid, ext = FileValidator.validate_file_bytes(png_bytes)
    assert valid is True
    assert ext == "png"


def test_invalid_file_signature():
    exe_bytes = b"MZ\x90\x00" + b"\x00" * 100
    valid, err = FileValidator.validate_file_bytes(exe_bytes)
    assert valid is False
    assert "Unsupported file format" in err


def test_file_size_exceeded():
    large_bytes = b"\xFF\xD8\xFF" + b"\x00" * (15 * 1024 * 1024)
    valid, err = FileValidator.validate_file_bytes(large_bytes)
    assert valid is False
    assert "exceeds maximum allowed size" in err
