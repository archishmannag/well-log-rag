from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class WitsmlVersion(str, Enum):
    """Supported WITSML versions."""

    VERSION_1_3_1 = "1.3.1"
    VERSION_1_4_1 = "1.4.1"
    VERSION_2_0 = "2.0"


class Uid(BaseModel):
    """Base model for WITSML objects with UIDs."""

    uid: str = Field(default_factory=lambda: str(uuid.uuid4()))


class WellCoordinates(BaseModel):
    """Well location coordinates."""

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    easting: Optional[float] = None
    northing: Optional[float] = None
    projection: Optional[str] = None
    datum: Optional[str] = None


class WellReference(BaseModel):
    """Reference to a well."""

    uid: str
    name: Optional[str] = None


class WellboreReference(BaseModel):
    """Reference to a wellbore."""

    uid: str
    name: Optional[str] = None
    well_reference: Optional[WellReference] = None


class Well(Uid):
    """WITSML Well object."""

    name: str
    field: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    operator: Optional[str] = None
    api: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    time_zone: Optional[str] = None
    time_step: Optional[float] = None
    location: Optional[WellCoordinates] = None
    wellbores: Optional[List["Wellbore"]] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "uid": "w-001",
                "name": "Example Well",
                "field": "Test Field",
                "country": "US",
                "state": "TX",
                "operator": "Test Operator",
                "api": "API123456789",
                "description": "Test well description",
                "location": {"latitude": 29.7604, "longitude": -95.3698},
            }
        }


class Wellbore(Uid):
    """WITSML Wellbore object."""

    name: str
    number: Optional[str] = None
    suffix_api: Optional[str] = None
    well_uid: str
    well_name: Optional[str] = None
    md_current: Optional[float] = None
    tvd_current: Optional[float] = None
    md_kickoff: Optional[float] = None
    tvd_kickoff: Optional[float] = None
    md_planned: Optional[float] = None
    tvd_planned: Optional[float] = None
    md_subseaPlanned: Optional[float] = None
    tvd_subseaPlanned: Optional[float] = None
    day_work_start: Optional[datetime] = None
    day_work_end: Optional[datetime] = None
    spud_date: Optional[datetime] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    shape: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "uid": "wb-001",
                "name": "Example Wellbore",
                "number": "WB-1",
                "well_uid": "w-001",
                "well_name": "Example Well",
                "md_current": 10520.5,
                "tvd_current": 8372.4,
                "status": "active",
            }
        }


class LogCurveInfo(BaseModel):
    """WITSML Log Curve Info."""

    mnemonic: str
    unit: Optional[str] = None
    data_type: Optional[str] = None
    curve_description: Optional[str] = None
    index_type: Optional[str] = None
    min_index: Optional[Union[float, str]] = None
    max_index: Optional[Union[float, str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    null_value: Optional[str] = None


class LogIndexType(str, Enum):
    """Log index types."""

    MEASURED_DEPTH = "measured depth"
    TIME = "time"
    DATE_TIME = "date time"
    VERTICAL_DEPTH = "vertical depth"
    INDEX = "index"


class LogDirection(str, Enum):
    """Log direction types."""

    INCREASING = "increasing"
    DECREASING = "decreasing"


class LogData(BaseModel):
    """WITSML Log Data."""

    mnemonic_list: List[str]
    units_list: Optional[List[str]] = None
    data: List[List[Any]]


class Log(Uid):
    """WITSML Log object."""

    name: str
    wellbore_uid: str
    wellbore_name: Optional[str] = None
    well_uid: Optional[str] = None
    well_name: Optional[str] = None
    service_company: Optional[str] = None
    run_number: Optional[str] = None
    creation_date: Optional[datetime] = None
    description: Optional[str] = None
    index_type: Optional[LogIndexType] = None
    index_curve: Optional[str] = None
    start_index: Optional[Union[float, str, datetime]] = None
    end_index: Optional[Union[float, str, datetime]] = None
    direction: Optional[LogDirection] = None
    curve_info: Optional[List[LogCurveInfo]] = None
    log_data: Optional[LogData] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "uid": "l-001",
                "name": "Gamma Ray Log",
                "wellbore_uid": "wb-001",
                "wellbore_name": "Example Wellbore",
                "well_uid": "w-001",
                "well_name": "Example Well",
                "service_company": "Test Logging Company",
                "run_number": "1",
                "index_type": "measured depth",
                "index_curve": "DEPTH",
                "curve_info": [
                    {"mnemonic": "DEPTH", "unit": "ft", "data_type": "double"},
                    {"mnemonic": "GR", "unit": "gAPI", "data_type": "double"},
                ],
            }
        }


class WitsmlObject(BaseModel):
    """Base model for WITSML objects with metadata."""

    object_type: str
    version: WitsmlVersion
    data: Dict[str, Any]


class WitsmlQuery(BaseModel):
    """WITSML query parameters."""

    object_type: str
    version: WitsmlVersion = WitsmlVersion.VERSION_1_4_1
    id: Optional[str] = None
    uid: Optional[str] = None
    parent_uid: Optional[str] = None
    name: Optional[str] = None
    include_data: Optional[bool] = False
    include_metadata: Optional[bool] = True
    start_index: Optional[Union[float, str]] = None
    end_index: Optional[Union[float, str]] = None
    additional_params: Optional[Dict[str, Any]] = None


class ServerCapabilities(BaseModel):
    """WITSML server capabilities."""

    url: str
    version: str
    supported_objects: List[Dict[str, str]]
    raw_xml: Optional[str] = None


# Schema registry for mapping between XML and Python objects
WitsmlSchemas = {"well": Well, "wellbore": Wellbore, "log": Log}


# Define circular reference
Well.model_rebuild()
Wellbore.model_rebuild()
Log.model_rebuild()
Wellbore.model_rebuild()