"""Tests for 02_preprocess.py."""

import json
import tempfile
from pathlib import Path

import pytest

# Import functions from the script
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.manifest_io import read_manifest, write_manifest


def test_validate_records():
    """Test record validation."""
    # Import the function
    sys.path.insert(0, str(Path(__file__).parent.parent))

    # We'll test by importing the module
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "preprocess",
        Path(__file__).parent.parent / "02_preprocess.py"
    )
    preprocess = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preprocess)

    records = [
        {"id": "001", "label": "white"},
        {"id": "002", "label": ""},  # Empty label
        {"id": "003"},  # Missing label
        {"label": "black"},  # Missing id
        {"id": "004", "label": "silver"},
    ]

    valid, errors = preprocess.validate_records(records, require_label=True, check_images=False)

    assert len(valid) == 2  # Only 001 and 004
    assert len(errors) == 3


def test_build_class_mapping():
    """Test class-to-index mapping."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "preprocess",
        Path(__file__).parent.parent / "02_preprocess.py"
    )
    preprocess = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preprocess)

    records = [
        {"id": "1", "label": "white"},
        {"id": "2", "label": "black"},
        {"id": "3", "label": "white"},
        {"id": "4", "label": "silver"},
    ]

    class_to_idx = preprocess.build_class_mapping(records)

    assert len(class_to_idx) == 3
    assert "white" in class_to_idx
    assert "black" in class_to_idx
    assert "silver" in class_to_idx
    # Should be sorted alphabetically
    assert class_to_idx == {"black": 0, "silver": 1, "white": 2}


def test_get_class_counts():
    """Test class count computation."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "preprocess",
        Path(__file__).parent.parent / "02_preprocess.py"
    )
    preprocess = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preprocess)

    records = [
        {"id": "1", "label": "white"},
        {"id": "2", "label": "black"},
        {"id": "3", "label": "white"},
        {"id": "4", "label": "white"},
    ]

    counts = preprocess.get_class_counts(records)

    assert counts == {"white": 3, "black": 1}


def test_extract_group_key():
    """Test group key extraction from record ID."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "preprocess",
        Path(__file__).parent.parent / "02_preprocess.py"
    )
    preprocess = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preprocess)

    record = {"id": "000001_henrique_00002_0000", "label": "white"}

    # Extract camera_id
    key = preprocess.extract_group_key(record, "camera_id")
    assert key == "henrique"

    # No grouping
    key_none = preprocess.extract_group_key(record, None)
    assert key_none == record["id"]


def test_split_data():
    """Test data splitting."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "preprocess",
        Path(__file__).parent.parent / "02_preprocess.py"
    )
    preprocess = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preprocess)

    # Create records with different cameras
    records = []
    for i in range(100):
        camera = ["henrique", "sandro", "rafael"][i % 3]
        records.append({
            "id": f"{i:06d}_{camera}_{i:05d}_0000",
            "label": ["white", "black", "silver"][i % 3],
        })

    split_records = preprocess.split_data(
        records,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        group_by="camera_id",
        seed=42,
    )

    # Check all records have split
    for r in split_records:
        assert "split" in r
        assert r["split"] in ["train", "val", "test"]

    # Check rough proportions
    from collections import Counter
    split_counts = Counter(r["split"] for r in split_records)
    assert split_counts["train"] >= 50  # At least 50%
