$ErrorActionPreference = "Stop"

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Content
    )

    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    [System.IO.File]::WriteAllText(
        $Path,
        $Content,
        [System.Text.UTF8Encoding]::new($false)
    )
}

# ---------------------------------------------------------
# 1. scripts/batch/build_transport_weather_summary.py
# ---------------------------------------------------------
$batchScript = @'
from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any


def find_latest_json_file(base_dir: str, prefix: str) -> Path:
    files = sorted(Path(base_dir).rglob(f"{prefix}_*.json"))
    if not files:
        raise FileNotFoundError(f"No file found in {base_dir} with prefix {prefix}")
    return files[-1]


def load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_transport_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    line_ref = payload.get("line_ref", "unknown_line")
    line_label = payload.get("line_label", "unknown_label")
    filtered_journeys = payload.get("filtered_journeys", [])

    destinations = []
    stop_refs = []
    departure_statuses = []

    for item in filtered_journeys:
        matched_calls = item.get("matched_calls", [])
        for call in matched_calls:
            stop_ref = call.get("StopPointRef", {})
            if isinstance(stop_ref, dict):
                stop_ref_value = stop_ref.get("value")
            else:
                stop_ref_value = stop_ref

            if stop_ref_value:
                stop_refs.append(str(stop_ref_value))

            destination_display = call.get("DestinationDisplay", [])
            if isinstance(destination_display, list) and destination_display:
                first = destination_display[0]
                if isinstance(first, dict):
                    destination_value = first.get("value")
                else:
                    destination_value = first
                if destination_value:
                    destinations.append(str(destination_value))

            status = call.get("DepartureStatus")
            if status:
                departure_statuses.append(str(status))

    return {
        "line_ref": line_ref,
        "line_label": line_label,
        "filtered_journey_count": len(filtered_journeys),
        "unique_stop_ref_count": len(sorted(set(stop_refs))),
        "unique_destination_count": len(sorted(set(destinations))),
        "destinations": sorted(set(destinations)),
        "stop_refs": sorted(set(stop_refs)),
        "departure_statuses": sorted(set(departure_statuses)),
    }


def extract_weather_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    weather_payload = payload.get("payload", {})
    hourly = weather_payload.get("hourly", {})

    times = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    precipitations = hourly.get("precipitation", [])
    wind_speeds = hourly.get("wind_speed_10m", [])

    temperature_avg = round(sum(temperatures) / len(temperatures), 2) if temperatures else None
    precipitation_total = round(sum(precipitations), 2) if precipitations else None
    wind_avg = round(sum(wind_speeds) / len(wind_speeds), 2) if wind_speeds else None

    return {
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "timezone": payload.get("timezone"),
        "hourly_row_count": len(times),
        "temperature_avg": temperature_avg,
        "precipitation_total": precipitation_total,
        "wind_speed_avg": wind_avg,
    }


def build_summary(transport_payloads: list[dict[str, Any]], weather_payload: dict[str, Any]) -> dict[str, Any]:
    transport_metrics = [extract_transport_metrics(payload) for payload in transport_payloads]
    weather_metrics = extract_weather_metrics(weather_payload)

    total_filtered_journeys = sum(item["filtered_journey_count"] for item in transport_metrics)
    observed_lines = sorted({item["line_label"] for item in transport_metrics})

    return {
        "summary_type": "transport_weather_batch_summary",
        "transport": {
            "observed_line_count": len(observed_lines),
            "observed_lines": observed_lines,
            "total_filtered_journeys": total_filtered_journeys,
            "lines": transport_metrics,
        },
        "weather": weather_metrics,
    }


def write_summary_json(output_path: Path, summary: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)


def write_summary_csv(output_path: Path, summary: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for line in summary["transport"]["lines"]:
        rows.append({
            "line_label": line["line_label"],
            "line_ref": line["line_ref"],
            "filtered_journey_count": line["filtered_journey_count"],
            "unique_stop_ref_count": line["unique_stop_ref_count"],
            "unique_destination_count": line["unique_destination_count"],
            "temperature_avg": summary["weather"]["temperature_avg"],
            "precipitation_total": summary["weather"]["precipitation_total"],
            "wind_speed_avg": summary["weather"]["wind_speed_avg"],
        })

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "line_label",
                "line_ref",
                "filtered_journey_count",
                "unique_stop_ref_count",
                "unique_destination_count",
                "temperature_avg",
                "precipitation_total",
                "wind_speed_avg",
            ]
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    transport_dir = "data/raw/idfm_stop_monitoring"
    weather_dir = "data/raw/openmeteo"

    latest_weather = find_latest_json_file(weather_dir, "openmeteo_raw")
    weather_payload = load_json(latest_weather)

    latest_transport_files = sorted(Path(transport_dir).rglob("idfm_raw_*.json"))[-10:]
    if not latest_transport_files:
        raise FileNotFoundError("No transport raw files found")

    transport_payloads = [load_json(path) for path in latest_transport_files]

    summary = build_summary(transport_payloads, weather_payload)

    json_output = Path("data/analytics/daily_kpis/transport_weather_summary.json")
    csv_output = Path("outputs/csv/transport_weather_summary.csv")

    write_summary_json(json_output, summary)
    write_summary_csv(csv_output, summary)

    print("=== BATCH TRANSPORT WEATHER SUMMARY ===")
    print(f"Transport files used: {len(latest_transport_files)}")
    print(f"Weather file used: {latest_weather}")
    print(f"Observed lines: {summary['transport']['observed_lines']}")
    print(f"Total filtered journeys: {summary['transport']['total_filtered_journeys']}")
    print(f"JSON output: {json_output}")
    print(f"CSV output: {csv_output}")


if __name__ == "__main__":
    main()
'@
Write-Utf8NoBom -Path "scripts/batch/build_transport_weather_summary.py" -Content $batchScript

# ---------------------------------------------------------
# 2. scripts/tests/test_batch_summary.py
# ---------------------------------------------------------
$testScript = @'
from __future__ import annotations

from pathlib import Path


def main() -> None:
    print("=== BATCH SUMMARY FILE VALIDATION ===")

    required_files = [
        "scripts/batch/build_transport_weather_summary.py",
    ]

    for path in required_files:
        if not Path(path).exists():
            raise FileNotFoundError(f"Missing file: {path}")
        print(f"[OK] {path}")

    print("")
    print("Batch summary structure validation completed successfully.")


if __name__ == "__main__":
    main()
'@
Write-Utf8NoBom -Path "scripts/tests/test_batch_summary.py" -Content $testScript

Write-Host ""
Write-Host "Batch transport-weather summary files created successfully." -ForegroundColor Green
Write-Host ""
Write-Host "Run now:" -ForegroundColor Cyan
Write-Host "python .\scripts\tests\test_batch_summary.py"
Write-Host "python .\scripts\batch\build_transport_weather_summary.py"