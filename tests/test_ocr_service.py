from unittest.mock import patch, MagicMock
import os
import sys
from app.services.ocr_service import _autodetect_tesseract


def test_autodetect_tesseract_with_valid_settings_cmd():
    with patch("app.services.ocr_service.settings") as mock_settings, \
         patch("os.path.exists", return_value=True):
        mock_settings.TESSERACT_CMD = "/custom/path/tesseract"
        assert _autodetect_tesseract() == "/custom/path/tesseract"


def test_autodetect_tesseract_ignores_invalid_settings_cmd():
    with patch("app.services.ocr_service.settings") as mock_settings, \
         patch("os.path.exists", return_value=False), \
         patch("shutil.which", return_value=None):
        mock_settings.TESSERACT_CMD = "/opt/homebrew/bin/tesseract"
        # Should return None instead of non-existent path
        assert _autodetect_tesseract() is None


def test_autodetect_tesseract_finds_in_path():
    with patch("app.services.ocr_service.settings") as mock_settings, \
         patch("shutil.which", side_effect=lambda cmd: "/usr/bin/tesseract" if "tesseract" in cmd else None), \
         patch("os.path.exists", return_value=True):
        mock_settings.TESSERACT_CMD = None
        assert _autodetect_tesseract() == "/usr/bin/tesseract"
