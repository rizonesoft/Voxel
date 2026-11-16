# Voxel interface specification

Written 2026-11-17. This is the contract for the interface: the built app matches it 1:1. Where this file, the prototypes and the contract files disagree, the contract files in `design/contract/` win, because they are generated from the prototypes the owner approved.

## What the owner decided (2026-11-17)

- The brand is "Lattice": the cube with one bright voxel, in Conclave Design System v2 colours and type (`assets/brand/README.md`).
- Voxel ships three interfaces, and all three are complete: **Workstation** (the default), **Lightbox** and **Console**.
- The interface is chosen when Voxel is installed, and can be changed at any time in Settings.

## The files

| Path | What it is |
| ---- | ---------- |
| `design/prototype/workstation.html`, `lightbox.html`, `console.html` | The approved designs, one clickable page per interface |
| `design/prototype/support.js`, `design/prototype/img/` | The small runtime that draws them, and the phantom images they show |
| `design/screens/<interface>/<screen>.png` | The picture of each screen, 1440 by 900: 45 in all |
| `design/contract/<interface>/<screen>.json` | Each screen's controls and texts with label, shortcut, state, rectangle, colours, font |
| `design/tokens.json` | Every colour, type style, spacing step, radius and shadow |
| `scripts/render-design.py` | Regenerates the pictures and the contract files from the prototypes |

Open a prototype in a browser with `?screen=<name>` to see one screen, for example `design/prototype/console.html?screen=mpr`. The pictures and contract files are generated: never edit them by hand, change the prototype and run the script.

## The 15 screens

Every interface has all 15. The name is the one in the file names.

| Screen | What it shows | Mode |
| ------ | ------------- | ---- |
| `welcome` | First run of a portable copy: choose the interface, Workstation preselected | none |
| `empty` | No study open: drop hint, Open file, Open folder, the More tools hint | plain |
| `xray` | One X-ray open: the short tool set, brightness presets | plain |
| `loading` | A study opening: first image dimmed, progress, tools already live | clinician |
| `stack` | An MRI series: overlay, slice slider, a length and an angle measurement | clinician |
| `mpr` | The linked planes with crosshairs and a rotation handle | clinician |
| `view3d` | The 3D view: MIP or Shaded, preset, threshold, quality, orientation cube | clinician |
| `layout` | Two panes side by side, linked, the active pane framed | clinician |
| `tags` | The tag browser open with a search typed | clinician |
| `export` | The export sheet: file name, Include patient details (off), Cancel, Save PNG | clinician |
| `only2d` | A series that cannot be a volume: MPR and 3D disabled, the reason shown | clinician |
| `refusal` | A file that is not DICOM: one plain sentence, the file name, two ways out | plain |
| `menu` | The menu open: file association, Settings, About Voxel | clinician |
| `settings` | The Settings window over the stack | clinician |
| `about` | The About window: version, label, graphics, licences | clinician |

## What all three interfaces share

- **One set of controls.** Every control exists once in the app (`src/ui/controls.rs`): its name, label, shortcut, icon, the modes it appears in, and what it does. An interface decides only where a control sits and how it is drawn. A control that works in one interface works in all three.
- **Two modes.** Plain mode shows Open, Fit, Reset, Lighter, Darker, Auto, More tools and the menu. Clinician mode ("More tools" on) adds Invert, Stack, MPR, 3D, Length, Angle, Clear, Layout, Link, Overlay, Tags and Export. Shortcuts of hidden controls do nothing.
- **The image area is black** (`image-ground`), whatever surrounds it. Scan images are never tinted.
- **The label** "For review only. Not for diagnostic use." is on screen at all times. Its wording is pending the owner's decision (D06 T01 §1) and is read from one constant.
- **Plane colours:** axial `plane-axial`, sagittal `plane-sagittal`, coronal `plane-coronal`. A crosshair line takes the colour of the plane it stands for.
- **Measurements** are drawn in `signal` at 1.5 pixels, with their value in `overlay` type in `signal-ink`.
- **Image information** sits in the corners in `overlay` type with a dark halo, and orientation letters at the middle of each edge.
- **The Settings, About and first-run windows are the same in every interface.**
- **The phantom data** in the designs (patient "Phantom, Voxel", the five MR Brain series, the chest X-ray) is the fixture the contract tests load, built by `tests/common/phantom.rs`.
- **Dark only.** Version 1 has one theme.

