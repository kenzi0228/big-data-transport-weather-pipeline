from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.idfm_line_parser import extract_estimated_journeys, filter_journeys_by_stop_refs


def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main() -> None:
    config = load_yaml("config/api/idfm_lines.yaml")

    files = {
        "metro_6": Path("outputs/reports/idfm_line_tests/metro_6.json"),
        "metro_7": Path("outputs/reports/idfm_line_tests/metro_7.json"),
    }

    print("=== IDFM LINE FILTERING TEST ===")

    for line in config["lines"]:
        if not line.get("enabled", False):
            continue

        line_label = line["line_label"]
        target_stop_refs = line.get("target_stop_refs", [])

        file_path = files.get(line_label)
        if file_path is None or not file_path.exists():
            print(f"[MISSING] {line_label} -> {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as file:
            payload = json.load(file)

        journeys = extract_estimated_journeys(payload)
        filtered_journeys = filter_journeys_by_stop_refs(journeys, target_stop_refs)

        print(f"[OK] {line_label}")
        print(f"     all_journeys={len(journeys)}")
        print(f"     filtered_journeys={len(filtered_journeys)}")
        print(f"     target_stop_refs={target_stop_refs}")


if __name__ == "__main__":
    main()