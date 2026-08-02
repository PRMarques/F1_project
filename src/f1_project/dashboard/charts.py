"""Construção do gráfico de pódio (Altair) a partir da tabela Gold `podium_by_race`.

Paleta e specs seguem o skill de dataviz: os 3 primeiros slots categóricos
(azul/laranja/aqua) já são o subconjunto documentado como validado "all-pairs"
em modo claro e escuro — o único caso possível aqui, já que um pódio nunca
tem mais de 3 marcas. Cor identifica a equipe (nunca a posição); a posição já
está no eixo X.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

_PODIUM_PALETTE = ["#2a78d6", "#eb6834", "#1baf7a"]
_PODIUM_ORDER = ["P1", "P2", "P3"]
_BAR_HEIGHT_BY_POSITION = {1: 3, 2: 2, 3: 1}


def build_podium_chart(race_podium: pd.DataFrame) -> alt.LayerChart:
    """Monta o gráfico de barras do pódio (P1/P2/P3) de uma única corrida.

    `race_podium` deve trazer as colunas `position`, `full_name` e `team_name`,
    já filtradas para uma sessão de corrida (ver `load.gold.compute_podium_by_race`).
    """
    data = race_podium.sort_values("position").copy()
    data["position_label"] = data["position"].astype(int).map(lambda p: f"P{p}")
    data["bar_height"] = data["position"].astype(int).map(_BAR_HEIGHT_BY_POSITION)

    teams = list(dict.fromkeys(data["team_name"]))
    color_scale = alt.Scale(domain=teams, range=_PODIUM_PALETTE[: len(teams)])

    bars = (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=60)
        .encode(
            x=alt.X("position_label:N", sort=_PODIUM_ORDER, title=None),
            y=alt.Y("bar_height:Q", axis=None),
            color=alt.Color("team_name:N", scale=color_scale, legend=alt.Legend(title="Equipe")),
            tooltip=[
                alt.Tooltip("position_label:N", title="Posição"),
                alt.Tooltip("full_name:N", title="Piloto"),
                alt.Tooltip("team_name:N", title="Equipe"),
            ],
        )
    )

    labels = (
        alt.Chart(data)
        .mark_text(dy=-10, fontWeight="bold")
        .encode(
            x=alt.X("position_label:N", sort=_PODIUM_ORDER),
            y=alt.Y("bar_height:Q"),
            text="full_name:N",
        )
    )

    return (bars + labels).properties(height=280)
