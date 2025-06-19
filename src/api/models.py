from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class WellMetadata(BaseModel):
    """Metadata about a well."""

    name: str = Field(..., description="Name of the well")
    field: Optional[str] = Field(None, description="Field where the well is located")
    country: Optional[str] = Field(
        None, description="Country where the well is located"
    )
    operator: Optional[str] = Field(None, description="Operator of the well")
    timeZone: Optional[str] = Field(None, description="Time zone of the well location")


class WellInfo(BaseModel):
    """Information about a well."""

    uid: str = Field(..., description="Unique identifier for the well")
    metadata: WellMetadata = Field(..., description="Metadata about the well")


class WellboreMetadata(BaseModel):
    """Metadata about a wellbore."""

    name: str = Field(..., description="Name of the wellbore")
    number: Optional[str] = Field(None, description="Number of the wellbore")
    wellUid: str = Field(..., description="UID of the well this wellbore belongs to")


class WellboreInfo(BaseModel):
    """Information about a wellbore."""

    uid: str = Field(..., description="Unique identifier for the wellbore")
    metadata: WellboreMetadata = Field(..., description="Metadata about the wellbore")


class CurveInfo(BaseModel):
    """Information about a log curve."""

    mnemonic: str = Field(..., description="Mnemonic code for the curve")
    unit: Optional[str] = Field(None, description="Unit of measurement for the curve")
    description: Optional[str] = Field(None, description="Description of the curve")
    index: Optional[bool] = Field(
        None, description="Whether this curve is an index curve"
    )


class LogMetadata(BaseModel):
    """Metadata about a log."""

    name: str = Field(..., description="Name of the log")
    wellUid: str = Field(..., description="UID of the well this log belongs to")
    wellboreUid: str = Field(..., description="UID of the wellbore this log belongs to")
    indexType: Optional[str] = Field(
        None, description="Type of index (e.g., measured depth, time)"
    )
    startIndex: Optional[str] = Field(None, description="Start index value")
    endIndex: Optional[str] = Field(None, description="End index value")


class LogData(BaseModel):
    """Log data values."""

    values: List[List[str]] = Field(
        ..., description="List of data rows, each containing values for all curves"
    )


class LogInfo(BaseModel):
    """Information about a log."""

    uid: str = Field(..., description="Unique identifier for the log")
    metadata: LogMetadata = Field(..., description="Metadata about the log")
    curves: List[CurveInfo] = Field(
        ..., description="Information about curves in the log"
    )
    data: Optional[LogData] = Field(None, description="Log data values")


class MessageMetadata(BaseModel):
    """Metadata about a message."""

    wellUid: Optional[str] = Field(
        None, description="UID of the well this message belongs to"
    )
    wellboreUid: Optional[str] = Field(
        None, description="UID of the wellbore this message belongs to"
    )
    source: Optional[str] = Field(None, description="Source of the message")
    messageType: Optional[str] = Field(None, description="Type of message")


class MessageInfo(BaseModel):
    """Information about a message."""

    uid: str = Field(..., description="Unique identifier for the message")
    metadata: MessageMetadata = Field(..., description="Metadata about the message")
    text: str = Field(..., description="Message text content")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of the message")


class GeologicalInterval(BaseModel):
    """Information about a geological interval."""

    top: float = Field(..., description="Top depth of the interval")
    base: float = Field(..., description="Base depth of the interval")
    lithology: Optional[str] = Field(None, description="Lithology description")
    description: Optional[str] = Field(None, description="Detailed description")


class MudLogMetadata(BaseModel):
    """Metadata about a mud log."""

    name: str = Field(..., description="Name of the mud log")
    wellUid: str = Field(..., description="UID of the well this mud log belongs to")
    wellboreUid: str = Field(
        ..., description="UID of the wellbore this mud log belongs to"
    )


class MudLogInfo(BaseModel):
    """Information about a mud log."""

    uid: str = Field(..., description="Unique identifier for the mud log")
    metadata: MudLogMetadata = Field(..., description="Metadata about the mud log")
    intervals: List[GeologicalInterval] = Field(
        ..., description="Geological intervals in the mud log"
    )


# File metadata for test server
class FileMetadata(BaseModel):
    """Additional metadata for files in the test server."""

    path: str = Field(..., description="Path to the file")
    original_name: str = Field(..., description="Original name of the file")


# Test server models
class FileInfo(BaseModel):
    """Information about a file in the test server."""

    id: str = Field(..., description="Unique identifier for the file")
    name: str = Field(..., description="Name of the file")
    well_name: str = Field(..., description="Name of the well in the file")
    file_type: str = Field(
        ...,
        description="Type of the file (log, well, wellbore, messages, mudLog, unknown)",
    )
    size: int = Field(..., description="Size of the file in bytes")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    metadata: FileMetadata = Field(..., description="Additional metadata")


class FileList(BaseModel):
    """List of files in the test server."""

    files: List[FileInfo] = Field(..., description="List of file information")
    count: int = Field(..., description="Total number of files")


