"""Agregações da camada Gold: voltas mais rápidas por circuito e pódio por corrida.

As tabelas Gold são recalculadas por completo a cada execução, a partir de toda a
Silver acumulada (não só do lote da última ingestão) — volume ainda modesto o
suficiente para não justificar um cálculo incremental.
"""

from __future__ import annotations

import logging

import pandas as pd

from f1_project.config import PROCESSED_DATA_DIR
from f1_project.load.silver import read_silver

logger = logging.getLogger(__name__)

FASTEST_LAPS_PER_CIRCUIT = 5
PODIUM_POSITIONS = 3
RACE_SESSION_NAME = "Race"

FASTEST_LAPS_FILENAME = "fastest_laps_by_circuit.parquet"
PODIUM_FILENAME = "podium_by_race.parquet"

_DRIVER_COLUMNS = ["session_key", "driver_number", "full_name", "team_name"]


def _with_driver_info(df: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    if drivers.empty:
        return df
    driver_cols = drivers[_DRIVER_COLUMNS].drop_duplicates(subset=["session_key", "driver_number"])
    return df.merge(driver_cols, on=["session_key", "driver_number"], how="left")


def compute_fastest_laps_by_circuit(
    laps: pd.DataFrame,
    sessions: pd.DataFrame,
    meetings: pd.DataFrame,
    drivers: pd.DataFrame,
    top_n: int = FASTEST_LAPS_PER_CIRCUIT,
) -> pd.DataFrame:
    """As `top_n` voltas mais rápidas de cada circuito, entre as corridas ingeridas.

    Considera apenas voltas com `lap_duration` válido (> 0), o que já exclui voltas
    de entrada/saída de pit e voltas sem tempo registrado. O circuito é resolvido via
    `session_key` -> `sessions.meeting_key` -> `meetings` — a OpenF1 não garante
    `meeting_key` diretamente em `laps`.
    """
    if laps.empty or sessions.empty or meetings.empty:
        return pd.DataFrame()

    valid_laps = laps[laps["lap_duration"].notna() & (laps["lap_duration"] > 0)]
    if valid_laps.empty:
        return pd.DataFrame()

    valid_laps = valid_laps.drop(columns=["meeting_key"], errors="ignore")
    merged = valid_laps.merge(
        sessions[["session_key", "meeting_key"]], on="session_key", how="left"
    )
    merged = merged.merge(
        meetings[["meeting_key", "circuit_short_name", "country_name", "year"]],
        on="meeting_key",
        how="left",
    )
    merged = _with_driver_info(merged, drivers)

    return (
        merged.sort_values("lap_duration")
        .groupby("circuit_short_name", group_keys=False)
        .head(top_n)
        .sort_values(["circuit_short_name", "lap_duration"])
        .reset_index(drop=True)
    )


def compute_podium_by_race(
    session_result: pd.DataFrame,
    sessions: pd.DataFrame,
    meetings: pd.DataFrame,
    drivers: pd.DataFrame,
) -> pd.DataFrame:
    """Top 3 posições finais (pódio) de cada sessão de corrida (`Race`) ingerida."""
    if session_result.empty or sessions.empty:
        return pd.DataFrame()

    race_sessions = sessions[sessions["session_name"] == RACE_SESSION_NAME]
    if race_sessions.empty:
        return pd.DataFrame()

    podium = session_result[session_result["session_key"].isin(race_sessions["session_key"])]
    podium = podium[podium["position"].notna() & (podium["position"] <= PODIUM_POSITIONS)]
    if podium.empty:
        return pd.DataFrame()

    podium = podium.drop(columns=["meeting_key"], errors="ignore")
    podium = podium.merge(
        race_sessions[["session_key", "meeting_key", "session_name"]],
        on="session_key",
        how="left",
    )
    if not meetings.empty:
        podium = podium.merge(
            meetings[["meeting_key", "meeting_name", "year", "country_name"]],
            on="meeting_key",
            how="left",
        )
    podium = _with_driver_info(podium, drivers)

    return podium.sort_values(["meeting_key", "position"]).reset_index(drop=True)


def build_gold_tables() -> None:
    """Lê a Silver completa, recalcula as tabelas Gold e grava em `data/processed/`."""
    sessions = read_silver("sessions")
    meetings = read_silver("meetings")
    drivers = read_silver("drivers")

    fastest_laps = compute_fastest_laps_by_circuit(read_silver("laps"), sessions, meetings, drivers)
    podium = compute_podium_by_race(read_silver("session_result"), sessions, meetings, drivers)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not fastest_laps.empty:
        output_path = PROCESSED_DATA_DIR / FASTEST_LAPS_FILENAME
        fastest_laps.to_parquet(output_path, engine="fastparquet", index=False)
        logger.info("Gold: %s voltas gravadas em %s", len(fastest_laps), output_path)

    if not podium.empty:
        output_path = PROCESSED_DATA_DIR / PODIUM_FILENAME
        podium.to_parquet(output_path, engine="fastparquet", index=False)
        logger.info("Gold: %s posições de pódio gravadas em %s", len(podium), output_path)


def read_fastest_laps_by_circuit() -> pd.DataFrame:
    path = PROCESSED_DATA_DIR / FASTEST_LAPS_FILENAME
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path, engine="fastparquet")


def read_podium_by_race() -> pd.DataFrame:
    path = PROCESSED_DATA_DIR / PODIUM_FILENAME
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path, engine="fastparquet")
