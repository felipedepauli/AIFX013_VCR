"""Tests for utility modules."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from src.utils.config import load_config, save_config
from src.utils.manifest_io import append_to_manifest, read_manifest, write_manifest


class TestConfig:
    """Tests for config utilities."""

    def test_load_config(self, tmp_path):
        config_data = {"key": "value", "nested": {"a": 1, "b": 2}}
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        loaded = load_config(config_file)
        assert loaded == config_data

    def test_load_config_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")

    def test_save_config(self, tmp_path):
        config_data = {"key": "value", "list": [1, 2, 3]}
        config_file = tmp_path / "output" / "config.yaml"

        save_config(config_data, config_file)

        assert config_file.exists()
        with open(config_file) as f:
            loaded = yaml.safe_load(f)
        assert loaded == config_data


class TestManifestIO:
    """Tests for manifest I/O utilities."""

    def test_write_and_read_manifest(self, tmp_path):
        records = [
            {"id": "001", "label": "white", "bbox_xyxy": [10, 20, 100, 200]},
            {"id": "002", "label": "black", "bbox_xyxy": [30, 40, 150, 250]},
        ]
        manifest_path = tmp_path / "manifest.jsonl"

        write_manifest(records, manifest_path)
        loaded = read_manifest(manifest_path)

        assert loaded == records

    def test_read_manifest_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            read_manifest("/nonexistent/manifest.jsonl")

    def test_read_manifest_invalid_json(self, tmp_path):
        manifest_path = tmp_path / "bad.jsonl"
        with open(manifest_path, "w") as f:
            f.write('{"valid": "json"}\n')
            f.write("not valid json\n")

        with pytest.raises(json.JSONDecodeError):
            read_manifest(manifest_path)

    def test_append_to_manifest(self, tmp_path):
        manifest_path = tmp_path / "manifest.jsonl"

        # Write initial
        write_manifest([{"id": "001"}], manifest_path)

        # Append
        append_to_manifest({"id": "002"}, manifest_path)
        append_to_manifest({"id": "003"}, manifest_path)

        loaded = read_manifest(manifest_path)
        assert len(loaded) == 3
        assert loaded[0]["id"] == "001"
        assert loaded[1]["id"] == "002"
        assert loaded[2]["id"] == "003"

    def test_empty_lines_ignored(self, tmp_path):
        manifest_path = tmp_path / "manifest.jsonl"
        with open(manifest_path, "w") as f:
            f.write('{"id": "001"}\n')
            f.write("\n")
            f.write('{"id": "002"}\n')
            f.write("   \n")

        loaded = read_manifest(manifest_path)
        assert len(loaded) == 2
