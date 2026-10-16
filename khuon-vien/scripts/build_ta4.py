"""B4 – build TA4 (sign TB5) from layout/buildings/ta4.json.
Usage: blender -b --factory-startup --python scripts/build_ta4.py
Outputs: blender/ta4.blend, export/TA4.fbx, export/TA4.glb
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lib import Builder, Face, ROOT, TILE
from mathutils import Vector

SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "ta4.json"), encoding="utf-8"))
C, G, LV = SPEC["colors"], SPEC["gallery"], SPEC["levels"]
X0, Y0, X1, Y1 = SPEC["rect"]
ST, GC, CB, RF = SPEC["stair_tower"], SPEC["glass_core"], SPEC["curved_bay"], SPEC["roof"]
NF = SPEC["floors"]


def lv(n):
    return 0.0 if n == 1 else LV["ground_h"] + (n - 2) * LV["typical_h"]


ROOF = lv(NF + 1)
TOP = ROOF + SPEC["parapet"]
YB = Y0 + G["depth"]                                                      # back wall of the open galleries

B = Builder("TA4")
paint = TILE.get("paint", 4)
B.material("concrete", C["concrete"], 0.9, 0, None, "paint_normal", tile=paint)
B.material("concrete_dark", C["concrete_dark"], 0.9)
B.material("louver", C["louver"], 0.7, 0.1)
B.material("pier", C["pier"], 0.8)
B.material("glass_green", C["glass_green"], 0.05, 0.3)
B.material("glass", C["glass"], 0.05, 0.2)
B.material("steel", C["steel"], 0.45, 0.8)
B.material("rust", C["rust"], 0.7, 0.4)
B.material("steel_dark", "#6f7275", 0.6, 0.5)
B.material("door", C["door"], 0.6)
B.material("roof", C["roof"], 0.5, 0.4)
B.material("roof_flat", C["roof_flat"], 0.95, 0, "roof_albedo", "paint_normal", tile=TILE.get("roof", 6))
B.material("rail", C["rail"], 0.4, 0.7)
B.material("sign_blue", C["sign_blue"], 0.4)
B.material("sign_white", "#ffffff", 0.5)

SOUTH = Face(B, (X0, Y0, 0), (1, 0, 0), (0, -1, 0), X1 - X0)            # u = x − 41.4
NORTH = Face(B, (X1, Y1, 0), (-1, 0, 0), (0, 1, 0), X1 - X0)
WEST = Face(B, (X0, Y1, 0), (0, -1, 0), (-1, 0, 0), Y1 - Y0)
EAST = Face(B, (X1, Y0, 0), (0, 1, 0), (1, 0, 0), Y1 - Y0)


def sector(key, cx, cy, a0, a1, r0, r1, z0, z1):
    B.hexa(key, [Vector((cx + r * math.cos(a), cy + r * math.sin(a), z)) for a in (a0, a1) for r in (r0, r1) for z in (z0, z1)])


def half_disc(key, cx, cy, r0, r1, z0, z1, seg=16):
    for i in range(seg):
        sector(key, cx, cy, math.pi + math.pi * i / seg, math.pi + math.pi * (i + 1) / seg, r0, r1, z0, z1)


def parapet_ring(x0, x1, y0, y1, z0, z1, t=0.25):
    for xa, xb, ya, yb in ((x0, x1, y0, y0 + t), (x0, x1, y1 - t, y1), (x0, x0 + t, y0, y1), (x1 - t, x1, y0, y1)):
        B.wbox("concrete", xa, xb, ya, yb, z0, z1)


# ================================================================== main mass + flat roofs + gable roof
B.wbox("concrete", X0, X1, YB, Y1, 0, ROOF)
parapet_ring(X0, X1, Y0, Y1, ROOF, TOP)
B.wbox("roof_flat", X0, X1, Y0, Y1, ROOF - 0.05, ROOF)
rx0, rx1 = RF["x"]; ry0, o = RF["y0"], RF["overhang"]
xm = (rx0 + rx1) / 2
for xe in (rx0 - o, rx1 + o):
    pts = []
    for x, z in ((xe, ROOF + 0.3), (xm, RF["ridge"])):
        for y in (ry0 - o, Y1 + o):
            for t in (-0.12, 0.0):
                pts.append(Vector((x, y, z + t)))
    B.hexa("roof", pts)
for yy, key, dy in ((ry0, "glass_green", 0.1), (Y1, "concrete", -0.2)):        # glazed south gable, solid north gable
    bm = B.bm[key]
    v = [bm.verts.new(p) for p in ((rx0, yy, ROOF), (rx1, yy, ROOF), (xm, yy, RF["ridge"] - 0.1),
                                    (rx0, yy + dy, ROOF), (rx1, yy + dy, ROOF), (xm, yy + dy, RF["ridge"] - 0.1))]
    for fc in ((0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)):
        bm.faces.new([v[i] for i in fc])
for k in range(1, 8):                                                      # mullions on the glazed gable
    xx = rx0 + (rx1 - rx0) * k / 8
    zt = ROOF + (RF["ridge"] - ROOF) * (1 - abs(xx - xm) / (xm - rx0))
    B.wbox("steel", xx - 0.04, xx + 0.04, ry0 - 0.05, ry0, ROOF, zt - 0.1)


# ================================================================== south: open galleries with louvers
def gallery(u0, u1):
    f = SOUTH
    d = G["depth"]
    for i in range(int((u1 - u0) / 3.0)):                                  # ground-floor doors on the back wall
        f.box("door", u0 + 1.0 + i * 3.0, u0 + 2.0 + i * 3.0, -d, -d + 0.06, 0.1, 2.4)
    for n in range(2, NF + 1):
        z0 = lv(n)
        f.box("concrete_dark", u0, u1, 0, d, z0 - 0.4, z0)                 # corridor slab
        f.box("concrete", u0, u1, 0, 0.15, z0, z0 + G["spandrel_h"])       # solid parapet
        f.box("rail", u0, u1, 0.05, 0.1, z0 + G["spandrel_h"] + 0.85, z0 + G["spandrel_h"] + 0.9)
        for i in range(int((u1 - u0) / 3.0)):                              # classroom doors / windows on the back wall
            f.box("glass", u0 + 1.0 + i * 3.0, u0 + 2.2 + i * 3.0, -d, -d + 0.05, z0 + 0.1, z0 + 2.3)
        hb = LV["typical_h"] - G["louver_from"]
        for k in range(G["slats"]):
            zz = z0 + G["louver_from"] + k * hb / G["slats"]
            f.box("louver", u0, u1, 0.05, G["louver_proud"], zz, zz + hb / G["slats"] * 0.8)
    f.box("concrete_dark", u0, u1, 0, d, ROOF - 0.4, ROOF)
    u = u0
    while u <= u1 + 1e-6:
        f.box("pier", max(u - 0.2, u0), min(u + 0.2, u1), 0.0, 0.4, 0, ROOF); u += G["pier_step"]


g0, g1 = GC["x"][0] - X0, GC["x"][1] - X0
cx, cy = CB["center"]; r = CB["radius"]
c0, c1 = cx - r - X0, cx + r - X0
gallery(0.0, g0)
gallery(c1, X1 - X0)
SOUTH.box("glass_green", g0, g1, 0, G["depth"], 0, TOP)                     # glass stair core
for n in range(2, NF + 2):
    SOUTH.box("steel", g0, g1, -0.01, 0.03, lv(n) - 0.1, lv(n) + 0.1)
# curved louvered bay
B.wbox("louver", cx - r, cx + r, Y0, YB, lv(2) - 0.4, ROOF)
half_disc("concrete_dark", cx, cy, 0, r - 0.3, lv(2) - 0.4, ROOF)
z = lv(2)
while z < ROOF:
    half_disc("louver", cx, cy, r - 0.3, r, z, z + 0.16); z += 0.35
for a in range(0, 9):                                                      # vertical fins holding the slats
    ang = math.pi + math.pi * a / 8
    sector("pier", cx, cy, ang - 0.02, ang + 0.02, r - 0.35, r + 0.02, lv(2) - 0.4, ROOF)
half_disc("concrete", cx, cy, 0, r + 0.3, ROOF, ROOF + 0.6)
half_disc("concrete", cx, cy, 0, CB["canopy_r"], CB["canopy_z"] - 0.35, CB["canopy_z"])   # porch canopy
for a in (0.25, 0.5, 0.75):
    ang = math.pi + math.pi * a
    px, py = cx + (CB["canopy_r"] - 0.6) * math.cos(ang), cy + (CB["canopy_r"] - 0.6) * math.sin(ang)
    B.cylinder("pier", px, py, 0, CB["canopy_z"] - 0.35, 0.25, 12)
B.wbox("glass", cx - r, cx + r, YB - 0.05, YB, 0, lv(2) - 0.4)              # glazed lobby under the bay
SG = SPEC["sign"]
su, sz = SG["x"] - X0, lv(SG["floor"]) + 0.2
SOUTH.box("sign_blue", su, su + SG["w"], 0.15, 0.2, sz, sz + SG["h"])
B.text(SG["text"], SOUTH, su + SG["w"] / 2, 0.2, sz + SG["h"] / 2, SG["h"] * 0.6, "sign_white", serif=False, extrude=0.01)

# ================================================================== other faces
for n in range(1, NF + 1):
    u = 1.5
    while u + 1.8 < NORTH.W - 1.0:
        NORTH.box("glass", u, u + 1.8, 0, 0.05, lv(n) + 1.0, lv(n) + 2.6); u += 3.8
for n in range(2, NF + 1):
    for cu in (3.0, 6.0):
        WEST.box("glass", cu - 0.6, cu + 0.6, 0, 0.05, lv(n) + 1.0, lv(n) + 2.4)
    EAST.box("glass", 8.0, 9.2, 0, 0.05, lv(n) + 1.0, lv(n) + 2.4)
B.wbox("concrete", X0, X0 + 0.25, Y0, YB, 0, ROOF)                         # gallery ends closed by side walls
B.wbox("concrete", X1 - 0.25, X1, Y0, YB, 0, ROOF)

# ================================================================== steel stair tower (west end)
tx0, ty0, tx1, ty1 = ST["rect"]
tm = (ty0 + ty1) / 2
for px in (tx0 + 0.1, tx1 - 0.1):
    for py in (ty0 + 0.1, ty1 - 0.1):
        top = ST["pylon_top"] if (px > tx0 + 1 and py < tm) else ROOF + 1.2
        B.tube("steel", (px, py, 0), (px, py, top), 0.09, 8)
levels = [lv(n) for n in range(2, NF + 1)] + [ROOF]
prev = 0.0
for zl in levels:
    zm = (prev + zl) / 2
    B.wbox("steel_dark", tx0, tx1, tm, ty1, zl - 0.2, zl)                   # floor landing (next to the door)
    B.wbox("rust", tx0, tx1, tm, ty1, zl - 0.26, zl - 0.2)                  # rusty underside, as in the photo
    B.wbox("steel_dark", tx0, tx1, ty0, ty0 + 0.9, zm - 0.2, zm)            # half landing
    for xa, xb, za, zb, ya, yb in ((tx0, (tx0 + tx1) / 2, prev, zm, tm, ty0 + 0.9), ((tx0 + tx1) / 2, tx1, zm, zl, ty0 + 0.9, tm)):
        pts = []
        for y, zz in ((ya, za), (yb, zb)):
            for x in (xa + 0.05, xb - 0.05):
                for t in (-0.18, 0.0):
                    pts.append(Vector((x, y, max(zz + t, 0.0))))
        B.hexa("steel_dark", pts)
        for x in (xa + 0.05, xb - 0.08):                                    # flight hand-rails
            B.tube("rail", (x, ya, za + 0.95), (x, yb, zb + 0.95), 0.025, 6)
    for xa, xb, ya, yb in ((tx0, tx1, ty1 - 0.05, ty1), (tx0, tx0 + 0.05, tm, ty1), (tx0, tx1, ty0, ty0 + 0.05), (tx0, tx0 + 0.05, ty0, ty0 + 0.9)):
        B.wbox("rail", xa, xb, ya, yb, zl + 0.95, zl + 1.0)
    B.wbox("door", X0 - 0.06, X0, tm + 0.6, tm + 1.6, zl, zl + 2.1)
    prev = zl
px, py = tx1 - 0.1, ty0 + 0.1                                               # lattice pylon on the top
for k in range(4):
    z0 = ROOF + 1.2 + k * (ST["pylon_top"] - ROOF - 1.2) / 4
    z1 = z0 + (ST["pylon_top"] - ROOF - 1.2) / 4
    B.tube("steel", (px - 2.5, py, z0), (px, py, z1), 0.05, 6)
    B.tube("steel", (px, py, z0), (px - 2.5, py, z1), 0.05, 6)
B.tube("steel", (px - 2.5, py, ROOF + 1.2), (px - 2.5, py, ST["pylon_top"]), 0.07, 6)

COLLIDERS = [(X0, X1, Y0, Y1, TOP), (cx - r, cx + r, cy - r, Y0, ROOF), (tx0, tx1, ty0, ty1, ROOF + 1.2)]
B.finish((tx0, min(cy - r, ty0), X1, Y1), ST["pylon_top"], "TA4", COLLIDERS)
