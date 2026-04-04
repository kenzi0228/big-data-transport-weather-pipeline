from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any

import yaml


def load_config(config_path: str = "config/app_config.yaml") -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json_records(input_path: str) -> list[dict[str, Any]]:
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_directory(path: str) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_raw_transport_data(records: list[dict[str, Any]], output_dir: str) -> Path:
    target_dir = ensure_directory(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = target_dir / f"transport_raw_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    return output_file


def validate_transport_record(record: dict[str, Any]) -> bool:
    required_fields = {
        "event_id",
        "timestamp",
        "line_id",
        "vehicle_id",
        "stop_id",
        "delay_minutes",
        "status",
        "latitude",
        "longitude",
    }
    return required_fields.issubset(record.keys())


def main() -> None:
    config = load_config()

    input_path = config["paths"]["transport_input"]
    output_dir = config["paths"]["transport_raw_output"]

    records = load_json_records(input_path)

    valid_records = [record for record in records if validate_transport_record(record)]
    invalid_count = len(records) - len(valid_records)

    output_file = save_raw_transport_data(valid_records, output_dir)

    print("=== INGESTION TRANSPORT ===")
    print(f"Fichier source : {input_path}")
    print(f"Nombre total d'enregistrements : {len(records)}")
    print(f"Enregistrements valides : {len(valid_records)}")
    print(f"Enregistrements invalides : {invalid_count}")
    print(f"Fichier brut généré : {output_file}")


if __name__ == "__main__":
    main()