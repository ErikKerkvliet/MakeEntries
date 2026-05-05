"""
Browser integration tests for the DLSite scraper.

Uses DLSite product RJ040256 — https://www.dlsite.com/maniax/work/=/product_id/RJ040256.html

Run with:
    .venv/bin/pytest tests/browser/test_dlsite_browser.py -v
"""

import re
import os
import pytest
from bs4 import BeautifulSoup
from dlsite import DlSite

DLSITE_ID = "RJ040256"

pytestmark = pytest.mark.browser


# ── One scrape per module ─────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def data(driver, glv):
    d = DlSite(glv)
    return d.get_entry_data(driver, DLSITE_ID, glv.vndb_id)


# ── Entry data structure ──────────────────────────────────────────────────────

def test_entry_has_required_keys(data):
    for key in ("cover", "infopage", "released", "chars", "samples"):
        assert key in data, f"Missing key: {key}"


def test_infopage_is_dlsite_url(data):
    assert "dlsite.com" in data["infopage"], \
        f"Unexpected infopage: {data['infopage']}"


def test_infopage_contains_product_id(data):
    assert DLSITE_ID in data["infopage"]


def test_released_matches_yyyy_mm_dd(data):
    date = data["released"]
    if date:
        assert re.match(r"\d{4}/\d{2}/\d{2}", date), \
            f"Unexpected release date format: {date}"


def test_samples_is_list(data):
    assert isinstance(data["samples"], list)


def test_chars_is_empty_list(data):
    # DLSite scraper does not extract character data
    assert data["chars"] == []


def test_cover_is_set(data):
    # When a main image exists, cover should be a local path
    assert data["cover"] != "", "Expected cover to be set"


def test_cover_path_ends_with_jpg(data):
    if data["cover"]:
        assert data["cover"].endswith(".jpg"), \
            f"Unexpected cover path: {data['cover']}"


def test_sample_paths_end_with_jpg(data):
    for s in data["samples"]:
        assert s.endswith(".jpg"), f"Unexpected sample path: {s}"


def test_images_downloaded_to_temp(data, glv):  # noqa: data ensures the scrape ran first
    temp_dir = os.path.join(glv.app_folder, glv.vndb_id, "temp")
    assert os.path.isdir(temp_dir), f"Temp dir not found: {temp_dir}"
    files = os.listdir(temp_dir)
    assert len(files) > 0, "No files downloaded to temp directory"


# ── get_release_date HTML parsing ─────────────────────────────────────────────

@pytest.mark.parametrize("html,expected", [
    (
        '<table id="work_outline"><tr>'
        '<th>販売日</th><td>2022年04月28日</td>'
        '</tr></table>',
        "2022/04/28",
    ),
    (
        '<table id="work_outline"><tr>'
        '<th>販売日</th><td>2019年12月06日</td>'
        '</tr></table>',
        "2019/12/06",
    ),
    (
        # No release date row
        '<table id="work_outline"><tr><th>ジャンル</th><td>RPG</td></tr></table>',
        None,
    ),
])
def test_get_release_date_parsing(html, expected):
    d = DlSite.__new__(DlSite)
    d.soup = BeautifulSoup(html, "html.parser")
    assert d.get_release_date() == expected


# ── get_images URL construction ───────────────────────────────────────────────

def test_get_images_skips_non_sample_images(tmp_path):
    html = """
    <html><body>
      <img src="//img.dlsite.jp/modpub/images2/work/doujin/RJ338000/RJ338204_img_smp1.jpg"/>
      <img src="//img.dlsite.jp/modpub/images2/work/doujin/RJ338000/RJ338204_img_main.jpg"/>
      <img src="//img.dlsite.jp/other/logo.png"/>
    </body></html>
    """
    glv_stub = type("G", (), {
        "log": lambda *a, **kw: None,
        "app_folder": str(tmp_path),
        "vndb_id": "test",
    })()
    os.makedirs(f"{tmp_path}/test/temp", exist_ok=True)

    d = DlSite.__new__(DlSite)
    d.glv = glv_stub
    d.base_url = "https:"
    d.dlsite_id = DLSITE_ID
    d.soup = BeautifulSoup(html, "html.parser")

    # Patch download_image to avoid real HTTP
    downloaded = []
    d.download_image = staticmethod(lambda url, path: downloaded.append(url))

    result = d.get_images({"cover": "", "samples": []})

    # Main image → cover, smp image → sample; logo.png must be excluded
    assert any("_img_main" in u or "_img_smp" in u for u in downloaded)
    assert not any("logo.png" in u for u in downloaded)
    assert result["cover"] != "" or len(result["samples"]) > 0
