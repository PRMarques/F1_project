"""Persistência da camada Bronze: resposta JSON crua da API, por endpoint e lote."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from f1_project.config import RAW_DATA_DIR

logger = logging.getLogger(__name__)


def save_raw_json(endpoint: str, batch_key: str, payload: list[dict[str, Any]]) -> Path:
    """Salva `payload` sem alteração em `data/raw/<endpoint>/<batch_key>.json`.

    `batch_key` identifica o lote da requisição (ex.: `session_key`, `meeting_key`
    ou o filtro usado, como o `year`), não uma chave de registro individual.
    """
    endpoint_dir = RAW_DATA_DIR / endpoint
    endpoint_dir.mkdir(parents=True, exist_ok=True)
    output_path = endpoint_dir / f"{batch_key}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Bronze: %s registros gravados em %s", len(payload), output_path)
    return output_path
