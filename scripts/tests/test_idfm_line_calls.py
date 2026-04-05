from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests
import yaml


def load_yaml(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_api_key_from_file(path: str) -> str:
    key_path = Path(path)
    if not key_path.exists():
        raise FileNotFoundError(f"Missing API key file: {path}")

    api_key = key_path.read_text(encoding="utf-8").strip()
    if not api_key:
        raise ValueError(f"API key file is empty: {path}")

    if api_key == "REPLACE_WITH_YOUR_REAL_IDFM_API_KEY":
        raise ValueError("Please replace the placeholder value in secrets/idfm_api_key.txt")

    return api_key


def main() -> None:
    credentials_path = Path("config/api/idfm_credentials.yaml")
    lines_path = Path("config/api/idfm_lines.yaml")

    if not credentials_path.exists():
        raise FileNotFoundError("Missing config/api/idfm_credentials.yaml")

    credentials = load_yaml(str(credentials_path))
    lines_config = load_yaml(str(lines_path))

    api_key_file = credentials["idfm"]["api_key_file"]
    api_key = load_api_key_from_file(api_key_file)
    timeout_seconds = credentials["idfm"]["timeout_seconds"]

    base_url = credentials["idfm"].get(
        "line_request_base_url",
        "https://prim.iledefrance-mobilites.fr/marketplace/requete-ligne"
    )

    enabled_lines = [line for line in lines_config["lines"] if line.get("enabled", False)]
    if not enabled_lines:
        raise ValueError("No enabled lines in config/api/idfm_lines.yaml")

    output_dir = Path("outputs/reports/idfm_line_tests")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== IDFM LINE REQUEST TEST ===")

    for line in enabled_lines:
        line_ref = line["line_ref"]
        line_label = line["line_label"]

        headers = {
            "Accept": "application/json",
            "apiKey": api_key
        }
        params = {
            "LineRef": line_ref
        }

        try:
            response = requests.get(
                base_url,
                headers=headers,
                params=params,
                timeout=timeout_seconds
            )

            print(f"[{response.status_code}] {line_label} -> {line_ref}")

            if response.status_code == 200:
                payload = response.json()

                output_file = output_dir / f"{line_label}.json"
                with open(output_file, "w", encoding="utf-8") as file:
                    json.dump(payload, file, indent=2, ensure_ascii=False)

                deliveries = (
                    payload.get("Siri", {})
                    .get("ServiceDelivery", {})
                    .get("EstimatedTimetableDelivery", [])
                )

                journey_count = 0
                for delivery in deliveries:
                    frames = delivery.get("EstimatedJourneyVersionFrame", [])
                    if not isinstance(frames, list):
                        continue

                    for frame in frames:
                        journeys = frame.get("EstimatedVehicleJourney", [])
                        if isinstance(journeys, list):
                            journey_count += len(journeys)

                print(f"    journeys={journey_count} saved={output_file}")
            else:
                print("    response body:")
                print(f"    {response.text}")

        except Exception as exc:
            print(f"[ERROR] {line_label} -> {line_ref} error={exc}")


if __name__ == "__main__":
    main()