# NiniSite Crawler

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Akhorramrouz/ninisite_crawler/blob/main/notebooks/quickstart.ipynb)

A Python package for crawling topics and comments from the [NiniSite](https://www.ninisite.com) discussion forums, plus the topic datasets already crawled from two forums.

## Repository layout

```
ninisite_crawler/        the Python package
├── forum.py             ForumCrawler: topic listings of a forum
├── topic.py             TopicCrawler: opening post and comments of one topic
├── pipeline.py          resumable bulk jobs: crawl_forum, crawl_comments, load_crawled, shard
├── data.py              load_topics: load the datasets in data/
├── search.py            search_topics: Persian-aware keyword search
└── http.py              shared HTTP session (retries, timeouts, rate limiting)
data/topics/             crawled topic lists, one .csv.gz per forum (see data/README.md)
notebooks/quickstart.ipynb   walkthrough you can run in Colab
```

## Installation

**Google Colab / any notebook (clone):**

```python
!git clone --depth 1 https://github.com/Akhorramrouz/ninisite_crawler.git
%cd ninisite_crawler
%pip install -q -r requirements.txt

import ninisite_crawler as nc
```

**pip install (package only, no clone):**

```bash
pip install git+https://github.com/Akhorramrouz/ninisite_crawler.git
```

When the repo isn't cloned, `load_topics()` downloads the datasets from GitHub.

**Local development:**

```bash
git clone --depth 1 https://github.com/Akhorramrouz/ninisite_crawler.git && cd ninisite_crawler && pip install -e .
```

## Usage

```python
import ninisite_crawler as nc

# Topic datasets in the repo (139 = spouse, 141 = problem_solution)
topics = nc.load_topics(139)

# One topic: opening post (dict) + comments (DataFrame)
post, comments = nc.TopicCrawler(11176867).crawl()

# Listing pages of a forum (end_page is inclusive; None = last page)
forum = nc.ForumCrawler(139)
forum.num_pages()
new_topics = forum.crawl(start_page=1, end_page=5)
```

### Keyword search

```python
hits = nc.search_topics(topics, ["خیانت", "طلاق"])                 # titles with any keyword
hits = nc.search_topics(topics, ["شوهرم", "خیانت"], match="all")   # titles with every keyword
hits = nc.search_topics(topics, "خیانت", exclude=["فیلم", "سریال"], whole_word=True)
```

Matching treats Arabic and Persian letter variants (ي/ی, ك/ک), half-spaces, diacritics and Persian digits as equivalent. The result has a `matched_keywords` column. Pass `columns="text"` to search crawled comments.

The [quickstart notebook](notebooks/quickstart.ipynb) also uses two Claude API prompts to find every topic on a subject. The first turns the subject into Persian search keywords. The second checks the matching titles for relevance. The output is a JSON file of topics and topic IDs.

### Bulk, resumable crawls

These jobs write small files as they go and skip whatever is already on disk. If a run is interrupted (for example a Colab timeout), rerun it to continue. On Colab, point `out_dir` at Google Drive.

```python
# A forum's whole topic list, saved in batches of 25 pages
all_topics = nc.crawl_forum(139, "output/forum_139", start_page=1, end_page=None)

# Comments for one shard (here 1 of 10) of the topic list
ids = nc.shard(topics.topic_id, index=0, num_shards=10)
nc.crawl_comments(ids, "output/comments_139_shard_0")   # failures go to failed.csv
posts, comments = nc.load_crawled("output/comments_139_shard_0")
```

Every crawler accepts `delay=` (seconds between requests, default `0.5`). Please keep it polite.

Column descriptions for every dataset are in [data/README.md](data/README.md).

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgments

This crawler was developed as part of a research project and is not affiliated with or endorsed by NiniSite.
