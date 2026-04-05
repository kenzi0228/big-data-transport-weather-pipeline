from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent


def find_latest_json_file(base_dir: str, prefix: str) -> Path | None:
    files = sorted((PROJECT_ROOT / base_dir).rglob(f"{prefix}_*.json"))
    return files[-1] if files else None


def count_raw_files(base_dir: str, prefix: str) -> int:
    return len(list((PROJECT_ROOT / base_dir).rglob(f"{prefix}_*.json")))


def load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_batch_summary() -> dict[str, Any] | None:
    return load_json(PROJECT_ROOT / "data" / "analytics" / "daily_kpis" / "transport_weather_summary.json")


def load_mapreduce_output() -> list[dict[str, Any]]:
    path = PROJECT_ROOT / "data" / "analytics" / "daily_kpis" / "mapreduce_line_destination_counts.txt"
    if not path.exists():
        return []

    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or "\t" not in line:
                continue

            key, count = line.split("\t", 1)
            if "|" not in key:
                continue

            line_label, destination = key.split("|", 1)
            rows.append(
                {
                    "Ligne": line_label.replace("metro_", ""),
                    "Destination": destination,
                    "Occurrences": int(count),
                }
            )
    return rows


def run_python_script(relative_path: str) -> tuple[bool, str]:
    script_path = PROJECT_ROOT / relative_path
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return True, (result.stdout or "").strip()
    except subprocess.CalledProcessError as exc:
        output = (exc.stdout or "") + "\n" + (exc.stderr or "")
        return False, output.strip()


def kafka_running() -> bool:
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return "kafka-local" in result.stdout.splitlines()
    except Exception:
        return False


def extract_latest_transport_events(limit: int = 12) -> list[dict[str, Any]]:
    latest_transport = find_latest_json_file("data/raw/idfm_stop_monitoring", "idfm_raw")
    payload = load_json(latest_transport)
    if not payload:
        return []

    line_label = payload.get("line_label", "unknown")
    filtered_journeys = payload.get("filtered_journeys", [])

    rows: list[dict[str, Any]] = []

    for item in filtered_journeys:
        matched_calls = item.get("matched_calls", [])
        for call in matched_calls:
            stop_ref_raw = call.get("StopPointRef", {})
            stop_ref = stop_ref_raw.get("value") if isinstance(stop_ref_raw, dict) else stop_ref_raw

            destination_display = call.get("DestinationDisplay", [])
            destination = "Inconnue"
            if isinstance(destination_display, list) and destination_display:
                first = destination_display[0]
                if isinstance(first, dict):
                    destination = str(first.get("value", "Inconnue"))
                elif isinstance(first, str):
                    destination = first

            expected_time = call.get("ExpectedArrivalTime") or call.get("ExpectedDepartureTime")
            status = call.get("DepartureStatus", "UNKNOWN")

            rows.append(
                {
                    "LigneLabel": line_label,
                    "Ligne": line_label.replace("metro_", ""),
                    "Destination": destination,
                    "Heure prévue": expected_time,
                    "Statut": status,
                    "StopPointRef": stop_ref,
                }
            )

    return rows[:limit]


def extract_weather_metrics() -> dict[str, Any] | None:
    latest_weather = find_latest_json_file("data/raw/openmeteo", "openmeteo_raw")
    payload = load_json(latest_weather)
    if not payload:
        return None

    weather_payload = payload.get("payload", {})
    hourly = weather_payload.get("hourly", {})

    times = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    precipitations = hourly.get("precipitation", [])
    wind_speeds = hourly.get("wind_speed_10m", [])

    def avg(values: list[float]) -> float | None:
        return round(sum(values) / len(values), 2) if values else None

    return {
        "Dernier fichier": latest_weather.name,
        "Points horaires": len(times),
        "Température moyenne": avg(temperatures),
        "Précipitations totales": round(sum(precipitations), 2) if precipitations else None,
        "Vent moyen": avg(wind_speeds),
    }


def format_status(status: str) -> str:
    mapping = {
        "ON_TIME": "À l'heure",
        "DELAYED": "Retardé",
        "EARLY": "En avance",
        "UNKNOWN": "Inconnu",
    }
    return mapping.get(status, status)


st.set_page_config(page_title="Pipeline Big Data Transport & Météo", layout="wide")

st.title("Pipeline Big Data Transport & Météo")
st.caption("Interface de démonstration : IDFM réel, Open-Meteo, Kafka, batch analytics, MapReduce")

