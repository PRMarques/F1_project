"""Funções de conveniência do dashboard sobre a leitura da camada Silver."""

from __future__ import annotations

import pandas as pd

from f1_project.load.silver import read_silver


def load_meetings() -> pd.DataFrame:
    return read_silver("meetings")


def load_sessions() -> pd.DataFrame:
    return read_silver("sessions")


def load_drivers() -> pd.DataFrame:
    return read_silver("drivers")
