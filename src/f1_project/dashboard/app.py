"""F1 Data Analytics — comparação entre dois pilotos numa sessão, via API pública OpenF1.

Execute com:
    poetry run streamlit run src/f1_project/dashboard/app.py
"""

from __future__ import annotations

import base64
import math
import re
import time
import unicodedata
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_URL = "https://api.openf1.org/v1"
BG = "#0B0D10"
PANEL = "#14181F"
BORDER = "#272D37"
TEXT = "#F3F5F7"
MUTED = "#8A93A3"
ACCENT = "#E10600"
DRIVER_A_COLOR = "#3B9EFF"
DRIVER_B_COLOR = "#F2A900"
COMPOUND_COLORS = {
    "SOFT": "#E10600",
    "MEDIUM": "#F2A900",
    "HARD": "#E5E7EB",
    "INTERMEDIATE": "#39B54A",
    "WET": "#2795E9",
}

st.set_page_config(page_title="F1 Data Analytics", page_icon="🏁", layout="wide")

st.markdown(
    f"""
    <style>
    .stApp {{background: {BG}; color: {TEXT};}}
    .block-container {{
        /* Reserva espaço para a barra fixa superior do Streamlit/Deploy. */
        padding-top: 4rem; padding-bottom: 2.5rem; max-width: 1600px;
        padding-left: 2.25rem; padding-right: 2.25rem;
    }}
    [data-testid="stMetric"], .panel {{
        background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px;
    }}
    h1, h2, h3 {{letter-spacing: -0.03em;}}
    .panel-title {{font-size: 1.02rem; font-weight: 700; margin-bottom: 10px;}}
    .driver-key {{font-size: .82rem; line-height: 1.1;}}
    .driver-key-dot {{font-size: .62rem; vertical-align: .08rem;}}
    .lower-panel-heading {{min-height: 82px;}}
    .panel-caption {{color: {MUTED}; font-size: .78rem; margin-top: 8px;}}
    .stat-card {{
        background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px;
        padding: 16px 18px; display: flex; align-items: center; gap: 14px;
    }}
    .stat-icon {{
        width: 44px; height: 44px; min-width: 44px; border-radius: 50%;
        background: rgba(225, 6, 0, 0.12); display: flex; align-items: center;
        justify-content: center; font-size: 20px;
    }}
    .stat-label {{color: {MUTED}; font-size: 0.82rem;}}
    .stat-value {{font-size: 1.55rem; font-weight: 800; line-height: 1.2;}}
    .comparison-summary {{
        display:grid; grid-template-columns:1fr .88fr 1fr; gap:12px;
        background:{PANEL}; border:1px solid {BORDER}; border-radius:14px;
        padding:14px; margin:0 0 16px;
    }}
    .summary-column {{padding:3px 14px;}}
    .summary-column.center {{
        border-left:1px solid {BORDER}; border-right:1px solid {BORDER};
        text-align:center;
    }}
    .summary-title {{font-size:.82rem; color:{MUTED}; text-transform:uppercase; font-weight:800;}}
    .summary-name {{font-size:1.08rem; font-weight:900; margin:3px 0 9px;}}
    .circuit-image-wrap {{
        height:112px; display:flex; align-items:center; justify-content:center; margin:5px 0 8px;
    }}
    .circuit-image {{
        max-width:210px; max-height:108px; width:100%; height:100%; object-fit:contain;
    }}
    .circuit-image-empty {{
        color:{MUTED}; font-size:.72rem; border:1px dashed {BORDER};
        border-radius:10px; padding:18px 24px;
    }}
    .summary-row {{
        display:flex; align-items:baseline; justify-content:space-between; gap:12px;
        padding:6px 0; border-top:1px solid rgba(39,45,55,.72);
    }}
    .summary-column.center .summary-row {{justify-content:center; flex-wrap:wrap;}}
    .summary-label {{color:{MUTED}; font-size:.75rem;}}
    .summary-value {{font-size:.88rem; font-weight:800; white-space:nowrap;}}
    .summary-note {{color:{MUTED}; font-size:.68rem; margin-top:7px;}}
    .dashboard-header {{margin: 0 0 8px;}}
    .brand {{display: flex; align-items: center; gap: 16px; min-height: 58px;}}
    .brand-badge {{
        width: 52px; height: 52px; min-width: 52px; border-radius: 50%; background: {ACCENT};
        display: flex; align-items: center; justify-content: center; font-size: 23px;
    }}
    .brand-name {{font-size: 2.03rem; font-weight: 900; letter-spacing: -0.035em; line-height: 1;}}
    .filters-row {{margin-top: 2px; margin-bottom: 4px;}}
    .updated-at {{color: {MUTED}; font-size: 0.8rem; text-align: right;}}
    .driver-card {{
        min-height: 76px; background: {PANEL}; border: 1px solid {BORDER};
        border-radius: 12px; padding: 9px 14px; display: flex; align-items: center;
        gap: 12px; overflow: hidden;
    }}
    .driver-card-content {{min-width:0; flex:1; display:flex; align-items:center; gap:14px;}}
    .driver-headshot {{height: 64px; width: 64px; object-fit: contain; align-self: flex-end;}}
    .driver-flag {{
        display:inline-flex; align-items:center; margin-left:7px;
        vertical-align:-3px;
    }}
    .driver-flag-img {{
        width:24px; height:18px; object-fit:cover; border-radius:3px;
        border:1px solid rgba(255,255,255,.22);
        box-shadow:0 1px 3px rgba(0,0,0,.35);
    }}
    .driver-flag-fallback {{
        color:{MUTED}; font-size:.68rem; font-weight:700; letter-spacing:.03em;
    }}
    .driver-role {{color: {MUTED}; font-size: .72rem; text-transform: uppercase;}}
    .driver-name {{font-size: 1rem; font-weight: 800; line-height: 1.2;}}
    .driver-team {{display:flex; align-items:center; gap:7px; margin-top:5px; color:{MUTED};}}
    .driver-number {{
        min-width:28px; padding:2px 6px; border-radius:6px; text-align:center;
        color:{TEXT}; font-size:.75rem; font-weight:900; border:1px solid {BORDER};
    }}
    .team-logo {{width:25px; height:25px; object-fit:contain;}}
    .team-logo-fallback {{
        width:25px; height:25px; border-radius:6px; display:inline-flex;
        align-items:center; justify-content:center; color:#fff; font-size:.61rem; font-weight:900;
    }}
    .team-name {{
        font-size:.72rem; font-weight:700; white-space:nowrap;
        overflow:hidden; text-overflow:ellipsis;
    }}
    .driver-card-main {{min-width:0; flex:1;}}
    .driver-championship {{
        min-width:235px; margin-left:auto; padding:8px 12px;
        border-left:1px solid {BORDER}; text-align:right;
    }}
    .champ-title {{
        color:{MUTED}; font-size:.64rem; text-transform:uppercase; letter-spacing:.06em;
    }}
    .champ-main {{font-size:.92rem; font-weight:900; margin-top:2px; white-space:nowrap;}}
    .champ-change {{font-size:.68rem; margin-top:2px; white-space:nowrap;}}
    .recent-results {{
        display:flex; justify-content:flex-end; align-items:center; gap:5px; margin-top:6px;
    }}
    .recent-label {{color:{MUTED}; font-size:.62rem; margin-right:2px;}}
    .recent-result {{
        min-width:25px; padding:3px 6px; border-radius:6px; text-align:center;
        background:#202630; border:1px solid {BORDER}; color:#D7DCE5;
        font-size:.67rem; font-weight:900;
    }}
    .recent-win {{background:#735A05; border-color:#A98408; color:#FFE27A;}}
    .recent-dnf {{background:#4A1720; border-color:#8B2735; color:#FF7785;}}
    .champ-up {{color:#65E6B7; font-weight:800;}}
    .champ-down {{color:#FF7785; font-weight:800;}}
    .champ-same {{color:{MUTED}; font-weight:800;}}
    @media (max-width:900px) {{
        .driver-card {{align-items:flex-start; flex-wrap:wrap;}}
        .driver-card-content {{flex-wrap:wrap;}}
        .driver-championship {{
            min-width:100%; width:100%; margin-left:76px; padding:7px 0 0;
            border-left:0; border-top:1px solid {BORDER}; text-align:left;
        }}
        .recent-results {{justify-content:flex-start;}}
    }}
    .season-grid-wrap {{
        overflow-x: auto; border: 1px solid {BORDER}; border-radius: 12px;
        background: {PANEL}; padding: 10px;
    }}
    .season-grid {{border-collapse: separate; border-spacing: 5px; min-width: 100%;}}
    .season-grid th {{
        color: {MUTED}; font-size: .69rem; font-weight: 700; text-align: center;
        min-width: 58px; height: 42px; padding: 4px; white-space: nowrap;
    }}
    .season-grid .driver-cell {{
        position: sticky; left: 0; z-index: 3; min-width: 126px; text-align: left;
        background: {PANEL}; color: {TEXT}; font-size: .78rem; padding: 0 9px;
    }}
    .season-grid td.result-cell {{
        height: 48px; min-width: 58px; border-radius: 7px; text-align: center;
        font-size: .78rem; font-weight: 900; border: 1px solid {BORDER};
    }}
    .season-grid .selected-gp {{
        outline: 2px solid {DRIVER_B_COLOR}; outline-offset: 1px;
        box-shadow: 0 0 12px rgba(242,169,0,.20);
    }}
    .season-legend {{color: {MUTED}; font-size: .75rem; margin: 7px 2px 2px;}}
    div[data-testid="stPlotlyChart"] {{
        background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px; padding: 6px;
    }}
    div[data-testid="stSelectbox"] label {{font-size: 0.78rem;}}
    @media (max-width: 1100px) {{
        .block-container {{padding-top: 4.25rem; padding-left: 1rem; padding-right: 1rem;}}
        .brand-name {{font-size: 1.65rem;}}
        .brand-badge {{width: 46px; height: 46px; min-width: 46px;}}
        .comparison-summary {{grid-template-columns:1fr;}}
        .summary-column.center {{
            border:0; border-top:1px solid {BORDER}; border-bottom:1px solid {BORDER};
            padding:12px 14px;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=21600, show_spinner=False)
def api_get(endpoint: str, timeout: int = 30, **params: Any) -> pd.DataFrame:
    """Consulta um endpoint da OpenF1 e devolve um DataFrame.

    A OpenF1 às vezes responde 404 (em vez de uma lista vazia) para sessões sem
    dados disponíveis nesse endpoint específico — tratamos isso como "sem dados",
    não como erro, para não derrubar o app por causa de uma sessão sem cobertura.
    """
    clean_params = {key: value for key, value in params.items() if value is not None}
    url = f"{API_URL}/{endpoint}"

    # O Streamlit reexecuta o arquivo a cada interação. O cache acima evita
    # repetir respostas já obtidas e as tentativas abaixo absorvem limites
    # temporários da API sem derrubar o dashboard com um traceback.
    for attempt in range(4):
        try:
            response = requests.get(
                url,
                params=clean_params,
                timeout=timeout,
                headers={"User-Agent": "F1-Data-Analytics/1.0"},
            )
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2**attempt)
            continue

        if response.status_code == 404:
            return pd.DataFrame()

        if response.status_code == 429:
            if attempt == 3:
                st.warning(
                    "A OpenF1 atingiu o limite temporário de consultas. "
                    "Aguarde alguns minutos e atualize a página."
                )
                st.stop()

            retry_after = response.headers.get("Retry-After")
            try:
                wait_seconds = float(retry_after) if retry_after else 2 ** (attempt + 1)
            except (TypeError, ValueError):
                wait_seconds = 2 ** (attempt + 1)
            time.sleep(min(max(wait_seconds, 1), 15))
            continue

        response.raise_for_status()
        return pd.DataFrame(response.json())

    return pd.DataFrame()


def seconds_to_lap(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    minutes, seconds = divmod(float(value), 60)
    return f"{int(minutes)}:{seconds:06.3f}"


def asset_slug(value: str) -> str:
    """Converte o nome do circuito no mesmo padrão usado pelo gerador de PNGs."""
    normalized = unicodedata.normalize("NFKD", str(value))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")


@st.cache_data(show_spinner=False)
def circuit_image_data(circuit: str, location: str = "") -> str | None:
    """Carrega um traçado local como data URI, sem rede nem FastF1 no dashboard."""
    asset_dir = Path(__file__).resolve().parent / "assets" / "circuits"
    candidates = [asset_slug(circuit), asset_slug(location)]
    for slug in dict.fromkeys(candidate for candidate in candidates if candidate):
        image_path = asset_dir / f"{slug}.png"
        if image_path.is_file():
            encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
            return f"data:image/png;base64,{encoded}"
    return None


def pace_axis_ticks(values: pd.Series, step_seconds: int = 5) -> tuple[list[int], list[str]]:
    """Cria marcações de ritmo a cada 5 segundos no formato minuto:segundo."""
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return [], []

    first_tick = math.floor(clean.min() / step_seconds) * step_seconds
    last_tick = math.ceil(clean.max() / step_seconds) * step_seconds
    tick_values = list(range(first_tick, last_tick + step_seconds, step_seconds))
    tick_labels = [f"{value // 60}:{value % 60:02d}" for value in tick_values]
    return tick_values, tick_labels


def chart_style(
    fig: go.Figure, title: str, height: int = 360, show_legend: bool = False
) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=TEXT)),
        height=height,
        margin=dict(l=22, r=22, t=52, b=24),
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(color=TEXT, family="Arial", size=10),
        legend=dict(
            orientation="h",
            y=1.1,
            x=1,
            xanchor="right",
            title=None,
            font=dict(size=9),
            itemsizing="constant",
        ),
        showlegend=show_legend,
        hoverlabel=dict(bgcolor="#202631", font_color=TEXT),
    )
    fig.update_xaxes(gridcolor="#252B34", zeroline=False, tickfont=dict(size=9))
    fig.update_yaxes(gridcolor="#252B34", zeroline=False, tickfont=dict(size=9))
    return fig


def country_flag(country_code: str | None, driver_acronym: str | None = None) -> str:
    """Gera a bandeira pela nacionalidade, nunca pela sigla exibida do piloto."""
    alpha3_to_alpha2 = {
        "ARG": "AR",
        "AUS": "AU",
        "AUT": "AT",
        "BEL": "BE",
        "BRA": "BR",
        "CAN": "CA",
        "CHN": "CN",
        "COL": "CO",
        "DEN": "DK",
        "ESP": "ES",
        "FIN": "FI",
        "FRA": "FR",
        "GBR": "GB",
        "GER": "DE",
        "IRL": "IE",
        "ITA": "IT",
        "JPN": "JP",
        "MEX": "MX",
        "MON": "MC",
        "NED": "NL",
        "NOR": "NO",
        "NZL": "NZ",
        "POL": "PL",
        "POR": "PT",
        "RUS": "RU",
        "SUI": "CH",
        "SWE": "SE",
        "THA": "TH",
        "USA": "US",
    }
    driver_to_alpha2 = {
        "ALB": "TH",
        "ALO": "ES",
        "ANT": "IT",
        "BEA": "GB",
        "BOR": "BR",
        "COL": "AR",
        "DOO": "AU",
        "GAS": "FR",
        "HAD": "FR",
        "HAM": "GB",
        "HUL": "DE",
        "LAW": "NZ",
        "LEC": "MC",
        "NOR": "GB",
        "OCO": "FR",
        "PIA": "AU",
        "RUS": "GB",
        "SAI": "ES",
        "STR": "CA",
        "TSU": "JP",
        "VER": "NL",
    }
    acronym = str(driver_acronym or "").strip().upper()
    code = str(country_code or "").strip().upper()
    code = driver_to_alpha2.get(acronym) or alpha3_to_alpha2.get(code, code)
    if len(code) != 2 or not code.isalpha():
        return '<span class="driver-flag driver-flag-fallback">PAÍS</span>'

    safe_code = escape(code.lower(), quote=True)
    return (
        '<span class="driver-flag">'
        f'<img class="driver-flag-img" src="https://flagcdn.com/w40/{safe_code}.png" '
        f'alt="Bandeira {escape(code)}" loading="lazy">'
        "</span>"
    )


def recent_results_html(results: list[str] | None) -> str:
    """Exibe as três corridas mais recentes até o GP selecionado."""
    values = (results or [])[-3:]
    if not values:
        return (
            '<div class="recent-results"><span class="recent-label">Últimos 3</span>'
            '<span class="recent-result">—</span></div>'
        )

    badges = []
    for value in values:
        css_class = (
            " recent-win"
            if value == "V"
            else " recent-dnf"
            if value in {"DNF", "DNS", "DSQ"}
            else ""
        )
        badges.append(f'<span class="recent-result{css_class}">{escape(value)}</span>')
    return (
        '<div class="recent-results"><span class="recent-label">Últimos 3</span>'
        + "".join(badges)
        + "</div>"
    )


def team_identity_html(driver: pd.Series) -> str:
    """Exibe número e equipe da sessão; usa logo PNG local quando disponível."""
    team_name = str(driver.get("team_name") or "Equipe não informada").strip()
    team_colour = str(driver.get("team_colour") or "555B66").strip().lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", team_colour):
        team_colour = "555B66"

    number_value = pd.to_numeric(pd.Series([driver.get("driver_number")]), errors="coerce").iloc[0]
    number = str(int(number_value)) if pd.notna(number_value) else "—"

    logo_dir = Path(__file__).resolve().parent / "assets" / "team_logos"
    logo_path = logo_dir / f"{asset_slug(team_name)}.png"
    if logo_path.is_file():
        encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        logo = (
            f'<img class="team-logo" src="data:image/png;base64,{encoded}" '
            f'alt="Logo {escape(team_name, quote=True)}">'
        )
    else:
        initials = "".join(word[0] for word in team_name.split()[:2]).upper() or "F1"
        logo = (
            f'<span class="team-logo-fallback" style="background:#{team_colour};">'
            f"{escape(initials)}</span>"
        )

    return (
        '<div class="driver-team">'
        f'<span class="driver-number">#{escape(number)}</span>{logo}'
        f'<span class="team-name">{escape(team_name)}</span></div>'
    )


def championship_line(standing: pd.Series | None, recent_results: list[str] | None = None) -> str:
    """Formata pontos, posição e variação oficial após a corrida selecionada."""
    if standing is None or standing.empty:
        return (
            '<div class="driver-championship"><div class="champ-title">Campeonato</div>'
            '<div class="champ-main">Dados indisponíveis</div>'
            f"{recent_results_html(recent_results)}</div>"
        )

    points = pd.to_numeric(pd.Series([standing.get("points_current")]), errors="coerce").iloc[0]
    current = pd.to_numeric(pd.Series([standing.get("position_current")]), errors="coerce").iloc[0]
    start = pd.to_numeric(pd.Series([standing.get("position_start")]), errors="coerce").iloc[0]
    if pd.isna(points) or pd.isna(current):
        return (
            '<div class="driver-championship"><div class="champ-title">Campeonato</div>'
            '<div class="champ-main">Dados indisponíveis</div>'
            f"{recent_results_html(recent_results)}</div>"
        )

    points_label = f"{float(points):g} pts"
    if pd.isna(start):
        change = '<span class="champ-same">posição anterior indisponível</span>'
    else:
        places = int(start) - int(current)
        if places > 0:
            label = "posição" if places == 1 else "posições"
            change = f'<span class="champ-up">▲ ganhou {places} {label}</span>'
        elif places < 0:
            lost = abs(places)
            label = "posição" if lost == 1 else "posições"
            change = f'<span class="champ-down">▼ perdeu {lost} {label}</span>'
        else:
            change = '<span class="champ-same">— manteve</span>'

    return (
        '<div class="driver-championship">'
        '<div class="champ-title">Campeonato após esta prova</div>'
        f'<div class="champ-main">P{int(current)} · {points_label}</div>'
        f'<div class="champ-change">{change}</div>{recent_results_html(recent_results)}</div>'
    )


def driver_card(
    driver: pd.Series,
    role: str,
    color: str,
    standing: pd.Series | None = None,
    recent_results: list[str] | None = None,
) -> str:
    """Cartão compacto com cor, bandeira e foto oficial fornecida pela OpenF1."""
    full_name = escape(str(driver.get("full_name") or driver.get("name_acronym") or "Piloto"))
    acronym = escape(str(driver.get("name_acronym") or ""))
    flag = country_flag(driver.get("country_code"), driver.get("name_acronym"))
    headshot = driver.get("headshot_url")
    image = (
        f'<img class="driver-headshot" src="{escape(str(headshot), quote=True)}" '
        f'alt="Foto de {full_name}">'
        if pd.notna(headshot) and str(headshot).strip()
        else ""
    )
    return (
        f'<div class="driver-card" style="border-left:4px solid {color};">'
        f'{image}<div class="driver-card-content"><div class="driver-card-main">'
        f'<div class="driver-role">{escape(role)}</div>'
        f'<div class="driver-name" style="color:{color};">● {acronym}{flag}</div>'
        f"<div>{full_name}</div>{team_identity_html(driver)}</div>"
        f"{championship_line(standing, recent_results)}</div></div>"
    )


def stat_card(icon: str, label: str, value: str) -> str:
    return (
        '<div class="stat-card">'
        f'<div class="stat-icon">{icon}</div>'
        f'<div><div class="stat-label">{label}</div>'
        f'<div class="stat-value">{value}</div></div>'
        "</div>"
    )


def position_by_lap(
    driver_number: int,
    laps: pd.DataFrame,
    positions: pd.DataFrame,
    chart_last_lap: int,
) -> pd.DataFrame:
    """Posição vigente em todas as voltas, mesmo sem mudança registrada pela API."""
    driver_laps = laps[laps["driver_number"] == driver_number].sort_values("date_start")
    driver_pos = positions[positions["driver_number"] == driver_number].sort_values("date")
    if driver_laps.empty or driver_pos.empty:
        return pd.DataFrame(columns=["lap_number", "position"])

    driver_laps = driver_laps.copy()
    driver_pos = driver_pos.copy()
    driver_laps["date_start"] = pd.to_datetime(driver_laps["date_start"], errors="coerce")
    driver_pos["date"] = pd.to_datetime(driver_pos["date"], errors="coerce")
    driver_laps = driver_laps.dropna(subset=["date_start"]).sort_values("date_start")
    driver_pos = driver_pos.dropna(subset=["date"]).sort_values("date")
    if driver_laps.empty or driver_pos.empty:
        return pd.DataFrame(columns=["lap_number", "position"])

    # Cada volta procura a posição mais recente conhecida. Assim a série já
    # nasce na volta 1, usando a posição inicial registrada antes da largada.
    merged = pd.merge_asof(
        driver_laps[["date_start", "lap_number"]],
        driver_pos[["date", "position"]],
        left_on="date_start",
        right_on="date",
        direction="backward",
    )

    merged = merged.dropna(subset=["lap_number"])
    if merged.empty:
        return pd.DataFrame(columns=["lap_number", "position"])

    by_lap = merged.groupby("lap_number", as_index=False)["position"].last()
    by_lap["lap_number"] = pd.to_numeric(by_lap["lap_number"], errors="coerce")
    by_lap["position"] = pd.to_numeric(by_lap["position"], errors="coerce")
    by_lap = by_lap.dropna(subset=["lap_number", "position"])
    if by_lap.empty:
        return pd.DataFrame(columns=["lap_number", "position"])

    # O endpoint position registra eventos, não necessariamente um ponto por volta.
    # A grade completa mantém a última posição conhecida até surgir uma mudança.
    full_laps = pd.DataFrame({"lap_number": range(1, chart_last_lap + 1)})
    by_lap["lap_number"] = by_lap["lap_number"].astype(int)
    complete = full_laps.merge(by_lap, on="lap_number", how="left")
    complete["position"] = complete["position"].ffill().bfill()
    return complete.dropna(subset=["position"])


# Recordes oficiais de volta em corrida. A OpenF1 não fornece este catálogo;
# entradas não cadastradas são mostradas como indisponíveis, sem estimativas.
CIRCUIT_RECORDS = {
    "Interlagos": ("1:10.540", "Valtteri Bottas", "2018"),
    "Monza": ("1:21.046", "Rubens Barrichello", "2004"),
    "Monaco": ("1:12.909", "Lewis Hamilton", "2021"),
    "Silverstone": ("1:27.097", "Max Verstappen", "2020"),
    "Spa-Francorchamps": ("1:46.286", "Valtteri Bottas", "2018"),
    "Suzuka": ("1:30.983", "Lewis Hamilton", "2019"),
}


def safe_max_speed(car_data: pd.DataFrame) -> float | None:
    if car_data.empty or "speed" not in car_data.columns:
        return None
    values = pd.to_numeric(car_data["speed"], errors="coerce").dropna()
    return float(values.max()) if not values.empty else None


def driver_summary(
    number: int,
    car_data: pd.DataFrame,
    laps: pd.DataFrame,
    pits: pd.DataFrame,
    positions: pd.DataFrame,
    result: pd.DataFrame,
) -> dict[str, str]:
    """Calcula o resumo usando apenas DataFrames já carregados da sessão."""
    driver_laps = laps[laps["driver_number"] == number] if not laps.empty else pd.DataFrame()
    lap_values = (
        pd.to_numeric(driver_laps.get("lap_duration"), errors="coerce").dropna()
        if not driver_laps.empty and "lap_duration" in driver_laps
        else pd.Series(dtype=float)
    )
    speed = safe_max_speed(car_data)
    pit_count = int((pits["driver_number"] == number).sum()) if not pits.empty else 0

    start = finish = None
    official = result[result["driver_number"] == number] if not result.empty else pd.DataFrame()
    if not official.empty:
        row = official.iloc[0]
        for field in ("grid_position", "starting_grid_position", "start_position"):
            if field in official.columns and pd.notna(row.get(field)):
                start = int(row[field])
                break
        if "position" in official.columns and pd.notna(row.get("position")):
            finish = int(row["position"])

    driver_positions = (
        positions[positions["driver_number"] == number].sort_values("date")
        if not positions.empty
        else pd.DataFrame()
    )
    if not driver_positions.empty:
        pos_values = pd.to_numeric(driver_positions["position"], errors="coerce").dropna()
        if not pos_values.empty:
            start = start if start is not None else int(pos_values.iloc[0])
            finish = finish if finish is not None else int(pos_values.iloc[-1])

    gained = start - finish if start is not None and finish is not None else None
    grid_finish = f"P{start} → P{finish}" if start is not None and finish is not None else "—"
    gained_label = f"{gained:+d}" if gained is not None else "—"
    return {
        "best_lap": seconds_to_lap(float(lap_values.min())) if not lap_values.empty else "—",
        "speed": f"{speed:.0f} km/h" if speed is not None else "—",
        "pits": str(pit_count),
        "grid_finish": grid_finish,
        "gained": gained_label,
    }


def summary_rows(items: list[tuple[str, str]]) -> str:
    return "".join(
        f'<div class="summary-row"><span class="summary-label">{escape(label)}</span>'
        f'<span class="summary-value">{escape(value)}</span></div>'
        for label, value in items
    )


def best_sector_times(driver_number: int, laps: pd.DataFrame) -> dict[int, float | None]:
    driver_laps = laps[laps["driver_number"] == driver_number]
    best: dict[int, float | None] = {}
    for sector in (1, 2, 3):
        values = driver_laps[f"duration_sector_{sector}"].dropna()
        best[sector] = float(values.min()) if not values.empty else None
    return best


def detect_retirements(
    selected_drivers: tuple[int, int], laps: pd.DataFrame, session_result: pd.DataFrame
) -> dict[int, int]:
    """Retorna abandonos confirmados pelo resultado oficial da sessão."""
    if laps.empty or "lap_number" not in laps.columns:
        return {}

    lap_numbers = pd.to_numeric(laps["lap_number"], errors="coerce")
    if lap_numbers.dropna().empty:
        return {}

    retirements: dict[int, int] = {}
    for number in selected_drivers:
        official = session_result[session_result["driver_number"] == number]
        if official.empty or "dnf" not in official.columns:
            continue
        dnf_value = official.iloc[0]["dnf"]
        is_dnf = bool(dnf_value) if pd.notna(dnf_value) else False
        if not is_dnf:
            continue
        driver_laps = pd.to_numeric(
            laps.loc[laps["driver_number"] == number, "lap_number"], errors="coerce"
        ).dropna()
        if driver_laps.empty:
            continue
        driver_last_lap = int(driver_laps.max())
        retirements[number] = driver_last_lap
    return retirements


@st.cache_data(ttl=3600, show_spinner=False)
def season_race_results(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega as corridas da temporada e seus resultados oficiais publicados."""
    season_meetings = api_get("meetings", year=year)
    season_sessions = api_get("sessions", year=year)
    if season_meetings.empty or season_sessions.empty:
        return pd.DataFrame(), pd.DataFrame()

    races = season_sessions[
        season_sessions["session_name"].astype(str).str.casefold().eq("race")
    ].copy()
    if races.empty:
        return pd.DataFrame(), season_meetings

    result_frames: list[pd.DataFrame] = []
    for race in races.sort_values("date_start").itertuples():
        result = api_get("session_result", session_key=int(race.session_key))
        if result.empty:
            continue
        result = result.copy()
        result["race_session_key"] = int(race.session_key)
        result_frames.append(result)

    results = pd.concat(result_frames, ignore_index=True) if result_frames else pd.DataFrame()
    return results, season_meetings


def result_cell_style(position: float | None, status: str) -> str:
    """Cor semafórica simples para leitura imediata do desempenho na corrida."""
    if status in {"DNF", "DNS", "DSQ"}:
        return "background:#4A1720;color:#FF7785;border-color:#8B2735;"
    if position is None or pd.isna(position):
        return f"background:#10141A;color:{MUTED};"
    place = int(position)
    if place <= 3:
        return "background:#735A05;color:#FFE27A;border-color:#A98408;"
    if place <= 6:
        return "background:#123F35;color:#65E6B7;border-color:#206B59;"
    if place <= 10:
        return "background:#143451;color:#75BEFF;border-color:#235986;"
    return "background:#202630;color:#B5BDCA;"


def result_flag(value: Any) -> bool:
    """Interpreta flags da API sem transformar valores ausentes em verdadeiro."""
    return bool(value) if pd.notna(value) else False


# --- Seleção de temporada, GP e sessão -------------------------------------------------

try:
    current_year = datetime.now().year
    meetings = api_get("meetings", year=current_year)
    if meetings.empty:
        current_year -= 1
        meetings = api_get("meetings", year=current_year)
except requests.RequestException as error:
    st.error(f"Não foi possível acessar a OpenF1: {error}")
    st.stop()

meetings = meetings.sort_values("date_start", ascending=False).drop_duplicates("meeting_key")

header_title, header_action = st.columns([6.2, 0.8], gap="small")
with header_title:
    st.markdown(
        '<div class="dashboard-header"><div class="brand">'
        '<div class="brand-badge">🏁</div>'
        '<div class="brand-name">F1 DATA ANALYTICS</div>'
        "</div></div>",
        unsafe_allow_html=True,
    )
with header_action:
    st.button("📌 Salvar", disabled=True, help="Exportação de relatório — em breve.")

st.markdown('<div class="filters-row"></div>', unsafe_allow_html=True)
filt_cols = st.columns(5, gap="medium")
with filt_cols[0]:
    year = st.selectbox("Temporada", range(current_year, 2022, -1))
if year != current_year:
    meetings = api_get("meetings", year=year).sort_values("date_start", ascending=False)
    meetings = meetings.drop_duplicates("meeting_key")

meeting_labels = {int(row.meeting_key): f"{row.country_name}" for row in meetings.itertuples()}
if not meeting_labels:
    st.warning("Nenhum GP encontrado para a temporada.")
    st.stop()

with filt_cols[1]:
    meeting_key = st.selectbox(
        "Grande Prêmio", list(meeting_labels), format_func=meeting_labels.get
    )

sessions = api_get("sessions", meeting_key=meeting_key).sort_values("date_start")
session_labels = {int(row.session_key): str(row.session_name) for row in sessions.itertuples()}
race_keys = [key for key, label in session_labels.items() if label.lower().startswith("race")]
default_session = list(session_labels).index(race_keys[0]) if race_keys else 0
with filt_cols[2]:
    session_key = st.selectbox(
        "Sessão", list(session_labels), index=default_session, format_func=session_labels.get
    )

with st.spinner("Carregando pilotos..."):
    drivers = api_get("drivers", session_key=session_key).drop_duplicates("driver_number")

if drivers.empty:
    st.warning("Esta sessão ainda não possui dados de pilotos disponíveis.")
    st.stop()

drivers["driver_number"] = drivers["driver_number"].astype(int)
driver_names = drivers.set_index("driver_number")["name_acronym"].to_dict()
driver_full_names = (
    drivers.set_index("driver_number")["full_name"].to_dict()
    if "full_name" in drivers.columns
    else driver_names.copy()
)
driver_numbers = drivers["driver_number"].astype(int).tolist()

with filt_cols[3]:
    driver_a = st.selectbox(
        "Piloto A",
        driver_numbers,
        index=0,
        format_func=lambda n: f"🔵  {driver_names.get(n, str(n))}",
    )
with filt_cols[4]:
    default_b = 1 if len(driver_numbers) > 1 else 0
    driver_b = st.selectbox(
        "Piloto B",
        driver_numbers,
        index=default_b,
        format_func=lambda n: f"🟡  {driver_names.get(n, str(n))}",
    )

st.markdown(
    f'<div class="updated-at">Atualizado em {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>',
    unsafe_allow_html=True,
)

driver_colors = {driver_a: DRIVER_A_COLOR, driver_b: DRIVER_B_COLOR}
driver_label = lambda n: driver_names.get(n, str(n))  # noqa: E731
driver_display = lambda n: driver_full_names.get(n, driver_label(n))  # noqa: E731

driver_rows = drivers.set_index("driver_number")

# O mesmo histórico alimenta os três últimos resultados dos cartões e a grade
# da temporada. Como a função é cacheada, ele é carregado apenas uma vez.
try:
    with st.spinner("Carregando histórico da temporada..."):
        season_results, season_meetings = season_race_results(year)
except requests.RequestException:
    season_results, season_meetings = pd.DataFrame(), pd.DataFrame()


def selected_driver_results(number: int) -> list[str]:
    """Retorna até três resultados, em ordem cronológica, até o GP escolhido."""
    if season_results.empty or season_meetings.empty:
        return []

    calendar = season_meetings.copy()
    calendar["date_start"] = pd.to_datetime(calendar["date_start"], errors="coerce")
    selected = calendar[
        pd.to_numeric(calendar["meeting_key"], errors="coerce").eq(int(meeting_key))
    ]
    if selected.empty:
        return []
    cutoff = selected["date_start"].max()
    allowed = calendar[calendar["date_start"].le(cutoff)][["meeting_key", "date_start"]]
    allowed["meeting_key"] = pd.to_numeric(allowed["meeting_key"], errors="coerce")

    driver_history = season_results[
        pd.to_numeric(season_results["driver_number"], errors="coerce").eq(number)
    ].copy()
    driver_history["meeting_key"] = pd.to_numeric(driver_history["meeting_key"], errors="coerce")
    rows = driver_history.merge(allowed, on="meeting_key", how="inner").sort_values("date_start")
    labels: list[str] = []
    for result in rows.tail(3).itertuples(index=False):
        if result_flag(getattr(result, "dsq", False)):
            labels.append("DSQ")
        elif result_flag(getattr(result, "dns", False)):
            labels.append("DNS")
        elif result_flag(getattr(result, "dnf", False)):
            labels.append("DNF")
        else:
            position = pd.to_numeric(
                pd.Series([getattr(result, "position", None)]), errors="coerce"
            ).iloc[0]
            labels.append(
                "V"
                if pd.notna(position) and int(position) == 1
                else f"P{int(position)}"
                if pd.notna(position)
                else "—"
            )
    return labels


# A classificação oficial é vinculada à corrida do GP, mesmo que o usuário
# esteja visualizando treino ou classificação. Uma única consulta traz todos
# os pilotos e já inclui Sprint, punições e regras de pontuação daquele ano.
race_session_key = race_keys[0] if race_keys else None
championship = (
    api_get("championship_drivers", session_key=race_session_key)
    if race_session_key is not None
    else pd.DataFrame()
)
championship_rows = (
    championship.assign(driver_number=pd.to_numeric(championship["driver_number"], errors="coerce"))
    .dropna(subset=["driver_number"])
    .drop_duplicates("driver_number", keep="last")
    .set_index("driver_number")
    if not championship.empty and "driver_number" in championship.columns
    else pd.DataFrame()
)


def selected_standing(number: int) -> pd.Series | None:
    if championship_rows.empty or number not in championship_rows.index:
        return None
    return championship_rows.loc[number]


identity_a, identity_b = st.columns(2, gap="large")
with identity_a:
    st.markdown(
        driver_card(
            driver_rows.loc[driver_a],
            "Piloto A",
            DRIVER_A_COLOR,
            selected_standing(driver_a),
            selected_driver_results(driver_a),
        ),
        unsafe_allow_html=True,
    )
with identity_b:
    st.markdown(
        driver_card(
            driver_rows.loc[driver_b],
            "Piloto B",
            DRIVER_B_COLOR,
            selected_standing(driver_b),
            selected_driver_results(driver_b),
        ),
        unsafe_allow_html=True,
    )
st.write("")

# --- Carrega dados da sessão -------------------------------------------------------

with st.spinner("Carregando dados da sessão..."):
    laps = api_get("laps", session_key=session_key)
    positions = api_get("position", session_key=session_key)
    current_result = api_get("session_result", session_key=session_key)
    stints = api_get("stints", session_key=session_key)
    pits = api_get("pit", session_key=session_key)
    weather = api_get("weather", session_key=session_key)
    car_data_a = api_get("car_data", timeout=60, session_key=session_key, driver_number=driver_a)
    car_data_b = api_get("car_data", timeout=60, session_key=session_key, driver_number=driver_b)

valid_laps = laps.copy()
if not valid_laps.empty:
    valid_laps["lap_duration"] = pd.to_numeric(valid_laps["lap_duration"], errors="coerce")
    valid_laps = valid_laps[
        valid_laps["lap_duration"].notna() & ~valid_laps["is_pit_out_lap"].fillna(False)
    ]

pair_laps = (
    valid_laps[valid_laps["driver_number"].isin([driver_a, driver_b])]
    if not valid_laps.empty
    else pd.DataFrame()
)
retirements = detect_retirements((driver_a, driver_b), laps, current_result)

# --- Resumo comparativo: Piloto A | Circuito | Piloto B -----------------------------

summary_a = driver_summary(driver_a, car_data_a, valid_laps, pits, positions, current_result)
summary_b = driver_summary(driver_b, car_data_b, valid_laps, pits, positions, current_result)

meeting_row = meetings.loc[meetings["meeting_key"] == meeting_key].iloc[0]
circuit_name = str(
    meeting_row.get("circuit_short_name")
    or meeting_row.get("location")
    or meeting_row.get("meeting_name")
    or "Circuito"
)
country_name = str(meeting_row.get("country_name") or "")
circuit_location = str(meeting_row.get("location") or "")
circuit_image = circuit_image_data(circuit_name, circuit_location)
circuit_visual = (
    f'<div class="circuit-image-wrap"><img class="circuit-image" '
    f'src="{circuit_image}" alt="Traçado de {escape(circuit_name)}"></div>'
    if circuit_image
    else '<div class="circuit-image-wrap"><div class="circuit-image-empty">'
    "Traçado ainda não gerado</div></div>"
)

latest_weather = (
    weather.sort_values("date").iloc[-1] if not weather.empty else pd.Series(dtype=object)
)
track_temp = latest_weather.get("track_temperature")
air_temp = latest_weather.get("air_temperature")
rain_detected = (
    bool(weather["rainfall"].fillna(False).astype(bool).any())
    if not weather.empty and "rainfall" in weather.columns
    else None
)
total_laps = (
    int(pd.to_numeric(laps["lap_number"], errors="coerce").max())
    if not laps.empty and pd.to_numeric(laps["lap_number"], errors="coerce").notna().any()
    else None
)
record_time, record_driver, record_year = CIRCUIT_RECORDS.get(
    circuit_name, ("Não cadastrado", "—", "—")
)

driver_items_a = [
    ("Melhor volta", summary_a["best_lap"]),
    ("Velocidade máxima", summary_a["speed"]),
    ("Pit stops", summary_a["pits"]),
    ("Grid → chegada", summary_a["grid_finish"]),
    ("Posições ganhas", summary_a["gained"]),
]
driver_items_b = [
    ("Melhor volta", summary_b["best_lap"]),
    ("Velocidade máxima", summary_b["speed"]),
    ("Pit stops", summary_b["pits"]),
    ("Grid → chegada", summary_b["grid_finish"]),
    ("Posições ganhas", summary_b["gained"]),
]
circuit_items = [
    ("Pista", f"{float(track_temp):.0f} °C" if pd.notna(track_temp) else "—"),
    ("Ar", f"{float(air_temp):.0f} °C" if pd.notna(air_temp) else "—"),
    ("Chuva", "Sim" if rain_detected else "Não" if rain_detected is not None else "—"),
    ("Voltas", str(total_laps) if total_laps is not None else "—"),
    ("Recorde em corrida", record_time),
    ("Recordista", f"{record_driver} · {record_year}" if record_driver != "—" else "—"),
]

st.markdown(
    '<div class="comparison-summary">'
    '<div class="summary-column">'
    f'<div class="summary-title">Piloto A</div>'
    f'<div class="summary-name" style="color:{DRIVER_A_COLOR}">'
    f"● {escape(driver_display(driver_a))}</div>{summary_rows(driver_items_a)}</div>"
    '<div class="summary-column center">'
    f'<div class="summary-title">Circuito</div>'
    f'<div class="summary-name">{escape(circuit_name)}</div>'
    f'<div class="summary-note">{escape(country_name)}</div>'
    f"{circuit_visual}{summary_rows(circuit_items)}"
    '<div class="summary-note">Recordes vêm de catálogo próprio; '
    "dados da sessão vêm da OpenF1.</div></div>"
    '<div class="summary-column">'
    f'<div class="summary-title">Piloto B</div>'
    f'<div class="summary-name" style="color:{DRIVER_B_COLOR}">'
    f"● {escape(driver_display(driver_b))}</div>{summary_rows(driver_items_b)}</div>"
    "</div>",
    unsafe_allow_html=True,
)

if retirements:
    retirement_items = " &nbsp; | &nbsp; ".join(
        f'<span style="color:{driver_colors[number]};font-weight:800;">'
        f"{driver_label(number)}</span> abandonou na volta "
        f'<strong style="color:#EF4444;">{lap_number}</strong>'
        for number, lap_number in retirements.items()
    )
    st.markdown(
        '<div style="background:rgba(239,68,68,.10);border:1px solid #EF4444;'
        'border-radius:10px;padding:10px 14px;margin-bottom:14px;">'
        f'<span style="color:#EF4444;font-weight:800;">⚠ ABANDONO</span>'
        f" &nbsp; {retirement_items}</div>",
        unsafe_allow_html=True,
    )

# --- Posição por volta / Ritmo de corrida -------------------------------------------

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown(
        f'<span class="driver-key" style="color:{DRIVER_A_COLOR};font-weight:800;">'
        f'<span class="driver-key-dot">●</span> {escape(driver_display(driver_a))}</span>'
        f' &nbsp;&nbsp; <span class="driver-key" style="color:{DRIVER_B_COLOR};font-weight:800;">'
        f'<span class="driver-key-dot">●</span> {escape(driver_display(driver_b))}</span>',
        unsafe_allow_html=True,
    )
    if not positions.empty and not laps.empty:
        session_last_lap = int(pd.to_numeric(laps["lap_number"], errors="coerce").max())
        frames = []
        for number in (driver_a, driver_b):
            chart_last_lap = retirements.get(number, session_last_lap)
            by_lap = position_by_lap(number, laps, positions, chart_last_lap)
            # Proteção defensiva: uma função sem `return` em algum caminho
            # devolve None. O dashboard deve seguir funcionando nesse caso.
            if by_lap is None:
                by_lap = pd.DataFrame(columns=["lap_number", "position"])
            if not by_lap.empty:
                by_lap = by_lap.copy()
                by_lap["piloto"] = driver_label(number)
                by_lap["driver_number"] = number
                frames.append(by_lap)
        pos_by_lap = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

        if not pos_by_lap.empty:
            fig = px.line(
                pos_by_lap,
                x="lap_number",
                y="position",
                color="piloto",
                markers=True,
                color_discrete_map={
                    driver_label(driver_a): DRIVER_A_COLOR,
                    driver_label(driver_b): DRIVER_B_COLOR,
                },
                line_shape="spline",
            )
            fig.update_traces(line_smoothing=0.65, marker=dict(size=4))
            worst_position = pos_by_lap["position"].max()
            for number in (driver_a, driver_b):
                driver_pits = (
                    pits[pits["driver_number"] == number] if not pits.empty else pd.DataFrame()
                )
                if not driver_pits.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=driver_pits["lap_number"],
                            y=[worst_position + 1] * len(driver_pits),
                            mode="markers+text",
                            text=["P"] * len(driver_pits),
                            textposition="middle center",
                            marker=dict(size=16, color=driver_colors[number]),
                            textfont=dict(color=BG, size=10),
                            showlegend=False,
                            hovertemplate="Pit stop — volta %{x}<extra></extra>",
                        )
                    )

            for number, driver_last_lap in retirements.items():
                fig.add_vline(
                    x=driver_last_lap,
                    line_width=2,
                    line_dash="dash",
                    line_color="#EF4444",
                )
                fig.add_annotation(
                    x=driver_last_lap,
                    y=1,
                    yref="paper",
                    text=f"Abandono · {driver_label(number)} · V{driver_last_lap}",
                    showarrow=False,
                    xanchor="left",
                    yanchor="bottom",
                    font=dict(color="#EF4444", size=11),
                    bgcolor="rgba(18, 22, 28, 0.88)",
                    bordercolor="#EF4444",
                    borderpad=4,
                )

            # Escala comparável em qualquer seleção: sempre da P1 à P20.
            fig.update_yaxes(
                autorange=False,
                range=[20.5, 0.5],
                tickmode="array",
                tickvals=[1, 5, 10, 15, 20],
                ticktext=["1", "5", "10", "15", "20"],
                title="Posição",
            )
            fig.update_xaxes(
                title="Volta",
                range=[1, session_last_lap],
                tickmode="linear",
                tick0=5,
                dtick=5,
            )
            st.plotly_chart(chart_style(fig, "Posição por volta", height=300), width="stretch")
        else:
            st.info("Sem dados de posição por volta para os pilotos selecionados.")
    else:
        st.info("Sem dados de posição para esta sessão.")

