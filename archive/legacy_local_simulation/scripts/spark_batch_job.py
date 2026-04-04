from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
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


def compute_batch_metrics(
    transport_records: list[dict[str, Any]],
    weather_records: list[dict[str, Any]],
    rainfall_threshold: float
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    transport_df = pd.DataFrame(transport_records)
    weather_df = pd.DataFrame(weather_records)

    merged_df = pd.merge(transport_df, weather_df, on="timestamp", how="left")
    merged_df["heavy_rain"] = merged_df["rainfall_mm"].fillna(0) > rainfall_threshold

    avg_all = merged_df["delay_minutes"].mean()
    avg_heavy_rain = merged_df.loc[merged_df["heavy_rain"], "delay_minutes"].mean()
    avg_no_heavy_rain = merged_df.loc[~merged_df["heavy_rain"], "delay_minutes"].mean()

    summary = {
        "total_transport_events": int(len(transport_df)),
        "total_weather_events": int(len(weather_df)),
        "matched_events": int(len(merged_df)),
        "average_delay_all": round(float(avg_all), 2) if pd.notna(avg_all) else 0.0,
        "average_delay_heavy_rain": round(float(avg_heavy_rain), 2) if pd.notna(avg_heavy_rain) else 0.0,
        "average_delay_no_heavy_rain": round(float(avg_no_heavy_rain), 2) if pd.notna(avg_no_heavy_rain) else 0.0
    }

    return merged_df.to_dict(orient="records"), summary


def save_outputs(
    merged_records: list[dict[str, Any]],
    summary: dict[str, Any],
    batch_output_dir: str,
    csv_output_dir: str
) -> tuple[Path, Path]:
    batch_dir = Path(batch_output_dir)
    csv_dir = Path(csv_output_dir)

    batch_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)

    json_output = batch_dir / "batch_summary.json"
    csv_output = csv_dir / "transport_weather_join.csv"

    with open(json_output, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    pd.DataFrame(merged_records).to_csv(csv_output, index=False, encoding="utf-8")

    return json_output, csv_output


def main() -> None:
    config = load_config()

    transport_raw_dir = config["paths"]["transport_raw_output"]
    weather_raw_dir = config["paths"]["weather_raw_output"]
    batch_output_dir = config["paths"]["batch_output"]
    csv_output_dir = config["paths"]["csv_output"]
    rainfall_threshold = config["processing"]["rainfall_threshold_mm"]

    latest_transport_file = find_latest_file(transport_raw_dir, "transport_raw")
    latest_weather_file = find_latest_file(weather_raw_dir, "weather_raw")

    transport_records = load_records(latest_transport_file)
    weather_records = load_records(latest_weather_file)

    merged_records, summary = compute_batch_metrics(
        transport_records,
        weather_records,
        rainfall_threshold
    )

    json_output, csv_output = save_outputs(
        merged_records,
        summary,
        batch_output_dir,
        csv_output_dir
    )

    print("=== BATCH PIPELINE STEP ===")
    print(f"Transport input: {latest_transport_file}")
    print(f"Weather input: {latest_weather_file}")
    print(f"Average delay all: {summary['average_delay_all']} minutes")
    print(f"Average delay in heavy rain: {summary['average_delay_heavy_rain']} minutes")
    print(f"Summary JSON: {json_output}")
    print(f"Join CSV: {csv_output}")


if __name__ == "__main__":
    main()