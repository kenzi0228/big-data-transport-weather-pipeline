from __future__ import annotations

import csv
import json
from pathlib import Path


RAW_DIR = Path("data/reference/raw")
OUTPUT_JSON = Path("data/reference/processed/stop_ref_to_station_name.json")


def detect_delimiter(sample: str) -> str:
    if sample.count(";") >= sample.count(","):
        return ";"
    return ","


def find_latest_reference_csv() -> Path:
    files = sorted(RAW_DIR.glob("idfm_arrets_*.csv"))
    if not files:
        raise FileNotFoundError(
            "No reference CSV found in data/reference/raw. "
            "Run scripts/reference/ingest_idfm_stops_reference.py first."
        )
    return files[-1]


def main() -> None:
    input_csv = find_latest_reference_csv()

    with open(input_csv, "r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(4096)
        delimiter = detect_delimiter(sample)
        file.seek(0)

        reader = csv.DictReader(file, delimiter=delimiter)
        fieldnames = reader.fieldnames or []

        required = {"ArRId", "ArRName"}
        missing = required - set(fieldnames)
        if missing:
            raise KeyError(f"Missing required columns in CSV: {sorted(missing)}")

        mapping: dict[str, str] = {}

        for row in reader:
            arr_id = (row.get("ArRId") or "").strip()
            arr_name = (row.get("ArRName") or "").strip()

            if not arr_id or not arr_name:
                continue

            stop_ref = f"STIF:StopPoint:Q:{arr_id}:"
            mapping[stop_ref] = arr_name

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
        json.dump(mapping, file, indent=2, ensure_ascii=False)

    print("=== STOP REF TO STATION NAME MAPPING ===")
    print(f"Input CSV: {input_csv}")
    print(f"Output JSON: {OUTPUT_JSON}")
    print(f"Mapped stop refs: {len(mapping)}")


if __name__ == "__main__":
    main()