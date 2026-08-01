# Image Comparison Report

## Scope

- **Image 1:** Original reference label
- **Image 2:** Bot-generated label
- **Original size:** 853 × 1280 px
- **Bot-generated size:** 600 × 900 px
- Both images use approximately the same 2:3 aspect ratio.

> This report evaluates visual fidelity, data accuracy, layout, and scan-readiness. For real shipping use, carrier-issued labels and carrier-generated barcode assets should be preserved rather than recreated.

---

## Executive Summary

The bot-generated result is recognizable as the same general label type, but it is **not yet a close reproduction of the original**.

The largest issues are:

1. The recipient block contains incorrect and missing text.
2. An extra horizontal divider was added between the sender and recipient areas.
3. The section heights differ substantially from the original.
4. The main `G`, header QR, and header text are too small.
5. The 2D codes and main barcode visibly differ and require scan validation.
6. The bottom section is much too short.
7. Font weights, sizes, spacing, and alignment do not match the reference.
8. The generated label has an unnecessary outer white margin.

---

## Critical Issues

### 1. Recipient information is incorrect

**Original:**

```text
SHIP TO:  FOOD LION
          1410 RIVER RIDGE DR
          CLEMMONS NC 27012-8355
```

**Bot-generated:**

```text
SHIP TO:  VEYA 1410 RIVER RIDGE DR
          CLEMMONS NC 27012-8355
```

Problems:

- `FOOD LION` is missing.
- `VEYA` appears in the generated version but is not present in the original.
- The recipient name and street address were merged into one line.
- The original three-level structure was reduced to two lines.
- The first address line no longer aligns with the recipient name position.

**Required fix:** Keep separate fields for recipient name, address line 1, and city/state/ZIP. Do not construct the whole recipient block from one unvalidated OCR string.

---

### 2. Barcode and 2D-code data cannot be assumed valid

The following symbols visibly differ between the images:

- Header QR code
- Recipient-area 2D code
- Main tracking barcode
- Bottom-right 2D code

A visually similar code is not sufficient. Each symbol must decode to the expected value and use the expected symbology.

**Required fix:**

- For legitimate shipping workflows, preserve the original carrier-generated barcode assets or request them from the authorized carrier system.
- Add automated decode verification after rendering.
- Reject the generated output when any code fails to decode or decodes to the wrong value.
- Do not generate live postage or carrier-routing codes from guessed content.

---

### 3. Extra divider changes the label structure

The original has one continuous sender/recipient panel from approximately:

```text
Y = 293 to 816
```

The bot-generated version inserts a horizontal divider around:

```text
Y = 370
```

This splits the sender and recipient areas into separate panels.

**Required fix:** Remove the divider between sender and recipient blocks. Position both blocks inside one continuous central panel.

---

## Major Layout Differences

### 4. Outer border and canvas margin

**Original:**

- Border starts almost at the image edge.
- Approximate left/right border position: `x = 1–2` and `x = 849–850`.

**Bot-generated:**

- Adds about 10 px of white canvas around the label.
- Approximate left/right border position: `x = 10–12` and `x = 588–590`.

**Required fix:** Render the label border at the intended page edge or crop the final image to the border.

---

### 5. Header height is too compressed

Horizontal divisions:

| Section boundary | Original | Bot-generated |
|---|---:|---:|
| Top border | 2–3 px | 10–12 px |
| Header bottom | 223–224 px | 144–146 px |
| Service title bottom | 291–292 px | 194–196 px |

When normalized to image height, the generated header is still slightly more compressed and its contents are much smaller than the available space.

**Required fix:** Increase the `G`, QR code, instructional copy, and postage notice proportionally while preserving the section height.

---

### 6. Central content proportions are incorrect

**Original central panel:**

```text
Y = 293 to 816
Height ≈ 524 px
```

**Bot layout:**

```text
Sender panel: Y = 197 to 369
Recipient panel: Y = 372 to 599
```

Although the total central area is similar in proportion, the internal division and vertical positioning differ substantially.

**Required fix:** Use one panel. Place sender information at the upper-left, routing data at the upper-right, and recipient information lower in the same panel.

---

### 7. Bottom section is much too short

**Original bottom band:**

```text
Y = 1142 to 1275
Height ≈ 134 px
```

**Bot bottom band:**

```text
Y = 832 to 888
Height ≈ 57 px
```

The generated bottom section has less than half the proportional height of the original.

Effects:

- Bottom-right code is too close to the borders.
- The large white area from the reference is missing.
- Overall visual balance is altered.

**Required fix:** Increase the final bottom band and reproduce the original code offset and surrounding whitespace.

---

## Element-by-Element Comparison

### 8. Large `G`

The generated `G` is much too small.

**Original:**

- Dominates the left header cell.
- Nearly fills the available height and width.

**Bot-generated:**

- Appears centered but occupies only a small part of the cell.
- Has excessive empty space around it.

**Required fix:** Increase the letter size substantially and verify baseline/centering against the original.

---

### 9. Header QR code

The bot-generated header QR is too small relative to the header cell.

**Required fix:** Increase its rendered dimensions and maintain a clean quiet zone. Validate it with a QR decoder after export.

---

### 10. Header instructional text

The generated text is:

- Too small
- Too tightly spaced
- Positioned too close to the QR code
- Less prominent than the reference

The line content is broadly similar, but the typographic proportions do not match.

**Required fix:** Increase font size and line spacing and match the reference’s four-line wrapping.

---

### 11. Postage notice

The text content is present, but:

- The generated box has different padding.
- Text is smaller.
- The box sits within a header layout that has different proportions.

**Required fix:** Match the reference box size, inset, text size, and line spacing.

---

### 12. Service title

**Original:** `USPS GROUND ADVANTAGE`

Differences:

- Original uses a lighter/regular weight.
- Generated version is much bolder.
- Generated text is slightly smaller relative to its panel.
- Vertical spacing differs.

**Required fix:** Use a regular sans-serif weight and match the original title height and baseline.

---

### 13. Sender block

The sender data matches:

```text
ALBERT OSBORN
421 SUNNY MAGNOLIA ROW
COMMERCE CITY CO 80229
```

However, the generated version is:

- Too small
- Too close to the upper border
- More tightly spaced
- Positioned differently relative to `0001` and `R004`

**Required fix:** Increase font size and line height and restore the original top/left padding.

---

### 14. `0001` identifier

The value is correct.

Differences:

- Generated value is smaller.
- Position is slightly lower relative to the sender block.
- Weight and spacing differ.

**Required fix:** Match the original top-right offset and font scale.

---

### 15. `R004` route box

The value is correct.

Differences:

- Generated text is bold; original appears regular.
- Box proportions and placement differ.
- Generated box is positioned within the artificial sender-only panel.

**Required fix:** Use regular-weight text and position it in the continuous central panel.

---

### 16. Recipient 2D code

The generated code is placed higher and closer to the `SHIP TO` line than in the original.

The original code begins below the `SHIP TO` heading and aligns beside the address block. The generated code begins almost level with the heading.

**Required fix:** Move the symbol downward and align it with the first address line. Verify the quiet zone and decoding.

---

### 17. Tracking section

The overall section is recognizable, but several details differ:

- Original uses heavier horizontal rules above and below the section.
- Generated rules use the same thin weight as most other borders.
- Generated barcode is wider relative to the page.
- Generated bars appear thinner and more densely spaced.
- Tracking title and number are smaller.
- Vertical spacing between title, barcode, and number differs.

**Required fix:**

- Restore the heavy section separators.
- Match the original barcode bounding box.
- Center the barcode and human-readable number independently.
- Verify the barcode by decoding, not visual inspection.

---

### 18. Tracking number text

The displayed number matches:

```text
9748 5774 0076 8408 8529 81
```

Differences:

- Generated text is smaller.
- Weight and vertical position differ.
- Spacing below the barcode is tighter.

**Required fix:** Increase font size and restore the original bottom spacing.

---

### 19. Bottom-right 2D code

The generated code is:

- Smaller
- Too close to the lower and right borders
- Located in a bottom band that is too short
- Visually different from the original symbol

**Required fix:** Increase the bottom band first, then position the code using the reference offsets and validate decoding.

---

## Typography Report

The generated output uses inconsistent weights compared with the original.

### Too bold in the generated image

- `USPS GROUND ADVANTAGE`
- `SHIP TO:`
- Recipient/address content
- `R004`

### Too small in the generated image

- Large `G`
- Header QR
- Header instructional text
- Sender block
- `0001`
- Tracking heading
- Tracking number

### Recommended typography system

Use a single metrically stable sans-serif family and define explicit styles:

```text
header_mark
header_instruction
postage_notice
service_title
sender_text
recipient_label
recipient_name
recipient_address
routing_primary
routing_box
tracking_heading
tracking_number
```

Do not rely on browser/default bold behavior. Set font family, size, weight, line height, and letter spacing explicitly for every style.

---

## Recommended Fix Priority

### Priority 1 — Must fix before testing

1. Correct recipient name and remove `VEYA`.
2. Restore separate recipient-name and address lines.
3. Remove the extra center divider.
4. Use authorized/verified code assets.
5. Add barcode and QR/Data Matrix decode tests.
6. Preserve exact tracking data.
7. Prevent approval when required fields do not match the source.

### Priority 2 — Major visual corrections

1. Increase the large `G`.
2. Increase the header QR and instructional text.
3. Expand the bottom section.
4. Restore heavy tracking-section separators.
5. Correct central-panel element positions.
6. Match title and label font weights.
7. Remove the 10 px outer canvas margin.

### Priority 3 — Fine tuning

1. Match text line heights.
2. Adjust box padding.
3. Match barcode bounding dimensions.
4. Refine horizontal and vertical alignment.
5. Match whitespace around all 2D codes.
6. Tune title and tracking-number letter spacing.

---

## Suggested Automated Quality Checks

Add these checks to the bot’s rendering pipeline:

### Data checks

- Source recipient name equals rendered recipient name.
- Source address lines equal rendered address lines.
- Tracking number digits match exactly.
- Required fields are not merged.
- No unknown OCR token is introduced.
- ZIP+4 formatting is preserved.

### Layout checks

- Expected section count and order.
- No divider exists inside the central sender/recipient panel.
- Header, tracking section, and bottom band fall within configured proportions.
- Outer border aligns with the final crop.
- Required elements remain inside safe bounds.

### Scan checks

- Decode the header QR.
- Decode the recipient-area 2D symbol.
- Decode the tracking barcode.
- Decode the bottom-right 2D symbol.
- Compare every decoded payload with its expected source value.
- Fail output generation when a required symbol is unreadable.

### Visual regression checks

Maintain the original as a reference fixture and compare:

- Section boundaries
- Element bounding boxes
- Text baselines
- Font sizes
- Border thickness
- Whitespace
- Overall structural similarity

Use tolerance ranges rather than requiring pixel-for-pixel equality.

---

## Final Assessment

| Category | Assessment |
|---|---|
| General resemblance | Moderate |
| Text accuracy | Poor because recipient data is wrong |
| Layout fidelity | Low to moderate |
| Typography fidelity | Low |
| Barcode confidence | Unverified |
| Production readiness | Not ready |
| Best next action | Fix data mapping first, then layout, then scan validation |

The generated image should not be treated as a valid shipping label until all machine-readable symbols are obtained from an authorized source or independently verified against the expected data.
