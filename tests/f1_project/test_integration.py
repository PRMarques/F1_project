"""Testes de integração reais contra a API OpenF1 pública.

Não rodam por padrão (ver `addopts = "-m 'not integration'"` em pyproject.toml).
Execute explicitamente com: poetry run pytest -m integration
"""

from __future__ import annotations

import pytest

from f1_project.ingestion.client import OpenF1Client
from f1_project.ingestion.endpoints import get_meetings


@pytest.mark.integration
def test_get_meetings_returns_data_from_real_api() -> None:
    with OpenF1Client() as client:
        result = get_meetings(client, year=2024, country_name="Brazil")

    assert isinstance(result, list)
    assert result
    assert result[0]["year"] == 2024
