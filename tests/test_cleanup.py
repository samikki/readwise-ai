"""Data-loss guards for Readwise cleanup. All HTTP is mocked."""

import argparse
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

import build
from readwise_ai import readwise
from readwise_ai.config import is_valid_url_prefix

SUMMARY_PREFIX = "https://example.com/readwise-ai/summary/"
WATCH_PREFIX = "https://example.com/readwise-ai/watch/"


def _resp(status: int, payload: dict | None = None, headers: dict | None = None) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload or {}
    r.headers = headers or {}
    r.text = ""
    return r


def _iso(days_ago: float) -> str:
    return (datetime.now() - timedelta(days=days_ago)).isoformat()


def _doc(doc_id: str, url: str, days_ago: float, tags: list[str]) -> dict:
    ts = _iso(days_ago)
    return {
        "id": doc_id,
        "source_url": url,
        "title": doc_id,
        "published_date": ts,
        "created_at": ts,
        "tags": {t: {"name": t} for t in tags},
    }


class FakeReadwise:
    """Routes mocked requests.get/post/delete to canned responses and records writes."""

    def __init__(self, docs: list[dict], books: list[dict] | None = None, books_status: list[int] | None = None):
        self.docs = docs
        self.books = books or []
        self.books_status = list(books_status or [])
        self.posts: list = []
        self.deletes: list[str] = []

    def get(self, url, params=None, headers=None, **kwargs):
        if url == readwise._LIST_URL:
            return _resp(200, {"results": self.docs, "nextPageCursor": None})
        if url == readwise._BOOKS_URL:
            status = self.books_status.pop(0) if self.books_status else 200
            if status != 200:
                return _resp(status, headers={"Retry-After": "0"})
            return _resp(200, {"results": self.books, "next": None})
        raise AssertionError(f"unexpected GET {url}")

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return _resp(201)

    def delete(self, url, **kwargs):
        self.deletes.append(url.rstrip("/").rsplit("/", 1)[-1])
        return _resp(204)


@pytest.fixture
def fake(monkeypatch):
    def install(*args, **kwargs) -> FakeReadwise:
        f = FakeReadwise(*args, **kwargs)
        monkeypatch.setattr(readwise.requests, "get", f.get)
        monkeypatch.setattr(readwise.requests, "post", f.post)
        monkeypatch.setattr(readwise.requests, "delete", f.delete)
        monkeypatch.setattr(readwise.time, "sleep", lambda s: None)
        return f
    return install


def _old_user_and_summary_docs() -> list[dict]:
    return [
        _doc("user-article", "https://news.example.org/story", 30, ["AI"]),
        _doc("user-untagged", "https://blog.example.net/post", 30, []),
        _doc("old-summary", SUMMARY_PREFIX + "2026-01-01", 30, ["Summary"]),
        _doc("old-watch", WATCH_PREFIX + "2026-01-01", 30, ["WatchSummary"]),
    ]


# --- Prefix validation ---

@pytest.mark.parametrize("prefix", [
    "", "/", "https://", "https:///", "http://example.com/", "https://example.com",
    "example.com/", "ftp://example.com/", None,
])
def test_invalid_prefixes_rejected(prefix):
    assert not is_valid_url_prefix(prefix)


@pytest.mark.parametrize("prefix", [SUMMARY_PREFIX, WATCH_PREFIX, "https://example.com/"])
def test_valid_prefixes_accepted(prefix):
    assert is_valid_url_prefix(prefix)


@pytest.mark.parametrize("prefix", ["", "https://", "http://example.com/x/", "https://example.com/x"])
def test_invalid_prefix_means_no_deletions(fake, prefix):
    f = fake(_old_user_and_summary_docs())
    assert build._cleanup_old_summaries(7, url_prefix=prefix) == 0
    assert build._cleanup_keep_latest(url_prefix=prefix, keep=0) == 0
    assert f.deletes == []


# --- User articles are never deleted ---

def test_user_articles_never_deleted_by_retention(fake):
    f = fake(_old_user_and_summary_docs())
    build._cleanup_old_summaries(7, url_prefix=SUMMARY_PREFIX)
    assert f.deletes == ["old-summary"]


