#!/usr/bin/env python3
"""Image helpers for the Mood Screen generative test.

Usage:
  python3 scripts/screen_image.py compress SRC.png OUT.webp
      Resize to at most 1200 px on the long side and save as WebP (quality 80).
      Falls back to JPEG next to OUT when Pillow has no WebP encoder.
  python3 scripts/screen_image.py compare ORIGINAL GENERATED [GENERATED ...]
      Measured evidence for the judges, one row per generated image:
        palette_de  k-means 5 colours in Lab (5% border cropped); each original
                    colour matched to its nearest generated colour, weighted by
                    its share. Lower is closer. Under 5 reads as the same palette.
        layout_r    correlation of 40x60 greyscale thumbnails. Higher means the
                    layout changed less. For a B image a low value is the goal.
      The numbers support the scores; they are not the scores.

Needs Pillow and numpy (pip install pillow numpy). Prints JSON.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

MAX_SIDE = 1200


def compress(src, out):
    im = Image.open(src).convert("RGB")
    im.thumbnail((MAX_SIDE, MAX_SIDE))
    try:
        im.save(out, "WEBP", quality=80, method=6)
    except (OSError, KeyError):
        out = os.path.splitext(out)[0] + ".jpg"
        im.save(out, "JPEG", quality=82, optimize=True, progressive=True)
    return {"file": out, "bytes": os.path.getsize(out), "size": im.size}


def lab(rgb):
    """sRGB (0-255, Nx3) to CIE Lab (D65)."""
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], axis=1)


def palette(path, k=5, iters=25):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    im = im.crop((int(w * 0.05), int(h * 0.05), int(w * 0.95), int(h * 0.95))).resize((120, 120))
    px = lab(np.asarray(im, dtype=float).reshape(-1, 3))
    rng = np.random.default_rng(0)  # fixed seed: the same image always gives the same palette
    centres = px[rng.choice(len(px), k, replace=False)]
    for _ in range(iters):
        near = np.argmin(((px[:, None] - centres[None]) ** 2).sum(-1), axis=1)
        centres = np.array([px[near == i].mean(0) if (near == i).any() else centres[i] for i in range(k)])
    share = np.bincount(near, minlength=k) / len(px)
    return centres, share


def palette_de(orig, gen):
    oc, osh = palette(orig)
    gc, _ = palette(gen)
    d = np.sqrt(((oc[:, None] - gc[None]) ** 2).sum(-1)).min(1)
    return float((d * osh).sum())


def layout_r(orig, gen):
    a, b = (np.asarray(Image.open(p).convert("L").resize((40, 60)), dtype=float).ravel() for p in (orig, gen))
    if a.std() == 0 or b.std() == 0:
        return 0.0  # a flat image has no layout to compare
    return float(np.corrcoef(a, b)[0, 1])


def main(argv):
    if len(argv) == 3 and argv[0] == "compress":
        print(json.dumps(compress(argv[1], argv[2])))
        return 0
    if len(argv) >= 3 and argv[0] == "compare":
        rows = [{"file": g, "palette_de": round(palette_de(argv[1], g), 1), "layout_r": round(layout_r(argv[1], g), 3)} for g in argv[2:]]
        print(json.dumps(rows, indent=2))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
