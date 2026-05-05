"""
Browser integration test fixtures.

The parent tests/conftest.py stubs out selenium and other heavy packages so
unit tests run without a real browser.  This file runs after that one and
removes those stubs so the real packages are imported here.

Run browser tests with:
    .venv/bin/pytest tests/browser/ -v
"""

import os
import sys
import pytest

# ── 1. Strip the unit-test stubs injected by the parent conftest ──────────────
_stubs = [
    "selenium", "undetected_chromedriver", "PIL", "pymysql",
    "pyperclip", "dotenv", "Db", "Globalvar", "AniDB", "Vndb",
    "Getchu", "dlsite", "CharacterHandler", "ScrolledFrame",
    "MainUI", "AskEntry", "Main",
]
for _k in list(sys.modules):
    if any(_k == s or _k.startswith(s + ".") for s in _stubs):
        del sys.modules[_k]

# ── 2. Ensure src/ is on the path ─────────────────────────────────────────────
_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if _src not in sys.path:
    sys.path.insert(0, _src)

# ── 3. Load env vars (.env contains ANIDB_USER / ANIDB_PASSWORD) ──────────────
from dotenv import load_dotenv
load_dotenv()


# ── 4. Fake DB — scrapers need glv.db but we don't want a real MySQL connection
class _FakeDB:
    connection = None

    def __init__(self, glv):
        glv.log("FakeDB: skipping real DB connection")

    def log(self, *a, **kw):
        pass

    def find_characters(self, *a):
        return []

    def find_developer_by_anidb_id(self, *a):
        return []

    def get_series_by_anidb_id(self, *a):
        return []

    def check_duplicate(self, *a, **kw):
        return False


# Patch Db.DB *before* Globalvar is imported so `from Db import DB` gets FakeDB
import Db as _db_mod
_db_mod.DB = _FakeDB

from Globalvar import Globalvar
import undetected_chromedriver as uc


# ── 5. Shared fixtures ────────────────────────────────────────────────────────

def _chrome_major_version() -> int:
    """Read the major version of the system Chrome binary."""
    import subprocess
    for binary in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium"):
        try:
            out = subprocess.check_output([binary, "--version"], stderr=subprocess.DEVNULL).decode()
            # output: "Google Chrome 147.0.7727.137"
            return int(out.strip().split()[-1].split(".")[0])
        except (FileNotFoundError, ValueError, IndexError):
            continue
    return 0   # let uc pick if detection fails


@pytest.fixture(scope="session")
def driver():
    """One Chrome instance for the entire test session."""
    opts = uc.ChromeOptions()
    opts.add_argument("--no-sandbox")
    version = _chrome_major_version()
    d = uc.Chrome(options=opts, version_main=version if version else None)
    d.set_window_size(1024, 768)
    yield d
    d.quit()


@pytest.fixture(scope="module")
def glv(driver, tmp_path_factory):
    """One Globalvar per test module, each with its own temp workspace."""
    tmp = tmp_path_factory.mktemp("browser")
    g = Globalvar()
    g.driver = driver
    g.db_label = "vndb"
    g.app_folder = str(tmp)
    g.vndb_id = "test"
    # Create the directory structure scrapers expect
    for sub in ("test/temp", "test/samples", "test/chars"):
        os.makedirs(f"{tmp}/{sub}", exist_ok=True)
    return g
