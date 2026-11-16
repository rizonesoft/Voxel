---
schema_version: 1
id: packaging
domain: 06-release
status: active
title: "TODO-01 -- Packaging and release"
track: M6
---

# TODO-01 -- Packaging and release

> **Goal:** Voxel is one portable exe a user copies to a PC and runs: double-clicking a DICOM file opens it in Voxel, the app says plainly what it may and may not be used for, and the owner has opened their own real X-ray and MRI studies in it and found every tool working.

> **Current state:** Measured 2026-11-17. No code exists. The release profile comes from D00 T01 §1, the size baseline from D00 T01 §2 and the tools from D05 T01. Two things are the owner's to decide and are not decided: the label (review only, or diagnostic use with certification) and whether to buy a code signing certificate. The foundation plan records the second as out of scope for version 1.

## Inputs

- `docs/plans/2026-11-17-voxel-tech-stack.md`: "The stack" (packaging), "Targets" (exe under 30 MB), "Risks" (diagnostic use is regulated) and "Out of scope for version 1" (code signing).
- `design/SPEC.md`, `design/contract/` and `design/screens/`: the approved interface. Every control named in this file is registered once in `src/ui/controls.rs` and every panel once in `src/ui/panels.rs` (D02 T02 §2), and is drawn by whichever of the three interfaces is active. Where a section says toolbar, read the interface's tool area: the toolbar in Workstation, the dock in Lightbox, the rail or an inspector panel in Console. Placement, size and look are fixed by the contract, not by this file.
- `docs/dependencies.md` from D00 T01 §2: the size baseline and the dependency list §4 builds the licence notices from.
- `src/main.rs` (the command-line argument path) from D02 T01 §3, which the file association in §3 calls.
- `src/ui/mode.rs` from D05 T01 §1, where §4 places the About entry.
- `todo/plan.json`: the acceptance bar §5 checks.
- -> XREF: D02 T02 §7 -- the Interface setting the installer of §6 writes before the first start

## Outcome

- The owner's label decision is recorded in `docs/decisions/2026-label.md`.
- `scripts/build-release.ps1` produces `dist/Voxel.exe` with an icon and version details, and fails when the exe is over 30 MB.
- `Voxel.exe --register` and `--unregister` add and remove a per-user "Open with Voxel" association for DICOM files, with no administrator rights.
- An About window shows the version, the label and the licences of everything Voxel is built from.
- `dist/VoxelSetup.exe` installs Voxel for the current user, asks which of the three interfaces to use, and uninstalls cleanly.
- The owner has run the acceptance pass on real studies and its result is recorded.

**Adjacency:** list=not-applicable (packaging creates no records to find); document=applicable; settings=applicable; reporting=not-applicable (no summaries in version 1); notifications=not-applicable (a local viewer notifies nobody); permissions=applicable; audit=not-applicable (no user data is changed); exchange=not-applicable (import is D01 T01, export is D05 T01 §7); reverse=applicable

**Adjacency rationale:** The document is the exe itself and the licence notices of §4. The setting is the file association, owned by §3 with Explorer's double-click as its consumer. Permissions: the association is written under the current user only, and §3 refuses cleanly when even that is denied. Reverse is `--unregister` in §3, which removes exactly what `--register` wrote.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | Diagnostic-use label decision | -- | [ ] |
| 2 | §2 | Portable release build with a size gate | D05 T01 §5, D05 T01 §6, D05 T01 §7 | [ ] |
| 3 | §3 | Per-user file association and its removal | §2 | [ ] |
| 4 | §4 | About window with version, label and licences | §1, §2 | [ ] |
| 5 | §5 | Acceptance pass on the owner's real studies | §3, §4, §6, D02 T02 §10 | [ ] |
| 6 | §6 | Installer with the interface choice | §2, §3, D02 T02 §7 | [ ] |

## 1. Diagnostic-use label decision

