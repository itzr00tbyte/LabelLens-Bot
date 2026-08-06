# ReceiptPilot Reference Video — Frame-by-Frame UX Report

## Review Scope

The uploaded reference video was analyzed from start to finish.

- **Duration:** 35.37 seconds
- **Frame rate:** 30 FPS
- **Total frames processed:** 1,061
- **Resolution:** 816 × 848
- **Review method:** Every frame was processed for visual changes, and each distinct interface state and transition was reviewed.

The goal is to reproduce the **interaction quality, screen flow, message structure, dynamic controls, and button-driven experience** for ReceiptPilot.

The reference bot’s branding, wording, carrier claims, and proprietary visual identity should not be copied.

For ReceiptPilot, the same interaction model should be used for legitimate document scanning, verification, correction, approval, history, and export.

---

# 1. Complete Timeline

## 00:00–00:01 — Start Screen

The user opens the bot and sends:

```text
/start
```

The bot responds with:

- A wide animated GIF/banner
- Friendly greeting
- Bot purpose
- Access/account status
- Credit/status information
- A short Quick Start instruction
- A clear call to upload or forward a document

Visible persistent bottom menu:

| Row | Buttons |
|---|---|
| 1 | `ℹ️ Quick Start` · `💪 Bulk Editing` |
| 2 | `📍 Manage Addresses` · `⚙️ Settings` |
| 3 | `🧾 Receipts` |

### ReceiptPilot equivalent

Use:

| Row | Buttons |
|---|---|
| 1 | `📤 Scan Document` · `📚 Bulk Scan` |
| 2 | `📍 Saved Details` · `⚙️ Settings` |
| 3 | `🧾 Submissions` |

Recommended start text:

```html
👋 <b>Welcome to ReceiptPilot</b>

Scan receipts, invoices, and shipping labels.

<b>Access:</b> Enabled
<b>Scans today:</b> 0

Send or forward an image to begin.
```

The large welcome banner should match ReceiptPilot branding and use the generated navy receipt-scanner display picture style.

---

## 00:01–00:05 — Forwarding an Existing Image

The user opens Saved Messages, long-presses or right-clicks an image, selects **Forward**, and forwards it to the bot.

Important distinction:

- The long-press menu
- Saved Messages screen
- Forward selector
- Blue outgoing message bubble
- Telegram dark theme
- Input bar

These are controlled by the Telegram client, not by the bot.

The bot only needs to accept:

- Newly uploaded photos
- Image files
- Forwarded images
- Forwarded image albums where supported
- Captions
- Multiple images for bulk processing

ReceiptPilot should process forwarded media exactly like directly uploaded media.

---

## 00:05–00:07 — Immediate Processing Feedback

After the image reaches the bot, it sends:

```text
Processing your image... Please wait.
```

The response appears quickly and the persistent menu remains available.

### ReceiptPilot required behavior

Immediately create one status message:

```html
⏳ <b>Processing your document…</b>

🖼 Preparing image
```

Then edit the same message:

```html
⏳ <b>Processing your document…</b>

✅ Image prepared
🔍 Reading text
```

Then:

```html
⏳ <b>Processing your document…</b>

✅ Image prepared
✅ Text extracted
🧩 Matching template
```

Then replace it with the result or confirmation screen.

Do not send a separate message for every processing stage.

---

## 00:07–00:12 — Parsed Data and Input Instructions

The reference bot displays a large instructional response explaining accepted address formats.

It supports:

### Format 1 — Multi-line

```text
RECEIVER NAME   | REQUIRED
ADDRESS LINE 1  | REQUIRED
ADDRESS LINE 2  | OPTIONAL
CITY            | REQUIRED
STATE/PROVINCE  | REQUIRED
POSTAL CODE     | REQUIRED
PHONE           | OPTIONAL
COMPANY         | OPTIONAL
```

### Format 2 — One-line

```text
RECEIVER NAME | REQUIRED
FULL ADDRESS  | REQUIRED
PHONE         | OPTIONAL
COMPANY       | OPTIONAL
```

It also shows:

- Example data
- Warnings
- Suggested alternatives based on ZIP code
- Distance information
- Expandable quote-style blocks

Visible action menu:

