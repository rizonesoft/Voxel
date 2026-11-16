---
schema_version: 1
id: image-view-2d
domain: 02-viewer
status: active
title: "TODO-01 -- 2D image view"
track: M1
---

# TODO-01 -- 2D image view

> **Goal:** A user double-clicks a DICOM file, or drops a file or folder on Voxel, and sees the image in under a second; they adjust brightness and contrast, zoom and pan, scroll through an MRI series and pick another series from a strip, and every one of those responds on the next frame.

> **Current state:** Measured 2026-11-17. No code exists. The empty window and the GPU adapter choice come from D00 T01 §3, and the image model, refusals, scan and background loader from D01 T01. There is no design SPEC: the surfaces below are specified in each section's Fidelity, Job, Treatment and Chrome lines.

## Inputs

- `docs/plans/2026-11-17-voxel-tech-stack.md`: "How each view works" (2D), "Targets" (first image under 1 second; window/level every frame) and "Source layout (planned)" (`src/render/`, `src/ui/`).
- `src/dicom/image.rs`, `src/dicom/error.rs`, `src/dicom/scan.rs` and `src/dicom/loader.rs` from D01 T01 §1 to §4.
- `src/app.rs` and `src/render/gpu.rs` from D00 T01 §3.
- The DICOM standard, PS3.3 C.11.2 (the VOI LUT linear window function), for the window/level formula in §1.

## Outcome

- An image is drawn from its stored 16-bit values with rescale, window/level and invert applied in `src/render/shaders/image2d.wgsl`, proved by pixel read-back.
- Mouse and keyboard control window/level, zoom, pan, fit and reset.
- A file or folder opens from the command line, a drop, or Ctrl+O, and a refusal shows one plain sentence.
- `scripts/measure-start.ps1` reports double-click to first image, checked against the 1 second target.
- A series strip lists every series with a thumbnail, and the wheel scrolls the stack.
- Window size and the last folder survive a restart.

**Adjacency:** list=applicable; document=not-applicable (export of a view is D05 T01 §7); settings=applicable; reporting=not-applicable (no summaries over studies in version 1); notifications=not-applicable (a local viewer notifies nobody); permissions=not-applicable (file access refusals are D01 T01 §2, shown by §3 here); audit=not-applicable (viewing changes nothing to audit); exchange=not-applicable (import is D01 T01; export is D05 T01 §7); reverse=applicable

**Adjacency rationale:** The list is the series strip in §5: a user finds a series by its thumbnail and description, never by a file name. Settings are owned by §7, with the window and the Open dialog as named consumers. Reverse is the reset in §2: every view change (window/level, zoom, pan, invert) is undone by one double-click or the R key.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | 16-bit image texture and the window/level shader | D00 T01 §3, D01 T01 §1 | [ ] |
| 2 | §2 | Zoom, pan, invert, fit and reset | §1 | [ ] |
| 3 | §3 | Open by argument, drag and drop, and the Open dialog | §1, D01 T01 §2 | [ ] |
| 4 | §4 | Start time measured against the one second target | §3 | [ ] |
| 5 | §5 | Series strip and stack scrolling | §3, D01 T01 §4, D01 T01 §5 | [ ] |
| 6 | §6 | Image information overlay and orientation markers | §5 | [ ] |
| 7 | §7 | Settings file for window size and last folder | §3 | [ ] |

## 1. 16-bit image texture and the window/level shader

This is the core of the 2D view and of the "fast" claim: the stored values go to the GPU once, and brightness and contrast are a pair of numbers the shader reads each frame. Converting the image to 8-bit on the CPU would make every adjustment a re-render of millions of pixels and would throw away the detail a radiograph holds.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Write `ImageTexture` in `src/render/image2d.rs` and the shader `src/render/shaders/image2d.wgsl`. Done when: an offscreen render of a ramp image matches the expected grey values.
2. Test window, rescale, invert and colour in `tests/render_image2d.rs` by pixel read-back. Done when: every case passes on the real adapter and on WARP.

