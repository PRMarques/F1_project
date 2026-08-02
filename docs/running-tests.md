# Rodando os testes

## Suíte padrão

```bash
poetry run pytest
```

Roda toda a suíte com cobertura (`--cov=f1_project --cov-report=term-missing`,
configurado em `pyproject.toml`). Falha se a cobertura total
ficar abaixo de 50% (`--cov-fail-under=50`) — use como sinal de que um módulo novo
ficou sem teste, não como meta a perseguir por si só.

Por padrão os testes marcados `@pytest.mark.integration` **não** rodam (`addopts`
inclui `-m "not integration"`), porque dependem da API OpenF1 real.

## Testes de integração

```bash
poetry run pytest -m integration
```

Use antes de um release ou ao mexer em `ingestion/client.py` /
`ingestion/endpoints.py`, para confirmar que o parsing continua compatível com a
resposta real da API. Não rode em loop nem em CI a cada commit — depende de rede e
de disponibilidade externa (veja `tests/f1_project/test_integration.py`).

## Rodando um subconjunto

```bash
poetry run pytest tests/f1_project/load/test_gold.py --no-cov       # um arquivo
poetry run pytest tests/f1_project/load/test_gold.py -k podium --no-cov  # um teste específico
poetry run pytest tests/f1_project/dashboard/ --no-cov               # um módulo inteiro
```

Use durante o desenvolvimento para iterar rápido em um módulo sem rodar a suíte
inteira a cada mudança. `--cov-fail-under=50` em `pyproject.toml` (`addopts`) se
aplica a **qualquer** execução do pytest, medindo cobertura sobre `f1_project`
inteiro — rodar um arquivo isolado sem `--no-cov` quase sempre falha o gate de
cobertura mesmo com todos os testes passando (erro `Coverage failure: total of N
is less than fail-under=50`). `--no-cov` desliga a coleta de cobertura só para
essa execução; a suíte completa (`poetry run pytest`, sem esse flag) continua
sendo o que precisa passar antes do PR.

## Cobertura em HTML

```bash
poetry run pytest --cov-report=html
```

Gera `htmlcov/index.html` — abra no navegador quando `--cov-report=term-missing`
não for suficiente para localizar visualmente quais linhas faltam cobertura.

## Convenções da suíte

- `tests/f1_project/` espelha `src/f1_project/`: um `test_<módulo>.py` por módulo de
  produção, no mesmo subcaminho. Ao criar um módulo novo, crie o teste no caminho
  correspondente — é assim que se decide onde um teste novo deve morar.
- Mocks de HTTP usam [`respx`](https://lundberg.github.io/respx/) (dependência dev)
  em vez de bater na API real — só os testes `integration` fazem chamadas de rede.
- `tests/f1_project/test_pipeline.py` cobre a orquestração ponta a ponta com dados
  falsos; testes de módulo (`ingestion/`, `validation/`, `transformation/`, `load/`)
  cobrem cada etapa isoladamente.
