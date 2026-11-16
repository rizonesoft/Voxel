---
schema_version: 1
id: study-loading
domain: 01-dicom
status: active
title: "TODO-01 -- Study loading"
track: M1
---

# TODO-01 -- Study loading

> **Goal:** Voxel turns what a user opens (one DICOM file, a folder, or a disc with a `DICOMDIR`) into studies, series and images in memory, quickly and without ever crashing on a bad file: the first image is ready before the rest of the study is read.

> **Current state:** Measured 2026-11-17. No code exists: there is no `src/`. The crates this file uses (`dicom-object`, `dicom-pixeldata`, `memmap2`, `rayon`) are named in `docs/plans/2026-11-17-voxel-tech-stack.md` and pinned by D00 T01 §2. The test corpus and `docs/codec-coverage.md` come from D00 T01 §4.

## Inputs

- `docs/plans/2026-11-17-voxel-tech-stack.md`: "The stack" (DICOM parsing, compressed pixels, loading), "Out of scope for version 1" (no database, no PACS networking) and "Source layout (planned)" (`src/dicom/`).
- `docs/codec-coverage.md` (from D00 T01 §4): which transfer syntaxes decode, which §2 turns into refusal messages.
- `tests/common/corpus.rs` (from D00 T01 §4): the files every test here opens.
- `tests/common/phantom.rs` (from D00 T01 §6): the synthetic series the scan, loader and multi-frame tests use.
- The DICOM standard, PS3.3 (image pixel, image plane and multi-frame modules) and PS3.10 (file format and `DICOMDIR`), for every tag named below.

## Outcome

- `voxel::dicom::load_image(path)` returns pixels, size, rescale, default window and pixel spacing for every corpus file whose transfer syntax decodes.
- A file that is not DICOM, is cut short or uses an unsupported format gives a named error, never a panic.
- `voxel::dicom::scan(path)` groups a folder or `DICOMDIR` into studies and series, ordered, without decoding any pixels.
- Opening a series yields its first image at once and the rest in the background, in slice order.

**Adjacency:** list=applicable @ D02 T01 §5; document=not-applicable (loading produces nothing a user carries away; export is D05 T01 §7); settings=not-applicable (loading has no tunable); reporting=not-applicable (no summaries over studies in version 1); notifications=not-applicable (a local viewer notifies nobody); permissions=applicable; audit=applicable; exchange=applicable; reverse=not-applicable (Voxel only reads study files and never changes them)

**Adjacency rationale:** Finding a series without knowing its file name is the series strip in D02 T01 §5. Permissions here means files the user cannot read, which §2 refuses with a message. Audit is the load log: every skipped file is logged with its path and reason (§3). Exchange is import, the whole subject of this file. Nothing is written back to a study, so there is nothing to reverse.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | One DICOM file read into an image model | D00 T01 §4 | [ ] |
| 2 | §2 | Named refusals for unreadable and unsupported files | §1 | [ ] |
| 3 | §3 | Folder and DICOMDIR scan into studies and series | §1, D00 T01 §6 | [ ] |
| 4 | §4 | Background series loading with the first slice first | §3 | [ ] |
| 5 | §5 | Multi-frame files opened as series | §3 | [ ] |

## 1. One DICOM file read into an image model

Everything Voxel shows starts as one image: a grid of stored values and the few tags needed to display them correctly. This section defines that model and fills it from a single file. It must keep the stored 16-bit values untouched, because window/level is applied on the GPU (D02 T01 §1).

**Phase:** 1
**Needs:** none
**Surface:** no

**Build order:**

1. Define `Image` and `PixelData` in `src/dicom/image.rs`. Done when: the types compile with the fields listed below.
2. Write `load_image` in `src/dicom/load.rs` and test it against the corpus in `tests/load_image.rs`. Done when: the known-value tests pass.

