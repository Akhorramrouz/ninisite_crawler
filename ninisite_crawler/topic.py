"""Crawl a single NiniSite topic: its opening post and all comments."""

from __future__ import annotations

import re

import pandas as pd
from tqdm.auto import tqdm

from .http import BASE_URL, Fetcher, max_page_number

POST_COLUMNS = [
    "topic_id",
    "forum_id",
    "title",
    "text",
    "date",
    "time",
    "username",
    "userid",
    "number_of_posts",
    "number_of_views",
    "number_of_pages",
]

COMMENT_COLUMNS = [
    "comment_id",
    "topic_id",
    "page",
    "text",
    "date",
    "time",
    "username",
    "userid",
    "is_reply",
    "reply_to_id",
    "reply_to_text",
]


def _text(tag, sep: str = "") -> str | None:
    return tag.get_text(sep, strip=True) if tag else None


def _number_before(word: str, text: str) -> int | None:
    match = re.search(r"(\d+)\s*" + word, text or "")
    return int(match.group(1)) if match else None


def _author(article) -> tuple[str | None, str | None]:
    nickname = article.select_one("a.nickname")
    username = _text(nickname)
    userid = nickname["href"].split("/")[2] if nickname and nickname.has_attr("href") else None
    return username, userid


class TopicCrawler:
    """
    Crawl one topic, e.g. ``TopicCrawler(11176867).crawl()``.

    ``crawl`` returns ``(post, comments)``: a dict for the opening post (columns in
    ``POST_COLUMNS``) and a DataFrame of comments (columns in ``COMMENT_COLUMNS``).
    """

    def __init__(self, topic_id: int, fetcher: Fetcher | None = None, delay: float = 0.5):
        self.topic_id = int(topic_id)
        self.url = f"{BASE_URL}/discussion/topic/{self.topic_id}"
        self.fetcher = fetcher or Fetcher(delay=delay)

    def parse_post(self, soup) -> dict:
        """Parse the opening post from the first page of the topic."""
        article = soup.select_one("article#topic")
        if article is None:
            raise ValueError(f"topic {self.topic_id}: no opening post found (deleted or private?)")
        username, userid = _author(article)
        stats = " ".join(span.get_text(" ", strip=True) for span in article.select("span.pull-xs-right"))
        forum = soup.select_one("a[href*='/discussion/forum/']")
        return {
            "topic_id": self.topic_id,
            "forum_id": int(forum["href"].split("/")[3]) if forum else None,
            "title": _text(article.select_one("div.forum__topic--header a")),
            "text": _text(article.select_one("div.post-message"), "\n"),
            "date": _text(article.select_one("span.date")),
            "time": _text(article.select_one("span.time")),
            "username": username,
            "userid": userid,
            "number_of_posts": _number_before("پست", stats),
            "number_of_views": _number_before("بازدید", stats),
            "number_of_pages": max_page_number(soup),
        }

    def parse_comment(self, article, page: int) -> dict:
        username, userid = _author(article)
        reply = article.select_one("div.reply-message")
        return {
            "comment_id": int(article["id"].split("-")[-1]),
            "topic_id": self.topic_id,
            "page": page,
            "text": _text(article.select_one("div.post-message"), "\n"),
            "date": _text(article.select_one("span.date")),
            "time": _text(article.select_one("span.time")),
            "username": username,
            "userid": userid,
            "is_reply": reply is not None,
            "reply_to_id": int(reply["data-id"]) if reply and reply.get("data-id", "").isdigit() else None,
            "reply_to_text": _text(reply, " "),
        }

    def parse_comments(self, soup, page: int) -> list[dict]:
        # The opening post (article#topic) is repeated on every page; comments have id="post-<n>".
        return [self.parse_comment(a, page) for a in soup.select("article.topic-post[id^='post-']")]

    def crawl(self, progress: bool = False) -> tuple[dict, pd.DataFrame]:
        first = self.fetcher.get(self.url)
        post = self.parse_post(first)
        rows = self.parse_comments(first, 1)
        for page in tqdm(range(2, post["number_of_pages"] + 1), desc=f"topic {self.topic_id}", disable=not progress):
            rows.extend(self.parse_comments(self.fetcher.get(self.url, page=page), page))
        comments = pd.DataFrame(rows, columns=COMMENT_COLUMNS).drop_duplicates("comment_id")
        comments["reply_to_id"] = comments["reply_to_id"].astype("Int64")
        return post, comments.reset_index(drop=True)
