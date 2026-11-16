#!/usr/bin/env python3
"""Check that the design reference is complete: every screen of every interface has a picture and a contract.

    python scripts/check-design.py

Exit 1 names each missing or malformed file. It reads only; scripts/render-design.py is what writes them.
"""
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTERFACES = ("workstation", "lightbox", "console")
SCREENS = ("welcome", "empty", "xray", "loading", "stack", "mpr", "view3d", "layout", "tags", "export", "only2d",
           "refusal", "menu", "settings", "about")


def png_size(path):
    with path.open("rb") as handle:
        head = handle.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def main():
    faults = []
    tokens = ROOT / "design" / "tokens.json"
    try:
        json.loads(tokens.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        faults.append(f"design/tokens.json: {exc}")
    for interface in INTERFACES:
        if not (ROOT / "design" / "prototype" / f"{interface}.html").is_file():
            faults.append(f"design/prototype/{interface}.html is missing")
        for screen in SCREENS:
            picture = ROOT / "design" / "screens" / interface / f"{screen}.png"
            contract = ROOT / "design" / "contract" / interface / f"{screen}.json"
            if not picture.is_file():
                faults.append(f"{picture.relative_to(ROOT).as_posix()} is missing")
            elif png_size(picture) != (1440, 900):
                faults.append(f"{picture.relative_to(ROOT).as_posix()} is not a 1440 by 900 PNG")
            try:
                data = json.loads(contract.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                faults.append(f"{contract.relative_to(ROOT).as_posix()}: {exc}")
                continue
            if data.get("interface") != interface or data.get("screen") != screen:
                faults.append(f"{contract.relative_to(ROOT).as_posix()} names another screen")
            if not data.get("controls") or not data.get("texts"):
                faults.append(f"{contract.relative_to(ROOT).as_posix()} lists no controls or no texts")
    if faults:
        print("\n".join(faults))
        return 1
    print(f"design reference complete: {len(INTERFACES) * len(SCREENS)} screens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
