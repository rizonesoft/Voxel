"""The unattended kit's operator page, its skill in three agents and its README (D02 T02 §11)."""
from __future__ import annotations

import contextlib
import importlib.util
import io
from pathlib import Path
import re
import shlex
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent  # the kit's templates, or an installed project
DOC = ROOT / "docs" / "unattended-run.md"
README = ROOT.parent / "README.md" if ROOT.name == "templates" else None
INVOKE = re.compile(r"python3 scripts/unattended-run\.py((?: [^`\n]+)?)")
# Every operation the page must show an example of, as the command and the options it names.
REQUIRED = {("start",), ("start", "--agent"), ("start", "--ships"), ("status",), ("attach",), ("attach", "--watch"),
            ("stop",), ("shortcut",), ("shortcut", "--remove")}
SOURCES = ("unattended-run.py", "unattended-preflight.py", "unattended-shortcut.ps1")
HOOKS = {".claude": ".claude/settings.json", ".agents": ".agents/hooks.json", ".codex": ".codex/hooks.json"}


def load_run():
    spec = importlib.util.spec_from_file_location("unattended_run_for_document", SCRIPTS / "unattended-run.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_document(text: str, parser) -> list[str]:
    """What is wrong with the page's invocations: one the launcher's own parser refuses, or an operation with no
    example. A `<...>` placeholder stands for a value (`<runner>` for an agent)."""
    problems, seen = [], set()
    for match in INVOKE.finditer(text):
        words = [("claude" if w == "<runner>" else "x" if w.startswith("<") else w)
                 for w in shlex.split(match.group(1))]
        try:
            with contextlib.redirect_stderr(io.StringIO()):  # argparse says why on stderr; the problem list says it
                parser.parse_args(words)
        except SystemExit:
            problems.append(f"the launcher refuses: python3 scripts/unattended-run.py{match.group(1)}")
            continue
        if words:
            seen.add((words[0],))
            seen.update((words[0], w) for w in words[1:] if w.startswith("--"))
    problems += [f"no example of {' '.join(op)}" for op in sorted(REQUIRED - seen)]
    return problems


def quoted_states(text: str) -> list[str]:
    """The first quoted message of each bullet under the page's 'What you may see' heading."""
    section = text.split("## What you may see", 1)[1].split("\n## ", 1)[0]
    return [found.group(1) for line in section.splitlines() if (found := re.match(r"- `([^`]+)`", line))]


class DocumentTest(unittest.TestCase):
    def setUp(self):
        self.text = DOC.read_text(encoding="utf-8")
        self.parser = load_run().build_parser()

    def test_every_invocation_is_one_the_launcher_takes_and_every_operation_has_one(self):
        self.assertEqual(check_document(self.text, self.parser), [])

    def test_the_check_refuses_a_bad_page(self):
        bad = {"a command the launcher lacks": self.text + "\n`python3 scripts/unattended-run.py frobnicate`\n",
               "a misplaced option": self.text + "\n`python3 scripts/unattended-run.py status --ships 1`\n",
               "a missing example": self.text.replace("attach --watch", "attach")}
        for label, text in bad.items():
            with self.subTest(label):
                self.assertTrue(check_document(text, self.parser), label)

    def test_every_state_the_page_explains_is_one_the_code_says(self):
        states = quoted_states(self.text)
        self.assertGreaterEqual(len(states), 9)
        code = "\n".join((SCRIPTS / name).read_text(encoding="utf-8") for name in SOURCES)
        for state in states:
            with self.subTest(state):
                self.assertIn(state, code)

    def test_the_page_states_the_shortcuts_exact_invocation(self):
        # Filed from the completion review of D02 T02 §10.
        self.assertIn("runs `wsl.exe -d <distro> --cd <project in WSL> --exec bash -lc <start command>`", self.text)


class SkillTest(unittest.TestCase):
    def test_each_agents_copy_carries_the_triggers_the_rules_and_its_own_hook(self):
        for folder, hook in HOOKS.items():
            with self.subTest(folder):
                text = (ROOT / folder / "skills" / "unattended-run" / "SKILL.md").read_text(encoding="utf-8")
                front, body = text.split("\n---\n", 1)
                self.assertIn("name: unattended-run", front)
                description = re.search(r"^description: (.+)$", front, re.M).group(1)
                for trigger in ("start", "stop", "watch", "debug"):
                    self.assertIn(trigger, description)
                for rule in ("Never stop the run, and never start another", "Never ask the operator a question"):
                    self.assertIn(rule, body)
                self.assertIn("`docs/unattended-run.md`", body)
                self.assertTrue(DOC.is_file(), "the page the skill names is not installed")
                self.assertIn(f"`{hook}`", body)
                for other in set(HOOKS.values()) - {hook}:
                    self.assertNotIn(other, body)
        self.assertTrue((ROOT / ".codex/skills/unattended-run/agents/openai.yaml").is_file())


@unittest.skipUnless(README is not None, "the README is the kit's own, beside its templates")
class ReadmeTest(unittest.TestCase):
    def test_the_file_table_names_exactly_the_kits_files(self):
        table = re.findall(r"^\| `([^`]+)` \|", README.read_text(encoding="utf-8"), re.M)
        files = sorted(rel for p in ROOT.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                       and not (rel := p.relative_to(ROOT).as_posix()).startswith("scripts/tests/"))
        self.assertEqual(sorted(t for t in table if t != "scripts/tests/"), files)
        self.assertIn("scripts/tests/", table)


if __name__ == "__main__":
    unittest.main()
