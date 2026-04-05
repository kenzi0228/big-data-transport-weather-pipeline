#!/usr/bin/env python3
from __future__ import annotations

import json
import sys


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue

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
                print(f"{key}\t1")


if __name__ == "__main__":
    main()