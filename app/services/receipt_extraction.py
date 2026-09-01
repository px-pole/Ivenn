import re
from datetime import datetime
from pathlib import Path

import pytesseract
from PIL import Image, UnidentifiedImageError

from app.schemas.attachment import ReceiptExtractionRead, ReceiptFieldSuggestion


class ExtractionUnsupportedError(Exception):
    """Raised when an attachment cannot be processed as an image."""


class ExtractionUnavailableError(Exception):
    """Raised when the configured OCR engine cannot run."""


_DATE_PATTERNS = (
    (re.compile(r"\b(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b"), ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d")),
    (re.compile(r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b"), ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%y", "%d/%m/%y", "%d.%m.%y")),
)
_TOTAL_PATTERN = re.compile(
    r"(?:grand\s+total|amount\s+due|total)\s*[:\-]?\s*[£€$]?\s*(\d[\d.,]*)",
    re.IGNORECASE,
)
_MODEL_PATTERN = re.compile(r"\bmodel\s*(?:no\.?|number|#|:)\s*([A-Z0-9][A-Z0-9._/-]+)", re.IGNORECASE)
_SERIAL_PATTERN = re.compile(r"\b(?:serial(?:\s+no\.?|\s+number)?|s/n)\s*[:#]?\s*([A-Z0-9][A-Z0-9._/-]+)", re.IGNORECASE)


def _suggest(value: str, confidence: float, evidence: str) -> ReceiptFieldSuggestion:
    return ReceiptFieldSuggestion(value=value, confidence=confidence, evidence=evidence.strip())


def _parse_date(lines: list[str]) -> ReceiptFieldSuggestion | None:
    for line in lines:
        for pattern, formats in _DATE_PATTERNS:
            match = pattern.search(line)
            if match is None:
                continue
            for date_format in formats:
                try:
                    parsed = datetime.strptime(match.group(1), date_format).date()
                    return _suggest(parsed.isoformat(), 0.82, line)
                except ValueError:
                    continue
    return None


def _normalize_amount(value: str) -> str | None:
    compact = value.replace(" ", "")
    if "," in compact and "." in compact:
        decimal_separator = "," if compact.rfind(",") > compact.rfind(".") else "."
        thousands_separator = "." if decimal_separator == "," else ","
        compact = compact.replace(thousands_separator, "").replace(decimal_separator, ".")
    elif "," in compact:
        compact = compact.replace(",", ".") if len(compact.rsplit(",", 1)[-1]) == 2 else compact.replace(",", "")

    try:
        return f"{float(compact):.2f}"
    except ValueError:
        return None


def _parse_total(lines: list[str]) -> ReceiptFieldSuggestion | None:
    for line in reversed(lines):
        match = _TOTAL_PATTERN.search(line)
        if match is None:
            continue
        amount = _normalize_amount(match.group(1))
        if amount is not None:
            return _suggest(amount, 0.88, line)
    return None


def _parse_pattern(lines: list[str], pattern: re.Pattern[str]) -> ReceiptFieldSuggestion | None:
    for line in lines:
        match = pattern.search(line)
        if match is not None:
            return _suggest(match.group(1), 0.78, line)
    return None


def parse_receipt_text(raw_text: str) -> ReceiptExtractionRead:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    merchant_line = next((line for line in lines if len(line) >= 3 and re.search(r"[A-Za-z]", line)), None)

    return ReceiptExtractionRead(
        raw_text=raw_text,
        merchant=_suggest(merchant_line, 0.55, merchant_line) if merchant_line else None,
        purchase_date=_parse_date(lines),
        estimated_value=_parse_total(lines),
        model=_parse_pattern(lines, _MODEL_PATTERN),
        serial_number=_parse_pattern(lines, _SERIAL_PATTERN),
    )


def extract_receipt(path: Path, mime_type: str) -> ReceiptExtractionRead:
    if not mime_type.startswith("image/"):
        raise ExtractionUnsupportedError("OCR currently supports JPEG, PNG, and WebP images")

    try:
        with Image.open(path) as image:
            raw_text = pytesseract.image_to_string(image)
    except (UnidentifiedImageError, OSError) as exc:
        raise ExtractionUnsupportedError("The attachment is not a readable image") from exc
    except pytesseract.TesseractNotFoundError as exc:
        raise ExtractionUnavailableError("The local OCR engine is not installed") from exc
    except pytesseract.TesseractError as exc:
        raise ExtractionUnavailableError("The local OCR engine could not process this image") from exc

    return parse_receipt_text(raw_text)
