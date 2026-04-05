from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import requests
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.hdfs_paths import build_partitioned_local_path


def load_yaml(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_app_config() -> dict[str, Any]:
    return load_yaml("config/app_config.yaml")


def load_openmeteo_config() -> dict[str, Any]:
    return load_yaml("config/api/openmeteo.yaml")


def fetch_openmeteo_data(config: dict[str, Any]) -> dict[str, Any]:
    endpoint = config["openmeteo"]["base_url"]
    params = {
        "latitude": config["openmeteo"]["latitude"],
        "longitude": config["openmeteo"]["longitude"],
        "hourly": config["openmeteo"]["hourly"],
        "forecast_days": config["openmeteo"]["forecast_days"],
        "timezone": config["openmeteo"]["timezone"],
    }

    response = requests.get(endpoint, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def build_weather_message(payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "openmeteo",
        "ingestion_time_utc": datetime.now(UTC).isoformat(),
        "latitude": config["openmeteo"]["latitude"],
        "longitude": config["openmeteo"]["longitude"],
        "timezone": config["openmeteo"]["timezone"],
        "payload": payload,
    }


def write_weather_raw(base_dir: str, message: dict[str, Any]) -> Path:
    now = datetime.now(UTC)
    target_dir = build_partitioned_local_path(base_dir, now)
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"openmeteo_raw_{now.strftime('%Y%m%d_%H%M%S_%f')}.json"
    target_file = target_dir / filename

    with open(target_file, "w", encoding="utf-8") as file:
        json.dump(message, file, indent=2, ensure_ascii=False)

    return target_file


def main() -> None:
    app_config = load_app_config()
    openmeteo_config = load_openmeteo_config()

    raw_weather_local = app_config["paths"]["raw_weather_local"]

    payload = fetch_openmeteo_data(openmeteo_config)
    message = build_weather_message(payload, openmeteo_config)
    written_file = write_weather_raw(raw_weather_local, message)

    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])

    print("=== OPEN-METEO TO RAW STORAGE ===")
    print(f"Latitude: {openmeteo_config['openmeteo']['latitude']}")
    print(f"Longitude: {openmeteo_config['openmeteo']['longitude']}")
    print(f"Hourly rows: {len(times)}")
    print(f"Written file: {written_file}")


if __name__ == "__main__":
    main()