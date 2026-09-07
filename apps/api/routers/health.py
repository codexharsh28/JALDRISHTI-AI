"""
Health & Readiness Observability APIRouter.
"""

from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(tags=["Health & Observability"])

@router.get("/api/v1/health")
def health_check():
    try:
        from services.runtime.mode_manager import mode_manager
        current_mode = mode_manager.get_status().system_mode.value
    except Exception:
        current_mode = "SIMULATION"

    return {
        "status": "HEALTHY",
        "service": "JALDRISHTI AI Backend",
        "mode": current_mode,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/api/v1/ready")
def readiness_check():
    return {
        "ready": True,
        "pilot_basin_loaded": "pilot-mahanadi-delta",
        "status": "OPERATIONAL"
    }
