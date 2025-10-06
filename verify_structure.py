#!/usr/bin/env python3
"""
Verify project structure without requiring full dependencies.
This script checks that all required files exist and have basic syntax correctness.
"""

import os
import ast
import sys
from pathlib import Path

def check_file_exists(filepath):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {filepath}")
        return True
    else:
        print(f"❌ {filepath} - NOT FOUND")
        return False

def check_python_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"   ⚠️  Syntax error: {e}")
        return False

def main():
    print("🔍 Verifying Parcel Feasibility Engine Structure\n")

    # Configuration files
    print("📋 Configuration Files:")
    config_files = [
        "pyproject.toml",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "Makefile",
        "README.md",
        "openapi.yaml",
        ".env.example",
    ]

    config_ok = all(check_file_exists(f) for f in config_files)

    # Python modules
    print("\n🐍 Python Modules:")
    python_files = [
        "app/__init__.py",
        "app/main.py",
        "app/api/__init__.py",
        "app/api/analyze.py",
        "app/api/rules.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/models/__init__.py",
        "app/models/parcel.py",
        "app/models/zoning.py",
        "app/models/analysis.py",
        "app/rules/__init__.py",
        "app/rules/base_zoning.py",
        "app/rules/sb9.py",
        "app/rules/sb35.py",
        "app/rules/ab2011.py",
        "app/rules/ab2097.py",
        "app/rules/density_bonus.py",
        "app/rules/overlays.py",
    ]

    python_ok = True
    for filepath in python_files:
        exists = check_file_exists(filepath)
        if exists:
            syntax_ok = check_python_syntax(filepath)
            python_ok = python_ok and syntax_ok
        else:
            python_ok = False

    # Test files
    print("\n🧪 Test Files:")
    test_files = [
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_base_zoning.py",
        "tests/test_sb9.py",
        "tests/test_sb35.py",
        "tests/test_ab2011.py",
        "tests/test_ab2097.py",
        "tests/test_density_bonus.py",
        "tests/test_overlays.py",
    ]

    test_ok = all(check_file_exists(f) for f in test_files)

    # Summary
    print("\n" + "="*60)
    total_files = len(config_files) + len(python_files) + len(test_files)

    if config_ok and python_ok and test_ok:
        print(f"✅ SUCCESS: All {total_files} files present and valid!")
        print("\n📊 Project Statistics:")
        print(f"   • Configuration files: {len(config_files)}")
        print(f"   • Python modules: {len(python_files)}")
        print(f"   • Test files: {len(test_files)}")
        print(f"   • Total: {total_files}")
        print("\n🚀 Next Steps:")
        print("   1. Start Docker: make docker-up")
        print("   2. Run tests: docker-compose exec api pytest -q")
        print("   3. Start API: make dev")
        print("   4. Visit: http://localhost:8000/docs")
        return 0
    else:
        print("❌ ERRORS: Some files are missing or invalid")
        return 1

if __name__ == "__main__":
    sys.exit(main())
