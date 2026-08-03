from __future__ import annotations

import httpx
import pytest
import respx

from f1_project import pipeline
from f1_project.config import Settings

BASE_URL = "https://api.openf1.org/v1/"


def _patch_data_dirs(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("f1_project.ingestion.bronze.RAW_DATA_DIR", tmp_path / "raw")
    monkeypatch.setattr("f1_project.load.silver.INTERIM_DATA_DIR", tmp_path / "interim")
    monkeypatch.setattr("f1_project.load.gold.PROCESSED_DATA_DIR", tmp_path / "processed")
    monkeypatch.setattr(
        "f1_project.transformation.rejected.REJECTED_DATA_DIR", tmp_path / "rejected"
    )
    monkeypatch.setattr(
        "f1_project.ingestion.client.default_settings",
        Settings(base_url=BASE_URL, timeout_seconds=5.0, max_retries=1),
    )


@respx.mock
def test_run_ingests_meetings_sessions_drivers_laps_and_session_result(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_data_dirs(tmp_path, monkeypatch)

    respx.get(f"{BASE_URL}meetings").mock(
        return_value=httpx.Response(
            200, json=[{"meeting_key": 1219, "year": 2024, "circuit_short_name": "Bahrain"}]
        )
    )
    respx.get(f"{BASE_URL}sessions").mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9222, "meeting_key": 1219, "session_name": "Race"}]
        )
    )
    respx.get(f"{BASE_URL}drivers").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "session_key": 9222,
                    "driver_number": 1,
                    "full_name": "Max Verstappen",
                    "team_name": "Red Bull",
                }
            ],
        )
    )
    respx.get(f"{BASE_URL}laps").mock(
        return_value=httpx.Response(
            200,
            json=[{"session_key": 9222, "driver_number": 1, "lap_number": 1, "lap_duration": 91.5}],
        )
    )
    respx.get(f"{BASE_URL}session_result").mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9222, "driver_number": 1, "position": 1}]
        )
    )

    pipeline.run(years=[2024])

    assert (tmp_path / "raw" / "meetings" / "2024.json").exists()
    assert (tmp_path / "raw" / "laps" / "9222.json").exists()
    assert (tmp_path / "raw" / "session_result" / "9222.json").exists()
    assert (tmp_path / "interim" / "laps" / "9222.parquet").exists()
    assert (tmp_path / "interim" / "session_result" / "9222.parquet").exists()
    assert (tmp_path / "processed" / "fastest_laps_by_circuit.parquet").exists()
    assert (tmp_path / "processed" / "podium_by_race.parquet").exists()


