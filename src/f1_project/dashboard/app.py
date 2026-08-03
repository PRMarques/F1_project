"""F1 Data Analytics — comparação entre dois pilotos numa sessão, via API pública OpenF1.

Execute com:
    poetry run streamlit run src/f1_project/dashboard/app.py
"""

from __future__ import annotations

from datetime import datetime
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

from f1_project.dashboard.helpers import (
    ACCENT,
    BG,
    BORDER,
    CIRCUIT_RECORDS,
    COMPOUND_COLORS,
    DRIVER_A_COLOR,
    DRIVER_B_COLOR,
    MUTED,
    PANEL,
    TEXT,
    api_get,
    best_sector_times,
    chart_style,
    circuit_image_data,
    default_meeting_index,
    detect_retirements,
    driver_card,
    driver_summary,
    pace_axis_ticks,
    position_by_lap,
    result_cell_style,
    result_flag,
    season_race_results,
    seconds_to_lap,
    summary_rows,
)

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
        "Grande Prêmio",
        list(meeting_labels),
        index=default_meeting_index(meetings),
        format_func=meeting_labels.get,
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
