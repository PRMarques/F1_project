"""Escrita da camada Silver: parquet tipado, particionado pela chave natural de agrupamento."""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel

from f1_project.config import INTERIM_DATA_DIR

logger = logging.getLogger(__name__)


def write_silver(records: list[BaseModel], entity: str, partition_field: str) -> list[Path]:
    """Grava `records` em `data/interim/<entity>/<partition_field>.parquet`.

    Cada valor distinto de `partition_field` vira seu próprio arquivo, sobrescrito a
    cada execução — reprocessar uma sessão/meeting substitui só a partição correspondente,
    sem duplicar dados de outras partições (escrita idempotente).
    """
    if not records:
        logger.info("Silver: nenhum registro válido para '%s', nada gravado", entity)
        return []

    groups: dict[Any, list[BaseModel]] = defaultdict(list)
    for record in records:
        groups[getattr(record, partition_field)].append(record)

    entity_dir = INTERIM_DATA_DIR / entity
    entity_dir.mkdir(parents=True, exist_ok=True)

    written_paths: list[Path] = []
    for partition_value, group_records in groups.items():
        output_path = entity_dir / f"{partition_value}.parquet"
        df = pd.DataFrame([record.model_dump() for record in group_records])
        df.to_parquet(output_path, engine="fastparquet", index=False)
        written_paths.append(output_path)
        logger.info("Silver: %s registros gravados em %s", len(df), output_path)

    return written_paths


def read_silver(entity: str) -> pd.DataFrame:
    """Lê e concatena todas as partições parquet de `data/interim/<entity>/`.

    Retorna um DataFrame vazio se a entidade ainda não tiver sido ingerida.
    """
    entity_dir = INTERIM_DATA_DIR / entity
    if not entity_dir.is_dir():
        return pd.DataFrame()

    parquet_files = sorted(entity_dir.glob("*.parquet"))
    if not parquet_files:
        return pd.DataFrame()

    return pd.concat(
        [pd.read_parquet(path, engine="fastparquet") for path in parquet_files],
        ignore_index=True,
    )
