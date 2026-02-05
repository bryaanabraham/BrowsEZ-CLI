"""
Tool upload orchestrator.

Coordinates validation, packaging, and publishing of tools.
"""

import sys
import yaml
from pathlib import Path
from typing import Optional

from .check_tool import validate_tool
from .packaging import package_tool
from .schemas import ToolMetadata, RiskLevel
from .api_client import ToolPublisherClient
from .config import ConfigManager


def run(directory: str, api_url: Optional[str] = None, risk_level: Optional[str] = None) -> None:
    """Validate, package, and upload a tool to the backend.
    
    Args:
        directory: Path to tool directory
        api_url: Optional API URL override
        risk_level: Optional risk level override
    """
    # Load configuration
    config_manager = ConfigManager()
    if api_url or risk_level:
        config_manager.update(api_url=api_url, risk_level=risk_level)
    config = config_manager.get()
    
    # Resolve directory path
    directory_path = Path(directory).resolve()
    
    print(f"\n{'='*60}")
    print(f"Publishing Tool: {directory_path.name}")
    print(f"{'='*60}\n")
    
    # Step 1: Validate tool structure
    print("Step 1/5: Validating tool structure...")
    errors = validate_tool(str(directory_path))
    if errors:
        print("[X] Validation failed:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("[OK] Tool structure valid\n")
    
    # Step 2: Parse tool.yaml metadata
    print("Step 2/5: Parsing tool metadata...")
    tool_yaml_path = directory_path / "tool.yaml"
    try:
        with open(tool_yaml_path, 'r', encoding='utf-8') as f:
            tool_yaml_data = yaml.safe_load(f)
        tool_metadata = ToolMetadata(**tool_yaml_data)
        print(f"[OK] Tool: {tool_metadata.name}")
        print(f"  Description: {tool_metadata.description[:80]}...\n")
    except Exception as e:
        print(f"[X] Failed to parse tool.yaml: {e}")
        sys.exit(1)
    
    # Step 3: Package tool
    print("Step 3/5: Creating package...")
    zip_path = None
    try:
        zip_path, content_hash = package_tool(directory_path)
        print(f"[OK] Package created: {zip_path.name}")
        print(f"  SHA-256: {content_hash}\n")
    except Exception as e:
        print(f"[X] Packaging failed: {e}")
        sys.exit(1)
    
    # Step 4: Upload to backend
    print("Step 4/5: Uploading to backend...")
    try:
        client = ToolPublisherClient(
            base_url=config.api_base_url,
            session_id=config.session_id,
            timeout=config.upload_timeout,
            retry_attempts=config.retry_attempts,
        )
        
        # Request upload URL
        print(f"  Requesting upload URL from {config.api_base_url}...")
        upload_response = client.request_tool_upload_url(
            tenant_id=config.tenant_id,
            tool_name=tool_metadata.name,
            content_hash=content_hash
        )
        print(f"[OK] Upload URL received (expires in {upload_response.expires_in_seconds}s)")
        # Upload to S3
        client.upload_to_s3(
            upload_response.upload_url,
            zip_path,
            required_headers=upload_response.required_headers,
        )
        
    except Exception as e:
        print(f"[X] Upload failed: {e}")
        if zip_path and zip_path.exists():
            print(f"  Package saved at: {zip_path}")
            print(f"  You can retry the upload manually")
        with open('debug_error.log', 'w') as f:
            f.write(str(e))
        sys.exit(1)
    
    # Step 5: Register tool
    print("\nStep 5/5: Registering tool...")
    try:
        register_request = tool_metadata.to_register_request(
            tenant_id=config.tenant_id,
            content_hash=content_hash,
            risk_level=config.get_risk_level()
        )
        
        response = client.register_tool(register_request)
        print("[OK] Tool registered successfully")
        print(f"  CDN URL: {upload_response.cdn_url}")
        
    except Exception as e:
        print(f"[X] Registration failed: {e}")
        print(f"  Package uploaded to S3: {upload_response.cdn_url}")
        print(f"  Local package: {zip_path}")
        sys.exit(1)
    
    # Cleanup
    if zip_path and zip_path.exists():
        zip_path.unlink()
    
    print(f"\n{'='*60}")
    print(f"[OK] Tool '{tool_metadata.name}' published successfully!")
    print(f"{'='*60}\n")
