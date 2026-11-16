# Starts Voxel's campaign run on Windows: an interactive agent session in this checkout, in this window, with every
# permission prompt off and its goal set. The run starts only when the operator starts it, and ends when its window
# closes, it crashes or the machine restarts: nothing here, or anywhere in this repository, starts or resumes it on its own.
#
# Voxel is a Windows program: every build section needs the MSVC toolchain, DirectX 12 and a desktop session, so the
# campaign runs here, in a Windows window. The unattended kit's WSL and tmux route (scripts/unattended-run.py) cannot
# build it and is not used for this project; see docs/campaign.md.
#
#   pwsh scripts/start-run.ps1                    start the run in Claude Code (the latest Opus)
#   pwsh scripts/start-run.ps1 -Runner agy        start it in Antigravity on Orchestrator (Carbon) (the Carbon runner)
#   pwsh scripts/start-run.ps1 -InstallShortcut   put "Voxel Claude campaign" and "Voxel Carbon campaign"
#                                                 on the desktop, each running the line above for its runner
#   pwsh scripts/start-run.ps1 -DryRun            print what would run or be written, and change nothing
#   pwsh scripts/start-run.ps1 -Model sonnet      start on another model
#   pwsh scripts/start-run.ps1 -Effort high       start the Claude runner at another effort (default medium)
#   pwsh scripts/start-run.ps1 -TakeOver          take over a held run guard without being asked
#
# Each shortcut's icon is Voxel's icon (assets/brand/voxel.ico) with its runner's badge in the corner, as the owner's
# other campaign launchers carry it: rendered on this machine into %LOCALAPPDATA%\Voxel-campaign by the unattended
# kit's stdlib renderer (scripts/campaign-icon.py), never into the repository.
#
# The goal is a Claude Code /goal, which is checked after every turn: the plan finished through the process-plan
# skill. That skill starts the run guard itself (scripts/campaign_guard.py and a heartbeat inside the session), so this
# file starts no guard.
#
# Two sessions must never write to one tree. When a guard from an earlier session is held, this file names that
# session and waits for Enter (or takes -TakeOver as the answer), and only then is the new session told it may take
# the run over from that one session. When no guard is held, the new session is told the opposite: a guard it then
# finds belongs to another live run, and it must start nothing. So two launches at once cannot both take the run.
#
# The Claude runner's model is the alias `opus`, which Claude Code resolves to the newest Opus, so the shortcut never
# needs editing when a new one ships, and its effort is medium, passed as --effort so the user's own interactive default
# (effortLevel in settings.json) never decides a campaign's cost. The Carbon runner's is gemini-pro-orchestrator
# (Orchestrator (Carbon)), which manages effort internally across its Carbon planning and Hydrogen execution turns.
#
# The session signs in with the long-lived token (`claude setup-token`, valid one year) kept in the user variable
# CLAUDE_CODE_OAUTH_TOKEN. A window opened before the token was stored does not have it yet, so it is read from the
# user's own variables here. When none is stored, the session uses the claude.ai sign-in and the start goes ahead.
# The token is never printed, and this file never creates or changes one.
#
# Adapted on 2026-11-17 from Conclave-SDK's own scripts/start-run.ps1, which is not part of a kit.
param(
  [ValidateSet('claude', 'agy')]
  [string]$Runner = 'claude',
  [switch]$InstallShortcut,
  [switch]$DryRun,
  [switch]$TakeOver,
  [string]$ShortcutDir = [Environment]::GetFolderPath('Desktop'),
  [string]$Model = '',
  [ValidateSet('low', 'medium', 'high', 'xhigh', 'max')]
  [string]$Effort = 'medium',
  [string]$IconDir = (Join-Path $env:LOCALAPPDATA 'Voxel-campaign'),
  [string]$UserEnvKey = 'HKCU:\Environment',
  [string]$Goal = '',
  # The three below exist for the tests: stand-ins for claude and agy, and a guard file outside the real build folder.
  [string]$ClaudePath = '',
  [string]$AgyPath = '',
  [string]$GuardFile = ''
)
$ErrorActionPreference = 'Stop'
# The automations kit marks every process a scheduled task runs: a run starts only when its operator starts it.
if ($env:CONCLAVE_AUTOMATION -and -not $InstallShortcut) {
  "start refused: it came from the scheduled task $env:CONCLAVE_AUTOMATION, and a run starts only when its operator starts it"
  exit 2
}
$repo = Split-Path $PSScriptRoot
$tokenName = 'CLAUDE_CODE_OAUTH_TOKEN'
if (-not $Model) { $Model = if ($Runner -eq 'agy') { 'gemini-pro-orchestrator' } else { 'opus' } }
if (-not $GuardFile) { $GuardFile = Join-Path $repo 'build\claude-campaign-guard.json' }

