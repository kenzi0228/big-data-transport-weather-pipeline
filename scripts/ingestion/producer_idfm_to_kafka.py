from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml
from kafka import KafkaProducer

from scripts.utils.idfm_parser import normalize_stop_visits


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


def fetch_stop_monitoring(
    base_url: str,
    api_key: str,
    monitoring_ref: str,
    timeout_seconds: int,
    maximum_stop_visits: int
) -> dict[str, Any]:
    url = f"{base_url}/{monitoring_ref}"

    headers = {
        "Accept": "application/json",
        "apiKey": api_key
    }

    params = {
        "MaximumStopVisits": maximum_stop_visits
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=timeout_seconds
    )
    response.raise_for_status()
    return response.json()


def build_raw_kafka_message(
    monitoring_ref: str,
    stop_label: str,
    payload: dict[str, Any]
) -> dict[str, Any]:
    return {
        "source": "idfm_stop_monitoring",
        "ingestion_time_utc": datetime.now(timezone.utc).isoformat(),
        "monitoring_ref": monitoring_ref,
        "stop_label": stop_label,
        "payload": payload
    }


def main() -> None:
    app_config = load_app_config()
    idfm_credentials = load_idfm_credentials()
    stops_config = load_yaml("config/api/idfm_stops.yaml")

    bootstrap_servers = app_config["kafka"]["bootstrap_servers"]
    topic_name = app_config["kafka"]["topic_idfm_raw"]

    producer = build_kafka_producer(bootstrap_servers)

    api_key = idfm_credentials["idfm"]["api_key"]
    base_url = idfm_credentials["idfm"]["base_url"]
    timeout_seconds = idfm_credentials["idfm"]["timeout_seconds"]
    poll_interval_seconds = idfm_credentials["idfm"]["poll_interval_seconds"]
    maximum_stop_visits = idfm_credentials["idfm"]["maximum_stop_visits"]

    enabled_stops = [stop for stop in stops_config["stops"] if stop.get("enabled", False)]

    if not enabled_stops:
        raise ValueError("No enabled stops found in config/api/idfm_stops.yaml")

    print("=== IDFM PRODUCER TO KAFKA ===")
    print(f"Kafka bootstrap servers: {bootstrap_servers}")
    print(f"Kafka topic: {topic_name}")
    print(f"Enabled stops: {len(enabled_stops)}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            cycle_start = datetime.now().isoformat()
            print("")
            print(f"Polling cycle started at: {cycle_start}")

            for stop in enabled_stops:
                monitoring_ref = stop["monitoring_ref"]
                stop_label = stop["label"]

                try:
                    payload = fetch_stop_monitoring(
                        base_url=base_url,
                        api_key=api_key,
                        monitoring_ref=monitoring_ref,
                        timeout_seconds=timeout_seconds,
                        maximum_stop_visits=maximum_stop_visits
                    )

                    raw_message = build_raw_kafka_message(
                        monitoring_ref=monitoring_ref,
                        stop_label=stop_label,
                        payload=payload
                    )
                    producer.send(topic_name, raw_message)

                    normalized_visits = normalize_stop_visits(
                        raw_payload=payload,
                        monitoring_ref=monitoring_ref,
                        stop_label=stop_label
                    )

                    print(
                        f"[OK] stop={stop_label} monitoring_ref={monitoring_ref} "
                        f"visits={len(normalized_visits)}"
                    )

                except Exception as exc:
                    print(
                        f"[ERROR] stop={stop_label} monitoring_ref={monitoring_ref} "
                        f"error={exc}"
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