import asyncio
from dataclasses import asdict
import json
import os
from PIL import Image

from app.services.extraction_service import FieldExtractionService
from app.services.ocr_service import OCRService
from app.services.spatial_scanner import SpatialScanner
from app.services.template_matcher import TemplateMatcher
from app.templates.loader import default_template_loader


async def run_batch_spatial_scan():
    print("===================================================")
    print("      LabelLens Spatial Bounding Box Scanner       ")
    print("===================================================")

    default_template_loader.reload_templates()
    matcher = TemplateMatcher()
    extractor = FieldExtractionService()

    base_samples_dir = "Samples"
    output_dir = "Samples/spatial_scans"
    os.makedirs(output_dir, exist_ok=True)

    summary_manifest = []

    for category in sorted(os.listdir(base_samples_dir)):
        cat_path = os.path.join(base_samples_dir, category)
        if not os.path.isdir(cat_path) or category == "spatial_scans":
            continue

        cat_output_dir = os.path.join(output_dir, category)
        os.makedirs(cat_output_dir, exist_ok=True)

        files = sorted([f for f in os.listdir(cat_path) if f.endswith((".png", ".jpg", ".jpeg"))])
        print(f"\nScanning carrier category: {category} ({len(files)} files)...")

        for fname in files:
            file_path = os.path.join(cat_path, fname)
            img = Image.open(file_path)

            # 1. Extract OCR text
            ocr_res = await OCRService.extract_text(img)

            # 2. Template matching & field extraction
            match = matcher.match(ocr_res.text, ocr_res.confidence)
            extracted_fields = {}
            template_name = "UNMATCHED"

            if match.template:
                template_name = match.template.name
                extracted_fields = extractor.extract_fields(match.template, ocr_res.text)

            # 3. Spatial scan with bounding boxes & receipt dimensions
            spatial_res = SpatialScanner.scan_image(
                image_input=img,
                filename=fname,
                extracted_fields=extracted_fields
            )

            # Convert result to dict
            spatial_dict = asdict(spatial_res)
            spatial_dict["matched_template"] = template_name

            # Save JSON scan output
            out_filename = f"{os.path.splitext(fname)[0]}.spatial.json"
            out_filepath = os.path.join(cat_output_dir, out_filename)
            with open(out_filepath, "w", encoding="utf-8") as f:
                json.dump(spatial_dict, f, indent=2)

            summary_manifest.append({
                "category": category,
                "filename": fname,
                "template": template_name,
                "dimensions": spatial_dict["dimensions"],
                "total_tokens": spatial_dict["total_tokens"],
                "average_confidence": spatial_dict["average_confidence"],
                "scan_file": out_filepath
            })

            print(
                f"  [✓] {fname:28s} | Size: {img.size[0]}x{img.size[1]} | "
                f"Tokens: {spatial_res.total_tokens:3d} | JSON: {out_filename}"
            )

    # Save summary manifest
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(summary_manifest, f, indent=2)

    print("\n===================================================")
    print(f"Spatial scan complete! Scanned {len(summary_manifest)} images.")
    print(f"Results saved to: {output_dir}/")
    print("===================================================")


if __name__ == "__main__":
    asyncio.run(run_batch_spatial_scan())