- [ ] Write `ImageTexture::upload(image)` in `src/render/image2d.rs`: create an `R16Uint` texture for `PixelData::U16`, `R16Sint` for `I16` and `Rgba8Unorm` for `Rgb8`, sized to the image, uploading the stored values unchanged. Done when: a test reads the texture back and gets the stored values. Cheaper substitute: an 8-bit texture must fail; the read-back asserts a value above 255.
- [ ] Split an image wider or taller than the adapter's `max_texture_dimension_2d` into tiles in `ImageTexture::upload`. Done when: a synthetic 20000 by 100 image uploads and renders with no seam in the read-back row.
- [ ] Write `src/render/shaders/image2d.wgsl`: read the four nearest texels with `textureLoad`, apply `value * slope + intercept`, blend bilinearly, apply the linear window function of PS3.3 C.11.2.1.2 with the centre and width from a uniform, and invert when the uniform says so. Done when: `tests/render_image2d.rs` renders a 0 to 4095 ramp with window centre 2048 and width 4096 and reads back a 0 to 255 ramp within one grey level.
- [ ] Add tests in `tests/render_image2d.rs` for a narrow window (values below the window read 0, above read 255), for a negative `rescale_intercept` on signed data, and for `invert`. Done when: all three pass, and each fails when its term is removed from the shader.
- [ ] Draw `Rgb8` images in `image2d.wgsl` without window/level. Done when: a colour corpus file renders with its top-left pixel colour read back unchanged.
- [ ] Draw the image in an `egui` paint callback from `src/ui/viewport.rs`, keeping the pixel aspect ratio from `pixel_spacing_mm` when the two spacings differ. Done when: a phantom with 1 by 2 mm pixels renders a circle as a circle in the read-back.
- [ ] Run `tests/render_image2d.rs` a second time with `VOXEL_FORCE_WARP=1`. Done when: the same assertions pass on the software adapter.
- [ ] Commit: `render: 16-bit image texture and window/level shader`

**Test checkpoint:** `cargo test --test render_image2d` passes with and without `VOXEL_FORCE_WARP=1`; removing the rescale term from `image2d.wgsl` fails the signed-data test.

## 2. Zoom, pan, invert, fit and reset

The controls a patient and a clinician both expect, each changing only shader uniforms or the view transform so the response is immediate. The mapping follows what most DICOM viewers use, so a clinician's habits carry over.

**Phase:** 1
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** functional; no design SPEC exists, so behaviour is specified here and the look is the `egui` default
**Job:** make the image brighter or darker, look closer at a detail, and get back to the starting view
**Treatment:** the image fills the viewport on black; no control sits on top of the image
**Chrome:** a slim toolbar above the viewport with Invert, Fit and Reset buttons, each with a tooltip naming its key

**Build order:**

1. Write the view state and its input handling in `src/ui/view_state.rs`. Done when: unit tests cover each gesture's effect on the state.
2. Wire the toolbar in `src/ui/toolbar.rs` and prove one gesture end to end with a read-back. Done when: the zoom test renders the expected pixel under the cursor.

- [ ] Define `ViewState` in `src/ui/view_state.rs` with window centre and width, zoom, pan offset, invert, and `reset()` returning to the image's default window and a fit-to-viewport zoom. Done when: a unit test asserts `reset()` after arbitrary changes equals the initial state.
- [ ] Map left-drag in `src/ui/view_state.rs` to window/level: horizontal changes width, vertical changes centre, scaled by the image's value range so a full-width drag covers the range. Done when: a unit test asserts a 100 pixel right drag widens the window and never produces a width below 1.
- [ ] Map Ctrl+wheel and right-drag to zoom about the cursor, and middle-drag or Space+left-drag to pan, in `src/ui/view_state.rs`, with zoom limited to 0.05 to 40. Done when: a unit test asserts the image point under the cursor is the same before and after a zoom step.
- [ ] Add the keys I (invert), F (fit), 1 (one image pixel per screen pixel) and R (reset), and double-click as reset, in `src/ui/view_state.rs`. Done when: unit tests assert each key's effect.
- [ ] Write the toolbar in `src/ui/toolbar.rs` with Invert, Fit and Reset buttons that call the same functions as the keys. Done when: a test driving the `egui` context clicks Reset and observes the reset state. Cheaper substitute: a button with its own copy of the reset logic must fail review; keys and buttons share one function.
- [ ] Disable the toolbar buttons and ignore the gestures when no image is open, in `src/ui/toolbar.rs` and `src/ui/view_state.rs`. Done when: a test with no image asserts the buttons are disabled and a drag changes nothing.
- [ ] Add `tests/view_gestures.rs`: render an image, apply a zoom of 2 about a known point through `ViewState`, and read back that the same image pixel is still under the cursor. Done when: the test passes and fails if zoom is applied about the viewport centre instead.
- [ ] Commit: `viewer: zoom, pan, invert, fit and reset`

