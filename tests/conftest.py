"""
Stub out heavy external dependencies (selenium, pymysql, pyperclip,
undetected_chromedriver) so all project modules can be imported in tests
without a running browser or database.
"""
import sys
import types


def _stub(name):
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


# ── selenium ──────────────────────────────────────────────────────────────────
selenium = _stub("selenium")
sel_common = _stub("selenium.common")
sel_exc = _stub("selenium.common.exceptions")
sel_exc.NoSuchElementException = Exception
selenium.common = sel_common
sel_common.exceptions = sel_exc

sel_wd = _stub("selenium.webdriver")
sel_wd_common = _stub("selenium.webdriver.common")
sel_wd_common_by = _stub("selenium.webdriver.common.by")
sel_wd_support = _stub("selenium.webdriver.support")
sel_wd_support_ec = _stub("selenium.webdriver.support.expected_conditions")
sel_wd_support_ec.presence_of_element_located = lambda *a: None
sel_wd_support_ec.visibility_of_element_located = lambda *a: None
sel_wd_support_ui = _stub("selenium.webdriver.support.ui")
sel_wd_support_ui.WebDriverWait = type("WebDriverWait", (), {"until": lambda *a, **kw: None})
sel_wd_chrome = _stub("selenium.webdriver.chrome")
sel_wd_chrome_opts = _stub("selenium.webdriver.chrome.options")

sel_exc.TimeoutException = Exception


class _By:
    ID = "id"
    XPATH = "xpath"
    CSS_SELECTOR = "css selector"
    TAG_NAME = "tag name"
    LINK_TEXT = "link text"
    PARTIAL_LINK_TEXT = "partial link text"
    CLASS_NAME = "class name"
    NAME = "name"


sel_wd_common_by.By = _By
selenium.webdriver = sel_wd
sel_wd.common = sel_wd_common
sel_wd_common.by = sel_wd_common_by
sel_wd.support = sel_wd_support
sel_wd_support.expected_conditions = sel_wd_support_ec
sel_wd_support.ui = sel_wd_support_ui
sel_wd.chrome = sel_wd_chrome
sel_wd_chrome.options = sel_wd_chrome_opts
sel_wd_chrome_opts.Options = object

# ── undetected_chromedriver ───────────────────────────────────────────────────
uc = _stub("undetected_chromedriver")
uc.Chrome = object
uc.ChromeOptions = object

# ── pymysql ───────────────────────────────────────────────────────────────────
pymysql = _stub("pymysql")
pymysql.Connection = lambda **kw: None

# ── pyperclip ─────────────────────────────────────────────────────────────────
pyperclip = _stub("pyperclip")
pyperclip.paste = lambda: ""

# ── dotenv ────────────────────────────────────────────────────────────────────
dotenv = _stub("dotenv")
dotenv.load_dotenv = lambda: None

# ── PIL ───────────────────────────────────────────────────────────────────────
pil = _stub("PIL")
pil_image = _stub("PIL.Image")


class _FakeImage:
    LANCZOS = 1
    format = "JPEG"

    def open(self, *a, **kw):
        return self

    def resize(self, *a, **kw):
        return self

    def save(self, *a, **kw):
        pass

    def crop(self, *a, **kw):
        return self

    def convert(self, *a, **kw):
        return self

    width = 100
    height = 100
    mode = "RGB"


pil_image.Image = _FakeImage()
pil_image.LANCZOS = _FakeImage.LANCZOS
pil.Image = pil_image

pil_imagetk = _stub("PIL.ImageTk")
pil_imagetk.PhotoImage = object
pil.ImageTk = pil_imagetk

# ── Add src/ to path so project modules are importable ───────────────────────
import os

src_path = os.path.join(os.path.dirname(__file__), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, os.path.abspath(src_path))
