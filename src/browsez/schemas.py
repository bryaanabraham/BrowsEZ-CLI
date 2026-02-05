"""
Schema validation module for tool publishing system.

Defines Pydantic models for API requests/responses and tool metadata validation.
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    """Risk level classification for tools."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RequestToolUploadURLRequest(BaseModel):
    """Request schema for tool upload URL."""
    tenant_id: str = Field(..., description="Organization/tenant ID")
    tool_name: str = Field(..., min_length=1, max_length=100)
    content_hash: str = Field(..., description="SHA-256 hash of artifact content")


class RequestUIModuleUploadURLRequest(BaseModel):
    """Request schema for UI module upload URL."""
    tenant_id: str = Field(..., description="Organization/tenant ID")
    module_name: str = Field(..., min_length=1, max_length=100)
    content_hash: str = Field(..., description="SHA-256 hash of module content")


class SignedUploadURLResponse(BaseModel):
    """Response schema for pre-signed upload URLs."""
    upload_url: str = Field(..., description="Pre-signed S3 PUT URL (time-limited)")
    cdn_url: Optional[str] = Field(None, description="CDN URL where artifact will be accessible")
    s3_key: Optional[str] = Field(None, description="S3 key for the artifact")
    expires_in_seconds: int = Field(..., description="Seconds until upload URL expires")
    required_headers: Optional[Dict[str, str]] = Field(
        None,
        description="Headers required when uploading to the signed URL",
    )


class RegisterToolArtifactRequest(BaseModel):
    """Request schema for tool registration."""
    tenant_id: str = Field(..., description="Organization/tenant ID")
    tool_name: str = Field(..., min_length=1, max_length=100)
    content_hash: str = Field(..., description="SHA-256 hash of artifact content")
    description: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    requires_permission: bool = False
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    ui_module_reference: Optional[str] = None


class RegisterUIModuleRequest(BaseModel):
    """Request schema for UI module registration."""
    tenant_id: str = Field(..., description="Organization/tenant ID")
    module_name: str = Field(..., min_length=1, max_length=100)
    content_hash: str = Field(..., description="SHA-256 hash of module content")


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class UserInfo(BaseModel):
    """User information schema."""
    id: str
    email: str
    created_at: str


class LoginResponseData(BaseModel):
    """Data field for login response."""
    session_id: str
    user: UserInfo
    expires_at: str


class LoginResponse(BaseModel):
    """Response schema for login endpoint."""
    success: bool
    data: LoginResponseData


# Tool Metadata Schemas (from tool.yaml)
class ToolMetadata(BaseModel):
    """Parsed tool.yaml schema."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputs: Dict[str, Any] = Field(..., description="Input schema definition")
    outputs: Dict[str, Any] = Field(..., description="Output schema definition")
    
    @field_validator('inputs', 'outputs')
    @classmethod
    def validate_schema_structure(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that inputs/outputs have proper schema structure."""
        if not isinstance(v, dict):
            raise ValueError("Schema must be a dictionary")
        
        # Basic validation - should have 'type' and 'properties'
        if 'type' not in v:
            raise ValueError("Schema must have 'type' field")
        
        if v.get('type') == 'object' and 'properties' not in v:
            raise ValueError("Object schema must have 'properties' field")
        
        return v
    
    def to_register_request(
        self,
        tenant_id: str,
        content_hash: str,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        requires_permission: bool = False,
        ui_module_reference: Optional[str] = None
    ) -> RegisterToolArtifactRequest:
        """Convert tool metadata to registration request."""
        return RegisterToolArtifactRequest(
            tenant_id=tenant_id,
            tool_name=self.name,
            content_hash=content_hash,
            description=self.description,
            risk_level=risk_level,
            requires_permission=requires_permission,
            input_schema=self.inputs,
            output_schema=self.outputs,
            ui_module_reference=ui_module_reference
        )


class UIModuleMetadata(BaseModel):
    """UI module metadata (minimal for now)."""
    module_name: str = Field(..., min_length=1, max_length=100)
    
    def to_register_request(
        self,
        tenant_id: str,
        content_hash: str
    ) -> RegisterUIModuleRequest:
        """Convert UI module metadata to registration request."""
        return RegisterUIModuleRequest(
            tenant_id=tenant_id,
            module_name=self.module_name,
            content_hash=content_hash
        )
