import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from src.witsml.parser import WitsmlParser

logger = logging.getLogger(__name__)


class WitsmlProcessor:
    """
    Processor for WITSML data.
    Transforms parsed WITSML data into formats suitable for analysis and storage.
    """

    def __init__(self):
        """Initialize the WITSML processor."""
        self.parser = WitsmlParser()

    def process_file(self, content: str) -> Dict[str, Any]:
        """
        Process a WITSML file and extract relevant information.

        Args:
            content: Raw WITSML XML content as a string

        Returns:
            Dictionary containing processed data with metadata
        """
        # Parse the XML content
        parsed_data = self.parser.parse_xml(content)

        # Identify the type of WITSML data
        data_type = self._identify_data_type(parsed_data)

        # Process according to data type
        processed_data = {
            "data_type": data_type,
            "metadata": self._extract_metadata(parsed_data, data_type),
            "content": self._process_by_type(parsed_data, data_type),
            "processed_at": datetime.now().isoformat(),
        }

        return processed_data

    def _identify_data_type(self, parsed_data: Dict[str, Any]) -> str:
        """
        Identify the type of WITSML data.

        Args:
            parsed_data: Parsed WITSML data

        Returns:
            String indicating the data type
        """
        # Check for known WITSML object types
        if "messages" in parsed_data:
            return "messages"
        elif "well" in parsed_data:
            return "well"
        elif "wellbore" in parsed_data:
            return "wellbore"
        elif "log" in parsed_data:
            return "log"
        elif "mudLog" in parsed_data:
            return "mudLog"
        else:
            return "unknown"

    def _extract_metadata(
        self, parsed_data: Dict[str, Any], data_type: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from the parsed WITSML data.

        Args:
            parsed_data: Parsed WITSML data
            data_type: Type of WITSML data

        Returns:
            Dictionary containing metadata
        """
        metadata = {
            "type": data_type,
            "version": self._extract_version(parsed_data),
        }

        # Extract metadata specific to each data type
        if data_type == "messages":
            if "messages" in parsed_data and parsed_data["messages"]:
                metadata["count"] = len(parsed_data["messages"])
                if parsed_data["messages"][0].get("uidWell"):
                    metadata["wellUid"] = parsed_data["messages"][0].get("uidWell")
                if parsed_data["messages"][0].get("uidWellbore"):
                    metadata["wellboreUid"] = parsed_data["messages"][0].get(
                        "uidWellbore"
                    )

        elif data_type == "well":
            # Extract well metadata
            if "well" in parsed_data and parsed_data["well"]:
                first_well = next(iter(parsed_data["well"].values()))
                if "name" in first_well:
                    metadata["wellName"] = first_well["name"]
                if "field" in first_well:
                    metadata["field"] = first_well["field"]

        elif data_type == "log":
            # Extract log metadata
            if "log" in parsed_data and parsed_data["log"]:
                first_log = next(iter(parsed_data["log"].values()))
                if "name" in first_log:
                    metadata["logName"] = first_log["name"]
                if "indexType" in first_log:
                    metadata["indexType"] = first_log["indexType"]

        return metadata

    def _extract_version(self, parsed_data: Dict[str, Any]) -> str:
        """
        Extract WITSML version from the parsed data.

        Args:
            parsed_data: Parsed WITSML data

        Returns:
            WITSML version string or 'unknown'
        """
        # Try to extract version from attributes
        for key, value in parsed_data.items():
            if isinstance(value, dict) and "attributes" in value:
                if "version" in value["attributes"]:
                    return value["attributes"]["version"]

        return "unknown"

    def _process_by_type(
        self, parsed_data: Dict[str, Any], data_type: str
    ) -> Dict[str, Any]:
        """
        Process the parsed data according to its type.

        Args:
            parsed_data: Parsed WITSML data
            data_type: Type of WITSML data

        Returns:
            Processed data specific to the type
        """
        if data_type == "messages":
            return self._process_messages(parsed_data)
        elif data_type == "well":
            return self._process_wells(parsed_data)
        elif data_type == "wellbore":
            return self._process_wellbores(parsed_data)
        elif data_type == "log":
            return self._process_logs(parsed_data)
        elif data_type == "mudLog":
            return self._process_mud_logs(parsed_data)
        else:
            # Return the parsed data as is for unknown types
            return parsed_data

    def _process_messages(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process WITSML messages data.

        Args:
            parsed_data: Parsed messages data

        Returns:
            Processed messages data
        """
        processed_messages = []

        if "messages" in parsed_data:
            for message in parsed_data["messages"]:
                processed_message = {
                    "uid": message.get("uid", ""),
                    "wellUid": message.get("uidWell", ""),
                    "wellboreUid": message.get("uidWellbore", ""),
                }

                # Add any additional content from the message
                if "content" in message and isinstance(message["content"], dict):
                    for key, value in message["content"].items():
                        if key not in ["attributes"]:
                            processed_message[key] = value

                processed_messages.append(processed_message)

        return {"messages": processed_messages}

    def _process_wells(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process WITSML well data.

        Args:
            parsed_data: Parsed well data

        Returns:
            Processed well data
        """
        processed_wells = {}

        if "well" in parsed_data:
            for uid, well_data in parsed_data["well"].items():
                processed_well = {"uid": uid}

                # Extract common well properties
                for key in [
                    "name",
                    "field",
                    "country",
                    "operator",
                    "numLicense",
                    "timeZone",
                ]:
                    if key in well_data:
                        processed_well[key] = well_data[key]

                processed_wells[uid] = processed_well

        return {"wells": processed_wells}

    def _process_wellbores(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process WITSML wellbore data."""
        processed_wellbores = {}

        if "wellbore" in parsed_data:
            for uid, wellbore_data in parsed_data["wellbore"].items():
                processed_wellbore = {"uid": uid}

                # Extract common wellbore properties
                for key in ["name", "number", "suffixAPI", "numGovt", "wellUid"]:
                    if key in wellbore_data:
                        processed_wellbore[key] = wellbore_data[key]

                processed_wellbores[uid] = processed_wellbore

        return {"wellbores": processed_wellbores}

    def _process_logs(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process WITSML log data."""
        processed_logs = {}

        if "log" in parsed_data:
            for uid, log_data in parsed_data["log"].items():
                processed_log = {"uid": uid}

                # Extract common log properties
                for key in ["name", "indexType", "startIndex", "endIndex"]:
                    if key in log_data:
                        processed_log[key] = log_data[key]

                # Process log curves if present
                if "logCurveInfo" in log_data:
                    processed_log["curves"] = []
                    if isinstance(log_data["logCurveInfo"], list):
                        for curve in log_data["logCurveInfo"]:
                            if isinstance(curve, dict):
                                curve_info = {"mnemonic": curve.get("mnemonic", "")}
                                if "unit" in curve:
                                    curve_info["unit"] = curve["unit"]
                                processed_log["curves"].append(curve_info)
                    elif isinstance(log_data["logCurveInfo"], dict):
                        curve = log_data["logCurveInfo"]
                        curve_info = {"mnemonic": curve.get("mnemonic", "")}
                        if "unit" in curve:
                            curve_info["unit"] = curve["unit"]
                        processed_log["curves"].append(curve_info)

                # Process log data if present
                if "logData" in log_data:
                    processed_log["data"] = self._process_log_data(log_data["logData"])

                processed_logs[uid] = processed_log

        return {"logs": processed_logs}

    def _process_log_data(self, log_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process WITSML log data values."""
        processed_data = []

        # Extract and process log data rows
        if "data" in log_data and isinstance(log_data["data"], list):
            for row in log_data["data"]:
                if isinstance(row, str):
                    # Split comma-separated values
                    values = row.split(",")
                    processed_data.append(values)

        return processed_data

    def _process_mud_logs(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process WITSML mudLog data."""
        processed_mud_logs = {}

        if "mudLog" in parsed_data:
            for uid, mud_log_data in parsed_data["mudLog"].items():
                processed_mud_log = {"uid": uid}

                # Extract common mudLog properties
                for key in ["name", "wellUid", "wellboreUid"]:
                    if key in mud_log_data:
                        processed_mud_log[key] = mud_log_data[key]

                # Process geological interval data if present
                if "geologicalIntervalSet" in mud_log_data:
                    processed_mud_log["intervals"] = self._process_geological_intervals(
                        mud_log_data["geologicalIntervalSet"]
                    )

                processed_mud_logs[uid] = processed_mud_log

        return {"mudLogs": processed_mud_logs}

    def _process_geological_intervals(
        self, interval_set: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process geological intervals from mudLog data."""
        intervals = []

        if "geologicalInterval" in interval_set:
            interval_data = interval_set["geologicalInterval"]

            # Handle both single interval and list of intervals
            if isinstance(interval_data, list):
                for interval in interval_data:
                    processed_interval = self._extract_interval_data(interval)
                    intervals.append(processed_interval)
            elif isinstance(interval_data, dict):
                processed_interval = self._extract_interval_data(interval_data)
                intervals.append(processed_interval)

        return intervals

    def _extract_interval_data(self, interval: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from a geological interval."""
        processed_interval = {}

        # Extract common interval properties
        for key in ["mdTop", "mdBottom", "lithology", "description"]:
            if key in interval:
                processed_interval[key] = interval[key]

        return processed_interval
