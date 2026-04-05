from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

PROJECT_ROOT = Path(__file__).resolve().parent
PARIS_TZ = ZoneInfo("Europe/Paris")


components.html(
    """
    <script>
        setTimeout(function() {
            window.parent.location.reload();
        }, 60000);
    </script>
    """,
    height=0,
)


def find_latest_files(base_dir: str, pattern: str, limit: int = 30) -> list[Path]:
    files = sorted((PROJECT_ROOT / base_dir).rglob(pattern))
    return files[-limit:]


@st.cache_data(ttl=30)
def load_json_file(path_str: str) -> dict[str, Any] | None:
    path = Path(path_str)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(ttl=30)
def load_many_json(paths: list[str]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for path_str in paths:
        payload = load_json_file(path_str)
        if payload is not None:
            payloads.append(payload)
    return payloads


@st.cache_data(ttl=300)
def load_stop_name_mapping() -> dict[str, str]:
    path = PROJECT_ROOT / "data" / "reference" / "processed" / "stop_ref_to_station_name.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def resolve_stop_name(stop_ref: str | None, mapping: dict[str, str]) -> str:
    if not stop_ref:
        return "Station inconnue"
    return mapping.get(stop_ref, stop_ref)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def format_paris_time(value: str | None) -> str:
    dt = parse_dt(value)
    if dt is None:
        return "Heure inconnue"
    return dt.astimezone(PARIS_TZ).strftime("%d/%m/%Y %H:%M:%S")


def format_status(status: str | None) -> str:
    mapping = {
        "ON_TIME": "A l'heure",
        "DELAYED": "Retarde",
        "EARLY": "En avance",
        "UNKNOWN": "Inconnu",
        None: "Inconnu",
    }
    return mapping.get(status, str(status))


def normalize_line(line_label: str) -> str:
    return line_label.replace("metro_", "")


def count_raw_files(base_dir: str, prefix: str) -> int:
    return len(list((PROJECT_ROOT / base_dir).rglob(f"{prefix}_*.json")))


def latest_weather_file() -> Path | None:
    files = sorted((PROJECT_ROOT / "data" / "raw" / "openmeteo").rglob("openmeteo_raw_*.json"))
    return files[-1] if files else None


def describe_weather(temp: float | None, rain: float | None, wind: float | None) -> str:
    if temp is None or rain is None or wind is None:
        return "Meteo actuelle a Paris : information indisponible."

    if temp < 5:
        temp_label = "tres froid"
    elif temp < 12:
        temp_label = "frais"
    elif temp < 20:
        temp_label = "doux"
    else:
        temp_label = "chaud"

    if rain == 0:
        rain_label = "sec"
    elif rain <= 2:
        rain_label = "legerement pluvieux"
    else:
        rain_label = "pluvieux"

    if wind < 15:
        wind_label = "peu venteux"
    elif wind < 30:
        wind_label = "venteux"
    else:
        wind_label = "tres venteux"

    return f"Meteo actuelle a Paris : {temp_label}, {rain_label}, {wind_label}."


def extract_weather_metrics() -> dict[str, Any] | None:
    latest_file = latest_weather_file()
    if latest_file is None:
        return None

    payload = load_json_file(str(latest_file))
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

    temp_avg = avg(temperatures)
    rain_total = round(sum(precipitations), 2) if precipitations else None
    wind_avg = avg(wind_speeds)

    return {
        "fichier": latest_file.name,
        "points_horaires": len(times),
        "temperature_moyenne": temp_avg,
        "precipitations_totales": rain_total,
        "vent_moyen": wind_avg,
        "description": describe_weather(temp_avg, rain_total, wind_avg),
    }


def extract_live_trains(limit_files: int = 30) -> list[dict[str, Any]]:
    files = find_latest_files("data/raw/idfm_stop_monitoring", "idfm_raw_*.json", limit=limit_files)
    payloads = load_many_json([str(p) for p in files])

    now = datetime.now(timezone.utc)
    trains: dict[str, dict[str, Any]] = {}

    for payload in payloads:
        line_label = payload.get("line_label", "unknown")
        line_ref = payload.get("line_ref", "unknown")
        filtered_journeys = payload.get("filtered_journeys", [])

        if not isinstance(filtered_journeys, list):
            continue

        for item in filtered_journeys:
            journey = item.get("journey", {})
            if not isinstance(journey, dict):
                continue

            dated_ref_obj = journey.get("DatedVehicleJourneyRef", {})
            if isinstance(dated_ref_obj, dict):
                train_id = dated_ref_obj.get("value", "")
            else:
                train_id = str(dated_ref_obj)

            if not train_id:
                continue

            destination = "Destination inconnue"
            destination_name = journey.get("DestinationName", [])
            if isinstance(destination_name, list) and destination_name:
                first = destination_name[0]
                if isinstance(first, dict):
                    destination = str(first.get("value", destination))
                elif isinstance(first, str):
                    destination = first

            estimated_calls_container = journey.get("EstimatedCalls", {})
            estimated_calls = estimated_calls_container.get("EstimatedCall", [])
            if not isinstance(estimated_calls, list):
                estimated_calls = []

            future_calls = []
            for call in estimated_calls:
                arrival = call.get("ExpectedArrivalTime")
                departure = call.get("ExpectedDepartureTime")
                best_time = arrival or departure
                best_dt = parse_dt(best_time)

                if best_dt is None:
                    continue

                if best_dt >= now:
                    stop_ref_raw = call.get("StopPointRef", {})
                    if isinstance(stop_ref_raw, dict):
                        stop_ref = stop_ref_raw.get("value")
                    else:
                        stop_ref = stop_ref_raw

                    status = call.get("DepartureStatus", "UNKNOWN")
                    approach = call.get("ArrivalProximityText", {})
                    if isinstance(approach, dict):
                        approach_text = approach.get("value")
                    else:
                        approach_text = None

                    future_calls.append(
                        {
                            "stop_ref": stop_ref,
                            "expected_time": best_time,
                            "expected_dt": best_dt,
                            "status": status,
                            "approach": approach_text,
                        }
                    )

            if not future_calls:
                continue

            future_calls.sort(key=lambda x: x["expected_dt"])
            next_call = future_calls[0]

            existing = trains.get(train_id)
            existing_dt = parse_dt(existing["heure_prevue_raw"]) if existing else None

            if existing is None or existing_dt is None or next_call["expected_dt"] < existing_dt:
                trains[train_id] = {
                    "train_id": train_id,
                    "line_label": line_label,
                    "ligne": normalize_line(line_label),
                    "line_ref": line_ref,
                    "destination": destination,
                    "prochain_arret_ref": next_call["stop_ref"],
                    "heure_prevue_raw": next_call["expected_time"],
                    "heure_prevue": format_paris_time(next_call["expected_time"]),
                    "statut_brut": next_call["status"],
                    "statut": format_status(next_call["status"]),
                    "approche": next_call["approach"],
                    "arrets_a_venir": future_calls[:5],
                }

    result = list(trains.values())
    result.sort(key=lambda x: (x["ligne"], x["destination"], x["heure_prevue_raw"]))
    return result


def build_aggregated_view(trains: list[dict[str, Any]], mapping_stations: dict[str, str]) -> pd.DataFrame:
    rows = []
    for train in trains:
        rows.append(
            {
                "Ligne": train["ligne"],
                "Destination": train["destination"],
                "Prochain arret": resolve_stop_name(train["prochain_arret_ref"], mapping_stations),
                "Heure prevue": train["heure_prevue"],
                "Statut": train["statut"],
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    aggregated = (
        df.groupby(["Ligne", "Destination", "Prochain arret", "Statut"], as_index=False)
          .agg(
              Nombre_metros=("Ligne", "count"),
              Premiere_heure_prevue=("Heure prevue", "min"),
          )
          .sort_values(by=["Ligne", "Destination", "Premiere_heure_prevue"])
    )
    return aggregated


st.set_page_config(page_title="Suivi temps reel des metros", layout="wide")

mapping_stations = load_stop_name_mapping()
trains = extract_live_trains()
weather = extract_weather_metrics()
now_paris = datetime.now(PARIS_TZ).strftime("%d/%m/%Y %H:%M:%S")

st.title("Suivi temps reel des metros")
st.caption("Mise a jour automatique toutes les 60 secondes")
st.write(f"**Heure locale Paris :** {now_paris}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Kafka", "Actif")
m2.metric("Fichiers transport", count_raw_files("data/raw/idfm_stop_monitoring", "idfm_raw"))
m3.metric("Metros affiches", len(trains))
m4.metric("Rafraichissement", "60 s")

if weather is not None:
    st.info(weather["description"])

st.divider()

c1, c2 = st.columns(2)

all_lines = sorted({train["ligne"] for train in trains})
selected_lines = c1.multiselect(
    "Filtre ligne",
    options=all_lines,
    default=all_lines,
)

all_statuses = sorted({train["statut"] for train in trains})
selected_statuses = c2.multiselect(
    "Filtre statut",
    options=all_statuses,
    default=all_statuses,
)

filtered_trains = [
    train for train in trains
    if (train["ligne"] in selected_lines if selected_lines else True)
    and (train["statut"] in selected_statuses if selected_statuses else True)
]

tab1, tab2, tab3 = st.tabs(["Transport temps reel", "Meteo Paris", "Vue tableau"])

with tab1:
    st.subheader("Liste des metros en circulation")

    if not filtered_trains:
        st.warning("Aucun metro ne correspond aux filtres actuels.")
    else:
        aggregated_df = build_aggregated_view(filtered_trains, mapping_stations)

        st.markdown("### Vue synthetique agregee")
        st.dataframe(aggregated_df, use_container_width=True, hide_index=True)

        st.markdown("### Detail par metro")
        for train in filtered_trains:
            with st.container(border=True):
                left, right = st.columns([1, 4])

                with left:
                    st.markdown(f"## Ligne {train['ligne']}")

                with right:
                    st.markdown(f"**Destination :** {train['destination']}")
                    st.markdown(f"**Prochain arret surveille :** {resolve_stop_name(train['prochain_arret_ref'], mapping_stations)}")
                    st.markdown(f"**Heure prevue :** {train['heure_prevue']}")
                    st.markdown(f"**Statut :** {train['statut']}")
                    if train["approche"]:
                        st.markdown(f"**Information d'approche :** {train['approche']}")

                    detail_rows = []
                    for call in train["arrets_a_venir"]:
                        detail_rows.append(
                            {
                                "Station": resolve_stop_name(call["stop_ref"], mapping_stations),
                                "Heure prevue": format_paris_time(call["expected_time"]),
                                "Statut": format_status(call["status"]),
                            }
                        )

                    st.markdown("**Arrets estimes a venir**")
                    st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

        st.info("Les donnees affichent des passages estimes sur les arrets surveilles, et non une geolocalisation GPS continue des rames.")

with tab2:
    st.subheader("Meteo Paris")

    if weather is None:
        st.warning("Aucune donnee meteo trouvee.")
    else:
        w1, w2, w3, w4 = st.columns(4)
        w1.metric("Temperature moyenne", weather["temperature_moyenne"])
        w2.metric("Precipitations totales", weather["precipitations_totales"])
        w3.metric("Vent moyen", weather["vent_moyen"])
        w4.metric("Points horaires", weather["points_horaires"])

        st.write(f"**Dernier fichier meteo :** {weather['fichier']}")
        st.write(f"**Resume meteo :** {weather['description']}")

with tab3:
    st.subheader("Vue tableau")

    if not filtered_trains:
        st.info("Aucune ligne a afficher.")
    else:
        rows = []
        for train in filtered_trains:
            rows.append(
                {
                    "Ligne": train["ligne"],
                    "Destination": train["destination"],
                    "Prochain arret": resolve_stop_name(train["prochain_arret_ref"], mapping_stations),
                    "Heure prevue": train["heure_prevue"],
                    "Statut": train["statut"],
                    "Identifiant train": train["train_id"],
                }
            )

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)