with right:
    st.markdown(
        f'<span class="driver-key" style="color:{DRIVER_A_COLOR};font-weight:800;">'
        f'<span class="driver-key-dot">●</span> {escape(driver_display(driver_a))}</span>'
        f' &nbsp;&nbsp; <span class="driver-key" style="color:{DRIVER_B_COLOR};font-weight:800;">'
        f'<span class="driver-key-dot">●</span> {escape(driver_display(driver_b))}</span>',
        unsafe_allow_html=True,
    )
    if not pair_laps.empty:
        pace = pair_laps.copy()
        pace["piloto"] = pace["driver_number"].map(driver_label)
        avg_by_lap = valid_laps.groupby("lap_number", as_index=False)["lap_duration"].mean()

        fig = px.line(
            pace,
            x="lap_number",
            y="lap_duration",
            color="piloto",
            markers=True,
            color_discrete_map={
                driver_label(driver_a): DRIVER_A_COLOR,
                driver_label(driver_b): DRIVER_B_COLOR,
            },
            line_shape="spline",
        )
        fig.add_trace(
            go.Scatter(
                x=avg_by_lap["lap_number"],
                y=avg_by_lap["lap_duration"],
                mode="lines",
                name="Média",
                line=dict(color=MUTED, dash="dash", width=1.5, shape="spline"),
            )
        )
        pace_ticks, pace_labels = pace_axis_ticks(
            pd.concat([pace["lap_duration"], avg_by_lap["lap_duration"]])
        )
        fig.update_traces(line_smoothing=0.65)
        fig.update_traces(marker=dict(size=4), selector=dict(mode="lines+markers"))
        fig.update_yaxes(
            title="Ritmo (min:seg)",
            tickmode="array",
            tickvals=pace_ticks,
            ticktext=pace_labels,
        )
        fig.update_xaxes(title="Volta", dtick=5)
        st.plotly_chart(chart_style(fig, "Ritmo de corrida", height=300), width="stretch")

        summary_cols = st.columns(2)
        for col, number in zip(summary_cols, (driver_a, driver_b), strict=True):
            driver_pace = pair_laps[pair_laps["driver_number"] == number]["lap_duration"]
            if not driver_pace.empty:
                col.markdown(
                    f'<span style="color:{driver_colors[number]};font-weight:700;">'
                    f"{driver_label(number)}</span> · "
                    f"Média: {seconds_to_lap(driver_pace.mean())} · "
                    f"Melhor: {seconds_to_lap(driver_pace.min())}",
                    unsafe_allow_html=True,
                )
    else:
        st.info("Sem dados de ritmo de corrida para esta sessão.")

