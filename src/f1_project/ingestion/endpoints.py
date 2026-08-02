"""Funções finas por endpoint ativo da OpenF1, delegando ao client genérico."""

from __future__ import annotations

from typing import Any

from f1_project.ingestion.client import OpenF1Client


def get_meetings(client: OpenF1Client, **filters: Any) -> list[dict[str, Any]]:
    """Busca fins de semana de GP/teste (`meeting_key`, `year`, `country_name`, ...)."""
    return client.get("meetings", **filters)


def get_sessions(client: OpenF1Client, **filters: Any) -> list[dict[str, Any]]:
    """Busca sessões (treino, classificação, corrida) por `year`, `country_name`, etc."""
    return client.get("sessions", **filters)


def get_drivers(client: OpenF1Client, **filters: Any) -> list[dict[str, Any]]:
    """Busca pilotos participantes de uma sessão (`session_key`, `driver_number`)."""
    return client.get("drivers", **filters)


def get_laps(client: OpenF1Client, **filters: Any) -> list[dict[str, Any]]:
    """Busca voltas de uma sessão (`session_key`, `driver_number`, `lap_number`)."""
    return client.get("laps", **filters)


def get_session_result(client: OpenF1Client, **filters: Any) -> list[dict[str, Any]]:
    """Busca a classificação final de uma sessão (`session_key`, `driver_number`, `position`)."""
    return client.get("session_result", **filters)
