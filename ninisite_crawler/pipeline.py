"""
Resumable, large-scale crawling jobs that write to disk.

Every job writes small files as it goes and skips the ones that already exist, so an
interrupted run (e.g. a Colab session timing out) continues where it stopped when rerun.
Point ``out_dir`` at Google Drive in Colab to keep results between sessions.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from .forum import TOPIC_COLUMNS, ForumCrawler
from .http import Fetcher
from .topic import COMMENT_COLUMNS, POST_COLUMNS, TopicCrawler


def shard(items: Sequence, index: int, num_shards: int) -> list:
    """Split ``items`` into ``num_shards`` near-equal chunks and return chunk ``index`` (0-based)."""
    if not 0 <= index < num_shards:
        raise ValueError(f"index must be in [0, {num_shards}), got {index}")
    return np.array_split(np.asarray(items), num_shards)[index].tolist()


def crawl_forum(
    forum_id: int,
    out_dir: str | Path,
    start_page: int = 1,
    end_page: int | None = None,
    batch_size: int = 25,
    delay: float = 0.5,
) -> pd.DataFrame:
    """
    Crawl a forum's topic list in batches of pages and return all topics, deduplicated.

    Each batch is saved as ``out_dir/pages_<first>_<last>.csv``; batches already on disk are
    skipped. ``end_page=None`` crawls to the forum's last page.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    crawler = ForumCrawler(forum_id, delay=delay)
    if end_page is None:
        end_page = crawler.num_pages()

    for first in range(start_page, end_page + 1, batch_size):
        last = min(first + batch_size - 1, end_page)
        path = out_dir / f"pages_{first}_{last}.csv"
        if path.exists():
            continue
        crawler.crawl(first, last).to_csv(path, index=False)

    return merge_forum_batches(out_dir)


def merge_forum_batches(out_dir: str | Path) -> pd.DataFrame:
    """Combine the ``pages_*.csv`` batches written by ``crawl_forum`` into one deduplicated DataFrame."""
    files = sorted(Path(out_dir).glob("pages_*.csv"), key=lambda p: int(p.stem.split("_")[1]))
    if not files:
        return pd.DataFrame(columns=TOPIC_COLUMNS)
    df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    return df.drop_duplicates("topic_id").reset_index(drop=True)


def crawl_comments(
    topic_ids: Iterable[int],
    out_dir: str | Path,
    delay: float = 0.5,
    retry_failed: bool = False,
) -> dict:
    """
    Crawl the opening post and comments of every topic in ``topic_ids``.

    Writes ``out_dir/posts/<id>.csv`` and ``out_dir/comments/<id>.csv`` per topic. Topics
    already crawled are skipped; topics that fail are logged in ``out_dir/failed.csv``
    and skipped on later runs unless ``retry_failed=True``.

    Returns counts: ``{"crawled": n, "skipped": n, "failed": n}``.
    """
    out_dir = Path(out_dir)
    posts_dir, comments_dir = out_dir / "posts", out_dir / "comments"
    posts_dir.mkdir(parents=True, exist_ok=True)
    comments_dir.mkdir(parents=True, exist_ok=True)
    failed_path = out_dir / "failed.csv"

    done = {int(p.stem) for p in comments_dir.glob("*.csv")}
    failed = set() if retry_failed else _read_failed(failed_path)
    fetcher = Fetcher(delay=delay)
    stats = {"crawled": 0, "skipped": 0, "failed": 0}

    topic_ids = [int(t) for t in topic_ids]
    progress = tqdm(topic_ids, desc="topics", unit="topic")
    for topic_id in progress:
        if topic_id in done or topic_id in failed:
            stats["skipped"] += 1
            continue
        try:
            post, comments = TopicCrawler(topic_id, fetcher=fetcher).crawl()
        except Exception as exc:  # keep going; the topic is logged and can be retried later
            stats["failed"] += 1
            _append_failed(failed_path, topic_id, exc)
        else:
            pd.DataFrame([post], columns=POST_COLUMNS).to_csv(posts_dir / f"{topic_id}.csv", index=False)
            # Written last: its presence marks the topic as done.
            comments.to_csv(comments_dir / f"{topic_id}.csv", index=False)
            stats["crawled"] += 1
        progress.set_postfix(stats)
    return stats


def load_crawled(out_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Combine the per-topic files written by ``crawl_comments`` into ``(posts, comments)`` DataFrames."""
    out_dir = Path(out_dir)

    def combine(folder: Path, columns: list[str]) -> pd.DataFrame:
        files = sorted(folder.glob("*.csv"))
        frames = [pd.read_csv(f) for f in tqdm(files, desc=folder.name, unit="file")]
        frames = [f for f in frames if not f.empty]
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=columns)

    return combine(out_dir / "posts", POST_COLUMNS), combine(out_dir / "comments", COMMENT_COLUMNS)


def _read_failed(path: Path) -> set[int]:
    if not path.exists():
        return set()
    return set(pd.read_csv(path)["topic_id"].astype(int))


def _append_failed(path: Path, topic_id: int, exc: Exception) -> None:
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new:
            writer.writerow(["topic_id", "error"])
        writer.writerow([topic_id, f"{type(exc).__name__}: {exc}"])