# --- Estratégia de pneus / Comparação de setores ------------------------------------
# Mantém a mesma grade 50/50 dos gráficos superiores para preservar o alinhamento.
col_strategy, col_sectors = st.columns([1, 1], gap="large")

with col_strategy:
    st.markdown(
        '<div class="lower-panel-heading"><div class="panel-title">Estratégia de pneus</div>'
        f'<span style="color:{DRIVER_A_COLOR};font-weight:800;">● '
        f"{escape(driver_display(driver_a))}</span> &nbsp;&nbsp; "
        f'<span style="color:{DRIVER_B_COLOR};font-weight:800;">● '
        f"{escape(driver_display(driver_b))}</span></div>",
        unsafe_allow_html=True,
    )
    if not stints.empty:
        fig = go.Figure()
        seen_compounds: set[str] = set()
        for number in (driver_a, driver_b):
            driver_stints = stints[stints["driver_number"] == number].sort_values("lap_start")
            for _, stint in driver_stints.iterrows():
                lap_start = stint.get("lap_start")
                lap_end = stint.get("lap_end")
                if pd.isna(lap_start) or pd.isna(lap_end):
                    continue
                compound = str(stint.get("compound") or "UNKNOWN")
                fig.add_trace(
                    go.Bar(
                        x=[lap_end - lap_start + 1],
                        y=[driver_label(number)],
                        base=lap_start,
                        orientation="h",
                        marker=dict(color=COMPOUND_COLORS.get(compound, MUTED)),
                        name=compound,
                        legendgroup=compound,
                        showlegend=compound not in seen_compounds,
                        hovertemplate=(
                            f"{compound} · voltas {int(lap_start)}-{int(lap_end)}<extra></extra>"
                        ),
                    )
                )
                seen_compounds.add(compound)
            driver_pits = (
                pits[pits["driver_number"] == number] if not pits.empty else pd.DataFrame()
            )
            for _, pit in driver_pits.iterrows():
                fig.add_annotation(
                    x=pit["lap_number"],
                    y=driver_label(number),
                    text="P",
                    showarrow=False,
                    font=dict(color=TEXT, size=10, family="Arial Black"),
                    bgcolor=BG,
                    bordercolor=driver_colors[number],
                    borderwidth=1,
                    yshift=18,
                )
        fig.update_layout(barmode="overlay")
        fig.update_xaxes(title="Volta", tickmode="linear", tick0=5, dtick=5)
        tyre_driver_labels = [driver_label(driver_a), driver_label(driver_b)]
        fig.update_yaxes(
            title="",
            tickmode="array",
            tickvals=tyre_driver_labels,
            ticktext=[
                f'<span style="color:{DRIVER_A_COLOR}">●</span> {tyre_driver_labels[0]}',
                f'<span style="color:{DRIVER_B_COLOR}">●</span> {tyre_driver_labels[1]}',
            ],
        )
        st.plotly_chart(chart_style(fig, "", height=238, show_legend=True), width="stretch")
    else:
        st.info("Sem dados de stints para esta sessão.")

