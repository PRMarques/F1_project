from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from f1_project.load import gold


def _laps_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "session_key": 1,
                "meeting_key": 100,
                "driver_number": 1,
                "lap_number": 1,
                "lap_duration": 91.5,
            },
            {
                "session_key": 1,
                "meeting_key": 100,
                "driver_number": 1,
                "lap_number": 2,
                "lap_duration": 90.2,
            },
            {
                "session_key": 1,
                "meeting_key": 100,
                "driver_number": 44,
                "lap_number": 1,
                "lap_duration": 89.8,
            },
            {
                "session_key": 1,
                "meeting_key": 100,
                "driver_number": 44,
                "lap_number": 2,
                "lap_duration": None,
            },
            {
                "session_key": 2,
                "meeting_key": 200,
                "driver_number": 1,
                "lap_number": 1,
                "lap_duration": 75.0,
            },
        ]
    )


def _meetings_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "meeting_key": 100,
                "meeting_name": "Bahrain Grand Prix",
                "circuit_short_name": "Bahrain",
                "country_name": "Bahrain",
                "year": 2023,
            },
            {
                "meeting_key": 200,
                "meeting_name": "Saudi Arabian Grand Prix",
                "circuit_short_name": "Jeddah",
                "country_name": "Saudi Arabia",
                "year": 2023,
            },
        ]
    )


def _drivers_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "session_key": 1,
                "driver_number": 1,
                "full_name": "Max Verstappen",
                "team_name": "Red Bull",
            },
            {
                "session_key": 1,
                "driver_number": 44,
                "full_name": "Lewis Hamilton",
                "team_name": "Mercedes",
            },
            {
                "session_key": 2,
                "driver_number": 1,
                "full_name": "Max Verstappen",
                "team_name": "Red Bull",
            },
        ]
    )


def _sessions_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"session_key": 1, "meeting_key": 100, "session_name": "Race"},
            {"session_key": 2, "meeting_key": 100, "session_name": "Qualifying"},
        ]
    )


def _laps_sessions_df() -> pd.DataFrame:
    """Sessões correspondentes a `_laps_df()`: session_key 1 -> meeting 100, 2 -> meeting 200."""
    return pd.DataFrame(
        [
            {"session_key": 1, "meeting_key": 100, "session_name": "Race"},
            {"session_key": 2, "meeting_key": 200, "session_name": "Race"},
        ]
    )


def _session_result_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"session_key": 1, "driver_number": 1, "position": 1},
            {"session_key": 1, "driver_number": 44, "position": 2},
            {"session_key": 1, "driver_number": 16, "position": 3},
            {"session_key": 1, "driver_number": 55, "position": 4},
            {"session_key": 2, "driver_number": 1, "position": 1},
        ]
    )


def test_compute_fastest_laps_by_circuit_ranks_and_excludes_invalid() -> None:
    result = gold.compute_fastest_laps_by_circuit(
        _laps_df(), _laps_sessions_df(), _meetings_df(), _drivers_df(), top_n=5
    )

    bahrain = result[result["circuit_short_name"] == "Bahrain"]
    assert len(bahrain) == 3
    assert list(bahrain["lap_duration"]) == sorted(bahrain["lap_duration"])
    assert bahrain["lap_duration"].min() == 89.8


def test_compute_fastest_laps_by_circuit_ignores_laps_own_meeting_key() -> None:
    """O circuito vem de `sessions.meeting_key`, não da coluna (possivelmente ausente) em `laps`."""
    laps = pd.DataFrame(
        [
            {
                "session_key": 2,
                "meeting_key": None,
                "driver_number": 1,
                "lap_number": 1,
                "lap_duration": 75.0,
            }
        ]
    )

    result = gold.compute_fastest_laps_by_circuit(
        laps, _laps_sessions_df(), _meetings_df(), pd.DataFrame()
    )

    assert list(result["circuit_short_name"]) == ["Jeddah"]


