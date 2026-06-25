"""Tests for pure logic methods in Main."""
import os
import sys
import pytest

# Main imports undetected_chromedriver at the top level; it's already stubbed
# by conftest.py.  We also need to stub chromedriver_autoinstaller if present.
import types
_ci = types.ModuleType("chromedriver_autoinstaller")
_ci.install = lambda: None
sys.modules.setdefault("chromedriver_autoinstaller", _ci)

from Main import Main


@pytest.fixture
def main(monkeypatch):
    """Main instance with Globalvar, DB, and driver stubbed out."""

    class _FakeDB:
        connection = None
        def __init__(self, *a, **kw): pass
        def log(self, *a, **kw): pass

    class _FakeGlv:
        db = _FakeDB()
        db_label = "vndb"
        test = False
        app_folder = "/tmp/makeentries_test"
        vndb_id = "9999"
        driver = None
        no_resize = False
        video_file_path = None

        def log(self, *a, **kw): pass
        def set_test(self, v): self.test = v
        def set_tables(self): pass
        def get_test(self): return self.test
        def make_char_dir(self, *a): pass

    monkeypatch.setattr("Main.Globalvar", _FakeGlv)
    monkeypatch.setattr("Main.CharacterHandler", lambda glv: type("CH", (), {"characters": lambda self, c: c})())

    m = Main.__new__(Main)
    m.glv = _FakeGlv()
    m.character_handler = type("CH", (), {"characters": staticmethod(lambda c: c)})()
    m.vndb_id = "9999"
    m.getchu_id = None
    m.site_id = None
    m.db_label = "vndb"
    m.site_label = "getchu"
    return m


# ── create_character_entry ────────────────────────────────────────────────────

def test_create_character_entry_full():
    char = {
        "name": "Alice",
        "romanji": "Alice",
        "gender": "female",
        "height": "160cm",
        "weight": "50kg",
        "measurements": "88-58-86",
        "age": "18",
        "cup": "D",
        "img1": "/path/a.jpg",
        "img2": "/path/b.jpg",
        "image_id": 3,
    }
    entry = Main.create_character_entry(char)
    assert entry["name"] == "Alice"
    assert entry["cup"] == "D"
    assert entry["image_id"] == 3
    assert entry["img1"] == "/path/a.jpg"


def test_create_character_entry_minimal():
    char = {"name": "Bob", "romanji": ""}
    entry = Main.create_character_entry(char)
    assert entry["name"] == "Bob"
    assert entry["img1"] == ""
    assert entry["img2"] == ""
    assert "image_id" not in entry


# ── combine_character_data ────────────────────────────────────────────────────

def _char(name, romanji="", **kw):
    base = {
        "name": name, "romanji": romanji,
        "gender": "", "height": "", "weight": "",
        "measurements": "", "age": "", "cup": "",
        "img1": "", "img2": "",
    }
    base.update(kw)
    return base


def test_combine_uses_vndb_order(main):
    vndb = [_char("Alice"), _char("Bob")]
    site = [_char("Bob"), _char("Alice")]
    result = main.combine_character_data(site, vndb)
    assert [r["name"] for r in result] == ["Alice", "Bob"]


def test_combine_merges_images_by_name(main):
    vndb = [_char("Alice")]
    site = [_char("Alice", img1="/site/alice.jpg")]
    result = main.combine_character_data(site, vndb)
    assert result[0]["img1"] == "/site/alice.jpg"


def test_combine_does_not_merge_by_position_when_names_differ(main):
    """VNDB is leading: a Getchu char must NOT be merged onto a VNDB char just
    because their list position (image_id) lines up. Pairing by position grabbed
    the wrong image whenever the two sites ordered characters differently."""
    vndb = [_char("アリス")]
    site = [_char("Alice", img1="/site/alice.jpg", image_id=1)]
    result = main.combine_character_data(site, vndb)
    # The VNDB character keeps its own (empty) image, no Getchu image stolen.
    assert result[0]["img1"] == ""
    # The unmatched Getchu character is appended as a separate entry instead.
    assert [r["name"] for r in result] == ["アリス", "Alice"]


def test_combine_appends_unmatched_site_chars(main):
    vndb = [_char("Alice")]
    site = [_char("Alice", img1="/a.jpg"), _char("Charlie", img1="/c.jpg")]
    result = main.combine_character_data(site, vndb)
    assert len(result) == 2
    assert result[1]["name"] == "Charlie"


def test_combine_ignores_spaces_in_name_matching(main):
    vndb = [_char("蒼乃 翼")]
    site = [_char("蒼乃翼", img1="/wing.jpg")]
    result = main.combine_character_data(site, vndb)
    assert result[0]["img1"] == "/wing.jpg"


