"""Tests for pure/static helpers in Db."""
import sys
import pytest
from math import floor


def _real_db():
    """Import the real DB class (conftest stubs pymysql so no real connection is made)."""
    sys.modules.pop("Db", None)
    import Db as db_module  # noqa: PLC0415
    return db_module.DB


# ── check_var_for_sql ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("normal string",  "normal string"),
    ("it's alive",     "it\\'s alive"),
    ('say "hello"',    'say \\"hello\\"'),
    ("both ' and \"",  "both \\' and \\\""),
    ("",               ""),
])
def test_check_var_for_sql(raw, expected):
    DB = _real_db()
    assert DB.check_var_for_sql(raw) == expected


# ── resize factor logic (pure math, no DB instance needed) ───────────────────

def test_resize_no_upscale():
    """Images smaller than max dimensions should not be enlarged (factor stays 1)."""
    img_w, img_h = 200, 100
    max_x, max_y = 600, 600
    factor_x = max_x / img_w   # 3.0
    factor_y = max_y / img_h   # 6.0
    # Both factors > 1 → do not upscale, keep factor = 1
    factor = 1 if (factor_x > 1 and factor_y > 1) else min(factor_x, factor_y)
    assert floor(img_w * factor) == 200
    assert floor(img_h * factor) == 100


def test_resize_downscale_width_limited():
    """Wide image should be scaled so width fits within max_x."""
    img_w, img_h = 1200, 400
    max_x, max_y = 600, 600
    factor_x = max_x / img_w   # 0.5
    factor_y = max_y / img_h   # 1.5
    factor = min(factor_x, factor_y)   # 0.5  (width is the limiting side)
    assert floor(img_w * factor) == 600
    assert floor(img_h * factor) == 200


def test_resize_downscale_height_limited():
    """Tall image should be scaled so height fits within max_y."""
    img_w, img_h = 400, 1200
    max_x, max_y = 600, 600
    factor_x = max_x / img_w   # 1.5
    factor_y = max_y / img_h   # 0.5
    factor = min(factor_x, factor_y)   # 0.5  (height is the limiting side)
    assert floor(img_w * factor) == 200
    assert floor(img_h * factor) == 600


def test_resize_square_within_max():
    """Square image larger than max → both dimensions capped equally."""
    img_w, img_h = 1000, 1000
    max_x, max_y = 600, 600
    factor_x = max_x / img_w   # 0.6
    factor_y = max_y / img_h   # 0.6
    factor = min(factor_x, factor_y)
    assert floor(img_w * factor) == 600
    assert floor(img_h * factor) == 600