@respx.mock
def test_run_skips_laps_and_session_result_for_non_race_sessions(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_data_dirs(tmp_path, monkeypatch)

    respx.get(f"{BASE_URL}meetings").mock(
        return_value=httpx.Response(200, json=[{"meeting_key": 1219, "year": 2024}])
    )
    respx.get(f"{BASE_URL}sessions").mock(
        return_value=httpx.Response(
            200,
            json=[{"session_key": 7763, "meeting_key": 1219, "session_name": "Practice 1"}],
        )
    )
    respx.get(f"{BASE_URL}drivers").mock(return_value=httpx.Response(200, json=[]))

    pipeline.run(years=[2024])

    assert not (tmp_path / "raw" / "laps").exists()
    assert not (tmp_path / "raw" / "session_result").exists()


@respx.mock
def test_run_ingests_multiple_years(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_data_dirs(tmp_path, monkeypatch)

    respx.get(f"{BASE_URL}meetings").mock(
        side_effect=[
            httpx.Response(200, json=[{"meeting_key": 1, "year": 2023}]),
            httpx.Response(200, json=[{"meeting_key": 2, "year": 2024}]),
        ]
    )
    respx.get(f"{BASE_URL}sessions").mock(return_value=httpx.Response(200, json=[]))
    respx.get(f"{BASE_URL}drivers").mock(return_value=httpx.Response(200, json=[]))

    pipeline.run(years=[2023, 2024])

    assert (tmp_path / "raw" / "meetings" / "2023.json").exists()
    assert (tmp_path / "raw" / "meetings" / "2024.json").exists()


@respx.mock
def test_run_skips_session_on_client_error_and_continues(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Uma sessão com erro (ex.: 404 real observado na OpenF1) não deve abortar as demais."""
    _patch_data_dirs(tmp_path, monkeypatch)

    respx.get(f"{BASE_URL}meetings").mock(
        return_value=httpx.Response(200, json=[{"meeting_key": 1, "year": 2024}])
    )
    respx.get(f"{BASE_URL}sessions").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"session_key": 1, "meeting_key": 1, "session_name": "Practice 1"},
                {"session_key": 2, "meeting_key": 1, "session_name": "Practice 2"},
            ],
        )
    )
    respx.get(f"{BASE_URL}drivers", params={"session_key": "1"}).mock(
        return_value=httpx.Response(404)
    )
    respx.get(f"{BASE_URL}drivers", params={"session_key": "2"}).mock(
        return_value=httpx.Response(200, json=[{"session_key": 2, "driver_number": 1}])
    )

    pipeline.run(years=[2024])

    assert not (tmp_path / "raw" / "drivers" / "1.json").exists()
    assert (tmp_path / "raw" / "drivers" / "2.json").exists()


@respx.mock
def test_run_skips_year_on_client_error_and_continues(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_data_dirs(tmp_path, monkeypatch)

    respx.get(f"{BASE_URL}meetings", params={"year": "2023"}).mock(return_value=httpx.Response(500))
    respx.get(f"{BASE_URL}meetings", params={"year": "2024"}).mock(
        return_value=httpx.Response(200, json=[{"meeting_key": 1, "year": 2024}])
    )
    respx.get(f"{BASE_URL}sessions").mock(return_value=httpx.Response(200, json=[]))

    pipeline.run(years=[2023, 2024])

    assert not (tmp_path / "raw" / "meetings" / "2023.json").exists()
    assert (tmp_path / "raw" / "meetings" / "2024.json").exists()


@respx.mock
def test_run_with_numeric_session_key_still_ingests_laps_and_session_result(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`session_key` chega tipado (int) do OpenF1; passar um `int` explícito não pode
    quebrar a comparação com `race_session_keys` (regressão: comparar int com str nunca
    dava match, então laps/session_result eram sempre pulados quando --session-key era
    informado)."""
    _patch_data_dirs(tmp_path, monkeypatch)

    respx.get(f"{BASE_URL}meetings").mock(
        return_value=httpx.Response(200, json=[{"meeting_key": 1219, "year": 2024}])
    )
    respx.get(f"{BASE_URL}sessions").mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9222, "meeting_key": 1219, "session_name": "Race"}]
        )
    )
    respx.get(f"{BASE_URL}drivers").mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9222, "driver_number": 1, "full_name": "Max Verstappen"}]
        )
    )
    respx.get(f"{BASE_URL}laps").mock(
        return_value=httpx.Response(
            200,
            json=[{"session_key": 9222, "driver_number": 1, "lap_number": 1, "lap_duration": 91.5}],
        )
    )
    respx.get(f"{BASE_URL}session_result").mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9222, "driver_number": 1, "position": 1}]
        )
    )

    pipeline.run(years=[2024], session_key=9222)

    assert (tmp_path / "raw" / "laps" / "9222.json").exists()
    assert (tmp_path / "raw" / "session_result" / "9222.json").exists()


@respx.mock
def test_run_with_latest_session_key_ingests_laps_and_session_result_for_race(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regressão: `--session-key latest` chegava como string `"latest"` em `_ingest_year`,
    nunca presente em `race_session_keys` (conjunto de `session_key` numéricos da lista de
    sessões do ano) — então `laps`/`session_result` eram sempre pulados, mesmo quando a
    sessão que `latest` resolve no servidor é uma corrida. A resolução dedicada via
    `sessions?session_key=latest` precisa acontecer para que a comparação funcione."""
    _patch_data_dirs(tmp_path, monkeypatch)

    respx.get(f"{BASE_URL}meetings").mock(
        return_value=httpx.Response(200, json=[{"meeting_key": 1219, "year": 2024}])
    )
    respx.get(f"{BASE_URL}sessions", params={"year": "2024"}).mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9230, "meeting_key": 1219, "session_name": "Race"}]
        )
    )
    respx.get(f"{BASE_URL}sessions", params={"session_key": "latest"}).mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9230, "meeting_key": 1219, "session_name": "Race"}]
        )
    )
    respx.get(f"{BASE_URL}drivers", params={"session_key": "latest"}).mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9230, "driver_number": 1, "full_name": "Max Verstappen"}]
        )
    )
    respx.get(f"{BASE_URL}laps", params={"session_key": "latest"}).mock(
        return_value=httpx.Response(
            200,
            json=[{"session_key": 9230, "driver_number": 1, "lap_number": 1, "lap_duration": 91.5}],
        )
    )
    respx.get(f"{BASE_URL}session_result", params={"session_key": "latest"}).mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9230, "driver_number": 1, "position": 1}]
        )
    )

    pipeline.run(years=[2024], session_key="latest")

    assert (tmp_path / "raw" / "drivers" / "9230.json").exists()
    assert (tmp_path / "raw" / "laps" / "9230.json").exists()
    assert (tmp_path / "raw" / "session_result" / "9230.json").exists()
    assert (tmp_path / "interim" / "laps" / "9230.parquet").exists()
    assert (tmp_path / "interim" / "session_result" / "9230.parquet").exists()


@respx.mock
def test_run_with_latest_session_key_skips_laps_and_session_result_for_non_race(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Quando `latest` resolve para uma sessão que não é corrida (ex.: treino em andamento),
    `laps`/`session_result` continuam sendo pulados — a correção não deve passar a ingerir
    tudo incondicionalmente para `latest`."""
    _patch_data_dirs(tmp_path, monkeypatch)

    respx.get(f"{BASE_URL}meetings").mock(
        return_value=httpx.Response(200, json=[{"meeting_key": 1219, "year": 2024}])
    )
    respx.get(f"{BASE_URL}sessions", params={"year": "2024"}).mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9210, "meeting_key": 1219, "session_name": "Practice 1"}]
        )
    )
    respx.get(f"{BASE_URL}sessions", params={"session_key": "latest"}).mock(
        return_value=httpx.Response(
            200,
            json=[{"session_key": 9210, "meeting_key": 1219, "session_name": "Practice 1"}],
        )
    )
    respx.get(f"{BASE_URL}drivers", params={"session_key": "latest"}).mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9210, "driver_number": 1, "full_name": "Max Verstappen"}]
        )
    )

    pipeline.run(years=[2024], session_key="latest")

    assert (tmp_path / "raw" / "drivers" / "9210.json").exists()
    assert not (tmp_path / "raw" / "laps").exists()
    assert not (tmp_path / "raw" / "session_result").exists()