| Row | Buttons |
|---|---|
| 1 | `🔽 Sort by…` · `🏠 View All Saved Addresses` |
| 2 | `📍 Distance Sort` · `🎲 Random Address` |
| 3 | `🔀 Hub Swap` |
| Additional | Add address, history, and other navigation actions |

### ReceiptPilot equivalent

After scanning, ReceiptPilot should show detected data rather than forcing the user to understand raw OCR.

For uncertain or missing data, display a structured help screen:

```html
🧩 <b>Some fields need confirmation</b>

Required:
• Recipient or merchant name
• Address or document number
• Date
• Total or tracking number

Optional:
• Phone
• Company
• Notes
```

Relevant actions:

| Row | Buttons |
|---|---|
| 1 | `✏️ Complete Fields` · `📍 Saved Details` |
| 2 | `🎲 Use Sample Data` · `🔄 Rescan` |
| 3 | `🏠 Main Menu` |

Sample data must be clearly marked as test data and must never be used in a real carrier transaction.

---

## 00:12–00:15 — Saved Address Selector

The user taps **View All Saved Addresses**.

The bot responds with:

```text
All Saved UPS Addresses (Page 1/1)

Select an address to use or navigate through pages.
```

Each saved record appears as a full-width button:

```text
John Doe - ABC Company - 123 Main St, New York, NY 10001
```

The selected record is sent back as a user action, and the bot immediately opens the confirmation screen.

### ReceiptPilot equivalent

Use a saved-data selector for:

- Saved merchants
- Saved sender profiles
- Saved recipient profiles
- Common billing addresses
- Common document templates

Example:

```html
📍 <b>Saved Profiles</b>

Select a profile to fill the missing fields.
```

Display one record per row:

```text
Food Lion · Clemmons, NC
ABC Company · New York, NY
Default Sender · Commerce City, CO
```

Use pagination after six to eight entries.

Required controls:

| Row | Buttons |
|---|---|
| 1 | `⬅️ Previous` · `Next ➡️` |
| 2 | `🔎 Search` · `➕ Add Profile` |
| 3 | `⬅️ Back` |

---

## 00:15–00:17 — Main Confirmation Card

The reference bot displays one compact confirmation card containing:

- Tracking number
- Carrier
- Ship-to heading
- Receiver name
- Address line 1
- Address line 2
- City
- State/province
- Postal code
- Phone
- Company
- Ship-from profile
- Notes

The address data is shown in a quoted monospaced block.

Example structure:

```text
Please confirm the shipping information:

Tracking Number: ...
Carrier: UPS

SHIP TO:
RECEIVER NAME  | John Doe
ADDRESS LINE 1 | 123 Main St
ADDRESS LINE 2 | Apt 101
CITY           | New York
STATE/PROVINCE | NY
POSTAL CODE    | 10001
PHONE          | ...
COMPANY        | ABC Company

SHIP FROM:
Default: TX

NOTES:
None
```

This screen acts as the bot’s main editor dashboard.

### ReceiptPilot equivalent

```html
✅ <b>Please confirm the detected information</b>

<b>Document:</b> USPS Ground Advantage
<b>Confidence:</b> 94%

<b>SHIP TO</b>
<pre>
RECIPIENT      | Food Lion
ADDRESS LINE 1 | 1410 River Ridge Dr
CITY           | Clemmons
STATE          | NC
POSTAL CODE    | 27012-8355
</pre>

<b>TRACKING</b>
<code>9748 •••• •••• •••• 8529 81</code>

<b>NOTES</b>
None
```

Use a monospaced block for aligned fields, but escape all content safely.

---

# 2. Main Dynamic Control Panel

The most important feature in the reference is a large, persistent configuration keyboard attached to the confirmation workflow.

## Primary Action

A full-width green button:

```text
✅ Generate Label
```

### ReceiptPilot equivalent

For scanning and verification:

```text
✅ Approve Result
```

For authorized integrations only:

```text
📦 Create Carrier Shipment
```

Do not generate real postage, tracking events, or carrier labels unless ReceiptPilot is connected to an authorized carrier account/API.

---

## Configuration Buttons Seen in the Video

The full control panel includes:

