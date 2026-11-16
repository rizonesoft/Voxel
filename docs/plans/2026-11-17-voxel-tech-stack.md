# Voxel tech stack and build plan

Written 2026-11-17. This is the foundation plan the `todo/` tree executes. Nothing is built yet: the repository holds this plan, the Conclave kits and `idea.txt`.

## What Voxel is

A lightweight, fast-opening DICOM viewer for X-rays and MRIs, as one small native Windows app instead of heavy PACS software (`idea.txt`).

## Decisions the owner made (2026-11-16 and 2026-11-17)

| Question | Answer | What it means |
| -------- | ------ | ------------- |
| Platforms | Windows only, no browser version | A native app; no webview and no cross-platform layer |
| Who uses it | Clinicians and patients | One app with a plain mode and a clinician mode |
| MRI depth | MPR and 3D are required | Series must become volumes; two extra GPU views |
| Brand | "Lattice", in Conclave Design System v2 colours and type | `assets/brand/`; the app uses the same tokens |
| Interface | Three ship: Workstation (default), Lightbox, Console | One control registry, three shells, `design/SPEC.md` |
| Choosing it | At install, and any time in Settings | An installer beside the portable exe; a Settings window |

## The stack

| Layer | Choice | Why |
| ----- | ------ | --- |
| Language | Rust (stable, MSVC target) | Native speed, one static exe, safe parsing of untrusted files |
| App shell | `eframe` (`winit` + `wgpu` + `egui` in one) | Starts fast; the least glue code for a window, GPU and UI |
| GPU backend | DirectX 12 through `wgpu`, WARP as fallback | Works on every Windows 10 and 11 PC, with or without a real GPU |
| DICOM parsing | `dicom-rs` (`dicom-object`, `dicom-pixeldata`) | Mature, pure Rust, reads headers without decoding pixels |
| Compressed pixels | The codec features of `dicom-pixeldata` | JPEG, JPEG Lossless, JPEG 2000, JPEG-LS and RLE exports |
| Maths | `glam` | Patient-space vectors and matrices for geometry, MPR and 3D |
| Loading | `memmap2` and `rayon` | First slice on screen at once, the rest decoded in the background |
| Dialogs and settings | `rfd`; `serde` with `toml` | Native Open dialogs; one small settings file in `%APPDATA%\Voxel` |
| Shaders | WGSL files under `src/render/shaders/` | Window/level, MPR plane sampling and ray marching live on the GPU |
| Tests | `cargo test`, offscreen `wgpu` renders with pixel read-back | Rendering is proved by pixels, not by eye |
| Interface | Three `egui` shells over one control and panel registry | The owner chose all three designs; a feature is written once |
| Type and icons | Archivo, IBM Plex Sans and Mono embedded; stroke icons drawn in code | The same on every PC, no font to install |
| Packaging | One portable exe, and a per-user installer built with Inno Setup | A disc or a locked-down PC runs the exe; the installer asks for the interface |

Crate versions are not pinned here. D00 T01 §2 pins the latest stable releases when the workspace is created, and `Cargo.lock` is the record.

## How each view works

- **2D (X-ray and single slices):** the 16-bit pixels go to the GPU as one texture; a shader applies rescale, window/level and invert, so adjusting brightness never re-decodes the image.
- **MPR:** the series is packed into one 16-bit 3D texture; a shader samples it on any plane (axial, coronal, sagittal, oblique) with linked crosshairs.
- **3D:** a ray-marching shader over the same 3D texture: maximum intensity projection first, then shaded volume rendering with transfer-function presets.

## Rejected alternatives

| Option | Why not |
| ------ | ------- |
| Tauri with Cornerstone3D | Slower start and more memory; only right if a browser version mattered |
| C++ with Qt, DCMTK or GDCM, and VTK | Widest coverage and ready-made 3D, but a large install and slow start |
| Electron | The opposite of lightweight |
| VTK for MPR and 3D only | A very large dependency for two shaders we can own |

