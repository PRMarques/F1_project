"""Funções de apoio do dashboard: formatação, HTML, cálculos e acesso à OpenF1.

Extraídas de ``app.py`` para permitir teste unitário sem executar o script
Streamlit (que roda de ponta a ponta a cada import, consultando a API real).
"""

from __future__ import annotations

import base64
import math
import re
import time
import unicodedata
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
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


def default_meeting_index(meetings: pd.DataFrame, now: pd.Timestamp | None = None) -> int:
    """Posição do último GP que já aconteceu, na ordem de `meetings` (mais recente primeiro).

    Evita que o dashboard abra por padrão numa corrida futura só porque é a última do
    calendário: `meetings` já vem ordenado por `date_start` decrescente, então a primeira
    linha com data no passado é o GP mais recente já disputado. Sem nenhum GP passado
    (ex.: início de temporada), volta para a primeira linha (comportamento anterior).
    """
    if meetings.empty:
        return 0
    reference = now if now is not None else pd.Timestamp.now(tz="UTC")
    dates = pd.to_datetime(meetings["date_start"], errors="coerce", utc=True)
    for position, date in enumerate(dates):
        if pd.notna(date) and date <= reference:
            return position
    return 0


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


def brand_logo_html() -> str:
    """Logo da Formula 1 usada no cabeçalho do dashboard."""
    logo_path = Path(__file__).resolve().parent / "assets" / "team_logos" / "formula1.png"
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f'<img class="brand-badge" src="data:image/png;base64,{encoded}" alt="Logo Formula 1">'


def team_logo_html(driver: pd.Series) -> str:
    """Logo da equipe atual do piloto; usa PNG local quando disponível."""
    team_name = str(driver.get("team_name") or "Equipe não informada").strip()
    team_colour = str(driver.get("team_colour") or "555B66").strip().lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", team_colour):
        team_colour = "555B66"

    logo_dir = Path(__file__).resolve().parent / "assets" / "team_logos"
    logo_path = logo_dir / f"{asset_slug(team_name)}.png"
    if logo_path.is_file():
        encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        return (
            f'<img class="team-logo" src="data:image/png;base64,{encoded}" '
            f'alt="Logo {escape(team_name, quote=True)}">'
        )

    initials = "".join(word[0] for word in team_name.split()[:2]).upper() or "F1"
    return (
        f'<span class="team-logo-fallback" style="background:#{team_colour};">'
        f"{escape(initials)}</span>"
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
    raw_number = driver.get("driver_number")
    if pd.isna(raw_number):
        raw_number = driver.name  # driver_rows usa driver_number como índice do Series
    number_value = pd.to_numeric(pd.Series([raw_number]), errors="coerce").iloc[0]
    number = str(int(number_value)) if pd.notna(number_value) else "—"
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
        '<div class="driver-identity">'
        '<div class="driver-label">'
        f'<div class="driver-role">{escape(role)}</div>'
        f'<div class="driver-acronym" style="color:{color};">'
        f'<span class="driver-number">#{escape(number)}</span> ● {acronym}{flag}</div></div>'
        f'<div class="driver-image-row">{image}{team_logo_html(driver)}</div>'
        f'<div class="driver-fullname">{full_name}</div></div>'
        f'<div class="driver-card-content">'
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
