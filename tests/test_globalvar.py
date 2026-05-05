"""Tests for pure utility methods in Globalvar."""
import pytest
from Globalvar import Globalvar
from selenium.webdriver.common.by import By


@pytest.fixture
def glv(monkeypatch):
    """Globalvar with DB and logging stubbed out."""
    monkeypatch.setattr("Globalvar.DB", lambda g: type("DB", (), {"connection": None, "log": lambda *a: None})())
    g = Globalvar()
    return g


# ── clean_string ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("a &amp; b",       "a & b"),
    ("&lt;tag&gt;",     "<tag>"),
    ("price&nbsp;now",  "price now"),
    ("&quot;hi&quot;",  '"hi"'),
    ("&apos;s",         "'s"),
    ("&copy; 2025",     "© 2025"),
    ("no entities",     "no entities"),
    ("&amp;&amp;",      "&&"),
])
def test_clean_string(raw, expected):
    assert Globalvar.clean_string(raw) == expected


# ── un_simplify ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("short,expected", [
    ("css",          By.CSS_SELECTOR),
    ("tag",          By.TAG_NAME),
    ("text",         By.LINK_TEXT),
    ("link_text",    By.LINK_TEXT),
    ("partial_text", By.PARTIAL_LINK_TEXT),
    ("class",        By.CLASS_NAME),
    # Already-canonical values pass through unchanged
    (By.ID,    By.ID),
    (By.XPATH, By.XPATH),
    # Unknown string passes through as-is
    ("custom", "custom"),
])
def test_un_simplify(short, expected):
    assert Globalvar.un_simplify(short) == expected
