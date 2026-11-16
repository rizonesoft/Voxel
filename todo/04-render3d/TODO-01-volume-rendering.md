---
schema_version: 1
id: volume-rendering
domain: 04-render3d
status: active
title: "TODO-01 -- 3D volume rendering"
track: M4
---

# TODO-01 -- 3D volume rendering

> **Goal:** The user turns an MRI volume around in 3D: first as a maximum intensity projection, then as a shaded rendering with presets, at a frame rate that stays usable on integrated graphics and on the WARP software adapter.

> **Current state:** Measured 2026-11-17. No code exists. The volume texture and the shared `sample_volume` shader function come from D03 T01 §2, the MPR layout and toolbar button from D03 T01 §3, the refusal state from D03 T01 §5, and the settings file from D02 T01 §7. The foundation plan chose an in-house ray-marching shader over VTK, so correctness is proved here against phantoms.

## Inputs

- `docs/plans/2026-11-17-voxel-tech-stack.md`: "How each view works" (3D), "Rejected alternatives" (VTK) and "Risks" (weak GPU, our own renderer).
- `design/SPEC.md`, `design/contract/` and `design/screens/`: the approved interface. Every control named in this file is registered once in `src/ui/controls.rs` and every panel once in `src/ui/panels.rs` (D02 T02 §2), and is drawn by whichever of the three interfaces is active. Where a section says toolbar, read the interface's tool area: the toolbar in Workstation, the dock in Lightbox, the rail or an inspector panel in Console. Placement, size and look are fixed by the contract, not by this file.
- `src/render/volume_texture.rs` and `src/render/shaders/volume_sample.wgsl` from D03 T01 §2.
- `src/volume/geometry.rs` (`VolumeGeometry`, the voxel-to-patient matrix) from D03 T01 §1.
- `src/settings.rs` from D02 T01 §7, which §3 extends.
- `tests/common/phantom.rs` from D00 T01 §6.

## Outcome

- A 3D viewport renders a maximum intensity projection of the open volume, orbiting with the mouse, with true proportions for anisotropic voxels.
- A shaded rendering mode with named presets and an adjustable threshold.
- A quality setting, persisted, and automatic lower quality while the view is moving, so orbiting stays responsive on WARP.

**Adjacency:** list=not-applicable (series are found through the strip in D02 T01 §5); document=not-applicable (export of a view is D05 T01 §7); settings=applicable; reporting=not-applicable (no summaries over studies in version 1); notifications=not-applicable (a local viewer notifies nobody); permissions=not-applicable (no access control in a local viewer); audit=not-applicable (viewing changes nothing to audit); exchange=not-applicable (import is D01 T01); reverse=applicable

**Adjacency rationale:** The setting is 3D quality, owned by §3 with the ray-marching step count as its named consumer. Reverse is the camera reset in §1 and the preset reset in §2: any orbit, zoom or threshold change returns to the default with one action.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | Orbit camera and maximum intensity projection | D03 T01 §2, D03 T01 §3, D03 T01 §5 | [ ] |
| 2 | §2 | Shaded volume rendering with presets | §1 | [ ] |
| 3 | §3 | 3D quality setting and lower quality while moving | §1, D02 T01 §7 | [ ] |

## 1. Orbit camera and maximum intensity projection

Maximum intensity projection (MIP) shows the brightest value along each line of sight. It is the simplest 3D mode, the standard one for MR angiography, and it proves the whole ray-marching path (camera, ray and volume intersection, sampling) before shading is added.

**Phase:** 4
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** turn the scanned volume around and see its bright structures from any direction
**Treatment:** one viewport on black showing the volume, with a small orientation cube in the bottom right corner labelled L, R, A, P, H, F that turns with the view
**Chrome:** a 3D button in the toolbar beside MPR (key 3), disabled with the refusal tooltip of D03 T01 §5 for a series that is not a volume; a Reset View button (key R) in the 3D viewport

**Build order:**

1. Write the camera in `src/render/camera.rs` and the shader `src/render/shaders/raymarch.wgsl` with the MIP mode. Done when: an offscreen MIP of the sphere phantom is a disc of the right diameter.
2. Write the viewport and its input in `src/ui/view3d.rs`. Done when: a drag orbits the camera and reset restores it.

