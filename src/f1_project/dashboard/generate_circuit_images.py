"""Gera uma vez os PNGs dos circuitos usados pelo dashboard.

Execute na raiz do projeto:
    poetry run python src/f1_project/dashboard/generate_circuit_images.py --year 2025

O Streamlit não importa FastF1: ele apenas lê os arquivos prontos em
``assets/circuits``. Isso mantém a navegação leve e não consome a OpenF1.
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import fastf1
import matplotlib.pyplot as plt
import numpy as np


OUTPUT_DIR = Path(__file__).resolve().parent / "assets" / "circuits"
CACHE_DIR = Path(__file__).resolve().parent / ".fastf1-cache"


def asset_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")


def rotate(points: np.ndarray, angle_degrees: float) -> np.ndarray:
    angle = np.deg2rad(angle_degrees)
    matrix = np.array(
        [[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]]
    )
    return points @ matrix


def generate_track(year: int, round_number: int, force: bool = False) -> Path:
    session = fastf1.get_session(year, round_number, "R")
    session.load(laps=True, telemetry=True, weather=False, messages=False)

    event = session.event
    circuit_name = str(event.get("Location") or event.get("EventName"))
    output_path = OUTPUT_DIR / f"{asset_slug(circuit_name)}.png"
    if output_path.exists() and not force:
        return output_path

    fastest = session.laps.pick_fastest()
    telemetry = fastest.get_telemetry()
    points = telemetry[["X", "Y"]].dropna().to_numpy(dtype=float)
    if len(points) < 2:
        raise RuntimeError(f"Telemetria insuficiente para {circuit_name}")

    circuit_info = session.get_circuit_info()
    points = rotate(points, float(getattr(circuit_info, "rotation", 0.0)))

    fig, ax = plt.subplots(figsize=(5.2, 3.0), dpi=160)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    ax.plot(points[:, 0], points[:, 1], color="#F3F5F7", linewidth=7, solid_capstyle="round")
    ax.plot(points[:, 0], points[:, 1], color="#697386", linewidth=2.2, solid_capstyle="round")
    ax.scatter(points[0, 0], points[0, 1], s=42, color="#E10600", zorder=5)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    fig.savefig(output_path, transparent=True, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera traçados de uma temporada de F1")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--force", action="store_true", help="Recria PNGs existentes")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(CACHE_DIR))

    schedule = fastf1.get_event_schedule(args.year, include_testing=False)
    failures: list[str] = []
    for event in schedule.itertuples():
        round_number = int(event.RoundNumber)
        name = str(event.EventName)
        try:
            output = generate_track(args.year, round_number, args.force)
            print(f"OK  {name}: {output.name}")
        except Exception as exc:  # mantém o lote mesmo se uma corrida falhar
            failures.append(name)
            print(f"ERRO  {name}: {exc}")

    print(f"\nConcluído: {len(schedule) - len(failures)} de {len(schedule)} circuitos.")
    if failures:
        print("Falhas: " + ", ".join(failures))


if __name__ == "__main__":
    main()