def test_compute_fastest_laps_by_circuit_respects_top_n() -> None:
    laps = pd.DataFrame(
        [
            {"session_key": 1, "driver_number": 1, "lap_number": n, "lap_duration": 100 - n}
            for n in range(1, 8)
        ]
    )
    sessions = pd.DataFrame([{"session_key": 1, "meeting_key": 100, "session_name": "Race"}])
    meetings = pd.DataFrame(
        [
            {
                "meeting_key": 100,
                "circuit_short_name": "Bahrain",
                "country_name": "Bahrain",
                "year": 2023,
            }
        ]
    )

    result = gold.compute_fastest_laps_by_circuit(laps, sessions, meetings, pd.DataFrame(), top_n=5)

    assert len(result) == 5
    assert result["lap_duration"].iloc[0] == result["lap_duration"].min()


def test_compute_fastest_laps_by_circuit_returns_empty_for_no_data() -> None:
    assert gold.compute_fastest_laps_by_circuit(
        pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    ).empty


def test_compute_podium_by_race_keeps_only_top_three_of_race_sessions() -> None:
    result = gold.compute_podium_by_race(
        _session_result_df(), _sessions_df(), _meetings_df(), _drivers_df()
    )

    assert len(result) == 3
    assert set(result["position"]) == {1, 2, 3}
    assert (result["session_key"] == 1).all()


def test_compute_podium_by_race_ignores_session_result_own_meeting_key() -> None:
    """O meeting_key vem de `sessions`, não da coluna (às vezes ausente) em `session_result`."""
    session_result = pd.DataFrame(
        [
            {"session_key": 1, "meeting_key": None, "driver_number": 1, "position": 1},
            {"session_key": 1, "meeting_key": None, "driver_number": 44, "position": 2},
            {"session_key": 1, "meeting_key": None, "driver_number": 16, "position": 3},
        ]
    )

    result = gold.compute_podium_by_race(
        session_result, _sessions_df(), _meetings_df(), _drivers_df()
    )

    assert len(result) == 3
    assert (result["meeting_key"] == 100).all()


def test_compute_podium_by_race_returns_empty_when_no_race_session() -> None:
    sessions = pd.DataFrame([{"session_key": 2, "meeting_key": 100, "session_name": "Qualifying"}])

    result = gold.compute_podium_by_race(
        _session_result_df(), sessions, _meetings_df(), _drivers_df()
    )

    assert result.empty


def test_compute_podium_by_race_returns_empty_for_no_data() -> None:
    assert gold.compute_podium_by_race(
        pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    ).empty


def test_build_and_read_gold_tables(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    interim_dir = tmp_path / "interim"
    processed_dir = tmp_path / "processed"
    monkeypatch.setattr("f1_project.load.silver.INTERIM_DATA_DIR", interim_dir)
    monkeypatch.setattr("f1_project.load.gold.PROCESSED_DATA_DIR", processed_dir)

    for entity, df in [
        ("laps", _laps_df()),
        ("meetings", _meetings_df()),
        ("drivers", _drivers_df()),
        ("sessions", _laps_sessions_df()),
        ("session_result", _session_result_df()),
    ]:
        entity_dir = interim_dir / entity
        entity_dir.mkdir(parents=True)
        df.to_parquet(entity_dir / "part.parquet", engine="fastparquet", index=False)

    gold.build_gold_tables()

    assert (processed_dir / gold.FASTEST_LAPS_FILENAME).exists()
    assert (processed_dir / gold.PODIUM_FILENAME).exists()
    assert not gold.read_fastest_laps_by_circuit().empty
    assert not gold.read_podium_by_race().empty


def test_read_gold_tables_return_empty_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("f1_project.load.gold.PROCESSED_DATA_DIR", tmp_path)

    assert gold.read_fastest_laps_by_circuit().empty
    assert gold.read_podium_by_race().empty
