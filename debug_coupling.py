#!/usr/bin/env python3
"""
Character coupling debug tool.

Scrapes a VNDB entry + a Getchu product the exact same way the real app does
(reusing Vndb, Getchu and Main.combine_character_data), then shows a focused
Tkinter UI with ONLY the character couplings and the images that belong to
them:  the VNDB portrait on the left and the Getchu image(s) on the right.

The point is to make coupling problems visible:
  * characters that show up twice (a Getchu character that didn't match any
    VNDB character and gets appended as an extra entry),
  * images that don't match the name (a Getchu character matched to a VNDB
    character by *position* / image_id instead of by name).

Usage
-----
    # Scrape + cache + open the UI
    python debug_coupling.py <vndb_id> <getchu_id>

    # Scrape + cache only, no UI (e.g. on a headless box)
    python debug_coupling.py <vndb_id> <getchu_id> --no-ui

    # Re-open the UI from a previous scrape without touching the network
    python debug_coupling.py <vndb_id> --from-cache

Snapshots are written to  site_data/<vndb_id>/  (coupling.json + imgs/).
"""

import argparse
import json
import os
import sys

# ── Make src/ importable ──────────────────────────────────────────────────────
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

CACHE_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site_data")


def clean(name):
    """Same name-normalisation the coupling logic uses."""
    return (name or "").replace(" ", "").replace("　", "")


# ──────────────────────────────────────────────────────────────────────────────
# Scraping
# ──────────────────────────────────────────────────────────────────────────────
def _chrome_major_version():
    import subprocess
    for binary in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium"):
        try:
            out = subprocess.check_output([binary, "--version"], stderr=subprocess.DEVNULL).decode()
            return int(out.strip().split()[-1].split(".")[0])
        except (FileNotFoundError, ValueError, IndexError):
            continue
    return 0


class _FakeDB:
    """Stand-in so we never touch MySQL while debugging the scrape."""
    connection = None

    def __init__(self, glv):
        pass

    def log(self, *a, **kw):
        pass

    def find_characters(self, *a, **kw):
        return []

    def check_duplicate(self, *a, **kw):
        return False


def _make_glv(vndb_id):
    # Patch the DB before Globalvar imports it, so no MySQL connection is made.
    import Db as _db_mod
    _db_mod.DB = _FakeDB

    from Globalvar import Globalvar
    glv = Globalvar()
    glv.db_label = "vndb"
    glv.vndb_id = vndb_id
    glv.app_folder = os.path.join(CACHE_ROOT)  # not really used (we skip screenshots)
    return glv


def _load_html_into_driver(driver, html_path):
    """Load a saved HTML page into the driver via a temp file:// URL so the real
    DOM-based parsers can run against it without any network access."""
    import tempfile
    with open(html_path, encoding="utf-8", errors="replace") as f:
        html = f.read()
    tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
    tmp.write(html)
    tmp.close()
    driver.get("file://" + tmp.name)
    return tmp.name


def scrape(vndb_id, getchu_id, vndb_html=None):
    """Run the real scrape and return the debug structure (no UI, no DB).

    If vndb_html points at a saved VNDB chars-page HTML file, the VNDB side is
    parsed from that file instead of hitting vndb.org.
    """
    glv = _make_glv(vndb_id)

    import undetected_chromedriver as uc
    from Vndb import Vndb
    from Getchu import Getchu
    from Main import Main

    opts = uc.ChromeOptions()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--ignore-certificate-errors")
    version = _chrome_major_version()
    driver = uc.Chrome(options=opts, version_main=version or None)
    driver.set_window_size(1024, 768)
    glv.driver = driver

    try:
        # 1. VNDB characters (name, romanji, image URL).
        vndb = Vndb(glv)
        vndb.entry_id = vndb_id
        if vndb_html:
            print(f"[vndb] parsing saved chars page: {vndb_html}")
            _load_html_into_driver(driver, vndb_html)
            chars_vndb = vndb.parse_char_data()
        else:
            print(f"[vndb] fetching characters for v{vndb_id} ...")
            chars_vndb = vndb.get_char_data()
        print(f"[vndb] {len(chars_vndb['chars'])} characters")
        if not chars_vndb["chars"]:
            print(f"[vndb] WARNING: 0 characters — wrong vndb id, or VNDB blocked the "
                  f"request. Check https://vndb.org/v{vndb_id}/chars")

        # 2. Getchu characters. Reuse the real parsing/matching, but skip the
        #    Selenium screenshotting — we download the source image URLs instead.
        print(f"[getchu] fetching characters for {getchu_id} ...")
        getchu = Getchu(glv)
        getchu.download_images = lambda *a, **kw: None  # skip screenshots
        data_site = getchu.get_entry_data(driver, getchu_id, vndb_id, chars_vndb)
        site_chars = data_site["chars"]
        print(f"[getchu] {len(site_chars)} characters")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    # 3. Reproduce the real merge (this is where doubles / mismatches appear).
    main = Main.__new__(Main)  # avoid __init__ (it builds Globalvar/DB)
    combined = main.combine_character_data(site_chars, chars_vndb["chars"])

    return build_debug_data(vndb_id, getchu_id, chars_vndb["chars"], site_chars, combined)


