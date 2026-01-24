# BrowsEZ Tool and UI Publishing

A modular, production-ready system for publishing tools and UI modules to a backend service.

## Features

- **Strict Schema Validation**: Ensures tools meet all requirements before packaging.
- **Deterministic Packaging**: Creates consistent zip files with content-based hashing (SHA-256).
- **Secure Uploads**: Uses pre-signed S3 URLs for artifacts.
- **Configurable**: Supports configuration via file, CLI arguments, and defaults.
- **Resilient**: Implements retry logic and exponential backoff for network operations.

## Architecture

The system is organized into the following modules:

1.  **`cli.py`**: The entry point for the command-line interface.
2.  **`upload_tool.py`**: Orchestrates the validation, packaging, and upload process.
3.  **`check_tool.py`**: Validates tool structure and metadata.
4.  **`packaging.py`**: Handles deterministic zipping and hashing.
5.  **`schemas.py`**: Defines Pydantic models for API contracts.
6.  **`api_client.py`**: Handles HTTP communication with the backend.
7.  **`config.py`**: Manages configuration loading.

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Publishing a Tool

To publish a tool using the default configuration (in `.toolrc.json`):

```bash
python cli.py publish-tool path/to/tool_directory
```

### Validating a Tool

To validate a tool without uploading:

```bash
python cli.py validate-tool path/to/tool_directory
```

### Configuration

The system uses a `.toolrc.json` file for configuration. It will be automatically created on the first run if it doesn't exist.

Default `.toolrc.json`:
```json
{
  "api_base_url": "https://browsez-platform-backend-production.up.railway.app",
  "tenant_id": "sample-tenant-123",
  "default_risk_level": "MEDIUM",
  "upload_timeout": 300,
  "retry_attempts": 3
}
```

You can also override settings via CLI arguments:

```bash
python cli.py publish-tool path/to/tool --api-url https://api.example.com --risk-level HIGH
```

## Directory Structure

A valid tool directory must look like this:

```
tool_name/
├── tool.yaml           # Metadata (name, inputs, outputs)
├── requirements.txt    # Python dependencies
└── src/
    ├── __init__.py
    └── main.py         # Entry point (run function, Input/Output classes)
```
