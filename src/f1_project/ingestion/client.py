"""Cliente HTTP genérico para a API OpenF1 (GET + query params, timeout e retry/backoff)."""

from __future__ import annotations

import logging
import time
from types import TracebackType
from typing import Any

import httpx

from f1_project.config import Settings
from f1_project.config import settings as default_settings

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = frozenset({429})


class OpenF1ClientError(RuntimeError):
    """Erro ao consultar a API OpenF1 após esgotar as tentativas configuradas."""


def _retry_after_seconds(response: httpx.Response) -> float | None:
    """Lê o header `Retry-After` (segundos) devolvido em respostas de rate limit."""
    retry_after = response.headers.get("Retry-After")
    if retry_after is None:
        return None
    try:
        return float(retry_after)
    except ValueError:
        return None


class OpenF1Client:
    """Cliente HTTP fino para os endpoints REST da OpenF1 (`GET /v1/<endpoint>`)."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings or default_settings
        self._client = client or httpx.Client(
            base_url=self._settings.base_url,
            timeout=self._settings.timeout_seconds,
        )

    def get(self, endpoint: str, **filters: Any) -> list[dict[str, Any]]:
        """Executa `GET /<endpoint>` com os filtros informados como query params.

        Suporta os mesmos filtros da OpenF1 (igualdade e operadores `<`, `<=`, `>`, `>=`
        embutidos no nome do parâmetro, ex. `lap_duration__gte=120`) e a keyword `latest`
        em `meeting_key`/`session_key`, repassados como valores comuns de query string.
        """
        params = {key: value for key, value in filters.items() if value is not None}
        last_error: Exception | None = None

        for attempt in range(1, self._settings.max_retries + 1):
            backoff_seconds = float(2 ** (attempt - 1))
            try:
                response = self._client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                is_retryable = status_code >= 500 or status_code in _RETRYABLE_STATUS_CODES
                if not is_retryable or attempt == self._settings.max_retries:
                    raise OpenF1ClientError(
                        f"Falha ao consultar '{endpoint}' (status {status_code})"
                    ) from exc
                last_error = exc
                backoff_seconds = _retry_after_seconds(exc.response) or backoff_seconds
            except httpx.TransportError as exc:
                if attempt == self._settings.max_retries:
                    raise OpenF1ClientError(f"Falha de rede ao consultar '{endpoint}'") from exc
                last_error = exc

            logger.warning(
                "Tentativa %s/%s falhou para '%s'; nova tentativa em %ss",
                attempt,
                self._settings.max_retries,
                endpoint,
                backoff_seconds,
            )
            time.sleep(backoff_seconds)

        raise OpenF1ClientError(f"Falha ao consultar '{endpoint}'") from last_error

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> OpenF1Client:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
