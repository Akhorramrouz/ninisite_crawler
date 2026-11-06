"""Keyword search over topics (or any text DataFrame), tolerant of Persian spelling variants."""

from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

# Arabic code points that Persian users type interchangeably with the Persian ones.
_CHAR_MAP = str.maketrans({
    "ي": "ی", "ى": "ی", "ئ": "ی",
    "ك": "ک",
    "ة": "ه", "ۀ": "ه",
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ؤ": "و",
    "‌": "",  # zero-width non-joiner (half-space): "می‌خوام" == "میخوام"
    "‏": "", "‎": "",  # direction marks
    "ـ": "",  # tatweel
    **{c: str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")},
    **{c: str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")},
})
_DIACRITICS = re.compile("[ً-ٰٟ]")
_SPACES = re.compile(r"\s+")


def normalize_persian(text) -> str:
    """Normalize Persian text for matching: unify Arabic/Persian letters and digits, drop diacritics and half-spaces."""
    if not isinstance(text, str):
        return ""
    text = _DIACRITICS.sub("", text.translate(_CHAR_MAP))
    return _SPACES.sub(" ", text).strip().lower()


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def search_topics(
    df: pd.DataFrame,
    keywords: str | Iterable[str],
    columns: str | Iterable[str] = "subject",
    match: str = "any",
    exclude: str | Iterable[str] | None = None,
    whole_word: bool = False,
    ignore_spaces: bool = False,
) -> pd.DataFrame:
    """
    Return the rows of ``df`` whose ``columns`` contain the ``keywords``.

    - ``match="any"`` keeps rows with at least one keyword, ``"all"`` rows with every keyword.
    - ``exclude`` drops rows containing any of these keywords.
    - ``whole_word=True`` matches whole words only ("کار" won't match "بیکار").
    - ``ignore_spaces=True`` ignores spaces too, so "می خوام" matches "میخوام".

    Text and keywords are normalized with ``normalize_persian``, so Arabic/Persian letter
    variants, half-spaces and diacritics don't affect matching. The result adds a
    ``matched_keywords`` column and is sorted by number of matches (then replies, if present).
    """
    if match not in ("any", "all"):
        raise ValueError("match must be 'any' or 'all'")
    def prepare(text: str) -> str:
        text = normalize_persian(text)
        return text.replace(" ", "") if ignore_spaces else text

    # Keywords that normalize to the same text (e.g. "خیانت" / "خيانت") are searched once.
    keywords = list({prepare(k): k for k in reversed(_as_list(keywords)) if prepare(k)}.values())[::-1]
    if not keywords:
        raise ValueError("no keywords given")

    columns = _as_list(columns)
    text = df[columns[0]].fillna("").astype(str)
    for column in columns[1:]:
        text = text + " " + df[column].fillna("").astype(str)
    text = text.map(prepare)

    def contains(keyword: str) -> pd.Series:
        keyword = prepare(keyword)
        if whole_word:
            return text.str.contains(rf"(?<!\w){re.escape(keyword)}(?!\w)", regex=True)
        return text.str.contains(keyword, regex=False)

    hits = pd.DataFrame({k: contains(k) for k in keywords}, index=df.index)
    mask = hits.any(axis=1) if match == "any" else hits.all(axis=1)
    for keyword in _as_list(exclude):
        mask &= ~contains(keyword)

    result = df[mask].copy()
    matched = hits[mask]
    # bool x str matrix product concatenates the names of the keywords that matched
    result["matched_keywords"] = matched.dot(matched.columns + ", ").str[:-2]
    order = ["_n_matches"] + (["number_of_replies"] if "number_of_replies" in result else [])
    result["_n_matches"] = matched.sum(axis=1)
    return result.sort_values(order, ascending=False).drop(columns="_n_matches")