| Setting | Display style |
|---|---|
| Service | `🚚 Service: Ground` |
| Weight | `⚖️ Weight: 🔴` or `⚖️ Weight: 3 LBS` |
| Sort belt | `↕️ Sort Belt: Automatic` |
| Dimensions | `📐 Dimensions: 🔴` |
| Return service | `🏠 RS: 🔴` or `🏠 RS: 🟢` |
| Reference 1 | `📝 Reference 1: None/Random` |
| Reference 2 | `📝 Reference 2: None` |
| Description | `📝 Description: None` |
| Tracking option | `🔀 Scramble Tracking: 🔴` |
| Sender editor | `📝 Edit Ship From` |
| Recipient editor | `✏️ Edit Ship To` |
| Note editor | `📝 Edit Note` |

### State indicators

- `🔴` means disabled, empty, or not configured.
- `🟢` means enabled.
- A real value replaces the indicator when configured.
- The keyboard is redrawn after every setting change.

### ReceiptPilot mapping

| Reference control | ReceiptPilot control |
|---|---|
| Service | `🧩 Template: USPS` |
| Weight | `🎯 Confidence: 94%` |
| Sort belt | `↕️ Sort: Automatic` |
| Dimensions | `🖼 Crop: Automatic` |
| Return service | `🔐 Masking: 🟢` |
| Reference 1 | `📝 Reference 1: None` |
| Reference 2 | `📝 Reference 2: None` |
| Description | `📝 Notes: None` |
| Scramble tracking | `🔒 Hide Tracking: 🟢` |
| Edit Ship From | `✏️ Edit Sender` |
| Edit Ship To | `✏️ Edit Recipient` |
| Edit Note | `✏️ Edit Notes` |

Recommended ReceiptPilot review keyboard:

| Row | Buttons |
|---|---|
| 1 | `✅ Approve Result` |
| 2 | `🧩 Template: USPS` |
| 3 | `🎯 Confidence: 94%` · `🔐 Masking: 🟢` |
| 4 | `✏️ Edit Sender` · `✏️ Edit Recipient` |
| 5 | `📝 Reference 1: None` · `📝 Reference 2: None` |
| 6 | `📝 Notes: None` · `🔎 View OCR` |
| 7 | `🔄 Rescan` · `❌ Reject` |

Secondary controls can be moved into a settings submenu on smaller screens.

---

# 3. One-Setting-at-a-Time Editing

## 00:17–00:19 — Weight Editor

The user taps the weight button.

The bot sends:

```text
Please enter the package weight in LBS:

Enter a whole number (e.g., 5 for 5 LBS)

Type OFF to turn off weight (or to go back)!
```

Shortcut buttons:

| Row | Buttons |
|---|---|
| 1 | `10` · `3` |
| 2 | `OFF` · `Back to Label Confirmation` |

The user enters `3`.

The bot replies:

```text
Weight set to 3 LBS.
```

It then returns to the confirmation screen and updates the button:

```text
⚖️ Weight: 3 LBS
```

### Required interaction rule

Every editable setting must follow the same pattern:

1. User taps a setting.
2. Bot opens a focused editor.
3. Bot explains the accepted input.
4. Bot shows common shortcut buttons.
5. User sends one value.
6. Bot validates it.
7. Bot sends a short success message.
8. Bot returns to confirmation.
9. The button immediately shows the new value.

ReceiptPilot examples:

- Total
- Date
- Merchant
- Tracking number
- Recipient name
- Template
- Confidence override
- Notes
- Export format
- Masking setting

---

## 00:20–00:23 — Boolean Toggle

The user taps `RS: 🔴`.

The bot immediately switches it on:

```text
Return Service turned ON
```

The confirmation screen reappears with:

```text
RS: 🟢
```

### ReceiptPilot toggle examples

- `🔐 Masking: 🔴/🟢`
- `🖼 Store Image: 🔴/🟢`
- `📝 Store OCR: 🔴/🟢`
- `🔔 Notify on Approval: 🔴/🟢`
- `🤖 Auto Template: 🔴/🟢`

Boolean options should toggle in one tap unless the change has privacy or retention consequences.

For privacy-sensitive settings, require confirmation.

---

## 00:24–00:28 — Text/Reference Editor

The user taps `Reference 1: None`.

The bot explains:

- Custom text is accepted.
- A `RANDOMIZE` keyword is supported.
- Special two-letter codes can be used.
- Common actions are available as buttons.

Buttons:

| Row | Buttons |
|---|---|
| 1 | `RANDOMIZE` · `OFF` |
| 2 | `Back to Label Confirmation` |

The user taps `RANDOMIZE`.

