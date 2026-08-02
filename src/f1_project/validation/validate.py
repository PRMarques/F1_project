"""Validação genérica de registros crus contra um schema Pydantic."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


def validate_records[SchemaT: BaseModel](
    records: list[dict[str, Any]], schema: type[SchemaT]
) -> tuple[list[SchemaT], list[dict[str, Any]]]:
    """Valida `records` contra `schema`.

    Retorna `(validos, rejeitados)`, onde cada item rejeitado é um dict com o
    registro original em `record` e o motivo da falha em `reason`.
    """
    valid: list[SchemaT] = []
    rejected: list[dict[str, Any]] = []

    for record in records:
        try:
            valid.append(schema.model_validate(record))
        except ValidationError as exc:
            rejected.append({"record": record, "reason": str(exc)})

    logger.info(
        "Validação %s: %s de %s registros válidos (%s rejeitados)",
        schema.__name__,
        len(valid),
        len(records),
        len(rejected),
    )
    return valid, rejected