**Test checkpoint:** `cargo test view_state` and `cargo test --test view_gestures` pass; zooming about the viewport centre instead of the cursor fails the gesture test.

## 3. Open by argument, drag and drop, and the Open dialog

Three ways in, one code path. The command-line argument is what a double-click in Explorer uses once the file association exists (D06 T01 §3), so it is the path the speed target is measured on. A refusal from D01 T01 §2 becomes one plain sentence in the window, never a crash and never a silent blank.

**Phase:** 1
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** functional; no design SPEC exists, so behaviour is specified here and the look is the `egui` default
**Job:** get a study on screen from wherever it is: a double-clicked file, a dragged folder, or a disc
**Treatment:** while loading, the file name and a thin progress line; on refusal, the plain sentence centred where the image would be, with the file name under it
**Chrome:** an Open button first in the toolbar (Ctrl+O) with a menu of Open File and Open Folder; the Windows title bar shows the file or folder name

**Build order:**

1. Write `open_path` in `src/app.rs` and call it from the argument, the drop handler and the dialog. Done when: all three reach the same function.
2. Show refusals and test the argument path end to end in `tests/open_paths.rs`. Done when: the tests pass.

- [ ] Write `App::open_path(path)` in `src/app.rs`: a file loads through `load_image` at once and its folder is scanned in the background; a folder or `DICOMDIR` is scanned and its first series opened. Done when: `tests/open_paths.rs` opens a corpus file through `open_path` and asserts an image is set within the test's time limit.
- [ ] Parse the first command-line argument as a path in `src/main.rs` and pass it to `open_path` before the first frame is drawn. Done when: `target/debug/voxel.exe <corpus file>` shows the image as the first thing drawn, with no empty-state frame in between. Cheaper substitute: opening the file after the window is shown must fail the measurement in §4.
- [ ] Handle a dropped file or folder in `src/app.rs` through `egui`'s dropped-files input, taking the first item when several are dropped. Done when: a test that injects a dropped-file event reaches `open_path` with that path.
- [ ] Add the Open button with Open File and Open Folder in `src/ui/toolbar.rs`, using the native Windows dialogs through the `rfd` crate, bound to Ctrl+O and Ctrl+Shift+O. Done when: choosing a corpus file in the dialog shows it, and cancelling the dialog changes nothing.
- [ ] Show `LoadError::user_message()` or `ScanError`'s message in `src/ui/viewport.rs` in place of the image when `open_path` fails, keeping the previous study closed. Done when: `tests/open_paths.rs` opens a text file and asserts the viewport state is the refusal with the `NotDicom` message. Cheaper substitute: a message box that blocks the window must fail; the refusal lives in the viewport.
- [ ] Show the file name and a progress line in `src/ui/viewport.rs` while a load is in flight, and cancel that load when another path is opened. Done when: a test that opens a second path during a slow phantom load ends with the second image and no result from the first.
- [ ] Commit: `viewer: open by argument, drop and dialog`

**Test checkpoint:** `cargo test --test open_paths` passes; routing the drop handler around `open_path` fails the dropped-file test.

## 4. Start time measured against the one second target

"Fast-opening" is the product, so it gets a number and a measurement instead of an impression. The target in the foundation plan is under 1 second from process start to the first image drawn, for a typical X-ray on an SSD.

**Phase:** 1
**Needs:** windows-host, display-session
**Surface:** no

**Build order:**

1. Log the time from process start to the first image frame in `src/app.rs`. Done when: the log line appears once per start.
2. Write `scripts/measure-start.ps1` and record the result in `docs/performance.md`. Done when: the file holds the measured median.

