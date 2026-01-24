"""
CLI interface for tool publishing system.

Provides user-friendly commands for publishing tools and UI modules.
"""

import sys
import argparse
from pathlib import Path

from check_tool import validate_tool
from upload_tool import run as upload_tool_run
from config import ConfigManager
from api_client import ToolPublisherClient


def validate_command(args: argparse.Namespace) -> None:
    """Validate a tool without uploading.
    
    Args:
        args: Parsed command-line arguments
    """
    directory_path = Path(args.directory).resolve()
    
    print(f"\nValidating tool: {directory_path.name}")
    print(f"{'='*60}\n")
    
    errors = validate_tool(str(directory_path))
    
    if errors:
        print("✗ Validation failed:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("✓ Tool structure valid")
        print("✓ tool.yaml schema valid")
        print("✓ requirements.txt present")
        print("✓ src/main.py has required functions")
        print("✓ Input/Output classes defined")
        print(f"\n{'='*60}")
        print("✓ All checks passed!")
        print(f"{'='*60}\n")


def publish_tool_command(args: argparse.Namespace) -> None:
    """Publish a tool to the backend.
    
    Args:
        args: Parsed command-line arguments
    """
    upload_tool_run(
        directory=args.directory,
        api_url=args.api_url,
        risk_level=args.risk_level
    )


def publish_ui_module_command(args: argparse.Namespace) -> None:
    """Publish a UI module to the backend.
    
    Args:
        args: Parsed command-line arguments
    """
    # TODO: Implement UI module publishing
    print("UI module publishing not yet implemented")
    sys.exit(1)


def login_command(args: argparse.Namespace) -> None:
    """Login to the platform.
    
    Args:
        args: Parsed command-line arguments
    """
    import getpass
    
    print(f"\nLogin to BrowsEZ Platform")
    print(f"{'='*60}\n")
    
    # Get credentials
    email = input("Email: ").strip()
    if not email:
        print("Error: Email is required")
        sys.exit(1)
        
    password = getpass.getpass("Password: ")
    if not password:
        print("Error: Password is required")
        sys.exit(1)
        
    # Attempt login
    print("\nAuthenticating...")
    config_manager = ConfigManager()
    config = config_manager.get()
    
    try:
        client = ToolPublisherClient(base_url=config.api_base_url)
        response = client.login(email, password)
        
        if response.success:
            user = response.data.user
            print(f"✓ Welcome back, {user.email}!")
            
            # Save session
            config_manager.update(
                session_id=response.data.session_id,
                user_email=user.email,
                expires_at=response.data.expires_at
            )
            print(f"✓ Session saved (expires: {response.data.expires_at})")
        else:
            print("✗ Login failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Login error: {e}")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Tool Publishing System - Publish tools and UI modules to backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a tool
  python cli.py validate-tool VA_Tools/create_va
  
  # Publish a tool (uses config from .toolrc.json)
  python cli.py publish-tool VA_Tools/create_va
  
  # Publish with overrides
  python cli.py publish-tool VA_Tools/create_va --api-url https://api.example.com/v1 --risk-level HIGH
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate tool command
    validate_parser = subparsers.add_parser(
        'validate-tool',
        help='Validate a tool without uploading'
    )
    validate_parser.add_argument(
        'directory',
        help='Path to tool directory'
    )
    validate_parser.set_defaults(func=validate_command)
    
    # Publish tool command
    publish_tool_parser = subparsers.add_parser(
        'publish-tool',
        help='Publish a tool to the backend'
    )
    publish_tool_parser.add_argument(
        'directory',
        help='Path to tool directory'
    )
    publish_tool_parser.add_argument(
        '--api-url',
        help='Override API base URL (default from .toolrc.json)'
    )
    publish_tool_parser.add_argument(
        '--risk-level',
        choices=['LOW', 'MEDIUM', 'HIGH'],
        help='Override risk level (default: MEDIUM)'
    )
    publish_tool_parser.add_argument(
        '--requires-permission',
        action='store_true',
        help='Mark tool as requiring permission'
    )
    publish_tool_parser.add_argument(
        '--ui-module-ref',
        help='Reference to UI module'
    )
    publish_tool_parser.set_defaults(func=publish_tool_command)
    
    # Publish UI module command
    publish_ui_parser = subparsers.add_parser(
        'publish-ui-module',
        help='Publish a UI module to the backend'
    )
    publish_ui_parser.add_argument(
        'directory',
        help='Path to UI module directory'
    )
    publish_ui_parser.add_argument(
        '--api-url',
        help='Override API base URL (default from .toolrc.json)'
    )
    publish_ui_parser.set_defaults(func=publish_ui_module_command)

    # Login command
    login_parser = subparsers.add_parser(
        'login',
        help='Login to the platform'
    )
    login_parser.set_defaults(func=login_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
