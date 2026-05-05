"""
Browser integration tests for the VNDB scraper.

Uses v38882 — https://www.vndb.org/v38882

Run with:
    .venv/bin/pytest tests/browser/test_vndb_browser.py -v
"""

import pytest
from Vndb import Vndb

VNDB_ID = "38882"

pytestmark = pytest.mark.browser


# ── One scrape per module — all tests share this cached result ────────────────

@pytest.fixture(scope="module")
def entry(driver, glv):
    return Vndb(glv).get_entry_data(driver, VNDB_ID)


@pytest.fixture(scope="module")
def chars(driver, glv):
    v = Vndb(glv)
    v.get_entry_data(driver, VNDB_ID)   # sets v.entry_id
    return v.get_char_data()


# ── Entry data ────────────────────────────────────────────────────────────────

def test_entry_has_all_keys(entry):
    for key in ("title", "romanji", "cover", "developer1", "developer2", "webpage"):
        assert key in entry, f"Missing key: {key}"


def test_romanji_nonempty(entry):
    assert isinstance(entry["romanji"], str) and entry["romanji"] != ""


def test_developer_nonempty(entry):
    assert entry["developer1"] != ""


def test_cover_is_vndb_url(entry):
    assert entry["cover"].startswith("https://t.vndb.org/"), \
        f"Unexpected cover URL: {entry['cover']}"


def test_cover_url_has_no_thumbnail_suffix(entry):
    # Vndb.get_entry_data strips the .t thumbnail suffix
    assert ".t." not in entry["cover"], \
        f"Cover URL still has thumbnail suffix: {entry['cover']}"


def test_all_string_fields_are_str(entry):
    for key in ("title", "romanji", "cover", "developer1", "developer2", "webpage"):
        assert isinstance(entry[key], str), f"Field '{key}' is not a string"


# ── Character data ────────────────────────────────────────────────────────────

def test_chars_key_present(chars):
    assert "chars" in chars


def test_has_at_least_one_character(chars):
    assert len(chars["chars"]) >= 1, "Expected at least 1 character"


def test_each_char_has_required_fields(chars):
    required = {"name", "romanji", "gender", "img1", "height", "weight",
                "measurements", "age", "cup"}
    for char in chars["chars"]:
        missing = required - char.keys()
        assert not missing, f"Character '{char.get('name')}' missing fields: {missing}"


def test_each_char_gender_is_valid(chars):
    valid = {"female", "male", "both", "unknown"}
    for char in chars["chars"]:
        assert char["gender"] in valid, \
            f"Invalid gender '{char['gender']}' for char '{char['name']}'"


def test_each_char_name_nonempty(chars):
    for char in chars["chars"]:
        assert char["name"] != "", "Found a character with an empty name"


def test_char_images_are_vndb_urls(chars):
    for char in chars["chars"]:
        if char["img1"]:
            assert char["img1"].startswith("https://"), \
                f"Unexpected img1 URL for '{char['name']}': {char['img1']}"
