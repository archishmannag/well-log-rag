import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, List, Optional

from src.witsml.schemas import WitsmlSchemas

logger = logging.getLogger(__name__)


class WitsmlParser:
    """
    Parses WITSML XML responses into Python objects.
    """

    def __init__(self):
        """Initialize the WITSML parser."""
        self.schemas = WitsmlSchemas
        # Define XML namespaces commonly used in WITSML
        self.namespaces = {
            "witsml": "http://www.witsml.org/schemas/131",
            "": "http://www.witsml.org/schemas/131",  # Default namespace
        }

    def parse_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse WITSML XML content into a Python dictionary.

        Args:
            xml_content: The XML content as a string

        Returns:
            Dictionary containing parsed data with structure reflecting the XML
        """
        try:
            # Remove any XML declaration and encoding info that might cause parsing issues
            if xml_content.startswith("<?xml"):
                xml_content = xml_content.split("?>", 1)[1].strip()

            # Parse the XML
            root = ET.fromstring(xml_content)

            # Determine the root element type and call the appropriate handler
            root_tag = self._strip_namespace(root.tag)

            if root_tag == "messages":
                return self._parse_messages(root)
            elif root_tag == "wells":
                return self._parse_wells(root)
            elif root_tag == "wellbores":
                return self._parse_wellbores(root)
            elif root_tag == "logs":
                return self._parse_logs(root)
            elif root_tag == "mudLogs":
                return self._parse_mud_logs(root)
            else:
                # Generic parsing for other elements
                return self._element_to_dict(root)
        except Exception as e:
            logger.error(f"Error parsing WITSML XML: {e}")
            # Return a minimal dict with error information
            return {"error": str(e), "raw_content": xml_content[:200] + "..."}

    def _strip_namespace(self, tag: str) -> str:
        """Remove namespace from XML tag."""
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag

    def _element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """
        Convert an XML element and its children to a dictionary.

        Args:
            element: XML element to convert

        Returns:
            Dictionary representing the element
        """
        result = {}

        # Add attributes if present
        if element.attrib:
            result["attributes"] = dict(element.attrib)

        # Process child elements
        for child in element:
            child_tag = self._strip_namespace(child.tag)
            child_dict = self._element_to_dict(child)

            # If the tag already exists in the result, convert it to a list
            if child_tag in result:
                if not isinstance(result[child_tag], list):
                    result[child_tag] = [result[child_tag]]
                result[child_tag].append(child_dict)
            else:
                result[child_tag] = child_dict

        # If the element has text and no children, just return the text
        if element.text and element.text.strip() and not result:
            return element.text.strip()

        # If the element has text and children, add the text as a special key
        if element.text and element.text.strip() and result:
            result["_text"] = element.text.strip()

        return result

    def _parse_messages(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parse WITSML messages element.

        Args:
            root: XML root element for messages

        Returns:
            Dictionary containing parsed messages data
        """
        result = {"messages": []}

        for message_elem in root.findall(".//{*}message"):
            message = {
                "uid": message_elem.get("uid", ""),
                "uidWellbore": message_elem.get("uidWellbore", ""),
                "uidWell": message_elem.get("uidWell", ""),
                "content": self._element_to_dict(message_elem),
            }
            result["messages"].append(message)

        return result

    def _parse_wells(self, root: ET.Element) -> Dict[str, Any]:
        """Parse WITSML wells element."""
        result = {"well": {}}

        for well_elem in root.findall(".//{*}well"):
            well_data = self._element_to_dict(well_elem)
            well_uid = well_elem.get("uid", "unknown")
            result["well"][well_uid] = well_data

        return result

    def _parse_wellbores(self, root: ET.Element) -> Dict[str, Any]:
        """Parse WITSML wellbores element."""
        result = {"wellbore": {}}

        for wellbore_elem in root.findall(".//{*}wellbore"):
            wellbore_data = self._element_to_dict(wellbore_elem)
            wellbore_uid = wellbore_elem.get("uid", "unknown")
            result["wellbore"][wellbore_uid] = wellbore_data

        return result

    def _parse_logs(self, root: ET.Element) -> Dict[str, Any]:
        """Parse WITSML logs element."""
        result = {"log": {}}

        for log_elem in root.findall(".//{*}log"):
            log_data = self._element_to_dict(log_elem)
            log_uid = log_elem.get("uid", "unknown")

            # Special handling for log data
            result["log"][log_uid] = log_data

        return result

    def _parse_mud_logs(self, root: ET.Element) -> Dict[str, Any]:
        """Parse WITSML mudLogs element."""
        result = {"mudLog": {}}

        for mudlog_elem in root.findall(".//{*}mudLog"):
            mudlog_data = self._element_to_dict(mudlog_elem)
            mudlog_uid = mudlog_elem.get("uid", "unknown")
            result["mudLog"][mudlog_uid] = mudlog_data

        return result
