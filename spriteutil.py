import pyxel

# fmt: off
_PALETTE = [
    (  0,   0,   0), ( 29,  43,  83), (126,  37,  83), (  0, 135,  81),
    (171,  82,  54), ( 95,  87,  79), (194, 195, 199), (255, 241, 232),
    (255,   0,  77), (255, 163,   0), (255, 236,  39), (  0, 228,  54),
    ( 41, 173, 255), (131, 118, 156), (255, 119, 168), (255, 204, 170),
]
# fmt: on


def _nearest(r, g, b):
    best, best_d = 0, float("inf")
    for i, (pr, pg, pb) in enumerate(_PALETTE):
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < best_d:
            best, best_d = i, d
    return best


def load_ppm(bank, dst_x, dst_y, path):
    """Load a P3 PPM file into a Pyxel image bank at (dst_x, dst_y)."""
    with open(path) as f:
        lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
    assert lines[0] == "P3", f"Not a P3 PPM: {path}"
    w, h = map(int, lines[1].split())
    # lines[2] is max_val; skip it
    vals = list(map(int, " ".join(lines[3:]).split()))
    img = pyxel.image(bank)
    idx = 0
    for y in range(h):
        for x in range(w):
            r, g, b = vals[idx], vals[idx + 1], vals[idx + 2]
            idx += 3
            img.pset(dst_x + x, dst_y + y, _nearest(r, g, b))
