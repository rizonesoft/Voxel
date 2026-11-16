---
schema_version: 1
id: toolchain-and-workspace
domain: 00-workspace
status: active
title: "TODO-01 -- Toolchain and workspace"
track: M0
---

# TODO-01 -- Toolchain and workspace

> **Goal:** The chosen stack is installed, pinned and proved on this machine: Rust builds the `voxel` package, an empty `eframe` window opens on DirectX 12 or WARP, a test corpus of DICOM files exists with a codec coverage table, and one command verifies a change.

> **Current state:** Measured 2026-11-17. The repository holds `idea.txt`, `AGENTS.md`, `docs/plans/2026-11-17-voxel-tech-stack.md` and the Conclave `base`, `todo` and `reviewer` kits. There is no `Cargo.toml` and no `src/`. `cargo` and `rustc` are not on `PATH` and `~/.cargo` does not exist, so Rust is not installed. `git`, `python` and `bosun` are installed.

## Inputs

- `docs/plans/2026-11-17-voxel-tech-stack.md`: "The stack" (every crate named here), "Risks" (codec coverage, weak GPU) and "Source layout (planned)".
- `AGENTS.md`: "Tech stack" and "Layout and commands", which §5 makes true.
- `idea.txt`: the one-line product statement.

## Outcome

- `cargo build --release` produces `target/release/voxel.exe` from a pinned toolchain and a committed `Cargo.lock`.
- Running the exe opens an empty Voxel window, and the log line names the GPU adapter in use.
- `tests/corpus.rs` opens every corpus file and `docs/codec-coverage.md` records which transfer syntaxes decode.
- `tests/common/phantom.rs` writes synthetic DICOM series with exact, known geometry for every later test.
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings` and `cargo test` pass and are the documented verify commands.

**Adjacency:** all=not-applicable (toolchain, dependency pins and an empty window: no records, documents, settings or user data exist yet)

**Adjacency rationale:** The first user-facing records arrive with the study model in D01 T01 and the first settings with D05 T01 §1, which own their adjacency.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | Rust toolchain pin and the `voxel` Cargo package | -- | [ ] |
| 2 | §2 | Dependency pins for the chosen stack | §1 | [ ] |
| 3 | §3 | Empty app window on DirectX 12 with WARP fallback | §2 | [ ] |
| 4 | §4 | DICOM test corpus and codec coverage table | §2 | [ ] |
| 5 | §5 | Verify commands and their documentation | §3, §4 | [ ] |
| 6 | §6 | Phantom series builder with known geometry | §4 | [ ] |

## 1. Rust toolchain pin and the `voxel` Cargo package

Nothing can be built until Rust is on the machine. This section installs it, pins the toolchain in the repository so every session builds with the same compiler, and creates the one package the foundation plan names. It adds no dependency and no feature code.

**Phase:** 0
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Install `rustup` with the stable MSVC toolchain and confirm the MSVC linker is present. Done when: `cargo --version` and `rustc --version` print in a new shell.
2. Create the package with `src/lib.rs` and `src/main.rs` and pin the toolchain in `rust-toolchain.toml`. Done when: `cargo build` exits 0.

- [ ] Install Rust with `winget install Rustlang.Rustup` and the `stable-x86_64-pc-windows-msvc` toolchain. Done when: `cargo --version` prints a version in a fresh PowerShell session. Cheaper substitute: a `cargo` reached only through a path typed into one shell must fail; it has to be on the user `PATH`.
- [ ] Confirm the MSVC linker with `rustc --print sysroot` and a `cargo new` build in the session scratchpad. Done when: a hello-world binary links and runs; if `link.exe` is missing, install the Visual Studio Build Tools C++ workload with `winget install Microsoft.VisualStudio.2022.BuildTools` and build again.
- [ ] Write `rust-toolchain.toml` with `channel = "stable"` pinned to the exact installed version and the `rustfmt` and `clippy` components. Done when: `rustup show` in the repository names that version as the override. Cheaper substitute: leaving the channel as a floating `stable` must fail; the pin is an exact version.
- [ ] Create `Cargo.toml` for package `voxel` (edition 2024, a `[lib]` and a `[[bin]]` named `voxel`), with `src/lib.rs` and a `src/main.rs` that calls `voxel::run()`. Done when: `cargo build` exits 0 and `target/debug/voxel.exe` exists.
- [ ] Add a `[profile.release]` to `Cargo.toml` with `lto = "fat"`, `codegen-units = 1`, `strip = true` and `panic = "abort"`. Done when: `cargo build --release` exits 0. Cheaper substitute: `opt-level = "z"` must not be set without a measured size and speed comparison.
- [ ] Add `tests/smoke.rs` asserting `voxel::version()` equals `env!("CARGO_PKG_VERSION")`. Done when: `cargo test --test smoke` passes and fails if `version()` returns a different string.
- [ ] Commit: `workspace: Rust toolchain pin and the voxel package`

**Test checkpoint:** `cargo build --release` exits 0 and `cargo test --test smoke` reports 1 passed; deleting `rust-toolchain.toml` makes `rustup show` stop naming the override.

## 2. Dependency pins for the chosen stack

The foundation plan names the crates but not their versions. This section adds each one at its latest stable release, with only the features Voxel needs, and records the release exe size as the baseline every later dependency is measured against.

**Phase:** 0
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add each crate from "The stack" in `docs/plans/2026-11-17-voxel-tech-stack.md` to `Cargo.toml` with explicit features. Done when: `cargo build --release` exits 0 with `Cargo.lock` committed.
2. Record the versions and the exe size in `docs/dependencies.md`. Done when: the table lists every direct dependency with its version, features and reason.

- [ ] Read the current feature list of `eframe` on docs.rs and add it to `Cargo.toml` with `default-features = false` and the `wgpu` renderer feature only (no `glow`). Done when: `cargo tree -e features -i wgpu` shows `wgpu` reached through `eframe`, and `cargo tree -i glow` finds nothing.
- [ ] Add `dicom-object`, `dicom-pixeldata` and `dicom-dictionary-std` to `Cargo.toml`, enabling every codec feature `dicom-pixeldata` documents for JPEG, JPEG Lossless, JPEG 2000, JPEG-LS and RLE, preferring a pure Rust codec where it offers a choice. Done when: `cargo build` exits 0 and the chosen features are listed in `docs/dependencies.md` with the transfer syntaxes each covers. Cheaper substitute: enabling only the default features must fail review; compressed exports are the stated risk.
- [ ] Add `glam`, `rayon`, `memmap2`, `rfd` (native file dialogs), `serde` and `toml` (the settings file), `anyhow`, `thiserror`, `log` and a small logger to `Cargo.toml`. Done when: `cargo build` exits 0.
- [ ] Add `dicom-test-files` and `image` (PNG only) under `[dev-dependencies]` in `Cargo.toml`. Done when: `cargo tree -e no-dev -i image` finds nothing, proving they stay out of the release exe.
- [ ] Write `docs/dependencies.md`: one table row per direct dependency (name, pinned version, features, why), and the size in bytes of `target/release/voxel.exe`. Done when: the size in the file matches `(Get-Item target/release/voxel.exe).Length` at the commit.
- [ ] Commit `Cargo.lock`. Done when: `git ls-files Cargo.lock` prints the path. Cheaper substitute: ignoring `Cargo.lock` must fail; an application commits it.
- [ ] Commit: `workspace: pin the stack's dependencies`

