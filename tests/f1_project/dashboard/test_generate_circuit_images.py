from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from f1_project.dashboard import generate_circuit_images as gci

# --- asset_slug -----------------------------------------------------------------------


def test_asset_slug_removes_accents_and_punctuation() -> None:
    assert gci.asset_slug("São Paulo") == "sao-paulo"
    assert gci.asset_slug("  Multiple   Spaces!! ") == "multiple-spaces"


# --- rotate ---------------------------------------------------------------------------


def test_rotate_by_zero_degrees_keeps_points_unchanged() -> None:
    points = np.array([[1.0, 0.0], [0.0, 1.0]])

    result = gci.rotate(points, 0.0)

    assert np.allclose(result, points)


def test_rotate_by_ninety_degrees() -> None:
    points = np.array([[1.0, 0.0]])

    result = gci.rotate(points, 90.0)

    assert np.allclose(result, [[0.0, 1.0]], atol=1e-9)


# --- generate_track ---------------------------------------------------------------------


class _FakeLap:
    def get_telemetry(self) -> pd.DataFrame:
        return pd.DataFrame({"X": [0.0, 1.0, 2.0, 3.0], "Y": [0.0, 1.0, 0.0, 1.0]})


class _FakeLaps:
    def pick_fastest(self) -> _FakeLap:
        return _FakeLap()


class _FakeCircuitInfo:
    rotation = 0.0


class _FakeSession:
    def __init__(self, event: dict[str, str]) -> None:
        self.laps = _FakeLaps()
        self.event = event

    def load(self, **kwargs: object) -> None:
        return None

    def get_circuit_info(self) -> _FakeCircuitInfo:
        return _FakeCircuitInfo()


def test_generate_track_renders_png_from_telemetry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(gci, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(
        gci.fastf1,
        "get_session",
        lambda year, round_number, kind: _FakeSession({"Location": "Test City"}),
    )

    output = gci.generate_track(2024, 1)

    assert output == tmp_path / "test-city.png"
    assert output.exists()


def test_generate_track_skips_existing_file_without_reloading_telemetry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(gci, "OUTPUT_DIR", tmp_path)
    existing = tmp_path / "test-city.png"
    existing.write_bytes(b"already there")

    class _ExplodingLaps:
        def pick_fastest(self) -> None:
            raise AssertionError("não deveria recalcular quando o PNG já existe")

    class _SkipSession(_FakeSession):
        def __init__(self, event: dict[str, str]) -> None:
            super().__init__(event)
            self.laps = _ExplodingLaps()

    monkeypatch.setattr(
        gci.fastf1,
        "get_session",
        lambda year, round_number, kind: _SkipSession({"Location": "Test City"}),
    )

    output = gci.generate_track(2024, 1, force=False)

    assert output == existing
    assert output.read_bytes() == b"already there"


def test_generate_track_raises_when_telemetry_insufficient(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(gci, "OUTPUT_DIR", tmp_path)

    class _EmptyLap:
        def get_telemetry(self) -> pd.DataFrame:
            return pd.DataFrame({"X": [], "Y": []})

    class _EmptyLaps:
        def pick_fastest(self) -> _EmptyLap:
            return _EmptyLap()

    class _EmptySession(_FakeSession):
        def __init__(self, event: dict[str, str]) -> None:
            super().__init__(event)
            self.laps = _EmptyLaps()

    monkeypatch.setattr(
        gci.fastf1,
        "get_session",
        lambda year, round_number, kind: _EmptySession({"Location": "Deserto"}),
    )

    with pytest.raises(RuntimeError, match="Telemetria insuficiente"):
        gci.generate_track(2024, 1)


# --- main -----------------------------------------------------------------------------


def test_main_generates_track_for_every_event_in_schedule(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(gci, "OUTPUT_DIR", tmp_path / "circuits")
    monkeypatch.setattr(gci, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(gci.fastf1.Cache, "enable_cache", lambda path: None)

    schedule = pd.DataFrame({"RoundNumber": [1, 2], "EventName": ["GP One", "GP Two"]})
    monkeypatch.setattr(
        gci.fastf1, "get_event_schedule", lambda year, include_testing=False: schedule
    )

    generated: list[int] = []

    def fake_generate_track(year: int, round_number: int, force: bool = False) -> Path:
        generated.append(round_number)
        if round_number == 2:
            raise RuntimeError("falha simulada")
        return tmp_path / "circuits" / f"round-{round_number}.png"

    monkeypatch.setattr(gci, "generate_track", fake_generate_track)
    monkeypatch.setattr("sys.argv", ["generate_circuit_images.py", "--year", "2024"])

    gci.main()

    assert generated == [1, 2]
    assert (tmp_path / "circuits").is_dir()
    assert (tmp_path / "cache").is_dir()
