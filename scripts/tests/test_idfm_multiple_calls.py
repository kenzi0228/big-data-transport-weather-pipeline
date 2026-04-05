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

    output_dir = Path("outputs/reports/idfm_tests")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== IDFM MULTI STOP TEST ===")

    for stop in enabled_stops:
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

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout_seconds
            )

            print(f"[{response.status_code}] {stop_label} -> {monitoring_ref} line_ref={line_ref}")

            if response.status_code == 200:
                payload = response.json()
                output_file = output_dir / f"{stop_label}.json"
                with open(output_file, "w", encoding="utf-8") as file:
                    json.dump(payload, file, indent=2, ensure_ascii=False)

                delivery = (
                    payload.get("Siri", {})
                    .get("ServiceDelivery", {})
                    .get("StopMonitoringDelivery", [])
                )

                visits = []
                if delivery and isinstance(delivery, list):
                    visits = delivery[0].get("MonitoredStopVisit", [])

                print(f"    visits={len(visits)} saved={output_file}")
            else:
                print("    response body:")
                print(f"    {response.text}")

        except Exception as exc:
            print(f"[ERROR] {stop_label} -> {monitoring_ref} error={exc}")


if __name__ == "__main__":
    main()