from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml
from kafka import KafkaConsumer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_yaml(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_app_config() -> dict[str, Any]:
    return load_yaml("config/app_config.yaml")


def build_consumer(bootstrap_servers: str, topic_name: str) -> KafkaConsumer:
    return KafkaConsumer(
        topic_name,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="idfm-hbase-consumer",
        value_deserializer=lambda value: json.loads(value.decode("utf-8"))
    )


def build_row_key(line_ref: str, stop_point_ref: str, destination: str) -> str:
    return f"{line_ref}#{stop_point_ref}#{destination}"


def extract_destination_from_call(call: dict[str, Any]) -> str:
    destination_display = call.get("DestinationDisplay", [])
    if isinstance(destination_display, list) and destination_display:
        first = destination_display[0]
        if isinstance(first, dict):
            return str(first.get("value", "unknown_destination")).strip()
        if isinstance(first, str):
            return first.strip()
    return "unknown_destination"


def extract_stop_point_ref(call: dict[str, Any]) -> str:
    stop_ref = call.get("StopPointRef", {})
    if isinstance(stop_ref, dict):
        return str(stop_ref.get("value", "unknown_stop")).strip()
    if isinstance(stop_ref, str):
        return stop_ref.strip()
    return "unknown_stop"


def main() -> None:
    app_config = load_app_config()

    bootstrap_servers = app_config["kafka"]["bootstrap_servers"]
    topic_name = app_config["kafka"]["topic_idfm_raw"]
    table_name = app_config["hbase"]["table_live_status"]

    consumer = build_consumer(bootstrap_servers, topic_name)

    print("=== KAFKA TO HBASE CONSUMER ===")
    print(f"Kafka bootstrap servers: {bootstrap_servers}")
    print(f"Kafka topic: {topic_name}")
    print(f"HBase table target: {table_name}")
    print("Current version prints the rows that should be written to HBase.")
    print("Press Ctrl+C to stop.")

    try:
        for kafka_message in consumer:
            payload = kafka_message.value

            line_ref = payload.get("line_ref", "unknown_line")
            line_label = payload.get("line_label", "unknown_label")
            filtered_journeys = payload.get("filtered_journeys", [])

            if not isinstance(filtered_journeys, list) or not filtered_journeys:
                print(f"[INFO] no filtered journeys found for line_label={line_label}")
                continue

            preview_count = 0

            for item in filtered_journeys:
                matched_calls = item.get("matched_calls", [])
                if not isinstance(matched_calls, list):
                    continue

                for call in matched_calls:
                    stop_point_ref = extract_stop_point_ref(call)
                    destination = extract_destination_from_call(call)
                    expected_arrival = call.get("ExpectedArrivalTime")
                    expected_departure = call.get("ExpectedDepartureTime")
                    departure_status = call.get("DepartureStatus", "unknown_status")

                    row_key = build_row_key(line_ref, stop_point_ref, destination)

                    print(
                        f"[HBASE UPSERT PREVIEW] "
                        f"table={table_name} "
                        f"row_key={row_key} "
                        f"line_label={line_label} "
                        f"expected_arrival={expected_arrival} "
                        f"expected_departure={expected_departure} "
                        f"departure_status={departure_status}"
                    )
                    preview_count += 1

            if preview_count == 0:
                print(f"[INFO] no matched calls found for line_label={line_label}")

    except KeyboardInterrupt:
        print("")
        print("Kafka to HBase consumer stopped by user.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()