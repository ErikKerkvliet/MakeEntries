"""
Standalone test for MainUI.py.
Run with:  ../.venv/bin/python test_main_ui.py

Opens the full application window (MainUI + ScrolledFrame) with fake data so
you can verify layout, scrolling, and UI behaviour without a DB or browser.

Edit the FAKE_DATA section below to point cover/char images to real files on
your system. Any path that does not exist will simply be skipped.
"""

import os
import sys
import types

# ── 1. Stub heavy dependencies BEFORE importing project modules ────────────────

def _make_stub_module(name):
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod

# Stub selenium so Globalvar.py can be imported without it installed/active
selenium       = _make_stub_module('selenium')
selenium_common = _make_stub_module('selenium.common')
selenium_common_exc = _make_stub_module('selenium.common.exceptions')
selenium_common_exc.NoSuchElementException = Exception
selenium.common = selenium_common
selenium_common.exceptions = selenium_common_exc

selenium_wd    = _make_stub_module('selenium.webdriver')
selenium_wd_cb = _make_stub_module('selenium.webdriver.common')
selenium_wd_cb_by = _make_stub_module('selenium.webdriver.common.by')

class _By:
    ID           = 'id'
    XPATH        = 'xpath'
    CSS_SELECTOR = 'css selector'
    TAG_NAME     = 'tag name'
    LINK_TEXT    = 'link text'
    PARTIAL_LINK_TEXT = 'partial link text'
    CLASS_NAME   = 'class name'
    NAME         = 'name'

selenium_wd_cb_by.By = _By
selenium.webdriver = selenium_wd
selenium_wd.common = selenium_wd_cb
selenium_wd_cb.by  = selenium_wd_cb_by

# Stub DB so Globalvar.__init__ doesn't open a real connection
class _FakeDB:
    def __init__(self, *a, **kw):
        self.connection = None

db_mod = _make_stub_module('Db')
db_mod.DB = _FakeDB


# ── 2. Minimal Globalvar stand-in ─────────────────────────────────────────────

class FakeGlobalvar:
    """Mimics the glv interface that MainUI and ScrolledFrame.App expect."""

    def __init__(self):
        self.db        = _FakeDB()
        self.db_label  = 'game'          # used in App.submit; keep it non-anidb
        self.db_site   = ''
        self.test      = False

    def log(self, message, log_type='message', browser=None):
        print(f'[LOG] {message}')

    def quit(self):
        print('[LOG] quit called')
        sys.exit(0)


# ── 3. Fake data ───────────────────────────────────────────────────────────────
# Point these paths to real images on your system to see actual pictures.
# Any path that doesn't exist will be gracefully skipped by ScrolledFrame.

HOME       = os.path.expanduser('~')
ENTRY_DIR  = f'{HOME}/MakeEntries/5020'   # adjust to a real entry folder

def _img(path):
    """Return path if the file exists, otherwise empty string."""
    return path if os.path.isfile(path) else ''

FAKE_DATA = {
    'cover1':     _img(f'{ENTRY_DIR}/_cover_1.jpg'),
    'cover2':     _img(f'{ENTRY_DIR}/_cover_2.jpg'),
    'title':      'Please Teach! My Angel',
    'romanji':    'Please Teach! My Angel',
    'developer1': 'Petit Pajamas',
    'developer2': '',
    'released':   '2004-05-28',
    'webpage':    'http://www.pajamas.ne.jp/pretty/',
    'infopage':   'https://vndb.org/v5020',
    'chars': [
        {
            'name':         '蒼乃 翼',
            'romanji':      'Aono Tsubasa',
            'gender':       'female',
            'measurements': '82-55-83',
            'height':       '155cm',
            'weight':       '',
            'cup':          'B',
            'age':          '17',
            'img1':         _img(f'{ENTRY_DIR}/chars/1/__img.jpg'),
            'img2':         _img(f'{ENTRY_DIR}/chars/1/charb.jpg'),
            'matches':      {},
        },
        {
            'name':         '天川 聖玲奈',
            'romanji':      'Amakawa Serena',
            'gender':       'female',
            'measurements': '92-62-88',
            'height':       '168cm',
            'weight':       '',
            'cup':          'F',
            'age':          '',
            'img1':         _img(f'{ENTRY_DIR}/chars/2/__img.jpg'),
            'img2':         _img(f'{ENTRY_DIR}/chars/2/charb.jpg'),
            'matches':      {},
        },
        {
            'name':         '蒼乃野々香',
            'romanji':      'Aono Nonoka',
            'gender':       'female',
            'measurements': '',
            'height':       '',
            'weight':       '',
            'cup':          '',
            'age':          '',
            'img1':         _img(f'{ENTRY_DIR}/chars/3/__img.jpg'),
            'img2':         _img(f'{ENTRY_DIR}/chars/3/charb.jpg'),
            'matches':      {},
        },
    ],
    'samples': [
        path for path in [
            _img(f'{ENTRY_DIR}/samples/sample1.jpg'),
            _img(f'{ENTRY_DIR}/samples/sample2.jpg'),
            _img(f'{ENTRY_DIR}/samples/sample1.jpg'),
            _img(f'{ENTRY_DIR}/samples/sample2.jpg'),
            _img(f'{ENTRY_DIR}/samples/sample1.jpg'),
            _img(f'{ENTRY_DIR}/samples/sample2.jpg'),
            _img(f'{ENTRY_DIR}/samples/sample3.jpg'),
            _img(f'{ENTRY_DIR}/samples/sample4.jpg'),
        ] if path
    ],
}

FAKE_VNDB_ID = 5020


# ── 4. Run ─────────────────────────────────────────────────────────────────────

def main():
    glv = FakeGlobalvar()

    from MainUI import MainUI

    ui = MainUI(glv)
    ui.fill_data(FAKE_DATA, FAKE_VNDB_ID)
    ui.do_loop()


if __name__ == '__main__':
    main()
