"""
Tool validation module.

Validates tool directory structure, tool.yaml schema, and main.py requirements.
"""

import os
import zipfile
import hashlib
from pathlib import Path
from typing import List
import yaml
import ast


def validate_tool(path: str) -> List[str]:
    errors = []

    required_root_files = {"requirements.txt", "tool.yaml"}

    # ---- Path check ----
    if not os.path.isdir(path):
        return [f"Path does not exist or is not a directory: {path}"]

    root_files = set(os.listdir(path))

    # ---- Root file presence ----
    missing_root = required_root_files - root_files
    if missing_root:
        errors.append(f"Missing root files: {', '.join(missing_root)}")

    # ---- tool.yaml validation ----
    tool_yaml_path = os.path.join(path, "tool.yaml")
    if "tool.yaml" in root_files:
        try:
            with open(tool_yaml_path, "r", encoding="utf-8") as f:
                tool_yaml = yaml.safe_load(f)

            if not isinstance(tool_yaml, dict):
                errors.append("tool.yaml must be a YAML mapping/object")
            else:
                required_fields = {"name", "description", "inputs", "outputs"}
                missing_fields = required_fields - tool_yaml.keys()
                if missing_fields:
                    errors.append(
                        f"tool.yaml missing fields: {', '.join(missing_fields)}"
                    )

        except Exception as e:
            errors.append(f"Invalid tool.yaml: {e}")

    # ---- requirements.txt validation ----
    req_path = os.path.join(path, "requirements.txt")
    if "requirements.txt" in root_files:
        if os.path.getsize(req_path) == 0:
            errors.append("requirements.txt must not be empty")

    # ---- src directory validation ----
    src_path = os.path.join(path, "src")
    if not os.path.isdir(src_path):
        errors.append("Missing src/ directory")
        return errors

    src_files = set(os.listdir(src_path))

    # Auto-create __init__.py if missing
    init_path = os.path.join(src_path, "__init__.py")
    if "__init__.py" not in src_files:
        open(init_path, "w").close()

    # main.py presence
    if "main.py" not in src_files:
        errors.append("Missing src/main.py")
        return errors

    # ---- main.py content validation ----
    main_py_path = os.path.join(src_path, "main.py")
    try:
        with open(main_py_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        found_run = False
        found_input = False
        found_output = False

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "run":
                found_run = True
            elif isinstance(node, ast.ClassDef):
                if node.name == "Input":
                    found_input = True
                elif node.name == "Output":
                    found_output = True

        if not found_run:
            errors.append("main.py must define a run() function")
        if not found_input:
            errors.append("main.py must define class Input(TypedDict)")
        if not found_output:
            errors.append("main.py must define class Output(TypedDict)")

    except SyntaxError as e:
        errors.append(f"Syntax error in main.py: {e}")
    except Exception as e:
        errors.append(f"Failed to parse main.py: {e}")

    return errors


def zip_directory(directory_path: Path, output_path: Path) -> None:
    """Create a zip file from a directory.
    
    Args:
        directory_path: Path to directory to zip
        output_path: Path for output zip file
    """
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = Path(root) / file
                zipf.write(file_path, file_path.relative_to(directory_path))


def calculate_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to file to hash
        
    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()
