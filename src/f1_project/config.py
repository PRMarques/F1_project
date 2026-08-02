"""Configurações centralizadas do pipeline: URL base, timeouts, retries e caminhos de dados."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REJECTED_DATA_DIR = DATA_DIR / "rejected"

DEFAULT_BASE_URL = "https://api.openf1.org/v1/"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RETRIES = 3


@dataclass(frozen=True)
class Settings:
    """Configuração de acesso à API OpenF1, sobrescrevível por variáveis de ambiente."""

    base_url: str = DEFAULT_BASE_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            base_url=os.getenv("OPENF1_BASE_URL", DEFAULT_BASE_URL),
            timeout_seconds=float(
                os.getenv("OPENF1_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
            ),
            max_retries=int(os.getenv("OPENF1_MAX_RETRIES", str(DEFAULT_MAX_RETRIES))),
        )


settings = Settings.from_env()
