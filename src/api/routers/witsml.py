from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from src.api.schemas.witsml import FileListResponse, FileResponse, FileQuery
from src.api.services.file_service import FileService

router = APIRouter()


@router.get("/files", response_model=FileListResponse)
async def list_files(
    well_name: Optional[str] = Query(None, description="Filter by well name"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    file_service: FileService = Depends(),
):
    """
    List all available WITSML files with optional filtering.
    """
    try:
        files = file_service.list_files(well_name=well_name, file_type=file_type)
        return FileListResponse(files=files, count=len(files))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve files: {str(e)}"
        )


@router.get("/files/{file_id}", response_model=FileResponse)
async def get_file(file_id: str, file_service: FileService = Depends()):
    """
    Retrieve a specific WITSML file by ID.
    """
    try:
        file_data = file_service.get_file(file_id)
        if not file_data:
            raise HTTPException(
                status_code=404, detail=f"File with ID {file_id} not found"
            )
        return file_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve file: {str(e)}"
        )


@router.post("/query", response_model=FileListResponse)
async def query_files(query: FileQuery, file_service: FileService = Depends()):
    """
    Query WITSML files based on advanced criteria.
    """
    try:
        files = file_service.query_files(query.dict())
        return FileListResponse(files=files, count=len(files))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query files: {str(e)}")