The bot confirms:

```text
Reference 1 set to RANDOMIZE.
```

The confirmation keyboard updates:

```text
Reference 1: Random
```

### ReceiptPilot equivalent

Reference fields may support:

- Custom order reference
- Internal record number
- Customer ID
- Store ID
- Notes
- Generated short submission ID

Do not randomize official tracking numbers, transaction IDs, or carrier-issued identifiers.

---

# 4. Generation and Final Delivery

## 00:30–00:32 — Generate Action

The user taps the green primary button.

The bot sends a user-action bubble and then:

```text
Generating UPS Ground label...
```

The primary configuration keyboard remains visible.

### ReceiptPilot equivalent

```html
⏳ <b>Preparing approved output…</b>

✅ Validating fields
📄 Creating export
```

Disable repeated processing server-side even if the user taps the button more than once.

---

## 00:33–00:35 — File Delivery

The bot returns:

- An image file
- Filename based on the tracking number
- File size
- Download action
- Success message
- Tracking number
- Version number

Example structure:

```text
UPS label created!

TRACKING NUMBER:
1Z...

[version 8.14.0]
```

### ReceiptPilot equivalent

Return:

- Approved PDF or image
- Submission ID
- Masked primary identifier
- Document type
- Export timestamp
- Application version when useful

Example:

```html
✅ <b>Submission Approved</b>

<b>Document:</b> USPS Ground Advantage
<b>Tracking:</b> 9748 •••• 8529
<b>Submission:</b> RP-8F2A19
<b>Saved:</b> 02 Aug 2026, 3:10 AM
```

Buttons:

| Row | Buttons |
|---|---|
| 1 | `📄 Export PDF` · `🖼 Export Image` |
| 2 | `🔎 View Details` · `📋 History` |
| 3 | `📤 Scan Another` |
| 4 | `🏠 Main Menu` |

---

# 5. Visual Language to Match

## Message style

The reference uses:

- Telegram dark mode
- Compact text
- Bold headings
- Monospaced data tables
- Quote-style blocks with a colored left edge
- Short status messages
- User actions displayed as normal sent messages
- Immediate feedback after every action
- Minimal decorative prose

ReceiptPilot should use Telegram HTML:

- `<b>` for headings and labels
- `<code>` for short identifiers
- `<pre>` for aligned field blocks
- `<blockquote>` where supported for grouped information
- Safe HTML escaping for every OCR/user-provided value

---

## Button style

The reference interface uses:

- Full-width primary action
- Two-column configuration rows
- Short button labels
- Dynamic current values
- Red/green state dots
- Back button in every editor
- Persistent controls near the input bar
- No need to type commands during the main workflow

ReceiptPilot must use reusable keyboard builders.

Suggested functions:

```text
build_main_menu_keyboard()
build_review_keyboard()
build_saved_profiles_keyboard()
build_weight_or_numeric_editor_keyboard()
build_boolean_settings_keyboard()
build_text_editor_keyboard()
build_export_keyboard()
build_history_keyboard()
```

---

## Emoji style

The video mainly uses simple Unicode emoji.

ReceiptPilot may use Telegram custom/premium emoji for:

- Processing
- Approved
- Warning
- Document
- Scanner
- Settings
- Privacy
- History

Requirements:

- Always include a normal Unicode fallback.
- Use custom emoji sparingly.
- Do not make every field animated.
- Keep the control panel professional and readable.
- Use the same icon for the same action everywhere.

---

# 6. What Telegram Controls vs What the Bot Controls

## Telegram controls

ReceiptPilot cannot directly control:

- Telegram dark/light theme
- Desktop/macOS window design
- Chat-list appearance
- Message bubble shape
- Right-click/long-press menu
- Saved Messages interface
- Forward selector
- Input-bar design
- Download-link rendering
- Telegram timestamps

## ReceiptPilot controls

ReceiptPilot can control:

- Welcome banner/GIF
- Message text and formatting
- Reply keyboard
- Inline keyboard
- Button labels
- Button state
- Button layout
- Processing status
- Callback actions
- Saved profile list
- Confirmation card
- Editing workflow
- File names
- Exported files
- Error messages
- Data validation
- Approval state
- History
- Privacy settings

The implementation should target the controllable parts and let Telegram render the native interface around them.

---

# 7. Required State Machine

Use explicit conversation states:

