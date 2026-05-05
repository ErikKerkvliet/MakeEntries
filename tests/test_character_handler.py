"""Tests for CharacterHandler."""
import pytest
from CharacterHandler import CharacterHandler


class _FakeDB:
    def __init__(self, rows):
        self._rows = rows

    def find_characters(self, character):
        return self._rows


class _FakeGlv:
    def __init__(self, rows):
        self.db = _FakeDB(rows)


def _char(name, romanji=""):
    return {"name": name, "romanji": romanji}


# ── character (single) ────────────────────────────────────────────────────────

def test_character_returns_empty_when_no_db_rows():
    glv = _FakeGlv([])
    handler = CharacterHandler(glv)
    result = handler.character(_char("Alice"))
    assert result == {}


def test_character_builds_match_dict():
    rows = [(10, 42, "Alice", "Game Title")]
    glv = _FakeGlv(rows)
    handler = CharacterHandler(glv)
    result = handler.character(_char("Alice"))
    assert 10 in result
    assert result[10] == "42, Alice"


def test_character_prefers_romanji_over_title():
    rows = [(10, 42, "AliceRomanji", "AliceTitle")]
    glv = _FakeGlv(rows)
    handler = CharacterHandler(glv)
    result = handler.character(_char("Alice"))
    assert result[10] == "42, AliceRomanji"


def test_character_falls_back_to_title_when_romanji_empty():
    rows = [(10, 42, "", "AliceTitle")]
    glv = _FakeGlv(rows)
    handler = CharacterHandler(glv)
    result = handler.character(_char("Alice"))
    assert result[10] == "42, AliceTitle"


def test_character_skips_rows_without_entry_id():
    rows = [(10, None, "Alice", "Title")]
    glv = _FakeGlv(rows)
    handler = CharacterHandler(glv)
    result = handler.character(_char("Alice"))
    assert result == {}


def test_character_deduplicates_by_char_id():
    rows = [
        (10, 42, "Alice", "Game A"),
        (10, 43, "Alice", "Game B"),  # same cid → deduplicated
    ]
    glv = _FakeGlv(rows)
    handler = CharacterHandler(glv)
    result = handler.character(_char("Alice"))
    assert len(result) == 1
    assert 10 in result


# ── characters (batch) ───────────────────────────────────────────────────────

def test_characters_adds_matches_key_to_all():
    rows = [(5, 1, "Alice", "Entry")]
    glv = _FakeGlv(rows)
    handler = CharacterHandler(glv)
    chars = [_char("Alice"), _char("Bob")]
    result = handler.characters(chars)
    assert all("matches" in c for c in result)


def test_characters_preserves_order():
    glv = _FakeGlv([])
    handler = CharacterHandler(glv)
    chars = [_char("Alice"), _char("Bob"), _char("Carol")]
    result = handler.characters(chars)
    assert [c["name"] for c in result] == ["Alice", "Bob", "Carol"]
