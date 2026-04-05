from __future__ import annotations

from pathlib import Path


def main() -> None:
    print("=== OPEN-METEO INGESTION FILE VALIDATION ===")

    required_files = [
        "config/api/openmeteo.yaml",
        "scripts/ingestion/ingest_openmeteo_to_hdfs.py",
    ]

    for path in required_files:
        if not Path(path).exists():
            raise FileNotFoundError(f"Missing file: {path}")
        print(f"[OK] {path}")

    print("")
    print("Open-Meteo ingestion structure validation completed successfully.")


if __name__ == "__main__":
    main()