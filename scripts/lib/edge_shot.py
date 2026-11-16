"""Render a page to a PNG with headless Microsoft Edge. Used by render-brand.py and render-design.py."""
import subprocess
import sys
import tempfile
from pathlib import Path

EDGE_PATHS = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
)


def edge():
    for path in EDGE_PATHS:
        if path.is_file():
            return path
    sys.exit("edge_shot: Microsoft Edge was not found")


def shoot_url(url, target, width, height, scale=1, transparent=False):
    """Screenshot a URL at width by height CSS pixels. The whole process tree is stopped on a timeout."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as work:
        command = [
            str(edge()), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--allow-file-access-from-files", f"--user-data-dir={Path(work) / 'profile'}",
            f"--window-size={width},{height}", f"--force-device-scale-factor={scale}",
            "--virtual-time-budget=8000", f"--screenshot={target}",
        ]
        if transparent:
            command.append("--default-background-color=00000000")
        command.append(url)
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            process.wait(timeout=90)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)], capture_output=True, check=False)
            sys.exit(f"edge_shot: Edge timed out rendering {target.name}")
    if not target.is_file():
        sys.exit(f"edge_shot: Edge wrote no image for {target.name}")


def shoot_html(html, target, width, height, scale=1, transparent=False):
    """Screenshot an HTML document given as text."""
    with tempfile.TemporaryDirectory() as work:
        page = Path(work) / "page.html"
        page.write_text(html, encoding="utf-8")
        shoot_url(page.as_uri(), target, width, height, scale, transparent)
