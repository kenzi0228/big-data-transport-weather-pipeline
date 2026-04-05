from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def load_transport_files(base_dir: str) -> list[dict]:
    files = sorted(Path(base_dir).rglob("idfm_raw_*.json"))[-20:]
    payloads = []

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as file:
            payloads.append(json.load(file))

    return payloads


def run_local_mapreduce(payloads: list[dict]) -> Counter:
    counter: Counter = Counter()

    for payload in payloads:
        line_label = payload.get("line_label", "unknown_line")
        filtered_journeys = payload.get("filtered_journeys", [])

        if not isinstance(filtered_journeys, list):
            continue

        for item in filtered_journeys:
            matched_calls = item.get("matched_calls", [])
            if not isinstance(matched_calls, list):
                continue

            for call in matched_calls:
                destination_display = call.get("DestinationDisplay", [])
                destination = "unknown_destination"

                if isinstance(destination_display, list) and destination_display:
                    first = destination_display[0]
                    if isinstance(first, dict):
                        destination = str(first.get("value", "unknown_destination")).strip()
                    elif isinstance(first, str):
                        destination = first.strip()

                key = f"{line_label}|{destination}"
                counter[key] += 1

    return counter


def write_output(counter: Counter, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        for key, count in sorted(counter.items()):
            file.write(f"{key}\t{count}\n")


def main() -> None:
    payloads = load_transport_files("data/raw/idfm_stop_monitoring")
    if not payloads:
        raise FileNotFoundError("No transport raw files found")

    counter = run_local_mapreduce(payloads)

    output_path = Path("data/analytics/daily_kpis/mapreduce_line_destination_counts.txt")
    write_output(counter, output_path)

    print("=== LOCAL MAPREDUCE TEST ===")
    print(f"Transport payloads used: {len(payloads)}")
    print(f"Distinct keys: {len(counter)}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()