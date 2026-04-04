from __future__ import annotations

from pathlib import Path
import yaml


def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main() -> None:
    print("=== IDFM CONFIG VALIDATION ===")

    required_files = [
        "config/app_config.yaml",
        "config/api/idfm_stops.yaml",
        "config/api/idfm_credentials.template.yaml",
        "scripts/utils/idfm_parser.py",
        "scripts/ingestion/producer_idfm_to_kafka.py",
    ]

    for path in required_files:
        if not Path(path).exists():
            raise FileNotFoundError(f"Missing file: {path}")
        print(f"[OK] {path}")

    stops_config = load_yaml("config/api/idfm_stops.yaml")
    stops = stops_config.get("stops", [])

    if not isinstance(stops, list) or not stops:
        raise ValueError("No stops declared in config/api/idfm_stops.yaml")

    enabled_count = 0
    for stop in stops:
        if "monitoring_ref" not in stop:
            raise KeyError("A stop is missing monitoring_ref")
        if "label" not in stop:
            raise KeyError("A stop is missing label")
        if stop.get("enabled", False):
            enabled_count += 1

    print(f"[OK] Stops declared: {len(stops)}")
    print(f"[OK] Enabled stops: {enabled_count}")

    print("")
    print("IDFM configuration validation completed successfully.")


if __name__ == "__main__":
    main()