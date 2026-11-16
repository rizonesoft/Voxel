# Running the Voxel campaign

A campaign is one agent session that works through `todo/implementation-plan.md` with the `process-plan` skill, with nobody at the keyboard. This page is for the operator.

## Start it

Double-click a desktop shortcut:

| Shortcut | Runner |
| -------- | ------ |
| **Voxel Claude campaign** | Claude Code on the latest Opus, medium effort |
| **Voxel Carbon campaign** | Google Antigravity on Orchestrator (Carbon) |

Each carries Voxel's icon with its runner's badge. They were written on 2026-11-17; `pwsh scripts/start-run.ps1 -InstallShortcut` writes them again on another PC or after the checkout moves. Without a shortcut: `pwsh scripts/start-run.ps1` (Claude) or `pwsh scripts/start-run.ps1 -Runner agy` (Carbon). `-DryRun` prints what would run and changes nothing.

Start one runner at a time. Two sessions must never write to one tree: when a run guard from an earlier session is held, the launcher names that session and waits for Enter before the new one may take the run over.

## Stop it

Close its window. A run starts only when you start it, and a closed window, a crash or a reboot ends it. Nothing restarts it: there is no scheduled task and no watchdog.

## Why it runs on Windows, not in WSL

Voxel is a Windows program. Every build section needs the MSVC toolchain, DirectX 12 and a desktop session (`windows-host`, `display-session`), so the campaign runs in a Windows window through `scripts/start-run.ps1`. The unattended kit's WSL and tmux route (`scripts/unattended-run.py`, `docs/unattended-run.md`) is installed with the kit but cannot build Voxel, so it is not the way to run this project.

## What the run will leave for you

The run never asks a question. It parks these, and says so in its run file:

| Section | Why it waits |
| ------- | ------------ |
| D06 T01 §1 | Your decision: the "review only" label, or certification for diagnostic use |
| D06 T01 §4 | The About window shows that label, so it waits for §1 |
| D02 T02 §10 | The 45-screen contract pass includes the About screen |
| D06 T01 §5 | The acceptance pass on your own real studies, with you present |

To unblock the first three, answer D06 T01 §1: put your decision and the exact label sentence in `docs/decisions/2026-label.md` and remove `owner-decision` from that section's Needs line. The designs already show "For review only. Not for diagnostic use."

## What is ready, checked 2026-11-17

| Check | Result |
| ----- | ------ |
| `python scripts/todo-graph.py validate` | valid, 49 sections |
| `python scripts/todo-graph.py plan --check` | plan current |
| `python scripts/todo-graph.py detect` | `windows-host` and `display-session` met |
| First ready section | D00 T01 §1, which installs Rust with `winget` (no administrator rights) |
| MSVC build tools | installed (Visual Studio 2022 Build Tools) |
| Reviewer | Codex, pinned in `.conclave/reviewers.toml`, found by the kit doctor |
| `claude`, `python`, `git`, `gh`, `winget` | on `PATH` |
| Working tree | clean, pushed to `origin/main` |

Rust itself is not installed yet: the first section installs it, and that is by design.

## When something looks wrong

- `python scripts/campaign_guard.py --self-test` checks the run guard's hooks.
- `python scripts/todo-graph.py query ready --have auto` lists what the run can work on now, and `query blocked` what waits and on what.
- `python D:/Conclave-SDK/forge.py doctor D:/Voxel` checks the kits (from the Conclave-SDK checkout).
