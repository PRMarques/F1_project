# Rodando localmente

## Pré-requisitos

- Python 3.12 (o projeto fixa `3.12.10` via `pyenv`, arquivo `.python-version` na raiz)
- [Poetry](https://python-poetry.org/) instalado globalmente (`pipx install poetry` é a forma recomendada)

## Setup inicial

Rodar uma única vez, ao clonar o repositório:

```bash
pyenv local 3.12.10                                  # garante a versão certa do Python
poetry config virtualenvs.in-project true --local     # cria o venv em .venv/ dentro do repo
poetry install                                        # instala dependências de runtime + dev
cp .env.example .env                                  # variáveis de ambiente locais
```

`poetry.toml` já força `virtualenvs.in-project = true`; o segundo comando acima é
redundante no dia a dia — só é necessário se você apagou `poetry.toml` ou está fora
do repositório. Edite `.env` se precisar mudar `OPENF1_TIMEOUT_SECONDS` ou
`OPENF1_MAX_RETRIES` (veja `src/f1_project/config.py` para os
valores padrão); a URL base da OpenF1 não costuma precisar de alteração.

## Rodar a ingestão

```bash
poetry run python -m f1_project.pipeline --years 2024
```

Usar quando quiser popular `data/` com dados reais antes de explorar o dashboard ou
depurar um módulo específico. Parâmetros disponíveis:

| Parâmetro | Quando usar |
|---|---|
| `--years` | Sempre obrigatório — um ou mais anos (ex.: `--years 2023 2024 2025`) |
| `--country-name` | Para restringir a um país e reduzir o volume de chamadas à API durante testes manuais |
| `--session-key` | Para depurar uma sessão específica sem reingerir o ano inteiro (aceita `latest`) |

Detalhes de comportamento (o que é ingerido por padrão, recálculo da Gold) estão em
[Execução](execucao.md#ingestao).

## Rodar o dashboard

```bash
poetry run streamlit run src/f1_project/dashboard/app.py
```

Use depois de rodar a ingestão pelo menos uma vez — sem dados em `data/interim/`, o
dashboard avisa e não quebra. Abre em `http://localhost:8501` por padrão.

## Rodar a documentação

```bash
poetry run mkdocs serve
```

Use ao editar arquivos em `docs/` — recarrega automaticamente a cada save. Abre em
`http://localhost:8000`.

## Lint e formatação

```bash
poetry run ruff check src tests            # lint
poetry run ruff check src tests --fix      # lint com autofix
poetry run ruff format src tests           # aplica formatação
```

Rode antes de abrir um PR — o CI (`.github/workflows/ci.yml`)
falha se `ruff check` ou `ruff format --check` encontrarem algo.
