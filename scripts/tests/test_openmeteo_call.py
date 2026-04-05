from __future__ import annotations

import json
from pathlib import Path

import requests


def main() -> None:
    latitude = 48.8566
    longitude = 2.3522

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,precipitation,wind_speed_10m",
        "forecast_days": 1
    }

    print("=== OPEN-METEO TEST ===")
    print(f"URL: {url}")
    print(f"Params: {params}")

    response = requests.get(url, params=params, timeout=20)
    print(f"HTTP status: {response.status_code}")
    response.raise_for_status()

    payload = response.json()

    output_dir = Path("outputs/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "openmeteo_test_response.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    print(f"Response saved to: {output_file}")

    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    print(f"Hourly rows: {len(times)}")


if __name__ == "__main__":
    main()