# ── organize_images ───────────────────────────────────────────────────────────

def test_organize_images_cover(main, tmp_path, monkeypatch):
    root = str(tmp_path / "entry")
    root_temp = str(tmp_path / "temp")
    os.makedirs(root_temp)

    cover_file = tmp_path / "temp" / "cover1.jpg"
    cover_file.write_bytes(b"img")

    moved = {}

    def fake_move(old, new):
        moved[new] = old

    monkeypatch.setattr(main, "move_file", fake_move)
    monkeypatch.setattr(os.path, "isfile", lambda p: str(p).endswith(".jpg"))

    main.vndb_id = "9999"
    main.glv.app_folder = str(tmp_path)
    main.glv.db_label = "vndb"

    main.organize_images(root, root_temp, ["cover1.jpg"])
    assert any("_cover_1.jpg" in k for k in moved)


def test_organize_images_sample(main, tmp_path, monkeypatch):
    root = str(tmp_path / "entry")
    root_temp = str(tmp_path / "temp")
    os.makedirs(root_temp)

    moved = {}
    monkeypatch.setattr(main, "move_file", lambda old, new: moved.__setitem__(new, old))
    monkeypatch.setattr(os.path, "isfile", lambda p: str(p).endswith(".jpg"))

    main.organize_images(root, root_temp, ["sample_3.jpg"])
    assert any("sample3.jpg" in k for k in moved)


def test_organize_images_char(main, tmp_path, monkeypatch):
    root = str(tmp_path / "entry")
    root_temp = str(tmp_path / "temp")

    moved = {}
    monkeypatch.setattr(main, "move_file", lambda old, new: moved.__setitem__(new, old))
    monkeypatch.setattr(os.path, "isfile", lambda p: str(p).endswith(".jpg"))

    main.organize_images(root, root_temp, ["char_2_img1.jpg"])
    assert any("__img.jpg" in k and "/2/" in k for k in moved)


def test_organize_images_char_vndb(main, tmp_path, monkeypatch):
    root = str(tmp_path / "entry")
    root_temp = str(tmp_path / "temp")

    moved = {}
    monkeypatch.setattr(main, "move_file", lambda old, new: moved.__setitem__(new, old))
    monkeypatch.setattr(os.path, "isfile", lambda p: str(p).endswith(".jpg"))

    main.organize_images(root, root_temp, ["char_2_vndb.jpg"])
    assert any("vndb.jpg" in k and "/2/" in k for k in moved)


# ── vndb-getchu image wiring ──────────────────────────────────────────────────

def test_combine_preserves_vndb_img1(main):
    vndb = [_char("アリス", img1="https://vndb/a.jpg")]
    site = [_char("アリス", img1="/g.jpg", image_id=1)]
    result = main.combine_character_data(site, vndb)
    # img1 becomes the Getchu image; the VNDB portrait is kept separately.
    assert result[0]["img1"] == "/g.jpg"
    assert result[0]["vndb_img1"] == "https://vndb/a.jpg"


def test_combine_data_uses_getchu_urls_for_vndb_getchu(main):
    data_vndb = {"title": "T", "romanji": "", "developer1": "",
                 "developer2": "", "webpage": "", "cover": ""}
    chars_vndb = {"chars": [_char("アリス", img1="https://vndb/a.jpg")]}
    site_char = _char("アリス", image_id=1, img1="/local/getchu.jpg",
                      getchu_img1="http://getchu/a1.jpg",
                      getchu_img2="http://getchu/a2.jpg")
    data_site = {"infopage": "", "cover": "", "released": "", "samples": [],
                 "chars": [site_char]}

    data = main.combine_data(data_vndb, chars_vndb, data_site)

    assert data["show_vndb"] is True
    c = data["chars"][0]
    assert c["vndb_img1"] == "https://vndb/a.jpg"   # VNDB portrait preserved
    assert c["img1"] == "http://getchu/a1.jpg"       # Getchu URL used for download
    assert c["img2"] == "http://getchu/a2.jpg"


def test_combine_data_no_show_vndb_for_dlsite(main):
    main.site_label = "dlsite"
    data_vndb = {"title": "T", "romanji": "", "developer1": "",
                 "developer2": "", "webpage": "", "cover": ""}
    chars_vndb = {"chars": [_char("アリス", img1="https://vndb/a.jpg")]}
    data_site = {"infopage": "", "cover": "", "released": "", "samples": [], "chars": []}

    data = main.combine_data(data_vndb, chars_vndb, data_site)
    assert "show_vndb" not in data
