from __future__ import annotations

import math
from typing import Any

import pandas as pd
import pytest
import requests

from f1_project.dashboard import helpers


@pytest.fixture(autouse=True)
def _clear_caches() -> None:
    """Evita que uma resposta cacheada de um teste vaze para o próximo."""
    helpers.api_get.clear()
    helpers.circuit_image_data.clear()
    helpers.season_race_results.clear()
    yield
    helpers.api_get.clear()
    helpers.circuit_image_data.clear()
    helpers.season_race_results.clear()


# --- seconds_to_lap -----------------------------------------------------------------


def test_seconds_to_lap_formats_minutes_and_seconds() -> None:
    assert helpers.seconds_to_lap(83.456) == "1:23.456"


def test_seconds_to_lap_handles_none_and_nan() -> None:
    assert helpers.seconds_to_lap(None) == "—"
    assert helpers.seconds_to_lap(float("nan")) == "—"


# --- asset_slug -----------------------------------------------------------------------


def test_asset_slug_removes_accents_and_punctuation() -> None:
    assert helpers.asset_slug("São Paulo") == "sao-paulo"
    assert helpers.asset_slug("Spa-Francorchamps") == "spa-francorchamps"
    assert helpers.asset_slug("  Multiple   Spaces!! ") == "multiple-spaces"


# --- circuit_image_data ---------------------------------------------------------------


def test_circuit_image_data_returns_data_uri_for_known_circuit() -> None:
    result = helpers.circuit_image_data("Monza")

    assert result is not None
    assert result.startswith("data:image/png;base64,")


def test_circuit_image_data_falls_back_to_location() -> None:
    result = helpers.circuit_image_data("Circuito Desconhecido", "Monza")

    assert result is not None
    assert result.startswith("data:image/png;base64,")


def test_circuit_image_data_returns_none_when_no_asset_matches() -> None:
    assert helpers.circuit_image_data("Circuito Totalmente Inexistente") is None


# --- pace_axis_ticks --------------------------------------------------------------------


def test_pace_axis_ticks_returns_empty_for_empty_series() -> None:
    ticks, labels = helpers.pace_axis_ticks(pd.Series(dtype=float))

    assert ticks == []
    assert labels == []


def test_pace_axis_ticks_builds_ticks_every_step() -> None:
    ticks, labels = helpers.pace_axis_ticks(pd.Series([61.0, 90.0, 125.0]))

    assert ticks == [60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125]
    assert labels[0] == "1:00"
    assert labels[-1] == "2:05"


# --- chart_style -----------------------------------------------------------------------


def test_chart_style_applies_title_height_and_legend() -> None:
    import plotly.graph_objects as go

    fig = helpers.chart_style(go.Figure(), "Ritmo", height=300, show_legend=True)

    assert fig.layout.title.text == "Ritmo"
    assert fig.layout.height == 300
    assert fig.layout.showlegend is True
    assert fig.layout.paper_bgcolor == helpers.PANEL


# --- country_flag ----------------------------------------------------------------------


def test_country_flag_maps_alpha3_country_code() -> None:
    flag = helpers.country_flag("BRA")

    assert "flagcdn.com/w40/br.png" in flag


def test_country_flag_prefers_driver_acronym_override() -> None:
    flag = helpers.country_flag("USA", driver_acronym="HAM")

    assert "flagcdn.com/w40/gb.png" in flag


def test_country_flag_falls_back_when_code_unresolvable() -> None:
    flag = helpers.country_flag("ZZZ")

    assert "driver-flag-fallback" in flag


# --- recent_results_html ----------------------------------------------------------------


def test_recent_results_html_returns_placeholder_when_empty() -> None:
    html = helpers.recent_results_html(None)

    assert "—" in html
    assert "recent-win" not in html


def test_recent_results_html_marks_wins_and_dnf() -> None:
    html = helpers.recent_results_html(["P5", "V", "DNF"])

    assert "recent-win" in html
    assert "recent-dnf" in html
    assert ">V<" in html


# --- team_identity_html -----------------------------------------------------------------


def test_team_identity_html_uses_initials_fallback_when_no_logo() -> None:
    driver = pd.Series(
        {"team_name": "Red Bull Racing", "team_colour": "3671C6", "driver_number": 1}
    )

    html = helpers.team_identity_html(driver)

    assert "#1" in html
    assert "background:#3671C6" in html
    assert "RB" in html


