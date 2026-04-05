from __future__ import annotations

import json
from pathlib import Path


def extract_stop_refs(payload: dict) -> dict[str, int]:
    ref_counts: dict[str, int] = {}

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
                    stop_point_ref = call.get("StopPointRef", {})
                    ref_value = None

                    if isinstance(stop_point_ref, dict):
                        ref_value = stop_point_ref.get("value")
                    elif isinstance(stop_point_ref, str):
                        ref_value = stop_point_ref

                    if ref_value:
                        ref_counts[ref_value] = ref_counts.get(ref_value, 0) + 1

    return dict(sorted(ref_counts.items(), key=lambda item: item[0]))


def main() -> None:
    files = [
        Path("outputs/reports/idfm_line_tests/metro_6.json"),
        Path("outputs/reports/idfm_line_tests/metro_7.json"),
    ]

    print("=== INSPECT IDFM LINE STOP REFS ===")

    for file_path in files:
        if not file_path.exists():
            print(f"[MISSING] {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as file:
            payload = json.load(file)

        ref_counts = extract_stop_refs(payload)

        print("")
        print(f"File: {file_path}")
        print(f"Unique stop refs: {len(ref_counts)}")
        for ref_value, count in ref_counts.items():
            print(f" - {ref_value} (count={count})")


if __name__ == "__main__":
    main()