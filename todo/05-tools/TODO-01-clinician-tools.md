---
schema_version: 1
id: clinician-tools
domain: 05-tools
status: active
title: "TODO-01 -- Modes and clinician tools"
track: M5
---

# TODO-01 -- Modes and clinician tools

> **Goal:** One app serves both audiences: a patient sees a plain viewer with nothing to get wrong, and a clinician switches on measurements, multi-viewport layouts, a tag browser and image export, with every tool reversible and every measurement honest about its accuracy.

> **Current state:** Measured 2026-11-17. No code exists. The 2D view, toolbar, overlay and settings file come from D02 T01, the MPR layout from D03 T01 §3 and the 3D view from D04 T01. The owner decided on 2026-11-16 that both clinicians and patients use Voxel (`docs/plans/2026-11-17-voxel-tech-stack.md`, "Decisions the owner made").

## Inputs

- `docs/plans/2026-11-17-voxel-tech-stack.md`: "Decisions the owner made" (one app with a plain mode and a clinician mode) and "Out of scope for version 1" (no reporting, no PACS).
- `design/SPEC.md`, `design/contract/` and `design/screens/`: the approved interface. Every control named in this file is registered once in `src/ui/controls.rs` and every panel once in `src/ui/panels.rs` (D02 T02 §2), and is drawn by whichever of the three interfaces is active. Where a section says toolbar, read the interface's tool area: the toolbar in Workstation, the dock in Lightbox, the rail or an inspector panel in Console. Placement, size and look are fixed by the contract, not by this file.
- `src/ui/toolbar.rs`, `src/ui/viewport.rs`, `src/ui/view_state.rs` and `src/ui/overlay.rs` from D02 T01 §2, §5 and §6.
- `src/settings.rs` from D02 T01 §7, which §1 and §5 extend.
- -> XREF: D02 T02 §2 -- the control registry the mode table of §1 is part of
- `src/dicom/image.rs` (`pixel_spacing_mm`, `spacing_source`) from D01 T01 §1, which decides what a measurement may claim.
- `src/ui/mpr.rs` from D03 T01 §3 and `src/ui/view3d.rs` from D04 T01 §1.

## Outcome

- Voxel starts in plain mode; clinician mode is one switch, remembered across restarts.
- Length and angle measurements on 2D and MPR views, in millimetres when the spacing is known and never in millimetres when it is not.
- Measurements can be selected, deleted, cleared and undone.
- Layouts of 1, 2 or 4 viewports with linked scrolling between series of the same study.
- A searchable browser of every DICOM tag of the image on screen.
- The current view exported as a PNG, without patient details unless the user asks for them.

**Adjacency:** list=applicable; document=applicable; settings=applicable; reporting=not-applicable (no summaries over studies in version 1); notifications=not-applicable (a local viewer notifies nobody); permissions=not-applicable (no access control in a local viewer); audit=not-applicable (measurements live for the session and are never written to the study); exchange=applicable; reverse=applicable

**Adjacency rationale:** The list is the tag browser's search in §6: a tag is found by name without knowing its number. The document is the exported PNG of §7, which is also the exchange (export). Settings are the mode (§1) and the layout (§5), each with a named consumer. Reverse is §4: every measurement created can be deleted, and the last action undone.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | Plain mode and clinician mode | D02 T01 §6, D02 T01 §7, D03 T01 §4, D04 T01 §3 | [ ] |
| 2 | §2 | Length measurement in millimetres | §1 | [ ] |
| 3 | §3 | Angle measurement | §2 | [ ] |
| 4 | §4 | Measurement selection, delete, clear and undo | §3 | [ ] |
| 5 | §5 | Viewport layouts with linked scrolling | §1 | [ ] |
| 6 | §6 | DICOM tag browser with search | §1 | [ ] |
| 7 | §7 | Current view exported as a PNG | §4 | [ ] |

## 1. Plain mode and clinician mode

A patient opening their own scan needs four things: see the image, scroll, change brightness, zoom. Everything else is noise to them and a tool to a clinician. The mode decides which controls are shown; it never changes what the image looks like or what the gestures do.

