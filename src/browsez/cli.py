"""
CLI interface for BrowsEZ tool publishing system.

Provides user-friendly commands for publishing tools and UI modules.
"""

import sys
import getpass
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .check_tool import validate_tool
from .upload_tool import run as upload_tool_run
from .config import ConfigManager
from .api_client import ToolPublisherClient


@click.group()
@click.version_option(version=__version__, prog_name="browsez")
def main() -> None:
    """BrowsEZ CLI - Publish tools and UI modules to the platform."""
    pass


@main.command()
def login() -> None:
    """Login to the BrowsEZ platform."""
    click.echo()
    click.echo(click.style("Login to BrowsEZ Platform", fg="cyan", bold=True))
    click.echo("=" * 60)
    click.echo()
    
    # Get credentials
    email = click.prompt("Email", type=str).strip()
    if not email:
        click.echo(click.style("Error: Email is required", fg="red"))
        sys.exit(1)
        
    password = getpass.getpass("Password: ")
    if not password:
        click.echo(click.style("Error: Password is required", fg="red"))
        sys.exit(1)
        
    # Attempt login
    click.echo()
    click.echo("Authenticating...")
    config_manager = ConfigManager()
    config = config_manager.get()
    
    try:
        client = ToolPublisherClient(base_url=config.api_base_url)
        response = client.login(email, password)
        
        if response.success:
            user = response.data.user
            click.echo(click.style(f"✓ Welcome back, {user.email}!", fg="green"))
            
            # Save session
            config_manager.update(
                session_id=response.data.session_id,
                user_email=user.email,
                expires_at=response.data.expires_at
            )
            click.echo(click.style(f"✓ Session saved (expires: {response.data.expires_at})", fg="green"))
        else:
            click.echo(click.style("✗ Login failed", fg="red"))
            sys.exit(1)
            
    except Exception as e:
        click.echo(click.style(f"✗ Login error: {e}", fg="red"))
        sys.exit(1)


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, dir_okay=True))
def validate(directory: str) -> None:
    """Validate a tool without uploading.
    
    DIRECTORY: Path to the tool directory to validate.
    """
    directory_path = Path(directory).resolve()
    
    click.echo()
    click.echo(click.style(f"Validating tool: {directory_path.name}", fg="cyan", bold=True))
    click.echo("=" * 60)
    click.echo()
    
    errors = validate_tool(str(directory_path))
    
    if errors:
        click.echo(click.style("✗ Validation failed:", fg="red"))
        for e in errors:
            click.echo(f"  - {e}")
        sys.exit(1)
    else:
        click.echo(click.style("✓ Tool structure valid", fg="green"))
        click.echo(click.style("✓ tool.yaml schema valid", fg="green"))
        click.echo(click.style("✓ requirements.txt present", fg="green"))
        click.echo(click.style("✓ src/main.py has required functions", fg="green"))
        click.echo(click.style("✓ Input/Output classes defined", fg="green"))
        click.echo()
        click.echo("=" * 60)
        click.echo(click.style("✓ All checks passed!", fg="green", bold=True))
        click.echo("=" * 60)
        click.echo()


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--api-url", help="Override API base URL (default from .toolrc.json)")
@click.option(
    "--risk-level",
    type=click.Choice(["LOW", "MEDIUM", "HIGH"], case_sensitive=False),
    help="Override risk level (default: MEDIUM)"
)
@click.option("--requires-permission", is_flag=True, help="Mark tool as requiring permission")
@click.option("--ui-module-ref", help="Reference to UI module")
def publish(
    directory: str,
    api_url: Optional[str],
    risk_level: Optional[str],
    requires_permission: bool,
    ui_module_ref: Optional[str]
) -> None:
    """Publish a tool to the backend.
    
    DIRECTORY: Path to the tool directory to publish.
    """
    upload_tool_run(
        directory=directory,
        api_url=api_url,
        risk_level=risk_level.upper() if risk_level else None
    )


@main.command("publish-ui")
@click.argument("directory", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--api-url", help="Override API base URL (default from .toolrc.json)")
def publish_ui(directory: str, api_url: Optional[str]) -> None:
    """Publish a UI module to the backend.
    
    DIRECTORY: Path to the UI module directory to publish.
    """
    # TODO: Implement UI module publishing
    click.echo(click.style("UI module publishing not yet implemented", fg="yellow"))
    sys.exit(1)


@main.group()
def config() -> None:
    """Manage CLI configuration."""
    pass


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    config_manager = ConfigManager()
    cfg = config_manager.get()
    
    click.echo()
    click.echo(click.style("Current Configuration", fg="cyan", bold=True))
    click.echo("=" * 60)
    click.echo()
    click.echo(f"  API Base URL:     {cfg.api_base_url}")
    click.echo(f"  Tenant ID:        {cfg.tenant_id}")
    click.echo(f"  Default Risk:     {cfg.default_risk_level}")
    click.echo(f"  Upload Timeout:   {cfg.upload_timeout}s")
    click.echo(f"  Retry Attempts:   {cfg.retry_attempts}")
    click.echo()
    
    if cfg.session_id:
        click.echo(click.style("Session:", fg="cyan"))
        click.echo(f"  User Email:       {cfg.user_email}")
        click.echo(f"  Expires At:       {cfg.expires_at}")
    else:
        click.echo(click.style("Not logged in", fg="yellow"))
    click.echo()


@config.command("set")
@click.argument("key", type=click.Choice(["api-url", "tenant-id", "risk-level"]))
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value.
    
    KEY: Configuration key to set (api-url, tenant-id, risk-level)
    VALUE: New value for the configuration key
    """
    config_manager = ConfigManager()
    
    if key == "api-url":
        config_manager.update(api_url=value)
    elif key == "tenant-id":
        config_manager.update(tenant_id=value)
    elif key == "risk-level":
        if value.upper() not in ["LOW", "MEDIUM", "HIGH"]:
            click.echo(click.style(f"Invalid risk level: {value}", fg="red"))
            click.echo("Valid values: LOW, MEDIUM, HIGH")
            sys.exit(1)
        config_manager.update(risk_level=value.upper())
    
    click.echo(click.style(f"✓ Set {key} = {value}", fg="green"))


@main.command()
def logout() -> None:
    """Clear the current session."""
    config_manager = ConfigManager()
    config_manager.update(
        session_id=None,
        user_email=None,
        expires_at=None
    )
    click.echo(click.style("✓ Logged out successfully", fg="green"))


if __name__ == "__main__":
    main()
