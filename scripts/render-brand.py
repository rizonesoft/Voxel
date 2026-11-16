#!/usr/bin/env python3
"""Render Voxel's brand images from the SVG sources in assets/brand.

    python scripts/render-brand.py

Writes, into assets/brand: the lockups (voxel-lockup.svg, voxel-lockup-light.svg), the icon PNGs, voxel.ico, the
social preview (1280 by 640) and the README banners (dark and light, 1280 by 320 at 2x). The SVG files voxel-mark.svg,
voxel-icon.svg, voxel-icon-small.svg, voxel-wordmark.svg and voxel-wordmark-light.svg are the hand-drawn sources and
are never written here.

Needs Microsoft Edge (the renderer) and Pillow. The social preview and the banners set their text in Archivo, IBM Plex Sans
and IBM Plex Mono from Google Fonts, so they need a network connection; the icon renders do not.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "assets" / "brand"
EDGE_PATHS = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
)
FONTS = ("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@88,600;88,700"
         "&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600&display=swap")
HEAD = "font-family:'Archivo','IBM Plex Sans',system-ui,sans-serif;font-stretch:88%;font-weight:700"
MONO = "font-family:'IBM Plex Mono',ui-monospace,monospace"
TAGLINE = "A lightweight DICOM viewer for <span style=\"white-space:nowrap\">X-rays</span> and MRIs."
ICO_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
SMALL_BELOW = 48  # frames under this size use the heavier small icon


def edge():
    for path in EDGE_PATHS:
        if path.is_file():
            return path
    sys.exit("render-brand: Microsoft Edge was not found")


def inner(svg_text):
    """The content of an SVG file's root element, and its viewBox."""
    box = re.search(r'viewBox="([^"]+)"', svg_text)
    body = re.search(r"<svg[^>]*>(.*)</svg>", svg_text, re.S)
    if box is None or body is None:
        sys.exit("render-brand: an SVG source has no viewBox or no root element")
    return body[1], box[1]


def screenshot(html, target, width, height, scale=1, transparent=False):
    """Render an HTML document to a PNG with headless Edge; the whole process tree is stopped on a timeout."""
    with tempfile.TemporaryDirectory() as work:
        page = Path(work) / "page.html"
        page.write_text(html, encoding="utf-8")
        command = [
            str(edge()), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            f"--user-data-dir={Path(work) / 'profile'}", f"--window-size={width},{height}",
            f"--force-device-scale-factor={scale}", "--virtual-time-budget=8000", f"--screenshot={target}",
        ]
        if transparent:
            command.append("--default-background-color=00000000")
        command.append(page.as_uri())
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            process.wait(timeout=90)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)], capture_output=True, check=False)
            sys.exit(f"render-brand: Edge timed out rendering {target.name}")
    if not target.is_file():
        sys.exit(f"render-brand: Edge wrote no image for {target.name}")


def page(body, background, extra_head=""):
    return (f'<!doctype html><html><head><meta charset="utf-8">{extra_head}<style>html,body{{margin:0;'
            f"background:{background};overflow:hidden}}</style></head><body>{body}</body></html>")


def write_lockups(mark, wordmark, wordmark_light):
    mark_body, _ = inner(mark)
    for name, source in (("voxel-lockup.svg", wordmark), ("voxel-lockup-light.svg", wordmark_light)):
        word_body, _ = inner(source)
        (BRAND / name).write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 740 160" role="img" aria-label="Voxel">\n'
            f'  <g transform="translate(-35.2 -35.2) scale(0.9)">{mark_body}</g>\n'
            f'  <g transform="translate(200 30)">{word_body}</g>\n'
            "</svg>\n", encoding="utf-8", newline="\n")


def render_icons(icon, icon_small):
    large, small = BRAND / "voxel-icon-1024.png", BRAND / "voxel-icon-small-1024.png"
    for svg, target in ((icon, large), (icon_small, small)):
        body = f'<div style="width:1024px;height:1024px">{svg.replace("<svg ", "<svg width=1024 height=1024 ", 1)}</div>'
        screenshot(page(body, "transparent"), target, 1024, 1024, transparent=True)
    detailed, heavy = Image.open(large).convert("RGBA"), Image.open(small).convert("RGBA")
    for size in (64, 192, 512):
        detailed.resize((size, size), Image.Resampling.LANCZOS).save(BRAND / f"voxel-icon-{size}.png", optimize=True)
    frames = [(heavy if size < SMALL_BELOW else detailed).resize((size, size), Image.Resampling.LANCZOS) for size in ICO_SIZES]
    frames[-1].save(BRAND / "voxel.ico", format="ICO", sizes=[(s, s) for s in ICO_SIZES],
                    append_images=frames[:-1])
    small.unlink()


def render_social(mark, wordmark):
    mark_body, mark_box = inner(mark)
    word_body, word_box = inner(wordmark)
    body = f"""
<div style="width:1280px;height:640px;position:relative;overflow:hidden;background:#131a22;color:#edf0f4;
font-family:'IBM Plex Sans',system-ui,sans-serif">
<svg viewBox="{mark_box}" width="470" style="position:absolute;right:96px;top:48px">{mark_body}</svg>
<div style="position:absolute;left:88px;top:0;height:640px;width:600px;display:flex;flex-direction:column;
justify-content:center;gap:36px">
<svg viewBox="{word_box}" width="470">{word_body}</svg>
<div style="{HEAD};font-size:40px;line-height:46px;letter-spacing:-0.01em">{TAGLINE}</div>
<div style="{MONO};font-size:18px;color:#4bcefd">2D · MPR · 3D · one small Windows app</div>
</div></div>"""
    screenshot(page(body, "#131a22", f'<link rel="stylesheet" href="{FONTS}">'), BRAND / "social-preview.png",
               1280, 640)


def render_banner(icon, wordmark, name, ground, ink, accent):
    word_body, word_box = inner(wordmark)
    body = f"""
<div style="width:1280px;height:320px;box-sizing:border-box;padding:0 72px;display:flex;align-items:center;
justify-content:space-between;gap:48px;background:{ground};color:{ink};font-family:'IBM Plex Sans',system-ui,sans-serif">
<div style="display:flex;align-items:center;gap:32px">
{icon.replace("<svg ", "<svg width=136 height=136 ", 1)}
<svg viewBox="{word_box}" width="380">{word_body}</svg></div>
<div style="display:flex;flex-direction:column;gap:14px;max-width:500px">
<div style="{HEAD};font-size:29px;line-height:35px">{TAGLINE}</div>
<div style="{MONO};font-size:16px;color:{accent}">2D · MPR · 3D · Windows</div>
</div></div>"""
    screenshot(page(body, ground, f'<link rel="stylesheet" href="{FONTS}">'), BRAND / name, 1280, 320, scale=2)


def main():
    read = lambda name: (BRAND / name).read_text(encoding="utf-8")
    mark, icon, icon_small = read("voxel-mark.svg"), read("voxel-icon.svg"), read("voxel-icon-small.svg")
    wordmark, wordmark_light = read("voxel-wordmark.svg"), read("voxel-wordmark-light.svg")
    write_lockups(mark, wordmark, wordmark_light)
    render_icons(icon, icon_small)
    render_social(mark, wordmark)
    render_banner(icon, wordmark, "banner-dark.png", "#131a22", "#edf0f4", "#4bcefd")
    render_banner(icon, wordmark_light, "banner-light.png", "#f2f5f8", "#151e27", "#006ba9")
    for path in sorted(BRAND.iterdir()):
        print(f"{path.stat().st_size:>9}  {path.name}")


if __name__ == "__main__":
    main()