**Phase:** 5
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** have a viewer as simple or as capable as the person using it needs
**Treatment:** plain mode shows the image, the series strip and a short toolbar (Open, Fit, Reset, Brightness presets); clinician mode adds MPR, 3D, measurement tools, layouts, the tag browser, Export and the full overlay
**Chrome:** a mode switch at the right end of the toolbar labelled "More tools" (off is plain mode); a first-run hint points at it once

**Build order:**

1. Define the mode and which controls each mode shows in `src/ui/mode.rs`. Done when: a unit test lists the controls per mode.
2. Persist the mode and apply it in `src/ui/toolbar.rs`. Done when: a restart keeps the chosen mode.

- [ ] Define `Mode` (Plain, Clinician) in `src/ui/mode.rs` with one table naming every toolbar control and panel and the modes it appears in. Done when: a unit test asserts Plain shows Open, Fit, Reset, the brightness presets and the mode switch, and nothing else.
- [ ] Build the toolbar in `src/ui/toolbar.rs` from that table, so a control added later must be placed in it. Done when: a test asserts every control the toolbar draws is in the table. Cheaper substitute: hiding clinician controls with a separate `if` beside each must fail review; the table is the one source.
- [ ] Add `mode` to `Settings` in `src/settings.rs`, defaulting to Plain, saved when the switch changes. Done when: a test switches to Clinician, loads a fresh `Settings` and reads Clinician.
- [ ] Add the brightness presets Lighter, Darker and Auto to the plain toolbar in `src/ui/toolbar.rs`, each changing the window through `ViewState`. Done when: unit tests assert Auto equals the image's default window and Lighter lowers the window centre.
- [ ] Keep the keyboard shortcuts of clinician tools inactive in Plain mode in `src/ui/mode.rs`. Done when: a test presses M in Plain mode and the layout does not change.
- [ ] Switch a view that Plain mode does not show (MPR, 3D, a multi-viewport layout) back to the single stack view when the mode changes to Plain, in `src/ui/mode.rs`. Done when: a test turns the switch off while in MPR and lands in the stack view.
- [ ] Show the first-run hint once in `src/ui/mode.rs`, recorded in `Settings` as `hint_seen`. Done when: a test sees the hint on a first start and not on the second.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `empty`, `xray`, `stack` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `ui: plain mode and clinician mode`

**Test checkpoint:** `cargo test mode` passes; adding a toolbar control without a row in the mode table fails the table test.

## 2. Length measurement in millimetres

The most used clinical tool, and the one most able to mislead. A length is only in millimetres when the file says how large a pixel is in the patient, and on a projection X-ray the spacing is measured at the detector, where the anatomy is magnified. The tool states which case applies instead of printing a number that looks exact.

**Phase:** 5
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** measure the distance between two points on the image
**Treatment:** a thin line with small end handles and a label beside its midpoint: "42.3 mm", "42.3 mm at detector" or "311 px"
**Chrome:** a Length tool button in the clinician toolbar (key L); the cursor becomes a crosshair while the tool is active; Esc returns to the default pointer

**Build order:**

1. Define the measurement model and the length calculation in `src/ui/measure.rs`. Done when: unit tests cover the three label cases.
2. Add the tool and its drawing in `src/ui/viewport.rs`. Done when: a drag on a phantom reads the true length.

- [ ] Define `Measurement::Length` in `src/ui/measure.rs` with its two end points stored in image pixel coordinates (in patient millimetres for MPR views), attached to its series and slice. Done when: `cargo build` exits 0 and a unit test asserts the points do not change when the view zooms.
- [ ] Write `length_label` in `src/ui/measure.rs`: millimetres from `pixel_spacing_mm` honouring different row and column spacing; the suffix "at detector" when `spacing_source` is `ImagerPixelSpacing`; pixels with the unit "px" when no spacing exists. Done when: unit tests assert the three labels, including a 3-4-5 triangle on a 1 by 2 mm image. Cheaper substitute: assuming 1 mm pixels when the spacing is missing must fail the "px" test.
- [ ] Add the Length tool to `src/ui/viewport.rs`: press sets the first point, drag shows the line and live label, release finishes it, Esc while dragging cancels it. Done when: `tests/measure.rs` drags across the sphere phantom's diameter and reads the true diameter within one pixel's spacing.
- [ ] Draw each measurement in `src/ui/viewport.rs` only on the slice it was made on, with a line width and label size that stay constant on screen at any zoom. Done when: a test asserts the measurement is absent one slice away and its on-screen width is unchanged after zooming.
- [ ] Measure in MPR views in `src/ui/mpr.rs` using the plane's patient coordinates. Done when: a test measures the anisotropic sphere's diameter in the coronal plane and reads the true value.
- [ ] Add the Length button to the mode table in `src/ui/mode.rs` (Clinician only) with key L, and keep the tool unavailable in the 3D view, where a distance on screen is not a distance in the patient. Done when: a test asserts the button is disabled with the tooltip "Not available in 3D" while the 3D view is open.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `stack` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `tools: length measurement`

