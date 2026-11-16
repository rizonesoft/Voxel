---
schema_version: 1
id: volume-and-mpr
domain: 03-volume
status: active
title: "TODO-01 -- Volume building and MPR"
track: M3
---

# TODO-01 -- Volume building and MPR

> **Goal:** An MRI series becomes one volume in patient space, and the user sees it in three linked planes (axial, coronal, sagittal) with crosshairs, can tilt a plane to any angle, and every plane is geometrically correct: a sphere scanned with thick slices still looks like a sphere.

> **Current state:** Measured 2026-11-17. No code exists. Series arrive ordered with per-image position and orientation from D01 T01 §3 and §5, decoded by the loader of D01 T01 §4. The 2D viewport, view state and series strip come from D02 T01. The foundation plan's risk "MRI geometry that will not form a volume" is answered here by §1 and §5. The phantom series every test here uses come from `tests/common/phantom.rs` (D00 T01 §6).

## Inputs

- `docs/plans/2026-11-17-voxel-tech-stack.md`: "How each view works" (MPR), "Risks" (geometry, our own renderer) and "Source layout (planned)" (`src/volume/`, `src/render/`).
- `design/SPEC.md`, `design/contract/` and `design/screens/`: the approved interface. Every control named in this file is registered once in `src/ui/controls.rs` and every panel once in `src/ui/panels.rs` (D02 T02 §2), and is drawn by whichever of the three interfaces is active. Where a section says toolbar, read the interface's tool area: the toolbar in Workstation, the dock in Lightbox, the rail or an inspector panel in Console. Placement, size and look are fixed by the contract, not by this file.
- `src/dicom/study.rs` (`Series`, `ImageRef`) and `src/dicom/loader.rs` from D01 T01.
- `src/ui/viewport.rs` and `src/ui/view_state.rs` from D02 T01 §1, §2 and §5.
- The DICOM standard, PS3.3 C.7.6.2 (the image plane module), for the mapping from pixel to patient coordinates used in §1.

## Outcome

- `voxel::volume::geometry` accepts a series as a volume or refuses it with a named reason, proved on phantom series with known geometry.
- A volume is one 16-bit 3D texture with a voxel-to-patient matrix.
- The MPR layout shows three planes with crosshairs that stay linked, and distances are true in millimetres in every plane.
- A plane can be rotated to any oblique angle and reset.
- A series that cannot form a volume still opens as a 2D stack, and the MPR button says why it is unavailable.

**Adjacency:** list=not-applicable (series are found through the strip in D02 T01 §5); document=not-applicable (export of a view is D05 T01 §7); settings=not-applicable (MPR has no tunable in version 1); reporting=not-applicable (no summaries over studies in version 1); notifications=not-applicable (a local viewer notifies nobody); permissions=not-applicable (no access control in a local viewer); audit=not-applicable (viewing changes nothing to audit); exchange=not-applicable (import is D01 T01); reverse=applicable

**Adjacency rationale:** Reverse is the reset of the planes in §4: any crosshair move or oblique rotation returns to the three standard planes through the volume centre with one action.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | Slice geometry check and the volume refusal reasons | D00 T01 §6, D01 T01 §3, D01 T01 §5 | [ ] |
| 2 | §2 | Volume packed into a 16-bit 3D texture | §1, D01 T01 §4, D02 T01 §1 | [ ] |
| 3 | §3 | Three-plane MPR layout with linked crosshairs | §2, D02 T01 §5, D02 T01 §6 | [ ] |
| 4 | §4 | Oblique plane rotation and plane reset | §3 | [ ] |
| 5 | §5 | Volume refusal shown with the 2D stack kept | §1, §3 | [ ] |

## 1. Slice geometry check and the volume refusal reasons

A volume is only valid when the slices are parallel, evenly spaced, the same size and from one acquisition. Real MRI series break each of those: localisers mix three orientations, some series skip slices, some repeat positions for several echoes. Building a volume from such a series would draw anatomy in the wrong place, so the check refuses and says why.

**Phase:** 3
**Needs:** none
**Surface:** no

**Build order:**

1. Write `VolumeGeometry::from_series` in `src/volume/geometry.rs`. Done when: an even axial phantom is accepted with the right matrix.
2. Add each refusal reason with a test in `tests/volume_geometry.rs`. Done when: one test per reason passes.

