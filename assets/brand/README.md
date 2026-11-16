# Voxel brand assets

The "Lightbox" identity, chosen by the owner on 2026-11-17: warm charcoal and film amber, with a mark of three stacked scan slices and a cross-section cut into the top one.

## Files

| File | What it is | Use it for |
| ---- | ---------- | ---------- |
| `voxel-mark.svg` | The mark alone, no tile, transparent | Inside the app, beside the wordmark |
| `voxel-icon.svg` | The app icon: the mark in its charcoal tile | 48 pixels and up |
| `voxel-icon-small.svg` | A heavier icon without the cross-section | Under 48 pixels |
| `voxel-wordmark.svg`, `voxel-wordmark-light.svg` | The wordmark for dark and for light grounds | Headers, the About window |
| `voxel-lockup.svg`, `voxel-lockup-light.svg` | Mark and wordmark together (generated) | Documents, the README |
| `voxel-icon-64.png`, `-192.png`, `-512.png`, `-1024.png` | Icon renders (generated) | Where SVG is not accepted |
| `voxel.ico` | Windows icon, 16 to 256 pixels (generated) | The exe, the window, shortcuts |
| `social-preview.png` | 1280 by 640 (generated) | The GitHub repository's social preview |
| `banner-dark.png`, `banner-light.png` | 1280 by 320 at 2x (generated) | The top of `README.md`, by colour scheme |

The five hand-drawn SVG files are the sources. Everything marked generated is written by `python scripts/render-brand.py`, which needs Microsoft Edge and Pillow; run it after changing a source and commit the results.

## Colours

| Name | Hex | Use |
| ---- | --- | --- |
| Charcoal | `#17140F` | The ground behind everything |
| Film | `#231E16` | The icon tile and raised surfaces |
| Deep amber | `#7A5200` | The lowest slice |
| Mid amber | `#C48700` | The middle slice |
| Amber | `#FFB000` | The top slice and the one accent |
| Cream | `#FFF3D6` | Text and the wordmark on dark; the light ground |

On a light ground the amber accent is `#B37400` in the wordmark and `#8A5A00` for small text, so it keeps its contrast.

## Type

DM Sans for text and DM Mono for figures and identifiers, both under the SIL Open Font License. The wordmark is drawn as strokes, not set in a font, so it never depends on one.

## Rules

- The wordmark's middle bar of the E is the only amber stroke; never recolour the other letters.
- Keep clear space around the mark of at least half the height of one slice.
- Never stretch the mark, never put it on amber, and never draw the slices without their gaps.
- Under 48 pixels use the small icon: the cross-section does not survive at that size.
