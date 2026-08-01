import io
import math
import random
from typing import Any, Dict
from PIL import Image, ImageDraw, ImageFont


class ReceiptImageGenerator:
    @staticmethod
    def generate_receipt_image(
        document_type: str,
        fields: Dict[str, Any],
        is_shipping: bool = False,
    ) -> Image.Image:
        """
        Generates a clean, realistic, high-resolution receipt or shipping label image
        with all extracted and edited fields clearly rendered.
        """
        width = 600
        height = 850 if is_shipping else 800

        # Background canvas (cream/white thermal paper look)
        bg_color = (252, 252, 250) if not is_shipping else (255, 255, 255)
        image = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(image)

        # Basic font loading (fallback to default if custom ttf not present)
        try:
            font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
            font_header = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
            font_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
            font_body = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
            font_mono = ImageFont.truetype("/System/Library/Fonts/Courier.ttc", 15)
        except Exception:
            font_title = ImageFont.load_default()
            font_header = ImageFont.load_default()
            font_bold = ImageFont.load_default()
            font_body = ImageFont.load_default()
            font_mono = ImageFont.load_default()

        if is_shipping or "shipping" in document_type.lower() or "usps" in document_type.lower() or "ups" in document_type.lower() or "fedex" in document_type.lower():
            ReceiptImageGenerator._draw_shipping_label(draw, width, height, fields, document_type, font_title, font_header, font_bold, font_body, font_mono)
        else:
            ReceiptImageGenerator._draw_store_receipt(draw, width, height, fields, document_type, font_title, font_header, font_bold, font_body, font_mono)

        return image

    @staticmethod
    def _draw_store_receipt(draw: ImageDraw.ImageDraw, width: int, height: int, fields: Dict[str, Any], doc_type: str, font_title: Any, font_header: Any, font_bold: Any, font_body: Any, font_mono: Any) -> None:
        # Receipt outer border & shadow line
        draw.rectangle([20, 20, width - 20, height - 20], outline=(200, 200, 200), width=2)

        y = 45
        # Header - Merchant Name
        merchant = str(fields.get("merchant_name") or fields.get("company_name") or "STORE RECEIPT").upper()
        draw.text((width // 2, y), merchant, fill=(20, 20, 20), font=font_title, anchor="mm")
        y += 35

        # Address / Subheader
        address = str(fields.get("address") or fields.get("location") or "123 Main Street, Beverly Hills, CA 90210")
        draw.text((width // 2, y), address, fill=(80, 80, 80), font=font_body, anchor="mm")
        y += 30

        # Date & Time
        date_str = str(fields.get("transaction_date") or fields.get("date") or "01/08/2026")
        draw.text((width // 2, y), f"DATE: {date_str}", fill=(100, 100, 100), font=font_body, anchor="mm")
        y += 35

        # Divider line
        draw.line([40, y, width - 40, y], fill=(160, 160, 160), width=2)
        y += 25

        # Items section
        draw.text((50, y), "ITEM DESCRIPTION", fill=(30, 30, 30), font=font_bold)
        draw.text((width - 50, y), "AMOUNT", fill=(30, 30, 30), font=font_bold, anchor="ra")
        y += 30

        # Draw dummy line items or custom fields
        default_items = [
            ("Item Purchase A", "$12.50"),
            ("Service Fee", "$3.00"),
            ("Standard Item B", "$3.00"),
        ]
        for item_name, price in default_items:
            draw.text((50, y), item_name, fill=(50, 50, 50), font=font_body)
            draw.text((width - 50, y), price, fill=(50, 50, 50), font=font_body, anchor="ra")
            y += 28

        # Divider line
        y += 10
        draw.line([40, y, width - 40, y], fill=(160, 160, 160), width=1)
        y += 25

        # Subtotal, Tax, Total
        subtotal = str(fields.get("subtotal") or "$18.50")
        tax = str(fields.get("tax") or "$1.50")
        total = str(fields.get("total") or "$20.00")

        draw.text((50, y), "SUBTOTAL", fill=(60, 60, 60), font=font_body)
        draw.text((width - 50, y), subtotal, fill=(60, 60, 60), font=font_body, anchor="ra")
        y += 28

        draw.text((50, y), "TAX", fill=(60, 60, 60), font=font_body)
        draw.text((width - 50, y), tax, fill=(60, 60, 60), font=font_body, anchor="ra")
        y += 35

        # Double line before Total
        draw.line([40, y, width - 40, y], fill=(30, 30, 30), width=2)
        y += 15

        draw.text((50, y), "TOTAL DUE", fill=(10, 10, 10), font=font_header)
        draw.text((width - 50, y), total, fill=(10, 10, 10), font=font_header, anchor="ra")
        y += 45

        # Divider
        draw.line([40, y, width - 40, y], fill=(160, 160, 160), width=1)
        y += 25

        # Other fields (if any)
        for k, v in fields.items():
            if k not in ["merchant_name", "company_name", "address", "location", "transaction_date", "date", "subtotal", "tax", "total"]:
                label = k.replace("_", " ").title()
                draw.text((50, y), f"{label}:", fill=(80, 80, 80), font=font_body)
                draw.text((width - 50, y), str(v), fill=(20, 20, 20), font=font_bold, anchor="ra")
                y += 28

        y += 20
        # Receipt Footer
        draw.text((width // 2, y), "THANK YOU FOR YOUR BUSINESS!", fill=(80, 80, 80), font=font_bold, anchor="mm")

    @staticmethod
    def _draw_shipping_label(draw: ImageDraw.ImageDraw, width: int, height: int, fields: Dict[str, Any], doc_type: str, font_title: Any, font_header: Any, font_bold: Any, font_body: Any, font_mono: Any) -> None:
        # Shipping Label Box Border
        draw.rectangle([15, 15, width - 15, height - 15], outline=(0, 0, 0), width=4)

        # Huge Carrier / Service Header Block
        carrier = str(fields.get("carrier") or "USPS").upper()
        service = str(fields.get("service") or "GROUND ADVANTAGE").upper()

        draw.rectangle([15, 15, 120, 120], fill=(0, 0, 0))
        draw.text((67, 67), carrier[0] if carrier else "P", fill=(255, 255, 255), font=font_title, anchor="mm")

        draw.text((140, 45), carrier, fill=(0, 0, 0), font=font_header)
        draw.text((140, 75), service, fill=(0, 0, 0), font=font_title)

        draw.line([15, 120, width - 15, 120], fill=(0, 0, 0), width=3)

        # SHIP FROM / SHIP TO Blocks
        y = 135
        sender_addr = str(fields.get("sender_address") or fields.get("ship_from") or "Albert Gibson, 421 Sunny Magnolia, Commerce City CO 80022")
        draw.text((30, y), "SHIP FROM:", fill=(100, 100, 100), font=font_bold)
        draw.text((130, y), sender_addr, fill=(0, 0, 0), font=font_body)

        y += 65
        draw.line([15, y, width - 15, y], fill=(0, 0, 0), width=2)
        y += 15

        recipient_addr = str(fields.get("recipient_address") or fields.get("address") or fields.get("ship_to") or "FOOD LION, 1410 RIVER RIDGE DR, CLEMMONS NC 27012")
        draw.text((30, y), "SHIP TO:", fill=(0, 0, 0), font=font_title)
        y += 35
        
        # Word wrap address
        words = recipient_addr.split()
        line1 = " ".join(words[:4])
        line2 = " ".join(words[4:])
        draw.text((30, y), line1.upper(), fill=(0, 0, 0), font=font_header)
        if line2:
            y += 30
            draw.text((30, y), line2.upper(), fill=(0, 0, 0), font=font_header)

        y += 50
        draw.line([15, y, width - 15, y], fill=(0, 0, 0), width=3)

        # Tracking Section
        y += 20
        trk_num = str(fields.get("tracking_number") or "9748 5774 0076 8408 8529 81")
        draw.text((width // 2, y), f"{carrier} TRACKING #", fill=(0, 0, 0), font=font_bold, anchor="mm")

        # Draw Barcode representation
        y += 30
        barcode_x = 40
        barcode_width = width - 80
        barcode_y = y
        barcode_h = 100

        # Draw vertical barcode stripes
        random.seed(hash(trk_num))
        curr_x = barcode_x
        while curr_x < barcode_x + barcode_width:
            w = random.choice([2, 3, 4, 6])
            gap = random.choice([2, 3, 4])
            draw.rectangle([curr_x, barcode_y, curr_x + w, barcode_y + barcode_h], fill=(0, 0, 0))
            curr_x += w + gap

        y += barcode_h + 20
        draw.text((width // 2, y), trk_num, fill=(0, 0, 0), font=font_header, anchor="mm")

    @staticmethod
    def get_image_bytes(image: Image.Image, format: str = "PNG") -> bytes:
        buf = io.BytesIO()
        image.save(buf, format=format)
        return buf.getvalue()

    @staticmethod
    def get_pdf_bytes(image: Image.Image) -> bytes:
        buf = io.BytesIO()
        # Convert RGB image to PDF
        image.convert("RGB").save(buf, format="PDF")
        return buf.getvalue()
