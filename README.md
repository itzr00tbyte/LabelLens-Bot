# Telegram Receipt and Shipping Label Bot

A production-ready Telegram Bot built with Python 3.12+, `python-telegram-bot`, Tesseract OCR, OpenCV, SQLAlchemy 2.x async ORM, and Pydantic. The bot ingests receipts, invoices, and shipping labels (USPS, UPS, FedEx), preprocesses images, runs OCR, matches against JSON/YAML document templates, extracts useful data, masks sensitive fields, and presents a clean interactive review workflow via Telegram inline keyboards.

---

## Features

- **Document Recognition:** Automatically identifies Store Receipts, Restaurant Receipts, Invoices, USPS Ground Advantage, UPS Ground, FedEx Express, and Generic Shipping Labels.
- **Image Preprocessing:** EXIF orientation correction, high-resolution rescaling, contrast enhancement (CLAHE), noise reduction, deskewing, and adaptive thresholding for optimal Tesseract OCR accuracy.
- **Configurable Template Engine:** Define new document templates via JSON or YAML without touching core Python code. Supports required/optional keywords, regex indicators, excluded keyword penalties, and custom scoring rules.
- **Sensitive Data Protection:** Masking algorithms for tracking numbers, payment cards, phone numbers, and emails on user-facing summary screens.
- **Interactive Review Flow:** Clean HTML summary screens with single continuous status message updates (`Preparing image` → `Reading text` → `Matching template` → `Preparing result`). Inline actions include `Approve`, `Correct`, `Scan Again`, `Reject`, `View Details`, and `Tracking Details`.
- **Manual Correction Flow:** Interactive field selection keyboard for manual user overrides (`Total`, `Date`, `Tracking No.`, etc.), indicated by ✏️ pencil markers.
- **Submission State Machine:** Validated state machine (`uploaded`, `processing`, `matched`, `needs_review`, `approved`, `rejected`, `failed`, `deleted`) with full audit logging.
- **Admin Dashboard:** Access control, processing stats, active template overview, failed scan review, and CSV export for approved records.
- **Docker Ready:** Complete containerization setup with multi-stage Tesseract OCR installation, non-root user execution, and volume persistence.

---

## Architecture

```text
Reci-Edit-Bot/
├── app/
│   ├── main.py                  # Bot entry point and handler registration
│   ├── config.py                # Pydantic BaseSettings config
│   ├── logging_config.py        # Structured logging initialization
│   ├── bot/
│   │   ├── handlers/            # Start, Uploads, Callbacks, Corrections, History, Admin
│   │   ├── keyboards/           # Main menu, Result, Templates, Admin keyboards
│   │   ├── messages/            # HTML Message renderers
│   │   └── middleware/          # Rate limiting and access control
│   ├── services/
│   │   ├── image_service.py     # OpenCV & Pillow preprocessing & deskew
│   │   ├── ocr_service.py       # Async Tesseract OCR wrapper
│   │   ├── template_matcher.py  # Template scoring & classification
│   │   ├── extraction_service.py# Field extraction engine
│   │   ├── validation_service.py# Tracking number, date, currency normalizer
│   │   ├── masking_service.py   # Sensitive field masking
│   │   └── submission_service.py# State machine & pipeline orchestrator
│   ├── templates/
│   │   ├── loader.py            # JSON/YAML template loader
│   │   ├── schemas.py           # Pydantic template schemas
│   │   └── documents/           # Default template definitions
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
├── tests/                       # Pytest test suite
├── Dockerfile                   # Production Docker image definition
├── docker-compose.yml           # Compose orchestration
└── alembic.ini                  # Migration configuration
```

---

## Requirements

- Python 3.12+ (or Docker)
- Tesseract OCR (with English dataset `tesseract-ocr-eng`)
- OpenCV dependencies (`libgl1`, `libglib2.0-0`)

---

## BotFather Setup

1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow instructions to get your **Bot Token**.
3. (Optional) Set bot description and profile picture via BotFather.
4. Copy the generated API token into your `.env` file as `TELEGRAM_BOT_TOKEN`.

---

## Local Installation

1. **Clone repository and setup environment:**
   ```bash
   git clone <repo-url>
   cd Reci-Edit-Bot
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Install Tesseract OCR (macOS):**
   ```bash
   brew install tesseract tesseract-lang
   ```

3. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to set `TELEGRAM_BOT_TOKEN` and your Telegram User ID in `ADMIN_TELEGRAM_IDS`.

4. **Run Bot:**
   ```bash
   python -m app.main
   ```

---

## Docker Installation

To run using Docker Compose:

```bash
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN
docker compose up --build -d
```

Check container status and logs:
```bash
docker compose logs -f telegram-receipt-bot
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Required | Telegram bot token from @BotFather |
| `ADMIN_TELEGRAM_IDS` | `[]` | Comma-separated list of Admin Telegram IDs |
| `DATABASE_URL` | `sqlite+aiosqlite:///./bot.db` | SQLAlchemy Async DB connection string |
| `TESSERACT_CMD` | `""` | Custom path to tesseract binary if not on PATH |
| `MAX_UPLOAD_MB` | `10` | Maximum file upload size in Megabytes |
| `MIN_TEMPLATE_CONFIDENCE` | `0.72` | Minimum confidence score to match template |
| `LOW_CONFIDENCE_THRESHOLD` | `0.82` | Threshold above which template is auto-accepted |
| `STORE_OCR_TEXT` | `true` | Store extracted raw OCR text in database |
| `RATE_LIMIT_UPLOADS_PER_MINUTE` | `5` | Maximum upload requests per user per minute |

---

## Adding a New Template

New document templates can be added by placing a `.json` or `.yaml` file inside `app/templates/documents/`.

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
  "minimum_score": 0.72,
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

Templates are reloaded automatically on bot startup or via Admin dashboard.

---

## Running Tests

Run the test suite with coverage:

```bash
.venv/bin/pytest -v
```

---

## Security & Privacy

- **Magic Bytes Validation:** Uploaded files are verified using header magic bytes to prevent file extension spoofing.
- **Sensitive Data Masking:** Tracking numbers and card details are obfuscated on summary screens.
- **Path Traversal Protection:** Temporary files are generated with cryptographically safe random tokens and cleaned up after processing.
- **Callback Verification:** Callback queries check user ownership or administrator rights before performing any state transition.
- **No Stack Traces:** Internal failures display reference IDs (`ERR-XXXXXX`) without exposing internal tracebacks.

---

## Production Deployment Checklist

- [ ] Set a strong `TELEGRAM_BOT_TOKEN` in `.env`.
- [ ] Configure `ADMIN_TELEGRAM_IDS` with authorized admin accounts.
- [ ] Use PostgreSQL (`postgresql+asyncpg://...`) for production workloads.
- [ ] Run bot under non-root Docker container or systemd daemon.
- [ ] Set up automated backup for persistent database volume.
