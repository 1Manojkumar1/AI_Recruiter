"""
JSONL loader for the candidate dataset.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import INPUT_FILE


def load_candidates(
    filepath: Optional[Path] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Load candidate records from a JSONL file.

    Parameters
    ----------
    filepath : Path, optional
        Path to the JSONL file. Defaults to ``config.INPUT_FILE``.
    limit : int, optional
        Maximum number of records to load. ``None`` means load all.

    Returns
    -------
    list[dict]
        Raw candidate dictionaries.
    """
    path = filepath or INPUT_FILE
    candidates: List[Dict[str, Any]] = []

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with open(path, "r", encoding="utf-8") as fh:
        for idx, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"[WARN] Skipping malformed line {idx + 1}: {exc}")
                continue
            candidates.append(record)
            if limit is not None and len(candidates) >= limit:
                break

    print(f"[INFO] Loaded {len(candidates)} candidates from {path.name}")
    return candidates