- [ ] Write `OrbitCamera` in `src/render/camera.rs`: a target at the volume centre in patient millimetres, a distance, yaw and pitch, an orthographic projection, and `reset()` to an anterior view with the head up. Done when: a unit test asserts the default view direction is along the patient anterior-posterior axis with the head axis up.
- [ ] Write `src/render/shaders/raymarch.wgsl`: for each pixel build a ray in patient space, intersect it with the volume's box through the inverse voxel-to-patient matrix, and step through the box calling `sample_volume`, keeping the largest value, with the step set to half the smallest voxel spacing. Done when: `tests/render_3d.rs` renders the sphere phantom and measures a disc diameter within one pixel of the true value from three directions.
- [ ] Add a test in `tests/render_3d.rs` with the `anisotropic(1, 1, 5)` sphere viewed from the side. Done when: the disc is round within one pixel. Cheaper substitute: marching in texture coordinates without the spacing must fail this test.
- [ ] Apply the window function to the MIP result in `raymarch.wgsl` with the same uniforms as the 2D view, so left-drag in the 3D viewport of `src/ui/view3d.rs` adjusts brightness and contrast. Done when: a test renders a ramp phantom with a narrow window and reads back saturated black and white regions.
- [ ] Write `View3d` in `src/ui/view3d.rs`: right-drag orbits, Ctrl+wheel zooms, middle-drag pans, R and double-click reset, pitch clamped short of the poles. Done when: unit tests assert each input's effect on `OrbitCamera` and that reset equals the initial state.
- [ ] Draw the orientation cube in `src/ui/view3d.rs` from the camera's rotation. Done when: `tests/render_3d.rs` with the `three_rods()` phantom asserts the patient-left rod points to the side the cube labels L.
- [ ] Add the 3D button to `src/ui/toolbar.rs` with key 3, using the same eligibility and tooltip as the MPR button. Done when: a test asserts it is enabled for the sphere phantom and disabled with the refusal sentence for the `missing_slice` phantom.
- [ ] Run `tests/render_3d.rs` with `VOXEL_FORCE_WARP=1`. Done when: the same assertions pass on the software adapter.
- [ ] Show the 3D view as the fourth pane of the MPR layout in the Workstation and Console interfaces in `src/ui/mpr.rs`, sharing the renderer and camera of `src/ui/view3d.rs`, and leave Lightbox's MPR at three panes (`design/SPEC.md`, "Interface 2: Lightbox"). Done when: a test opens MPR in each interface and counts four panes, three panes and four panes.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `view3d`, `mpr` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `3d: orbit camera and maximum intensity projection`

**Test checkpoint:** `cargo test --test render_3d` passes with and without `VOXEL_FORCE_WARP=1`; marching in texture coordinates without voxel spacing fails the anisotropic sphere test.

## 2. Shaded volume rendering with presets

The mode that looks like a solid object: each ray accumulates colour and opacity from a transfer function and is lit by the local gradient. MRI has no standard value scale (unlike CT), so the presets are defined relative to the volume's own value range and the user adjusts one threshold.

**Phase:** 4
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** see the volume as a solid surface, and choose how much of the dimmer tissue is hidden
**Treatment:** the same 3D viewport, with the volume drawn opaque and lit from the viewer's upper left
**Chrome:** a mode switch (MIP, Shaded) in the 3D viewport's corner, a preset drop-down (Surface, Soft, Bright structures) and a threshold slider, with a Reset Preset button

**Build order:**

1. Add the compositing mode and the transfer function texture to `raymarch.wgsl` and `src/render/transfer.rs`. Done when: a shaded render of the sphere phantom shows a lit sphere.
2. Add the presets and controls in `src/ui/view3d.rs`. Done when: each preset renders differently and reset restores the default.

