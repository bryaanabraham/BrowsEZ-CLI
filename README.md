# BrowsEZ CLI

A command-line tool for publishing tools and UI modules to the BrowsEZ platform.

## Installation

### From PyPI

```bash
pip install browsez-cli
```

### From Source (GitHub)

```bash
# Clone and install in editable mode
cd cli-mode
pip install -e .
```

## Quick Start

```bash
# Login to the platform
browsez login

# Validate a tool before publishing
browsez validate path/to/tool_directory

# Publish a tool
browsez publish path/to/tool_directory
```

## Commands

| Command | Description |
|---------|-------------|
| `browsez login` | Login to the BrowsEZ platform |
| `browsez logout` | Clear the current session |
| `browsez validate <dir>` | Validate a tool without uploading |
| `browsez publish <dir>` | Publish a tool to the backend |
| `browsez publish-ui <dir>` | Publish a UI module (coming soon) |
| `browsez config show` | Show current configuration |
| `browsez config set <key> <value>` | Set a config value |

## Configuration

The CLI uses a `.toolrc.json` file for configuration. It is auto-created on first run:

```json
{
  "api_base_url": "https://browsez-platform-backend-production.up.railway.app",
  "tenant_id": "sample-tenant-123",
  "default_risk_level": "MEDIUM",
  "upload_timeout": 300,
  "retry_attempts": 3
}
```

Override settings via CLI:

```bash
browsez config set api-url https://api.example.com
browsez config set risk-level HIGH
```

## Tool Directory Structure

A valid tool directory must have:

```
tool_name/
├── tool.yaml           # Metadata (name, inputs, outputs)
├── requirements.txt    # Python dependencies
└── src/
    ├── __init__.py
    └── main.py         # Entry point (run function, Input/Output classes)
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Build the package
python -m build

# Upload to PyPI (requires twine and credentials)
twine upload dist/*
```

## Features

- **Strict Schema Validation**: Ensures tools meet all requirements before packaging
- **Deterministic Packaging**: Creates consistent zip files with content-based hashing (SHA-256)
- **Secure Uploads**: Uses pre-signed S3 URLs for artifacts
- **Configurable**: Supports configuration via file, CLI arguments, and defaults
- **Resilient**: Implements retry logic and exponential backoff for network operations