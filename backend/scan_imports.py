#!/usr/bin/env python3
"""
Script to scan the codebase for import issues.
This will attempt to import all Python modules in the app directory
and report any import errors.
"""
import os
import sys
import importlib
import traceback
from pathlib import Path
from typing import List, Tuple

# Add the parent directory to sys.path to allow absolute imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

def find_python_files(start_dir: str) -> List[str]:
    """Find all Python files in the directory tree."""
    python_files = []
    for root, _, files in os.walk(start_dir):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files

def file_to_module_name(file_path: str, base_dir: str) -> str:
    """Convert a file path to a module name."""
    rel_path = os.path.relpath(file_path, base_dir)
    module_name = rel_path.replace(os.path.sep, ".").replace(".py", "")
    return module_name

def test_import(module_name: str) -> Tuple[bool, str]:
    """Test importing a module and return success status and error message."""
    try:
        importlib.import_module(module_name)
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

def main():
    # Directory containing the Python packages
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Scanning for Python files in {base_dir}...")
    python_files = find_python_files(base_dir)
    print(f"Found {len(python_files)} Python files.")
    
    print("\nTesting imports...")
    failures = 0
    
    for file_path in python_files:
        module_name = file_to_module_name(file_path, os.path.dirname(base_dir))
        
        # Skip __init__.py files and __pycache__ directories
        if module_name.endswith("__init__") or "__pycache__" in module_name:
            continue
        
        # Skip alembic files for now as they might have special dependencies
        if "alembic" in module_name:
            continue
            
        print(f"Testing import for {module_name}...", end=" ")
        success, error = test_import(module_name)
        
        if success:
            print("OK")
        else:
            print("FAILED")
            print(f"  Error: {error.splitlines()[0]}")
            failures += 1
    
    print("\nImport test summary:")
    print(f"  Tested: {len(python_files)} modules")
    print(f"  Succeeded: {len(python_files) - failures} modules")
    print(f"  Failed: {failures} modules")
    
    if failures > 0:
        print("\nSome imports failed. Check the error messages above.")
        return 1
    else:
        print("\nAll imports succeeded!")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 