Software used to diagnose from medical images is a regulated medical device in most countries (the FDA in the United States, CE marking in Europe, SAHPRA in South Africa). Clinicians are in scope, so Voxel must say which it is. The recommendation in the foundation plan is to ship labelled "For review only. Not for diagnostic use." and treat certification as a separate project. This is the owner's decision, and the wording appears in the app (§4), so it is recorded before that section runs.

**Phase:** 6
**Needs:** owner-decision
**Surface:** no

**Build order:**

1. Put the two options and the recommendation to the owner. Done when: the owner has answered.
2. Record the answer in `docs/decisions/2026-label.md` and remove the `owner-decision` Need from this section. Done when: the file holds the decision, its date and the exact label wording.

- [ ] Ask the owner to choose between (a) the review-only label, recommended, and (b) pursuing certification for diagnostic use, stating that (b) is a regulatory project outside this plan. Done when: the owner's answer is quoted in `docs/decisions/2026-label.md` with its date.
- [ ] Write the exact label wording the app will show into `docs/decisions/2026-label.md`, as one sentence short enough for a status bar. Done when: the sentence is in the file and the owner has seen it. Cheaper substitute: wording invented in §4 without this record must fail review.
- [ ] Remove `owner-decision` from this section's Needs line, leaving `none`. Done when: `python scripts/todo-graph.py resolve 'D06 T01 §1'` no longer reports the section as waiting.
- [ ] Commit: `release: record the diagnostic-use label decision`

**Test checkpoint:** `python scripts/todo-graph.py validate` exits 0 and `docs/decisions/2026-label.md` holds the owner's quoted answer and the label sentence; deleting the sentence makes §4's label test fail.

## 2. Portable release build with a size gate

"Lightweight" gets the same treatment as "fast": a number and a gate. One script builds the exe the user receives, stamps it with an icon and version, and fails when it has grown past the target, so a heavy dependency cannot arrive unnoticed.

**Phase:** 6
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Embed the icon and version details through a build script. Done when: Explorer shows the icon and the file's Details tab shows the version.
2. Write `scripts/build-release.ps1` with the size gate. Done when: it produces `dist/Voxel.exe` and fails over 30 MB.

- [ ] Create `assets/voxel.ico` (a simple cube mark at 16, 32, 48 and 256 pixels) and `assets/voxel.svg` as its source. Done when: both files are committed and the icon opens in an image viewer at all four sizes.
- [ ] Add `build.rs` with the `winresource` crate as a build dependency to embed the icon, the product name "Voxel", the version from `Cargo.toml` and a DPI-aware, UTF-8 application manifest. Done when: `target/release/voxel.exe` shows the icon in Explorer and the version on its Details tab, and the window is sharp on a display scaled to 150 percent.
- [ ] Set the window and taskbar icon in `src/app.rs` from the same `assets/voxel.ico`. Done when: the running app shows the icon in the taskbar.
- [ ] Build with the C runtime linked statically (`-C target-feature=+crt-static` in `.cargo/config.toml`) so the exe needs no redistributable. Done when: `dumpbin /dependents target/release/voxel.exe` lists no `VCRUNTIME` or `MSVCP` library. Cheaper substitute: shipping the redistributable installer beside the exe must fail; the product is one file.
- [ ] Write `scripts/build-release.ps1`: run `cargo build --release --locked` through `bosun run --` when `bosun` is installed, copy the exe to `dist/Voxel.exe`, print its size, and exit 1 when it is over 30 MB. Done when: the script produces the file and prints the size; `dist/` is in `.gitignore`.
- [ ] Prove the gate can fail by running `scripts/build-release.ps1 -MaxMegabytes 1`. Done when: the run exits 1 and names the size and the limit.
- [ ] Record the release size and the date in `docs/performance.md`. Done when: the value matches `(Get-Item dist/Voxel.exe).Length`.
- [ ] Run `dist/Voxel.exe` from a folder outside the repository on a path with a space and a non-ASCII character, opening a corpus file by argument. Done when: the image shows, proving the exe depends on nothing beside it.
- [ ] Commit: `release: portable build with icon, version and size gate`

**Test checkpoint:** `pwsh scripts/build-release.ps1` exits 0 and prints a size under 30 MB; `pwsh scripts/build-release.ps1 -MaxMegabytes 1` exits 1.

