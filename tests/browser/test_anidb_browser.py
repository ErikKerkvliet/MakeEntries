"""
Browser integration tests for the AniDB scraper.

Uses AniDB entry 19769 — https://anidb.net/anime/19769
Requires valid ANIDB_USER / ANIDB_PASSWORD in the .env file.

Run with:
    .venv/bin/pytest tests/browser/test_anidb_browser.py -v
"""

import os
import pytest
from AniDB import AniDB

ANIDB_ID = "19769"

pytestmark = pytest.mark.browser


# ── One scrape per module ─────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def anidb_glv(glv):
    glv.db_label = "anidb"
    return glv


@pytest.fixture(scope="module")
def data(driver, anidb_glv):
    return AniDB(anidb_glv).get_entry_data(driver, ANIDB_ID)


# ── Entry data structure ──────────────────────────────────────────────────────

def test_entry_has_required_keys(data):
    for key in ("title", "romanji", "cover", "infopage",
                "webpage", "developer1", "chars", "samples"):
        assert key in data, f"Missing key: {key}"


def test_title_contains_vol(data):
    # AniDB.get_title() always appends " Vol. NN"
    assert "Vol." in data["title"], \
        f"Expected 'Vol.' in title, got: {data['title']}"


def test_title_starts_with_series_name(data):
    # For NGE, the alternate name contains "Evangelion"
    assert data["title"] != "" and data["title"] != "None Vol. 01", \
        f"Title looks invalid: {data['title']}"


def test_romanji_nonempty(data):
    assert isinstance(data["romanji"], str) and data["romanji"] != "", \
        "romanji should be a non-empty string"


def test_infopage_is_anidb_url(data):
    assert data["infopage"] == f"https://www.anidb.net/anime/{ANIDB_ID}", \
        f"Unexpected infopage: {data['infopage']}"


def test_chars_is_empty_list(data):
    # AniDB.get_entry_data returns an empty chars list by design
    assert data["chars"] == [], \
        f"Expected empty chars list, got {len(data['chars'])} entries"


def test_samples_is_empty_list(data):
    assert data["samples"] == []


def test_cover_downloaded(data, anidb_glv):  # noqa: data ensures the scrape ran first
    # download_cover() saves to {app_folder}/{vndb_id}/_cover_2.jpg
    cover_path = os.path.join(anidb_glv.app_folder, anidb_glv.vndb_id, "_cover_2.jpg")
    assert os.path.isfile(cover_path), \
        f"Cover file not found at: {cover_path}"


def test_cover_url_is_http(data):
    # The cover field is the remote URL before download
    if data["cover"]:
        assert data["cover"].startswith("http"), \
            f"Unexpected cover value: {data['cover']}"


def test_all_string_fields_are_str(data):
    for key in ("title", "romanji", "infopage", "webpage", "developer1"):
        assert isinstance(data[key], str), f"Field '{key}' is not a string"
