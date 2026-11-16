# Unattended run

An unattended run is one agent session working through `todo/implementation-plan.md` with `process-plan`, in a tmux session that outlives the terminal that started it. This page is for the operator who starts, watches and stops it. The run lives in tmux, so it runs on Linux and in WSL; on Windows a desktop shortcut starts it in WSL.

A run never restarts itself. It starts only when you start it, and `stop`, a crash or a reboot ends it. Nothing in the kit resumes a run at boot, at logon or on a timer, the automations kit refuses a scheduled task that starts one, and `start` refuses to run under a scheduled task.

## Set it up

1. Install the kit after the todo kit: `python forge.py kit <project> unattended`.
2. Set `name`, `model` and `effort` in `.conclave/unattended.json`; the template leaves them `null`, and the loader refuses the profile until they are set, except Antigravity Orchestrator models (`gemini-pro-orchestrator` and `gemini-pro-orchestrator-*`), which manage effort internally, reject `--effort`, and require `"effort": null` (setting any non-null effort is refused). To start the run on another agent as well, add it under `runners` with its own `model` and `effort`, for example `"runners": {"agy": {"model": "gemini-4-carbon-medium", "effort": "medium"}}` or `"runners": {"agy": {"model": "gemini-pro-orchestrator", "effort": null}}` (the launcher omits `--effort` for Orchestrator models on both fresh starts and `--conversation` resumes).
3. Check the machine: `python forge.py doctor <project> unattended`. It reports each kit file, the todo kit, tmux and the `unattended-run` skill in each agent's folder.

## Start it

From a terminal in the project, in WSL or on Linux:

```bash
python3 scripts/unattended-run.py start
python3 scripts/unattended-run.py start --agent agy
python3 scripts/unattended-run.py start --ships 3
```

`--agent` starts the run on one of the profile's runners, with that runner's model and effort; the preflight then checks that agent's own CLI, version and Stop hook. `--ships N` ends the run once it has shipped N sections; the heartbeat enforces it, so a bounded run needs its heartbeat, and a resume keeps the run's own bound.

`start` runs the preflight first (one PASS or FAIL line per precondition) and starts nothing on a FAIL. When the run's tmux session is gone but its marker is still there (a crash), `start` resumes that agent session; after a `stop` it starts a fresh one.

### Shortcuts

On Windows, `pwsh scripts/unattended-shortcut.ps1 -Distro Ubuntu -Icon <the project's icon>` puts a `<Project> <Runner> campaign` shortcut on the desktop for each runner the profile names (`-ShortcutDir` puts them elsewhere). Each runs PowerShell, which runs `wsl.exe -d <distro> --cd <project in WSL> --exec bash -lc <start command>`, the start command being `python3 scripts/unattended-run.py start --agent <runner>`. `--exec` keeps the login shell from parsing the command again. When the run does not start, the window says so and waits for Enter, and it does the same when WSL itself fails (a drive gone, a distro removed).

On Linux, the launcher writes a desktop entry per runner:

```bash
python3 scripts/unattended-run.py shortcut
python3 scripts/unattended-run.py shortcut --agent agy
```

To remove them: `pwsh scripts/unattended-shortcut.ps1 -Remove` (with the same `-ShortcutDir` if you used one) and

```bash
python3 scripts/unattended-run.py shortcut --remove
python3 scripts/unattended-run.py shortcut --remove --dir ~/Desktop
```

Both find the project's own shortcuts by a mark they carry, so removal works whatever the profile, the icon or the distro now are, and leaves other projects' shortcuts alone.

## Watch it

```bash
python3 scripts/unattended-run.py status
python3 scripts/unattended-run.py attach --watch
```

`status` says whether the run and its heartbeat are live, the run's session and start, its guard, the heartbeat's state, the health file (`build/unattended-health.json`: alive, sections shipped, the ship limit, the last ship and the hours since it) and any stall notice. `attach --watch` attaches read-only. Detach with tmux's prefix and `d` (Ctrl-b, then d): the run goes on.

## Attach and stop it

```bash
python3 scripts/unattended-run.py attach
python3 scripts/unattended-run.py stop
```

`attach` gives you the run's terminal; while you are attached with a client that can type, the heartbeat does not nudge it. `stop` ends the run's guard, its tmux sessions and every process it started, records the end in the health file, and removes the run's marker, so the next `start` starts fresh. A run cannot stop itself: `stop` from inside the run is refused.

## What the heartbeat does

The heartbeat runs in its own tmux session beside the run. Every `tick_seconds` it:

- nudges the run when its window has shown nothing for `idle_minutes` (never while you are attached and can type);
- counts the sections the run has shipped (rows turned `[x]` in each TODO file's Implementation Order table, commit by commit) and writes the health file;
- ends a bounded run once it has shipped its `--ships` sections;
- writes the stall notice `build/unattended-needs-operator.md` when nothing has shipped for `stall_hours`, at most once per `stall_hours`, and nudges the run to find out why;
- records a run whose session has died as ended and stops everything it started. It never restarts it.

## What you may see, and what to do

- `unknown (tmux could not be asked)`: `status` could not reach tmux. Check `tmux ls` in the same WSL distro; nothing about the run is assumed.
- `health: none`: the heartbeat has not written its health file yet (the run started moments ago, or with `--no-heartbeat`). Look again after a tick. A health file whose `updated` is old means one of two things: the heartbeat is not running (`status` shows it `stopped`: start it again, alone, in its own tmux session with `tmux new-session -d -s <name>-heartbeat python3 scripts/unattended-run.py heartbeat`; it supervises the live run and starts nothing), or it is running but cannot write (`status` shows it `live`): its own tmux session says why (`tmux attach -r -t <name>-heartbeat`), most often a full disk (`df -h .`); it keeps supervising and writes again once it can.
- `the preflight refused the run (FAIL lines above); nothing was started`: fix each FAIL line and start again.
- `start refused: it came from the scheduled task`: a scheduled task tried to start the run. Start it yourself, and remove the task.
- `the run's guard was not ended`: the run is stopped but its guard is not; run `stop` again.
- `records it once the disk takes it`: `stop` could not write the end (a full or failing disk); the heartbeat stays and writes it when it can. Free the disk; nothing else is needed.
- `Nothing has shipped for`: the stall notice. Read the run file, `git log` and the gate logs, then attach or stop the run.
- `The run did not start: the reason is above. Press Enter to close.`: a shortcut's start failed; the reason is the lines above it.
- `WSL could not start the run`: WSL itself failed before the run's command (the project's drive is gone, or the distro); fix WSL and try the shortcut again.