## 3. Per-user file association and its removal

Double-clicking a file is the whole product. A portable app has no installer to register it, so Voxel registers itself on request, for the current user only, without administrator rights, and removes exactly what it added. It offers itself in "Open with" and never takes a default away from another program without the user choosing it in Windows.

**Phase:** 6
**Needs:** windows-host
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** make DICOM files open in Voxel from Explorer, and undo that
**Treatment:** a short confirmation sentence after each action, for example "DICOM files can now be opened with Voxel"
**Chrome:** two entries in the app's corner menu, "Open DICOM files with Voxel" and "Remove file association", shown in both modes; the same actions as `--register` and `--unregister` on the command line

**Build order:**

1. Write register and unregister in `src/assoc.rs` under `HKEY_CURRENT_USER\Software\Classes`. Done when: the round-trip test leaves the registry as it found it.
2. Add the command-line flags and the menu entries. Done when: a double-click on a `.dcm` file opens Voxel.

- [ ] Write `register()` in `src/assoc.rs`: create the ProgID `Voxel.DicomFile` with an open command of the current exe path and `"%1"`, and add it under `OpenWithProgids` of `.dcm`, `.dicom` and `.ima`, all under `HKEY_CURRENT_USER\Software\Classes`, then notify the shell with `SHChangeNotify`. Done when: `tests/assoc.rs`, run against a test root key, reads back the keys and values. Cheaper substitute: writing under `HKEY_LOCAL_MACHINE` must fail; no administrator prompt may appear.
- [ ] Write `unregister()` in `src/assoc.rs` removing only the ProgID and the three `OpenWithProgids` values `register()` adds. Done when: a test that registers and unregisters leaves an export of the test root key identical to the one taken before, including a pre-existing value from another program on `.dcm`.
- [ ] Add `--register` and `--unregister` to `src/main.rs`, running without opening the window, printing the confirmation sentence and returning exit code 0, or 1 with a plain sentence when the registry write is refused. Done when: a test with a read-only test root key gets exit code 1 and the sentence.
- [ ] Add the two menu entries in `src/ui/mode.rs` (both modes) calling the same functions, showing "Remove file association" only while registered. Done when: a test asserts the entries' visibility before and after registering.
- [ ] Detect in `src/assoc.rs` that the registered path no longer matches the running exe (the exe was moved) and offer to update it with a line in the empty-state view. Done when: a test with a stale path sees the offer, and accepting it rewrites the command.
- [ ] Open a file whose name has no extension, as on patient discs, when it is passed by argument: the association cannot cover these, so `src/app.rs` relies on content detection (D01 T01 §2), and the Open Folder action covers the disc. Done when: `tests/open_paths.rs` opens an extensionless corpus copy by argument.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `menu`, `settings` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `release: per-user file association and its removal`

**Test checkpoint:** `cargo test --test assoc` passes; making `unregister()` delete the whole `.dcm` key fails the pre-existing-value test.

## 4. About window with version, label and licences

The place a user or an auditor looks to learn what this program is. It carries the label the owner decided in §1, shown also in the status bar so it is seen without being looked for, and the licence notices that the open-source crates Voxel is built from require.

**Phase:** 6
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** find out which version this is, what it may be used for, and what it is built from
**Treatment:** a small window with the icon, "Voxel", the version, the label sentence, and a scrolling list of components with their licences
**Chrome:** an About entry in the corner menu (both modes); the label sentence also sits at the left of the status bar at all times; Esc closes the window

**Build order:**

1. Generate the licence notices at build time into `assets/licences.txt`. Done when: the file lists every dependency in `Cargo.lock` that ships in the exe.
2. Write the About window in `src/ui/about.rs` and the status bar label. Done when: the label test passes.