summary = load_batch_summary()
weather = extract_weather_metrics()
events = extract_latest_transport_events()
mapreduce_rows = load_mapreduce_output()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Kafka", "Actif" if kafka_running() else "Inactif")
c2.metric("Fichiers transport", count_raw_files("data/raw/idfm_stop_monitoring", "idfm_raw"))
c3.metric("Fichiers météo", count_raw_files("data/raw/openmeteo", "openmeteo_raw"))
c4.metric(
    "Journeys filtrés",
    summary["transport"]["total_filtered_journeys"] if summary else "N/A"
)

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Vue d'ensemble", "Transport temps réel", "Météo Paris", "Analytics", "Actions"]
)

with tab1:
    st.subheader("État global")

    if summary:
        observed_lines = summary["transport"].get("observed_lines", [])
        st.write(f"**Lignes observées :** {', '.join(observed_lines) if observed_lines else 'Aucune'}")
        st.write(f"**Total des journeys filtrés :** {summary['transport'].get('total_filtered_journeys', 0)}")
    else:
        st.info("Le résumé batch n'est pas encore disponible.")

    latest_transport = find_latest_json_file("data/raw/idfm_stop_monitoring", "idfm_raw")
    latest_weather = find_latest_json_file("data/raw/openmeteo", "openmeteo_raw")

    left, right = st.columns(2)
    with left:
        st.markdown("**Dernier fichier transport**")
        st.code(str(latest_transport) if latest_transport else "Aucun fichier")
    with right:
        st.markdown("**Dernier fichier météo**")
        st.code(str(latest_weather) if latest_weather else "Aucun fichier")

with tab2:
    st.subheader("Transport temps réel")

    if not events:
        st.warning("Aucun événement transport trouvé.")
    else:
        for row in events:
            with st.container(border=True):
                left, right = st.columns([1, 4])

                with left:
                    st.markdown(f"## 🚇 {row['Ligne']}")

                with right:
                    st.markdown(f"**Destination :** {row['Destination']}")
                    st.markdown(f"**Heure prévue :** {row['Heure prévue']}")
                    st.markdown(f"**Statut :** {format_status(row['Statut'])}")
                    st.markdown(f"**StopPointRef :** `{row['StopPointRef']}`")

with tab3:
    st.subheader("Météo Paris")

    if not weather:
        st.warning("Aucune donnée météo trouvée.")
    else:
        w1, w2, w3, w4 = st.columns(4)
        w1.metric("🌡️ Température moyenne", weather["Température moyenne"])
        w2.metric("🌧️ Précipitations totales", weather["Précipitations totales"])
        w3.metric("💨 Vent moyen", weather["Vent moyen"])
        w4.metric("🕒 Points horaires", weather["Points horaires"])

        st.write(f"**Dernier fichier météo :** {weather['Dernier fichier']}")

with tab4:
    st.subheader("Analytics")

    if summary:
        lines = summary["transport"].get("lines", [])
        if lines:
            df_lines = pd.DataFrame(lines)
            st.markdown("### Résumé batch par ligne")
            st.dataframe(df_lines, use_container_width=True)

    if mapreduce_rows:
        st.markdown("### Résultat MapReduce")
        df_map = pd.DataFrame(mapreduce_rows)
        st.dataframe(df_map, use_container_width=True)
    else:
        st.info("Aucune sortie MapReduce trouvée.")

with tab5:
    st.subheader("Actions")

    if st.button("Relancer ingestion météo"):
        ok, output = run_python_script("scripts/ingestion/ingest_openmeteo_to_hdfs.py")
        st.success("Ingestion météo exécutée avec succès.") if ok else st.error("Échec de l'ingestion météo.")
        st.code(output or "Aucune sortie")

    if st.button("Relancer batch summary"):
        ok, output = run_python_script("scripts/batch/build_transport_weather_summary.py")
        st.success("Batch summary exécuté avec succès.") if ok else st.error("Échec du batch summary.")
        st.code(output or "Aucune sortie")

    if st.button("Relancer MapReduce local"):
        ok, output = run_python_script("scripts/mapreduce/run_mapreduce_local.py")
        st.success("MapReduce local exécuté avec succès.") if ok else st.error("Échec du MapReduce local.")
        st.code(output or "Aucune sortie")

    st.info("Le producer Kafka temps réel reste à lancer séparément si tu veux alimenter la pipeline en continu.")