- [ ] Define `VolumeGeometry` in `src/volume/geometry.rs` (dimensions, spacing in mm on three axes, origin, and the voxel-to-patient `glam::Mat4`) and `VolumeRefusal` with `TooFewSlices`, `MixedOrientation`, `MixedSize`, `UnevenSpacing { smallest, largest }`, `DuplicatePositions`, `MissingGeometry` and `TooLarge`. Done when: `cargo build` exits 0 and each refusal has a plain-language `user_message()`.
- [ ] Write `VolumeGeometry::from_series` in `src/volume/geometry.rs`: compute the slice normal as the cross product of the row and column directions of `ImageOrientationPatient`, project each `ImagePositionPatient` on it, and take the slice spacing from the positions, never from `SliceThickness` or `SpacingBetweenSlices`. Done when: `tests/volume_geometry.rs` accepts a phantom with 5 mm spacing whose `SliceThickness` tag says 3 mm and reports 5 mm. Cheaper substitute: reading spacing from the `SliceThickness` tag must fail that test.
- [ ] Refuse in `from_series` with `MixedOrientation` when any slice's direction cosines differ from the first by more than 0.001, and with `MixedSize` when rows, columns or pixel spacing differ. Done when: a three-plane localiser phantom gives `MixedOrientation`.
- [ ] Refuse in `from_series` with `UnevenSpacing` when any gap differs from the median by more than 1 percent, and with `DuplicatePositions` when two slices share a position. Done when: a phantom with one slice removed gives `UnevenSpacing` and a two-echo phantom gives `DuplicatePositions`.
- [ ] Split a series with duplicate positions into sub-series in `src/volume/geometry.rs` by `EchoTime`, then `TemporalPositionIdentifier`, then `DiffusionBValue`, and accept each part that then passes. Done when: the two-echo phantom yields two accepted geometries, and a phantom with unexplained duplicates still gives `DuplicatePositions`.
- [ ] Refuse in `from_series` with `TooFewSlices` under 3 slices, `MissingGeometry` when position or orientation is absent, and `TooLarge` when any dimension exceeds the adapter's `max_texture_dimension_3d` or the volume exceeds 2 GB. Done when: tests cover the three reasons.
- [ ] Commit: `volume: slice geometry check and refusal reasons`

**Test checkpoint:** `cargo test --test volume_geometry` passes with one test per `VolumeRefusal` variant; taking spacing from `SliceThickness` fails the 5 mm phantom test.

## 2. Volume packed into a 16-bit 3D texture

One texture holds the whole series so MPR and 3D sample it on the GPU. The stored values stay 16-bit, and the shader interpolates between voxels; on an adapter without a filterable 16-bit format the shader interpolates by hand, so the picture is the same everywhere.

**Phase:** 3
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Write `Volume` and `VolumeTexture` in `src/volume/volume.rs` and `src/render/volume_texture.rs`. Done when: a phantom uploads and one voxel reads back.
2. Write the shared sampling function in `src/render/shaders/volume_sample.wgsl` with both interpolation paths. Done when: both paths give the same value in a test.

- [ ] Write `Volume::build(geometry, loader)` in `src/volume/volume.rs`: copy each decoded slice into one contiguous buffer in slice order as the loader delivers it, applying each slice's own rescale so all voxels share one scale. Done when: a test builds a ramp phantom and asserts voxel (x, y, z) equals the ramp value. Cheaper substitute: assuming one rescale for the whole series must fail; a phantom with per-slice rescale differences asserts a uniform result.
- [ ] Write `VolumeTexture::upload` in `src/render/volume_texture.rs`: use `R16Unorm` or `R16Snorm` with linear filtering when the adapter offers `TEXTURE_FORMAT_16BIT_NORM`, and otherwise `R16Uint` or `R16Sint`, recording which path is active. Done when: the log names the path and a read-back test returns the stored voxel on both.
- [ ] Write `sample_volume(position)` in `src/render/shaders/volume_sample.wgsl`: one filtered `textureSampleLevel` on the filterable path, and eight `textureLoad` fetches blended trilinearly on the integer path, behind one function both renderers call. Done when: `tests/volume_sample.rs` samples a ramp phantom at a half-voxel offset on both paths and reads the midpoint value within one level.
- [ ] Upload slices to `VolumeTexture` as they arrive and expose `loaded_fraction()`, so MPR can draw while the volume fills. Done when: a test with a slow loader samples a loaded slice correctly while `loaded_fraction()` is under 1.
- [ ] Release the texture and the buffer in `VolumeTexture` when the series is closed or replaced. Done when: a test opens and closes 20 phantom volumes and the process's GPU memory report returns to its starting value within 5 percent.
- [ ] Run `tests/volume_sample.rs` with `VOXEL_FORCE_WARP=1`. Done when: the assertions pass on the software adapter.
- [ ] Commit: `volume: 16-bit 3D texture and shared sampling`

