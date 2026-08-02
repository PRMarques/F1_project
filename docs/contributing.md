# Contribuindo

## Antes de começar

Siga o setup em [Rodando localmente](running-local.md) e dê uma olhada em
[Estrutura do projeto](project-structure.md) e [Arquitetura](arquitetura.md) para
saber onde uma mudança se encaixa antes de escrever código.

## Fluxo de trabalho

1. Crie uma branch a partir de `main` (ex.: `feat/nome-curto`, `fix/nome-curto`).
2. Faça a mudança, incluindo teste(s) no caminho espelhado em `tests/` (veja
   [Rodando os testes](running-tests.md#convencoes-da-suite)).
3. Rode a checklist local abaixo antes de abrir o PR — é exatamente o que o CI roda.
4. Abra o PR contra `main` com uma descrição curta do porquê da mudança, não só do quê.

## Checklist antes do PR

```bash
poetry run ruff check src tests
poetry run ruff format --check src tests
poetry run pytest
poetry run mkdocs build --strict
```

Rode essa sequência sempre — é a mesma usada em
`.github/workflows/ci.yml`. Um PR que falha aqui
falha no CI; rodar local primeiro evita ida e volta. `mkdocs build --strict` só é
necessário se você tocou em `docs/`, `mkdocs.yml` ou em links entre eles (o `--strict`
trata link quebrado como erro de build).

## Estilo de código

- Lint e formatação são de responsabilidade do `ruff`, configurado em
  `pyproject.toml` (`select = ["E", "F", "I", "UP", "B", "N", "S", "C90"]`).
  Não discuta estilo em review — rode `ruff format` e `ruff check --fix`.
- `tests/**/*.py` ignora a regra `S101` (uso de `assert`) — é esperado em teste,
  não em código de produção.
- Schemas novos (entidades da OpenF1) seguem o padrão de `validation/schemas.py`:
  só a chave natural (e `meeting_key`/`session_key` de referência) é obrigatória; o
  resto é opcional, porque a API pode retornar campos nulos.

## Testes

- Todo módulo novo em `src/f1_project/` ganha um `test_<módulo>.py` no caminho
  espelhado em `tests/f1_project/`.
- Não adicione chamadas de rede reais em testes normais — use `respx` para mockar
  HTTP. Testes que precisam da API real levam `@pytest.mark.integration` (não rodam
  no CI por padrão; veja [Rodando os testes](running-tests.md#testes-de-integracao)).
- Cobertura mínima de 50% é validada automaticamente
  (`--cov-fail-under=50`) — um PR que derruba a cobertura abaixo disso falha o CI.

## Documentação

Se a mudança altera comportamento observável (novo parâmetro de CLI, nova tabela
Gold, novo endpoint ingerido), atualize a página correspondente em `docs/` no mesmo
PR — a [Arquitetura](arquitetura.md) e a [Execução](execucao.md) devem refletir o
estado atual do pipeline, não o de quando foram escritas.

## Variáveis de ambiente

Se a mudança adiciona uma variável de ambiente nova (lida em
`src/f1_project/config.py`), adicione também uma entrada comentada
em `.env.example` com o valor padrão — é a referência que
qualquer pessoa usa no setup inicial.
