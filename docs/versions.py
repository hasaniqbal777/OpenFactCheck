"""Module for generating switch.json file."""

#!/usr/bin/env python3
from __future__ import annotations

import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WEBSITE_HOME = "https://openfactcheck.readthedocs.io/en/"
DOCS_HOME = "docs"
DOCS_LATEST = "latest"
DOCS_ROOT = os.path.join(ROOT, DOCS_HOME)
DOCS_DEST = os.path.join(ROOT, "public")
VERSION_FILE = os.path.join(DOCS_ROOT, "src", "_static", "versions.json")


def format_version_entry(version: str) -> dict[str, str]:
    """Format a single entry of switcher.json, as expected by `pydata-sphinx-theme`."""
    return {
        "url": "/".join((WEBSITE_HOME, version, "")),
        "version": version,
    }


def validate_docs_folder(path: str) -> bool:
    """Check that folder with path specified contains valid documentation."""
    return os.path.isdir(path) and os.path.isfile(os.path.join(path, "index.html"))


def get_versions() -> list[str]:
    """List available versions of the package in the expected order."""
    with open(VERSION_FILE) as infile:
        versions = json.load(infile)

    print("Available versions:")
    for version in versions:
        print(f"  - {version}")


if __name__ == "__main__":
    get_versions()
