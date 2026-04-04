from __future__ import annotations

import json
from pathlib import Path


def assert_exists(path: str) -> None:
    if not Path(path).exists():
        raise FileNotFoundError(f"Missing required file: {path}")


def assert_json_has_keys(path: str, required_keys: list[str]) -> None:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    for key in required_keys:
        if key not in data:
            raise KeyError(f"Missing key '{key}' in {path}")


def main() -> None:
    print("=== PIPELINE VALIDATION TESTS ===")

    required_files = [
        "config/app_config.yaml",
        "data/sample/transport_sample.json",
        "data/sample/weather_sample.json",
        "scripts/ingestion/ingest_transport.py",
        "scripts/ingestion/ingest_weather.py",
        "scripts/streaming/spark_streaming_job.py",
        "scripts/batch/spark_batch_job.py",
        "data/processed/streaming/streaming_indicators.json",
        "data/processed/batch/batch_summary.json",
        "outputs/csv/transport_weather_join.csv",
    ]

    for file_path in required_files:
        assert_exists(file_path)
        print(f"[OK] {file_path}")

    assert_json_has_keys(
        "data/processed/streaming/streaming_indicators.json",
        [
            "total_events",
            "delayed_events_over_threshold",
            "average_delay_all_events",
            "average_delay_by_line",
        ]
    )
    print("[OK] streaming_indicators.json structure")

    assert_json_has_keys(
        "data/processed/batch/batch_summary.json",
        [
            "total_transport_events",
            "total_weather_events",
            "matched_events",
            "average_delay_all",
            "average_delay_heavy_rain",
            "average_delay_no_heavy_rain",
        ]
    )
    print("[OK] batch_summary.json structure")

    print("")
    print("Pipeline validation completed successfully.")


if __name__ == "__main__":
    main()