def _client() -> pipeline.OpenF1Client:
    return pipeline.OpenF1Client(Settings(base_url=BASE_URL, timeout_seconds=5.0, max_retries=1))


def test_resolve_race_session_checks_membership_directly_for_numeric_key() -> None:
    with _client() as client:
        resolved_key, is_race = pipeline._resolve_race_session(client, 9222, {9222})

    assert resolved_key == 9222
    assert is_race is True


@respx.mock
def test_resolve_race_session_resolves_latest_to_real_key_and_race_flag() -> None:
    respx.get(f"{BASE_URL}sessions", params={"session_key": "latest"}).mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9230, "meeting_key": 1219, "session_name": "Race"}]
        )
    )

    with _client() as client:
        resolved_key, is_race = pipeline._resolve_race_session(client, "latest", set())

    assert resolved_key == 9230
    assert is_race is True


@respx.mock
def test_resolve_race_session_resolves_latest_to_non_race() -> None:
    respx.get(f"{BASE_URL}sessions", params={"session_key": "latest"}).mock(
        return_value=httpx.Response(
            200, json=[{"session_key": 9210, "meeting_key": 1219, "session_name": "Practice 1"}]
        )
    )

    with _client() as client:
        resolved_key, is_race = pipeline._resolve_race_session(client, "latest", set())

    assert resolved_key == 9210
    assert is_race is False


@respx.mock
def test_resolve_race_session_latest_with_empty_response_defaults_to_non_race() -> None:
    respx.get(f"{BASE_URL}sessions", params={"session_key": "latest"}).mock(
        return_value=httpx.Response(200, json=[])
    )

    with _client() as client:
        resolved_key, is_race = pipeline._resolve_race_session(client, "latest", set())

    assert resolved_key == "latest"
    assert is_race is False


def test_parse_session_key_converts_digits_to_int() -> None:
    assert pipeline._parse_session_key("9222") == 9222
    assert isinstance(pipeline._parse_session_key("9222"), int)


def test_parse_session_key_keeps_latest_keyword_as_string() -> None:
    assert pipeline._parse_session_key("latest") == "latest"


def test_main_parses_numeric_session_key_argument(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(pipeline, "run", lambda **kwargs: captured.update(kwargs) or None)

    pipeline.main(["--years", "2024", "--session-key", "9222"])

    assert captured["session_key"] == 9222
    assert isinstance(captured["session_key"], int)


@respx.mock
def test_run_routes_invalid_records_to_rejected(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_data_dirs(tmp_path, monkeypatch)

    respx.get(f"{BASE_URL}meetings").mock(
        return_value=httpx.Response(200, json=[{"year": 2024}])  # falta meeting_key
    )
    respx.get(f"{BASE_URL}sessions").mock(return_value=httpx.Response(200, json=[]))

    pipeline.run(years=[2024])

    assert (tmp_path / "rejected" / "meetings" / "2024.json").exists()
    assert not (tmp_path / "interim" / "meetings").exists()