## Shortcuts

| Control | Key | Control | Key |
| ------- | --- | ------- | --- |
| Open file | Ctrl O | Open folder | Ctrl Shift O |
| Fit | F | Reset | R, or double-click |
| Invert | I | One image pixel per screen pixel | 1 |
| Lighter, Darker, Auto | +, -, 0 | Overlay | O |
| Stack | S | MPR | M |
| 3D | 3 | Reset planes | Shift R |
| Length | L | Angle | A |
| Delete measurement | Del | Undo, redo | Ctrl Z, Ctrl Y |
| Layout | G | Link scrolling | K |
| Tags | T | Export | Ctrl E |
| Close a window or cancel a tool | Esc | Hide the series list | Tab |

## Interface 1: Workstation (the default)

The layout radiology staff already know. Top to bottom at 1440 by 900:

| Region | Size | Content |
| ------ | ---- | ------- |
| Title bar | 36 high, `surface-sunken` | Mark, "Voxel", the patient and study, window buttons |
| Toolbar | 52 high, `surface` | Every control as icon and label, in groups split by hairlines; More tools switch and menu at the right |
| Series strip | 240 wide, `ground` | Patient, study line, one card per series (64 pixel thumbnail, name, counts, "2D only" tag) |
| Image area | the rest | One pane, 1 by 2, or MPR as 2 by 2 (axial, sagittal, coronal, 3D) |
| Tag panel | 360 wide, only on `tags` | Search, rows, Copy value |
| Status bar | 28 high, `surface-sunken` | The label at the left; modality, matrix, spacing and graphics at the right |

Popovers (export, menu, 3D settings, the 2D-only reason) are `surface-raised` with `elevation-2`, anchored under the control that opened them.

## Interface 2: Lightbox

The image fills the window and everything else floats on `glass`. The simplest for a patient.

| Region | Size | Content |
| ------ | ---- | ------- |
| Title bar | 32 high | Mark, "Voxel", window buttons |
| Image area | everything below | One pane, 1 by 2, or MPR as one large axial pane with sagittal and coronal stacked at the right |
| Study chip | 44 high pill, top left | Initials, patient, study line |
| View switch | 44 high pill, top centre, clinician only | Stack, MPR, 3D |
| Filmstrip | 78 high, above the dock, clinician only | One card per series (52 pixel thumbnail) |
| Dock | 56 high, bottom centre | Every control as a 44 pixel icon button with a tooltip; More tools switch; menu |
| Label | bottom left | The label, in `small` type |

Sheets (tags, export, 3D settings, menu) float over the image with a 16 pixel radius. The 3D view has no MPR fourth pane in this interface.

## Interface 3: Console

Every setting and figure visible at once, in Conclave-style panels.

| Region | Size | Content |
| ------ | ---- | ------- |
| Top bar | 44 high, `surface` | Mark, "Voxel", the path patient / study / series, More tools switch, window buttons |
| Rail | 56 wide, `surface` | Open, then Stack, MPR, 3D, then Overlay, Tags, Export, each a 44 pixel icon button; menu at the bottom. The active view has a `signal` bar on its left edge |
| Series list | 212 wide | "Series" label with the count, one row per series (44 pixel thumbnail) |
| Image area | the rest | As Workstation: one pane, 1 by 2, or MPR as 2 by 2 |
| Inspector | 296 wide, clinician only | Panels that change with the view (below) |
| Status bar | 28 high | A `warn` dot and the label at the left; figures at the right |

Inspector panels, each a `surface` panel with a `micro` code at the top right:

| Panel | Shown on | Content |
| ----- | -------- | ------- |
| Window | every view but tags | Width and Level as figures; Auto, Lighter, Darker; Fit, Reset, Invert |
| Measurements | stack, layout | Length, Angle; the list of measurements on the slice; Delete, Undo, Clear |
| Layout | stack, layout, 2D-only | 1, 1 x 2, 2 x 1, 2 x 2; Link scrolling |
| 3D rendering | 3D | MIP or Shaded, Preset, Threshold, Quality, Reset preset, Reset view |
| Planes | MPR | The slice of each plane in its colour, the rotation, Reset planes |
| DICOM tags | tags | Search, rows, Copy value |
| Export picture | export | File name, Include patient details, Cancel, Save PNG |
| 2D only | 2D-only | The reason MPR and 3D are unavailable, with a `warn` border |

## Settings

One window, the same in every interface, opened from the menu. Every change is saved at once and applies at once, with no restart.

| Setting | Choices | Default |
| ------- | ------- | ------- |
| Interface | Workstation, Lightbox, Console (three picture cards) | Workstation |
| Start with | Simple tools, More tools, What I used last | Simple tools |
| Image information | Full, Minimal, Off | Full |
| 3D quality | Automatic, Low, Medium, High | Automatic |
| DICOM files open with Voxel | Add or Remove, for this Windows account only | not set |

"Reset to defaults" restores every row above. Changing the interface keeps the open study, the slice, the window and the measurements.

## Choosing the interface at install

- **The installer** (`VoxelSetup.exe`, per-user, no administrator rights) has a page "Choose how Voxel looks" with the three interfaces and their one-line descriptions, Workstation selected. It writes the choice to the settings file before the first start.
- **A portable copy** (`Voxel.exe` run with no settings file) shows the `welcome` screen once, with the same three cards, and saves the choice on Continue.
- Either way the choice is the Interface setting, and Settings changes it later.

## What 1:1 means, and how it is proved

The app has a contract mode used only by tests: `voxel --contract <interface> <screen>` loads the phantom fixture, shows that screen in a 1440 by 900 window, writes what it drew as JSON in the same shape as `design/contract/`, saves a screenshot, and exits. `tests/ui_contract.rs` runs it for all 45 screens and compares:

| What | Rule |
| ---- | ---- |
| Controls | The same set as the contract file, matched by label: none missing, none extra |
| Label, shortcut, tooltip, enabled state, options, value | Exactly equal |
| Control rectangle | Each edge within 2 pixels |
| Text | Every text in the contract is present with the same words, font family, size and weight |
| Text position | Left and top within 3 pixels (text is measured by a different engine) |
| Colours | Fill and ink exactly equal to the token |
| Picture | Outside the image panes, the screenshot differs from `design/screens/` by no more than 2 percent of pixels, after a 1 pixel blur |

A screen passes only when every row passes. The image panes are excluded from the picture rule because the app draws real phantom volumes where the prototype shows drawings; their content is proved by the rendering tests instead. Anything the design does not show (a hover state, a focus ring, a window smaller than 1440 by 900) follows the rules below.

## States the pictures do not show

- **Hover:** a control's fill becomes `surface-raised` (`line` on glass); a card's border becomes `line-hover`.
- **Pressed:** the fill becomes `line`, with no movement.
- **Keyboard focus:** a 2 pixel `ground` gap then a 2 pixel `signal` ring, on every control.
- **Active:** `signal-soft` fill with `signal-ink` text (Workstation, Console); solid `signal` with `on-signal` text (Lightbox).
- **Disabled:** `line-strong` text, no hover, and a tooltip that says why.
- **Tooltips:** `surface-raised`, `small` type, after 400 ms, naming the control and its shortcut.
- **Smaller windows:** the minimum is 1024 by 640. Workstation's toolbar drops its labels below 1280 wide and keeps the icons. Lightbox's filmstrip scrolls sideways. Console's inspector scrolls, and its series list narrows to thumbnails below 1180 wide.
- **Motion:** 120 ms for hover and press, 200 ms for panels and sheets, ease-out, and none at all when Windows has animations turned off.

## Changing the design

A change to the interface starts in a prototype, never in the app. Edit the prototype, run `python scripts/render-design.py`, review the changed pictures, and commit the prototype, pictures and contract files together with the code that follows them. A contract test that fails is fixed in the app unless the owner has approved a design change.