**Test checkpoint:** `cargo test --test volume_sample` passes on both interpolation paths and under `VOXEL_FORCE_WARP=1`; using nearest-voxel sampling fails the half-voxel midpoint test.

## 3. Three-plane MPR layout with linked crosshairs

The view clinicians ask for by name: the same point shown in three perpendicular planes. Each plane is a rectangle in patient space sampled from the volume, so thick slices are stretched to their true size and a click in one plane moves the other two.

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** look at one point of the anatomy from three directions at once and move through the volume in any of them
**Treatment:** the planes as `design/SPEC.md` lays them out per interface (a 2 by 2 grid in Workstation and Console, whose fourth pane D04 T01 §1 fills with the 3D view; one large axial pane with sagittal and coronal stacked beside it in Lightbox), each with two crosshair lines in the colours `plane-axial`, `plane-sagittal` and `plane-coronal` of the planes that cut it
**Chrome:** an MPR button in the toolbar (key M) that switches the open series between the stack view and the MPR layout; each viewport keeps the overlay and orientation letters of D02 T01 §6

**Build order:**

1. Write the plane model in `src/volume/plane.rs` and the shader `src/render/shaders/mpr.wgsl`. Done when: an offscreen render of the sphere phantom gives a circle of the right diameter in each plane.
2. Write the layout and crosshair interaction in `src/ui/mpr.rs`. Done when: a click in one plane moves the other two.

- [ ] Define `Plane` in `src/volume/plane.rs` (a centre point and two unit axes in patient millimetres) with `axial`, `coronal` and `sagittal` constructors built from patient axes, not from the acquisition's slice direction. Done when: a unit test on a sagittally acquired phantom asserts the axial plane's normal is the patient head-foot axis.
- [ ] Write `src/render/shaders/mpr.wgsl`: for each output pixel compute the patient position on the `Plane`, transform it to texture coordinates with the inverse voxel-to-patient matrix, call `sample_volume`, and apply the same window function as `image2d.wgsl`; positions outside the volume draw black. Done when: `tests/render_mpr.rs` renders the sphere phantom in three planes and measures a diameter within one pixel of the true value in each.
- [ ] Add a test in `tests/render_mpr.rs` with the `anisotropic(1, 1, 5)` sphere. Done when: the coronal and sagittal renders are circles, not ellipses, within one output pixel. Cheaper substitute: drawing one texel per output pixel must fail this test.
- [ ] Add a test in `tests/render_mpr.rs` with the `three_rods()` phantom asserting the edge letters and the rod directions agree in each plane. Done when: the patient-left rod points to the side labelled L in the axial and coronal views.
- [ ] Write `MprView` in `src/ui/mpr.rs`: three viewports sharing one focus point; a click or drag in one sets the focus and the other two planes move to pass through it; the wheel moves a plane along its normal by one voxel spacing. Done when: a test clicks a known voxel in the axial view and asserts the sagittal and coronal planes now contain that point.
- [ ] Draw the crosshair lines in `src/ui/mpr.rs` at the focus point with a small gap at the centre, and share window/level across the three views while each keeps its own zoom and pan. Done when: a test asserts the line positions for a known focus and that a window change in one view applies to all.
- [ ] Add the MPR button to `src/ui/toolbar.rs` with the M key, switching back to the stack view on a second press at the slice nearest the focus point. Done when: a test toggles twice and lands on the expected slice index.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `mpr` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `mpr: three-plane layout with linked crosshairs`

**Test checkpoint:** `cargo test --test render_mpr` passes; drawing one texel per output pixel fails the anisotropic sphere test.

## 4. Oblique plane rotation and plane reset

Anatomy rarely lines up with the scanner. Rotating the crosshair in one view tilts the other two planes, which is how a clinician lines a view up with a structure such as a spinal disc. Reset returns to the standard planes.

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** tilt the cut planes to line up with a structure, and get back to the standard planes
**Treatment:** small round handles on the crosshair lines away from the centre; dragging a handle rotates both lines together and the angle shows beside the handle while dragging
**Chrome:** a Reset Planes button beside the MPR button (key Shift+R), disabled while the planes are standard

**Build order:**

