"""
API client module for communicating with the backend service.

Handles upload URL requests, S3 uploads, and artifact registration.
"""

import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from schemas import (
    RequestToolUploadURLRequest,
    RequestUIModuleUploadURLRequest,
    SignedUploadURLResponse,
    RegisterToolArtifactRequest,
    RegisterUIModuleRequest,
    LoginRequest,
    LoginResponse
)


class ToolPublisherClient:
    """API client for tool publishing operations."""
    
    def __init__(
        self,
        base_url: str,
        session_id: Optional[str] = None,
        timeout: int = 300,
        retry_attempts: int = 3,
    ):
        """Initialize API client.
        
        Args:
            base_url: Base URL of the API (e.g., https://browsez-platform-backend-production.up.railway.app)
            session_id: Optional session ID for authentication
            timeout: Request timeout in seconds
            session_id: Optional session ID for authentication
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.base_url = base_url.rstrip('/')
        self.session_id = session_id
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.session = requests.Session()
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> requests.Response:
        """Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint path
            json_data: Optional JSON payload
            files: Optional files to upload
            retry: Whether to retry on failure
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: On request failure after retries
        """
        url = f"{self.base_url}{endpoint}"
        
        # Add session cookie if available
        headers = {}
        if self.session_id:
            headers['Cookie'] = f"session_id={self.session_id}"
            
        attempts = self.retry_attempts if retry else 1
        
        for attempt in range(attempts):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=json_data,
                    files=files,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code in (401, 403):
                    raise requests.RequestException("Session expired or invalid. Please login again.")
                    
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt < attempts - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    print(f"Request failed (attempt {attempt + 1}/{attempts}): {e}")
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise
        
        # Should never reach here, but for type safety
        raise requests.RequestException("Request failed after all retries")
    
    def login(self, email: str, password: str) -> LoginResponse:
        """Login to the platform.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            LoginResponse containing session_id and user info
        """
        request_data = LoginRequest(email=email, password=password)
        
        response = self._make_request(
            method='POST',
            endpoint='/api/auth/login',
            json_data=request_data.model_dump(),
            retry=False  # Don't retry login on failure
        )
        
        return LoginResponse(**response.json())
    
    def request_tool_upload_url(
        self,
        tenant_id: str,
        tool_name: str,
        content_hash: str
    ) -> SignedUploadURLResponse:
        """Request pre-signed upload URL for a tool.
        
        Args:
            tenant_id: Organization/tenant ID
            tool_name: Name of the tool
            content_hash: SHA-256 hash of the tool package
            
        Returns:
            SignedUploadURLResponse with upload URL and CDN URL
            
        Raises:
            requests.RequestException: On API error
        """
        request_data = RequestToolUploadURLRequest(
            tenant_id=tenant_id,
            tool_name=tool_name,
            content_hash=content_hash
        )
        
        response = self._make_request(
            method='POST',
            endpoint='/api/artifacts/tools/upload-url',
            json_data=request_data.model_dump()
        )
        
        response_json = response.json()
        if not response_json.get('success'):
            raise requests.RequestException(f"Failed to get upload URL: {response_json.get('error')}")
            
        return SignedUploadURLResponse(**response_json['data'])
    
    def request_ui_module_upload_url(
        self,
        tenant_id: str,
        module_name: str,
        content_hash: str
    ) -> SignedUploadURLResponse:
        """Request pre-signed upload URL for a UI module.
        
        Args:
            tenant_id: Organization/tenant ID
            module_name: Name of the UI module
            content_hash: SHA-256 hash of the module package
            
        Returns:
            SignedUploadURLResponse with upload URL and CDN URL
            
        Raises:
            requests.RequestException: On API error
        """
        request_data = RequestUIModuleUploadURLRequest(
            tenant_id=tenant_id,
            module_name=module_name,
            content_hash=content_hash
        )
        
        response = self._make_request(
            method='POST',
            endpoint='/api/artifacts/ui-modules/upload-url',
            json_data=request_data.model_dump()
        )
        
        response_json = response.json()
        if not response_json.get('success'):
            raise requests.RequestException(f"Failed to get upload URL: {response_json.get('error')}")
            
        return SignedUploadURLResponse(**response_json['data'])
    
    def upload_to_s3(
        self,
        upload_url: str,
        file_path: Path,
        show_progress: bool = True
    ) -> bool:
        """Upload file to S3 using pre-signed URL.
        
        Args:
            upload_url: Pre-signed S3 PUT URL
            file_path: Path to file to upload
            show_progress: Whether to show upload progress
            
        Returns:
            True if upload successful
            
        Raises:
            requests.RequestException: On upload failure
        """
        file_size = file_path.stat().st_size
        
        if show_progress:
            print(f"Uploading {file_path.name} ({file_size:,} bytes)...")
        
        with open(file_path, 'rb') as f:
            headers = {
                'Content-Type': 'application/zip'
            }
            
            response = requests.put(
                upload_url,
                data=f,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
        
        if show_progress:
            print(f"✓ Upload complete")
        
        return True
    
    def register_tool(
        self,
        request: RegisterToolArtifactRequest
    ) -> Dict[str, Any]:
        """Register a tool artifact with the backend.
        
        Args:
            request: Tool registration request
            
        Returns:
            Registration response from backend
            
        Raises:
            requests.RequestException: On API error
        """
        response = self._make_request(
            method='POST',
            endpoint='/api/artifacts/tools/register',
            json_data=request.model_dump()
        )
        
        return response.json()
    
    def register_ui_module(
        self,
        request: RegisterUIModuleRequest
    ) -> Dict[str, Any]:
        """Register a UI module artifact with the backend.
        
        Args:
            request: UI module registration request
            
        Returns:
            Registration response from backend
            
        Raises:
            requests.RequestException: On API error
        """
        response = self._make_request(
            method='POST',
            endpoint='/api/artifacts/ui-modules/register',
            json_data=request.model_dump()
        )
        
        return response.json()
