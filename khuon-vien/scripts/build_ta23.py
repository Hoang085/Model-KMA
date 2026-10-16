"""B4 – build the TA2 + TA3 cluster from layout/buildings/ta23.json.
Usage: blender -b --factory-startup --python scripts/build_ta23.py
Outputs: blender/ta23.blend, export/TA23.fbx, export/TA23.glb
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lib import Builder, Face, ROOT, TILE

SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "ta23.json"), encoding="utf-8"))
C, A2, A3 = SPEC["colors"], SPEC["ta2"], SPEC["ta3"]
L2, L3, LO = A2["levels"], A3["levels"], A3["louver"]
X20, Y20, X21, Y21 = A2["rect"]
X30, Y30, X31, Y31 = A3["rect"]


def lv2(n):
    return L2["plinth"] if n == 1 else L2["plinth"] + L2["ground_h"] + (n - 2) * L2["typical_h"]


def lv3(n):
    return 0.0 if n == 1 else L3["ground_h"] + (n - 2) * L3["typical_h"]


ROOF2, ROOF3 = lv2(A2["floors"] + 1), lv3(A3["floors"] + 1)
TOP2, TOP3 = ROOF2 + A2["parapet"], ROOF3 + A3["parapet"]

B = Builder("TA23")
paint = TILE.get("paint", 4)
B.material("white", C["white"], 0.85, 0, None, "paint_normal", tile=paint)
B.material("silver", C["silver"], 0.4, 0.6, "metal_albedo", None, tile=TILE.get("metal", 2))
B.material("glass", C["glass"], 0.05, 0.3)
B.material("glass_dark", C["glass_dark"], 0.04, 0.2)
B.material("frame", C["frame"], 0.45, 0.5)
B.material("pilaster", C["pilaster"], 0.5, 0, "granite_albedo", "granite_normal", 0.4, tile=TILE.get("granite", 1.5))
B.material("gold", C["gold"], 0.3, 1.0)
B.material("louver", C["louver"], 0.6, 0.4)
B.material("louver_dark", C["louver_dark"], 0.6, 0.3)
B.material("ta3_wall", C["ta3_wall"], 0.85, 0, None, "paint_normal", tile=paint)
B.material("ta3_back", "#7d7871", 0.9)
B.material("window_dark", C["window_dark"], 0.1, 0.2)
B.material("shutter", C["shutter"], 0.5, 0.5)
B.material("roof_tile", C["roof_tile"], 0.8, 0, "podium_tile_albedo", "podium_tile_normal", 0.5, tile=TILE.get("podium", 1.2))
B.material("roof_flat", C["roof_flat"], 0.95, 0, "roof_albedo", "paint_normal", tile=TILE.get("roof", 6))
B.material("sign_blue", C["sign_blue"], 0.4)
B.material("sign_white", "#ffffff", 0.5)

# faces: u from the viewer's left, w outward
E2 = Face(B, (X21, Y20, 0), (0, 1, 0), (1, 0, 0), Y21 - Y20)          # u = y − 15.7
S2 = Face(B, (X20, Y20, 0), (1, 0, 0), (0, -1, 0), X21 - X20)
W2 = Face(B, (X20, Y21, 0), (0, -1, 0), (-1, 0, 0), Y21 - Y20)
N2 = Face(B, (X30, Y21, 0), (-1, 0, 0), (0, 1, 0), X30 - X20)         # strip of TA2 north end west of TA3
E3 = Face(B, (X31, Y30, 0), (0, 1, 0), (1, 0, 0), Y31 - Y30)
N3 = Face(B, (X31, Y31, 0), (-1, 0, 0), (0, 1, 0), X31 - X30)
S3 = Face(B, (X30, Y30, 0), (1, 0, 0), (0, -1, 0), X31 - X30)
W3 = Face(B, (X30, Y31, 0), (0, -1, 0), (-1, 0, 0), Y31 - Y30)


def parapet_ring(x0, x1, y0, y1, z0, z1, key, t=0.25):
    for xa, xb, ya, yb in ((x0, x1, y0, y0 + t), (x0, x1, y1 - t, y1), (x0, x0 + t, y0, y1), (x1 - t, x1, y0, y1)):
        B.wbox(key, xa, xb, ya, yb, z0, z1)


# ================================================================== masses + roofs
B.wbox("white", X20, X21, Y20, Y21, 0, ROOF2)
parapet_ring(X20, X21, Y20, Y21, ROOF2, TOP2, "white")
B.wbox("roof_tile", X20 + 0.25, X21 - 0.25, Y20 + 0.25, Y21 - 0.25, ROOF2, ROOF2 + 0.05)
rb = A2["roof_box"]["rect"]
B.wbox("white", rb[0], rb[2], rb[1], rb[3], ROOF2, ROOF2 + A2["roof_box"]["h"])
B.wbox("ta3_back", X30, X31, Y30, Y31, 0, ROOF3)                          # dark wall seen through the louvers
B.wbox("ta3_wall", X30 - 0.02, X31 + 0.02, Y30 - 0.02, Y31 + 0.02, 0, lv3(2))  # light ground floor
parapet_ring(X30 - 0.8, X31 + 0.8, Y30 - 0.8, Y31 + 0.8, ROOF3, TOP3, "white", t=0.9)  # cap band over the louvers
B.wbox("roof_flat", X30, X31, Y30, Y31, ROOF3, ROOF3 + 0.05)
rb = A3["roof_box"]["rect"]
B.wbox("white", rb[0], rb[2], rb[1], rb[3], ROOF3, ROOF3 + A3["roof_box"]["h"])
for i in range(3):                                                         # rooftop AC on TA3
    B.wbox("shutter", rb[0] + 0.5 + i * 2.0, rb[0] + 1.6 + i * 2.0, rb[3] + 1.5, rb[3] + 2.3, ROOF3, ROOF3 + 0.8)


# ================================================================== TA2: glass ribbons (east, south)
def ribbons(f, shopfront):
    e = A2["end_panel"]
    f.box("pilaster", 0, f.W, 0, 0.06, 0, L2["plinth"])
    if shopfront:
        z0, z1 = L2["plinth"], lv2(2) - 0.5
        f.box("glass_dark", e, f.W - e, 0, 0.04, z0, z1)
        u = e
        while u < f.W - e - 0.1:
            f.box("pilaster", u, min(u + 0.45, f.W - e), 0, 0.15, z0, z1)
            for k in (1, 2):
                uu = u + 0.45 + (A2["pier_step"] - 0.45) * k / 3
                if uu < f.W - e:
                    f.box("frame", uu - 0.03, uu + 0.03, 0.04, 0.09, z0, z1)
            f.box("frame", u, min(u + A2["pier_step"], f.W - e), 0.04, 0.09, z0 + 2.4, z0 + 2.46)
            u += A2["pier_step"]
    else:
        for u in (e + 1.0, f.W / 2 - 0.75, f.W - e - 2.5):
            f.box("glass_dark", u, u + 1.5, 0, 0.04, 1.2, 2.8)
    f.box("silver", 0, f.W, 0, 0.1, lv2(2) - 0.5, lv2(2))
    for n in range(2, A2["floors"] + 1):
        z0 = lv2(n)
        f.box("silver", 0, f.W, 0, 0.1, z0, z0 + A2["spandrel"])
        f.box("glass", e, f.W - e, 0, 0.04, z0 + A2["spandrel"], z0 + L2["typical_h"])
        u = e
        while u <= f.W - e + 1e-6:
            f.box("frame", u - 0.03, u + 0.03, 0.04, 0.1, z0 + A2["spandrel"], z0 + L2["typical_h"]); u += 1.2


def punched(f, z_levels, step, z_off=1.0):
    for zb in z_levels:
        u = 1.8
        while u + 1.5 < f.W - 0.8:
            f.box("glass_dark", u, u + 1.5, 0, 0.04, zb + z_off, zb + z_off + 1.6)
            f.box("frame", u - 0.06, u + 1.56, 0, 0.08, zb + z_off - 0.06, zb + z_off)
            u += step


ribbons(E2, True)
ribbons(S2, False)
SL = A2["slogan"]
zs = lv2(SL["floor"]) + A2["spandrel"] / 2
B.text(SL["text"], E2, SL["u_center"], 0.1, zs, SL["h"], "gold", serif=True, extrude=0.03)
punched(W2, [lv2(n) for n in range(1, A2["floors"] + 1)], A2["pier_step"])
punched(N2, [lv2(n) for n in range(2, A2["floors"] + 1)], 10.0)


# ================================================================== TA3: louvers (east, north, south)
def louvers(f, z_from, ext0=0.0, ext1=0.0, ground=True):
    st, off = LO["post_step"], LO["offset"]
    for n in range(2, A3["floors"] + 1):                                    # small windows behind the slats
        z0 = lv3(n)
        if z0 + 2.3 < z_from:
            continue
        u = 1.2
        while u + 1.4 < f.W:
            f.box("window_dark", u, u + 1.4, 0, 0.04, z0 + 1.0, z0 + 2.3); u += st
    z = max(lv3(2) - 0.2, z_from)
    while z < ROOF3:
        f.box("louver", -ext0, f.W + ext1, off - 0.15, off + 0.18, z, z + LO["slat"] + 0.04); z += LO["pitch"]
    u = 0.0
    while u <= f.W + 1e-6:
        f.box("louver_dark", max(u - 0.15, -ext0), min(u + 0.15, f.W + ext1), 0, off + 0.2, z_from if not ground else 0, ROOF3)
        u += st
    if ground:
        u, i = 0.0, 0
        while u < f.W - 0.1:
            b = min(u + st, f.W)
            f.box("shutter" if i % 3 else "window_dark", u + 0.5, b - 0.2, 0, 0.05, 0.2, 3.0)
            u, i = b, i + 1


o = LO["offset"] + 0.2
louvers(E3, 0.0, ext1=o)
louvers(N3, 0.0, ext0=0.0, ext1=o)
# south face of TA3: full height on the 4 m that stands proud of TA2, above the TA2 roof elsewhere
louvers(Face(B, (X21, Y30, 0), (1, 0, 0), (0, -1, 0), X31 - X21), 0.0, ext0=0.0, ext1=o)
louvers(Face(B, (X30, Y30, 0), (1, 0, 0), (0, -1, 0), X21 - X30), TOP2 + 0.1, ext0=o, ground=False)
W3.box("ta3_wall", 0, W3.W, 0, 0.03, 0, ROOF3)                            # west face has no louvers
punched(W3, [lv3(n) for n in range(2, A3["floors"] + 1)], LO["post_step"])
SG = A3["sign"]
su, sz = SG["u_from_south"], lv3(SG["floor"]) + 2.6
E3.box("sign_blue", su, su + SG["w"], 0, o + 0.05, sz, sz + SG["h"])
B.text(SG["text"], E3, su + SG["w"] / 2, o + 0.05, sz + SG["h"] / 2, SG["h"] * 0.6, "sign_white", serif=False, extrude=0.01)

COLLIDERS = [(X20, X21, Y20, Y21, TOP2), (X30, X31 + o, Y30, Y31 + o, TOP3)]
B.finish((X20, Y20, X31, Y31), TOP3 + A3["roof_box"]["h"], "TA23", COLLIDERS)
