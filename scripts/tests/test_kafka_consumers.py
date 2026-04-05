from __future__ import annotations

from pathlib import Path


def main() -> None:
    print("=== CONSUMER FILE VALIDATION ===")

    required_files = [
        "scripts/utils/hdfs_paths.py",
        "scripts/consumers/kafka_to_hdfs.py",
        "scripts/consumers/kafka_to_hbase.py",
    ]

    for path in required_files:
        if not Path(path).exists():
            raise FileNotFoundError(f"Missing file: {path}")
        print(f"[OK] {path}")

    print("")
    print("Kafka consumer files validation completed successfully.")


if __name__ == "__main__":
    main()