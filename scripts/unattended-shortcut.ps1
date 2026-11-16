# Puts "<Project> <Runner> campaign" shortcuts on the Windows desktop, one per runner the run profile names (its own
# agent and its `runners`), each starting the unattended run in WSL on that runner, with the project's icon and the
# runner's badge in its corner (the shape of Office's and Isotone's campaign launchers). The run lives in tmux, in WSL;
# Windows only starts it.
#
#   pwsh scripts/unattended-shortcut.ps1 -Distro Ubuntu -Icon assets/brand/project.ico
#   pwsh scripts/unattended-shortcut.ps1 -Remove       remove every shortcut and icon this project made
#
# Each link runs PowerShell, which runs `wsl.exe -d <distro> --cd <project in WSL> --exec bash -lc <start command>`:
# the command `unattended-run.py`'s start_command gives (a test holds the two equal), which starts the run on the runner
# and, on a failure, says so and waits for Enter; a failure of WSL itself is said and waits for Enter too.
# Links and icons are written under a temporary name and moved over the old, so a failed save or icon keeps a
# working shortcut and leaves no broken one.
# Removal finds this project's links by the mark in their description, so it works whatever the profile, the icon
# or the distro now are. Nothing here starts a run: only the operator's double-click does.
param(
  [string]$Distro = '',
  [string]$Icon = '',
  [string]$Project = '',
  [string]$ShortcutDir = [Environment]::GetFolderPath('Desktop'),
  [string]$IconDir = '',
  [switch]$Remove,
  # For the tests: a stand-in for wsl.exe, and the Python that reads the profile and renders the icons.
  [string]$Wsl = '',
  [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
# The project this script is installed in holds the profile; -Project says where the run starts when that differs
# (a project in WSL given by its \\wsl.localhost\<distro>\ path, or its Linux path).
$root = Split-Path $here
if (-not $Project) { $Project = $root }
if (-not ($Project -match '^\\\\wsl(?:\.localhost|\$)\\' -or $Project.StartsWith('/'))) {
  $found = Resolve-Path -LiteralPath $Project -ErrorAction Ignore
  if (-not $found) { "unattended-shortcut: the project folder does not exist: '$Project'; nothing was written"; exit 1 }
  $Project = $found.Path.TrimEnd('\')
}
$name = Split-Path $Project -Leaf
if (-not $IconDir) { $IconDir = Join-Path $env:LOCALAPPDATA $name }
$mark = "conclave-unattended: $Project"
# The project's own key, in its icons' names: two projects may share an icon folder, or a folder name.
$sha = [System.Security.Cryptography.SHA256]::Create()
$digest = $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Project.ToLowerInvariant()))
$key = -join ($digest[0..3] | ForEach-Object { $_.ToString('x2') })
$labels = @{ claude = 'Claude'; codex = 'Codex'; agy = 'Carbon' }

function Refuse([string]$why) { "unattended-shortcut: $why; nothing was written"; exit 1 }

function Get-Owned {
  $shell = New-Object -ComObject WScript.Shell
  Get-ChildItem -LiteralPath $ShortcutDir -Filter '*campaign*.lnk' -File -ErrorAction Ignore |
    Where-Object { $shell.CreateShortcut($_.FullName).Description -eq $mark }
}

if ($Remove) {
  $links = @(Get-Owned)
  foreach ($link in $links) { Remove-Item -LiteralPath $link.FullName; "removed: $($link.FullName)" }
  # Named apart from the -Icon parameter: PowerShell names ignore case, and $icon would be that typed string.
  $badges = @(Get-ChildItem -LiteralPath $IconDir -Filter "campaign-*-$key.ico" -File -ErrorAction Ignore)
  foreach ($badge in $badges) { Remove-Item -LiteralPath $badge.FullName; "removed: $($badge.FullName)" }
  "unattended-shortcut: $($links.Count) shortcut(s) and $($badges.Count) icon(s) of $Project removed"
  exit 0
}

if (-not $Distro) { Refuse '-Distro names no WSL distro' }
if (-not $Icon -or -not (Test-Path -LiteralPath $Icon -PathType Leaf)) { Refuse "-Icon is not a file: '$Icon'" }
if (-not $Python) {
  $Python = (Get-Command python -CommandType Application -ErrorAction Ignore | Select-Object -First 1).Source
}
if (-not $Python) { Refuse 'python is not on PATH' }
if (-not $Wsl) {
  $Wsl = (Get-Command wsl.exe -CommandType Application -ErrorAction Ignore | Select-Object -First 1).Source
}
if (-not $Wsl) { Refuse 'wsl.exe is not on PATH: install WSL' }
$env:WSL_UTF8 = '1'  # wsl.exe lists its distros in UTF-16 otherwise
# Every call into WSL is --exec: `wsl.exe -- <command>` hands the command to the login shell, which eats the
# backslashes of a Windows path and parses the start command again (found by the live proof, 2026-11-13).

# The runners, read by the kit's own profile loader, so a profile the run would refuse is refused here too.
$reader = @'
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("unattended_lib", sys.argv[1])
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)
profile = lib.load_profile(sys.argv[2])
print(json.dumps([profile["agent"], *profile.get("runners", {})]))
'@
$read = & $Python -B -c $reader (Join-Path $here 'lib\unattended.py') $root 2>&1
if ($LASTEXITCODE -ne 0) { Refuse "the run profile cannot be read: $(($read | Out-String).Trim())" }
$agents = @(($read | Select-Object -Last 1) | ConvertFrom-Json)

