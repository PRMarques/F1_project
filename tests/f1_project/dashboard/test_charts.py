from __future__ import annotations

import altair as alt
import pandas as pd

from f1_project.dashboard.charts import build_podium_chart


def _podium_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"position": 2, "full_name": "Lewis Hamilton", "team_name": "Mercedes"},
            {"position": 1, "full_name": "Max Verstappen", "team_name": "Red Bull"},
            {"position": 3, "full_name": "Charles Leclerc", "team_name": "Ferrari"},
        ]
    )


def test_build_podium_chart_returns_layered_chart_with_bars_and_labels() -> None:
    chart = build_podium_chart(_podium_df())

    assert isinstance(chart, alt.LayerChart)
    assert len(chart.layer) == 2


def test_build_podium_chart_orders_by_position() -> None:
    chart = build_podium_chart(_podium_df())

    bars_data = chart.data
    assert list(bars_data["position_label"]) == ["P1", "P2", "P3"]
    assert list(bars_data["full_name"]) == ["Max Verstappen", "Lewis Hamilton", "Charles Leclerc"]
    assert list(bars_data["bar_height"]) == [3, 2, 1]


def test_build_podium_chart_assigns_validated_categorical_colors_per_team() -> None:
    chart = build_podium_chart(_podium_df())

    color_encoding = chart.layer[0].encoding.color.to_dict()
    assert color_encoding["scale"]["domain"] == ["Red Bull", "Mercedes", "Ferrari"]
    assert color_encoding["scale"]["range"] == ["#2a78d6", "#eb6834", "#1baf7a"]


def test_build_podium_chart_reuses_slot_for_same_team_on_multiple_steps() -> None:
    same_team_podium = pd.DataFrame(
        [
            {"position": 1, "full_name": "Max Verstappen", "team_name": "Red Bull"},
            {"position": 2, "full_name": "Sergio Perez", "team_name": "Red Bull"},
            {"position": 3, "full_name": "Charles Leclerc", "team_name": "Ferrari"},
        ]
    )

    chart = build_podium_chart(same_team_podium)

    color_encoding = chart.layer[0].encoding.color.to_dict()
    assert color_encoding["scale"]["domain"] == ["Red Bull", "Ferrari"]
    assert color_encoding["scale"]["range"] == ["#2a78d6", "#eb6834"]
