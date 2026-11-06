"""HTTP helpers: a shared session with retries, timeouts and polite delays."""

from __future__ import annotations

import time

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.ninisite.com"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ninisite-crawler/1.0; "
        "+https://github.com/Akhorramrouz/ninisite_crawler)"
    ),
    "Accept-Language": "fa,en;q=0.8",
}


def make_session(retries: int = 5, backoff: float = 1.0) -> requests.Session:
    """Return a ``requests.Session`` that retries on transient errors (429/5xx)."""
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class Fetcher:
    """Fetches pages and parses them with BeautifulSoup, sleeping ``delay`` seconds between requests."""

    def __init__(self, session: requests.Session | None = None, delay: float = 0.5, timeout: float = 30):
        self.session = session or make_session()
        self.delay = delay
        self.timeout = timeout
        self._last_request = 0.0

    def get(self, url: str, **params) -> BeautifulSoup:
        wait = self.delay - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        response = self.session.get(url, params=params or None, timeout=self.timeout)
        self._last_request = time.monotonic()
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")


def max_page_number(soup: BeautifulSoup) -> int:
    """Return the highest page number in a page's pagination bar (1 if there is none)."""
    numbers = [
        int(li.get_text(strip=True))
        for li in soup.select("ul.pagination li")
        if li.get_text(strip=True).isdigit()
    ]
    return max(numbers, default=1)
