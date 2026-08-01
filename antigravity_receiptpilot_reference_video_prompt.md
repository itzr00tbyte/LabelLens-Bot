# Antigravity Prompt: Production-Ready Telegram Receipt and Shipping Label Bot

You are a senior Python engineer, Telegram bot architect, OCR specialist, database designer, and product UX designer.

Build a production-ready Telegram bot that accepts receipts, invoices, and shipping labels, identifies the correct document template, extracts important fields, and presents a clean review flow with optimized Telegram inline buttons.

Use any existing project files as the starting point. Inspect the current repository before changing code. Preserve working functionality, refactor weak or duplicated code, and write the complete implementation rather than only describing it.

---

## Main Objective

Create a Telegram bot where a user can:

1. Upload a receipt, invoice, or shipping label.
2. See one continuously updated processing message.
3. Let the bot preprocess the image and run OCR.
4. Match the document against configured templates.
5. Display the detected document type, confidence score, and important extracted fields.
6. Confirm, correct, rescan, reject, or inspect the result using optimized inline buttons.
7. Save only approved or intentionally retained submissions.
8. View previous submissions.
9. Allow administrators to review templates, failed scans, and low-confidence results.

The bot must feel clean, professional, fast, and easy to understand.

---

## Technology Stack

Use:

- Python 3.12 or newer
- Latest stable `python-telegram-bot`
- Fully asynchronous handlers and services
- Tesseract OCR
- Pillow and OpenCV for image preprocessing
- SQLAlchemy 2.x
- SQLite for development
- PostgreSQL-ready database configuration
- Pydantic settings and validation
- Alembic migrations
- Docker
- Docker Compose
- Pytest
- Structured logging
- Environment variables loaded from `.env`

Do not hardcode secrets, tokens, database credentials, administrator IDs, or deployment-specific values.

---

## Initial Supported Document Types

Support a configurable template system with these initial categories:

- Store receipt
- Restaurant receipt
- Invoice
- USPS shipping label
- UPS shipping label
- FedEx shipping label
- Generic shipping label
- Unknown document

New templates must be addable through JSON or YAML configuration without modifying the main bot logic.

Do not build template detection as a large `if/elif` chain.

---

## Telegram UX Principles

Use Telegram-compatible HTML formatting consistently.

Use short messages, one clear heading per screen, bold labels for important fields, and minimal explanatory text.

Use no more than two primary buttons per row.

Keep destructive actions separate from approval actions.

Always provide a path back to the main menu.

Prefer editing an existing message instead of sending multiple status messages.

Never show raw JSON, stack traces, or long OCR blocks to normal users.

Show a maximum of five important extracted fields on the summary screen. Put all other fields behind a `View Details` button.

Use consistent emoji labels.

Escape all user-controlled text before inserting it into Telegram HTML.

---

## Start Screen

When the user sends `/start`, show:

**Welcome to Receipt Scanner**

Upload a receipt, invoice, or shipping label as a photo or image file.

The bot will identify the document, extract useful information, and let you review the result before saving it.

Inline keyboard:

| Row | Buttons |
|---|---|
| 1 | `📤 Upload Document` |
| 2 | `📋 My Submissions` · `❓ Help` |
| 3 | `⚙️ Settings` |

The upload button should explain how to attach a photo or image file.

---

## Supported Uploads

Accept:

- Telegram photos
- JPG
- JPEG
- PNG
- WEBP
- PDF image pages when PDF support is implemented

Reject unsupported files with a clear message.

Validate both MIME type and actual file signature.

Limit upload size using configuration.

Never trust the original filename.

Store temporary files under generated names.

Prevent path traversal.

Delete temporary files after processing.

---

## Processing Flow

After upload, immediately send one status message:

**Processing your document...**

Update the same message through these stages:

- `🖼 Preparing image`
- `🔍 Reading text`
- `🧩 Matching template`
- `✅ Preparing result`

The processing pipeline must:

