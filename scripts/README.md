# Scripts

Utility and maintenance scripts for LabelLens-Bot. These are **not** part of the production bot — they are offline tools for data analysis, auditing, and CI validation.

## Available Scripts

### `scan_all_samples_spatial.py`

Performs a full spatial bounding box scan on all sample images in `Samples/`.

Outputs per-image `.spatial.json` files to `Samples/spatial_scans/{category}/` containing:
- Receipt/document image dimensions (width, height, aspect ratio)
- Bounding box coordinates `(x, y, w, h)` for every OCR token
- Normalized coordinates `(norm_x, norm_y, norm_w, norm_h)` relative to image size
- Matched template name and confidence score
- Extracted field bounding boxes

**Usage:**

```bash
PYTHONPATH=. python scripts/scan_all_samples_spatial.py
```

**Output:**
```
Samples/
└── spatial_scans/
    ├── manifest.json           # Summary of all scanned images
    ├── Fedx/
    │   └── *.spatial.json
    ├── UPS/
    │   └── *.spatial.json
    └── USPS/
        └── *.spatial.json
```