# Each runner's shortcut: its name is also the window title, so the operator can tell the campaigns apart.
$shortcuts = @(
  @{ Runner = 'claude'; Name = 'Voxel Claude campaign'; Icon = 'voxel-campaign-claude.ico'
     Description = 'Start the Voxel campaign in Claude Code (the latest Opus)' },
  @{ Runner = 'agy'; Name = 'Voxel Carbon campaign'; Icon = 'voxel-campaign-carbon.ico'
     Description = 'Start the Voxel campaign in Google Antigravity on Orchestrator (Carbon)' }
)
$title = ($shortcuts | Where-Object { $_.Runner -eq $Runner }).Name

if ($InstallShortcut) {
  $pwsh = (Get-Process -Id $PID).Path
  $brand = Join-Path $repo 'assets\brand\voxel.ico'
  $renderer = Join-Path $repo 'scripts\campaign-icon.py'
  $retired = @()
  if ($DryRun) {
    foreach ($s in $shortcuts) {
      "would write: $(Join-Path $ShortcutDir "$($s.Name).lnk")"
      "  target: $pwsh -NoLogo -NoExit -NoProfile -File `"$PSCommandPath`" -Runner $($s.Runner)"
      "  icon: $(Join-Path $IconDir $s.Icon)"
    }
    foreach ($link in $retired) { if (Test-Path -LiteralPath $link) { "would remove: $link" } }
    exit 0
  }
  $python = (Get-Command python -CommandType Application -ErrorAction Ignore | Select-Object -First 1).Source
  if (-not $python) { 'python is not on PATH: install Python 3, then write the shortcuts again'; exit 1 }
  New-Item -ItemType Directory -Force $IconDir | Out-Null
  foreach ($s in $shortcuts) {
    $icon = Join-Path $IconDir $s.Icon
    & $python $renderer badge $brand $s.Runner $icon
    if ($LASTEXITCODE -ne 0) { "the icon for $($s.Name) could not be rendered"; exit 1 }
    $link = Join-Path $ShortcutDir "$($s.Name).lnk"
    $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($link)
    $shortcut.TargetPath = $pwsh
    $shortcut.Arguments = "-NoLogo -NoExit -NoProfile -File `"$PSCommandPath`" -Runner $($s.Runner)"
    $shortcut.WorkingDirectory = $repo
    $shortcut.Description = $s.Description
    $shortcut.IconLocation = "$icon,0"
    $shortcut.Save()
    "shortcut written: $link"
  }
  foreach ($link in $retired) {
    if (Test-Path -LiteralPath $link) { Remove-Item -LiteralPath $link; "shortcut removed: $link" }
  }
  exit 0
}

if (-not $Goal) {
  $Goal = (@'
Finish the Voxel implementation plan (todo/implementation-plan.md) 100% complete and aim for excellence: the best lightweight DICOM viewer of its kind, fast to open and a pleasure to use, matching design/SPEC.md 1:1 in all three interfaces. Act autonomously under the Operating directive and Design contract rules in AGENTS.md: decide and act instead of asking, heal what breaks at its owning layer, never edit a file under design/contract or design/screens to make a test pass, and improve the repo, its tools and methods whenever they slow the work or let a defect through. Work it with the process-plan skill, as the prompt `process plan` does, without stopping between sections or phases. Never ask the operator a question: take the industry-standard option and record the decision, and what reversing it would cost, in the run file. The goal is met only when `python scripts/todo-graph.py query stats` shows verified equal to total, or every row still open is in phase 99 or waits on a Need this session cannot meet and the run file carries its PARKED line and park record.
'@).Trim()
}

# Who holds the run, read before anything starts. The guard's own field is session_id (scripts/campaign_guard.py).
$held = $null
if (Test-Path -LiteralPath $GuardFile) {
  $held = try { [string](Get-Content -LiteralPath $GuardFile -Raw | ConvertFrom-Json).session_id } catch { '' }
  if ($held -notmatch '^[0-9A-Za-z-]{8,64}$') { $held = '' }
}
if ($null -eq $held) {
  $Goal += ' No run guard was held when this session was launched: if process-plan finds a guard owned by another session, another run is live, so start nothing, never use --handover, and end the turn.'
} elseif ($held) {
  $Goal += " A run guard held by session $held was acknowledged by the operator at launch: take the run over from that session only, with ``acquire --handover resumed-from-launcher``. If the guard names any other session, another run is live: start nothing and end the turn."
} else {
  $Goal += ' A run guard file was present at launch but named no session: do not take it over. Report what the guard file holds and end the turn.'
}
# One line with no double quote: it is passed to the agent as a single argument. Claude Code allows 4,000 characters.
if ($Goal.Contains('"') -or $Goal.Contains("`n")) { 'the goal must be one line with no double quote'; exit 1 }
if ($Goal.Length -gt 4000) { "the goal is $($Goal.Length) characters; Claude Code allows 4,000"; exit 1 }

if ($Runner -eq 'agy') {
  # Antigravity takes its flags as --name=value; --prompt-interactive runs the goal and keeps the session open. It
  # chooses its own conversation id, which the run guard records (agy --help, 1.5.6).
  $agent = 'agy'
  $arguments = @("--model=$Model", '--dangerously-skip-permissions', "--prompt-interactive=$Goal")
} else {
  $agent = 'claude'
  $session = [guid]::NewGuid().ToString()
  $arguments = @('--session-id', $session, '--dangerously-skip-permissions', '--model', $Model, '--effort', $Effort, '--name', $title, "/goal $Goal")
}
if ($DryRun) {
  "in $repo"
  if ($null -ne $held) { "a run guard is held by session $(if ($held) { $held } else { '(the guard file names none)' }): a real start asks before taking it over" }
  "$agent $($arguments[0..($arguments.Count - 2)] -join ' ') `"$($arguments[-1])`""
  exit 0
}

# Looked up, not assumed: a missing tool is named with its fix instead of failing as a bare "not recognized".
$python = (Get-Command python -CommandType Application -ErrorAction Ignore | Select-Object -First 1).Source
$stand_in = if ($agent -eq 'agy') { $AgyPath } else { $ClaudePath }
$program = if ($stand_in) { $stand_in } else { (Get-Command $agent -ErrorAction Ignore | Select-Object -First 1).Source }
if (-not $python) { 'python is not on PATH: install Python 3, then start again'; exit 1 }
if (-not $program) {
  if ($agent -eq 'agy') { 'agy is not on PATH: install Google Antigravity, then start again' } else { 'claude is not on PATH: install Claude Code, then start again' }
  exit 1
}

if ($null -ne $held) {
  "a run guard is held by session $(if ($held) { $held } else { '(the guard file names none)' })"
  'If that session is still working in another window, close this one now.'
  if (-not $TakeOver) { [void](Read-Host 'Press Enter to start a new session that takes the run over') }
}

# The sign-in (Claude Code's; Antigravity signs in itself). Each line says where it came from, never the token itself.
if ($agent -eq 'agy') {
  'sign-in: Antigravity uses its own Google sign-in'
} elseif ([Environment]::GetEnvironmentVariable($tokenName)) {
  'sign-in: the long-lived token this window already has'
} else {
  $token = if (Test-Path -LiteralPath $UserEnvKey) { (Get-Item -LiteralPath $UserEnvKey).GetValue($tokenName, $null) }
  if ($token) {
    [Environment]::SetEnvironmentVariable($tokenName, $token)
    $token = $null
    'sign-in: the long-lived token from your user variables'
  } else {
    'sign-in: no long-lived token is stored, so the session uses the claude.ai sign-in'
    "          to store one: run ``claude setup-token`` and keep its output as the user variable $tokenName"
  }
}

# claude.exe shows --name in its title; Antigravity never rewrites the host title, so the one set here persists.
try { $Host.UI.RawUI.WindowTitle = $title } catch { Write-Verbose "window title not set: $($_.Exception.Message)" }
Set-Location -LiteralPath $repo
& $program @arguments
