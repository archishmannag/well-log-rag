import pytest
import os
from pathlib import Path

from src.witsml.processor import WitsmlProcessor
from src.witsml.parser import WitsmlParser


def test_processor_initialization():
    """Test that the processor initializes correctly."""
    processor = WitsmlProcessor()
    assert processor is not None
    assert hasattr(processor, "parser")


def test_process_file(witsml_files):
    """Test processing a WITSML file."""
    if not witsml_files:
        pytest.skip("No WITSML files found in data directory")

    # Take the first file for testing
    file_path = witsml_files[0]

    # Read file
    with open(file_path, "r") as f:
        file_content = f.read()

    # Process file
    processor = WitsmlProcessor()
    result = processor.process_file(file_content)

    # Basic validation
    assert result is not None
    assert isinstance(result, dict)
    assert "metadata" in result


def test_parser(witsml_files):
    """Test the WITSML parser."""
    if not witsml_files:
        pytest.skip("No WITSML files found in data directory")

    # Take the first file for testing
    file_path = witsml_files[0]

    # Read file
    with open(file_path, "r") as f:
        file_content = f.read()

    # Parse XML
    parser = WitsmlParser()
    result = parser.parse_xml(file_content)

    # Basic validation
    assert result is not None
    assert isinstance(result, dict)
