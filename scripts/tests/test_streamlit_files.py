from __future__ import annotations

from pathlib import Path


def main() -> None:
    print("=== STREAMLIT DEMO FILE VALIDATION ===")

    required_files = [
        "main.py",
        "app.py",
    ]

    for path in required_files:
        if not Path(path).exists():
            raise FileNotFoundError(f"Missing file: {path}")
        print(f"[OK] {path}")

    print("")
    print("Streamlit demo files validation completed successfully.")


if __name__ == "__main__":
    main()