"""
Packaging module for creating deterministic zip files and content hashing.

Ensures that identical tool content produces identical hashes.
"""

import os
import zipfile
import hashlib
from pathlib import Path
from typing import Tuple, Optional


def create_deterministic_zip(source_dir: Path, output_path: Path) -> Path:
    """Create a deterministic zip file with consistent ordering and timestamps.
    
    Args:
        source_dir: Directory to zip
        output_path: Output zip file path
        
    Returns:
        Path to created zip file
    """
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Collect all files and sort them for deterministic ordering
        files_to_add = []
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(source_dir)
                files_to_add.append((file_path, relative_path))
        
        # Sort by relative path for consistency
        files_to_add.sort(key=lambda x: str(x[1]))
        
        # Add files with consistent timestamp
        consistent_time = (1980, 1, 1, 0, 0, 0)
        for file_path, relative_path in files_to_add:
            # Create ZipInfo with consistent timestamp
            zip_info = zipfile.ZipInfo(str(relative_path))
            zip_info.date_time = consistent_time
            zip_info.compress_type = zipfile.ZIP_DEFLATED
            
            # Set consistent permission (regular file: 0o100644, rw-r--r--)
            # If executable (chmod +x), we might want 0o100755
            # For simplicity and reproducibility, we normalize to 644 for all files unless explicitly executable
            mode = 0o100644
            
            # Check if source is executable (simplistic check for Linux/Mac, Windows ignores this mostly)
            # but we want output consistency.
            if os.access(file_path, os.X_OK) and not os.name == 'nt':
                 mode = 0o100755
            
            zip_info.external_attr = mode << 16
            
            # Read and write file content
            with open(file_path, 'rb') as f:
                zipf.writestr(zip_info, f.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    
    return output_path


def calculate_content_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to file to hash
        
    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        # Read in chunks for memory efficiency
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def package_tool(tool_dir: Path, output_dir: Optional[Path] = None) -> Tuple[Path, str]:
    """Package a tool directory into a zip file and calculate its hash.
    
    Args:
        tool_dir: Path to tool directory
        output_dir: Optional output directory for zip file (defaults to current directory)
        
    Returns:
        Tuple of (zip_path, content_hash)
        
    Raises:
        ValueError: If tool_dir doesn't exist or is not a directory
    """
    if not tool_dir.is_dir():
        raise ValueError(f"Tool directory does not exist: {tool_dir}")
    
    # Determine output path
    if output_dir is None:
        output_dir = Path.cwd()
    
    zip_filename = f"{tool_dir.name}.zip"
    zip_path = output_dir / zip_filename
    
    # Create deterministic zip
    create_deterministic_zip(tool_dir, zip_path)
    
    # Calculate hash
    content_hash = calculate_content_hash(zip_path)
    
    return zip_path, content_hash


def package_ui_module(module_dir: Path, output_dir: Optional[Path] = None) -> Tuple[Path, str]:
    """Package a UI module directory into a zip file and calculate its hash.
    
    Args:
        module_dir: Path to UI module directory
        output_dir: Optional output directory for zip file (defaults to current directory)
        
    Returns:
        Tuple of (zip_path, content_hash)
        
    Raises:
        ValueError: If module_dir doesn't exist or is not a directory
    """
    # Same implementation as package_tool for now
    return package_tool(module_dir, output_dir)
