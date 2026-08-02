# Traçados dos circuitos

Os traçados exibidos no dashboard são gerados a partir de telemetria real de
corrida (coordenadas X/Y da volta mais rápida de cada GP), via
[FastF1](https://docs.fastf1.dev/) — não são imagens prontas.

`fastf1` e `matplotlib` já são dependências do projeto (`pyproject.toml`); um
`poetry install` na raiz é suficiente. Gere os circuitos de 2025:

```bash
poetry run python src/f1_project/dashboard/generate_circuit_images.py --year 2025
```

Os PNGs serão criados automaticamente em:

```text
src/f1_project/dashboard/assets/circuits/
```

Depois disso, inicie normalmente o dashboard:

```bash
poetry run streamlit run src/f1_project/dashboard/app.py
```

O FastF1 é usado somente pelo gerador. Durante a navegação, o dashboard apenas
lê os PNGs locais e não faz chamadas adicionais à OpenF1.