**Test checkpoint:** `cargo test measure` and `cargo test --test measure` pass; treating missing spacing as 1 mm fails the "px" label test.

## 3. Angle measurement

The second standard tool: the angle between two lines meeting at a point, used for alignment and joint angles. It shares the model, drawing and coordinate handling of the length tool.

**Phase:** 5
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** measure the angle between two structures
**Treatment:** two thin lines from a shared vertex with a small arc and a label in degrees to one decimal place
**Chrome:** an Angle tool button beside Length in the clinician toolbar (key A)

**Build order:**

1. Add `Measurement::Angle` and its calculation to `src/ui/measure.rs`. Done when: unit tests cover known angles.
2. Add the three-click tool in `src/ui/viewport.rs`. Done when: a test places three points and reads the angle.

- [ ] Add `Measurement::Angle` (three points: end, vertex, end) to `src/ui/measure.rs` and `angle_degrees`, computed in millimetres so different row and column spacing does not distort it, and in pixels when no spacing exists. Done when: unit tests assert 90 degrees for a right angle on a 1 by 2 mm image, and 0 to 180 as the range.
- [ ] Add the Angle tool to `src/ui/viewport.rs`: three clicks place end, vertex, end, with a live preview after the first; Esc cancels. Done when: `tests/measure.rs` places three points on the `three_rods()` phantom and reads 90.0 between two rods.
- [ ] Draw the arc and label in `src/ui/viewport.rs`, placing the label outside the arc so it never covers the vertex. Done when: a test asserts the label's rectangle does not contain the vertex for acute and obtuse angles.
- [ ] Add the Angle button to the mode table in `src/ui/mode.rs` (Clinician only) with key A, unavailable in 3D like Length. Done when: a test asserts the button states in 2D, MPR and 3D.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `stack` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `tools: angle measurement`

**Test checkpoint:** `cargo test measure` and `cargo test --test measure` pass; computing the angle in pixel units on the 1 by 2 mm image fails the right-angle test.

## 4. Measurement selection, delete, clear and undo

Every create needs its reverse. A misplaced measurement must be movable and removable, and a mistaken delete recoverable, or the tools are a trap.

**Phase:** 5
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** fix or remove a measurement, and take back the last change
**Treatment:** a selected measurement is drawn brighter with larger handles
**Chrome:** Delete removes the selection; a Clear Measurements button in the clinician toolbar; Ctrl+Z and Ctrl+Y undo and redo

**Build order:**

1. Add selection, edit and an undo stack to `src/ui/measure.rs`. Done when: unit tests cover each operation and its undo.
2. Wire the keys and the button. Done when: the end-to-end test passes.

- [ ] Add `MeasurementSet` in `src/ui/measure.rs` holding the session's measurements per series, with `select` by hit-test within 6 screen pixels of a line or handle. Done when: a unit test selects the nearer of two overlapping measurements.
- [ ] Add handle dragging to `MeasurementSet` in `src/ui/measure.rs` so an end point or vertex can be moved, with the label updating live. Done when: a test drags a length's end point and reads the new length.
- [ ] Add an undo stack to `MeasurementSet` covering create, move, delete and clear, with redo, capped at 100 steps. Done when: unit tests assert each operation is undone and redone exactly, and that a new action clears the redo stack.
- [ ] Bind Delete, Ctrl+Z and Ctrl+Y in `src/ui/viewport.rs` and add Clear Measurements to the mode table in `src/ui/mode.rs`, disabled when the series has none. Done when: `tests/measure.rs` creates two measurements, clears, undoes, and finds both back. Cheaper substitute: a clear that cannot be undone must fail this test.
- [ ] Keep measurements when the user changes slice, series or layout and comes back, and drop them when the study is closed, in `src/ui/measure.rs`. Done when: a test leaves a series, returns and finds its measurements, then opens another study and finds none.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `stack` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `tools: measurement select, delete, clear and undo`

