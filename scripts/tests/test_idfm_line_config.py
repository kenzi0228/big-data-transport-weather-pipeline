from __future__ import annotations

from pathlib import Path
import yaml


def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main() -> None:
    print("=== IDFM LINE CONFIG VALIDATION ===")

    required_files = [
        "config/api/idfm_lines.yaml",
        "scripts/utils/idfm_line_parser.py",
        "scripts/tests/test_idfm_line_calls.py",
        "scripts/ingestion/producer_idfm_line_to_kafka.py",
    ]

    for path in required_files:
        if not Path(path).exists():
            raise FileNotFoundError(f"Missing file: {path}")
        print(f"[OK] {path}")

    lines_config = load_yaml("config/api/idfm_lines.yaml")
    lines = lines_config.get("lines", [])

    if not isinstance(lines, list) or not lines:
        raise ValueError("No lines declared in config/api/idfm_lines.yaml")

    enabled_count = 0
    for line in lines:
        if "line_ref" not in line:
            raise KeyError("A line is missing line_ref")
        if "line_label" not in line:
            raise KeyError("A line is missing line_label")
        if line.get("enabled", False):
            enabled_count += 1

    print(f"[OK] Lines declared: {len(lines)}")
    print(f"[OK] Enabled lines: {enabled_count}")
    print("")
    print("IDFM line configuration validation completed successfully.")


if __name__ == "__main__":
    main()