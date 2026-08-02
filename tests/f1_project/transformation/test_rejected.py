from __future__ import annotations

import json
from pathlib import Path

import pytest

from f1_project.transformation.rejected import save_rejected


def test_save_rejected_writes_file_with_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("f1_project.transformation.rejected.REJECTED_DATA_DIR", tmp_path)
    rejected = [{"record": {"meeting_key": "bad"}, "reason": "Input should be a valid integer"}]

    output_path = save_rejected("meetings", "2024", rejected)

    assert output_path == tmp_path / "meetings" / "2024.json"
    assert json.loads(output_path.read_text(encoding="utf-8")) == rejected


def test_save_rejected_returns_none_for_empty_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("f1_project.transformation.rejected.REJECTED_DATA_DIR", tmp_path)

    result = save_rejected("meetings", "2024", [])

    assert result is None
    assert not (tmp_path / "meetings").exists()