def test_user_articles_never_deleted_by_keep_latest(fake):
    f = fake(_old_user_and_summary_docs())
    build._cleanup_keep_latest(url_prefix=WATCH_PREFIX, keep=0, tag="WatchSummary")
    assert f.deletes == ["old-watch"]


def test_prefix_match_without_tag_is_not_deleted(fake):
    # A user article that happens to live under the prefix but lacks our tag
    docs = [
        _doc("user-under-prefix", SUMMARY_PREFIX + "my-own-note", 30, ["AI"]),
        _doc("watch-under-prefix", WATCH_PREFIX + "x", 30, ["Summary"]),
    ]
    f = fake(docs)
    assert build._cleanup_old_summaries(7, url_prefix=SUMMARY_PREFIX) == 0
    assert build._cleanup_keep_latest(url_prefix=WATCH_PREFIX, keep=0, tag="WatchSummary") == 0
    assert f.deletes == []


def test_broad_prefix_still_protects_user_articles(fake):
    # Even a valid-but-broad prefix only deletes tagged documents
    docs = [
        _doc("user-on-same-host", "https://example.com/article", 30, []),
        _doc("old-summary", SUMMARY_PREFIX + "a", 30, ["Summary"]),
    ]
    f = fake(docs)
    build._cleanup_old_summaries(7, url_prefix="https://example.com/")
    assert f.deletes == ["old-summary"]


# --- Retention cutoff and keep-latest ---

def test_retention_cutoff(fake):
    docs = [
        _doc("fresh", SUMMARY_PREFIX + "a", 2, ["Summary"]),
        _doc("just-inside", SUMMARY_PREFIX + "b", 6.9, ["Summary"]),
        _doc("just-outside", SUMMARY_PREFIX + "c", 7.1, ["Summary"]),
        _doc("old", SUMMARY_PREFIX + "d", 20, ["Summary"]),
    ]
    f = fake(docs)
    assert build._cleanup_old_summaries(7, url_prefix=SUMMARY_PREFIX) == 2
    assert sorted(f.deletes) == ["just-outside", "old"]


def test_retention_preserves_highlighted(fake):
    docs = [
        _doc("old-a", SUMMARY_PREFIX + "a", 20, ["Summary"]),
        _doc("old-b", SUMMARY_PREFIX + "b", 20, ["Summary"]),
    ]
    books = [{"source_url": SUMMARY_PREFIX + "a", "num_highlights": 2}]
    f = fake(docs, books=books)
    assert build._cleanup_old_summaries(7, url_prefix=SUMMARY_PREFIX) == 1
    assert f.deletes == ["old-b"]


def test_keep_latest_keeps_newest(fake):
    docs = [_doc(f"w{i}", WATCH_PREFIX + str(i), i, ["WatchSummary"]) for i in range(5)]
    f = fake(docs)
    assert build._cleanup_keep_latest(url_prefix=WATCH_PREFIX, keep=3, tag="WatchSummary") == 2
    assert sorted(f.deletes) == ["w3", "w4"]


def test_keep_latest_noop_when_at_or_below_keep(fake):
    docs = [_doc(f"w{i}", WATCH_PREFIX + str(i), i, ["WatchSummary"]) for i in range(3)]
    f = fake(docs)
    assert build._cleanup_keep_latest(url_prefix=WATCH_PREFIX, keep=3, tag="WatchSummary") == 0
    assert f.deletes == []


def test_keep_latest_preserves_highlighted(fake):
    docs = [_doc(f"w{i}", WATCH_PREFIX + str(i), i, ["WatchSummary"]) for i in range(5)]
    books = [{"source_url": WATCH_PREFIX + "4", "num_highlights": 1}]
    f = fake(docs, books=books)
    assert build._cleanup_keep_latest(url_prefix=WATCH_PREFIX, keep=3, tag="WatchSummary") == 1
    assert f.deletes == ["w3"]


# --- Highlight lookup fails closed ---

