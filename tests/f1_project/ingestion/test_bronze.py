from __future__ import annotations

import json
from pathlib import Path

import pytest

from f1_project.ingestion.bronze import save_raw_json


def test_save_raw_json_writes_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("f1_project.ingestion.bronze.RAW_DATA_DIR", tmp_path)
    payload = [{"meeting_key": 1219, "year": 2024}]

    output_path = save_raw_json("meetings", "2024", payload)

    assert output_path == tmp_path / "meetings" / "2024.json"
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_save_raw_json_creates_endpoint_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("f1_project.ingestion.bronze.RAW_DATA_DIR", tmp_path)

    save_raw_json("sessions", "latest", [])

    assert (tmp_path / "sessions").is_dir()
