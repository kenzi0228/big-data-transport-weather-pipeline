from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests
import yaml


def load_yaml(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main() -> None:
    credentials_path = Path("config/api/idfm_credentials.yaml")
    stops_path = Path("config/api/idfm_stops.yaml")

    if not credentials_path.exists():
        raise FileNotFoundError("Missing config/api/idfm_credentials.yaml")

    credentials = load_yaml(str(credentials_path))
    stops_config = load_yaml(str(stops_path))

    api_key = credentials["idfm"]["api_key"]
    base_url = credentials["idfm"]["base_url"]
    timeout_seconds = credentials["idfm"]["timeout_seconds"]
    maximum_stop_visits = credentials["idfm"]["maximum_stop_visits"]

    enabled_stops = [stop for stop in stops_config["stops"] if stop.get("enabled", False)]
    if not enabled_stops:
        raise ValueError("No enabled stops in config/api/idfm_stops.yaml")

    stop = enabled_stops[0]
    monitoring_ref = stop["monitoring_ref"]
    stop_label = stop["label"]
    line_ref = stop.get("line_ref", "")

    url = base_url
    headers = {
        "Accept": "application/json",
        "apiKey": api_key
    }
    params = {
        "MonitoringRef": monitoring_ref,
        "MaximumStopVisits": maximum_stop_visits
    }

    if line_ref:
        params["LineRef"] = line_ref

    print("=== IDFM SINGLE CALL TEST ===")
    print(f"Stop label: {stop_label}")
    print(f"MonitoringRef: {monitoring_ref}")
    print(f"LineRef: {line_ref}")
    print(f"URL: {url}")
    print(f"Params: {params}")

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=timeout_seconds
    )

    print(f"HTTP status: {response.status_code}")

    if response.status_code != 200:
        print("Response body:")
        print(response.text)
        response.raise_for_status()

    payload = response.json()

    output_dir = Path("outputs/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "idfm_single_test_response.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    print(f"Response saved to: {output_file}")

    delivery = (
        payload.get("Siri", {})
        .get("ServiceDelivery", {})
        .get("StopMonitoringDelivery", [])
    )

    if delivery and isinstance(delivery, list):
        visits = delivery[0].get("MonitoredStopVisit", [])
        print(f"MonitoredStopVisit count: {len(visits)}")
    else:
        print("No StopMonitoringDelivery found in payload.")


if __name__ == "__main__":
    main()