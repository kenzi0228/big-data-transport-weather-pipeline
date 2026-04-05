from __future__ import annotations

import json
from pathlib import Path


def extract_stop_names(payload: dict) -> list[str]:
    names = set()

    deliveries = (
        payload.get("Siri", {})
        .get("ServiceDelivery", {})
        .get("EstimatedTimetableDelivery", [])
    )

    for delivery in deliveries:
        frames = delivery.get("EstimatedJourneyVersionFrame", [])
        if not isinstance(frames, list):
            continue

        for frame in frames:
            journeys = frame.get("EstimatedVehicleJourney", [])
            if not isinstance(journeys, list):
                continue

            for journey in journeys:
                estimated_calls = journey.get("EstimatedCalls", {})
                calls = estimated_calls.get("EstimatedCall", [])
                if not isinstance(calls, list):
                    continue

                for call in calls:
                    stop_name = call.get("StopPointName")
                    if isinstance(stop_name, dict):
                        value = stop_name.get("value")
                        if value:
                            names.add(str(value).strip())
                    elif isinstance(stop_name, str):
                        names.add(stop_name.strip())

    return sorted(names)


def main() -> None:
    files = [
        Path("outputs/reports/idfm_line_tests/metro_6.json"),
        Path("outputs/reports/idfm_line_tests/metro_7.json"),
    ]

    print("=== INSPECT IDFM LINE STOP NAMES ===")

    for file_path in files:
        if not file_path.exists():
            print(f"[MISSING] {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as file:
            payload = json.load(file)

        stop_names = extract_stop_names(payload)

        print("")
        print(f"File: {file_path}")
        print(f"Unique stop names: {len(stop_names)}")
        for name in stop_names:
            print(f" - {name}")


if __name__ == "__main__":
    main()