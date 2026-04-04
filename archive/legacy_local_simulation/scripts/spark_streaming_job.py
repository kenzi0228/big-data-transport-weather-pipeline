from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str = "config/app_config.yaml") -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def find_latest_file(directory: str, prefix: str) -> Path:
    files = sorted(Path(directory).glob(f"{prefix}_*.json"))
    if not files:
        raise FileNotFoundError(f"No file found in {directory} with prefix {prefix}")
    return files[-1]


def load_records(file_path: Path) -> list[dict[str, Any]]:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def compute_stream_metrics(records: list[dict[str, Any]], delay_threshold: int) -> dict[str, Any]:
    total_events = len(records)
    delayed_events = [record for record in records if record["delay_minutes"] > delay_threshold]

    average_delay = 0.0
    if total_events > 0:
        average_delay = sum(record["delay_minutes"] for record in records) / total_events

    line_stats: dict[str, list[int]] = {}
    for record in records:
        line_id = record["line_id"]
        line_stats.setdefault(line_id, []).append(record["delay_minutes"])

    average_delay_by_line = {
        line_id: round(sum(delays) / len(delays), 2)
        for line_id, delays in line_stats.items()
    }

    return {
        "total_events": total_events,
        "delayed_events_over_threshold": len(delayed_events),
        "average_delay_all_events": round(average_delay, 2),
        "average_delay_by_line": average_delay_by_line,
    }


def save_metrics(metrics: dict[str, Any], output_dir: str) -> Path:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    output_file = target_dir / "streaming_indicators.json"
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2, ensure_ascii=False)

    return output_file


def main() -> None:
    config = load_config()

    transport_raw_dir = config["paths"]["transport_raw_output"]
    streaming_output_dir = config["paths"]["streaming_output"]
    delay_threshold = config["processing"]["delay_threshold_minutes"]

    latest_transport_file = find_latest_file(transport_raw_dir, "transport_raw")
    transport_records = load_records(latest_transport_file)

    metrics = compute_stream_metrics(transport_records, delay_threshold)
    output_file = save_metrics(metrics, streaming_output_dir)

    print("=== STREAMING PIPELINE STEP ===")
    print(f"Input file: {latest_transport_file}")
    print(f"Total events: {metrics['total_events']}")
    print(f"Delayed events over threshold: {metrics['delayed_events_over_threshold']}")
    print(f"Average delay: {metrics['average_delay_all_events']} minutes")
    print(f"Output file: {output_file}")


if __name__ == "__main__":
    main()