with col_sectors:
    st.markdown(
        '<div class="lower-panel-heading"><div class="panel-title">Comparação de setores</div>'
        f'<span style="color:{DRIVER_A_COLOR};font-weight:800;">● '
        f"{escape(driver_display(driver_a))}</span> &nbsp;&nbsp; "
        f'<span style="color:{DRIVER_B_COLOR};font-weight:800;">● '
        f"{escape(driver_display(driver_b))}</span>"
        f'<div class="panel-caption">Diferença de tempo (s) — '
        f"{escape(driver_label(driver_a))} vs {escape(driver_label(driver_b))}</div></div>",
        unsafe_allow_html=True,
    )
    if not pair_laps.empty:
        sectors_a = best_sector_times(driver_a, laps)
        sectors_b = best_sector_times(driver_b, laps)
        rows = []
        for sector in (1, 2, 3):
            time_a, time_b = sectors_a[sector], sectors_b[sector]
            if time_a is None or time_b is None:
                continue
            difference = abs(time_b - time_a)
            rows.append(
                {
                    "setor": f"Setor {sector}",
                    "a": -difference,
                    "b": difference,
                }
            )
        sector_df = pd.DataFrame(rows)

        if not sector_df.empty:
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=sector_df["setor"],
                    y=sector_df["a"],
                    name=driver_label(driver_a),
                    marker=dict(color=DRIVER_A_COLOR),
                    text=sector_df["a"].map(lambda d: f"{d:.3f}" if d else ""),
                    textposition="outside",
                )
            )
            fig.add_trace(
                go.Bar(
                    x=sector_df["setor"],
                    y=sector_df["b"],
                    name=driver_label(driver_b),
                    marker=dict(color=DRIVER_B_COLOR),
                    text=sector_df["b"].map(lambda d: f"{d:.3f}" if d else ""),
                    textposition="outside",
                )
            )
            fig.add_hline(y=0, line_color=MUTED, line_width=1)
            sector_limit = max(
                abs(sector_df[["a", "b"]].to_numpy()).max() * 1.5,
                0.1,
            )
            fig.update_layout(barmode="group")
            fig.update_yaxes(range=[-sector_limit, sector_limit], title="s", zeroline=False)
            fig.update_xaxes(title="")
            st.plotly_chart(chart_style(fig, "", height=238), width="stretch")
            st.caption(f"Negativo = {driver_label(driver_a)} mais rápido")
        else:
            st.info("Sem tempos de setor completos para os dois pilotos.")
    else:
        st.info("Sem dados de setores para esta sessão.")

