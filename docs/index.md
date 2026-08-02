# F1 Project

Projeto de portfólio em engenharia de dados e análise: um pipeline que extrai dados históricos da [OpenF1 API](https://openf1.org/docs/#api-endpoints), valida e transforma os registros seguindo a arquitetura Bronze → Silver → Gold, e um dashboard que confronta o desempenho de dois pilotos numa mesma sessão.

## Objetivo

- **Pipeline de dados ponta a ponta:** ingestão, validação de schema (Pydantic), deduplicação e agregação, com camada dedicada para registros rejeitados na validação.
  - **Fonte:** `https://api.openf1.org/v1/`, dados históricos (>= 2023), sem autenticação.
  - **Frequência:** batch sob demanda (não é um pipeline de dados em tempo real).
  - **Escopo atual:** `meetings`, `sessions` e `drivers` (todas as sessões); `laps` e `session_result` (sessões de corrida), com agregações Gold de voltas mais rápidas por circuito e pódio por corrida. Fases futuras (`stints`, `pit`, `starting_grid`, contexto de sessão) seguem o plano de implementação incremental descrito no repositório.
- **Confronto de desempenho entre pilotos:** o dashboard compara dois pilotos lado a lado numa sessão — melhor volta, velocidade máxima, pit stops, posições ganhas/perdidas, ritmo volta a volta, posição por volta, estratégia de pneus, diferença de tempo por setor e evolução no campeonato. Consulta a OpenF1 diretamente, por lotes, sob demanda, para a sessão selecionada (dados históricos, não é streaming ao vivo).
- **Diferencial — traçados gerados por telemetria:** os desenhos dos circuitos exibidos no dashboard são gerados a partir de telemetria real de corrida (coordenadas X/Y da volta mais rápida de cada GP), via [FastF1](https://docs.fastf1.dev/), não de imagens prontas. Veja `src/f1_project/dashboard/COMO_GERAR_CIRCUITOS.md` no repositório.

## Requisitos de instalação

- **Python 3.12** — versão fixada em `.python-version`; gerencie com [pyenv](https://github.com/pyenv/pyenv) (ou [pyenv-win](https://github.com/pyenv-win/pyenv-win) no Windows)
- **[Poetry](https://python-poetry.org/)** instalado globalmente
- Acesso à internet para consultar a OpenF1 (API pública, sem autenticação)

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
poetry run streamlit run src/f1_project/dashboard/app.py
```

Veja [Execução](execucao.md) para detalhes dos parâmetros e [Arquitetura](arquitetura.md) para o fluxo de dados completo.