**Test checkpoint:** `cargo build --release --locked` exits 0, and `cargo tree -i glow` prints an error that the package is not found; removing `Cargo.lock` makes `--locked` fail.

## 3. Empty app window on DirectX 12 with WARP fallback

This proves the shell of the stack end to end: `eframe` opens a window, `wgpu` picks DirectX 12, and a PC with no usable GPU still gets a window through WARP, the software adapter Windows ships. It draws no image; the viewer arrives in D02 T01.

**Phase:** 0
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** functional shell only; there is no design SPEC yet, so the look is the `egui` default dark theme
**Job:** start the app and see an empty Voxel window that says how to open a study
**Treatment:** a centred hint "Drop a DICOM file or folder here, or press Ctrl+O", nothing else
**Chrome:** the Windows title bar reading "Voxel"; no menu or toolbar yet (D02 T01 §3 adds Open)

**Build order:**

1. Write `src/app.rs` with the `eframe::App` and the adapter choice in `src/render/gpu.rs`. Done when: `cargo run` opens a window titled "Voxel".
2. Add the WARP fallback and an offscreen test of the adapter choice in `tests/gpu_adapter.rs`. Done when: the test passes with the fallback forced.

- [ ] Write `voxel::run()` in `src/app.rs` to start `eframe` with the `wgpu` renderer, a 1280 by 800 window titled "Voxel", and the empty-state hint. Done when: `cargo run` shows the window and the hint. Cheaper substitute: a window drawn through the `glow` renderer must fail; the plan's renderer is `wgpu`.
- [ ] Write `choose_adapter` in `src/render/gpu.rs`: request DirectX 12 and a high-performance adapter first, then fall back to the WARP software adapter, and log the adapter name and backend. Done when: the log shows one line such as `gpu: <name> (Dx12)` at start.
- [ ] Add the environment variable `VOXEL_FORCE_WARP=1` to `choose_adapter` in `src/render/gpu.rs` so the fallback can be exercised on a PC with a GPU. Done when: `$env:VOXEL_FORCE_WARP = '1'; cargo run` logs the Microsoft Basic Render Driver and still shows the window.
- [ ] Make `choose_adapter` return an error naming the cause when no adapter exists, and show it with a native message box from `src/app.rs` before exit. Done when: a test with an adapter list forced empty gets the error text "Voxel could not start the graphics system" and exit code 2. Cheaper substitute: a panic with a backtrace must fail; a patient sees this.
- [ ] Write `tests/gpu_adapter.rs`: create an offscreen `wgpu` device through `choose_adapter` with and without the forced fallback and assert the backend is DirectX 12 both times. Done when: `cargo test --test gpu_adapter` passes and fails if the fallback branch is removed.
- [ ] Set the subsystem to `windows` in `src/main.rs` for release builds only. Done when: starting `target/release/voxel.exe` from Explorer opens no console window, and `cargo run` in debug still prints the log.
- [ ] Commit: `app: empty window on DirectX 12 with WARP fallback`

