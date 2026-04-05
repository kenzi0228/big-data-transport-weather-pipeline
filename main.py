from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent
    app_path = project_root / "app.py"

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
    ]

    subprocess.run(cmd, check=True, cwd=str(project_root))


if __name__ == "__main__":
    main()