- [ ] Generate `assets/licences.txt` with `cargo about` (configured in `about.toml` to accept the licences in use) from `scripts/build-release.ps1`, failing the build on a licence not in the accepted list. Done when: the file names every non-dev dependency, and adding a dependency with an unlisted licence fails the script.
- [ ] Hold the label sentence in one constant, `LABEL`, in `src/ui/about.rs`, with a test asserting it equals the sentence recorded in `docs/decisions/2026-label.md`. Done when: `cargo test label` passes and fails when either side changes alone. Cheaper substitute: the sentence typed separately in the status bar and the About window must fail review; both read `LABEL`.
- [ ] Write the About window in `src/ui/about.rs` showing the icon, name, `CARGO_PKG_VERSION`, `LABEL`, the GPU adapter in use and the embedded licence text. Done when: a test opens it and finds the version string and `LABEL`.
- [ ] Draw `LABEL` at the left of the status bar in `src/ui/toolbar.rs` in both modes. Done when: a test asserts the status bar text in Plain and Clinician modes.
- [ ] Add the About entry to the mode table in `src/ui/mode.rs` (both modes) with Esc closing the window. Done when: a test opens and closes it.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `about` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `release: About window with version, label and licences`

**Test checkpoint:** `cargo test label` and `cargo test about` pass; changing the sentence in `docs/decisions/2026-label.md` without changing `LABEL` fails `cargo test label`.

## 5. Acceptance pass on the owner's real studies

Phantoms and public test files prove correctness; they do not prove that the studies the owner actually receives open and look right. The plan's acceptance bar says "on real studies", so the owner runs the finished exe on their own X-ray and MRI studies. This is attended: nobody else has the studies, and nobody else can say the images look as they should.

**Phase:** 99
**Needs:** attended
**Surface:** no

**Build order:**

1. Write the checklist the owner follows in `docs/acceptance.md`. Done when: it has one line per item of the acceptance bar in `todo/plan.json`.
2. The owner runs it on real studies and each result is recorded. Done when: every line has a result and a date.

- [ ] Write `docs/acceptance.md` with one checkable line each for: double-click an X-ray file; window/level, zoom, pan, invert, reset; open an MRI folder and a disc with a `DICOMDIR`; scroll each series; MPR with crosshairs and an oblique plane; 3D in MIP and shaded modes; length and angle on an MRI and an X-ray; a 1 by 2 layout with linked scrolling; the tag browser; a PNG export; plain mode; register and unregister; each of the three interfaces, switched in Settings with a study open; an install with `dist/VoxelSetup.exe` choosing a non-default interface, and its uninstall. Done when: the file exists and names no patient.
- [ ] Run `dist/Voxel.exe` with the owner on at least one real X-ray study and one real multi-series MRI study, ticking each line or recording what went wrong. Done when: every line carries a result and the date, with no patient name, ID or image added to the repository. Cheaper substitute: running the checklist on corpus or phantom files must fail; the bar says real studies.
- [ ] Record the start time `scripts/measure-start.ps1` reports for the real X-ray file in `docs/acceptance.md`. Done when: the value is in the file and under 1000 ms, or the shortfall is filed through `add-todo`.
- [ ] File each failed line as a new section through the `add-todo` skill, naming the series type and transfer syntax without patient details, and add any unsupported format to `docs/codec-coverage.md`. Done when: every failed line names the section that owns its fix, or no line failed.
- [ ] Commit: `release: acceptance pass on real studies recorded`

**Test checkpoint:** `python scripts/todo-graph.py validate` exits 0 and `Select-String -Path docs/acceptance.md -Pattern '\[ \]'` finds no unticked line without a named owning section; an unticked line with no owner is found by that command.

## 6. Installer with the interface choice

The owner decided on 2026-11-17 that the interface is chosen when Voxel is installed. The portable exe stays, for discs and locked-down PCs, and an installer is added beside it: per-user, with no administrator prompt, whose one custom page asks the question the first-run chooser asks a portable copy (D02 T02 §9).

