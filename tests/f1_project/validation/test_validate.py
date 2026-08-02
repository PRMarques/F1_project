from __future__ import annotations

from f1_project.validation.schemas import (
    DriverSchema,
    LapSchema,
    MeetingSchema,
    SessionResultSchema,
)
from f1_project.validation.validate import validate_records


def test_validate_records_accepts_valid_and_rejects_invalid() -> None:
    records = [
        {"meeting_key": 1219, "year": 2024, "meeting_name": "Brazil Grand Prix"},
        {"meeting_key": "not-an-int", "year": 2024},
        {"year": 2024},  # falta meeting_key obrigatório
    ]

    valid, rejected = validate_records(records, MeetingSchema)

    assert len(valid) == 1
    assert valid[0].meeting_key == 1219
    assert len(rejected) == 2
    assert all("reason" in item and "record" in item for item in rejected)


def test_validate_records_handles_empty_input() -> None:
    valid, rejected = validate_records([], MeetingSchema)

    assert valid == []
    assert rejected == []


def test_validate_records_allows_null_optional_fields() -> None:
    records = [{"session_key": 9222, "driver_number": 1, "headshot_url": None}]

    valid, rejected = validate_records(records, DriverSchema)

    assert len(valid) == 1
    assert rejected == []


def test_validate_records_accepts_lap_and_rejects_missing_key() -> None:
    records = [
        {"session_key": 9222, "driver_number": 1, "lap_number": 1, "lap_duration": 91.234},
        {"session_key": 9222, "driver_number": 1},  # falta lap_number obrigatório
    ]

    valid, rejected = validate_records(records, LapSchema)

    assert len(valid) == 1
    assert valid[0].lap_duration == 91.234
    assert len(rejected) == 1


def test_validate_records_accepts_session_result_with_null_position() -> None:
    records = [{"session_key": 9222, "driver_number": 1, "position": None, "dnf": True}]

    valid, rejected = validate_records(records, SessionResultSchema)

    assert len(valid) == 1
    assert valid[0].position is None
    assert rejected == []
