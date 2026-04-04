from __future__ import annotations

from pathlib import Path

REQUIRED = [
    "config/app_config.yaml",
    "config/api/idfm_stops.yaml",
    "scripts/ingestion/producer_idfm_to_kafka.py",
    "scripts/ingestion/ingest_openmeteo_to_hdfs.py",
    "scripts/consumers/kafka_to_hdfs.py",
    "scripts/consumers/kafka_to_hbase.py",
    "scripts/hbase/init_hbase_table.py",
    "scripts/hive/create_external_tables.hql",
    "scripts/hive/create_enriched_view.hql",
    "scripts/mapreduce/mapper.py",
    "scripts/mapreduce/reducer.py",
    "scripts/oozie/workflow.xml"
]

def main() -> None:
    print("=== PROJECT STRUCTURE VALIDATION ===")
    missing = []

    for path in REQUIRED:
        if Path(path).exists():
            print(f"[OK] {path}")
        else:
            print(f"[MISSING] {path}")
            missing.append(path)

    if missing:
        raise SystemExit(1)

    print("")
    print("Structure validation successful.")

if __name__ == "__main__":
    main()