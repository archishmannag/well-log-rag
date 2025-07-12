# Test Suite for Well Log RAG

This directory contains tests and a test server for the Well Log RAG application.

## Structure

- `conftest.py` - Pytest configuration and fixtures
- `test_server/` - FastAPI server implementation for testing
  - `app.py` - Test server that loads WITSML files from the data directory
- `test_processor.py` - Tests for the WITSML processor
- `test_api.py` - Tests for the API endpoints

## Running Tests

To run all tests:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/test_api.py
```

## Test Server

The test server provides a simplified API that mimics the production server but loads data from local WITSML files instead of connecting to a WITSML server or database.

To run the test server:

```bash
uvicorn tests.test_server.app:app --reload
```

Then access the API at `http://localhost:8000`.

## Adding Test Data

Place WITSML XML files in the `data/` directory at the root of the project. The test server will automatically load these files.