- [ ] Define `Image` in `src/dicom/image.rs` with `rows`, `cols`, `pixels` (`PixelData::U16`, `I16` or `Rgb8`), `rescale_slope`, `rescale_intercept`, `window` (centre and width, optional), `invert` (true for `MONOCHROME1`), `pixel_spacing_mm` (optional) and `bits_stored`. Done when: `cargo build` exits 0.
- [ ] Write `load_image(path)` in `src/dicom/load.rs`: open the file through a `memmap2` map, read the image pixel module tags, and decode the pixel data with `dicom-pixeldata` into the stored integer type without applying rescale or window. Done when: `tests/load_image.rs` reads `pydicom/CT_small.dcm` and asserts its rows, columns and the stored value of pixel (0, 0) against the values printed by `dcmdump` or `pydicom` and recorded in the test. Cheaper substitute: converting to 8-bit on load must fail; the test asserts a stored value above 255.
- [ ] Read `PixelRepresentation` (0028,0103) in `load_image` and choose `I16` for signed data. Done when: a test on a signed corpus file asserts a negative stored value.
- [ ] Read `PhotometricInterpretation` (0028,0004) in `load_image`: set `invert` for `MONOCHROME1`, decode `RGB` and `YBR_FULL` to `Rgb8`, and return `LoadError::UnsupportedPhotometric` for the rest. Done when: tests cover one `MONOCHROME1`, one `MONOCHROME2` and one colour corpus file.
- [ ] Read the default window from `WindowCenter` and `WindowWidth` (0028,1050 and 1051, first value when multi-valued) in `load_image`; when absent, compute it in `src/dicom/window.rs` from the 0.5th and 99.5th percentiles of the stored values. Done when: a test asserts the tag values for a file that has them and the percentile result for a synthetic image that does not.
- [ ] Read pixel spacing in `load_image` in this order: `PixelSpacing` (0028,0030), then `ImagerPixelSpacing` (0018,1164), recording which one was used in `Image::spacing_source`. Done when: tests cover an MR file (`PixelSpacing`) and an X-ray file (`ImagerPixelSpacing`), and a file with neither gives `None`.
- [ ] Commit: `dicom: read one file into the image model`

**Test checkpoint:** `cargo test --test load_image` passes; changing `load_image` to scale pixels to 8-bit fails the stored-value assertion.

## 2. Named refusals for unreadable and unsupported files

Patients open whatever is on the disc they were given: text files, shortcuts, images with formats Voxel cannot decode. Each case gets an error type the interface can turn into one plain sentence (D02 T01 §3), and none of them may crash the app.

**Phase:** 1
**Needs:** none
**Surface:** no

**Build order:**

1. Define `LoadError` in `src/dicom/error.rs` with one variant per cause and a plain-language `user_message`. Done when: every variant has a message.
2. Test each cause in `tests/load_errors.rs`. Done when: each test gets the expected variant and no test panics.

- [ ] Define `LoadError` in `src/dicom/error.rs` with `NotDicom`, `Truncated`, `NoPixelData`, `UnsupportedTransferSyntax { uid, name }`, `UnsupportedPhotometric`, `AccessDenied` and `Io`, each with a `user_message()` a patient can read. Done when: a unit test asserts no message contains a tag number or the word "panic".
- [ ] Return `NotDicom` from `load_image` in `src/dicom/load.rs` for a file without the `DICM` preamble that also fails the implicit little-endian fallback read. Done when: `tests/load_errors.rs` gets `NotDicom` for a text file and a PNG.
- [ ] Return `Truncated` from `load_image` when the pixel data is shorter than rows by columns by bytes per sample. Done when: a corpus file cut to half its length in the test's temporary folder gives `Truncated`. Cheaper substitute: padding the missing pixels with zeros must fail; a half image shown as whole is a wrong image.
- [ ] Return `UnsupportedTransferSyntax` from `load_image` with the syntax name from `dicom-transfer-syntax-registry` when no decoder exists. Done when: a test file whose transfer syntax UID is rewritten to an unknown value gives the variant with that UID.
- [ ] Return `NoPixelData` from `load_image` for objects with no (7FE0,0010), such as structured reports and presentation states. Done when: a corpus file of that kind gives `NoPixelData`.
- [ ] Wrap decoding in `load_image` with `std::panic::catch_unwind` at the codec boundary only, mapping a codec panic to `LoadError::Io` with the codec's name. Done when: a fuzzed corpus file (random bytes written over the pixel data in the test's temporary folder) returns an error and the test process survives. Cheaper substitute: `catch_unwind` around the whole app must fail review; the boundary is the third-party decoder.
- [ ] Commit: `dicom: named refusals for bad files`