# --- Mapa de desempenho na temporada -------------------------------------------------

st.write("")
st.markdown(
    '<div class="panel-title">Desempenho dos pilotos no campeonato</div>', unsafe_allow_html=True
)
st.caption(
    "Cada quadrado é o resultado de uma corrida. A coluna contornada em amarelo "
    "corresponde ao Grande Prêmio selecionado."
)

if not season_results.empty and not season_meetings.empty:
    completed_keys = set(
        pd.to_numeric(season_results["meeting_key"], errors="coerce").dropna().astype(int)
    )
    race_calendar = season_meetings[
        season_meetings["meeting_key"].astype(int).isin(completed_keys)
    ].copy()
    race_calendar["date_start"] = pd.to_datetime(race_calendar["date_start"], errors="coerce")
    race_calendar = race_calendar.sort_values("date_start").drop_duplicates("meeting_key")

    header_cells = ['<th class="driver-cell">Piloto</th>']
    for meeting in race_calendar.itertuples():
        selected_class = " selected-gp" if int(meeting.meeting_key) == int(meeting_key) else ""
        short_name = str(getattr(meeting, "country_code", "") or "")
        if not short_name:
            short_name = str(getattr(meeting, "country_name", "GP"))[:3].upper()
        header_cells.append(
            f'<th class="{selected_class.strip()}" title="{escape(str(meeting.meeting_name))}">'
            f"{escape(short_name)}</th>"
        )

    body_rows = []
    for number, color in ((driver_a, DRIVER_A_COLOR), (driver_b, DRIVER_B_COLOR)):
        cells = [
            f'<td class="driver-cell"><span style="color:{color};font-weight:900;">'
            f"● {escape(driver_label(number))}</span></td>"
        ]
        driver_results = season_results[
            pd.to_numeric(season_results["driver_number"], errors="coerce").eq(number)
        ]
        for meeting in race_calendar.itertuples():
            row = driver_results[
                pd.to_numeric(driver_results["meeting_key"], errors="coerce").eq(
                    int(meeting.meeting_key)
                )
            ]
            position = None
            status = "—"
            laps_done = None
            if not row.empty:
                result = row.iloc[-1]
                if result_flag(result.get("dsq", False)):
                    status = "DSQ"
                elif result_flag(result.get("dns", False)):
                    status = "DNS"
                elif result_flag(result.get("dnf", False)):
                    status = "DNF"
                else:
                    position = pd.to_numeric(
                        pd.Series([result.get("position")]), errors="coerce"
                    ).iloc[0]
                    status = f"P{int(position)}" if pd.notna(position) else "—"
                laps_done = result.get("number_of_laps")

            selected_class = " selected-gp" if int(meeting.meeting_key) == int(meeting_key) else ""
            tooltip = status
            if status == "DNF" and pd.notna(laps_done):
                tooltip = f"DNF · {int(laps_done)} voltas completadas"
            cell_style = result_cell_style(position, status)
            cells.append(
                f'<td class="result-cell{selected_class}" style="{cell_style}" '
                f'title="{escape(tooltip)}">{status}</td>'
            )
        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    season_grid_html = (
        '<div class="season-grid-wrap"><table class="season-grid"><thead><tr>'
        + "".join(header_cells)
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table>"
        + '<div class="season-legend">P1–P3: pódio · P4–P6: destaque · '
        + "P7–P10: pontos · DNF/DNS/DSQ: corrida não concluída</div></div>"
    )
    st.markdown(season_grid_html, unsafe_allow_html=True)
else:
    st.info("Ainda não há resultados de corrida publicados para montar o mapa da temporada.")

st.caption("Fonte: OpenF1 · projeto não oficial e sem vínculo com a Fórmula 1.")