- [ ] Record `std::time::Instant` at the top of `main` in `src/main.rs` and log `first-image: <ms>` in `src/app.rs` after the first frame that draws an image has been presented. Done when: a start with a file argument logs the line exactly once.
- [ ] Add a `--exit-after-first-image` argument in `src/main.rs` that closes the app after that frame, for measurement only. Done when: the process exits with code 0 and the log line is present.
- [ ] Write `scripts/measure-start.ps1`: build release, start `target/release/voxel.exe <file> --exit-after-first-image` 10 times after one warm-up, read each log line, and print the median and the slowest. Every child it starts is stopped with its process tree on a 30 second timeout. Done when: the script prints two numbers for a corpus X-ray file.
- [ ] Record the median, the slowest, the file, the machine and the date in `docs/performance.md`. Done when: the file is committed with the measured values.
- [ ] If the median is 1000 ms or more, profile the start with the log's phase timestamps (process start, window, GPU device, file read, decode, upload, first frame) and remove the largest cost in the layer that owns it. Done when: the median in `docs/performance.md` is under 1000 ms, or the file names the cost that cannot be removed and why. Cheaper substitute: a splash image drawn early while the real image loads must fail; the measured frame is the real image.
- [ ] Commit: `perf: start time measured against the target`

**Test checkpoint:** `pwsh scripts/measure-start.ps1` prints a median under 1000 ms for the corpus X-ray file; adding a 2 second sleep before `open_path` makes it print a median over 1000 ms and exit non-zero.

## 5. Series strip and stack scrolling

An MRI study is several series of slices. The strip is how a user finds the series they want without knowing any identifier, and the wheel is how they move through it. Scrolling must stay smooth while slices are still being decoded.

**Phase:** 2
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** functional; no design SPEC exists, so behaviour is specified here and the look is the `egui` default
**Job:** see every series in the study, pick one, and scroll through its slices
**Treatment:** a vertical strip on the left, one card per series with a thumbnail of its middle slice, the series description, the modality and the image count; the open series is outlined
**Chrome:** the strip is resizable and collapses with Tab; a slice slider runs down the right edge of the viewport for series with more than one image

**Build order:**

1. Write the strip in `src/ui/series_strip.rs` over the scan result. Done when: a scanned corpus folder shows one card per series.
2. Write stack scrolling in `src/ui/viewport.rs` over `SeriesLoader`. Done when: the wheel changes the slice and the loader is reprioritised.

- [ ] Write `SeriesStrip` in `src/ui/series_strip.rs`: one card per `Series` grouped under its study, with description, modality and image count, in series number order. Done when: a test over a two-series scan asserts two cards with the right counts.
- [ ] Generate each card's thumbnail in `src/ui/series_strip.rs` by decoding the middle image in the background and downscaling it to 128 pixels with its default window. Done when: cards appear at once with a placeholder and gain thumbnails without blocking a frame. Cheaper substitute: decoding thumbnails on the interface thread must fail; a test asserts no frame takes over 50 ms while thumbnails load for a 20-series phantom study.
- [ ] Open a series in the viewport on a card click or Enter, starting `SeriesLoader` at its middle image, in `src/ui/series_strip.rs`. Done when: a test clicks the second card and the viewport's series is the second.
- [ ] Map the wheel, the Up and Down keys, Page Up, Page Down, Home and End to slice changes in `src/ui/viewport.rs`, calling `SeriesLoader::reprioritise` for the new slice. Done when: unit tests assert each input's new index, clamped to the series.
- [ ] Draw the nearest loaded slice with a "loading" mark in `src/ui/viewport.rs` when the wanted slice is not decoded yet, and swap to it when it arrives. Done when: a test with a slow phantom loader shows the mark and then the wanted slice. Cheaper substitute: blocking the frame until the slice decodes must fail the 50 ms frame assertion.
- [ ] Keep the window/level, zoom and pan when the slice changes, and reset them when the series changes, in `src/ui/view_state.rs`. Done when: unit tests assert both.
- [ ] Add the slice slider in `src/ui/viewport.rs`, hidden for single-image series, and on single images make the plain wheel zoom. Done when: a test asserts the slider is absent for an X-ray and present for the phantom series.
- [ ] Show the per-slice `LoadError` message in place of a slice that failed to decode, with scrolling still working past it, in `src/ui/viewport.rs`. Done when: a series with one truncated file scrolls across it and shows the message on that slice only.
- [ ] Commit: `viewer: series strip and stack scrolling`

**Test checkpoint:** `cargo test series_strip` and `cargo test --test stack_scroll` pass; decoding on the interface thread fails the 50 ms frame assertion.

## 6. Image information overlay and orientation markers

A viewer that shows an image without saying whose it is, or which side is left, is unsafe to use even for review. The overlay puts the identifying text in the corners and the orientation letters on the edges, the convention every DICOM viewer follows.

