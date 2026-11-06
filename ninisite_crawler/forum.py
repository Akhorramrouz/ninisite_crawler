"""Crawl the topic listings of a NiniSite forum."""

from __future__ import annotations

from typing import Iterator

import pandas as pd
from tqdm.auto import tqdm

from .http import BASE_URL, Fetcher, max_page_number

TOPIC_COLUMNS = [
    "topic_id",
    "forum_id",
    "subject",
    "link",
    "creator_username",
    "creator_userid",
    "number_of_replies",
    "last_reply_date",
    "last_reply_time",
]


def _text(tag) -> str | None:
    return tag.get_text(strip=True) if tag else None


class ForumCrawler:
    """
    Crawl the topic list of one forum, e.g. ``ForumCrawler(139)`` for the spouse forum.

    Each forum page lists about 30 topics. ``crawl`` returns one row per topic with the
    columns in ``TOPIC_COLUMNS``.
    """

    def __init__(self, forum_id: int, fetcher: Fetcher | None = None, delay: float = 0.5):
        self.forum_id = int(forum_id)
        self.url = f"{BASE_URL}/discussion/forum/{self.forum_id}"
        self.fetcher = fetcher or Fetcher(delay=delay)

    def num_pages(self) -> int:
        """Number of listing pages the forum currently has."""
        return max_page_number(self.fetcher.get(self.url))

    def parse_topic(self, item) -> dict:
        """Parse one ``div.category--header`` topic row."""
        anchor = item.select_one("a[href*='/discussion/topic/']")
        href = anchor["href"]
        creator = item.select_one("div.last-topic-user a")
        replies = _text(item.select_one("span.topic_number.hidden-sm-up")) or "0"
        return {
            "topic_id": int(href.split("/")[3]),
            "forum_id": self.forum_id,
            "subject": _text(item.select_one("span.topic_subject")),
            "link": BASE_URL + href,
            "creator_username": _text(creator),
            "creator_userid": creator["href"].split("/")[2] if creator else None,
            "number_of_replies": int(replies.split()[0]),
            "last_reply_date": _text(item.select_one("span.last-topic-date")),
            "last_reply_time": _text(item.select_one("span.last-topic-time")),
        }

    def parse_page(self, page: int) -> list[dict]:
        soup = self.fetcher.get(self.url, page=page)
        return [self.parse_topic(item) for item in soup.select("div.category--header")]

    def iter_pages(self, start_page: int = 1, end_page: int | None = None, progress: bool = True) -> Iterator[list[dict]]:
        """Yield the parsed topics of each page from ``start_page`` to ``end_page`` (inclusive)."""
        if end_page is None:
            end_page = self.num_pages()
        pages = range(start_page, end_page + 1)
        for page in tqdm(pages, desc=f"forum {self.forum_id}", unit="page", disable=not progress):
            yield self.parse_page(page)

    def crawl(self, start_page: int = 1, end_page: int | None = None, progress: bool = True) -> pd.DataFrame:
        """
        Crawl pages ``start_page``..``end_page`` (inclusive; ``None`` = last page).

        Topics can shift between pages while crawling, so duplicates are dropped.
        """
        rows = [row for page in self.iter_pages(start_page, end_page, progress) for row in page]
        df = pd.DataFrame(rows, columns=TOPIC_COLUMNS)
        return df.drop_duplicates("topic_id").reset_index(drop=True)
