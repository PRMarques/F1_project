"""Deduplicação pela chave natural de cada entidade."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence

from f1_project.validation.schemas import (
    DriverSchema,
    LapSchema,
    MeetingSchema,
    SessionResultSchema,
    SessionSchema,
)

logger = logging.getLogger(__name__)

NATURAL_KEYS: dict[type, Callable[[object], tuple]] = {
    MeetingSchema: lambda record: (record.meeting_key,),
    SessionSchema: lambda record: (record.session_key,),
    DriverSchema: lambda record: (record.session_key, record.driver_number),
    LapSchema: lambda record: (record.session_key, record.driver_number, record.lap_number),
    SessionResultSchema: lambda record: (record.session_key, record.driver_number),
}


def deduplicate[SchemaT](
    records: Sequence[SchemaT], key_fn: Callable[[SchemaT], tuple]
) -> list[SchemaT]:
    """Remove duplicatas mantendo o último registro observado por chave natural."""
    deduped: dict[tuple, SchemaT] = {}
    for record in records:
        deduped[key_fn(record)] = record

    removed = len(records) - len(deduped)
    if removed:
        logger.info("Deduplicação: %s registros duplicados removidos", removed)
    return list(deduped.values())
