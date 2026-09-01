import csv
import io
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.storage import resolve_path
from app.db.models import Category, HouseholdItem, Room


@dataclass
class ReportItemRow:
    item: HouseholdItem
    thumbnail_path: Path | None = None


@dataclass
class RoomReportSection:
    room_name: str
    rows: list[ReportItemRow] = field(default_factory=list)
    subtotal: Decimal = Decimal("0")


def _thumbnail_path(item: HouseholdItem) -> Path | None:
    photo = next((attachment for attachment in item.attachments if attachment.attachment_type == "item_photo"), None)
    if photo is None:
        return None

    path = resolve_path(photo.storage_key)
    return path if path.is_file() else None


def _thumbnail(path: Path | None) -> Image | str:
    if path is None:
        return ""

    try:
        ImageReader(path).getSize()
        return Image(str(path), width=16 * mm, height=16 * mm, kind="proportional")
    except Exception:
        return ""


def build_room_sections(db: Session, *, include_all_statuses: bool = False) -> list[RoomReportSection]:
    stmt = (
        select(HouseholdItem)
        .options(
            selectinload(HouseholdItem.room),
            selectinload(HouseholdItem.category),
            selectinload(HouseholdItem.attachments),
        )
        .order_by(HouseholdItem.name)
    )
    if not include_all_statuses:
        stmt = stmt.where(HouseholdItem.status == "active")

    items = list(db.scalars(stmt))

    sections_by_room: dict[uuid.UUID, RoomReportSection] = {}
    for item in items:
        section = sections_by_room.setdefault(item.room_id, RoomReportSection(room_name=item.room.name))
        section.rows.append(ReportItemRow(item=item, thumbnail_path=_thumbnail_path(item)))
        section.subtotal += item.estimated_value or Decimal("0")

    return sorted(sections_by_room.values(), key=lambda section: section.room_name)


def total_estimated_value(sections: list[RoomReportSection]) -> Decimal:
    return sum((section.subtotal for section in sections), Decimal("0"))


def inventory_summary(db: Session) -> dict[str, int]:
    total_items = db.scalar(select(func.count(HouseholdItem.id))) or 0
    active_items = db.scalar(select(func.count(HouseholdItem.id)).where(HouseholdItem.status == "active")) or 0
    rooms_count = db.scalar(select(func.count(Room.id))) or 0
    categories_count = db.scalar(select(func.count(Category.id))) or 0

    return {
        "total_items": int(total_items),
        "active_items": int(active_items),
        "rooms_count": int(rooms_count),
        "categories_count": int(categories_count),
    }


def render_inventory_pdf(sections: list[RoomReportSection]) -> bytes:
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph("Household Inventory Report", styles["Title"]), Spacer(1, 6 * mm)]

    for section in sections:
        story.append(Paragraph(escape(section.room_name), styles["Heading2"]))
        table_data = [["Photo", "Name", "Category", "Brand / Model", "Serial Number", "Purchase Date", "Est. Value"]]
        for row in section.rows:
            item = row.item
            brand_model = " / ".join(value for value in (item.brand, item.model) if value)
            table_data.append(
                [
                    _thumbnail(row.thumbnail_path),
                    escape(item.name),
                    escape(item.category.name if item.category else ""),
                    escape(brand_model),
                    escape(item.serial_number or ""),
                    item.purchase_date.isoformat() if item.purchase_date else "",
                    f"{item.estimated_value:.2f}" if item.estimated_value is not None else "",
                ]
            )

        table = Table(
            table_data,
            repeatRows=1,
            colWidths=[20 * mm, 38 * mm, 32 * mm, 44 * mm, 38 * mm, 30 * mm, 26 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEE9")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#173D35")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CCD5D0")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.extend(
            [
                table,
                Paragraph(f"Room subtotal: {section.subtotal:.2f}", styles["Normal"]),
                Spacer(1, 6 * mm),
            ]
        )

    story.append(Paragraph(f"Total estimated value: {total_estimated_value(sections):.2f}", styles["Heading2"]))
    document.build(story)
    return buffer.getvalue()


def render_inventory_csv(sections: list[RoomReportSection]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Room", "Name", "Category", "Brand", "Model", "Serial Number", "Estimated Value", "Purchase Date", "Status"]
    )
    for section in sections:
        for row in section.rows:
            item = row.item
            writer.writerow(
                [
                    section.room_name,
                    item.name,
                    item.category.name if item.category else "",
                    item.brand or "",
                    item.model or "",
                    item.serial_number or "",
                    str(item.estimated_value) if item.estimated_value is not None else "",
                    item.purchase_date.isoformat() if item.purchase_date else "",
                    item.status,
                ]
            )
    return buffer.getvalue()