- [ ] Define `TransferFunction` in `src/render/transfer.rs` as a 256-entry colour and opacity table over the volume's 0.5th to 99.5th percentile value range, uploaded as a 1D texture. Done when: a unit test asserts the table for a known preset and threshold.
- [ ] Add front-to-back compositing to `src/render/shaders/raymarch.wgsl` as a second mode: look up each sample in the transfer texture, correct opacity for the step length, accumulate, and stop when opacity passes 0.98. Done when: `tests/render_3d.rs` renders the sphere phantom with an opaque preset and reads a filled disc with the phantom's inside colour.
- [ ] Add gradient shading to the compositing mode in `raymarch.wgsl`: estimate the gradient by central differences of `sample_volume`, and light with one headlight offset to the upper left. Done when: a test asserts the sphere render is brighter in its upper-left quarter than its lower-right quarter.
- [ ] Offset each ray's start by a per-pixel fraction of one step in `raymarch.wgsl` to remove banding. Done when: a test on a ramp phantom asserts the rendered gradient has no step larger than two grey levels between neighbouring pixels.
- [ ] Add the presets Surface, Soft and Bright structures and the threshold slider to `src/ui/view3d.rs`, each rebuilding the `TransferFunction` only, never the volume texture. Done when: a test switches presets and asserts three different renders and no volume re-upload (an upload counter in the test build). Cheaper substitute: re-uploading the volume on a slider move must fail the counter assertion.
- [ ] Add the mode switch and the Reset Preset button to `src/ui/view3d.rs`, with the mode and preset remembered per series for the session. Done when: a test changes the threshold, resets, and reads the preset's default threshold.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `view3d` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `3d: shaded volume rendering with presets`

**Test checkpoint:** `cargo test --test render_3d` and `cargo test transfer` pass; removing the opacity correction for step length fails the filled-disc test when the step count changes.

## 3. 3D quality setting and lower quality while moving

Ray marching costs the most of anything Voxel draws, and the foundation plan requires it to work with no real GPU. The renderer drops to a coarser step and a smaller target while the view is moving and refines when it stops, and a setting lets a user on a weak PC cap the quality.

**Phase:** 4
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** 1:1 with `design/SPEC.md` and the contract files in `design/contract/`, in all three interfaces
**Job:** keep the 3D view responsive on a slow PC
**Treatment:** the 3D image is slightly softer while being turned and sharpens within a moment of stopping
**Chrome:** a Quality drop-down (Low, Medium, High, Automatic) in the 3D viewport's corner menu, defaulting to Automatic

**Build order:**

1. Add the quality levels and the moving and still states in `src/render/quality.rs`. Done when: unit tests cover the step and target size per level and state.
2. Persist the setting in `src/settings.rs` and measure frame time on WARP in `tests/render_3d_perf.rs`. Done when: the frame-time test passes.

- [ ] Define `Quality` (Low, Medium, High, Automatic) in `src/render/quality.rs` with, per level and per state (moving, still), the ray step as a multiple of the voxel spacing and the render target scale. Done when: a unit test asserts the table.
- [ ] Render the 3D view in `src/ui/view3d.rs` to an offscreen target at the current scale and draw it scaled to the viewport, switching to the moving state on input and to the still state 150 ms after the last input. Done when: a test asserts the target size shrinks during a drag and returns to full size afterwards.
- [ ] Make Automatic in `src/render/quality.rs` choose the level from the measured time of the last still frame: step down when it exceeds 100 ms, up when under 25 ms, never changing more than once per second. Done when: a unit test feeding frame times asserts the level changes and the once-per-second limit.
- [ ] Add `quality_3d` to `Settings` in `src/settings.rs`, defaulting to Automatic, with the Quality drop-down in `src/ui/view3d.rs` as its control. Done when: a test sets Low, saves, loads a fresh `Settings` and reads Low, and the renderer uses the Low step. Cheaper substitute: a setting that is saved but not read by the renderer must fail; the test reads the step the renderer used.
- [ ] Write `tests/render_3d_perf.rs`: with `VOXEL_FORCE_WARP=1` and a 256 by 256 by 128 phantom at Low quality in the moving state on a 1280 by 800 viewport, render 20 frames and assert the median is under 100 ms. Done when: the test passes, and `docs/performance.md` records the median with the machine and date.
- [ ] Run `cargo test --test ui_contract -- --nocapture` and read the report for the screens `view3d` in `workstation`, `lightbox` and `console`. Done when: no control or text this section adds is reported missing, extra or misplaced in any of the three (`design/SPEC.md`, "What 1:1 means"). Cheaper substitute: editing a file under `design/contract/` or `design/screens/` to quiet the report must fail review.
- [ ] Commit: `3d: quality setting and lower quality while moving`

**Test checkpoint:** `cargo test quality` and `cargo test --test render_3d_perf` pass; rendering the moving state at full step and full target size fails the WARP frame-time test.

## Verification

- The sphere phantom renders round from every direction in MIP and shaded modes, on the real adapter and on WARP.
- Orbiting a phantom MRI volume on WARP stays under 100 ms per frame at Low quality, recorded in `docs/performance.md`.
- The 3D quality setting survives a restart.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
