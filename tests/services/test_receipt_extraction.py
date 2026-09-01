from app.services.receipt_extraction import parse_receipt_text


def test_parse_receipt_text_returns_item_field_suggestions():
    result = parse_receipt_text(
        """Example Electronics
2026-08-29
Model: TV-55X
Serial No: SN-12345
Grand Total £1,249.99
"""
    )

    assert result.merchant and result.merchant.value == "Example Electronics"
    assert result.purchase_date and result.purchase_date.value == "2026-08-29"
    assert result.model and result.model.value == "TV-55X"
    assert result.serial_number and result.serial_number.value == "SN-12345"
    assert result.estimated_value and result.estimated_value.value == "1249.99"


def test_parse_receipt_text_supports_decimal_comma():
    result = parse_receipt_text("Shop Name\nTotal: €49,95")

    assert result.estimated_value and result.estimated_value.value == "49.95"