1. Download the highest-resolution Telegram image.
2. Correct orientation using EXIF.
3. Resize very large images safely.
4. Convert to grayscale.
5. Improve contrast.
6. Reduce noise.
7. Apply adaptive thresholding when useful.
8. Deskew when possible.
9. Run OCR.
10. Normalize OCR text.
11. Match against configured templates.
12. Calculate a confidence score.
13. Extract template-specific fields.
14. Validate extracted values.
15. Store the processing result.
16. Display the review screen.

Image preprocessing must be modular and testable.

---

## Template Matching Engine

Build a reusable template engine.

Each template should support:

- Template ID
- Display name
- Category
- Version
- Priority
- Enabled state
- Required keywords
- Optional keywords
- Excluded keywords
- Regex indicators
- Layout or anchor hints
- Minimum confidence
- Field extraction definitions
- Allowed actions

Template scoring should consider:

- Required keyword coverage
- Optional keyword coverage
- Excluded keyword penalties
- Regex matches
- Extracted field success
- OCR confidence
- Template priority
- Conflicting carrier names
- Missing required fields

Do not identify a document based on one keyword alone.

Return:

- Best matching template
- Confidence score
- Matched signals
- Missing required signals
- Alternative likely templates

---

## Example Template

Create an initial USPS Ground Advantage template similar to:

```json
{
  "id": "usps_ground_advantage",
  "name": "USPS Ground Advantage",
  "category": "shipping_label",
  "version": 1,
  "priority": 100,
  "enabled": true,
  "required_keywords": [
    "USPS",
    "GROUND ADVANTAGE",
    "TRACKING"
  ],
  "optional_keywords": [
    "SHIP TO",
    "POSTAGE",
    "PACKAGE PICKUP",
    "POST OFFICE"
  ],
  "excluded_keywords": [
    "FEDEX",
    "UPS"
  ],
  "minimum_score": 0.72,
  "fields": {
    "carrier": {
      "type": "constant",
      "value": "USPS"
    },
    "service": {
      "type": "constant",
      "value": "Ground Advantage"
    },
    "tracking_number": {
      "type": "regex",
      "patterns": [
        "\\b(?:\\d[ ]*){20,22}\\b"
      ],
      "required": true,
      "normalize": "digits_only"
    },
    "recipient_name": {
      "type": "anchored_text",
      "anchor": "SHIP TO"
    },
    "recipient_address": {
      "type": "anchored_block",
      "anchor": "SHIP TO"
    }
  },
  "actions": [
    "approve",
    "correct",
    "rescan",
    "reject",
    "details"
  ]
}
```

The bot must correctly recognize a USPS Ground Advantage label similar to the provided sample and normalize tracking numbers that contain spaces.

---

## Extracted Fields

For receipts, extract when available:

- Merchant name
- Store location
- Receipt number
- Transaction date
- Transaction time
- Subtotal
- Tax
- Discount
- Tip
- Total
- Currency
- Payment method
- Last four card digits
- Item count

For invoices, extract when available:

- Company name
- Invoice number
- Invoice date
- Due date
- Customer name
- Subtotal
- Tax
- Total
- Currency

For shipping labels, extract when available:

- Carrier
- Service type
- Tracking number
- Sender name
- Sender address
- Recipient name
- Recipient address
- City
- State
- ZIP code
- Package reference
- Route code

Use reusable validators for dates, currency, totals, tracking numbers, ZIP codes, and identifiers.

---

## Sensitive Data Masking

Mask sensitive values by default.

Examples:

- Tracking number: `9748 •••• •••• •••• 8529 81`
- Payment card: `•••• 1234`
- Phone number: `••• ••• 0198`
- Email: `a••••@example.com`

Do not log full tracking numbers, addresses, payment information, or raw OCR text unless explicitly enabled for development.

---

## Result Screen

Display a clear summary such as:

```html
✅ <b>Document Detected</b>

<b>Type:</b> USPS Ground Advantage
<b>Confidence:</b> 94%

<b>Extracted Information</b>
• Carrier: USPS
• Service: Ground Advantage
• Tracking: 9748 •••• •••• •••• 8529 81
• Recipient: Food Lion
• Destination: Clemmons, NC 27012

Please review the information before approving it.
```

Do not show raw OCR text on this screen.

