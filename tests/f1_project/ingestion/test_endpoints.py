from __future__ import annotations

from unittest.mock import MagicMock

from f1_project.ingestion import endpoints


def test_get_meetings_delegates_to_client() -> None:
    client = MagicMock()
    client.get.return_value = [{"meeting_key": 1219}]

    result = endpoints.get_meetings(client, year=2024)

    client.get.assert_called_once_with("meetings", year=2024)
    assert result == [{"meeting_key": 1219}]


def test_get_sessions_delegates_to_client() -> None:
    client = MagicMock()
    client.get.return_value = []

    result = endpoints.get_sessions(client, session_key="latest")

    client.get.assert_called_once_with("sessions", session_key="latest")
    assert result == []


def test_get_drivers_delegates_to_client() -> None:
    client = MagicMock()
    client.get.return_value = [{"driver_number": 1}]

    result = endpoints.get_drivers(client, session_key=9222)

    client.get.assert_called_once_with("drivers", session_key=9222)
    assert result == [{"driver_number": 1}]
