#!/usr/bin/env python3
"""Prep a photo for ASCII conversion.

A flatly-lit face converts to a dark, unreadable blob. Three fixes:
  1. Remove the background with rembg so the subject is isolated.
  2. Boost local contrast with OpenCV CLAHE (gives a flat face real
     highlights and shadows).
  3. Composite onto pure white so the background maps to the blank end of
     the ASCII ramp (white -> spaces).

Output: scripts/source-prepped.png (grayscale). Run once per photo:

    python scripts/prep_photo.py path/to/photo.jpg
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# Optional HEIC/HEIF support (iPhone photos) if pillow-heif is installed.
try:  # pragma: no cover
    import pillow_heif  # type: ignore

    pillow_heif.register_heif_opener()
except Exception:
    pass

from rembg import remove

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "scripts" / "source-prepped.png"

# Portraits look best cropped fairly tight; cap the working size for speed.
MAX_SIDE = 1000


def load(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    if max(img.size) > MAX_SIDE:
        scale = MAX_SIDE / max(img.size)
        img = img.resize((round(img.width * scale), round(img.height * scale)))
    return img


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/prep_photo.py <photo>", file=sys.stderr)
        return 2
    src = Path(sys.argv[1]).expanduser()
    if not src.exists():
        print(f"no such file: {src}", file=sys.stderr)
        return 1

    img = load(src)

    # 1. isolate the subject
    cut = remove(img)  # RGBA with transparent background
    alpha = np.array(cut.split()[-1])
    mask = alpha > 40  # subject pixels

    # 2. composite onto pure white
    white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(white, cut).convert("L")
    gray = np.array(comp)

    # 3. CLAHE local-contrast boost (only meaningful on the subject)
    clahe = cv2.createCLAHE(clipLimit=2.4, tileGridSize=(8, 8))
    boosted = clahe.apply(gray)

    # keep the background pure white so it maps to spaces
    boosted[~mask] = 255

    # 4. crop to the subject so it fills the ASCII grid (drop empty margins)
    ys, xs = np.where(mask)
    if len(xs):
        pad_x = int(0.05 * (xs.max() - xs.min() + 1))
        pad_y = int(0.05 * (ys.max() - ys.min() + 1))
        x0 = max(0, xs.min() - pad_x)
        x1 = min(boosted.shape[1], xs.max() + pad_x + 1)
        y0 = max(0, ys.min() - pad_y)
        y1 = min(boosted.shape[0], ys.max() + pad_y + 1)
        boosted = boosted[y0:y1, x0:x1]

    Image.fromarray(boosted).save(OUT)
    print(f"Wrote {OUT.relative_to(ROOT)} ({boosted.shape[1]}x{boosted.shape[0]})")
    print("Next: python scripts/make_ascii_svg.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
