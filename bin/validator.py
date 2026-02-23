#!/usr/bin/env python3
"""
validate_ocd.py

Simple validator for the Open Contributions Descriptor (OCD)
against a JSON Schema.

Supports:
  - Local JSON file
  - Remote URL (https://...)
  - Local schema file OR schema URL

Requirements:
  pip install jsonschema requests

Usage examples:

  # Validate local file against local schema
  python validate_ocd.py data.json schema.json

  # Validate URL against schema
  python validate_ocd.py https://example.org/.well-known/open-contributions.json schema.json

  # Validate URL against remote schema
  python validate_ocd.py https://example.org/.well-known/open-contributions.json https://example.org/schema.json
"""

import json
import sys
from pathlib import Path
from typing import Any

import requests
from jsonschema import Draft202012Validator


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def load_json(source: str) -> Any:
    """Load JSON from URL or local file."""
    if is_url(source):
        print(f"[+] Fetching JSON from URL: {source}")
        r = requests.get(source, timeout=30)
        r.raise_for_status()
        return r.json()

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")

    print(f"[+] Loading JSON file: {source}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

def validate(instance: Any, schema: Any) -> int:
    """Validate JSON instance against schema."""
    print("[+] Validating JSON against schema...")

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)

    if not errors:
        print("✅ Validation successful — JSON is valid.")
        return 0

    print(f"❌ Validation failed ({len(errors)} error(s)):\n")

    for err in errors:
        location = "/".join(str(p) for p in err.path)
        if not location:
            location = "(root)"
        print(f"- Path: {location}")
        print(f"  Error: {err.message}\n")

    return 1


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    if len(sys.argv) != 3:
        print("Usage: validate_ocd.py <json_file_or_url> <schema_file_or_url>")
        sys.exit(2)

    json_source = sys.argv[1]
    schema_source = sys.argv[2]

    try:
        instance = load_json(json_source)
        schema = load_json(schema_source)
    except Exception as e:
        print(f"ERROR loading input: {e}")
        sys.exit(2)

    try:
        exit_code = validate(instance, schema)
    except Exception as e:
        print(f"Validation error: {e}")
        sys.exit(2)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
