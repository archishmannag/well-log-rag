from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional, Dict, Any

from src.api.services.witsml_service import WitsmlService
from src.api.schemas.witsml import FileListResponse, FileResponse

router = APIRouter()


def get_witsml_service():
    """Dependency to get the WITSML service."""
    return WitsmlService()


@router.get("/status", response_model=Dict[str, Any])
async def get_server_status(
    witsml_service: WitsmlService = Depends(get_witsml_service),
):
    """
    Get the status of the WITSML server connection.
    """
    try:
        connected = witsml_service.check_connection()
        return {
            "status": "connected" if connected else "disconnected",
            "server_url": witsml_service.get_server_info().get("url", "Unknown"),
        }
    except Exception as e:
        error_message = str(e)
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to check WITSML server status",
                "error": error_message,
                "error_type": type(e).__name__,
            },
        )


@router.get("/info", response_model=Dict[str, Any])
async def get_server_info(witsml_service: WitsmlService = Depends(get_witsml_service)):
    """
    Get detailed information about the WITSML server.
    """
    try:
        return witsml_service.get_server_info()
    except Exception as e:
        error_message = str(e)
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve WITSML server information",
                "error": error_message,
                "error_type": type(e).__name__,
            },
        )


@router.get("/wells", response_model=List[Dict[str, Any]])
async def get_wells(witsml_service: WitsmlService = Depends(get_witsml_service)):
    """
    Get all wells from the WITSML server.
    """
    try:
        return witsml_service.get_wells()
    except Exception as e:
        error_message = str(e)
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve wells from WITSML server",
                "error": error_message,
                "error_type": type(e).__name__,
            },
        )


@router.get("/wells/{well_uid}/wellbores", response_model=List[Dict[str, Any]])
async def get_wellbores(
    well_uid: str = Path(..., description="Unique identifier for the well"),
    witsml_service: WitsmlService = Depends(get_witsml_service),
):
    """
    Get wellbores for a specific well.
    """
    try:
        return witsml_service.get_wellbores(well_uid)
    except Exception as e:
        error_message = str(e)
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Failed to retrieve wellbores for well {well_uid}",
                "error": error_message,
                "error_type": type(e).__name__,
            },
        )


@router.get(
    "/wells/{well_uid}/wellbores/{wellbore_uid}/logs",
    response_model=List[Dict[str, Any]],
)
async def get_logs(
    well_uid: str = Path(..., description="Unique identifier for the well"),
    wellbore_uid: str = Path(..., description="Unique identifier for the wellbore"),
    witsml_service: WitsmlService = Depends(get_witsml_service),
):
    """
    Get logs for a specific wellbore.
    """
    try:
        return witsml_service.get_logs(well_uid, wellbore_uid)
    except Exception as e:
        error_message = str(e)
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Failed to retrieve logs for wellbore {wellbore_uid}",
                "error": error_message,
                "error_type": type(e).__name__,
            },
        )


@router.get(
    "/wells/{well_uid}/wellbores/{wellbore_uid}/logs/{log_uid}/data",
    response_model=Dict[str, Any],
)
async def get_log_data(
    well_uid: str = Path(..., description="Unique identifier for the well"),
    wellbore_uid: str = Path(..., description="Unique identifier for the wellbore"),
    log_uid: str = Path(..., description="Unique identifier for the log"),
    start_index: Optional[str] = Query(None, description="Start index for log data"),
    end_index: Optional[str] = Query(None, description="End index for log data"),
    witsml_service: WitsmlService = Depends(get_witsml_service),
):
    """
    Get log data for a specific log.
    """
    try:
        return witsml_service.get_log_data(
            well_uid, wellbore_uid, log_uid, start_index, end_index
        )
    except Exception as e:
        error_message = str(e)
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Failed to retrieve log data for log {log_uid}",
                "error": error_message,
                "error_type": type(e).__name__,
                "context": {
                    "well_uid": well_uid,
                    "wellbore_uid": wellbore_uid,
                    "log_uid": log_uid,
                    "start_index": start_index,
                    "end_index": end_index,
                },
            },
        )


@router.post("/clear-cache", status_code=204)
async def clear_cache(witsml_service: WitsmlService = Depends(get_witsml_service)):
    """
    Clear the WITSML client cache.
    """
    try:
        witsml_service.clear_cache()
    except Exception as e:
        error_message = str(e)
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to clear WITSML cache",
                "error": error_message,
                "error_type": type(e).__name__,
            },
        )