**Test checkpoint:** `cargo test --test load_errors` passes with one test per `LoadError` variant; removing the truncation check makes the truncated-file test fail.

## 3. Folder and DICOMDIR scan into studies and series

A study arrives as a folder of hundreds of files, often with meaningless names, or as a disc with a `DICOMDIR` index. The scan reads only headers, groups images by study and series, and orders them, so the series strip (D02 T01 §5) can appear while no pixel has been decoded.

**Phase:** 2
**Needs:** none
**Surface:** no

**Build order:**

1. Define `Study`, `Series` and `ImageRef` in `src/dicom/study.rs` and write `scan` in `src/dicom/scan.rs`. Done when: a corpus folder scans into the expected groups.
2. Read `DICOMDIR` when present, and log every skipped file. Done when: the `DICOMDIR` test and the mixed-folder test pass.

- [ ] Define `Study` (UID, patient name, patient ID, date, description), `Series` (UID, modality, description, number, `images`) and `ImageRef` (path, frame, instance number, position, orientation, SOP instance UID) in `src/dicom/study.rs`. Done when: `cargo build` exits 0.
- [ ] Write `scan(path)` in `src/dicom/scan.rs`: walk the folder, read each file's header up to but not including the pixel data with `dicom-object`'s read-until option, in parallel with `rayon`, and group by `StudyInstanceUID` and `SeriesInstanceUID`. Done when: `tests/scan.rs` builds a folder of corpus files from two series and asserts two `Series` with the right image counts. Cheaper substitute: decoding pixels during the scan must fail; the test asserts the scan of a 200-file phantom folder finishes without any call into `dicom-pixeldata` (a counter in the test build).
- [ ] Order each series' `images` in `scan` by position along the slice normal (from `ImagePositionPatient` and `ImageOrientationPatient`), falling back to `InstanceNumber`, then to file name. Done when: a test with files written in shuffled order gets them back in spatial order.
- [ ] Read a `DICOMDIR` file in `src/dicom/dicomdir.rs` when `scan` is given one or finds one at the folder root, resolving each referenced file path case-insensitively. Done when: a test `DICOMDIR` built over corpus files yields the same studies as the folder walk.
- [ ] Skip files that are not DICOM or have no pixel data during `scan`, logging one line each with the path and the `LoadError`. Done when: a folder with a text file, a shortcut and a structured report scans without error and the log has three skip lines.
- [ ] Return `ScanError::NothingFound` from `scan` when no image was found, with the folder path and the count of files looked at. Done when: a test on an empty folder and on a folder of text files gets that error.
- [ ] Bound the walk in `scan` to 8 folder levels and never follow links or junctions. Done when: a test folder holding a junction to its own parent scans once and ends.
- [ ] Commit: `dicom: scan folders and DICOMDIR into studies and series`

**Test checkpoint:** `cargo test --test scan` passes; reversing the sort in `scan` fails the shuffled-order test.

## 4. Background series loading with the first slice first

Fast opening means the first image shows while the rest is still on disk. This section loads the image the user is looking at first, then the others outward from it, off the interface thread, and lets a newer request cancel an older one.

