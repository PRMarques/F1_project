"""Schemas Pydantic por entidade: tipos, campos obrigatórios e chave natural.

Campos que identificam o registro (chave natural) são obrigatórios; os demais são
opcionais porque a OpenF1 pode retorná-los nulos ou omiti-los sem invalidar o registro.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MeetingSchema(BaseModel):
    """Um fim de semana de GP ou teste. Chave natural: `meeting_key`."""

    meeting_key: int
    meeting_name: str | None = None
    meeting_official_name: str | None = None
    location: str | None = None
    country_key: int | None = None
    country_code: str | None = None
    country_name: str | None = None
    circuit_key: int | None = None
    circuit_short_name: str | None = None
    date_start: datetime | None = None
    gmt_offset: str | None = None
    year: int | None = None


class SessionSchema(BaseModel):
    """Uma sessão (treino, classificação, sprint, corrida). Chave natural: `session_key`."""

    session_key: int
    meeting_key: int
    session_name: str | None = None
    session_type: str | None = None
    date_start: datetime | None = None
    date_end: datetime | None = None
    gmt_offset: str | None = None
    location: str | None = None
    country_key: int | None = None
    country_code: str | None = None
    country_name: str | None = None
    circuit_key: int | None = None
    circuit_short_name: str | None = None
    year: int | None = None


class DriverSchema(BaseModel):
    """Um piloto participante de uma sessão. Chave natural: (`session_key`, `driver_number`)."""

    session_key: int
    meeting_key: int | None = None
    driver_number: int
    broadcast_name: str | None = None
    full_name: str | None = None
    name_acronym: str | None = None
    team_name: str | None = None
    team_colour: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    headshot_url: str | None = None
    country_code: str | None = None


class LapSchema(BaseModel):
    """Uma volta de um piloto. Chave natural: (`session_key`, `driver_number`, `lap_number`)."""

    session_key: int
    meeting_key: int | None = None
    driver_number: int
    lap_number: int
    lap_duration: float | None = None
    is_pit_out_lap: bool | None = None
    duration_sector_1: float | None = None
    duration_sector_2: float | None = None
    duration_sector_3: float | None = None
    date_start: datetime | None = None


class SessionResultSchema(BaseModel):
    """Resultado final de um piloto na sessão. Chave natural: (`session_key`, `driver_number`)."""

    session_key: int
    meeting_key: int | None = None
    driver_number: int
    position: int | None = None
    number_of_laps: int | None = None
    points: float | None = None
    dnf: bool | None = None
    dns: bool | None = None
    dsq: bool | None = None
