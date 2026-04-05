from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import yaml
from kafka import KafkaConsumer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.hdfs_paths import build_partitioned_local_path


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
        group_id="idfm-hdfs-consumer",
        value_deserializer=lambda value: json.loads(value.decode("utf-8"))
    )


def write_raw_event(base_dir: str, message: dict[str, Any]) -> Path:
    now = datetime.now(UTC)
    target_dir = build_partitioned_local_path(base_dir, now)
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"idfm_raw_{now.strftime('%Y%m%d_%H%M%S_%f')}.json"
    target_file = target_dir / filename

    with open(target_file, "w", encoding="utf-8") as file:
        json.dump(message, file, indent=2, ensure_ascii=False)

    return target_file


def main() -> None:
    app_config = load_app_config()

    bootstrap_servers = app_config["kafka"]["bootstrap_servers"]
    topic_name = app_config["kafka"]["topic_idfm_raw"]
    raw_idfm_local = app_config["paths"]["raw_idfm_local"]

    consumer = build_consumer(bootstrap_servers, topic_name)

    print("=== KAFKA TO HDFS CONSUMER ===")
    print(f"Kafka bootstrap servers: {bootstrap_servers}")
    print(f"Kafka topic: {topic_name}")
    print(f"Local raw target: {raw_idfm_local}")
    print("Press Ctrl+C to stop.")

    try:
        for kafka_message in consumer:
            payload = kafka_message.value
            written_file = write_raw_event(raw_idfm_local, payload)

            line_ref = payload.get("line_ref", "unknown_line")
            line_label = payload.get("line_label", "unknown_label")
            filtered_journey_count = payload.get("filtered_journey_count", 0)

            print(
                f"[OK] line_ref={line_ref} "
                f"line_label={line_label} "
                f"filtered_journey_count={filtered_journey_count} "
                f"written={written_file}"
            )

    except KeyboardInterrupt:
        print("")
        print("Kafka to HDFS consumer stopped by user.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()