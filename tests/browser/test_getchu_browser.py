"""
Browser integration tests for the Getchu scraper.

Uses Getchu product 695580 — http://www.getchu.com/soft.phtml?id=695580

Run with:
    .venv/bin/pytest tests/browser/test_getchu_browser.py -v
"""

import re
import pytest
from Getchu import Getchu

GETCHU_ID = "695580"

pytestmark = pytest.mark.browser


# ── One scrape per module ─────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def data(driver, glv):
    g = Getchu(glv)
    return g.get_entry_data(driver, GETCHU_ID, glv.vndb_id)


# ── Entry data structure ──────────────────────────────────────────────────────

def test_entry_has_required_keys(data):
    for key in ("released", "cover", "infopage", "chars", "samples"):
        assert key in data, f"Missing key: {key}"


def test_infopage_is_getchu_url(data):
    assert "getchu.com" in data["infopage"], \
        f"Unexpected infopage: {data['infopage']}"


def test_infopage_contains_product_id(data):
    assert GETCHU_ID in data["infopage"]


def test_cover_is_getchu_url(data):
    if data["cover"]:
        assert "getchu.com" in data["cover"], \
            f"Unexpected cover URL: {data['cover']}"


def test_released_matches_date_format(data):
    date = data["released"]
    assert re.match(r"\d{4}[/\-]\d{2}[/\-]\d{2}", date) or date == "0000-00-00", \
        f"Unexpected release date: {date}"


def test_samples_is_list(data):
    assert isinstance(data["samples"], list)


def test_chars_is_list(data):
    assert isinstance(data["chars"], list)


# ── Character data ────────────────────────────────────────────────────────────

def test_each_char_has_required_fields(data):
    required = {"name", "romanji", "gender", "cup", "image_id",
                "img1", "img2", "getchu_img1", "getchu_img2"}
    for char in data["chars"]:
        missing = required - char.keys()
        assert not missing, f"Char '{char.get('name')}' missing: {missing}"


def test_each_char_gender_is_female(data):
    # Getchu always sets gender = 'female'
    for char in data["chars"]:
        assert char["gender"] == "female", \
            f"Expected 'female' for '{char['name']}', got '{char['gender']}'"


def test_each_char_image_id_is_positive(data):
    for char in data["chars"]:
        assert isinstance(char["image_id"], int) and char["image_id"] >= 1, \
            f"Invalid image_id for '{char['name']}': {char['image_id']}"


def test_cup_is_single_letter_or_empty(data):
    for char in data["chars"]:
        cup = char["cup"]
        assert cup == "" or (len(cup) == 1 and cup.isalpha()), \
            f"Unexpected cup value '{cup}' for '{char['name']}'"


# ── get_character_data HTML parsing ──────────────────────────────────────────

def test_character_data_name_extraction():
    """Unit-level check of the HTML parsing inside get_character_data."""
    sample_tr = (
        '<td><h4 class="chara-name">桜井 美咲 CV：田村ゆかり</h4></td>'
        '<td><img src="/image/chara1.jpg"/></td>'
    )
    g = Getchu.__new__(Getchu)
    g.nrs = {}
    g.getchu_to_vndb_index = {}

    data = {"chars": []}
    g.glv = type("G", (), {"log": lambda *a, **kw: None,
                            "app_folder": "/tmp", "vndb_id": "0"})()
    g.page_url = "http://www.getchu.com"
    g.get_character_data([sample_tr, sample_tr], data, None)

    assert len(data["chars"]) == 1
    char = data["chars"][0]
    # CV info must be stripped
    assert "CV" not in char["name"]
    assert "桜井" in char["name"] or "美咲" in char["name"]
