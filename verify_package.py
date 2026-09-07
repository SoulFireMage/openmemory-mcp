#!/usr/bin/env python3
"""
Verification script to check if all package components are present.
Run this AFTER copying to Windows to verify the package is complete.
"""

import sys
from pathlib import Path


def check_file(path: Path, name: str) -> bool:
    """Check if a file exists"""
    if path.exists():
        print(f"✓ {name}: {path}")
        return True
    else:
        print(f"✗ {name}: MISSING - {path}")
        return False


def main():
    print("OpenMemory MCP Package Verification\n" + "=" * 50)

    # Get package root
    root = Path(__file__).parent
    print(f"\nPackage root: {root}\n")

    # Check all required files
    checks = [
        (root / "pyproject.toml", "Package config"),
        (root / "README.md", "Main documentation"),
        (root / "WINDOWS_QUICKSTART.md", "Quick start guide"),
        (root / ".env.example", "Environment template"),
        (root / "src" / "openmemory_mcp" / "__init__.py", "Package init"),
        (root / "src" / "openmemory_mcp" / "__main__.py", "Entry point"),
        (root / "src" / "openmemory_mcp" / "client.py", "API client"),
        (root / "src" / "openmemory_mcp" / "server.py", "MCP server"),
    ]

    results = [check_file(path, name) for path, name in checks]

    print("\n" + "=" * 50)
    if all(results):
        print("✓ All files present! Package is complete.")
        print("\nNext steps:")
        print("1. pip install -e .")
        print("2. Edit %APPDATA%\\Claude\\claude_desktop_config.json")
        print("3. Restart Claude Desktop")
        return 0
    else:
        print("✗ Some files are missing. Package is incomplete.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