def test_team_identity_html_falls_back_to_default_colour_on_invalid_hex() -> None:
    driver = pd.Series({"team_name": "Equipe X", "team_colour": "not-a-color", "driver_number": 44})

    html = helpers.team_identity_html(driver)

    assert "background:#555B66" in html


# --- championship_line -------------------------------------------------------------------


def test_championship_line_handles_missing_standing() -> None:
    assert "Dados indisponíveis" in helpers.championship_line(None)
    assert "Dados indisponíveis" in helpers.championship_line(pd.Series(dtype=object))


def test_championship_line_reports_gained_positions() -> None:
    standing = pd.Series({"points_current": 87.0, "position_current": 2, "position_start": 4})

    html = helpers.championship_line(standing)

    assert "P2" in html
    assert "87 pts" in html
    assert "ganhou 2 posições" in html


def test_championship_line_reports_lost_positions() -> None:
    standing = pd.Series({"points_current": 10.0, "position_current": 6, "position_start": 4})

    assert "perdeu 2 posições" in helpers.championship_line(standing)


def test_championship_line_reports_same_position() -> None:
    standing = pd.Series({"points_current": 10.0, "position_current": 4, "position_start": 4})

    assert "manteve" in helpers.championship_line(standing)


def test_championship_line_handles_missing_start_position() -> None:
    standing = pd.Series({"points_current": 10.0, "position_current": 4, "position_start": None})

    assert "posição anterior indisponível" in helpers.championship_line(standing)


# --- driver_card -----------------------------------------------------------------------


def test_driver_card_renders_role_and_name() -> None:
    driver = pd.Series(
        {
            "full_name": "Max Verstappen",
            "name_acronym": "VER",
            "country_code": "NED",
            "headshot_url": None,
            "team_name": "Red Bull Racing",
            "team_colour": "3671C6",
            "driver_number": 1,
        }
    )

    html = helpers.driver_card(driver, "Piloto A", helpers.DRIVER_A_COLOR)

    assert "Piloto A" in html
    assert "Max Verstappen" in html
    assert "VER" in html


# --- stat_card -----------------------------------------------------------------------


def test_stat_card_renders_icon_label_and_value() -> None:
    html = helpers.stat_card("🏁", "Voltas", "58")

    assert "🏁" in html
    assert "Voltas" in html
    assert "58" in html


# --- position_by_lap --------------------------------------------------------------------


def test_position_by_lap_returns_empty_when_no_data() -> None:
    empty = pd.DataFrame(columns=["driver_number", "date_start", "lap_number"])
    result = helpers.position_by_lap(1, empty, empty.rename(columns={"date_start": "date"}), 3)

    assert list(result.columns) == ["lap_number", "position"]
    assert result.empty


def test_position_by_lap_uses_latest_known_position_per_lap() -> None:
    laps = pd.DataFrame(
        {
            "driver_number": [1, 1, 1],
            "date_start": [
                "2024-01-01 00:01:00",
                "2024-01-01 00:02:00",
                "2024-01-01 00:03:00",
            ],
            "lap_number": [1, 2, 3],
        }
    )
    positions = pd.DataFrame(
        {
            "driver_number": [1, 1],
            "date": ["2024-01-01 00:00:30", "2024-01-01 00:01:30"],
            "position": [5, 3],
        }
    )

    result = helpers.position_by_lap(1, laps, positions, chart_last_lap=3)

    assert result["lap_number"].tolist() == [1, 2, 3]
    assert result["position"].tolist() == [5, 3, 3]


def test_position_by_lap_fills_laps_without_recorded_events() -> None:
    laps = pd.DataFrame(
        {
            "driver_number": [1, 1],
            "date_start": ["2024-01-01 00:01:00", "2024-01-01 00:03:00"],
            "lap_number": [1, 3],
        }
    )
    positions = pd.DataFrame(
        {
            "driver_number": [1],
            "date": ["2024-01-01 00:00:30"],
            "position": [7],
        }
    )

    result = helpers.position_by_lap(1, laps, positions, chart_last_lap=5)

    assert result["lap_number"].tolist() == [1, 2, 3, 4, 5]
    assert result["position"].tolist() == [7, 7, 7, 7, 7]


# --- safe_max_speed --------------------------------------------------------------------


def test_safe_max_speed_returns_none_for_empty_or_missing_column() -> None:
    assert helpers.safe_max_speed(pd.DataFrame()) is None
    assert helpers.safe_max_speed(pd.DataFrame({"other": [1, 2]})) is None


