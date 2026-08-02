# Tecnologias

Visão geral de toda a stack usada no projeto, por área.

## Linguagem e runtime

| Tecnologia | Uso |
|---|---|
| [Python 3.12](https://www.python.org/) | Linguagem principal, versão fixada em `.python-version` |
| [Poetry](https://python-poetry.org/) | Gerenciamento de dependências, ambiente virtual e build (`pyproject.toml`, `poetry.lock`) |

## Pipeline de dados

| Tecnologia | Uso |
|---|---|
| [httpx](https://www.python-httpx.org/) | Cliente HTTP para consumir a [OpenF1 API](https://openf1.org/docs/#api-endpoints), com timeout e retry/backoff |
| [Pydantic](https://docs.pydantic.dev/) | Schemas de validação por entidade (`validation/schemas.py`) |
| [pandas](https://pandas.pydata.org/) | Deduplicação, transformação e agregações (camadas Silver e Gold) |
| [fastparquet](https://fastparquet.readthedocs.io/) | Leitura e escrita idempotente das camadas Silver/Gold em Parquet |
| [python-dotenv](https://saurabh-kumar.com/python-dotenv/) | Carregamento de configuração via `.env` (`config.py`) |
| [FastF1](https://docs.fastf1.dev/) | Telemetria real de corrida (coordenadas X/Y), usada para gerar os traçados dos circuitos |

## Dashboard e visualização

| Tecnologia | Uso |
|---|---|
| [Streamlit](https://streamlit.io/) | Interface web do dashboard (`dashboard/app.py`) |
| [Altair](https://altair-viz.github.io/) | Gráfico de pódio |
| [Plotly](https://plotly.com/python/) | Gráficos interativos de confronto entre pilotos |
| [Matplotlib](https://matplotlib.org/) | Renderização local dos traçados dos circuitos em PNG a partir da telemetria do FastF1 |

## Qualidade e testes

| Tecnologia | Uso |
|---|---|
| [Ruff](https://docs.astral.sh/ruff/) | Lint e formatação (`ruff check`, `ruff format`) |
| [pytest](https://docs.pytest.org/) | Testes automatizados, espelhando a estrutura de `src/f1_project/` em `tests/` |
| [pytest-cov](https://pytest-cov.readthedocs.io/) | Cobertura de testes, com mínimo de 50% configurado (`--cov-fail-under=50`) |
| [respx](https://lundberg.github.io/respx/) | Mock de chamadas HTTP da OpenF1 nos testes, sem depender da API real |

## Documentação

| Tecnologia | Uso |
|---|---|
| [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) | Site de documentação (`docs/`, tema e navegação em `mkdocs.yml`), com suporte a diagramas Mermaid |

## Automação e CI/CD

| Tecnologia | Uso |
|---|---|
| [Taskipy](https://github.com/taskipy/taskipy) | Atalhos de tarefas via Poetry (`poetry run task docs`) |
| [GitHub Actions](https://docs.github.com/actions) | Pipeline de CI (`.github/workflows/ci.yml`): lint, testes com cobertura e build estrito da documentação a cada push/PR |

## Fonte de dados externa

| Tecnologia | Uso |
|---|---|
| [OpenF1 API](https://openf1.org/) | API pública, sem autenticação, fonte de todos os dados históricos (>= 2023) consumidos pelo pipeline e pelo dashboard |

## Formatos de dados

- **JSON** — camada Bronze (`data/raw/`), resposta crua da API
- **Parquet** — camadas Silver (`data/interim/`) e Gold (`data/processed/`)