1. Add rotation about the focus point to the plane model in `src/volume/plane.rs`. Done when: unit tests cover rotation and orthogonality.
2. Add the handles and the reset in `src/ui/mpr.rs`. Done when: a drag rotates the planes and reset restores them.

- [ ] Add `MprPlanes::rotate(view, angle)` in `src/volume/plane.rs`: rotate the two other planes about the focus point around the normal of the view being dragged, keeping the three planes mutually perpendicular. Done when: a unit test rotates by 30 degrees and asserts the three normals are still perpendicular to within 0.0001.
- [ ] Add a test in `tests/render_mpr.rs` rendering the `tilted(20)` rod phantom after rotating the planes by 20 degrees. Done when: the rod appears along the horizontal axis at its full true length within one pixel.
- [ ] Draw the rotation handles in `src/ui/mpr.rs` and map a handle drag to `MprPlanes::rotate`, showing the angle in degrees while dragging. Done when: a test drags a handle through a known arc and reads the expected angle.
- [ ] Recompute the edge letters for oblique planes in `src/ui/overlay.rs`, showing compound letters (such as "LA") when the direction lies between two axes. Done when: a unit test at 45 degrees between left and anterior asserts "LA".
- [ ] Add `MprPlanes::reset()` and the Reset Planes button in `src/ui/toolbar.rs` with Shift+R, returning to the standard planes through the volume centre. Done when: a test rotates, moves the focus, resets, and asserts the initial planes. Cheaper substitute: resetting only the angle and leaving the focus moved must fail the test.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `mpr` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `mpr: oblique rotation and plane reset`

**Test checkpoint:** `cargo test plane` and `cargo test --test render_mpr` pass; rotating about the volume centre instead of the focus point fails the tilted-rod test.

## 5. Volume refusal shown with the 2D stack kept

The promise from the foundation plan: the 2D stack always works. When a series cannot form a volume the user keeps scrolling it as before, and the MPR and 3D buttons say in one sentence why they are unavailable instead of failing or silently doing nothing.

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** understand why MPR or 3D is not offered for this series, without losing the image already on screen
**Treatment:** the MPR button is shown disabled, and its tooltip carries the refusal sentence, for example "This series has gaps between slices, so it cannot be shown in 3D"
**Chrome:** the same disabled state and tooltip on the 3D button once D04 T01 §1 adds it; a small "2D only" tag on the series card in the strip

**Build order:**

1. Compute volume eligibility per series after the scan in `src/ui/series_strip.rs`. Done when: each card knows accepted or the refusal.
2. Wire the disabled state and tooltip in `src/ui/toolbar.rs`. Done when: the refusal sentence shows for a refused phantom.

- [ ] Call `VolumeGeometry::from_series` for each series after the scan, in the background, storing `Result<VolumeGeometry, VolumeRefusal>` on the series in `src/ui/series_strip.rs`. Done when: a test over a study with one even phantom and one localiser phantom records one acceptance and one `MixedOrientation`.
- [ ] Disable the MPR button in `src/ui/toolbar.rs` for a refused series and set its tooltip to `VolumeRefusal::user_message()`. Done when: a test asserts the disabled state and the tooltip text for the `missing_slice` phantom. Cheaper substitute: hiding the button must fail; the user is told why.
- [ ] Show the "2D only" tag on the series card in `src/ui/series_strip.rs` for a refused series, and no tag for a single-image series (an X-ray is not a failed volume). Done when: a test asserts the tag on the localiser phantom and none on a single X-ray.
- [ ] Offer each accepted sub-series of a split series (§1, the two-echo case) as its own card in `src/ui/series_strip.rs`, named with the split value such as "TE 30 ms". Done when: the two-echo phantom shows two cards and MPR opens on each.
- [ ] Switch to the stack view in `src/ui/mpr.rs` when the open series is replaced by a refused one while the MPR layout is showing. Done when: a test opens an accepted series in MPR, then clicks a refused card, and the viewport is the stack view of the refused series.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `only2d` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `mpr: volume refusal shown, 2D stack kept`

**Test checkpoint:** `cargo test --test volume_refusal_ui` passes; hiding the MPR button instead of disabling it with a tooltip fails the tooltip test.

## Verification

- The sphere phantom, including the 1 by 1 by 5 mm variant, measures its true diameter in all three planes and after an oblique rotation.
- A phantom study mixing an even series, a localiser and a two-echo series opens in MPR for each eligible series, and each refused series still scrolls as a 2D stack with its reason shown.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
