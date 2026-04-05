from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml
from kafka import KafkaProducer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.idfm_line_parser import extract_estimated_journeys, filter_journeys_by_stop_refs


def load_yaml(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_app_config() -> dict[str, Any]:
    return load_yaml("config/app_config.yaml")


def load_idfm_credentials() -> dict[str, Any]:
    credentials_path = Path("config/api/idfm_credentials.yaml")
    template_path = Path("config/api/idfm_credentials.template.yaml")

    if credentials_path.exists():
        return load_yaml(str(credentials_path))

    if template_path.exists():
        raise FileNotFoundError(
            "Missing config/api/idfm_credentials.yaml. "
            "Copy config/api/idfm_credentials.template.yaml to "
            "config/api/idfm_credentials.yaml and fill your API key."
        )

    raise FileNotFoundError("Missing IDFM credentials configuration file.")


def build_kafka_producer(bootstrap_servers: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
        linger_ms=100
    )


def fetch_line_monitoring(
    base_url: str,
    api_key: str,
    line_ref: str,
    timeout_seconds: int
) -> dict[str, Any]:
    headers = {
        "Accept": "application/json",
        "apiKey": api_key
    }

    params = {
        "LineRef": line_ref
    }

    response = requests.get(
        base_url,
        headers=headers,
        params=params,
        timeout=timeout_seconds
    )
    response.raise_for_status()
    return response.json()


def build_raw_kafka_message(
    line_ref: str,
    line_label: str,
    target_stop_refs: list[str],
    filtered_journeys: list[dict[str, Any]],
    raw_payload: dict[str, Any]
) -> dict[str, Any]:
    return {
        "source": "idfm_line_request",
        "ingestion_time_utc": datetime.now(timezone.utc).isoformat(),
        "line_ref": line_ref,
        "line_label": line_label,
        "target_stop_refs": target_stop_refs,
        "filtered_journey_count": len(filtered_journeys),
        "filtered_journeys": filtered_journeys,
        "payload": raw_payload
    }


def main() -> None:
    app_config = load_app_config()
    idfm_credentials = load_idfm_credentials()
    lines_config = load_yaml("config/api/idfm_lines.yaml")

    bootstrap_servers = app_config["kafka"]["bootstrap_servers"]
    topic_name = app_config["kafka"]["topic_idfm_raw"]

    producer = build_kafka_producer(bootstrap_servers)

    api_key = idfm_credentials["idfm"]["api_key"]
    timeout_seconds = idfm_credentials["idfm"]["timeout_seconds"]
    poll_interval_seconds = idfm_credentials["idfm"]["poll_interval_seconds"]

    base_url = idfm_credentials["idfm"].get(
        "line_request_base_url",
        "https://prim.iledefrance-mobilites.fr/marketplace/requete-ligne"
    )

    enabled_lines = [line for line in lines_config["lines"] if line.get("enabled", False)]
    if not enabled_lines:
        raise ValueError("No enabled lines found in config/api/idfm_lines.yaml")

    print("=== IDFM LINE PRODUCER TO KAFKA ===")
    print(f"Kafka bootstrap servers: {bootstrap_servers}")
    print(f"Kafka topic: {topic_name}")
    print(f"Enabled lines: {len(enabled_lines)}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            cycle_start = datetime.now().isoformat()
            print("")
            print(f"Polling cycle started at: {cycle_start}")

            for line in enabled_lines:
                line_ref = line["line_ref"]
                line_label = line["line_label"]
                target_stop_refs = line.get("target_stop_refs", [])

                try:
                    payload = fetch_line_monitoring(
                        base_url=base_url,
                        api_key=api_key,
                        line_ref=line_ref,
                        timeout_seconds=timeout_seconds
                    )

                    journeys = extract_estimated_journeys(payload)
                    filtered_journeys = filter_journeys_by_stop_refs(journeys, target_stop_refs)

                    raw_message = build_raw_kafka_message(
                        line_ref=line_ref,
                        line_label=line_label,
                        target_stop_refs=target_stop_refs,
                        filtered_journeys=filtered_journeys,
                        raw_payload=payload
                    )
                    producer.send(topic_name, raw_message)

                    print(
                        f"[OK] line={line_label} line_ref={line_ref} "
                        f"all_journeys={len(journeys)} filtered_journeys={len(filtered_journeys)}"
                    )

                except Exception as exc:
                    print(
                        f"[ERROR] line={line_label} line_ref={line_ref} error={exc}"
                    )

            producer.flush()
            time.sleep(poll_interval_seconds)

    except KeyboardInterrupt:
        print("")
        print("Producer stopped by user.")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()