# LabelLens — Telegram Shipping Label Bot

A production-ready Telegram bot that ingests shipping labels (UPS, FedEx, USPS), processes them with Tesseract OCR, matches against a configurable template engine, extracts structured fields, performs spatial bounding box scanning, and presents an interactive review and correction workflow via Telegram inline keyboards.

---

## Features

- **Document Recognition:** Automatically identifies UPS Ground / Ground Saver, FedEx Ground / Ground Return / Home Delivery / Express, USPS Ground Advantage, Store Receipts, Restaurant Receipts, and Invoices.
- **Image Preprocessing:** EXIF orientation correction, high-resolution rescaling, contrast enhancement (CLAHE), noise reduction, deskewing, and adaptive thresholding for optimal Tesseract OCR accuracy.
- **Configurable Template Engine:** Define new document templates via JSON without touching core Python code. Supports required/optional keywords, regex indicators, excluded keyword penalties, and custom scoring rules.
- **Spatial Bounding Box Scanning:** Extracts `(x, y, w, h)` pixel positions and normalized coordinates for every OCR token and matched field. Stores receipt dimensions per submission for future bounding-box-driven field editing.
- **Sensitive Data Protection:** Masking algorithms for tracking numbers, payment cards, phone numbers, and emails on user-facing summary screens.
- **Interactive Review Flow:** Clean HTML summary screens with single continuous status message updates (`Preparing image` → `Reading text` → `Matching template` → `Preparing result`). Inline actions: `Approve`, `Correct`, `Scan Again`, `Reject`, `View Details`, `Tracking Details`.
- **Manual Correction Flow:** Interactive field selection keyboard for manual user overrides with ✏️ indicators.
- **Submission State Machine:** Validated state machine (`uploaded` → `processing` → `matched` / `needs_review` → `approved` / `rejected` / `failed`) with full audit logging.
- **Admin Dashboard:** Access control, processing stats, active template overview, failed scan review, and CSV export.
- **Docker & PM2 Ready:** Complete containerization with Tesseract pre-installed, non-root user, and PM2 ecosystem config for Linux server deployment.

---

## Architecture

```text
LabelLens-Bot/
├── app/
│   ├── main.py                  # Bot entry point and handler registration
│   ├── config.py                # Pydantic BaseSettings config
│   ├── logging_config.py        # Structured logging initialization
│   ├── bot/
│   │   ├── handlers/            # start, uploads, callbacks, corrections, history, admin
│   │   ├── keyboards/           # Main menu, result, template, admin keyboards
│   │   ├── messages/            # HTML message renderers
│   │   └── middleware/          # Rate limiting and access control
│   ├── services/
│   │   ├── image_service.py     # OpenCV & Pillow preprocessing & deskew
│   │   ├── ocr_service.py       # Async Tesseract OCR wrapper (Linux-optimized)
│   │   ├── template_matcher.py  # Template scoring & classification
│   │   ├── extraction_service.py# Field extraction engine (regex, anchored, constant)
│   │   ├── spatial_scanner.py   # Bounding box (X, Y, W, H) & receipt dimensions
│   │   ├── validation_service.py# Tracking number, date, currency normalizer
│   │   ├── masking_service.py   # Sensitive field masking
│   │   └── submission_service.py# State machine & pipeline orchestrator
│   ├── templates/
│   │   ├── loader.py            # JSON/YAML template loader
│   │   ├── schemas.py           # Pydantic template schemas
│   │   └── documents/           # Template definitions (UPS, FedEx, USPS, receipts)
│   ├── database/
│   │   ├── models.py            # SQLAlchemy 2.x async models
│   │   ├── session.py           # Engine & async_sessionmaker setup
│   │   ├── repositories/        # UserRepository, SubmissionRepository, etc.
│   │   └── migrations/          # Async Alembic migration files
│   └── utils/
│       ├── telegram_formatting.py # HTML escaping helpers
│       ├── callback_data.py     # Compact byte-safe callback serializer
│       ├── file_validation.py   # File magic-bytes & MIME validation
│       └── identifiers.py       # Error reference ID generator
├── tests/                       # Pytest test suite (30 tests)
├── scripts/                     # Offline audit & utility scripts
│   ├── README.md
│   └── scan_all_samples_spatial.py
├── Samples/                     # Sample carrier label images for CI testing
│   ├── Fedx/                    # FedEx Ground, Ground Return, Home Delivery samples
│   ├── UPS/                     # UPS Ground / Ground Saver samples
│   ├── USPS/                    # USPS Ground Advantage samples
│   └── spatial_scans/           # Auto-generated spatial JSON coordinate data
├── docs/                        # Reports and documentation
├── Dockerfile                   # Production Docker image (Tesseract pre-installed)
├── docker-compose.yml           # Compose orchestration
├── ecosystem.config.js          # PM2 process manager configuration
├── pm2.sh                       # PM2 lifecycle management script
├── run.sh                       # Linux shell runner (auto-installs dependencies)
├── run.bat                      # Windows batch runner
└── alembic.ini                  # Migration configuration
```