**Phase:** 2
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** functional; no design SPEC exists, so the corner layout follows the common DICOM viewer convention
**Job:** know whose image this is, when it was taken, which slice is showing and which way is left
**Treatment:** small light text with a dark outline in the four corners of the viewport, and single letters (L, R, A, P, H, F) centred on the four edges
**Chrome:** an overlay toggle in the toolbar (key O) cycling full, minimal and off

**Build order:**

1. Compute the overlay text and the edge letters in `src/ui/overlay.rs`. Done when: unit tests cover the text and the letters.
2. Draw them in the viewport and add the toggle. Done when: the toggle cycles the three states.

- [ ] Write `overlay_text(study, series, image, view)` in `src/ui/overlay.rs`: patient name and ID top left; study date and series description top right; slice number of count, and zoom bottom left; window centre and width bottom right. Done when: a unit test asserts the four strings for a phantom image, with DICOM person names (`Family^Given`) shown as "Family, Given".
- [ ] Write `edge_letters(orientation)` in `src/ui/overlay.rs` from `ImageOrientationPatient`, giving the letter at each viewport edge, and nothing when the tag is absent. Done when: unit tests assert the letters for axial, coronal and sagittal orientations and for a missing tag. Cheaper substitute: fixed letters per modality must fail; the test uses a flipped axial orientation.
- [ ] Draw the overlay in `src/ui/viewport.rs` so it stays fixed while the image zooms and pans. Done when: a test asserts the text positions are unchanged after a zoom.
- [ ] Add the overlay toggle to `src/ui/toolbar.rs` and the O key, cycling full, minimal (letters, slice number) and off. Done when: a test presses O three times and sees the three states in order.
- [ ] Show a "Lossy compressed" note in the overlay when `LossyImageCompression` (0028,2110) is `01`. Done when: a lossy JPEG corpus file shows the note and a lossless file does not.
- [ ] Commit: `viewer: information overlay and orientation markers`

**Test checkpoint:** `cargo test overlay` passes; swapping the row and column direction in `edge_letters` fails the flipped-axial test.

## 7. Settings file for window size and last folder

The first persisted state in the app, and the one file every later setting (3D quality, mode, layout) is added to. It must never lose the user's settings to a crash halfway through a write, and a damaged file must not stop the app starting.

**Phase:** 2
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Write `Settings` with load and atomic save in `src/settings.rs`. Done when: the round-trip and damaged-file tests pass.
2. Wire the two first consumers in `src/app.rs` and `src/ui/toolbar.rs`. Done when: a restart restores the window size.

- [ ] Define `Settings` in `src/settings.rs` (window width, height and maximised; last opened folder; a `version` number) stored as TOML at `%APPDATA%\Voxel\settings.toml`, with every field defaulted so older files load. Done when: a unit test loads an empty file and gets the defaults.
- [ ] Write `Settings::save` in `src/settings.rs` to write a temporary file beside the target and rename it over the target. Done when: a test that fails the write halfway leaves the previous file intact. Cheaper substitute: truncating and rewriting the file in place must fail that test.
- [ ] Make `Settings::load` in `src/settings.rs` return the defaults and rename the file to `settings.toml.damaged` when it does not parse. Done when: a test with a corrupt file gets defaults and finds the renamed file.
- [ ] Add a `VOXEL_SETTINGS_DIR` override in `src/settings.rs` so tests never touch the user's real settings. Done when: every test that saves settings uses a temporary folder and `%APPDATA%\Voxel` is unchanged after `cargo test`.
- [ ] Restore the window size in `src/app.rs` at start and save it on close, clamping to the current monitor so a window is never restored off screen. Done when: a test saves a size larger than the monitor and reads back a clamped size.
- [ ] Start the Open dialogs in `src/ui/toolbar.rs` at the last opened folder and save it after a successful open. Done when: a test opens a path and reads the folder back from a fresh `Settings::load`.
- [ ] Commit: `settings: persisted window size and last folder`

**Test checkpoint:** `cargo test settings` passes; writing the file in place instead of by rename fails the interrupted-write test.

## Verification

- `target/release/voxel.exe <X-ray file>` shows the image in under 1 second by `scripts/measure-start.ps1`, and window/level, zoom, pan, invert, fit and reset all respond.
- Dropping a multi-series MRI folder shows the strip, scrolling is smooth while slices load, and the overlay names the patient, the slice and the orientation.
- A text file dropped on the window shows one plain sentence and the app keeps running.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
