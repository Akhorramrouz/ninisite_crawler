# NiniSite Crawler

This repository contains a web crawler for the NiniSite forums. It allows you to crawl topics and comments from specific forums and topics on the NiniSite website (https://www.ninisite.com).

## Installation

To use this crawler, you need to have Python installed on your system. Clone this repository and install the required dependencies using the following command:

```
pip install -r requirements.txt
```

## Usage

### NinisiteTopicCrawler

The `NinisiteTopicCrawler` class allows you to crawl comments from a specific topic on NiniSite. Here's an example of how to use it:

```python
crawler = NinisiteTopicCrawler(topic_id)
comments_df = crawler.crawl_comments_in_topic()
```

Replace `topic_id` with the ID of the topic you want to crawl. The `crawl_comments_in_topic` method returns a Pandas DataFrame containing the crawled comments.

### NiniSiteForumCrawler

The `NiniSiteForumCrawler` class allows you to crawl topics from a specific forum on NiniSite. Here's an example of how to use it:

```python
crawler = NiniSiteForumCrawler(forum_number)
topics_df = crawler.crawl_topics_in_forum(starting_page, number_pages)
```

Replace `forum_number` with the number of the forum you want to crawl. The optional parameters `starting_page` and `number_pages` allow you to specify the starting page and the number of pages to crawl (default values: starting_page=1, number_pages=10). The `crawl_topics_in_forum` method returns a Pandas DataFrame containing the crawled topics.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## Acknowledgments

This crawler was developed as a part of a project and is not affiliated with or endorsed by NiniSite.
