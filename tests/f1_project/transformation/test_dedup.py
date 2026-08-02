from __future__ import annotations

from f1_project.transformation.dedup import NATURAL_KEYS, deduplicate
from f1_project.validation.schemas import DriverSchema, LapSchema, MeetingSchema


def test_deduplicate_keeps_last_record_per_key() -> None:
    first = MeetingSchema(meeting_key=1219, meeting_name="Old Name")
    second = MeetingSchema(meeting_key=1219, meeting_name="New Name")

    result = deduplicate([first, second], NATURAL_KEYS[MeetingSchema])

    assert len(result) == 1
    assert result[0].meeting_name == "New Name"


def test_deduplicate_composite_key_for_drivers() -> None:
    driver_a = DriverSchema(session_key=9222, driver_number=1)
    driver_b = DriverSchema(session_key=9222, driver_number=44)
    driver_a_dup = DriverSchema(session_key=9222, driver_number=1, full_name="Updated")

    result = deduplicate([driver_a, driver_b, driver_a_dup], NATURAL_KEYS[DriverSchema])

    assert len(result) == 2
    assert {r.driver_number for r in result} == {1, 44}


def test_deduplicate_empty_input_returns_empty_list() -> None:
    assert deduplicate([], NATURAL_KEYS[MeetingSchema]) == []


def test_deduplicate_composite_key_for_laps() -> None:
    lap_1 = LapSchema(session_key=9222, driver_number=1, lap_number=1, lap_duration=91.5)
    lap_2 = LapSchema(session_key=9222, driver_number=1, lap_number=2, lap_duration=90.8)
    lap_1_dup = LapSchema(session_key=9222, driver_number=1, lap_number=1, lap_duration=91.1)

    result = deduplicate([lap_1, lap_2, lap_1_dup], NATURAL_KEYS[LapSchema])

    assert len(result) == 2
    lap_one = next(r for r in result if r.lap_number == 1)
    assert lap_one.lap_duration == 91.1
