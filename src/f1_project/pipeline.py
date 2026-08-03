"""Orquestrador: ingestão ponta a ponta de meetings, sessions, drivers, laps e session_result.

`laps` e `session_result` só são ingeridos para sessões de corrida (`session_name ==
"Race"`) — são as únicas relevantes para as agregações Gold hoje (voltas mais rápidas
por circuito, pódio por corrida).
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Sequence
from typing import Any

from f1_project.ingestion import endpoints
from f1_project.ingestion.bronze import save_raw_json
from f1_project.ingestion.client import OpenF1Client, OpenF1ClientError
from f1_project.load.gold import build_gold_tables
from f1_project.load.silver import write_silver
from f1_project.transformation.dedup import NATURAL_KEYS, deduplicate
from f1_project.transformation.rejected import save_rejected
from f1_project.validation.schemas import (
    DriverSchema,
    LapSchema,
    MeetingSchema,
    SessionResultSchema,
    SessionSchema,
)
from f1_project.validation.validate import validate_records

logger = logging.getLogger(__name__)

RACE_SESSION_NAME = "Race"
LATEST_SESSION_KEYWORD = "latest"


def _parse_session_key(value: str) -> int | str:
    """Converte `--session-key` para `int` (a OpenF1 usa `session_key` numérico), exceto
    pela keyword `latest`, que é repassada como string para a API resolver a sessão atual.
    """
    if value == LATEST_SESSION_KEYWORD:
        return value
    return int(value)


def _ingest_entity(
    client: OpenF1Client,
    fetch_fn: Callable[..., list[dict[str, Any]]],
    endpoint: str,
    batch_key: str,
    schema: type,
    partition_field: str,
    **filters: Any,
) -> list:
    """Executa ingest -> Bronze -> validação -> rejeitados -> dedup -> Silver para um endpoint."""
    raw_records = fetch_fn(client, **filters)
    save_raw_json(endpoint, batch_key, raw_records)

    valid, rejected = validate_records(raw_records, schema)
    save_rejected(endpoint, batch_key, rejected)

    deduped = deduplicate(valid, NATURAL_KEYS[schema])
    write_silver(deduped, endpoint, partition_field)
    return deduped


def _ingest_year(
    client: OpenF1Client,
    year: int,
    country_name: str | None,
    session_key: int | str | None,
) -> None:
    reference_filters = {"year": year}
    if country_name is not None:
        reference_filters["country_name"] = country_name
    batch_key = str(year)

    _ingest_entity(
        client,
        endpoints.get_meetings,
        "meetings",
        batch_key,
        MeetingSchema,
        "meeting_key",
        **reference_filters,
    )

    sessions = _ingest_entity(
        client,
        endpoints.get_sessions,
        "sessions",
        batch_key,
        SessionSchema,
        "session_key",
        **reference_filters,
    )

    session_keys: list[int | str] = (
        [session_key] if session_key is not None else [s.session_key for s in sessions]
    )
    race_session_keys = {s.session_key for s in sessions if s.session_name == RACE_SESSION_NAME}

    for key in session_keys:
        try:
            _ingest_entity(
                client,
                endpoints.get_drivers,
                "drivers",
                str(key),
                DriverSchema,
                "session_key",
                session_key=key,
            )

            if key in race_session_keys:
                _ingest_entity(
                    client,
                    endpoints.get_laps,
                    "laps",
                    str(key),
                    LapSchema,
                    "session_key",
                    session_key=key,
                )
                _ingest_entity(
                    client,
                    endpoints.get_session_result,
                    "session_result",
                    str(key),
                    SessionResultSchema,
                    "session_key",
                    session_key=key,
                )
        except OpenF1ClientError:
            logger.warning(
                "Sessão %s: falha na ingestão, pulando para a próxima", key, exc_info=True
            )


def run(
    years: Sequence[int],
    country_name: str | None = None,
    session_key: int | str | None = None,
) -> None:
    """Ingesta meetings/sessions/drivers de cada ano em `years`, mais laps/session_result
    das sessões de corrida, e recalcula as tabelas Gold ao final.

    Se `session_key` for informado, drivers/laps/session_result são restritos a essa
    sessão (aceita a keyword `latest`) em vez de todas as sessões do ano.
    """
    with OpenF1Client() as client:
        for year in years:
            try:
                _ingest_year(client, year, country_name, session_key)
            except OpenF1ClientError:
                logger.warning(
                    "Ano %s: falha na ingestão, pulando para o próximo", year, exc_info=True
                )

    build_gold_tables()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Ingestão OpenF1: meetings, sessions, drivers e (para corridas) laps e "
            "session_result, com recálculo das tabelas Gold ao final."
        )
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        required=True,
        help="Anos a ingerir (ex.: --years 2023 2024 2025)",
    )
    parser.add_argument("--country-name", type=str, default=None, help="Filtra por país")
    parser.add_argument(
        "--session-key",
        type=_parse_session_key,
        default=None,
        help="Restringe a ingestão a uma sessão específica (aceita 'latest')",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    try:
        run(years=args.years, country_name=args.country_name, session_key=args.session_key)
    except OpenF1ClientError:
        logger.exception("Falha crítica na ingestão")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
