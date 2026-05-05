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