**Test checkpoint:** `cargo test measure` and `cargo test --test measure` pass; removing clear from the undo stack fails the clear-and-undo test.

## 5. Viewport layouts with linked scrolling

Clinicians compare: two sequences of the same anatomy side by side, scrolling together. Linking is by position in the patient, not by slice number, because two series rarely have the same slice count.

**Phase:** 5
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** look at two or four series at once and scroll them together
**Treatment:** the viewport area splits into equal panes with a thin divider; the active pane has a coloured border; each pane has its own overlay
**Chrome:** a Layout drop-down in the clinician toolbar (1, 1 by 2, 2 by 1, 2 by 2) and a Link Scrolling toggle (key K); a series card dropped on a pane opens there

**Build order:**

1. Write the layout model in `src/ui/layout.rs`. Done when: unit tests cover pane counts and the active pane.
2. Add linked scrolling by patient position in `src/ui/link.rs`. Done when: two phantoms with different slice counts stay aligned.

- [ ] Define `Layout` in `src/ui/layout.rs` (1, 1 by 2, 2 by 1, 2 by 2) holding one viewport state per pane and the active pane, with a click making a pane active and toolbar actions applying to it. Done when: unit tests assert pane counts and that Reset affects only the active pane.
- [ ] Open a series in a pane in `src/ui/layout.rs` by clicking a card (active pane) or dragging a card onto a pane. Done when: a test drops the second card on the second pane and both panes show different series.
- [ ] Write `linked_slice` in `src/ui/link.rs`: given the active pane's slice position in patient space, pick in each other pane the slice of its series nearest that position along its own normal, only for series whose normals are within 10 degrees. Done when: a test with a 20-slice and a 40-slice phantom covering the same range scrolls one and finds the other at the nearest position. Cheaper substitute: linking by slice index must fail this test.
- [ ] Add the Link Scrolling toggle to the mode table in `src/ui/mode.rs` with key K, and a small link mark in each linked pane's overlay in `src/ui/overlay.rs`; a pane whose series is not parallel shows the mark struck through. Done when: a test asserts the marks for a parallel and a perpendicular pair.
- [ ] Add `layout` and `link_scrolling` to `Settings` in `src/settings.rs`, with the Layout drop-down as the control. Done when: a test sets 1 by 2, loads a fresh `Settings` and reads 1 by 2.
- [ ] Keep each pane's series when the layout grows, and keep the active pane's series when it shrinks, in `src/ui/layout.rs`. Done when: a test going 2 by 2 to 1 keeps the active pane's series on screen.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `layout` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `tools: viewport layouts with linked scrolling`

**Test checkpoint:** `cargo test layout` and `cargo test link` pass; linking panes by slice index fails the 20 and 40 slice test.

## 6. DICOM tag browser with search

When an image looks wrong, or a clinician needs an acquisition parameter, the answer is in the file's tags. The browser shows all of them for the image on screen, by name, searchable.

**Phase:** 5
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** find a piece of information stored in the image file, such as the echo time or the slice thickness
**Treatment:** a side panel on the right with a search box and a table of tag number, name, type and value; sequences expand as nested rows
**Chrome:** a Tags button in the clinician toolbar (key T) toggling the panel; a copy-value action on each row

**Build order:**

1. Read every element of the current image's file into rows in `src/dicom/tags.rs`. Done when: a corpus file yields the expected rows.
2. Write the panel in `src/ui/tag_panel.rs`. Done when: search filters the rows.

