"""The unattended kit's Windows shortcut (D02 T02 §10): unattended-shortcut.ps1 against a stand-in for wsl.exe.

The links are read back through WScript.Shell and their own target and arguments are run, windowless, against the
stand-in, so the command line Windows would hand wsl.exe is the one checked. Nothing here opens a window or touches
the real desktop: every link goes to a scratch folder.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
PWSH = shutil.which("pwsh")
# The stand-in for wsl.exe: it lists two distros, translates a Windows path, says whether a folder exists (all do but
# those in STUB_WSL_MISSING), and records every call; with STUB_WSL_FAIL set it fails everything.
STUB_WSL = r'''import json, os, sys
args = sys.argv[1:]
with open(os.environ["STUB_WSL_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(args) + "\n")
if os.environ.get("STUB_WSL_FAIL"):
    sys.exit(1)
if args[:2] == ["-l", "-q"]:
    print("Ubuntu\nDebian")
    sys.exit(0)
rest = args[args.index("--exec") + 1:] if "--exec" in args else []
if rest[:2] == ["wslpath", "-a"]:
    drive, _, tail = rest[2].partition(":")
    print("/mnt/" + drive.lower() + tail.replace("\\", "/"))
elif rest[:2] == ["test", "-d"]:
    sys.exit(1 if rest[2] in os.environ.get("STUB_WSL_MISSING", "").split("|") else 0)
'''


def windowless():
    """No console window of its own for any process a test starts on Windows (a console child of a parent with
    none opens one over the owner's work: 2026-11-12, Office's launcher tests flashed 5 to 10); 0 elsewhere."""
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(os.name == "nt" and PWSH, "a .lnk shortcut and WScript.Shell are Windows's (PowerShell 7)")
class ShortcutTest(unittest.TestCase):
    PROFILE = {"schema_version": 1, "name": "demo", "agent": "claude", "model": "opus", "effort": "medium",
               "prompt_file": "docs/unattended-prompt.md", "branch": "main", "skip_permissions": True, "tools": [],
               "min_disk_gb": 1, "min_ram_gb": 1, "tick_seconds": 300, "idle_minutes": 45, "stall_hours": 6,
               "preflight": [], "runners": {"agy": {"model": "gemini-4-carbon-medium", "effort": "medium"}}}

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.project = base / "My Proj's"  # a space and a quote
        for rel in ("lib/unattended.py", "campaign-icon.py", "unattended-shortcut.ps1"):
            (self.project / "scripts" / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SCRIPTS / rel, self.project / "scripts" / rel)
        (self.project / ".conclave").mkdir()
        (self.project / "docs").mkdir()
        (self.project / "docs" / "unattended-prompt.md").write_text("Run the plan.\n", encoding="utf-8")
        self.write_profile(self.PROFILE)
        icon_module = load("campaign_icon_for_shortcut", SCRIPTS / "campaign-icon.py")
        self.icon = base / "brand.png"
        self.icon.write_bytes(icon_module.write_png(256, 256, bytearray(bytes((16, 34, 26, 255)) * 256 * 256)))
        self.desk, self.icons = base / "desk", base / "icons"
        stub = base / "stub_wsl.py"
        stub.write_text(STUB_WSL, encoding="utf-8")
        self.wsl = base / "wsl.cmd"
        self.wsl.write_text(f'@"{sys.executable}" "{stub}" %*\r\n', encoding="utf-8")
        self.log = base / "wsl.log"
        self.env = {**os.environ, "STUB_WSL_LOG": str(self.log)}
        self.run = load("unattended_run_for_shortcut", SCRIPTS / "unattended-run.py")

    def write_profile(self, profile):
        (self.project / ".conclave" / "unattended.json").write_text(json.dumps(profile), encoding="utf-8")

    def shortcut(self, *args, **env):
        command = [PWSH, "-NoProfile", "-NonInteractive", "-File", str(self.project / "scripts" / "unattended-shortcut.ps1"),
                   "-ShortcutDir", str(self.desk), "-IconDir", str(self.icons),
                   "-Wsl", str(self.wsl), "-Python", sys.executable, *args]
        return subprocess.run(command, capture_output=True, text=True, timeout=180, env={**self.env, **env},
                              creationflags=windowless())

    def read_link(self, path):
        # The path goes through the environment: it holds a quote, which a PowerShell string would end at.
        script = ("$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:LINK_PATH); "
                  "@{target = $s.TargetPath; arguments = $s.Arguments; icon = $s.IconLocation; "
                  "description = $s.Description} | ConvertTo-Json -Compress")
        done = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True,
                              text=True, timeout=60, env={**os.environ, "LINK_PATH": str(path)},
                              creationflags=windowless())
        return json.loads(done.stdout)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()] if self.log.exists() \
            else []

    def links(self):
        return sorted(p.name for p in self.desk.glob("*.lnk")) if self.desk.exists() else []

    def install(self):
        done = self.shortcut("-Distro", "Ubuntu", "-Icon", str(self.icon))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done

    def activate(self, link, **env):
        """The link's own target and arguments, as Windows runs them on a double-click, windowless, Enter typed."""
        return subprocess.run(f'"{link["target"]}" {link["arguments"]}', input="\n", capture_output=True, text=True,
                              timeout=120, env={**self.env, **env}, creationflags=windowless())

    def test_one_link_per_runner_hands_wsl_the_start_command_of_that_runner(self):
        # The command itself (it starts the run, and waits for Enter when it cannot) is the Linux entry's, run in bash
        # by DesktopEntryTest; the live proof in the findings file ran it through the real wsl.exe.
        self.install()
        self.assertEqual(self.links(), ["My Proj's Carbon campaign.lnk", "My Proj's Claude campaign.lnk"])
        translated = next(c for c in self.calls() if c[3:5] == ["wslpath", "-a"])
        linux = "/mnt/" + translated[5][0].lower() + translated[5][2:].replace("\\", "/")
        self.assertTrue(linux.endswith("/My Proj's"), linux)
        for label, agent in (("Carbon", "agy"), ("Claude", "claude")):
            with self.subTest(agent):
                link = self.read_link(self.desk / f"My Proj's {label} campaign.lnk")
                self.assertEqual(Path(link["target"]).stem, "pwsh")
                icon = link["icon"].rsplit(",", 1)[0]
                self.assertRegex(Path(icon).name, rf"^campaign-{agent}-[0-9a-f]{{8}}\.ico$")
                self.assertTrue(Path(icon).is_file())
                self.log.unlink()
                ran = self.activate(link)
                self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
                self.assertEqual(self.calls(), [["-d", "Ubuntu", "--cd", linux, "--exec", "bash", "-lc",
                                                 self.run.start_command(agent)]])

    def test_a_project_in_wsl_starts_from_its_linux_path(self):
        for label, project in (("the distro's own UNC path", "\\\\wsl.localhost\\Ubuntu\\home\\x\\demo"),
                               ("the older wsl$ form", "\\\\wsl$\\Ubuntu\\home\\x\\demo"),
                               ("a Linux path", "/home/x/demo")):
            with self.subTest(label):
                shutil.rmtree(self.desk, ignore_errors=True)
                self.log.unlink(missing_ok=True)
                done = self.shortcut("-Distro", "Ubuntu", "-Icon", str(self.icon), "-Project", project)
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                self.assertFalse([c for c in self.calls() if "wslpath" in c], "a WSL path went through wslpath")
                self.log.unlink()
                ran = self.activate(self.read_link(self.desk / "demo Claude campaign.lnk"))
                self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
                self.assertEqual(self.calls()[0][:5], ["-d", "Ubuntu", "--cd", "/home/x/demo", "--exec"])

    def test_a_project_in_another_distro_is_refused(self):
        done = self.shortcut("-Distro", "Ubuntu", "-Icon", str(self.icon), "-Project",
                             "\\\\wsl.localhost\\Debian\\home\\x\\demo")
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("the project is in distro 'Debian', not 'Ubuntu'", done.stdout)
        self.assertEqual(self.links(), [])

    def test_a_failure_of_wsl_itself_is_said_and_waits_for_enter(self):
        # Round 1 of D02 T02 §10: a drive gone or a distro removed fails before bash, whose own wait cannot run.
        self.install()
        link = self.read_link(self.desk / "My Proj's Claude campaign.lnk")
        waiting = subprocess.Popen(f'"{link["target"]}" {link["arguments"]}', stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                   env={**self.env, "STUB_WSL_FAIL": "1"}, creationflags=windowless())
        self.addCleanup(lambda: waiting.poll() is None and waiting.kill())
        time.sleep(5)
        self.assertIsNone(waiting.poll(), "the window closed without waiting for Enter")
        out, _ = waiting.communicate("\n", timeout=60)  # Enter: it closes
        self.assertIn("WSL could not start the run (exit 1): the reason is above. Press Enter to close.", out)
        self.assertEqual(waiting.returncode, 0)

    def test_a_link_is_kept_when_its_replacement_cannot_be_made(self):
        self.install()
        link = self.desk / "My Proj's Claude campaign.lnk"
        before = link.read_bytes()
        broken = Path(self._tmp.name) / "not-an-image.png"
        broken.write_bytes(b"not a png")
        done = self.shortcut("-Distro", "Ubuntu", "-Icon", str(broken))
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("could not be rendered; its shortcut is left as it was", done.stdout)
        self.assertEqual(link.read_bytes(), before)
        self.assertEqual([p.name for p in self.desk.iterdir() if ".tmp" in p.name], [], "a temporary link was left")

    def test_remove_takes_this_projects_links_whatever_the_setup_now_is(self):
        self.install()
        other = self.desk / "Other Claude campaign.lnk"
        shutil.copyfile(self.desk / "My Proj's Claude campaign.lnk", other)
        subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-Command",
                        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:LINK_PATH); "
                        "$s.Description = 'conclave-unattended: D:\\elsewhere'; $s.Save()"],
                       capture_output=True, timeout=60, env={**os.environ, "LINK_PATH": str(other)},
                       creationflags=windowless())
        (self.desk / "notes.txt").write_text("mine\n", encoding="utf-8")
        another = self.icons / "campaign-claude-deadbeef.ico"  # another project's icon in a shared icon folder
        another.write_bytes(b"icon")
        self.write_profile({**self.PROFILE, "runners": {}})  # the profile dropped a runner
        self.icon.unlink()  # the icon is gone
        done = self.shortcut("-Remove", STUB_WSL_FAIL="1")  # and WSL answers nothing
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.links(), ["Other Claude campaign.lnk"])
        self.assertTrue((self.desk / "notes.txt").exists())
        self.assertEqual(list(self.icons.glob("campaign-*.ico")), [another])

    def test_what_cannot_make_a_working_link_is_refused_before_anything_is_written(self):
        cases = {"a distro WSL does not list": (["-Distro", "Arch", "-Icon", str(self.icon)], {}, "no distro 'Arch'"),
                 "a project WSL does not have": (["-Distro", "Ubuntu", "-Icon", str(self.icon)],
                                                 {"STUB_WSL_MISSING": "*"}, "does not exist in 'Ubuntu'"),
                 "no icon": (["-Distro", "Ubuntu"], {}, "-Icon is not a file"),
                 "a profile the run would refuse": (["-Distro", "Ubuntu", "-Icon", str(self.icon)], {},
                                                    "the run profile cannot be read")}
        for label, (args, env, said) in cases.items():
            with self.subTest(label):
                if label == "a profile the run would refuse":
                    self.write_profile({**self.PROFILE, "effort": "extreme"})
                if label == "a project WSL does not have":
                    env = {"STUB_WSL_MISSING": "|".join(self._linux_candidates())}
                done = self.shortcut(*args, **env)
                self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
                self.assertIn(said, done.stdout)
                self.assertEqual(self.links(), [])

    def _linux_candidates(self):
        """The WSL path the stand-in gives this project, for the long and the short spelling of the temp folder."""
        paths = {str(self.project), os.path.realpath(self.project)}
        return ["/mnt/" + p[0].lower() + p[2:].replace("\\", "/") for p in paths]


if __name__ == "__main__":
    unittest.main()
