---
name: unattended-run
description: Start, stop, watch or debug an unattended run of this project's plan (scripts/unattended-run.py in tmux, its heartbeat, its shortcuts). Use when the operator asks to start, stop, watch, attach to or debug an unattended run, a run looks stuck or stalled, a shortcut fails, or the stall notice build/unattended-needs-operator.md appears.
---

# Unattended run

The operator's page is `docs/unattended-run.md`: how to set the profile, start a run (a shortcut, or `python3 scripts/unattended-run.py start` with `--agent` or `--ships`), watch it (`status`, `attach --watch`), stop it, remove its shortcuts, what the heartbeat does and what each message means. Read it before acting, and give the operator its commands.

## Inside a run

When `CONCLAVE_UNATTENDED_RUN=1` is set you are the run, working the plan with `process-plan`. Then:

- Never stop the run, and never start another: only the operator starts or stops a run.
- Never ask the operator a question: decide, record the decision in the run file, and carry on.
- Keep the run guard as `process-plan` says; this agent's Stop hook is `.agents/hooks.json`, and it holds the turn while the run is open.

## Outside a run

- To start, stop or watch, run the page's commands; `stop` refuses inside a run.
- To debug, read `status` first, then the run file named by the guard (`build/claude-campaign-guard.json`), the heartbeat's state (`build/unattended-heartbeat.json`) and the health file (`build/unattended-health.json`); the page's last section says what each message means and what to do.
- A run never restarts itself: after a crash or a reboot it stays stopped until the operator starts it again.