```text
HOME
WAITING_FOR_UPLOAD
PROCESSING
WAITING_FOR_PROFILE_SELECTION
REVIEW
EDITING_FIELD
EDITING_NUMERIC_VALUE
EDITING_TEXT_VALUE
EDITING_BOOLEAN_SETTING
WAITING_FOR_CONFIRMATION
GENERATING_OUTPUT
COMPLETED
FAILED
CANCELLED
```

Each submission should also have persistent database states:

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

Every callback must verify:

- Correct user
- Correct submission
- Correct current state
- Non-expired action
- No duplicate completion

---

# 8. Required Data Architecture

Store the current editor values in the database or a server-side cache.

Do not encode full data in callback strings.

Example callback data:

```text
doc:approve:1842
doc:field:recipient:1842
doc:setting:masking:1842
doc:export:pdf:1842
profile:select:93:1842
nav:review:1842
```

Keep callback data compact.

Recommended current-review record:

```json
{
  "submission_id": 1842,
  "user_id": 123456789,
  "template": "usps_ground_advantage",
  "confidence": 0.94,
  "fields": {
    "recipient_name": "Food Lion",
    "address_line_1": "1410 River Ridge Dr",
    "city": "Clemmons",
    "state": "NC",
    "postal_code": "27012-8355",
    "tracking_number": "9748577400768408852981"
  },
  "settings": {
    "mask_sensitive_data": true,
    "store_original_image": false,
    "store_ocr_text": true
  },
  "status": "needs_review"
}
```

---

# 9. Exact ReceiptPilot Flow to Build

## Step 1

User opens `/start`.

Show branded banner, status card, and persistent main menu.

## Step 2

User sends or forwards an image.

Accept the image without requiring another command.

## Step 3

Show one edited processing message.

## Step 4

Run OCR, template detection, field extraction, and validation.

## Step 5

When fields are uncertain, show structured guidance and saved-profile options.

## Step 6

Show a compact confirmation card.

## Step 7

Show a large dynamic configuration keyboard.

## Step 8

Allow each field or setting to be edited separately.

## Step 9

After each change, return to the confirmation card and redraw the keyboard with the new value.

## Step 10

Use a prominent green approval button.

## Step 11

Validate all required fields and prevent duplicate approval.

## Step 12

Return an approved export and keep navigation buttons available.

---

# 10. Mandatory Quality Requirements

- All forwarded images must be accepted.
- The first processing response should appear immediately.
- The user should not need to memorize commands.
- Main actions should always be visible as buttons.
- Every submenu must have a back action.
- Every setting must show its current value.
- Changed values must update immediately.
- Numeric editors should include shortcut buttons.
- Boolean controls should show red/green state.
- Long saved lists must use pagination.
- The confirmation card must remain compact.
- Sensitive data must be masked by default.
- OCR text should be behind a details screen.
- Duplicate taps must be idempotent.
- Generated exports must have safe filenames.
- Errors must return the user to a recoverable state.
- Temporary files must be deleted.
- Mobile-width layouts must be tested.

---

# 11. Important Differences for ReceiptPilot

The reference video demonstrates a shipping-label generation workflow.

ReceiptPilot should copy:

- The button-driven UX
- Dynamic settings panel
- Saved profiles
- One-field-at-a-time editing
- Confirmation screen
- Immediate status feedback
- File delivery
- Persistent navigation

ReceiptPilot should not copy or enable:

- Unauthorized postage generation
- Fabricated carrier labels
- Fake tracking events
- Randomized official tracking numbers
- Altered routing codes intended to misrepresent a shipment
- Carrier branding that implies authorization without permission

For legitimate label creation, connect the final action to an authorized USPS, UPS, FedEx, or shipping-platform API and return the carrier-issued label unchanged.

For the current receipt-verification product, the primary action should be:

```text
✅ Approve Result
```

rather than:

```text
✅ Generate Label
```

---

# 12. Final Assessment

The reference experience is defined by five major qualities:

1. **The bot responds immediately.**
2. **Nearly every action is button-driven.**
3. **The confirmation screen acts as a live dashboard.**
4. **Every setting displays its current value.**
5. **Editing happens one field at a time and always returns to the dashboard.**

ReceiptPilot should reproduce those five qualities exactly while using its own branding, legitimate document-processing purpose, secure data model, and authorized integrations.
