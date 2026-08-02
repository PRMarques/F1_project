# Estrutura do projeto

```text
F1_project/
├── src/f1_project/
│   ├── config.py                  # Settings (URL base, timeout, retries, caminhos de data/), lidas de .env
│   ├── pipeline.py                 # Orquestrador: liga ingestão → validação → transformação → Silver → Gold
│   ├── ingestion/
│   │   ├── client.py                # Cliente HTTP genérico (GET /v1/<endpoint>) com retry/backoff
│   │   ├── endpoints.py             # Uma função fina por endpoint (get_meetings, get_sessions, ...)
│   │   └── bronze.py                # Persiste o JSON cru em data/raw/
│   ├── validation/
│   │   ├── schemas.py               # Schemas Pydantic por entidade (chave natural obrigatória)
│   │   └── validate.py              # Valida uma lista de registros contra um schema
│   ├── transformation/
│   │   ├── dedup.py                 # Deduplicação pela chave natural de cada entidade
│   │   └── rejected.py              # Roteia registros inválidos para data/rejected/
│   ├── load/
│   │   ├── silver.py                # Leitura/escrita idempotente da camada Silver (parquet)
│   │   └── gold.py                  # Agregações Gold (voltas mais rápidas, pódio)
│   └── dashboard/
│       ├── app.py                   # App Streamlit (entrypoint da UI)
│       ├── loaders.py                # Funções de conveniência sobre load.silver.read_silver
│       ├── charts.py                 # Gráficos Altair (pódio)
│       └── generate_circuit_images.py # Script utilitário, roda fora do pipeline
├── tests/f1_project/                # Espelha o layout de src/f1_project/ (um test_*.py por módulo)
├── data/                             # Não versionado (.gitignore) — recriado ao rodar o pipeline
│   ├── raw/                          # Bronze: JSON cru por endpoint/lote
│   ├── interim/                      # Silver: parquet tipado e deduplicado
│   ├── processed/                    # Gold: tabelas agregadas
│   └── rejected/                     # Registros que falharam validação
├── docs/                             # Fonte do site MkDocs (nav em mkdocs.yml)
├── .github/workflows/ci.yml          # Lint, testes e build da doc a cada push/PR
├── pyproject.toml                    # Dependências e config de ruff/pytest/coverage
├── poetry.toml                       # Força venv em .venv/ dentro do repo
├── poetry.lock                       # Versões travadas — não editar à mão
├── .env.example                      # Template de variáveis de ambiente (copiar para .env)
└── mkdocs.yml                        # Navegação e tema do site de documentação
```

## Quando mexer em cada parte

- **Novo endpoint da OpenF1**: adicionar em `ingestion/endpoints.py`, schema em
  `validation/schemas.py`, e ligar a chamada em `pipeline.py`. Veja
  [Arquitetura](arquitetura.md) para o fluxo completo e a tabela de chaves naturais.
- **Mudança de agregação ou nova tabela Gold**: `load/gold.py`.
- **Mudança na navegação ou nos gráficos do dashboard**: `dashboard/app.py` (layout),
  `dashboard/loaders.py` (dados), `dashboard/charts.py` (visualização).
- **Nova variável de configuração**: `config.py` + `.env.example` (documentar o valor
  padrão e o efeito da variável).
- **Teste de um módulo novo**: criar `tests/f1_project/<mesmo_caminho>/test_<módulo>.py`
  — a suíte usa esse espelhamento para localizar cobertura por módulo.