def test_safe_max_speed_returns_maximum() -> None:
    assert helpers.safe_max_speed(pd.DataFrame({"speed": [280, 310, 295]})) == 310.0


# --- driver_summary --------------------------------------------------------------------


def test_driver_summary_computes_best_lap_speed_pits_and_positions() -> None:
    laps = pd.DataFrame({"driver_number": [1, 1], "lap_duration": [91.234, 89.876]})
    car_data = pd.DataFrame({"speed": [300, 320]})
    pits = pd.DataFrame({"driver_number": [1, 1]})
    positions = pd.DataFrame(
        {"driver_number": [1, 1], "date": ["2024-01-01", "2024-01-02"], "position": [3, 1]}
    )
    result = pd.DataFrame({"driver_number": [1], "grid_position": [5], "position": [1]})

    summary = helpers.driver_summary(1, car_data, laps, pits, positions, result)

    assert summary["best_lap"] == helpers.seconds_to_lap(89.876)
    assert summary["speed"] == "320 km/h"
    assert summary["pits"] == "2"
    assert summary["grid_finish"] == "P5 → P1"
    assert summary["gained"] == "+4"


def test_driver_summary_defaults_when_no_data_available() -> None:
    empty = pd.DataFrame()

    summary = helpers.driver_summary(1, empty, empty, empty, empty, empty)

    assert summary == {
        "best_lap": "—",
        "speed": "—",
        "pits": "0",
        "grid_finish": "—",
        "gained": "—",
    }


# --- summary_rows ----------------------------------------------------------------------


def test_summary_rows_escapes_label_and_value() -> None:
    html = helpers.summary_rows([("<Label>", "<Value>")])

    assert "&lt;Label&gt;" in html
    assert "&lt;Value&gt;" in html


# --- best_sector_times -------------------------------------------------------------------


def test_best_sector_times_returns_minimum_per_sector() -> None:
    laps = pd.DataFrame(
        {
            "driver_number": [1, 1, 2],
            "duration_sector_1": [30.1, 29.8, 31.0],
            "duration_sector_2": [28.5, None, 27.0],
            "duration_sector_3": [25.0, 24.9, 26.0],
        }
    )

    best = helpers.best_sector_times(1, laps)

    assert best[1] == 29.8
    assert best[2] == 28.5
    assert best[3] == 24.9


# --- detect_retirements ------------------------------------------------------------------


def test_detect_retirements_returns_empty_without_lap_data() -> None:
    assert helpers.detect_retirements((1, 2), pd.DataFrame(), pd.DataFrame()) == {}


def test_detect_retirements_flags_confirmed_dnf() -> None:
    laps = pd.DataFrame({"driver_number": [1, 1, 2], "lap_number": [1, 2, 1]})
    session_result = pd.DataFrame({"driver_number": [1, 2], "dnf": [True, False]})

    retirements = helpers.detect_retirements((1, 2), laps, session_result)

    assert retirements == {1: 2}


# --- season_race_results -----------------------------------------------------------------


def test_season_race_results_returns_empty_when_no_meetings_or_sessions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(helpers, "api_get", lambda endpoint, **params: pd.DataFrame())

    results, meetings = helpers.season_race_results(2024)

    assert results.empty
    assert meetings.empty


