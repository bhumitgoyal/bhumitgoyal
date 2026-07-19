#!/usr/bin/env python3
"""Convert scripts/source-prepped.png into a self-typing monochrome ASCII SVG.

The prepped image is downsampled to a character grid; each cell's brightness
picks a glyph from a density ramp (sparse = bright, dense = dark). Each row is
revealed left-to-right by a SMIL clip wipe, staggered top to bottom, with a
block cursor riding the newest row. Prints once and freezes — no looping.
GitHub renders SMIL inside <img>-embedded SVGs, so it animates on your profile.

    python scripts/make_ascii_svg.py            # animated
    STATIC=1 python scripts/make_ascii_svg.py    # frozen frame (local preview)
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "source-prepped.png"
OUT = ROOT / "ascii.svg"
STATIC = os.environ.get("STATIC") == "1"

# bright (sparse) -> dark (dense); leading space clears the background to nothing
RAMP = " .`:-=+*cs#%@"

COLS = 100
CHAR_ASPECT = 0.5   # monospace cell height ~2x its width
FONT_SIZE = 8
CHAR_W = FONT_SIZE * 0.6
LINE_H = FONT_SIZE * 1.05

FONT = "'SF Mono','JetBrains Mono','Fira Code',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
INK = "#c9d1d9"      # one light-gray fill — monochrome keeps it clean, not noisy
CURSOR = "#39d353"
PANEL = "#0d1117"
BORDER = "#21262d"

PAD = 16
ROW_DELAY = 0.032   # stagger between rows
ROW_DUR = 0.42      # wipe duration per row


def to_grid() -> list[str]:
    if not SRC.exists():
        raise SystemExit(
            f"missing {SRC.relative_to(ROOT)} — run: python scripts/prep_photo.py <photo>"
        )
    img = Image.open(SRC).convert("L")
    rows = max(1, round(COLS * (img.height / img.width) * CHAR_ASPECT))
    small = img.resize((COLS, rows))
    px = np.array(small)

    n = len(RAMP) - 1
    lines: list[str] = []
    for r in range(rows):
        chars = []
        for c in range(COLS):
            b = int(px[r, c])
            idx = round((255 - b) / 255 * n)
            chars.append(RAMP[idx])
        lines.append("".join(chars).rstrip() or " ")
    # trim fully-blank leading/trailing rows
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(lines: list[str]) -> str:
    grid_w = COLS * CHAR_W
    width = grid_w + PAD * 2
    height = len(lines) * LINE_H + PAD * 2

    text_rows: list[str] = []
    clips: list[str] = []
    cursors: list[str] = []

    for i, line in enumerate(lines):
        y = PAD + (i + 1) * LINE_H - LINE_H * 0.25
        row_w = len(line) * CHAR_W
        begin = i * ROW_DELAY

        if STATIC:
            clip_attr = ""
        else:
            cid = f"w{i}"
            clips.append(
                f'<clipPath id="{cid}"><rect x="{PAD:.1f}" y="{PAD + i * LINE_H:.1f}" '
                f'width="0" height="{LINE_H:.1f}">'
                f'<animate attributeName="width" from="0" to="{row_w:.1f}" '
                f'begin="{begin:.3f}s" dur="{ROW_DUR}s" fill="freeze" '
                f'calcMode="spline" keySplines="0.22 0.61 0.36 1" keyTimes="0;1"/>'
                f'</rect></clipPath>'
            )
            clip_attr = f' clip-path="url(#{cid})"'
            # block cursor rides the wipe edge, then vanishes when the row lands
            cursors.append(
                f'<rect x="{PAD:.1f}" y="{PAD + i * LINE_H + 1:.1f}" width="{CHAR_W:.1f}" '
                f'height="{LINE_H - 2:.1f}" fill="{CURSOR}" opacity="0">'
                f'<animate attributeName="x" from="{PAD:.1f}" to="{PAD + row_w:.1f}" '
                f'begin="{begin:.3f}s" dur="{ROW_DUR}s" fill="freeze" '
                f'calcMode="spline" keySplines="0.22 0.61 0.36 1" keyTimes="0;1"/>'
                f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.05;0.85;1" '
                f'begin="{begin:.3f}s" dur="{ROW_DUR}s" fill="freeze"/>'
                f'</rect>'
            )

        text_rows.append(
            f'<text{clip_attr} x="{PAD:.1f}" y="{y:.1f}" textLength="{row_w:.1f}" '
            f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{esc(line)}</text>'
        )

    # blinking cursor parked at the end, after the whole portrait has printed
    total = len(lines) * ROW_DELAY + ROW_DUR
    end_cursor = "" if STATIC else (
        f'<rect x="{PAD:.1f}" y="{PAD + (len(lines) - 1) * LINE_H + 1:.1f}" '
        f'width="{CHAR_W:.1f}" height="{LINE_H - 2:.1f}" fill="{CURSOR}" opacity="0">'
        f'<animate attributeName="opacity" values="0;1;0;1;0;1" '
        f'begin="{total:.2f}s" dur="2.4s" repeatCount="indefinite" keyTimes="0;0.16;0.33;0.5;0.66;1"/>'
        f'</rect>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="ASCII portrait">
  <style>
    text {{ font-family: {FONT}; font-size: {FONT_SIZE}px; fill: {INK}; white-space: pre; }}
  </style>
  <rect x="0.5" y="0.5" width="{width - 1:.1f}" height="{height - 1:.1f}" rx="10" fill="{PANEL}" stroke="{BORDER}"/>
  <defs>{''.join(clips)}</defs>
  <g>{''.join(text_rows)}</g>
  <g>{''.join(cursors)}{end_cursor}</g>
</svg>
"""


def main() -> int:
    lines = to_grid()
    OUT.write_text(build(lines))
    print(f"Wrote {OUT.relative_to(ROOT)} ({COLS}x{len(lines)} chars, {'static' if STATIC else 'animated'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