Main result keyboard:

| Row | Buttons |
|---|---|
| 1 | `✅ Approve` · `✏️ Correct` |
| 2 | `🔄 Scan Again` · `❌ Reject` |
| 3 | `🔎 View Details` |
| 4 | `🏠 Main Menu` |

Shipping-label result keyboard:

| Row | Buttons |
|---|---|
| 1 | `✅ Approve` · `✏️ Correct` |
| 2 | `📦 Tracking Details` |
| 3 | `🔄 Scan Again` · `❌ Reject` |
| 4 | `🏠 Main Menu` |

Do not automatically open external tracking pages. Show a tracking-details screen first.

---

## Callback Data

Use compact callback data such as:

```text
doc:approve:123
doc:edit:123
doc:rescan:123
doc:reject:123
doc:details:123
doc:track:123
tpl:select:usps
page:history:2
```

Keep callback data below Telegram limits.

Never place JSON or OCR text in callback data.

Store state in the database or a short-lived cache.

Every callback must verify:

- The submission exists.
- The requesting user owns it or is an administrator.
- The current submission state allows the action.
- The callback has not already been completed.

Answer callback queries immediately.

Prevent duplicate approvals and repeated side effects.

---

## Manual Correction Flow

When the user taps `✏️ Correct`, show:

```html
✏️ <b>Select a field to correct</b>
```

Generate buttons from fields available for that document.

Example:

| Row | Buttons |
|---|---|
| 1 | `Merchant` · `Date` |
| 2 | `Total` · `Receipt No.` |
| 3 | `Tracking No.` |
| 4 | `⬅️ Back` |

After a field is selected:

1. Ask the user to send the corrected value.
2. Validate the value.
3. Explain validation errors clearly.
4. Save the corrected value.
5. Mark it as user-corrected.
6. Return to the review screen.

Display corrected fields with a pencil marker, for example:

```text
• Total: $42.18 ✏️
```

Support `/cancel` during correction mode.

Use Telegram conversation state safely and avoid global mutable state.

---

## Low-Confidence Flow

When confidence is below the normal threshold but above the minimum threshold, show:

```html
⚠️ <b>Possible Match</b>

I found a likely document type, but the confidence is lower than usual.

<b>Possible type:</b> USPS Ground Advantage
<b>Confidence:</b> 76%
```

Keyboard:

| Row | Buttons |
|---|---|
| 1 | `✅ Use This Match` |
| 2 | `🧩 Select Another` |
| 3 | `🔄 Rescan` · `❌ Cancel` |

---

## Unknown Document Flow

When no template reaches the minimum score, show:

```html
🧩 <b>Document Type Not Identified</b>

Choose the closest template manually or upload a clearer image.
```

Keyboard:

| Row | Buttons |
|---|---|
| 1 | `🧩 Choose Template` |
| 2 | `🔄 Try Again` · `📤 New Image` |
| 3 | `❌ Cancel` |

---

## Template Selection

Show likely templates first.

Do not display more than eight templates on one screen.

Use pagination when needed.

Example keyboard:

| Row | Buttons |
|---|---|
| 1 | `USPS Label` · `UPS Label` |
| 2 | `FedEx Label` · `Store Receipt` |
| 3 | `Invoice` · `Other` |
| 4 | `⬅️ Back` |

After manual selection, rerun field extraction with the selected template.

Record that the template was manually selected.

---

## Submission History

The `📋 My Submissions` screen should display:

- Submission date
- Document type
- Approval status
- Masked primary identifier
- Confidence score

Example:

```html
📋 <b>My Submissions</b>

<b>1. USPS Ground Advantage</b>
Tracking: 9748 •••• 8529
Status: Approved
Date: 01 Aug 2026

<b>2. Store Receipt</b>
Total: $24.50
Status: Needs Review
Date: 31 Jul 2026
```

Use pagination.

Keyboard:

| Row | Buttons |
|---|---|
| 1 | `⬅️ Previous` · `Next ➡️` |
| 2 | `🏠 Main Menu` |

Allow the user to open a submission details screen.

---

## Admin Features