---

## Requirements

- Python 3.12+
- Tesseract OCR (with English dataset `tesseract-ocr-eng`)
- OpenCV dependencies (`libgl1`, `libglib2.0-0`)

---

## Installation

### macOS (Local Development)

```bash
git clone git@github.com:itzr00tbyte/LabelLens-Bot.git
cd LabelLens-Bot

# Install Tesseract
brew install tesseract tesseract-lang

# Setup Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN and ADMIN_TELEGRAM_IDS

# Run bot
python3 -m app.main
```

### Linux (Server Deployment)

```bash
# Install system dependencies
sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libgl1 libglib2.0-0

# Clone and configure
git clone git@github.com:itzr00tbyte/LabelLens-Bot.git
cd LabelLens-Bot
cp .env.linux.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN

# Install Python dependencies globally
pip3 install -r requirements.txt --break-system-packages

# Run via PM2 (auto-restart, log management, startup persistence)
npm install -g pm2
./pm2.sh start
pm2 save
pm2 startup
```

### Docker

```bash
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN
docker compose up --build -d
docker compose logs -f telegram-receipt-bot
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Required | Telegram bot token from @BotFather |
| `ADMIN_TELEGRAM_IDS` | `[]` | Comma-separated list of Admin Telegram IDs |
| `DATABASE_URL` | `sqlite+aiosqlite:///./bot.db` | SQLAlchemy Async DB connection string |
| `TESSERACT_CMD` | Auto-detected | Custom path to tesseract binary if not on PATH |
| `MAX_UPLOAD_MB` | `10` | Maximum file upload size in Megabytes |
| `MIN_TEMPLATE_CONFIDENCE` | `0.50` | Minimum confidence score to match template |
| `LOW_CONFIDENCE_THRESHOLD` | `0.50` | Threshold above which template is auto-accepted |
| `STORE_OCR_TEXT` | `true` | Store extracted raw OCR text in database |
| `RATE_LIMIT_UPLOADS_PER_MINUTE` | `0` | Maximum upload requests per user per minute (0 = unlimited) |
| `OMP_NUM_THREADS` | `2` | OpenMP threads for Tesseract (Linux multi-core optimization) |

See [`.env.example`](.env.example) or [`.env.linux.example`](.env.linux.example) for a full reference.

---

## Adding a New Template

New document templates can be added by placing a `.json` file inside `app/templates/documents/`.

Example `custom_label.json`:
```json
{
  "id": "custom_label",
  "name": "Custom Express Label",
  "category": "shipping_label",
  "version": 1,
  "priority": 100,
  "enabled": true,
  "required_keywords": ["CUSTOM EXPRESS", "TRACKING"],
  "optional_keywords": ["SHIP TO", "WEIGHT"],
  "excluded_keywords": ["USPS", "FEDEX"],
  "regex_indicators": ["CX\\d{10}"],
  "minimum_score": 0.70,
  "fields": {
    "carrier": { "type": "constant", "value": "Custom Express" },
    "tracking_number": {
      "type": "regex",
      "patterns": ["CX\\d{10}"],
      "required": true,
      "normalize": "digits_only"
    }
  }
}
```

Templates are reloaded automatically on bot startup.

---

## Running Tests

```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

Expected: **30 / 30 tests pass**.

---

## Offline Scripts

### Spatial Bounding Box Scan (all samples)

```bash
PYTHONPATH=. python scripts/scan_all_samples_spatial.py
```

Scans all carrier label images in `Samples/`, generates `*.spatial.json` files with `(x, y, w, h)` positions and receipt dimensions.

---

## Security & Privacy

- **Magic Bytes Validation:** Uploaded files verified via header magic bytes to prevent file extension spoofing.
- **Sensitive Data Masking:** Tracking numbers and card details obfuscated on summary screens.
- **Path Traversal Protection:** Temporary files generated with cryptographically safe random tokens.
- **Callback Verification:** Callback queries check user ownership or admin rights before state transitions.
- **No Stack Traces Exposed:** Internal failures display reference IDs (`ERR-XXXXXX`) without internal tracebacks.

---

## Production Deployment Checklist

- [ ] Set `TELEGRAM_BOT_TOKEN` in `.env`
- [ ] Configure `ADMIN_TELEGRAM_IDS` with authorized admin accounts
- [ ] Run `pm2 save && pm2 startup` to enable auto-restart on reboot
- [ ] Use PostgreSQL (`postgresql+asyncpg://...`) for production workloads
- [ ] Set up automated backup for persistent database volume
