from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from f1_project.load.silver import read_silver, write_silver
from f1_project.validation.schemas import MeetingSchema, SessionSchema


def test_write_silver_partitions_by_field(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("f1_project.load.silver.INTERIM_DATA_DIR", tmp_path)
    sessions = [
        SessionSchema(session_key=1, meeting_key=100, session_name="Practice 1"),
        SessionSchema(session_key=2, meeting_key=100, session_name="Practice 2"),
    ]

    paths = write_silver(sessions, "sessions", "session_key")

    assert {p.name for p in paths} == {"1.parquet", "2.parquet"}
    df = pd.read_parquet(tmp_path / "sessions" / "1.parquet")
    assert df.iloc[0]["session_name"] == "Practice 1"


def test_write_silver_overwrites_existing_partition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("f1_project.load.silver.INTERIM_DATA_DIR", tmp_path)
    write_silver([MeetingSchema(meeting_key=1, meeting_name="Old")], "meetings", "meeting_key")

    write_silver([MeetingSchema(meeting_key=1, meeting_name="New")], "meetings", "meeting_key")

    df = pd.read_parquet(tmp_path / "meetings" / "1.parquet")
    assert len(df) == 1
    assert df.iloc[0]["meeting_name"] == "New"


def test_write_silver_returns_empty_list_for_no_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("f1_project.load.silver.INTERIM_DATA_DIR", tmp_path)

    result = write_silver([], "meetings", "meeting_key")

    assert result == []


def test_read_silver_concatenates_all_partitions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("f1_project.load.silver.INTERIM_DATA_DIR", tmp_path)
    entity_dir = tmp_path / "meetings"
    entity_dir.mkdir()
    pd.DataFrame([{"meeting_key": 1}]).to_parquet(
        entity_dir / "1.parquet", engine="fastparquet", index=False
    )
    pd.DataFrame([{"meeting_key": 2}]).to_parquet(
        entity_dir / "2.parquet", engine="fastparquet", index=False
    )

    result = read_silver("meetings")

    assert sorted(result["meeting_key"]) == [1, 2]


def test_read_silver_returns_empty_dataframe_when_dir_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("f1_project.load.silver.INTERIM_DATA_DIR", tmp_path)

    result = read_silver("sessions")

    assert result.empty
