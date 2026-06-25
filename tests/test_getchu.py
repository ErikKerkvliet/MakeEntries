"""Tests for pure static helpers in Getchu."""
import pytest
from Getchu import Getchu


# ── find_str ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("full,sub,expected_pos", [
    ("Hello World",  "World",  6),
    ("Hello World",  "Hello",  0),
    ("Hello World",  "lo",     3),
    ("Hello World",  "hello",  0),   # case-insensitive
    ("Hello World",  "WORLD",  6),   # case-insensitive
    ("abcdef",       "xyz",   -1),   # not found
    ("",             "a",     -1),   # empty haystack
    ("abc",          "abc",    0),   # full match
])
def test_find_str(full, sub, expected_pos):
    assert Getchu.find_str(full, sub) == expected_pos


def test_find_str_returns_first_occurrence():
    # "ab" appears at index 0 and 3; should return first position
    result = Getchu.find_str("ababab", "ab")
    assert result == 0


# ── character name extraction (get_character_data) ─────────────────────────────

def _extract_name(chara_name_html):
    """Run get_character_data on a single row and return the parsed name."""
    g = Getchu.__new__(Getchu)
    g.nrs = {}
    g.getchu_to_vndb_index = {}
    g.page_url = "http://www.getchu.com"
    g.glv = type("G", (), {"log": lambda *a, **kw: None,
                           "app_folder": "/tmp", "vndb_id": "0"})()
    tr = (f'<td><h4 class="chara-name">{chara_name_html}</h4></td>'
          f'<td><img src="/brandnew/x/chara1.jpg"/></td>')
    data = {"chars": []}
    g.get_character_data(["header", tr], data, None)
    return data["chars"][0]["name"]


@pytest.mark.parametrize("html,expected", [
    # Caption + <br> + name + reading + CV  → only the name after <br>, before （
    ('<span class="bootstrap">\n母性あふれる看板娘<br>千々石 野乃（ちじわ のの） CV：高野零\n</span>',
     "千々石 野乃"),
    # Self-closing <br/> variant
    ("看板娘<br/>星 詠美（ほし えみ）", "星 詠美"),
    # No caption, no <br> — plain name + CV
    ("桜井 美咲 CV：田村ゆかり", "桜井 美咲"),
    # No CV, no reading
    ("パトリーナ", "パトリーナ"),
])
def test_character_name_extraction(html, expected):
    assert _extract_name(html) == expected
