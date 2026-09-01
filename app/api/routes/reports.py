from fastapi import APIRouter, Response

from app.api.dependencies import DbSession
from app.services.reports import (
    build_room_sections,
    inventory_summary,
    render_inventory_csv,
    render_inventory_pdf,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
def inventory_summary_endpoint(db: DbSession) -> dict[str, int]:
    return inventory_summary(db)


@router.get("/inventory.pdf")
def inventory_report_pdf(db: DbSession) -> Response:
    sections = build_room_sections(db)
    pdf_bytes = render_inventory_pdf(sections)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=inventory-report.pdf"},
    )


@router.get("/inventory.csv")
def inventory_report_csv(db: DbSession) -> Response:
    sections = build_room_sections(db)
    csv_text = render_inventory_csv(sections)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory-report.csv"},
    )
