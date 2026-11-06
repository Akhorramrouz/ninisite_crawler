"""Access to the topic datasets shipped in the repo's ``data/`` folder."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Forums that have a crawled topic list in data/topics/.
FORUMS = {
    139: "spouse",
    141: "problem_solution",
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_URL = "https://raw.githubusercontent.com/Akhorramrouz/ninisite_crawler/main/data"


def topics_filename(forum_id: int) -> str:
    return f"forum_{forum_id}_{FORUMS[forum_id]}.csv.gz"


def load_topics(forum_id: int, data_dir: str | Path | None = None) -> pd.DataFrame:
    """
    Load the crawled topic list of a forum (see ``FORUMS``).

    Reads ``data/topics/`` from the cloned repo; if the repo isn't on disk (e.g. the package
    was pip-installed), the file is downloaded from GitHub instead.
    """
    if forum_id not in FORUMS:
        raise KeyError(f"no dataset for forum {forum_id}; available: {sorted(FORUMS)}")
    name = topics_filename(forum_id)
    path = Path(data_dir or DATA_DIR) / "topics" / name
    source = path if path.exists() else f"{RAW_URL}/topics/{name}"
    return pd.read_csv(source)