def test_season_race_results_concatenates_results_per_race(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    meetings_df = pd.DataFrame({"meeting_key": [1], "country_name": ["Brazil"]})
    sessions_df = pd.DataFrame(
        {
            "session_key": [10, 11],
            "session_name": ["Race", "Qualifying"],
            "date_start": ["2024-11-03", "2024-11-02"],
        }
    )
    result_df = pd.DataFrame({"driver_number": [1], "position": [1]})

    def fake_api_get(endpoint: str, **params: Any) -> pd.DataFrame:
        if endpoint == "meetings":
            return meetings_df
        if endpoint == "sessions":
            return sessions_df
        if endpoint == "session_result":
            assert params["session_key"] == 10
            return result_df
        raise AssertionError(f"unexpected endpoint {endpoint}")

    monkeypatch.setattr(helpers, "api_get", fake_api_get)

    results, meetings = helpers.season_race_results(2024)

    assert results["race_session_key"].tolist() == [10]
    assert meetings.equals(meetings_df)


# --- result_cell_style -------------------------------------------------------------------


def test_result_cell_style_marks_dnf_dns_dsq() -> None:
    for status in ("DNF", "DNS", "DSQ"):
        assert "FF7785" in helpers.result_cell_style(None, status)


def test_result_cell_style_handles_missing_position() -> None:
    assert helpers.MUTED in helpers.result_cell_style(None, "—")
    assert helpers.MUTED in helpers.result_cell_style(float("nan"), "—")


@pytest.mark.parametrize(
    ("position", "expected_fragment"),
    [(1, "FFE27A"), (3, "FFE27A"), (5, "65E6B7"), (6, "65E6B7"), (8, "75BEFF"), (15, "B5BDCA")],
)
def test_result_cell_style_bands_by_position(position: int, expected_fragment: str) -> None:
    assert expected_fragment in helpers.result_cell_style(float(position), f"P{position}")


# --- result_flag -----------------------------------------------------------------------


def test_result_flag_interprets_present_and_missing_values() -> None:
    assert helpers.result_flag(True) is True
    assert helpers.result_flag(False) is False
    assert helpers.result_flag(None) is False
    assert helpers.result_flag(float("nan")) is False


# --- api_get ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(
        self, status_code: int, json_data: Any = None, headers: dict[str, str] | None = None
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.headers = headers or {}

    def json(self) -> Any:
        return self._json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


def test_api_get_returns_dataframe_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        helpers.requests,
        "get",
        lambda *args, **kwargs: _FakeResponse(200, [{"meeting_key": 1}]),
    )

    result = helpers.api_get("meetings", year=2024)

    assert result.to_dict("records") == [{"meeting_key": 1}]


def test_api_get_returns_empty_dataframe_on_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(helpers.requests, "get", lambda *args, **kwargs: _FakeResponse(404))

    result = helpers.api_get("sessions", session_key=999)

    assert result.empty


def test_api_get_omits_none_params(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_get(url: str, params: dict[str, Any], **kwargs: Any) -> _FakeResponse:
        captured["params"] = params
        return _FakeResponse(200, [])

    monkeypatch.setattr(helpers.requests, "get", fake_get)

    helpers.api_get("drivers", session_key=1, driver_number=None)

    assert "driver_number" not in captured["params"]
    assert captured["params"]["session_key"] == 1


def test_api_get_retries_on_transient_network_error_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(helpers.time, "sleep", lambda _seconds: None)
    calls = {"count": 0}

    def flaky_get(*args: Any, **kwargs: Any) -> _FakeResponse:
        calls["count"] += 1
        if calls["count"] < 2:
            raise requests.ConnectionError("boom")
        return _FakeResponse(200, [{"driver_number": 1}])

    monkeypatch.setattr(helpers.requests, "get", flaky_get)

    result = helpers.api_get("drivers", session_key=1)

    assert result.to_dict("records") == [{"driver_number": 1}]
    assert calls["count"] == 2


def test_api_get_raises_after_exhausting_retries_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(helpers.time, "sleep", lambda _seconds: None)

    def always_fails(*args: Any, **kwargs: Any) -> _FakeResponse:
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(helpers.requests, "get", always_fails)

    with pytest.raises(requests.ConnectionError):
        helpers.api_get("laps", session_key=1)


def test_api_get_retries_on_rate_limit_honoring_retry_after(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr(helpers.time, "sleep", lambda seconds: sleep_calls.append(seconds))
    calls = {"count": 0}

    def rate_limited_get(*args: Any, **kwargs: Any) -> _FakeResponse:
        calls["count"] += 1
        if calls["count"] == 1:
            return _FakeResponse(429, headers={"Retry-After": "3"})
        return _FakeResponse(200, [{"stint_number": 1}])

    monkeypatch.setattr(helpers.requests, "get", rate_limited_get)

    result = helpers.api_get("stints", session_key=1)

    assert result.to_dict("records") == [{"stint_number": 1}]
    assert sleep_calls == [3.0]


def test_api_get_raises_on_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(helpers.requests, "get", lambda *args, **kwargs: _FakeResponse(500))

    with pytest.raises(requests.HTTPError):
        helpers.api_get("weather", session_key=1)


def test_pace_axis_ticks_step_seconds_is_configurable() -> None:
    ticks, _labels = helpers.pace_axis_ticks(pd.Series([10.0, 20.0]), step_seconds=10)

    assert ticks == [10, 20]
    assert math.isclose(ticks[1] - ticks[0], 10)