Restrict administrator access through configured Telegram user IDs or database roles.

Admin menu:

| Row | Buttons |
|---|---|
| 1 | `🧩 Templates` · `📥 Submissions` |
| 2 | `📊 Statistics` · `⚠️ Failed Scans` |
| 3 | `👥 Users` · `⚙️ Settings` |
| 4 | `🏠 Main Menu` |

Admin capabilities:

- View templates
- Enable or disable templates
- Change template priority
- Review failed scans
- Review low-confidence matches
- Review user corrections
- View processing statistics
- Export approved records as CSV
- Delete submissions
- Block abusive users
- View sanitized error references

Keep template creation configuration-file based until the core bot is complete and fully tested.

Do not overbuild a visual template editor in the first version.

---

## Commands

Implement:

```text
/start       Open the main menu
/upload      Explain how to upload a document
/history     Show user submissions
/help        Show help
/settings    Show user settings
/privacy     Show privacy information
/cancel      Cancel the current operation
/admin       Open the admin menu
```

Only expose `/admin` functionality to authorized administrators.

Configure Telegram command menus during startup.

---

## Database Models

Create at least these models.

### User

- ID
- Telegram user ID
- Username
- Display name
- Role
- Is blocked
- Created at
- Last active at

### Submission

- ID
- User ID
- Original filename
- File hash
- Telegram file ID
- Document category
- Template ID
- Match confidence
- Status
- OCR text
- OCR confidence
- Extracted fields JSON
- Corrected fields JSON
- Approved at
- Rejected at
- Created at
- Updated at

### Template

- ID
- Template key
- Name
- Category
- Version
- Enabled
- Priority
- Configuration JSON
- Created at
- Updated at

### Audit Log

- ID
- User ID
- Submission ID
- Action
- Metadata JSON
- Created at

Use database migrations.

Use repository classes for database access.

Do not place SQL queries directly in handlers.

---

## Submission State Machine

Use these statuses:

```text
uploaded
processing
matched
needs_review
approved
rejected
failed
deleted
```

Validate transitions.

Examples:

- `uploaded → processing`
- `processing → matched`
- `processing → failed`
- `matched → approved`
- `matched → needs_review`
- `needs_review → approved`
- `needs_review → rejected`

Prevent invalid transitions such as:

- `deleted → processing`
- duplicate `approved → approved`
- `rejected → approved` without an explicit restore flow

Record important transitions in the audit log.

---

## Security and Privacy

Implement:

- Upload-size limits
- MIME validation
- File-signature validation
- Safe generated filenames
- Path-traversal protection
- Temporary-file deletion
- Configurable image retention
- File hashing for duplicate detection
- User rate limiting
- Per-user ownership checks
- Administrator authorization
- Sensitive-data masking
- Safe Telegram HTML escaping
- Generic user-facing errors
- Internal error reference IDs
- No stack traces in chat
- No secrets in logs
- No raw OCR in standard logs
- No arbitrary code execution from uploaded files
- Graceful handling of malformed images
- Protection against duplicate callbacks
- Optional allowlist mode
- Optional blocked-user list

Provide a clear `/privacy` screen explaining what is stored and for how long.

---

## Error Messages

Unsupported file:

```html
⚠️ <b>Unsupported File</b>

Please upload a JPG, PNG, WEBP, or supported PDF.
```

OCR failure:

```html
⚠️ <b>I Could Not Read This Document Clearly</b>

Try another photo with:

• Better lighting
• No shadows
• The full document visible
• The camera directly above the document
```

Buttons:

| Row | Buttons |
|---|---|
| 1 | `📤 Upload Again` |
| 2 | `🏠 Main Menu` |

No template match:

```html
🧩 <b>Document Type Not Identified</b>

Choose the closest template manually or upload a clearer image.
```

Internal error:

```html
❌ <b>Processing Failed</b>

The document was not approved or saved as complete.

Reference: ERR-XXXXXX
```

Never expose internal exception details.

---

## Recommended Project Structure