def build_debug_data(vndb_id, getchu_id, vndb_chars, site_chars, combined):
    """Join the raw VNDB and Getchu lists exactly the way combine_character_data
    does, but keep both image sources separate so we can compare them."""
    couplings = []
    for i, v in enumerate(vndb_chars):
        vclean = clean(v.get("name", ""))

        # Mirror combine_character_data: match a Getchu char by (clean) name only.
        match, mtype = None, "none"
        for s in site_chars:
            if vclean and vclean == clean(s.get("name", "")):
                match, mtype = s, "name"
                break

        flags = []
        vndb_img = v.get("img1") or ""
        if not vndb_img:
            flags.append("no-vndb-img")
        if mtype == "none":
            flags.append("no-getchu-match")
        if match:
            if not match.get("getchu_img1") and not match.get("getchu_img2"):
                flags.append("no-getchu-img")

        couplings.append({
            "image_id": i + 1,
            "vndb_name": v.get("name", ""),
            "vndb_romanji": v.get("romanji", ""),
            # Full VNDB character data (this is what ends up in the DB; combine
            # keeps all VNDB metadata and only borrows images from Getchu).
            "vndb_gender": v.get("gender", ""),
            "vndb_height": v.get("height", ""),
            "vndb_weight": v.get("weight", ""),
            "vndb_measurements": v.get("measurements", ""),
            "vndb_age": v.get("age", ""),
            "vndb_cup": v.get("cup", ""),
            "vndb_img_url": vndb_img,
            "match_type": mtype,
            "getchu_name": match.get("name", "") if match else "",
            "getchu_cup": match.get("cup", "") if match else "",
            "getchu_img1_url": match.get("getchu_img1", "") if match else "",
            "getchu_img2_url": match.get("getchu_img2", "") if match else "",
            "flags": flags,
        })

    # Getchu characters that matched no VNDB name -> appended as extra entries.
    # These are the "double" characters.
    v_names = {clean(v.get("name", "")) for v in vndb_chars}
    extras = []
    for s in site_chars:
        if clean(s.get("name", "")) not in v_names:
            extras.append({
                "image_id": s.get("image_id"),
                "getchu_name": s.get("name", ""),
                "getchu_img1_url": s.get("getchu_img1", ""),
                "getchu_img2_url": s.get("getchu_img2", ""),
            })

    return {
        "vndb_id": vndb_id,
        "getchu_id": getchu_id,
        "n_vndb": len(vndb_chars),
        "n_getchu": len(site_chars),
        "n_combined": len(combined),
        "couplings": couplings,
        "extras": extras,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Image download + caching
# ──────────────────────────────────────────────────────────────────────────────
def _download(url, dest):
    url = (url or "").split('"')[0]
    if not url or not url.startswith("http"):
        return None
    if os.path.isfile(dest):
        return dest
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        # Getchu blocks hot-linking without a getchu referer.
        "Referer": "http://www.getchu.com/",
    }
    try:
        import requests
        r = requests.get(url, headers=headers, stream=True, timeout=15)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(4096):
                f.write(chunk)
        return dest
    except Exception as exc:
        print(f"  ! failed to download {url}: {exc}")
        return None


