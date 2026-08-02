from __future__ import annotations

import httpx
import pytest
import respx

from f1_project.config import Settings
from f1_project.ingestion.client import OpenF1Client, OpenF1ClientError

BASE_URL = "https://api.openf1.org/v1/"


def _settings(max_retries: int = 3) -> Settings:
    return Settings(base_url=BASE_URL, timeout_seconds=5.0, max_retries=max_retries)


@respx.mock
def test_get_returns_parsed_json() -> None:
    route = respx.get(f"{BASE_URL}meetings").mock(
        return_value=httpx.Response(200, json=[{"meeting_key": 1219}])
    )
    client = OpenF1Client(settings=_settings())

    result = client.get("meetings", year=2024)

    assert result == [{"meeting_key": 1219}]
    assert route.calls.last.request.url.params["year"] == "2024"


@respx.mock
def test_get_omits_none_filters() -> None:
    route = respx.get(f"{BASE_URL}sessions").mock(return_value=httpx.Response(200, json=[]))
    client = OpenF1Client(settings=_settings())

    result = client.get("sessions", year=2024, country_name=None)

    assert result == []
    assert "country_name" not in route.calls.last.request.url.params


@respx.mock
def test_get_raises_on_client_error_without_retry() -> None:
    route = respx.get(f"{BASE_URL}drivers").mock(return_value=httpx.Response(404))
    client = OpenF1Client(settings=_settings())

    with pytest.raises(OpenF1ClientError):
        client.get("drivers")

    assert route.call_count == 1


@respx.mock
def test_get_retries_on_server_error_then_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("f1_project.ingestion.client.time.sleep", lambda _seconds: None)
    route = respx.get(f"{BASE_URL}laps").mock(return_value=httpx.Response(500))
    client = OpenF1Client(settings=_settings(max_retries=3))

    with pytest.raises(OpenF1ClientError):
        client.get("laps")

    assert route.call_count == 3


@respx.mock
def test_get_recovers_after_transient_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("f1_project.ingestion.client.time.sleep", lambda _seconds: None)
    respx.get(f"{BASE_URL}stints").mock(
        side_effect=[httpx.Response(500), httpx.Response(200, json=[{"stint_number": 1}])]
    )
    client = OpenF1Client(settings=_settings(max_retries=3))

    result = client.get("stints")

    assert result == [{"stint_number": 1}]


@respx.mock
def test_get_retries_on_rate_limit_honoring_retry_after(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr(
        "f1_project.ingestion.client.time.sleep", lambda seconds: sleep_calls.append(seconds)
    )
    respx.get(f"{BASE_URL}drivers").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "7"}),
            httpx.Response(200, json=[{"driver_number": 1}]),
        ]
    )
    client = OpenF1Client(settings=_settings(max_retries=3))

    result = client.get("drivers")

    assert result == [{"driver_number": 1}]
    assert sleep_calls == [7.0]


def test_context_manager_returns_client_and_closes() -> None:
    with OpenF1Client(settings=_settings()) as client:
        assert isinstance(client, OpenF1Client)
