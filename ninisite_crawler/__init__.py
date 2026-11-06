"""Crawler for the NiniSite (ninisite.com) discussion forums."""

from .data import FORUMS, load_topics
from .forum import ForumCrawler
from .pipeline import crawl_comments, crawl_forum, load_crawled, merge_forum_batches, shard
from .topic import TopicCrawler

__version__ = "1.0.0"

__all__ = [
    "FORUMS",
    "ForumCrawler",
    "TopicCrawler",
    "crawl_comments",
    "crawl_forum",
    "load_crawled",
    "load_topics",
    "merge_forum_batches",
    "shard",
]
