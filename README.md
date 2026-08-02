# F1 Project

Projeto de portfólio em engenharia de dados e análise: um pipeline que extrai dados históricos da [OpenF1 API](https://openf1.org/docs/#api-endpoints), valida e transforma os registros seguindo a arquitetura Bronze → Silver → Gold, e um dashboard que confronta o desempenho de dois pilotos numa mesma sessão.

## Objetivo

- **Pipeline de dados ponta a ponta**: ingestão, validação de schema (Pydantic), deduplicação e agregação, com uma camada dedicada para registros rejeitados na validação.
- **Confronto de desempenho entre pilotos**: o dashboard compara dois pilotos lado a lado numa sessão — melhor volta, velocidade máxima, pit stops, posições ganhas/perdidas, ritmo volta a volta, posição por volta, estratégia de pneus, diferença de tempo por setor e evolução no campeonato. Os dados são consultados por lotes, sob demanda, para a sessão selecionada (dados históricos, não é streaming ao vivo).
- **Diferencial — traçados gerados por telemetria**: os desenhos dos circuitos exibidos no dashboard não são imagens prontas baixadas da internet; são gerados a partir de telemetria real de corrida (coordenadas X/Y da volta mais rápida de cada GP), via [FastF1](https://docs.fastf1.dev/), e renderizados localmente como PNG. Veja [Traçados dos circuitos](src/f1_project/dashboard/COMO_GERAR_CIRCUITOS.md).

## Requisitos de instalação

- **Python 3.12** — versão fixada em `.python-version`; gerencie com [pyenv](https://github.com/pyenv/pyenv) (ou [pyenv-win](https://github.com/pyenv-win/pyenv-win) no Windows)
- **[Poetry](https://python-poetry.org/)** instalado globalmente (`pipx install poetry` é a forma recomendada)
- Acesso à internet para consultar a OpenF1 (API pública, sem autenticação) — não há chave ou cadastro necessário

## Instalação

```bash
pyenv local 3.12.10
poetry config virtualenvs.in-project true --local
poetry install
cp .env.example .env
```

## Execução

```bash
poetry run python -m f1_project.pipeline --years 2023 2024 2025
```

## Dashboard

```bash
poetry run streamlit run src/f1_project/dashboard/app.py
```

Consulta a OpenF1 sob demanda, por lotes, para a sessão selecionada (não depende da ingestão local): escolha temporada → Grande Prêmio → sessão → dois pilotos, e compare o desempenho dos dois em painéis lado a lado. Não requer rodar o pipeline antes — mas para gerar os traçados dos circuitos localmente, veja [Traçados dos circuitos](src/f1_project/dashboard/COMO_GERAR_CIRCUITOS.md).

## Documentação

Documentação completa (arquitetura, endpoints cobertos, decisões de schema) em [`docs/`](docs/index.md), servida via MkDocs Material:

```bash
poetry run mkdocs serve
```

## Tecnologias

| Área | Tecnologias |
|---|---|
| Linguagem e dependências | Python 3.12, Poetry |
| Pipeline de dados | httpx, Pydantic, pandas, fastparquet, python-dotenv, FastF1 |
| Dashboard e visualização | Streamlit, Altair, Plotly, Matplotlib |
| Qualidade e testes | Ruff, pytest, pytest-cov, respx |
| Documentação | MkDocs Material |
| Automação e CI/CD | Taskipy, GitHub Actions |
| Fonte de dados | [OpenF1 API](https://openf1.org/) |
| Formatos de dados | JSON (Bronze), Parquet (Silver/Gold) |

Detalhes de uso de cada tecnologia em [Tecnologias](docs/tecnologias.md).

## Testes e qualidade

```bash
poetry run ruff check src tests
poetry run ruff format --check src tests
poetry run pytest
```
