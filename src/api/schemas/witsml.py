from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class FileInfo(BaseModel):
    """Basic information about a WITSML file."""

    file_id: str = Field(..., description="Unique identifier for the file")
    well_name: str = Field(..., description="Name of the well")
    file_type: str = Field(
        ..., description="Type of WITSML file (log, trajectory, etc.)"
    )
    file_size: int = Field(..., description="Size of the file in bytes")
    created_at: datetime = Field(..., description="File creation timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class FileListResponse(BaseModel):
    """Response model for file listing endpoints."""

    files: List[FileInfo] = Field(default_factory=list, description="List of files")
    count: int = Field(..., description="Total number of files returned")


class FileContent(BaseModel):
    """Detailed content of a WITSML file."""

    header: Dict[str, Any] = Field(..., description="File header information")
    data: Dict[str, Any] = Field(..., description="Parsed file data")


class FileResponse(BaseModel):
    """Response model for file retrieval endpoints."""

    info: FileInfo = Field(..., description="File information")
    content: FileContent = Field(..., description="File content")


class FileQuery(BaseModel):
    """Query parameters for advanced file searching."""

    well_names: Optional[List[str]] = Field(
        None, description="List of well names to include"
    )
    file_types: Optional[List[str]] = Field(
        None, description="List of file types to include"
    )
    date_range: Optional[Dict[str, datetime]] = Field(
        None, description="Date range for file creation"
    )
    metadata_filters: Optional[Dict[str, Any]] = Field(
        None, description="Filters to apply to metadata"
    )
