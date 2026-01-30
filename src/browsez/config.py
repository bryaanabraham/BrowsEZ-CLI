"""
Configuration management module.

Handles loading configuration from multiple sources with priority:
1. Command-line arguments (optional overrides)
2. Configuration file (.toolrc.json)
3. Default values
"""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

from .schemas import RiskLevel


@dataclass
class Config:
    """Configuration settings for tool publishing."""
    api_base_url: str = "https://browsez-platform-backend-production.up.railway.app"
    tenant_id: str = "sample-tenant-123"  # Keep for backward compatibility if needed, or remove if strict
    session_id: Optional[str] = None
    user_email: Optional[str] = None
    expires_at: Optional[str] = None
    default_risk_level: str = "MEDIUM"
    upload_timeout: int = 300
    retry_attempts: int = 3
    kms_key_id: Optional[str] = None
    
    def get_risk_level(self) -> RiskLevel:
        """Convert string risk level to enum."""
        return RiskLevel[self.default_risk_level]


class ConfigManager:
    """Manages configuration loading and persistence."""
    
    DEFAULT_CONFIG_FILE = ".toolrc.json"
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config manager.
        
        Args:
            config_path: Optional path to config file. Defaults to .toolrc.json in current directory.
        """
        self.config_path = config_path or Path.cwd() / self.DEFAULT_CONFIG_FILE
        self.config = self._load_config()
    
    def _load_config(self) -> Config:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Config(**data)
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration")
                return Config()
        else:
            # Create default config file
            config = Config()
            self._save_config(config)
            print(f"Created default configuration file: {self.config_path}")
            return config
    
    def _save_config(self, config: Config) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save config to {self.config_path}: {e}")
    
    def update(
        self,
        api_url: Optional[str] = None,
        tenant_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        session_id: Optional[str] = None,
        user_email: Optional[str] = None,
        expires_at: Optional[str] = None,
        kms_key_id: Optional[str] = None
    ) -> None:
        """Update configuration with optional overrides.
        
        Args:
            api_url: Override API base URL
            tenant_id: Override tenant ID
            risk_level: Override default risk level
            session_id: Update session ID
            user_email: Update user email
            expires_at: Update session expiration
        """
        if api_url:
            self.config.api_base_url = api_url
        if tenant_id:
            self.config.tenant_id = tenant_id
        if risk_level:
            self.config.default_risk_level = risk_level
        if session_id is not None:
            self.config.session_id = session_id if session_id else None
        if user_email is not None:
            self.config.user_email = user_email if user_email else None
        if expires_at is not None:
            self.config.expires_at = expires_at if expires_at else None
        if kms_key_id:
            self.config.kms_key_id = kms_key_id
        
        # Save changes
        self._save_config(self.config)
    
    def get(self) -> Config:
        """Get current configuration."""
        return self.config