**Test checkpoint:** `cargo test --test gpu_adapter` reports 2 passed, and `$env:VOXEL_FORCE_WARP = '1'; cargo run` logs the Microsoft Basic Render Driver; removing the fallback branch fails the forced test.

## 4. DICOM test corpus and codec coverage table

The largest stack risk is a compressed format `dicom-rs` cannot decode. This section builds the corpus every later test uses and measures the coverage instead of assuming it: each file is opened and decoded, and the result is written down per transfer syntax.

**Phase:** 0
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Write `tests/common/corpus.rs` listing the corpus files from `dicom-test-files`. Done when: every listed file resolves to a path on disk.
2. Write `tests/corpus.rs` to decode each file and produce `docs/codec-coverage.md`. Done when: the table has one row per transfer syntax with decoded or failed.

- [ ] Read the `dicom-test-files` crate documentation and list in `tests/common/corpus.rs` every file it offers that is an X-ray (CR, DX), an MR image or a multi-frame image, with its modality and transfer syntax. Done when: the list covers at least one file each for uncompressed, RLE, JPEG baseline, JPEG Lossless, JPEG 2000 and JPEG-LS, or names the format with no test file.
- [ ] Write `tests/corpus.rs` test `every_corpus_file_opens`: open each file with `dicom_object::open_file` and assert the header reads. Done when: `cargo test --test corpus every_corpus_file_opens` passes.
- [ ] Write `tests/corpus.rs` test `decode_coverage`: decode the pixel data of each file with `dicom-pixeldata` and collect per transfer syntax UID whether it decoded, without failing on a decode error. Done when: the test prints one line per transfer syntax.
- [ ] Write the collected result to `docs/codec-coverage.md` as a table (transfer syntax name, UID, test file, decoded or the error text). Done when: the file is committed and matches the test's printed lines. Cheaper substitute: a table written by hand from the crate's README must fail; it is measured.
- [ ] For each transfer syntax that failed, add the matching C codec feature (OpenJPEG or CharLS bindings) in `Cargo.toml` and run the test again. Done when: the row reads decoded, or the row names the format as unsupported with the error, and `docs/dependencies.md` records the added feature and the new exe size.
- [ ] Add to `tests/corpus.rs` the test `required_syntaxes_decode` asserting that uncompressed, RLE, JPEG baseline, JPEG Lossless and JPEG 2000 all decoded. Done when: the test passes, and fails when a required codec feature is removed from `Cargo.toml`.
- [ ] Commit: `corpus: DICOM test files and measured codec coverage`

**Test checkpoint:** `cargo test --test corpus` reports 3 passed and `docs/codec-coverage.md` has a row for each of the six formats; removing the JPEG 2000 feature from `Cargo.toml` fails `required_syntaxes_decode`.

## 5. Verify commands and their documentation