**Phase:** 6
**Needs:** windows-host
**Surface:** yes
**Fidelity:** the wizard is Inno Setup's standard look; the page's title, the three names and their one-line descriptions are word for word those of the `welcome` screen in `design/SPEC.md`
**Job:** install Voxel and pick how it looks, in one pass
**Treatment:** a standard wizard page titled "Choose how Voxel looks" with three radio buttons (Workstation, selected and marked "Recommended"; Lightbox; Console), each with its description, and the sentence "You can change this later in Settings."
**Chrome:** the wizard's own Back, Next and Cancel; a checkbox "Open DICOM files with Voxel", ticked, on the tasks page

**Build order:**

1. Write `installer/voxel.iss` and build it from `scripts/build-release.ps1`. Done when: `dist/VoxelSetup.exe` exists.
2. Prove install, first start and uninstall end to end. Done when: the round-trip test leaves the account as it found it.

- [ ] Install Inno Setup 6 with `winget install JRSoftware.InnoSetup` and record its version in `docs/dependencies.md` as a build tool. Done when: `iscc /?` prints its version.
- [ ] Write `installer/voxel.iss`: `PrivilegesRequired=lowest`, the default folder `{localappdata}\Programs\Voxel`, the exe from `dist/Voxel.exe`, the icon `assets/brand/voxel.ico`, the version read from the exe, a Start menu shortcut, and the label sentence from `docs/decisions/2026-label.md` on the welcome page. Done when: `iscc installer/voxel.iss` writes `dist/VoxelSetup.exe` and running it shows no administrator prompt. Cheaper substitute: an installer that asks for elevation must fail; a clinic PC's user often has none.
- [ ] Add the custom page "Choose how Voxel looks" in the `[Code]` section of `installer/voxel.iss` with the three radio buttons and descriptions, Workstation selected. Done when: the page shows between the folder page and the tasks page, and its texts equal the `welcome` screen's in `design/contract/workstation/welcome.json` (a test compares the strings).
- [ ] Write the choice after the files are copied by running `Voxel.exe --set-interface <name>`, a flag added in `src/main.rs` that writes only the `interface` field through `Settings::save` and exits 0. Done when: a test runs the flag with a temporary settings folder and reads the field back, and an existing settings file keeps its other fields. Cheaper substitute: the installer writing `settings.toml` itself must fail; the settings file has one writer.
- [ ] Run `Voxel.exe --register` from the installer when the "Open DICOM files with Voxel" task is ticked, and `Voxel.exe --unregister` from the uninstaller always. Done when: after install with the task ticked `tests/assoc.rs`'s check finds the ProgID, and after uninstall it does not.
- [ ] Ask in the uninstaller whether to remove the settings too, default No, and remove `%APPDATA%\Voxel` only on Yes. Done when: both answers are exercised and leave the expected state.
- [ ] Build the installer in `scripts/build-release.ps1` after the exe, and fail the script when `iscc` is missing or the installer is over 40 MB. Done when: the script writes both files and prints both sizes.
- [ ] Write `scripts/test-installer.ps1`: install silently into a temporary folder with `/VERYSILENT /DIR=<temp> /INTERFACE=lightbox` (a command-line parameter the script reads), start the installed exe with `--exit-after-first-image` on a phantom file, uninstall silently, and compare the registry export and the folder listing before and after. Every process it starts is stopped with its tree on a 120 second timeout. Done when: the script exits 0, the app started in Lightbox with no chooser, and nothing is left behind but the settings file.
- [ ] Commit: `release: installer with the interface choice`

**Test checkpoint:** `pwsh scripts/build-release.ps1` writes `dist/Voxel.exe` and `dist/VoxelSetup.exe`, and `pwsh scripts/test-installer.ps1` exits 0; removing the `--unregister` call from the uninstaller makes it exit 1 with the leftover ProgID named.

## Verification

- `dist/Voxel.exe`, copied alone to another folder, starts, opens a file by double-click after `--register`, and shows the decided label in the status bar and the About window.
- `--unregister` leaves the user's registry as it was before `--register`.
- The exe is under 30 MB and `docs/acceptance.md` records the owner's pass on real studies.
- `dist/VoxelSetup.exe` installs without an administrator prompt, starts in the chosen interface with no chooser, and uninstalls leaving nothing but the settings file.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