$listed = @(& $Wsl -l -q 2>$null | ForEach-Object { ($_ -replace "`0", '').Trim() } | Where-Object { $_ })
if ($LASTEXITCODE -ne 0 -or $listed -notcontains $Distro) {
  Refuse "WSL has no distro '$Distro' (it lists: $($listed -join ', '))"
}

# The project's path in WSL: a \\wsl.localhost\<distro>\ or \\wsl$\<distro>\ path is that distro's own path, a Linux
# path is itself, and a Windows-drive path is what wslpath says.
if ($Project -match '^\\\\wsl(?:\.localhost|\$)\\([^\\]+)\\(.*)$') {
  if ($Matches[1] -ne $Distro) { Refuse "the project is in distro '$($Matches[1])', not '$Distro'" }
  $linux = '/' + ($Matches[2] -replace '\\', '/')
} elseif ($Project.StartsWith('/')) {
  $linux = $Project
} else {
  $linux = (& $Wsl -d $Distro --exec wslpath -a $Project 2>$null | Select-Object -First 1)
  if ($LASTEXITCODE -ne 0 -or -not $linux) { Refuse "wslpath could not translate '$Project'" }
  $linux = $linux.Trim()
}
& $Wsl -d $Distro --exec test -d $linux 2>$null
if ($LASTEXITCODE -ne 0) { Refuse "the project path '$linux' does not exist in '$Distro'" }

# A PowerShell string literal of any text.
function PSQuote([string]$text) { "'" + $text.Replace("'", "''") + "'" }

# One argument as the Windows command line passes it (backslashes doubled before a quote, the quote escaped).
function Quote([string]$arg) {
  if ($arg -and $arg -notmatch '[\s"]') { return $arg }
  '"' + ($arg -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
}

$renderer = Join-Path $here 'campaign-icon.py'
$pwsh = (Get-Process -Id $PID).Path  # the PowerShell 7 that runs this script runs the links too
$brand = (Resolve-Path -LiteralPath $Icon).Path
New-Item -ItemType Directory -Force -Path $IconDir, $ShortcutDir | Out-Null
$shell = New-Object -ComObject WScript.Shell
foreach ($agent in $agents) {
  $label = "$name $($labels[$agent]) campaign"
  $badge = Join-Path $IconDir "campaign-$agent-$key.ico"
  $badgeTemp = "$badge.$PID.tmp.ico"
  & $Python -B $renderer badge $brand $agent $badgeTemp
  if ($LASTEXITCODE -ne 0) {
    Remove-Item -LiteralPath $badgeTemp -ErrorAction Ignore
    "unattended-shortcut: the icon for $label could not be rendered; its shortcut is left as it was"
    exit 1
  }
  Move-Item -LiteralPath $badgeTemp -Destination $badge -Force
  $command = "python3 scripts/unattended-run.py start --agent $agent || " +
    "{ echo 'The run did not start: the reason is above. Press Enter to close.'; read -r _; }"
  $link = Join-Path $ShortcutDir "$label.lnk"
  $linkTemp = Join-Path $ShortcutDir "$label.$PID.tmp.lnk"
  try {
    $shortcut = $shell.CreateShortcut($linkTemp)
    # PowerShell runs wsl.exe, so a failure of WSL itself (a drive gone, a distro removed) is said and waits for Enter
    # too; the command is in the link, not in a script on the project's drive, which may be the one that is gone.
    $words = @('-d', $Distro, '--cd', $linux, '--exec', 'bash', '-lc', $command)
    $code = "& $(PSQuote $Wsl) $(($words | ForEach-Object { PSQuote $_ }) -join ' '); if (`$LASTEXITCODE -ne 0) { " +
      "Write-Host ('WSL could not start the run (exit ' + `$LASTEXITCODE + '): the reason is above. ' + " +
      "'Press Enter to close.'); " +
      "[void][Console]::ReadLine() }"
    $shortcut.TargetPath = $pwsh
    $shortcut.Arguments = "-NoLogo -NoProfile -Command $(Quote $code)"
    $shortcut.WorkingDirectory = $env:USERPROFILE
    $shortcut.Description = $mark
    $shortcut.IconLocation = "$badge,0"
    $shortcut.Save()
    Move-Item -LiteralPath $linkTemp -Destination $link -Force
  } catch {
    Remove-Item -LiteralPath $linkTemp -ErrorAction Ignore
    "unattended-shortcut: the shortcut $label could not be saved ($($_.Exception.Message)); the old one is kept"
    exit 1
  }
  "shortcut written: $link"
}
exit 0