- [ ] Write `tag_rows(path, frame)` in `src/dicom/tags.rs`: every element with its tag, its name from `dicom-dictionary-std` ("Private tag" when unknown), its value representation and a display value, with sequences as nested rows and the pixel data shown as its length only. Done when: `tests/tags.rs` asserts the `PatientName`, `Modality` and `Rows` rows of a corpus file.
- [ ] Shorten long values in `tag_rows` to 200 characters with the full length noted, and render binary values as a byte count. Done when: a test asserts a long value is shortened and marked.
- [ ] Write `TagPanel` in `src/ui/tag_panel.rs` with a search box filtering by name, tag number or value, case-insensitive, and a count of matching rows. Done when: a test types "echo" and sees only rows whose name or value contains it. Cheaper substitute: a filter that searches names only must fail a test that searches for a value.
- [ ] Reload the rows in `TagPanel` when the slice or the active pane changes, off the interface thread. Done when: a test scrolls one slice and the `InstanceNumber` row changes.
- [ ] Add the copy-value action to each row in `src/ui/tag_panel.rs` and the Tags button to the mode table in `src/ui/mode.rs` with key T. Done when: a test copies a row and reads its full value from the clipboard, not the shortened one.
- [ ] Show "No file open" in `TagPanel` when nothing is open, and the `LoadError` message when the file cannot be read. Done when: a test asserts both states.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `tags` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `tools: DICOM tag browser with search`

**Test checkpoint:** `cargo test --test tags` and `cargo test tag_panel` pass; searching names only fails the value-search test.

## 7. Current view exported as a PNG

Users want to keep or send a picture: a patient to show a relative, a clinician for a presentation. The export is exactly what is on screen, and it leaves patient details out unless the user asks for them, because a picture travels further than its owner intends.

**Phase:** 5
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** save the current view as a picture
**Treatment:** the exported PNG shows the active pane as displayed, with its window, zoom, measurements and orientation letters
**Chrome:** an Export button in the clinician toolbar (Ctrl+E) opening a native Save dialog, with a checkbox "Include patient details", off by default

**Build order:**

1. Render the active pane to an offscreen target and encode it in `src/export.rs`. Done when: an exported PNG decodes to the expected pixels.
2. Add the dialog, the checkbox and the refusal paths in `src/ui/toolbar.rs`. Done when: the tests pass.

- [ ] Write `export_png(pane, options, path)` in `src/export.rs`: render the active pane at its on-screen size through the same renderer to an offscreen target, read it back and encode it with the `png` crate, added to `Cargo.toml` and `docs/dependencies.md` with the new exe size. Done when: `tests/export.rs` exports a ramp phantom view and decodes the file to the same pixels as the read-back of the view. Cheaper substitute: a screenshot of the window must fail; the export has no toolbar and no neighbouring panes.
- [ ] Leave the patient name, patient ID and dates out of the exported overlay in `src/export.rs` unless `options.include_patient_details` is set, keeping the orientation letters and measurements either way. Done when: a test exports with the option off and finds no pixel difference in the name's corner against a render with the overlay text removed, and a difference with the option on.
- [ ] Write the PNG with no text metadata chunks in `src/export.rs`. Done when: a test parses the file's chunks and finds no `tEXt`, `iTXt` or `zTXt`.
- [ ] Write the file to a temporary name beside the target and rename it in `src/export.rs`, returning a named error when the folder is read-only or the disk is full. Done when: a test exporting into a read-only folder gets the error and finds no partial file.
- [ ] Add the Export button to the mode table in `src/ui/mode.rs` with Ctrl+E, the native Save dialog through `rfd` suggesting a name without the patient name (`voxel-<modality>-<date exported>.png`), and a short confirmation line naming the saved file. Done when: a test exports and reads the confirmation with the path. Cheaper substitute: a suggested file name containing the patient name must fail a test on the suggestion.
- [ ] Show the export error as one plain sentence in the toolbar's status line in `src/ui/toolbar.rs`. Done when: a test with the read-only folder sees the sentence.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `export` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `tools: export the current view as a PNG`

**Test checkpoint:** `cargo test --test export` passes; drawing the patient name with the option off fails the corner-pixel test.

## Verification

- A first start shows plain mode; switching on "More tools" adds every clinician control, and the choice survives a restart.
- On the sphere phantom a length reads the true diameter in 2D and MPR, an X-ray length carries "at detector", and an image without spacing reads in "px".
- Create, move, delete, clear, undo and redo all work on measurements in a 1 by 2 layout with linked scrolling.
- An exported PNG holds no patient details unless asked for.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
