# Schedule Parser & Calendar Sync - Interview Q&A

## Q1: Why use OCR + LLM instead of pure template matching?
**A:** Schedule formats vary widely between employers - tables, lists, calendar grids. Template matching breaks on format changes. OCR + LLM handles any visual format because the LLM understands the semantic meaning of schedule data regardless of layout.

## Q2: How do you handle OCR errors?
**A:** The image preprocessor enhances contrast and sharpness before OCR. The LLM parser is robust to minor OCR errors because it understands context (e.g., "Apr12" is likely "Apr 12"). The validator agent catches impossible values.

## Q3: How do you prevent duplicate calendar events?
**A:** Before creating events, we check Google Calendar for existing events at the same date/time range. If a matching event exists (same title pattern and time), we skip creation and increment the duplicates_skipped counter.

## Q4: What image formats are supported?
**A:** PNG, JPG, JPEG, BMP, TIFF via Pillow. The preprocessor converts all formats to grayscale PNG for consistent OCR processing.

## Q5: How would you handle recurring shifts?
**A:** The parser agent can detect patterns (e.g., "Mon-Fri 6am-2pm") and create recurring events using Google Calendar's RRULE recurrence format instead of individual events.