```text
app/
├── main.py
├── config.py
├── logging_config.py
├── bot/
│   ├── handlers/
│   │   ├── start.py
│   │   ├── uploads.py
│   │   ├── callbacks.py
│   │   ├── corrections.py
│   │   ├── history.py
│   │   └── admin.py
│   ├── keyboards/
│   │   ├── main_menu.py
│   │   ├── result.py
│   │   ├── templates.py
│   │   └── admin.py
│   ├── messages/
│   │   └── renderers.py
│   └── middleware/
│       ├── rate_limit.py
│       └── access_control.py
├── services/
│   ├── image_service.py
│   ├── ocr_service.py
│   ├── template_matcher.py
│   ├── extraction_service.py
│   ├── validation_service.py
│   ├── masking_service.py
│   └── submission_service.py
├── templates/
│   ├── loader.py
│   ├── schemas.py
│   └── documents/
│       ├── usps_ground_advantage.json
│       ├── generic_receipt.json
│       └── generic_invoice.json
├── database/
│   ├── models.py
│   ├── session.py
│   ├── repositories/
│   └── migrations/
├── utils/
│   ├── telegram_formatting.py
│   ├── callback_data.py
│   ├── file_validation.py
│   └── identifiers.py
└── tests/
    ├── test_template_matcher.py
    ├── test_extraction.py
    ├── test_masking.py
    ├── test_callbacks.py
    ├── test_state_machine.py
    └── fixtures/
```

Keep handlers small.

Place business logic in services.

Place database access in repositories.

Place message rendering and keyboard construction in reusable modules.

---

## Configuration

Create `.env.example`:

```env
TELEGRAM_BOT_TOKEN=
ADMIN_TELEGRAM_IDS=
DATABASE_URL=sqlite+aiosqlite:///./bot.db

TESSERACT_CMD=
MAX_UPLOAD_MB=10
MIN_TEMPLATE_CONFIDENCE=0.72
LOW_CONFIDENCE_THRESHOLD=0.82

STORE_ORIGINAL_IMAGES=false
STORE_OCR_TEXT=true
TEMP_FILE_RETENTION_MINUTES=15

RATE_LIMIT_UPLOADS_PER_MINUTE=5
LOG_LEVEL=INFO
ENVIRONMENT=development
```

Validate configuration during startup.

Stop with a clear error when required variables are missing.

---

## Docker Requirements

Provide:

- `Dockerfile`
- `docker-compose.yml`
- Tesseract installation
- Non-root application user
- Persistent database volume
- Optional persistent uploads volume
- Health check
- `.dockerignore`

The project should start with:

```bash
cp .env.example .env
docker compose up --build
```

---

## Code Quality Requirements

- Use type hints throughout.
- Use async functions correctly.
- Avoid global mutable state.
- Use enums for statuses and categories.
- Use Pydantic models for configuration and extracted data.
- Add docstrings to public services.
- Use dependency injection where practical.
- Avoid duplicated keyboard definitions.
- Avoid duplicated message formatting.
- Keep functions focused.
- Do not silently swallow exceptions.
- Add structured logs with request or submission IDs.
- Add graceful shutdown.
- Close database sessions correctly.
- Handle Telegram API errors safely.
- Keep core logic independent from Telegram handlers.
- Do not leave placeholders in core functionality.
- Run formatting and linting.

---

## Testing Requirements

Add automated tests for:

- Template loading
- Required keyword matching
- Optional keyword scoring
- Excluded keyword penalties
- Regex indicators
- Tracking-number normalization
- Receipt total extraction
- Date extraction
- Sensitive-field masking
- Callback parsing
- Submission ownership checks
- Valid and invalid state transitions
- Duplicate approval prevention
- Invalid image rejection
- Low-confidence handling
- Unknown-document handling
- Manual template selection
- Manual field correction
- Rate limiting

Use mocked Telegram updates for handler tests.

Include at least one USPS Ground Advantage OCR fixture.

Expected result:

```text
Category: shipping_label
Template: usps_ground_advantage
Carrier: USPS
Service: Ground Advantage
```

Verify that tracking numbers containing spaces are normalized to digits before validation.

---

## README Requirements

Create a professional README containing:

1. Project overview
2. Features
3. Architecture
4. Requirements
5. BotFather setup
6. Local installation
7. Docker installation
8. Environment variables
9. Adding a new template
10. Running tests
11. Security notes
12. Privacy and data retention
13. Troubleshooting
14. Production deployment checklist

Include exact commands.

---

## Implementation Order

### Phase 1 — Foundation

- Inspect the repository
- Create the project structure
- Add configuration
- Add structured logging
- Add database models
- Add migrations
- Add `/start`
- Add the main keyboard

### Phase 2 — Upload Processing

- Handle photos and image files
- Validate files
- Add temporary storage
- Add image preprocessing
- Add OCR
- Add progress-message editing

### Phase 3 — Template Engine

- Add template schema
- Add template loader
- Add template scoring
- Add USPS Ground Advantage template
- Add generic receipt template
- Add generic invoice template

### Phase 4 — Results and Buttons

- Add result rendering
- Add masking
- Add approve action
- Add correction flow
- Add rescan action
- Add reject action
- Add details screen
- Add secure callbacks

### Phase 5 — History and Admin

- Add submission history
- Add pagination
- Add admin dashboard
- Add failed-scan review
- Add low-confidence review
- Add statistics
- Add CSV export

### Phase 6 — Testing and Deployment

- Add unit tests
- Add integration tests
- Add Docker files
- Add README
- Run linting
- Run tests
- Fix every failure

Do not break completed phases while implementing later phases.

---

## Acceptance Criteria

The project is complete when:

- The bot starts without errors.
- `/start` displays a professional menu.
- Users can upload supported images.
- Uploaded files are validated.
- OCR is performed.
- USPS Ground Advantage labels are recognized.
- Generic receipts and invoices can be recognized.
- Extracted fields are displayed clearly.
- Confidence scores are shown.
- Sensitive values are masked.
- Buttons are clean and logically arranged.
- Users can approve, correct, reject, rescan, and inspect details.
- Users cannot modify another user's submission.
- Duplicate callback clicks do not create duplicate actions.
- Temporary files are deleted.
- Admin access is restricted.
- State transitions are validated.
- Tests pass.
- Docker deployment works.
- Setup documentation is complete.

---

## Final Output Requirements

After implementation, provide:

1. A concise summary of completed functionality.
2. The final project tree.
3. Architectural decisions.
4. Setup commands.
5. Test results.
6. Remaining limitations.
7. A list of files created or modified.

Do not only explain what should be built.

Write the actual production-quality code and project files.

Prioritize a reliable working core over unnecessary complexity.

---

## Reference Video Interaction Style — Mandatory

Use the uploaded reference video as a UX and interaction reference only. Do not copy its branding, name, proprietary text, logo, or visual identity.

The final ReceiptPilot bot should feel similar in these ways:

- A persistent, button-led interface
- Compact information cards
- Contextual inline keyboards under each screen
- Clear primary actions in prominent button rows
- Settings displayed as a grid of short buttons
- Submenus that replace or update the current message
- One-question-at-a-time data entry
- Easy navigation back to the previous screen
- Minimal command typing
- Immediate status feedback during processing
- Confirmation before completing an action
- A dashboard-like main menu
- Saved records and history accessible through buttons

The reference video must influence the interaction model, not the business purpose. ReceiptPilot scans and verifies user-provided documents. It must not create counterfeit receipts, postage, carrier labels, tracking records, or documents intended to misrepresent a real transaction.

### Persistent Main Navigation

Keep a compact reply keyboard or persistent menu available during normal use.

Recommended persistent keyboard:

| Row | Buttons |
|---|---|
| 1 | `📤 Scan Document` · `📋 History` |
| 2 | `🧩 Templates` · `⚙️ Settings` |
| 3 | `❓ Help` · `🏠 Home` |

Use a resizeable keyboard that does not cover too much of the chat.

The persistent keyboard is for top-level navigation. Use inline keyboards for actions related to a specific submission.

### Home Dashboard

The `/start` and `🏠 Home` actions should open a dashboard-style message.

Example:

```html
🧾 <b>ReceiptPilot</b>

Your document scanning assistant.

<b>Status</b>
• Access: Enabled
• Scans today: 2
• Saved submissions: 14
• Default mode: Automatic

Upload a receipt, invoice, or shipping label to begin.
```

Inline keyboard:

| Row | Buttons |
|---|---|
| 1 | `📤 Scan a Document` |
| 2 | `📋 Recent Scans` · `🧩 Templates` |
| 3 | `⚙️ Scan Settings` · `🔐 Privacy` |

Do not show irrelevant account fields such as credits or expiration unless the application actually supports those features.

### Upload Behavior

The upload process should resemble the reference video's fast feedback.

After a user uploads a document:

1. Send or edit one status message immediately.
2. Show `⏳ Processing your document…`.
3. Update the same message as each stage completes.
4. Avoid sending multiple noisy progress messages.
5. Replace the progress message with the result screen when finished.

Example status updates:

```html
⏳ <b>Processing your document…</b>

🖼 Preparing image
```

```html
⏳ <b>Processing your document…</b>

✅ Image prepared
🔍 Reading text
```

```html
⏳ <b>Processing your document…</b>

✅ Image prepared
✅ Text read
🧩 Matching template
```

### Result Configuration Screen

After detection, show a confirmation card followed by a dense but organized control panel similar to the reference.

Example:

```html
✅ <b>Please confirm the detected information</b>

<b>Document:</b> USPS Ground Advantage
<b>Confidence:</b> 94%

<b>Recipient</b>
Food Lion
1410 River Ridge Dr
Clemmons, NC 27012

<b>Tracking</b>
9748 •••• •••• •••• 8529 81

<b>Status:</b> Ready for review
```

Recommended inline keyboard:

| Row | Buttons |
|---|---|
| 1 | `✅ Approve` · `📄 Export PDF` |
| 2 | `🧩 Template: USPS` · `🎯 Confidence: 94%` |
| 3 | `✏️ Recipient` · `✏️ Tracking` |
| 4 | `✏️ Sender` · `✏️ Notes` |
| 5 | `🔎 Details` · `📝 OCR Text` |
| 6 | `🔄 Rescan` · `❌ Reject` |
| 7 | `🏠 Main Menu` |

Only display buttons that are supported for the current document.

Buttons such as confidence display may open an explanation screen rather than performing a destructive action.

### Dynamic Button Labels

Button labels should reflect the current value when useful.

Examples:

```text
🧩 Template: USPS
💵 Total: $42.18
📅 Date: 01 Aug 2026
🎯 Confidence: 94%
🔐 Masking: On
🖼 Image Storage: Off
```

Keep labels short enough to avoid wrapping excessively.

When a value changes, redraw the keyboard so the updated value is immediately visible.

### Contextual Submenus

Tapping a setting should open a focused submenu.

Example template submenu:

```html
🧩 <b>Select Document Template</b>

Current template: USPS Ground Advantage
```

| Row | Buttons |
|---|---|
| 1 | `USPS` · `UPS` |
| 2 | `FedEx` · `Store Receipt` |
| 3 | `Invoice` · `Generic Label` |
| 4 | `🤖 Automatic Detection` |
| 5 | `⬅️ Back to Review` |

Example export submenu:

```html
📤 <b>Export Submission</b>

Choose an export format.
```

| Row | Buttons |
|---|---|
| 1 | `📄 PDF` · `📊 CSV` |
| 2 | `🧾 JSON` · `🖼 Annotated Image` |
| 3 | `⬅️ Back` |

Only include export formats actually implemented.

### One-Question-at-a-Time Input

When a user chooses an editable field:

1. Show the current value.
2. Ask for one replacement value.
3. Validate the reply.
4. Save it.
5. Return to the review screen.
6. Update the button label.

Example:

```html
✏️ <b>Edit Tracking Number</b>

Current value:
<code>9748577400768408852981</code>

Send the corrected tracking number.

Use /cancel to keep the current value.
```

Do not ask users to fill several fields in one long message.

### Saved Records Screen

Provide a saved-submissions view similar to the reference video's saved-address list.

Example:

```html
📋 <b>Saved Submissions</b>

Select a submission to view or continue editing.
```

Display each saved item as its own inline button:

```text
USPS · 9748 •••• 8529 · Approved
Receipt · Food Lion · $42.18
Invoice · INV-1048 · Review
```

Use pagination after six to eight entries.

Navigation keyboard:

| Row | Buttons |
|---|---|
| 1 | `⬅️ Previous` · `Next ➡️` |
| 2 | `🔎 Search` · `↕️ Sort` |
| 3 | `🏠 Main Menu` |

### Sort Screen

Support a compact sort menu:

| Row | Buttons |
|---|---|
| 1 | `🕒 Newest` · `🕰 Oldest` |
| 2 | `🎯 Confidence` · `📄 Type` |
| 3 | `✅ Approved` · `⚠️ Needs Review` |
| 4 | `⬅️ Back` |

### Scan Settings Screen

Create a button-grid settings screen inspired by the reference.

Example:

```html
⚙️ <b>Scan Settings</b>

Change how new documents are processed.
```

| Row | Buttons |
|---|---|
| 1 | `🤖 Detection: Auto` · `🔐 Masking: On` |
| 2 | `🖼 Store Images: Off` · `📝 Store OCR: On` |
| 3 | `🎯 Min Score: 72%` · `🌐 Language: Auto` |
| 4 | `♻️ Reset Defaults` |
| 5 | `🏠 Main Menu` |

Settings must be real and connected to application behavior. Do not create decorative buttons that do nothing.

### Message Editing Rules

Use message editing heavily, as in the reference video.

Edit the existing bot message when:

- Moving between a result and its submenu
- Updating a setting
- Changing a field
- Paginating records
- Updating processing status
- Returning from a submenu

Send a new message when:

- A user uploads a new document
- A file is returned
- A critical error must remain visible
- Telegram no longer allows the old message to be edited

Always answer callback queries immediately.

### Navigation Rules

Every submenu must include a back button.

Use context-specific labels:

```text
⬅️ Back to Review
⬅️ Back to History
⬅️ Back to Settings
🏠 Main Menu
```

Do not make users restart the bot to escape a submenu.

### Confirmation Rules

Require confirmation before:

- Approving a low-confidence result
- Deleting a saved submission
- Clearing history
- Exporting unmasked sensitive data
- Changing retention settings
- Allowing original-image storage

Example confirmation keyboard:

| Row | Buttons |
|---|---|
| 1 | `✅ Yes, Continue` |
| 2 | `⬅️ Cancel` |

### Final Approval Screen

After approval, replace the review interface with a simple completion screen.

```html
✅ <b>Submission Approved</b>

<b>Type:</b> USPS Ground Advantage
<b>Tracking:</b> 9748 •••• 8529
<b>Saved:</b> 01 Aug 2026, 10:49 PM

The document is now available in your history.
```

Keyboard:

| Row | Buttons |
|---|---|
| 1 | `📄 Export` · `🔎 View Details` |
| 2 | `📤 Scan Another` |
| 3 | `📋 History` · `🏠 Main Menu` |

### Mobile Layout Requirements

The interface must be optimized for narrow Telegram mobile screens.

- Keep button labels concise.
- Use one or two buttons per row.
- Avoid long callback labels.
- Avoid more than seven inline keyboard rows on ordinary screens.
- Put secondary actions in submenus.
- Use `<code>` blocks only for short identifiers.
- Use compact field summaries.
- Avoid wide Markdown tables in actual Telegram messages.
- Test on Android and iOS-sized chat layouts.

### Implementation Requirement

Implement this reference-style interaction as reusable screen renderers and keyboard builders.

Create components such as:

```text
render_home_dashboard()
render_processing_status()
render_review_screen()
render_template_selector()
render_field_editor()
render_history_screen()
render_settings_screen()
render_approval_screen()

build_main_reply_keyboard()
build_review_keyboard()
build_template_keyboard()
build_history_keyboard()
build_settings_keyboard()
```

Do not hardcode keyboards separately inside every handler.

The result should feel like a polished button-driven Telegram application rather than a command-line tool inside chat.