**Phase:** 2
**Needs:** none
**Surface:** no

**Build order:**

1. Write `SeriesLoader` in `src/dicom/loader.rs` with a priority order and a channel of results. Done when: the order test passes.
2. Add cancellation and a memory bound. Done when: the cancel test and the bound test pass.

- [ ] Write `SeriesLoader::start(series, first_index)` in `src/dicom/loader.rs`: decode `first_index` first, then the remaining images alternating outward from it, on the `rayon` pool, sending each result with its index over a channel. Done when: `tests/loader.rs` asserts the first message received is `first_index` for a 50-image phantom series.
- [ ] Add `SeriesLoader::cancel()` in `src/dicom/loader.rs`, checked before each decode, and call it when the loader is dropped. Done when: a test that cancels after the first result receives no more than the images already in flight, and no thread is left running after the test.
- [ ] Add `SeriesLoader::reprioritise(index)` in `src/dicom/loader.rs` so scrolling moves the decode order to the slice now on screen. Done when: a test that reprioritises to the last index receives it before the middle indices.
- [ ] Report a failed image from `SeriesLoader` as an indexed `LoadError` and carry on with the rest. Done when: a series with one truncated file delivers every other image and one error for that index. Cheaper substitute: aborting the whole series on one bad slice must fail.
- [ ] Hold decoded images in `src/dicom/cache.rs` behind a byte budget (default 2 GB or half of physical memory, whichever is smaller), dropping the slices furthest from the current one first. Done when: a test with a small budget shows the cache size never exceeds it while scrolling a phantom series end to end.
- [ ] Commit: `dicom: background series loading, first slice first`

**Test checkpoint:** `cargo test --test loader` passes; decoding in plain index order instead of outward from `first_index` fails the order test when `first_index` is not 0.

## 5. Multi-frame files opened as series

Newer MRI exports put a whole series in one enhanced multi-frame file, with the geometry held per frame. Such a file must appear as an ordinary series so stack scrolling and volume building need no special case.

**Phase:** 2
**Needs:** none
**Surface:** no

**Build order:**

1. Read frame count and per-frame geometry in `src/dicom/multiframe.rs`. Done when: a multi-frame corpus file yields one `ImageRef` per frame.
2. Decode a single frame without decoding the whole file. Done when: the single-frame test passes.

- [ ] Read `NumberOfFrames` (0028,0008) in `scan` and expand a multi-frame file into one `ImageRef` per frame in `src/dicom/multiframe.rs`. Done when: `tests/multiframe.rs` asserts the frame count of a multi-frame corpus file.
- [ ] Read each frame's position, orientation, spacing and pixel value transformation from the per-frame and shared functional group sequences (5200,9230 and 5200,9229) in `src/dicom/multiframe.rs`. Done when: a phantom enhanced MR file written by the test yields the positions it was written with.
- [ ] Decode one frame by index in `load_image` using the `dicom-pixeldata` per-frame decode, for native and encapsulated pixel data. Done when: a test decodes frame 3 of a multi-frame file and its pixels equal frame 3 of a whole-file decode. Cheaper substitute: decoding every frame to return one must fail; the test asserts the single-frame call on a large phantom is at least five times faster than the whole-file decode.
- [ ] Treat a multi-frame file with no per-frame geometry (ultrasound-style cine) as a stack ordered by frame number. Done when: a corpus file of that kind scans into one series and its `ImageRef` positions are `None`.
- [ ] Commit: `dicom: multi-frame files as series`

**Test checkpoint:** `cargo test --test multiframe` passes; ignoring the per-frame functional groups fails the phantom position test.

## Verification

- `voxel::dicom::scan` on a folder holding the whole corpus returns every decodable image grouped and ordered, and the log lists each skipped file with its reason.
- No test in `tests/load_errors.rs`, `tests/scan.rs`, `tests/loader.rs` or `tests/multiframe.rs` can make the process panic.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
