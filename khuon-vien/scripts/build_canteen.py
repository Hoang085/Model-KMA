"""B4 – build the Canteen (+ green-shutter store) from layout/buildings/canteen.json.
Usage: blender -b --factory-startup --python scripts/build_canteen.py
Outputs: blender/canteen.blend, export/CANTEEN.fbx, export/CANTEEN.glb
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lib import Builder, Face, ROOT, TILE
from mathutils import Vector

SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "canteen.json"), encoding="utf-8"))
C, K = SPEC["colors"], SPEC["canteen"]
LV, BD = K["levels"], K["balcony"]
F1 = LV["plinth"]
F2 = F1 + LV["f1_h"]
F3 = F2 + LV["f2_h"]
EAVE = F3 + LV["f3_h"]
RIDGE = EAVE + K["roof"]["rise"]
OV = K["roof"]["overhang"]
X0, Y0, X1, Y1 = K["rect"]
AX0, AY0, AX1, AY1 = K["annex"]["rect"]
AH = K["annex"]["h"]

B = Builder("CANTEEN")
paint = TILE.get("paint", 4)
B.material("yellow", C["yellow"], 0.9, 0, None, "paint_normal", tile=paint)
B.material("yellow_dark", C["yellow_dark"], 0.9)
B.material("frame", C["white_frame"], 0.5)
B.material("glass", C["glass"], 0.05, 0.2)
B.material("stone", C["stone_band"], 0.8, 0, "granite_albedo", "granite_normal", 0.5, tile=TILE.get("granite", 1.5))
B.material("plinth", C["plinth"], 0.8, 0, "granite_albedo", "granite_normal", 0.5, tile=TILE.get("granite", 1.5))
B.material("rail", C["rail"], 0.4, 0.6)
B.material("roof", C["roof_tile"], 0.8, 0, "tile_albedo", "tile_normal", 0.8, tile=TILE.get("tile", 1.0))
B.material("annex", C["annex"], 0.6, 0.3)
B.material("shutter", C["annex_shutter"], 0.5, 0.5, "metal_albedo", None, tile=TILE.get("metal", 2))
B.material("slab", "#cfd2d4", 0.8)

SOUTH = Face(B, (X0, Y0, 0), (1, 0, 0), (0, -1, 0), X1 - X0)       # u = x − 47.1
WEST = Face(B, (X0, Y1, 0), (0, -1, 0), (-1, 0, 0), Y1 - Y0)       # u = 118 − y
NORTH = Face(B, (X1, Y1, 0), (-1, 0, 0), (0, 1, 0), X1 - X0)
EAST = Face(B, (X1, Y0, 0), (0, 1, 0), (1, 0, 0), Y1 - Y0)


def extrude(f, key, outline, w0, w1):
    """Closed solid from a (u, z) outline pushed out from w0 to w1 on face f."""
    bm = B.bm[key]
    a = [bm.verts.new(f.P(u, w0, z)) for u, z in outline]
    b = [bm.verts.new(f.P(u, w1, z)) for u, z in outline]
    n = len(outline)
    bm.faces.new(a[::-1]); bm.faces.new(b)
    for i in range(n):
        bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))


def arch_outline(cu, z0, w, h, grow=0.0):
    r = w / 2 + grow
    zs = z0 + h - w / 2
    return [(cu - r, z0 - grow), (cu + r, z0 - grow)] + \
           [(cu + r * math.cos(math.pi * k / 10), zs + r * math.sin(math.pi * k / 10)) for k in range(0, 11)]


def arch_window(f, cu, z0, w, h):
    extrude(f, "frame", arch_outline(cu, z0, w, h, 0.12), 0.0, 0.05)
    extrude(f, "glass", arch_outline(cu, z0, w, h), 0.05, 0.08)
    zs = z0 + h - w / 2
    f.box("frame", cu - 0.03, cu + 0.03, 0.08, 0.12, z0, z0 + h)
    f.box("frame", cu - w / 2, cu + w / 2, 0.08, 0.12, zs - 0.03, zs + 0.03)
    f.box("frame", cu - w / 2, cu + w / 2, 0.08, 0.12, z0 + (zs - z0) / 2 - 0.02, z0 + (zs - z0) / 2 + 0.02)


def rect_window(f, u0, u1, z0, z1, proud=0.0):
    t = 0.08
    f.box("glass", u0, u1, proud, proud + 0.04, z0, z1)
    for a, b, c, d in ((u0 - t, u1 + t, z0 - t, z0), (u0 - t, u1 + t, z1, z1 + t), (u0 - t, u0, z0, z1), (u1, u1 + t, z0, z1)):
        f.box("frame", a, b, proud, proud + 0.08, c, d)
    f.box("frame", (u0 + u1) / 2 - 0.03, (u0 + u1) / 2 + 0.03, proud, proud + 0.07, z0, z1)


def arcade_face(f, bays, ext0=0.0):
    step = f.W / bays
    for i in range(bays):
        cu = step * (i + 0.5)
        arch_window(f, cu, F1 + 0.3, K["arch"]["w"], K["arch"]["h"])
        rect_window(f, cu - 0.8, cu + 0.8, F2 + 1.15, F2 + 2.7)
        rect_window(f, cu - 0.8, cu + 0.8, F3 + 0.3, F3 + 2.5)
    b0, b1 = K["band"]
    f.box("stone", -0.02, f.W + 0.02, 0, 0.1, b0, b1)
    d = BD["depth"]
    # F2 balcony: slab + solid yellow parapet
    f.box("yellow_dark", -ext0, f.W, 0, d, F2 - 0.2, F2)
    f.box("yellow", -ext0, f.W, d - 0.15, d, F2, F2 + BD["f2_parapet_h"])
    f.box("yellow_dark", -ext0, f.W, d - 0.2, d + 0.05, F2 + BD["f2_parapet_h"], F2 + BD["f2_parapet_h"] + 0.06)
    # F3 balcony: slab + green railing
    f.box("yellow", -ext0, f.W, 0, d, F3 - 0.3, F3)
    f.box("rail", -ext0, f.W, d - 0.1, d, F3 + BD["f3_rail_h"] - 0.06, F3 + BD["f3_rail_h"])
    u = -ext0
    while u <= f.W:
        f.box("rail", u - 0.015, u + 0.015, d - 0.08, d - 0.05, F3, F3 + BD["f3_rail_h"]); u += 0.3


def plain_face(f, n):
    step = f.W / n
    for z in (F1 + 1.0, F2 + 1.0, F3 + 1.0):
        for i in range(n):
            cu = step * (i + 0.5)
            rect_window(f, cu - 0.65, cu + 0.65, z, z + 1.5)
    f.box("yellow_dark", 0, f.W, 0, 0.08, F2 - 0.15, F2 + 0.15)


# ================================================================== masses
B.wbox("yellow", X0, X1, Y0, Y1, 0, EAVE)
for f in (SOUTH, WEST, NORTH, EAST):
    f.box("plinth", 0, f.W, 0, 0.06, 0, F1)
B.wbox("yellow_dark", X0 - OV, X1 + OV, Y0 - OV, Y1 + OV, EAVE - 0.3, EAVE)      # eave fascia / soffit
hw = (Y1 - Y0) / 2 + OV
ex0, ex1, ey0, ey1 = X0 - OV, X1 + OV, Y0 - OV, Y1 + OV
bm = B.bm["roof"]
v = {k: bm.verts.new(p) for k, p in {"a": (ex0, ey0, EAVE), "b": (ex1, ey0, EAVE), "c": (ex1, ey1, EAVE), "d": (ex0, ey1, EAVE),
                                     "r0": (ex0 + hw, (ey0 + ey1) / 2, RIDGE), "r1": (ex1 - hw, (ey0 + ey1) / 2, RIDGE)}.items()}
for fc in (("a", "b", "r1", "r0"), ("b", "c", "r1"), ("c", "d", "r0", "r1"), ("d", "a", "r0"), ("a", "d", "c", "b")):
    bm.faces.new([v[k] for k in fc])

arcade_face(SOUTH, K["arch_bays_south"], ext0=BD["depth"])
arcade_face(WEST, K["arch_bays_west"])
plain_face(NORTH, 8)
plain_face(EAST, 4)

# ================================================================== store with green roller shutters (east end)
B.wbox("annex", AX0, AX1, AY0, AY1, 0, AH)
B.wbox("slab", AX0, AX1 + 0.2, AY0 - 0.2, AY1 + 0.2, AH, AH + 0.25)
AS = Face(B, (AX0, AY0, 0), (1, 0, 0), (0, -1, 0), AX1 - AX0)
n = K["annex"]["shutters"]
w = AS.W / n
for i in range(n):
    a, b = i * w + 0.25, (i + 1) * w - 0.25
    AS.box("shutter", a, b, 0, 0.06, 0, AH - 0.5)
    AS.box("slab", a - 0.1, b + 0.1, 0, 0.3, AH - 0.5, AH - 0.2)

COLLIDERS = [(X0, X1, Y0, Y1, RIDGE), (AX0, AX1, AY0, AY1, AH)]
B.finish((X0, Y0, AX1, Y1), RIDGE, "CANTEEN", COLLIDERS)
