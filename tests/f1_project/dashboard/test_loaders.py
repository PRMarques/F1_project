from __future__ import annotations

from pathlib import Path

import pytest

from f1_project.dashboard.loaders import load_drivers, load_meetings, load_sessions


def test_load_meetings_sessions_drivers_delegate_to_read_silver(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("f1_project.load.silver.INTERIM_DATA_DIR", tmp_path)

    assert load_meetings().empty
    assert load_sessions().empty
    assert load_drivers().empty