def save_cache(data):
    """Download every image and rewrite the structure with local paths."""
    base = os.path.join(CACHE_ROOT, str(data["vndb_id"]))
    imgs = os.path.join(base, "imgs")
    os.makedirs(imgs, exist_ok=True)

    def grab(url, name):
        if not url:
            return ""
        path = _download(url, os.path.join(imgs, name + ".jpg"))
        return os.path.relpath(path, base) if path else ""

    print("[cache] downloading images ...")
    for c in data["couplings"]:
        cid = c["image_id"]
        c["vndb_img"] = grab(c["vndb_img_url"], f"v{cid}")
        c["getchu_img1"] = grab(c["getchu_img1_url"], f"g{cid}_a")
        c["getchu_img2"] = grab(c["getchu_img2_url"], f"g{cid}_b")
    for n, e in enumerate(data["extras"], 1):
        e["getchu_img1"] = grab(e["getchu_img1_url"], f"extra{n}_a")
        e["getchu_img2"] = grab(e["getchu_img2_url"], f"extra{n}_b")

    with open(os.path.join(base, "coupling.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[cache] snapshot written to {base}/coupling.json")
    return base


def load_cache(vndb_id):
    base = os.path.join(CACHE_ROOT, str(vndb_id))
    path = os.path.join(base, "coupling.json")
    if not os.path.isfile(path):
        sys.exit(f"No cached snapshot at {path}. Run a scrape first.")
    with open(path, encoding="utf-8") as f:
        return base, json.load(f)


# ──────────────────────────────────────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────────────────────────────────────
def run_ui(base, data):
    from tkinter import (Tk, Frame, Label, Canvas, Scrollbar, Toplevel, Button,
                         VERTICAL, RIGHT, LEFT, BOTH, Y, NW, W)
    from PIL import Image, ImageTk

    OK, WARN, BAD, HEAD = "#e8f5e9", "#fff8e1", "#ffebee", "#37474f"

    root = Tk()
    root.title(f"Coupling debug  |  v{data['vndb_id']}  +  getchu {data['getchu_id']}")
    root.geometry("1000x820+0+0")

    refs = []  # keep PhotoImage refs alive

    def load_thumb(rel, box):
        if not rel:
            return None
        path = os.path.join(base, rel)
        if not os.path.isfile(path):
            return None
        try:
            img = Image.open(path)
            img.thumbnail(box, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            refs.append(photo)
            return photo, Image.open(path)
        except Exception:
            return None

    def show_full(path):
        try:
            full = Image.open(path)
        except Exception:
            return
        top = Toplevel(root)
        top.title(os.path.basename(path))
        photo = ImageTk.PhotoImage(full)
        refs.append(photo)
        Button(top, image=photo, command=top.destroy).pack()

    def img_widget(parent, rel, box):
        path = os.path.join(base, rel) if rel else ""
        loaded = load_thumb(rel, box)
        if loaded:
            photo, _ = loaded
            b = Button(parent, image=photo, bd=0, command=lambda p=path: show_full(p))
            return b
        return Label(parent, text="(no image)", width=box[0] // 8,
                     height=box[1] // 16, relief="groove", fg="#b71c1c")

    # ── scroll container ──
    canvas = Canvas(root, highlightthickness=0)
    sb = Scrollbar(root, orient=VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=sb.set)
    sb.pack(side=RIGHT, fill=Y)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    inner = Frame(canvas)
    canvas.create_window(0, 0, window=inner, anchor=NW)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    def _wheel(e):
        canvas.yview_scroll(-1 if (e.num == 4 or e.delta > 0) else 1, "units")
    for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        canvas.bind_all(seq, _wheel)

    # ── header ──
    summary = (f"VNDB chars: {data['n_vndb']}   "
               f"Getchu chars: {data['n_getchu']}   "
               f"Combined (final): {data['n_combined']}   "
               f"Doubles: {len(data['extras'])}")
    Label(inner, text=summary, bg=HEAD, fg="white", anchor=W,
          font=("Calibri", 12, "bold"), padx=10, pady=8).pack(fill="x")
    Label(inner, text="Left = VNDB portrait & name.   Right = Getchu name & image(s).   "
                      "Click an image to enlarge.",
          anchor=W, fg="#555", padx=10).pack(fill="x")

    # ── coupling rows ──
    for c in data["couplings"]:
        # Skip characters that have no image on either side — nothing to compare.
        if not (c.get("vndb_img") or c.get("getchu_img1") or c.get("getchu_img2")):
            continue

        flags = c["flags"]
        if "no-getchu-match" in flags or "matched-by-position" in flags:
            bg = BAD
        elif any(f.startswith("no-") for f in flags):
            bg = WARN
        else:
            bg = OK

        row = Frame(inner, bg=bg, bd=1, relief="solid")
        row.pack(fill="x", padx=6, pady=4)

        # left: VNDB portrait
        left = Frame(row, bg=bg)
        left.pack(side=LEFT, padx=6, pady=6)
        img_widget(left, c.get("vndb_img", ""), (150, 190)).pack()
        Label(left, text=f"#{c['image_id']}  {c['vndb_name']}", bg=bg,
              font=("Calibri", 10, "bold"), wraplength=170).pack()
        if c["vndb_romanji"]:
            Label(left, text=c["vndb_romanji"], bg=bg, fg="#555", wraplength=170).pack()

        # data column: full VNDB character data
        info = Frame(row, bg=bg)
        info.pack(side=LEFT, padx=10, pady=6, anchor="n")
        fields = [
            ("Name", c["vndb_name"]),
            ("Romanji", c["vndb_romanji"]),
            ("Gender", c.get("vndb_gender", "")),
            ("Height", c.get("vndb_height", "")),
            ("Weight", c.get("vndb_weight", "")),
            ("Measurements", c.get("vndb_measurements", "")),
            ("Age", c.get("vndb_age", "")),
            ("Cup", c.get("vndb_cup", "")),
        ]
        for label, value in fields:
            line = Frame(info, bg=bg)
            line.pack(anchor=W)
            Label(line, text=f"{label}:", bg=bg, fg="#555", width=12, anchor=W,
                  font=("Calibri", 9)).pack(side=LEFT)
            Label(line, text=value or "—", bg=bg, anchor=W, wraplength=180,
                  fg="#000" if value else "#bbb",
                  font=("Calibri", 9, "bold" if value else "normal")).pack(side=LEFT)

        # middle: status
        mid = Frame(row, bg=bg)
        mid.pack(side=LEFT, padx=10)
        arrow = {"name": "✓ name", "id": "≈ position", "none": "✗ no match"}[c["match_type"]]
        acol = {"name": "#2e7d32", "id": "#e65100", "none": "#b71c1c"}[c["match_type"]]
        Label(mid, text=arrow, bg=bg, fg=acol, font=("Calibri", 11, "bold")).pack()
        for fl in flags:
            Label(mid, text=fl, bg=bg, fg="#b71c1c").pack(anchor=W)

        # right: Getchu
        right = Frame(row, bg=bg)
        right.pack(side=LEFT, padx=6, pady=6)
        Label(right, text=c["getchu_name"] or "(no getchu character)", bg=bg,
              font=("Calibri", 10, "bold"), wraplength=260).pack(anchor=W)
        if c.get("getchu_cup"):
            Label(right, text=f"Cup: {c['getchu_cup']}", bg=bg, fg="#555",
                  font=("Calibri", 9)).pack(anchor=W)
        gimgs = Frame(right, bg=bg)
        gimgs.pack(anchor=W)
        img_widget(gimgs, c.get("getchu_img1", ""), (150, 190)).pack(side=LEFT, padx=2)
        img_widget(gimgs, c.get("getchu_img2", ""), (120, 160)).pack(side=LEFT, padx=2)

    # ── extras / doubles ──
    extras = [e for e in data["extras"] if e.get("getchu_img1") or e.get("getchu_img2")]
    if extras:
        Label(inner, text="Getchu characters with NO VNDB match — appended as extra "
                          "(duplicate) entries:", bg="#b71c1c", fg="white", anchor=W,
              font=("Calibri", 11, "bold"), padx=10, pady=6).pack(fill="x", pady=(14, 0))
        for e in extras:
            row = Frame(inner, bg=BAD, bd=1, relief="solid")
            row.pack(fill="x", padx=6, pady=4)
            Label(row, text=f"image_id {e['image_id']}", bg=BAD, fg="#b71c1c",
                  width=14).pack(side=LEFT)
            Label(row, text=e["getchu_name"], bg=BAD,
                  font=("Calibri", 10, "bold"), wraplength=260).pack(side=LEFT, padx=6)
            img_widget(row, e.get("getchu_img1", ""), (150, 190)).pack(side=LEFT, padx=2)
            img_widget(row, e.get("getchu_img2", ""), (120, 160)).pack(side=LEFT, padx=2)

    root.mainloop()


# ──────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Debug VNDB/Getchu character couplings.")
    ap.add_argument("vndb_id", help="VNDB entry id (digits)")
    ap.add_argument("getchu_id", nargs="?", help="Getchu product id (digits)")
    ap.add_argument("--from-cache", action="store_true",
                    help="render a previous snapshot without scraping")
    ap.add_argument("--no-ui", action="store_true", help="scrape + cache only")
    ap.add_argument("--vndb-html", metavar="PATH",
                    help="parse VNDB characters from this saved chars-page HTML "
                         "(default: site_data/vndb.txt if it exists)")
    ap.add_argument("--vndb-live", action="store_true",
                    help="force a live VNDB scrape, ignoring site_data/vndb.txt")
    args = ap.parse_args()

    vndb_id = "".join(ch for ch in args.vndb_id if ch.isdigit())

    if args.from_cache:
        base, data = load_cache(vndb_id)
        run_ui(base, data)
        return

    if not args.getchu_id:
        ap.error("getchu_id is required unless --from-cache is given")
    getchu_id = "".join(ch for ch in args.getchu_id if ch.isdigit())

    # Resolve the VNDB source: explicit file > default site_data/vndb.txt > live.
    vndb_html = args.vndb_html or os.path.join(CACHE_ROOT, "vndb.txt")
    if args.vndb_live or not os.path.isfile(vndb_html):
        vndb_html = None

    data = scrape(vndb_id, getchu_id, vndb_html=vndb_html)
    base = save_cache(data)

    if not args.no_ui:
        run_ui(base, data)


if __name__ == "__main__":
    main()
