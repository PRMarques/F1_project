"""Roteamento de registros que falharam validação para a área de rejeitados."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from f1_project.config import REJECTED_DATA_DIR

logger = logging.getLogger(__name__)


def save_rejected(
    endpoint: str, batch_key: str, rejected_records: list[dict[str, Any]]
) -> Path | None:
    """Salva registros rejeitados (com motivo) em `data/rejected/<endpoint>/<batch_key>.json`.

    Retorna `None` sem gravar arquivo quando não há registros rejeitados.
    """
    if not rejected_records:
        return None

    endpoint_dir = REJECTED_DATA_DIR / endpoint
    endpoint_dir.mkdir(parents=True, exist_ok=True)
    output_path = endpoint_dir / f"{batch_key}.json"
    output_path.write_text(
        json.dumps(rejected_records, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    logger.warning("Rejeitados: %s registros gravados em %s", len(rejected_records), output_path)
    return output_path
