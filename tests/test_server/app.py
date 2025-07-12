from fastapi import FastAPI, HTTPException, Depends, Query, Path, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import os
import glob
from pathlib import Path
import uuid
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import asyncio
import json
import time

# Import the processor and parser from the main application
from src.witsml.processor import WitsmlProcessor
from src.witsml.parser import WitsmlParser

# Import the response models
from src.api.models import (
    FileInfo,
    FileList,
    FileResponse,
    HealthCheck,
    ReloadResponse,
    ErrorResponse,
    WellMetadata,
    WellInfo,
    LogMetadata,
    LogInfo,
    LogData,
    CurveInfo,
    MessageInfo,
    MessageMetadata,
    MudLogInfo,
    MudLogMetadata,
    GeologicalInterval,
    WitsmlMetadata,
    WitsmlContentData,
    ProcessedData,
    DataHeader,
    FileContent,
    FileMetadata,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory containing sample WITSML files
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Initialize processor and parser
processor = WitsmlProcessor()
parser = WitsmlParser()

# In-memory database for test data
files_db = {}
file_contents_db = {}


# Load test data into memory on startup
# @app.on_event("startup")
@asynccontextmanager
async def startup_event(app: FastAPI):
    # Scan data directory for WITSML files
    witsml_files = glob.glob(str(DATA_DIR / "*.xml"))
    logger.info(f"Found {len(witsml_files)} WITSML files in {DATA_DIR}")

    for file_path in witsml_files:
        file_id = str(uuid.uuid4())
        file_name = os.path.basename(file_path)
        logger.info(f"Processing file: {file_name}")

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Add debug logs to check file content
        logger.info(f"File analysis for {file_name}:")
        logger.info(f"  - File size: {len(content)} bytes")

        # More thorough content analysis
        data_tags = re.findall(r"<(?:\w+:)?data>", content)
        data_sections = re.findall(r"<(?:\w+:)?data>[\s\S]*?</(?:\w+:)?data>", content)

        logger.info(f"  - Data tags found: {len(data_tags)}")
        logger.info(f"  - Data sections found: {len(data_sections)}")

        if data_sections:
            # Analyze the first data section
            first_data = data_sections[0]
            lines = [line for line in first_data.split("\n") if line.strip()]
            logger.info(f"  - First data section has approximately {len(lines)} lines")
        trimmed_content = content

        # Try to parse to determine well name and file type
        try:
            parsed_data = parser.parse_xml(trimmed_content)

            # Verify that parsing preserved data
            if "log" in parsed_data:
                for log_uid, log_data in parsed_data["log"].items():
                    if "logData" in log_data and not log_data.get("logData", {}).get(
                        "data"
                    ):
                        logger.error(
                            f"Parsed log has no data! Reverting to original for {file_name}"
                        )
                        trimmed_content = content
                        parsed_data = parser.parse_xml(content)
                        break

            if "well" in parsed_data and "name" in parsed_data["well"]:
                well_name = parsed_data["well"]["name"]
            else:
                well_name = f"Unknown Well ({file_name})"

            if "log" in parsed_data:
                file_type = "log"
            elif "well" in parsed_data:
                file_type = "well"
            elif "wellbore" in parsed_data:
                file_type = "wellbore"
            elif "messages" in parsed_data:
                file_type = "messages"
            elif "mudLog" in parsed_data:
                file_type = "mudLog"
            else:
                file_type = "unknown"

        except Exception as e:
            logger.error(f"Error parsing file {file_name}: {str(e)}")
            well_name = f"Unknown Well ({file_name})"
            file_type = "unknown"

        # Store file metadata
        files_db[file_id] = {
            "id": file_id,
            "name": file_name,
            "well_name": well_name,
            "file_type": file_type,
            "size": len(trimmed_content),
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "metadata": {"path": file_path, "original_name": file_name},
        }

        # Process file content
        try:
            processed_data = processor.process_file(trimmed_content)

            file_contents_db[file_id] = {
                "header": {"file_name": file_name},
                "data": processed_data,
            }
            logger.info(f"Successfully processed file: {file_name}")
        except Exception as e:
            logger.error(f"Error processing file {file_name}: {str(e)}")
            # Store raw content if processing fails
            file_contents_db[file_id] = {
                "header": {"file_name": file_name, "error": str(e)},
                "data": {
                    "raw_content": trimmed_content[:1000] + "..."
                    if len(trimmed_content) > 1000
                    else trimmed_content
                },
            }

    logger.info(f"Loaded {len(files_db)} WITSML files from {DATA_DIR}")
    yield


# Create FastAPI app
app = FastAPI(
    title="WITSML Test Server",
    description="Test server for WITSML processing using local files",
    version="0.1.0",
    lifespan=startup_event,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthCheck)
async def root():
    """Health check endpoint."""
    return HealthCheck(status="ok", data_dir=str(DATA_DIR), files_loaded=len(files_db))


@app.get("/files", response_model=FileList)
async def list_files(
    well_name: Optional[str] = Query(None, description="Filter by well name"),
    file_type: Optional[str] = Query(
        None, description="Filter by file type (log, well, wellbore, messages, mudLog)"
    ),
):
    """List all available WITSML files with optional filtering."""
    results = []

    for file_id, file_data in files_db.items():
        # Apply filters
        if well_name and file_data["well_name"] != well_name:
            continue

        if file_type and file_data["file_type"] != file_type:
            continue

        results.append(file_data)

    return FileList(files=results, count=len(results))


@app.get("/files/{file_id}", response_model=FileResponse)
async def get_file(file_id: str):
    """Get a specific file by ID."""
    if file_id not in files_db:
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")

    if file_id not in file_contents_db:
        raise HTTPException(
            status_code=404, detail=f"Content for file {file_id} not found"
        )

    # Get the raw data
    raw_file_info = files_db[file_id]
    raw_content = file_contents_db[file_id]

    # Transform the data to match our Pydantic models
    file_info = FileInfo(
        id=raw_file_info["id"],
        name=raw_file_info["name"],
        well_name=raw_file_info["well_name"],
        file_type=raw_file_info["file_type"],
        size=raw_file_info["size"],
        created_at=raw_file_info["created_at"],
        updated_at=raw_file_info["updated_at"],
        metadata=FileMetadata(
            path=raw_file_info["metadata"]["path"],
            original_name=raw_file_info["metadata"]["original_name"],
        ),
    )

    # Create the header
    header = DataHeader(
        file_name=raw_content["header"]["file_name"],
        error=raw_content["header"].get("error"),
    )

    # Process the data content
    raw_data = raw_content["data"]

    # Create the WitsmlMetadata
    witsml_metadata = WitsmlMetadata(
        type=raw_data["data_type"],
        version=raw_data["metadata"].get("version", "unknown"),
        wellName=raw_data["metadata"].get("wellName"),
        wellUid=raw_data["metadata"].get("wellUid"),
        wellboreUid=raw_data["metadata"].get("wellboreUid"),
        count=raw_data["metadata"].get("count"),
        field=raw_data["metadata"].get("field"),
        logName=raw_data["metadata"].get("logName"),
        indexType=raw_data["metadata"].get("indexType"),
    )

    # Process content based on type
    processed_content = {}

    # For log data, we need to transform the structure
    if raw_data["data_type"] == "log" and "logs" in raw_data["content"]:
        logs_dict = {}
        for log_uid, log_data in raw_data["content"]["logs"].items():
            # Create curves
            curves = []
            if "curves" in log_data:
                for curve in log_data.get("curves", []):
                    curves.append(
                        CurveInfo(
                            mnemonic=curve.get("mnemonic", ""),
                            unit=curve.get("unit"),
                            description=None,
                            index=None,
                        )
                    )

            # Create log metadata
            log_metadata = LogMetadata(
                name=log_data.get("name", "Unnamed Log"),
                wellUid=log_data.get("wellUid", "unknown"),
                wellboreUid=log_data.get("wellboreUid", "unknown"),
                indexType=log_data.get("indexType"),
                startIndex=log_data.get("startIndex"),
                endIndex=log_data.get("endIndex"),
            )

            # Create log data if available
            log_data_obj = None
            if "data" in log_data and log_data["data"]:
                # Convert the raw data to the expected format
                # Assuming data is a list of string arrays
                log_data_obj = LogData(values=log_data["data"])

            # Create the complete log info
            logs_dict[log_uid] = LogInfo(
                uid=log_uid,
                metadata=log_metadata,
                curves=curves,
                data=log_data_obj,
            )

        processed_content["logs"] = logs_dict

    # Similar transformations for other data types
    elif raw_data["data_type"] == "well" and "wells" in raw_data["content"]:
        wells_dict = {}
        for well_uid, well_data in raw_data["content"]["wells"].items():
            well_metadata = WellMetadata(
                name=well_data.get("name", "Unnamed Well"),
                field=well_data.get("field"),
                country=well_data.get("country"),
                operator=well_data.get("operator"),
                timeZone=well_data.get("timeZone"),
            )

            wells_dict[well_uid] = WellInfo(
                uid=well_uid,
                metadata=well_metadata,
            )

        processed_content["wells"] = wells_dict

    # Handle messages
    elif raw_data["data_type"] == "messages" and "messages" in raw_data["content"]:
        messages_list = []
        for msg_data in raw_data["content"]["messages"]:
            msg_metadata = MessageMetadata(
                wellUid=msg_data.get("wellUid"),
                wellboreUid=msg_data.get("wellboreUid"),
                source=msg_data.get("source"),
                messageType=msg_data.get("messageType"),
            )

            message = MessageInfo(
                uid=msg_data.get("uid", "unknown"),
                metadata=msg_metadata,
                text=msg_data.get("text", ""),
                timestamp=None,  # Would parse timestamp if available
            )

            messages_list.append(message)

        processed_content["messages"] = messages_list

    # For raw content (e.g., in case of errors)
    if "raw_content" in raw_data["content"]:
        processed_content["raw_content"] = raw_data["content"]["raw_content"]

    # Create the WitsmlContentData
    witsml_content = WitsmlContentData(**processed_content)

    # Create the processed data
    processed_data = ProcessedData(
        data_type=raw_data["data_type"],
        metadata=witsml_metadata,
        content=witsml_content,
        processed_at=raw_data["processed_at"],
    )

    # Create the file content
    file_content = FileContent(
        header=header,
        data=processed_data,
    )

    # Return the complete response
    return FileResponse(
        info=file_info,
        content=file_content,
    )


# Add a new endpoint for streaming log data via SSE
@app.get("/files/{file_id}/stream", description="Stream log data via SSE")
async def stream_log_data(
    file_id: str,
    request: Request,
    delay: int = Query(10000, description="Delay between data points in milliseconds"),
):
    """
    Stream log data as Server-Sent Events (SSE) with a configurable delay.
    This emulates real-time data coming from machines.

    Args:
        file_id: The ID of the file to stream
        delay: Delay between data points in milliseconds (default: 10000ms)

    Returns:
        StreamingResponse: Server-sent events stream
    """
    if file_id not in files_db:
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")

    if file_id not in file_contents_db:
        raise HTTPException(
            status_code=404, detail=f"Content for file {file_id} not found"
        )

    # Get file information
    file_info = files_db[file_id]
    file_content = file_contents_db[file_id]

    # Check if it's a log file
    if file_info["file_type"] != "log":
        raise HTTPException(status_code=400, detail="Only log files can be streamed")

    # Create an async generator function to stream the data
    async def event_generator():
        # Send the file metadata as the first event
        metadata = {
            "file_name": file_info["name"],
            "well_name": file_info["well_name"],
            "timestamp": datetime.now().isoformat(),
        }
        yield f"event: metadata\ndata: {json.dumps(metadata)}\n\n"

        # Get the log data from the processed content
        data = file_content["data"]
        log_content = data.get("content", {}).get("logs", {})

        if not log_content:
            error_data = {
                "type": "error",
                "message": "No log data available for streaming",
            }
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
            return

        # Get the first log (assuming there might be multiple logs in the file)
        log_uid, log_info = next(iter(log_content.items()))

        # Get the curve info to send as schema
        curves = log_info.get("curves", [])
        schema = {"log_uid": log_uid, "curves": curves}
        yield f"event: schema\ndata: {json.dumps(schema)}\n\n"

        # Get the actual data rows
        data_rows = log_info.get("data", [])

        # Stream each data row with a delay
        for i, row in enumerate(data_rows):
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("Client disconnected, stopping stream")
                break

            # Prepare the data point
            data_point = {
                "log_uid": log_uid,
                "index": i,
                "timestamp": (datetime.now() + timedelta(seconds=i * 0.5)).isoformat(),
                "values": row,
            }

            # Send the data point
            yield f"event: data\ndata: {json.dumps(data_point)}\n\n"

            # Wait for the specified delay
            await asyncio.sleep(delay / 1000.0)  # Convert ms to seconds

        # Send end event
        end_data = {"type": "end", "message": "Stream complete"}
        yield f"event: end\ndata: {json.dumps(end_data)}\n\n"

    # Return a streaming response with the appropriate media type for SSE
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


# Add a custom exception handler for better error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        {
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat(),
        },
        exc.status_code,
    )
