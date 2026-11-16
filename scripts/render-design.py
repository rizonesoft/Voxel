#!/usr/bin/env python3
"""Render every screen of Voxel's three interface prototypes, and write each screen's contract.

    python scripts/render-design.py                 every screen of every interface
    python scripts/render-design.py console mpr     one screen of one interface

For each screen of design/prototype/<interface>.html this writes:

    design/screens/<interface>/<screen>.png     the picture the built app is compared against
    design/contract/<interface>/<screen>.json   every control and every text on the screen: label, shortcut, state,
                                                 rectangle, colours, font

Both are the reference for the 1:1 implementation (design/SPEC.md). Needs Microsoft Edge, and a network connection
for the fonts.
"""
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from lib.edge_shot import edge, shoot_url

ROOT = Path(__file__).resolve().parent.parent
PROTOTYPE = ROOT / "design" / "prototype"
SCREENS_DIR = ROOT / "design" / "screens"
CONTRACT_DIR = ROOT / "design" / "contract"
INTERFACES = ("workstation", "lightbox", "console")
SCREENS = ("welcome", "empty", "xray", "loading", "stack", "mpr", "view3d", "layout", "tags", "export", "only2d",
           "refusal", "menu", "settings", "about")
WIDTH, HEIGHT = 1440, 900


def contract(url):
    """The contract a prototype page writes into its own document when opened with contract=1."""
    with tempfile.TemporaryDirectory() as work:
        command = [str(edge()), "--headless=new", "--disable-gpu", "--no-first-run", "--allow-file-access-from-files",
                   f"--user-data-dir={Path(work) / 'profile'}", f"--window-size={WIDTH},{HEIGHT}",
                   "--virtual-time-budget=8000", "--dump-dom", url + "&contract=1"]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            dom, _ = process.communicate(timeout=90)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)], capture_output=True, check=False)
            sys.exit(f"render-design: Edge timed out reading {url}")
    found = re.search(r'<pre id="voxel-contract">(.*?)</pre>', dom.decode("utf-8", "replace"), re.S)
    if found is None:
        sys.exit(f"render-design: the page wrote no contract: {url}")
    return json.loads(html.unescape(found[1]))


def main(argv):
    interfaces = [argv[0]] if argv else INTERFACES
    screens = [argv[1]] if len(argv) > 1 else SCREENS
    for interface in interfaces:
        page = PROTOTYPE / f"{interface}.html"
        if interface not in INTERFACES or not page.is_file():
            sys.exit(f"render-design: no such interface: {interface}")
        for screen in screens:
            if screen not in SCREENS:
                sys.exit(f"render-design: no such screen: {screen}")
            url = f"{page.as_uri()}?screen={screen}"
            picture = SCREENS_DIR / interface / f"{screen}.png"
            shoot_url(url, picture, WIDTH, HEIGHT)
            data = {"interface": interface, "screen": screen, **contract(url)}
            target = CONTRACT_DIR / interface / f"{screen}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            print(f"{interface}/{screen}: {len(data['controls'])} controls, {len(data['texts'])} texts")


if __name__ == "__main__":
    main(sys.argv[1:])
