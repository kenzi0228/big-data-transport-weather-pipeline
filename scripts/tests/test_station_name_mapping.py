from __future__ import annotations

from pathlib import Path


def main() -> None:
    print("=== STATION NAME MAPPING FILE VALIDATION ===")

    required_files = [
        "scripts/reference/build_stop_ref_mapping.py",
    ]

    for path in required_files:
        if not Path(path).exists():
            raise FileNotFoundError(f"Missing file: {path}")
        print(f"[OK] {path}")

    print("")
    print("Station name mapping files validation completed successfully.")


if __name__ == "__main__":
    main()