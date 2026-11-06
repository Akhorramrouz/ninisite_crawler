# Data

## `topics/`

Topic lists crawled from NiniSite forums in May 2023, one gzipped CSV per forum
(pandas reads them directly: `pd.read_csv("forum_139_spouse.csv.gz")`, or use
`ninisite_crawler.load_topics(139)`).

| File | Forum | Topics |
|---|---|---|
| `forum_139_spouse.csv.gz` | 139 – همسران (spouses) | 160,971 |
| `forum_141_problem_solution.csv.gz` | 141 – problem / solution | 267,763 |

| Column | Description |
|---|---|
| `topic_id` | Topic ID (`https://www.ninisite.com/discussion/topic/<topic_id>`) |
| `forum_id` | Forum ID |
| `subject` | Topic title |
| `link` | Full topic URL |
| `creator_username` | Username of the topic's creator |
| `creator_userid` | User GUID of the topic's creator |
| `number_of_replies` | Reply count at crawl time |

Topics crawled with the current code also have `last_reply_date` and `last_reply_time`.

## Crawled posts and comments

`ninisite_crawler.crawl_comments()` writes these per topic; `load_crawled()` combines them.

**Posts** (`posts/<topic_id>.csv`, one row per topic): `topic_id`, `forum_id`, `title`,
`text`, `date`, `time`, `username`, `userid`, `number_of_posts`, `number_of_views`,
`number_of_pages`.

**Comments** (`comments/<topic_id>.csv`): `comment_id`, `topic_id`, `page`, `text`,
`date`, `time`, `username`, `userid`, `is_reply`, `reply_to_id` (comment being replied
to), `reply_to_text` (quoted snippet).

Dates use the Persian (Solar Hijri) calendar, e.g. `1402/03/05`. Recent posts may show
a relative date such as `دیروز` ("yesterday") instead.
