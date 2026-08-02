# Execução

## Comandos Poetry

Comandos usados no dia a dia do projeto e quando usar cada um.

**Setup do ambiente** (rodar uma vez ao clonar o repositório):

```bash
pyenv local 3.12.10                        # fixa a versão do Python do projeto
poetry config virtualenvs.in-project true --local  # cria o venv em .venv/ dentro do repo
poetry install                              # instala dependências de [project] + grupo dev
```

**Dependências** (ao adicionar/remover bibliotecas):

```bash
poetry add <pacote>              # nova dependência de runtime (ex.: poetry add requests)
poetry add --group dev <pacote>  # nova dependência só de desenvolvimento (lint, teste, docs)
poetry remove <pacote>           # remove uma dependência
poetry update                    # atualiza dependências respeitando os limites do pyproject.toml
poetry lock                      # regrava o poetry.lock após editar pyproject.toml à mão
poetry show --tree               # lista dependências instaladas e suas relações
```

**Execução de comandos dentro do venv** (sem precisar ativar o ambiente manualmente):

```bash
poetry run python -m f1_project.pipeline --years 2024   # roda o pipeline de ingestão
poetry run streamlit run src/f1_project/dashboard/app.py  # sobe o dashboard
poetry run pytest                                        # roda a suíte de testes
poetry run ruff check src tests                          # lint
poetry run mkdocs serve                                  # documentação local
```

Use `poetry run <comando>` sempre que precisar executar algo dentro do venv do
projeto sem ativar o shell explicitamente — é a forma usada em todos os exemplos
deste documento. Para uma sessão interativa mais longa (vários comandos seguidos),
pode ser mais prático ativar o ambiente uma vez:

```bash
poetry env activate   # imprime o comando de ativação do venv para o shell atual
```

## Ingestão

```bash
poetry run python -m f1_project.pipeline --years 2024
poetry run python -m f1_project.pipeline --years 2023 2024 2025
poetry run python -m f1_project.pipeline --years 2024 --country-name "Brazil"
poetry run python -m f1_project.pipeline --years 2024 --session-key 9222
```

| Parâmetro | Descrição |
|---|---|
| `--years` | Um ou mais anos a ingerir (ex.: `--years 2023 2024 2025`) |
| `--country-name` | Filtra `meetings`/`sessions` pelo país, em cada ano |
| `--session-key` | Restringe drivers/laps/session_result a uma sessão específica (aceita `latest`) |

Sem `--session-key`, `drivers` é ingerido para todas as sessões de cada ano; `laps` e
`session_result` só são ingeridos para as sessões de corrida (`session_name == "Race"`),
já que são a base das agregações Gold hoje (voltas mais rápidas por circuito, pódio).
Ao final da ingestão, as tabelas Gold são recalculadas automaticamente a partir de toda
a Silver acumulada em `data/interim/` — não só do lote da execução atual.

## Dashboard

Depois de rodar a ingestão, explore os dados em uma interface Streamlit:

```bash
poetry run streamlit run src/f1_project/dashboard/app.py
```

A navegação segue a hierarquia ano → corrida (`meeting`) → sessão → pilotos (camada
Silver, `data/interim/`). Para uma sessão de corrida, mostra também o pódio (gráfico
P1/P2/P3) e as 5 voltas mais rápidas já registradas para o circuito daquela corrida
(camada Gold, `data/processed/`). Sem dados ingeridos, o dashboard avisa e pede para
rodar `f1_project.pipeline` primeiro.

## Testes e qualidade

```bash
poetry run ruff check src tests
poetry run ruff format --check src tests
poetry run pytest
```

Testes de integração reais (chamada à API OpenF1 viva) são marcados com `@pytest.mark.integration` e não rodam por padrão:

```bash
poetry run pytest -m integration
```

## Documentação

```bash
poetry run mkdocs serve
poetry run mkdocs build --strict
```
