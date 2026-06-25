"""Unit tests for Vndb.get_char_data's anti-bot warm-up / retry behaviour."""
from Vndb import Vndb


class _FakeDriver:
    def __init__(self):
        self.gets = []

    def get(self, url):
        self.gets.append(url)


class _FakeGlv:
    def __init__(self, driver):
        self.driver = driver

    def log(self, *a, **kw):
        pass

    @staticmethod
    def sleep(*a, **kw):
        pass


def _make_vndb(parse_results):
    """Build a Vndb whose parse_char_data yields the given results in order."""
    driver = _FakeDriver()
    v = Vndb.__new__(Vndb)
    v.glv = _FakeGlv(driver)
    v.pageUrl = "https://vndb.org"
    v.entry_id = "61832"

    calls = {"n": 0}

    def fake_parse():
        i = min(calls["n"], len(parse_results) - 1)
        calls["n"] += 1
        return {"chars": list(parse_results[i])}

    v.parse_char_data = fake_parse
    return v, driver


def test_no_retry_when_chars_found_first_try():
    # First parse already returns a character -> only the chars page is loaded.
    v, driver = _make_vndb([["alice"]])
    data = v.get_char_data()
    assert data["chars"] == ["alice"]
    assert driver.gets == ["https://vndb.org/v61832/chars#chars"]


def test_warmup_retry_recovers_after_empty_first_try():
    # First parse empty (interstitial), second parse succeeds after warm-up.
    v, driver = _make_vndb([[], ["bob"]])
    data = v.get_char_data()
    assert data["chars"] == ["bob"]
    # chars page, then main entry page (warm-up), then chars page again.
    assert driver.gets == [
        "https://vndb.org/v61832/chars#chars",
        "https://vndb.org/v61832",
        "https://vndb.org/v61832/chars#chars",
    ]


def test_returns_empty_when_entry_has_no_characters():
    # Both attempts empty -> empty result (warning is logged, not raised).
    v, driver = _make_vndb([[], []])
    data = v.get_char_data()
    assert data["chars"] == []
    assert driver.gets.count("https://vndb.org/v61832/chars#chars") == 2
