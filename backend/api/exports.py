"""
Exports API — NPCBVI HMIS Form 1 CSV download.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import require_roles
from services.export_service import generate_hmis_form1
import io
import re

router = APIRouter(prefix="/referrals/export", tags=["Exports"])


@router.get("/hmis-form1")
async def export_hmis_form1(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$", description="Year-month like 2026-08"),
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("officer", "admin")),
):
    """Download NPCBVI Form 1 as CSV for a given month."""
    # Parse year-month
    match = re.match(r"^(\d{4})-(\d{2})$", month)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM.")

    year = int(match.group(1))
    month_num = int(match.group(2))

    if month_num < 1 or month_num > 12:
        raise HTTPException(status_code=400, detail="Month must be between 01 and 12")

    district_id = auth.get("district_id")
    csv_content = await generate_hmis_form1(db, year, month_num, district_id)

    filename = f"NPCBVI_Form1_{month}_{district_id or 'ALL'}.csv"

    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