## Out of scope for version 1

- A study database: a folder scan and DICOMDIR replace it.
- PACS networking (C-FIND, C-MOVE, DICOMweb).
- CT-specific tools, fusion, and reporting.
- Certification as a medical device (see Risks).
- Code signing: an unsigned exe shows a Windows SmartScreen warning on first run, and a certificate costs money, so it is the owner's call and no section buys one.

## Targets

These are the plan's own targets, set on 2026-11-17 and open to the owner's change.

| Target | Value | Proved by |
| ------ | ----- | --------- |
| Double-click to first image, typical X-ray, SSD | Under 1 second | D02 T01 §4 |
| Release exe size | Under 30 MB | D06 T01 §2 |
| Window/level and scroll response | Every frame, no re-decode | D02 T01 §1, §5 |

## Risks and how the plan answers them

| Risk | Answer | Owner |
| ---- | ------ | ----- |
| A compressed format `dicom-rs` cannot decode | Coverage table from real test files; a C codec per failing format | D00 T01 §4 |
| MRI geometry that will not form a volume | The 2D stack always works; the volume refusal says why | D03 T01 §1, §5 |
| Weak or missing GPU | WARP fallback, and a 3D quality setting | D00 T01 §3, D04 T01 §3 |
| Diagnostic use is regulated (FDA, CE, SAHPRA) | Owner decides the label before release | D06 T01 §1 |
| Our own volume renderer has bugs | Phantom volumes with known answers, pixel read-back tests | D00 T01 §6 |
| Three interfaces drift apart | One registry; a contract test over all 45 screens | D02 T02 §2, §4, §10 |
| The app does not match the design | `design/contract/` compared by test, within stated tolerances | D02 T02 §4 |

## Milestones and phases

The phase names are in `todo/plan.json`. Each milestone is one TODO file.

| Phase | Milestone | TODO file |
| ----- | --------- | --------- |
| 0 | Toolchain, workspace, app shell, test corpus | `todo/00-workspace/TODO-01-toolchain-and-workspace.md` |
| 1 and 2 | DICOM files, folders and series loaded | `todo/01-dicom/TODO-01-study-loading.md` |
| 1 and 2 | 2D viewing, fast open, stack scrolling | `todo/02-viewer/TODO-01-image-view-2d.md` |
| 1 to 6 | Theme, three interfaces, Settings, the design contract | `todo/02-viewer/TODO-02-interface-contract.md` |
| 3 | Volume building and MPR | `todo/03-volume/TODO-01-volume-and-mpr.md` |
| 4 | 3D rendering | `todo/04-render3d/TODO-01-volume-rendering.md` |
| 5 | Modes, measurements, layouts, tags, export | `todo/05-tools/TODO-01-clinician-tools.md` |
| 6 and 99 | Label, portable build, installer, file association, real-study pass | `todo/06-release/TODO-01-packaging.md` |

## Source layout (planned)

One Cargo package, `voxel`, with a library and a thin binary so everything is testable.

| Path | Holds |
| ---- | ----- |
| `src/main.rs` | Argument parsing and app start only |
| `src/lib.rs` | Module root |
| `src/dicom/` | File reading, study and series model, folder and DICOMDIR scan |
| `src/volume/` | Slice geometry, volume building |
| `src/render/` | GPU resources, the 2D, MPR and 3D renderers, `shaders/*.wgsl` |
| `src/ui/` | Theme, control and panel registries, viewports, tools, Settings |
| `src/ui/interfaces/` | The three shells: `workstation.rs`, `lightbox.rs`, `console.rs` |
| `design/` | The approved interface: SPEC, tokens, prototypes, pictures, contract files |
| `installer/` | The Inno Setup script |
| `src/settings.rs` | The persisted settings file |
| `tests/` | Integration tests, phantom builders, offscreen render tests |
