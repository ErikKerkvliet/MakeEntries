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


def test_combine_merges_images_by_index(main):
    """When names differ but image_id matches, images are still merged."""
    vndb = [_char("アリス")]
    site = [_char("Alice", img1="/site/alice.jpg", image_id=1)]
    result = main.combine_character_data(site, vndb)
    assert result[0]["img1"] == "/site/alice.jpg"


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
