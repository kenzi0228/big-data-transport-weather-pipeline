from __future__ import annotations

from pathlib import Path


def main() -> None:
    print("=== MAPREDUCE FILE VALIDATION ===")

    required_files = [
        "scripts/mapreduce/mapper.py",
        "scripts/mapreduce/reducer.py",
        "scripts/mapreduce/run_mapreduce_local.py",
    ]

    for path in required_files:
        if not Path(path).exists():
            raise FileNotFoundError(f"Missing file: {path}")
        print(f"[OK] {path}")

    print("")
    print("MapReduce files validation completed successfully.")


if __name__ == "__main__":
    main()