@pytest.mark.parametrize("status", [500, 401, 404])
def test_highlight_api_error_means_no_deletions(fake, status):
    f = fake(_old_user_and_summary_docs(), books_status=[status, status])
    assert build._cleanup_old_summaries(7, url_prefix=SUMMARY_PREFIX) == 0
    assert build._cleanup_keep_latest(url_prefix=WATCH_PREFIX, keep=0, tag="WatchSummary") == 0
    assert f.deletes == []


def test_highlight_api_persistent_429_means_no_deletions(fake):
    f = fake(_old_user_and_summary_docs(), books_status=[429] * readwise._MAX_RETRIES)
    assert build._cleanup_old_summaries(7, url_prefix=SUMMARY_PREFIX) == 0
    assert f.deletes == []


def test_highlight_api_429_then_success_backs_off_and_proceeds(fake, monkeypatch):
    sleeps: list = []
    f = fake(_old_user_and_summary_docs(), books_status=[429, 200])
    monkeypatch.setattr(readwise.time, "sleep", sleeps.append)
    assert build._cleanup_old_summaries(7, url_prefix=SUMMARY_PREFIX) == 1
    assert sleeps == [0]
    assert f.deletes == ["old-summary"]


def test_highlight_api_failure_on_later_page_returns_none(monkeypatch):
    calls = iter([
        _resp(200, {"results": [{"source_url": SUMMARY_PREFIX + "a", "num_highlights": 1}], "next": "p2"}),
        _resp(500),
    ])
    monkeypatch.setattr(readwise.requests, "get", lambda **kw: next(calls))
    assert readwise.fetch_highlighted_urls(SUMMARY_PREFIX) is None


def test_highlight_api_connection_error_returns_none(monkeypatch):
    def boom(**kw):
        raise readwise.requests.ConnectionError("down")
    monkeypatch.setattr(readwise.requests, "get", boom)
    assert readwise.fetch_highlighted_urls(SUMMARY_PREFIX) is None


def test_highlight_api_malformed_json_returns_none(monkeypatch):
    r = _resp(200)
    r.json.side_effect = ValueError("not json")
    monkeypatch.setattr(readwise.requests, "get", lambda **kw: r)
    assert readwise.fetch_highlighted_urls(SUMMARY_PREFIX) is None


# --- Dry run performs no writes ---

def _args(**overrides) -> argparse.Namespace:
    base = dict(sources=["feed"], days=1, max_articles=10, dry_run=True, output=None, watch=False)
    base.update(overrides)
    return argparse.Namespace(**base)


def test_cleanup_dry_run_reports_but_does_not_delete(fake):
    f = fake(_old_user_and_summary_docs())
    assert build._cleanup_old_summaries(7, url_prefix=SUMMARY_PREFIX, dry_run=True) == 1
    assert build._cleanup_keep_latest(url_prefix=WATCH_PREFIX, keep=0, tag="WatchSummary", dry_run=True) == 1
    assert f.deletes == []
    assert f.posts == []


def test_run_summary_dry_run_sends_no_post_or_delete(fake, monkeypatch, caplog):
    f = fake(_old_user_and_summary_docs())
    orig = build._cleanup_old_summaries
    monkeypatch.setattr(
        build, "_cleanup_old_summaries",
        lambda days, **kw: orig(days, url_prefix=SUMMARY_PREFIX, **kw),
    )
    monkeypatch.setattr(build, "generate_html_summary", lambda docs: "<html></html>")
    caplog.set_level("INFO")
    build._run_summary(_args())
    assert "would delete old summary: old-summary" in caplog.text
    assert f.deletes == []
    assert f.posts == []


def test_run_watch_dry_run_sends_no_post_or_delete(fake, monkeypatch, caplog):
    f = fake(_old_user_and_summary_docs())
    monkeypatch.setattr(build, "WATCH_URL_PREFIX", WATCH_PREFIX)
    monkeypatch.setattr(build, "WATCH_KEEP", 0)
    monkeypatch.setattr(build, "generate_watch_summary", lambda docs: "text")
    caplog.set_level("INFO")
    build._run_watch(_args(watch=True))
    assert "would delete old watch summary: old-watch" in caplog.text
    assert f.deletes == []
    assert f.posts == []
