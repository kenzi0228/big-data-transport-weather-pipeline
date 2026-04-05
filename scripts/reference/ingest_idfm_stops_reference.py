from __future__ import annotations

from datetime import datetime
from pathlib import Path

import requests


REFERENCE_URL = "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/arrets/exports/csv?lang=fr&timezone=Europe%2FParis&use_labels=true&delimiter=%3B"
OUTPUT_DIR = Path("data/reference/raw")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"idfm_arrets_{now}.csv"

    response = requests.get(REFERENCE_URL, timeout=60)
    response.raise_for_status()

    output_file.write_bytes(response.content)

    print("=== IDFM STOPS REFERENCE INGESTION ===")
    print(f"Downloaded file: {output_file}")
    print(f"Size (bytes): {output_file.stat().st_size}")


if __name__ == "__main__":
    main()