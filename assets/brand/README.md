# Voxel brand assets

The "Lattice" identity, chosen by the owner on 2026-11-17: a cube with one bright voxel at its near corner, in the slate and signal blue of the Conclave Design System v2, so Voxel sits in the same family as the owner's other tools.

## Files

| File | What it is | Use it for |
| ---- | ---------- | ---------- |
| `voxel-mark.svg` | The cube alone, no tile, transparent | Inside the app, beside the wordmark |
| `voxel-icon.svg` | The app icon: the cube in its slate tile | 48 pixels and up |
| `voxel-icon-small.svg` | A heavier icon with a larger voxel | Under 48 pixels |
| `voxel-wordmark.svg`, `voxel-wordmark-light.svg` | The wordmark for dark and for light grounds | Headers, the About window |
| `voxel-lockup.svg`, `voxel-lockup-light.svg` | Mark and wordmark together (generated) | Documents, the README |
| `voxel-icon-64.png`, `-192.png`, `-512.png`, `-1024.png` | Icon renders (generated) | Where SVG is not accepted |
| `voxel.ico` | Windows icon, 16 to 256 pixels (generated) | The exe, the window, shortcuts |
| `social-preview.png` | 1280 by 640 (generated) | The GitHub repository's social preview |
| `banner-dark.png`, `banner-light.png` | 1280 by 320 at 2x (generated) | The top of `README.md`, by colour scheme |

The five hand-drawn SVG files are the sources. Everything marked generated is written by `python scripts/render-brand.py`, which needs Microsoft Edge and Pillow; run it after changing a source and commit the results.

## Colours

The names are the Conclave Design System v2 tokens; the three cube shades below signal are Voxel's own.

| Name | Dark | Light | Use |
| ---- | ---- | ----- | --- |
| `ground` | `#131a22` | `#f2f5f8` | Behind everything |
| `surface` | `#1b232c` | `#fcfdff` | The icon tile, panels |
| `ink` | `#edf0f4` | `#151e27` | Text, the wordmark, the voxel's top face |
| `signal` | `#34c8fd` | `#0075b1` | The cube's top face, the O of the wordmark, the one accent |
| `signal-ink` | `#4bcefd` | `#006ba9` | The accent as small text |
| Cube left | `#1a86b4` | same | The cube's left face |
| Cube right | `#0f5778` | same | The cube's right face |
| Voxel left, voxel right | `#a9e6fe`, `#74d8fd` | same | The bright voxel's side faces |

## Type

Archivo, slightly condensed (width 88), for display; IBM Plex Sans for text; IBM Plex Mono for figures and identifiers. All three are under the SIL Open Font License. The wordmark is drawn as strokes, not set in a font, so it never depends on one.

## Rules

- The hexagon O is the only signal stroke in the wordmark; never recolour the other letters.
- Keep clear space around the mark of at least the width of the bright voxel.
- Never stretch or rotate the cube, never put it on a signal fill, and never recolour its faces.
- Under 48 pixels use the small icon: its voxel is larger so it survives at that size.
