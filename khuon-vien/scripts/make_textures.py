"""Generate tileable PBR textures (albedo + normal) procedurally with numpy, inside Blender.
Usage: blender -b --factory-startup --python scripts/make_textures.py
Output: textures/<name>_albedo.png, textures/<name>_normal.png
Each texture tiles seamlessly; the build scripts map them with world-space box UVs (see 'tile_m').
"""
import bpy, json, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "textures")
os.makedirs(OUT, exist_ok=True)
SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "ta1.json"), encoding="utf-8"))
C = SPEC["colors"]
N = 1024
rng = np.random.default_rng(7)


def hexrgb(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)


def periodic(cx, cy, n=N):
    """Tileable value noise with cx x cy cells, smooth-interpolated, range 0..1."""
    g = rng.random((cy, cx)).astype(np.float32)
    x = np.arange(n) * cx / n; y = np.arange(n) * cy / n
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    fx = x - x0; fy = y - y0
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    x1 = (x0 + 1) % cx; y1 = (y0 + 1) % cy
    a = g[np.ix_(y0, x0)]; b = g[np.ix_(y0, x1)]; c = g[np.ix_(y1, x0)]; d = g[np.ix_(y1, x1)]
    fx = fx[None, :]; fy = fy[:, None]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def fbm(cells, weights):
    out = sum(w * periodic(c, c) for c, w in zip(cells, weights))
    return out / sum(weights)


def normal_from_height(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    nz = np.ones_like(h)
    n = np.stack([-dx, -dy, nz], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def save(name, rgb, non_color=False):
    h, w = rgb.shape[:2]
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.ones((h, w, 1), np.float32)], -1)
    img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=False)
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    img.pixels = rgba.ravel()
    img.filepath_raw = os.path.join(OUT, name + ".png"); img.file_format = "PNG"; img.save()


def srgb_tint(hexcol, value):
    """value ~1.0 around the base colour; returns an sRGB image."""
    return np.clip(hexrgb(hexcol)[None, None, :] * value[..., None], 0, 1)


# ---------------------------------------------------------------- painted render (walls, fins, slabs)
low = fbm([3, 6, 12], [1, .6, .35])
mid = fbm([24, 48], [1, .6])
fine = fbm([180, 360], [1, .7])
streak = periodic(90, 2)                                       # vertical rain streaks
pores = (rng.random((N, N)) > 0.9985).astype(np.float32)
pores = np.maximum(pores, np.roll(pores, 1, 0) * .6)
value = 1 + (low - .5) * .16 + (mid - .5) * .07 + (fine - .5) * .05 - (streak - .5).clip(0) * .09 - pores * .15
height = fine * .7 + mid * .3 - pores * 1.5
nrm = normal_from_height(height, 2.2)
for name, key in (("paint_wall", "wall_main"), ("paint_fin", "fin"), ("paint_slab", "slab"), ("paint_dark", "opening")):
    save(name + "_albedo", srgb_tint(C[key], value))
save("paint_normal", nrm, True)

# TB2 palette: cream / grey-blue paint + brown podium tiles
TB2 = json.load(open(os.path.join(ROOT, "layout", "buildings", "tb2.json"), encoding="utf-8"))["colors"]
for name, key in (("paint_cream", "cream"), ("paint_grey", "grey")):
    save(name + "_albedo", srgb_tint(TB2[key], value))
save("paint_cream_dark_albedo", srgb_tint("#cbbd9c", value))
yy0, xx0 = np.mgrid[0:N, 0:N].astype(np.float32) / N
trow = np.floor(yy0 * 4).astype(int)                         # 1.2 m tile: 2 x 4 tiles of 0.6 x 0.3 m
txs = xx0 * 2 + (trow % 2) * .5
tcol = np.floor(txs).astype(int) % 2
tbx = txs - np.floor(txs); tby = yy0 * 4 - trow
grout = ((tbx < .015) | (tbx > .985) | (tby < .03) | (tby > .97)).astype(np.float32)
tvar = rng.random((4, 2)).astype(np.float32)[trow, tcol]
v = (1 + (tvar - .5) * .16 + (fine - .5) * .06) * (1 - grout) + grout * .7
save("podium_tile_albedo", srgb_tint(TB2["podium"], v))
save("podium_tile_normal", normal_from_height(1 - grout * .7 + fine * .05, 3.0), True)

# HĐ palette: dark grey frame + brown-grey fins
HD = json.load(open(os.path.join(ROOT, "layout", "buildings", "hd.json"), encoding="utf-8"))["colors"]
for name, key in (("paint_hd_frame", "grey_frame"), ("paint_hd_fin", "fin"), ("paint_hd_cream", "cream"), ("paint_hd_cream_dark", "cream_dark")):
    save(name + "_albedo", srgb_tint(HD[key], value))

# ---------------------------------------------------------------- roof concrete with stains
stain = fbm([4, 8, 16], [1, .7, .4])
v = 1 + (fine - .5) * .12 - (stain - .45).clip(0) * .5
save("roof_albedo", srgb_tint("#a9acaa", v))

# ---------------------------------------------------------------- granite steps
speck = rng.random((N, N)).astype(np.float32)
v = 1 + (fbm([60, 200], [1, .8]) - .5) * .25 + (speck > .97) * .25 - (speck < .03) * .3
save("granite_albedo", srgb_tint(C["steps"], v))
save("granite_normal", normal_from_height(fbm([200, 400], [1, .5]), 1.2), True)

# ---------------------------------------------------------------- brushed metal (louvers)
brush = periodic(3, 400) * .6 + periodic(8, 900) * .4
save("metal_albedo", srgb_tint(C["louver"], 1 + (brush - .5) * .2))

# ---------------------------------------------------------------- brick pavers (1 m tile: 5 x 10 bricks, running bond)
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / N
rows = 10; cols = 5
r = np.floor(yy * rows).astype(int)
xs = xx * cols + (r % 2) * .5
c = np.floor(xs).astype(int) % cols
bx = xs - np.floor(xs); by = yy * rows - r
mortar = ((bx < .04) | (bx > .96) | (by < .07) | (by > .93)).astype(np.float32)
brick_var = rng.random((rows, cols)).astype(np.float32)[r, c]
v = (1 + (brick_var - .5) * .3 + (fine - .5) * .15) * (1 - mortar) + mortar * .62
alb = srgb_tint(C["brick"], v) * (1 - mortar[..., None]) + mortar[..., None] * hexrgb("#8d8a84")[None, None, :]
save("brick_albedo", alb)
save("brick_normal", normal_from_height(1 - mortar * .8 + fine * .15, 3.0), True)

# ---------------------------------------------------------------- red roof tiles (0.5 m tile)
rows = 4
by = (yy * rows) % 1
ridge = np.abs(np.sin(xx * np.pi * 6))
v = (.75 + .35 * ridge) * (1 - .25 * (by < .12)) * (1 + (mid - .5) * .2)
save("tile_albedo", srgb_tint(C["tile_red"], v))
save("tile_normal", normal_from_height(ridge * .6 + (by > .12) * .3, 4.0), True)

TILE = {"podium": 1.2, "paint": 4.0, "roof": 6.0, "granite": 1.5, "metal": 2.0, "brick": 1.0, "tile": 1.0}
json.dump(TILE, open(os.path.join(OUT, "tile_sizes.json"), "w"))
print("TEXTURES DONE", sorted(os.listdir(OUT)))