class DataHeader(BaseModel):
    """Header information for file content."""

    file_name: str = Field(..., description="Name of the file")
    error: Optional[str] = Field(None, description="Error message if processing failed")


class WitsmlMetadata(BaseModel):
    """Metadata extracted from WITSML data."""

    type: str = Field(..., description="Type of WITSML data")
    version: str = Field(..., description="WITSML version")
    wellName: Optional[str] = Field(None, description="Name of the well")
    wellUid: Optional[str] = Field(None, description="UID of the well")
    wellboreUid: Optional[str] = Field(None, description="UID of the wellbore")
    count: Optional[int] = Field(None, description="Count of items (for messages)")
    field: Optional[str] = Field(None, description="Field where the well is located")
    logName: Optional[str] = Field(None, description="Name of the log")
    indexType: Optional[str] = Field(None, description="Type of index for the log")


class WitsmlContentData(BaseModel):
    """Content of processed WITSML data."""

    wells: Optional[Dict[str, WellInfo]] = Field(
        None, description="Well data keyed by UID"
    )
    wellbores: Optional[Dict[str, WellboreInfo]] = Field(
        None, description="Wellbore data keyed by UID"
    )
    logs: Optional[Dict[str, LogInfo]] = Field(
        None, description="Log data keyed by UID"
    )
    messages: Optional[List[MessageInfo]] = Field(None, description="Message data")
    mudLogs: Optional[Dict[str, MudLogInfo]] = Field(
        None, description="Mud log data keyed by UID"
    )
    raw_content: Optional[str] = Field(
        None, description="Raw content if processing failed"
    )


class ProcessedData(BaseModel):
    """Processed WITSML data."""

    data_type: str = Field(..., description="Type of the WITSML data")
    metadata: WitsmlMetadata = Field(
        ..., description="Metadata extracted from the data"
    )
    content: WitsmlContentData = Field(..., description="Content of the processed data")
    processed_at: str = Field(..., description="Timestamp when the data was processed")


class FileContent(BaseModel):
    """Content of a file in the test server."""

    header: DataHeader = Field(..., description="Header information")
    data: ProcessedData = Field(..., description="Processed data")


class FileResponse(BaseModel):
    """Response with file information and content."""

    info: FileInfo = Field(..., description="File information")
    content: FileContent = Field(..., description="File content")


class HealthCheck(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Status of the server")
    data_dir: str = Field(..., description="Path to the data directory")
    files_loaded: int = Field(..., description="Number of files loaded")


class ReloadResponse(BaseModel):
    """Response after reloading files."""

    status: str = Field(..., description="Status of the reload operation")
    files_count: int = Field(..., description="Number of files loaded after reload")


# Main API models
class SearchQuery(BaseModel):
    """Search query parameters."""

    query: str = Field(..., description="Search query text")
    filters: Optional[Dict[str, str]] = Field(None, description="Optional filters")
    max_results: Optional[int] = Field(
        20, description="Maximum number of results to return"
    )


class SearchResult(BaseModel):
    """A single search result."""

    id: str = Field(..., description="Unique identifier for the result")
    score: float = Field(..., description="Relevance score")
    source: str = Field(..., description="Source of the result (file/document name)")
    content_type: str = Field(..., description="Type of content (log, message, etc.)")
    content: Dict[str, Any] = Field(..., description="Result content")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")


class SearchResponse(BaseModel):
    """Response for search queries."""

    results: List[SearchResult] = Field(..., description="List of search results")
    total: int = Field(..., description="Total number of matching results")
    query_time_ms: int = Field(..., description="Query execution time in milliseconds")


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    timestamp: str = Field(..., description="Timestamp of the error")


# Add models for streaming data
class StreamMetadata(BaseModel):
    """Metadata for a streaming session."""

    type: str = Field("metadata", description="Event type")
    file_name: str = Field(..., description="Name of the file being streamed")
    well_name: str = Field(..., description="Name of the well")
    timestamp: str = Field(..., description="Timestamp of the stream start")


class StreamSchema(BaseModel):
    """Schema definition for streamed log data."""

    type: str = Field("schema", description="Event type")
    log_uid: str = Field(..., description="UID of the log being streamed")
    curves: List[Dict[str, Any]] = Field(..., description="Curve definitions")


class StreamDataPoint(BaseModel):
    """A single data point in a stream."""

    type: str = Field("data", description="Event type")
    log_uid: str = Field(..., description="UID of the log")
    index: int = Field(..., description="Index of the data point in the sequence")
    timestamp: str = Field(..., description="Timestamp of the data point")
    values: List[str] = Field(..., description="Values for each curve")


class StreamEnd(BaseModel):
    """End of stream notification."""

    type: str = Field("end", description="Event type")
    message: str = Field(..., description="End message")


class StreamError(BaseModel):
    """Stream error notification."""

    type: str = Field("error", description="Event type")
    message: str = Field(..., description="Error message")
