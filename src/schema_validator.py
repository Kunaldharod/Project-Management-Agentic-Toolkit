"""
schema_validator.py
-------------------
Validates AI-generated PMBOK artifact JSON against the canonical schemas
before they are written to the artifacts/ directory.

Called internally by the n8n workflow between the AI Agent node and the
file-write node. Can also be used standalone for debugging.

Usage:
    python schema_validator.py --schema schemas/risk_register.schema.json \
                               --data artifacts/risk_register.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import jsonschema
from jsonschema import ValidationError, validate

log = logging.getLogger(__name__)


def load_json(path: str) -> dict | list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_artifact(schema_path: str, data_path: str) -> tuple[bool, list[str]]:
    """Returns (is_valid, list_of_error_messages)."""
    try:
        schema = load_json(schema_path)
        data   = load_json(data_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return False, [str(e)]

    errors = []
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        # Collect all errors (not just the first)
        validator = jsonschema.Draft7Validator(schema)
        for err in sorted(validator.iter_errors(data), key=lambda e: e.path):
            errors.append(f"  [{' > '.join(str(p) for p in err.path)}] {err.message}")

    return (len(errors) == 0), errors


def validate_payload_dict(schema_path: str, data: dict) -> tuple[bool, list[str]]:
    """Validate an in-memory dict against a schema file."""
    try:
        schema = load_json(schema_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return False, [str(e)]

    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for err in sorted(validator.iter_errors(data), key=lambda e: e.path):
        errors.append(f"  [{' > '.join(str(p) for p in err.path)}] {err.message}")

    return (len(errors) == 0), errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a PMBOK JSON artifact")
    parser.add_argument("--schema", required=True, help="Path to JSON schema file")
    parser.add_argument("--data",   required=True, help="Path to artifact JSON file to validate")
    args = parser.parse_args()

    is_valid, errors = validate_artifact(args.schema, args.data)
    if is_valid:
        print(json.dumps({"valid": True, "errors": []}))
    else:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