`AGENTS.md` already names the verify commands as the plan's intent. This section makes them true on a clean tree and wires the one script that runs them, so every later section has a single gate.

**Phase:** 0
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Make `cargo fmt --check` and `cargo clippy --all-targets -- -D warnings` pass on the tree. Done when: both exit 0.
2. Write `scripts/check.ps1` and update `AGENTS.md`. Done when: the script exits 0 on a clean tree and non-zero on a formatting fault.

- [ ] Run `cargo fmt` and fix every `cargo clippy --all-targets -- -D warnings` finding in `src/` and `tests/`. Done when: both commands exit 0. Cheaper substitute: an `#![allow(clippy::all)]` in `src/lib.rs` must fail; findings are fixed, not silenced.
- [ ] Write `scripts/check.ps1`: run `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test --locked` and `python scripts/todo-graph.py validate` in order, stop at the first failure and return its exit code. Done when: `pwsh scripts/check.ps1` exits 0.
- [ ] Prove `scripts/check.ps1` can fail: misformat a line in `src/lib.rs`, run it, then restore the line. Done when: the run with the fault exits non-zero and names `cargo fmt`.
- [ ] Replace the "Nothing is built yet" sentence in the "Layout and commands" section of `AGENTS.md` with the working commands, naming `bosun run -- pwsh scripts/check.ps1` as the full check. Done when: every command in that section runs as written.
- [ ] Commit: `workspace: one verify command`

**Test checkpoint:** `bosun run -- pwsh scripts/check.ps1` exits 0 on a clean tree; with one misformatted line in `src/lib.rs` it exits non-zero.

## 6. Phantom series builder with known geometry

The loader, the volume builder and both in-house renderers need tests with known answers. The phantom builder writes real DICOM files for shapes whose position and size in patient space are exact, so a test can ask "is the sphere centre where it should be, in millimetres, in every plane" instead of comparing against a picture nobody can verify. It lives under `tests/` and never ships in the app.

**Phase:** 0
**Needs:** none
**Surface:** no

**Build order:**

1. Write the builder in `tests/common/phantom.rs`. Done when: it writes a series whose files read back with the geometry it was given.
2. Add the variants the loading, geometry and rendering tests need. Done when: each variant has a self-test.

- [ ] Write `PhantomSeries` in `tests/common/phantom.rs`: given dimensions, in-plane spacing, slice spacing, orientation and origin, write one DICOM MR file per slice into a temporary folder with `dicom-object`, with voxel values from a shape function evaluated in patient millimetres. Done when: `tests/phantom_selftest.rs` opens each file with `dicom_object::open_file` and reads back the `ImagePositionPatient`, `ImageOrientationPatient` and `PixelSpacing` it was given.
- [ ] Add the shapes `sphere(centre_mm, radius_mm)`, `ramp(axis)` and `three_rods()` (three rods of different lengths along the patient left, posterior and head axes) to `tests/common/phantom.rs`. Done when: a self-test asserts a voxel inside the sphere reads the inside value and one outside reads the background.
- [ ] Add the variants `shuffled()`, `missing_slice(n)`, `two_echoes()`, `localiser()`, `tilted(angle)`, `anisotropic(1, 1, 5)` and `slow(delay)` (a wrapper that delays each read, for loader tests) to `PhantomSeries`. Done when: each variant has a self-test asserting the property its name states.
- [ ] Add `PhantomSeries::as_multiframe()` writing the same volume as one enhanced MR file with per-frame functional groups. Done when: a self-test reads the per-frame positions back and they equal the per-slice phantom's.
- [ ] Label every phantom file with patient name `PHANTOM^VOXEL` and a `SeriesDescription` starting "Synthetic". Done when: a self-test asserts both tags, so no phantom can be mistaken for a real study.
- [ ] Delete each phantom's temporary folder when the `PhantomSeries` value is dropped. Done when: a self-test asserts the folder is gone after the value goes out of scope.
- [ ] Commit: `tests: phantom series builder with known geometry`

**Test checkpoint:** `cargo test --test phantom_selftest` passes; writing `ImagePositionPatient` with the row and column offsets swapped fails the read-back test.

## Verification

- A fresh shell runs `cargo build --release --locked`, then `target/release/voxel.exe` opens an empty Voxel window and the log names a DirectX 12 adapter.
- `docs/codec-coverage.md` and `docs/dependencies.md` match what the tests and the build measure at the closing commit.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
