import pytest
from app.services.image_generator import ReceiptImageGenerator


def test_generate_usps_label_clone():
    fields = {
        "carrier": "USPS",
        "service": "Ground Advantage",
        "tracking_number": "9748577400768408852981",
        "recipient_name": "FOOD LION",
        "recipient_address": "1410 RIVER RIDGE DR\nCLEMMONS NC 27012-8355",
        "sender_address": "ALBERT OSBORN\n421 SUNNY MAGNOLIA ROW\nCOMMERCE CITY CO 80229",
    }
    img = ReceiptImageGenerator.generate_receipt_image("usps_ground_advantage", fields, is_shipping=True)
    assert img.size == (800, 1200)

    png_bytes = ReceiptImageGenerator.get_image_bytes(img, format="PNG")
    assert len(png_bytes) > 5000

    pdf_bytes = ReceiptImageGenerator.get_pdf_bytes(img)
    assert len(pdf_bytes) > 5000


def test_generate_ups_label_clone():
    fields = {
        "carrier": "UPS",
        "service": "UPS Ground",
        "tracking_number": "1ZAG59389010935288",
        "recipient_name": "JOHN SMITH",
        "recipient_address": "100 MAIN STREET\nCHICAGO IL 60601",
        "weight": "1.0 LBS",
        "reference_1": "INV-89201",
    }
    img = ReceiptImageGenerator.generate_receipt_image("ups_ground", fields, is_shipping=True)
    assert img.size == (800, 1200)

    png_bytes = ReceiptImageGenerator.get_image_bytes(img, format="PNG")
    assert len(png_bytes) > 5000


def test_generate_fedex_label_clone():
    fields = {
        "carrier": "FedEx",
        "service": "FedEx Ground",
        "tracking_number": "874835624920",
        "recipient_name": "ACME CORP",
        "recipient_address": "500 CORPORATE PKWY\nDALLAS TX 75201",
        "weight": "2.5 LBS",
    }
    img = ReceiptImageGenerator.generate_receipt_image("fedex_ground", fields, is_shipping=True)
    assert img.size == (800, 1200)

    png_bytes = ReceiptImageGenerator.get_image_bytes(img, format="PNG")
    assert len(png_bytes) > 5000


def test_generate_store_receipt():
    fields = {
        "merchant_name": "Target Stores",
        "total": "$45.20",
        "tax": "$3.20",
        "date": "08/06/2026",
    }
    img = ReceiptImageGenerator.generate_receipt_image("generic_receipt", fields, is_shipping=False)
    assert img.size == (800, 1200)

    png_bytes = ReceiptImageGenerator.get_image_bytes(img, format="PNG")
    assert len(png_bytes) > 5000
