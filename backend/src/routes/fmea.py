"""
API routes for FMEA report generation.

This module defines the REST API endpoint for generating and downloading
FMEA XLSX reports from the Mind Graph data.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4**
"""

import io
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from ..services.fmea_report_service import FMEAReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/fmea", tags=["FMEA"])

fmea_service = FMEAReportService()

XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


@router.get("/report/{fmea_type}")
async def generate_fmea_report(fmea_type: str) -> StreamingResponse:
    """Generate and download an FMEA XLSX report.

    Args:
        fmea_type: One of "design", "process", "iso14971", "general".

    Returns:
        StreamingResponse containing the XLSX file bytes.
    """
    try:
        xlsx_bytes = fmea_service.generate_report(fmea_type)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    except RuntimeError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
    except FileNotFoundError as exc:
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    filename = f"fmea_report_{fmea_type}.xlsx"
    return StreamingResponse(
        content=io.BytesIO(xlsx_bytes),
        media_type=XLSX_CONTENT_TYPE,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
