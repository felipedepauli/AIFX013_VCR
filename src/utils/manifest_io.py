"""Manifest I/O utilities.

Manifests are JSONL files (one JSON object per line).
This is the central data contract between pipeline stages.
"""

import json
from pathlib import Path
from typing import Any


def read_manifest(path: str | Path) -> list[dict[str, Any]]:
    """Read a JSONL manifest file.

    Args:
        path: Path to the manifest file.

    Returns:
        List of records (dictionaries).

    Raises:
        FileNotFoundError: If the manifest doesn't exist.
        json.JSONDecodeError: If a line is not valid JSON.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON at line {line_num}: {e.msg}",
                    e.doc,
                    e.pos,
                )
    return records


def write_manifest(records: list[dict[str, Any]], path: str | Path) -> None:
    """Write records to a JSONL manifest file.

    Args:
        records: List of records (dictionaries).
        path: Path to write the manifest file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_to_manifest(record: dict[str, Any], path: str | Path) -> None:
    """Append a single record to a manifest file.

    Args:
        record: Record to append.
        path: Path to the manifest file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
