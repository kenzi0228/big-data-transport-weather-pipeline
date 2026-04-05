from __future__ import annotations

from pathlib import Path


def main() -> None:
    print("=== BATCH SUMMARY FILE VALIDATION ===")

    required_files = [
        "scripts/batch/build_transport_weather_summary.py",
    ]

    for path in required_files:
        if not Path(path).exists():
            raise FileNotFoundError(f"Missing file: {path}")
        print(f"[OK] {path}")

    print("")
    print("Batch summary structure validation completed successfully.")


if __name__ == "__main__":
    main()