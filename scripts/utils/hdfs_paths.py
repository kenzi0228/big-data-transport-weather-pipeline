from __future__ import annotations

from datetime import datetime
from pathlib import Path


def build_partitioned_local_path(base_dir: str, dt: datetime) -> Path:
    return (
        Path(base_dir)
        / f"year={dt.year:04d}"
        / f"month={dt.month:02d}"
        / f"day={dt.day:02d}"
        / f"hour={dt.hour:02d}"
    )