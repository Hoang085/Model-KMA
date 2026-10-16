"""B4 – build Nhà ăn hệ quân (TB3) from layout/buildings/nha_an.json.
Usage: blender -b --factory-startup --python scripts/build_nha_an.py
Outputs: blender/nha_an.blend, export/NHA_AN.fbx, export/NHA_AN.glb
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lib import Builder, Face, ROOT, TILE
from mathutils import Vector

SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "nha_an.json"), encoding="utf-8"))
C, BL, LV = SPEC["colors"], SPEC["blocks"], SPEC["levels"]
FS, FW = SPEC["faces"]["south"], SPEC["faces"]["west"]
X0, Y0, X1, Y1 = SPEC["footprint_rect"]
F1, F2, PAR = LV["floor1"], LV["floor2"], LV["parapet"]
FR, HALL, WING, ROT = BL["front"]["rect"], BL["hall"], BL["low_wing"], BL["rotunda"]
HX0, HY0, HX1, HY1 = HALL["rect"]
WX0, WY0, WX1, WY1 = WING["rect"]
EAVE, RIDGE = HALL["eave"], HALL["ridge"]

B = Builder("NHA_AN")
paint = TILE.get("paint", 4)
B.material("cream", C["cream"], 0.9, 0, "paint_hd_cream_albedo", "paint_normal", tile=paint)
B.material("cream_dark", C["cream_dark"], 0.9, 0, "paint_hd_cream_dark_albedo", "paint_normal", tile=paint)
B.material("grey", C["grey_panel"], 0.7, 0, "paint_hd_frame_albedo", "paint_normal", tile=paint)
B.material("recess", C["recess"], 0.8)
B.material("glass", C["glass"], 0.04, 0.15)
B.material("glass_rot", C["glass_rot"], 0.03, 0.2)
B.material("mullion", C["mullion"], 0.4, 0.6)
B.material("frame", C["frame"], 0.45, 0.5)
B.material("marble", C["marble"], 0.25)
B.material("vein", C["marble_vein"], 0.3)
B.material("step", C["step"], 0.6)
B.material("plinth", C["plinth"], 0.6, 0, "podium_tile_albedo", "podium_tile_normal", 0.5, tile=TILE.get("podium", 1.2))
B.material("roof_red", C["roof"], 0.55, 0.35)
B.material("roof_flat", "#b4b6b4", 0.95, 0, "roof_albedo", "paint_normal", tile=TILE.get("roof", 6))
B.material("duct", C["duct"], 0.3, 0.9)
B.material("ac", C["ac"], 0.6)
B.material("door_dark", C["door_dark"], 0.6)
B.material("grille", "#555a5e", 0.45, 0.6)
B.material("white", "#f4f4f2", 0.5)
B.material("sign_blue", C["sign_blue"], 0.4)
B.material("granite", "#8b8f92", 0.75, 0, "granite_albedo", "granite_normal", 0.4, tile=TILE.get("granite", 1.5))

SOUTH = Face(B, (X0, Y0, 0), (1, 0, 0), (0, -1, 0), FS["width"])            # u = x − 40.9
WEST = Face(B, (FR[0], HY1, 0), (0, -1, 0), (-1, 0, 0), FW["width"])        # u = 77.1 − y
NORTH = Face(B, (HX1, HY1, 0), (-1, 0, 0), (0, 1, 0), HX1 - HX0)             # u = 64.4 − x
E_WING = Face(B, (WX1, Y0, 0), (0, 1, 0), (1, 0, 0), WY1 - WY0)              # u = y − 38.6
E_FRONT = Face(B, (FR[2], Y0, 0), (0, 1, 0), (1, 0, 0), FR[3] - FR[1])
E_HALL = Face(B, (HX1, Y0, 0), (0, 1, 0), (1, 0, 0), HY1 - Y0)


def window(f, u0, u1, z0, z1, panes=2, proud=0.0, sill=True):
    t = 0.07
    f.box("glass", u0, u1, proud - 0.02, proud + 0.02, z0, z1)
    for a, b, c, d in ((u0 - t, u1 + t, z0 - t, z0), (u0 - t, u1 + t, z1, z1 + t), (u0 - t, u0, z0, z1), (u1, u1 + t, z0, z1)):
        f.box("frame", a, b, proud, proud + 0.08, c, d)
    for i in range(1, panes):
        uu = u0 + (u1 - u0) * i / panes
        f.box("frame", uu - 0.025, uu + 0.025, proud, proud + 0.06, z0, z1)
    if sill:
        f.box("cream_dark", u0 - 0.1, u1 + 0.1, proud, proud + 0.12, z0 - 0.14, z0 - t)


def glazed_wall(f, u0, u1, z0, z1, panes, w=0.02):
    f.box("glass", u0, u1, w - 0.02, w + 0.02, z0, z1)
    for i in range(panes + 1):
        uu = u0 + (u1 - u0) * i / panes
        f.box("frame", uu - 0.04, uu + 0.04, w, w + 0.08, z0, z1)
    for zz in (z0, z1 - 0.06, z0 + 2.4 if z1 - z0 > 3 else None):
        if zz is not None:
            f.box("frame", u0, u1, w, w + 0.08, zz, zz + 0.06)


def prism(key, pts):
    """Closed solid from a list of bottom/top vertex rings given as [(x, y, z), ...] faces."""
    bm = B.bm[key]
    v = {k: bm.verts.new(p) for k, p in pts["verts"].items()}
    for fc in pts["faces"]:
        bm.faces.new([v[k] for k in fc])


def gable(f, u0, u1, w0, w1, ze, za):
    """Triangular pediment block on face f: base u0..u1 at height ze, apex za, from w0 to w1."""
    um = (u0 + u1) / 2
    P = lambda u, w, z: tuple(f.P(u, w, z))
    prism("cream", {"verts": {"a0": P(u0, w0, ze), "b0": P(u1, w0, ze), "c0": P(um, w0, za),
                              "a1": P(u0, w1, ze), "b1": P(u1, w1, ze), "c1": P(um, w1, za)},
                    "faces": [("a0", "b0", "c0"), ("a1", "c1", "b1"), ("a0", "a1", "b1", "b0"),
                              ("b0", "b1", "c1", "c0"), ("c0", "c1", "a1", "a0")]})


def sector(key, cx, cy, a0, a1, r0, r1, z0, z1):
    pts = [Vector((cx + r * math.cos(a), cy + r * math.sin(a), z)) for a in (a0, a1) for r in (r0, r1) for z in (z0, z1)]
    B.hexa(key, pts)


def parapet_ring(x0, x1, y0, y1, z0, z1, t=0.25, key="cream"):
    for xa, xb, ya, yb in ((x0, x1, y0, y0 + t), (x0, x1, y1 - t, y1), (x0, x0 + t, y0, y1), (x1 - t, x1, y0, y1)):
        B.wbox(key, xa, xb, ya, yb, z0, z1)
    for xa, xb, ya, yb in ((x0 - 0.05, x1 + 0.05, y0 - 0.05, y0 + t), (x0 - 0.05, x1 + 0.05, y1 - t, y1 + 0.05),
                           (x0 - 0.05, x0 + t, y0, y1), (x1 - t, x1 + 0.05, y0, y1)):
        B.wbox("cream_dark", xa, xb, ya, yb, z1, z1 + 0.08)


# ================================================================== masses
# front block is L-shaped: full depth east of the dark joint strip, set back behind the drum to the west
RC = BL["rotunda"]["center"]
XJ0, XJ1 = X0 + FS["recess"][0], X0 + FS["recess"][1]                           # joint strip x 48.9..49.9
for bx0, bx1, by0 in ((XJ1, FR[2], FR[1]), (FR[0], XJ0, RC[1])):
    B.wbox("cream", bx0, bx1, by0, FR[3], 0, PAR - 0.9)
    parapet_ring(bx0, bx1, by0, FR[3], PAR - 0.9, PAR)
    B.wbox("roof_flat", bx0 + 0.25, bx1 - 0.25, by0 + 0.25, FR[3] - 0.25, PAR - 0.9, PAR - 0.85)
B.wbox("recess", XJ0, XJ1, FR[1] + 0.6, FR[3], 0, FS["recess"][2])
B.wbox("roof_flat", XJ0, XJ1, FR[1] + 0.6, FR[3], FS["recess"][2], FS["recess"][2] + 0.05)
for i in range(4):                                                             # rooftop AC condensers
    B.wbox("ac", FR[0] + 9 + i * 1.6, FR[0] + 10.1 + i * 1.6, FR[3] - 3.0, FR[3] - 2.2, PAR - 0.85, PAR - 0.05)

B.wbox("cream", HX0, HX1, HY0, HY1, 0, EAVE)                                   # dining hall, gable roof N–S
OVH = HALL["overhang"]
XM = (HX0 + HX1) / 2
for yy, dy in ((HY1, -0.25), (HY0, 0.25)):                                         # gable walls (north end + south above the front block)
    prism("cream", {"verts": {"a": (HX0, yy, EAVE), "b": (HX1, yy, EAVE), "c": (XM, yy, RIDGE - 0.15),
                              "a1": (HX0, yy + dy, EAVE), "b1": (HX1, yy + dy, EAVE), "c1": (XM, yy + dy, RIDGE - 0.15)},
                    "faces": [("a", "b", "c"), ("a1", "c1", "b1"), ("a", "a1", "b1", "b"), ("b", "b1", "c1", "c"), ("c", "c1", "a1", "a")]})
for xe in (HX0 - OVH, HX1 + OVH):                                                  # two roof slopes, 0.12 thick, overhanging
    pts = []
    for (x, z) in ((xe, EAVE - 0.2), (XM, RIDGE)):
        for y in (HY0, HY1 + OVH):
            for t in (-0.12, 0.0):
                pts.append(Vector((x, y, z + t)))
    B.hexa("roof_red", pts)
for yy in (HY1 + OVH,):                                                            # red-brown verge trim on the north gable
    for xe in (HX0 - OVH, HX1 + OVH):
        B.tube("step", (xe, yy, EAVE - 0.2), (XM, yy, RIDGE + 0.02), 0.09, 6)

B.wbox("cream", WX0, WX1, WY0, WY1, 0, WING["parapet"] - 0.6)                  # low wing
parapet_ring(WX0, WX1, WY0, WY1, WING["parapet"] - 0.6, WING["parapet"])
B.wbox("roof_flat", WX0 + 0.25, WX1 - 0.25, WY0 + 0.25, WY1 - 0.25, WING["parapet"] - 0.6, WING["parapet"] - 0.55)

# ================================================================== rotunda (curved glass drum)
cx, cy = ROT["center"]; r = ROT["radius"]; c0, c1 = ROT["cornice"]
B.cylinder("cream", cx, cy, 0, 0.3, r + 0.05, 48)
B.cylinder("glass_rot", cx, cy, 0.3, c0, r, 48)
for k in range(36):
    a = 2 * math.pi * k / 36
    p = (cx + (r + 0.04) * math.cos(a), cy + (r + 0.04) * math.sin(a))
    B.tube("mullion", (p[0], p[1], 0.3), (p[0], p[1], c0), 0.045, 6)
zz = 1.55
while zz < c0 - 0.3:
    B.cylinder("mullion", cx, cy, zz - 0.03, zz + 0.03, r + 0.05, 48); zz += 1.25
B.cylinder("cream_dark", cx, cy, F2 - 0.15, F2 + 0.15, r + 0.08, 48)           # floor band
B.cylinder("cream", cx, cy, c0, c1, r + 0.3, 48)                               # cornice cap
B.cylinder("roof_flat", cx, cy, c1, c1 + 0.04, r + 0.1, 48)

# outside stair wrapping the drum: rises from the south-east (z 0) round the west to F2 at the west wall
SW = FS["stair_wall"]
a_lo, a_hi = math.radians(297), math.radians(125)
N = 28
for i in range(N):
    t0, t1 = i / N, (i + 1) / N
    aa, ab = a_lo + (a_hi - a_lo) * t0, a_lo + (a_hi - a_lo) * t1
    zt = F2 * t1
    sector("granite", cx, cy, aa, ab, r + 0.1, r + 1.45, 0, max(zt, 0.15))
    sector("cream", cx, cy, aa, ab, r + 1.45, r + 1.7, 0, zt + 1.0)
B.wbox("granite", FR[0] - 1.6, FR[0], 45.2, 48.2, 0, F2)                       # top landing at the west wall
B.wbox("cream", FR[0] - 1.85, FR[0] - 1.6, 45.2, 48.2, 0, F2 + 1.0)
WEST.box("door_dark", 29.2, 30.6, 0, 0.06, F2, F2 + 2.3)                       # upper door off the landing

# ================================================================== south face (main entrance)
f = SOUTH
GL = FS["grey_left"]
f.box("grey", GL["u0"], GL["u1"], 0, 0.1, GL["z0"], GL["z1"])
zg = GL["z0"] + 1.2
while zg < GL["z1"]:
    f.box("recess", GL["u0"], GL["u1"], 0.1, 0.11, zg, zg + 0.02); zg += 1.2
window(f, GL["window"][0], GL["window"][1], GL["window"][2], GL["window"][3], 3, proud=0.1, sill=False)
f.box("door_dark", GL["board"][0], GL["board"][1], 0.1, 0.16, GL["board"][2], GL["board"][3])
GR = FS["grey_right"]
f.box("grey", GR["u0"], GR["u1"], 0, 0.1, GR["z0"], GR["z1"])
for u0, u1, z0, z1 in GR["windows"]:
    window(f, u0, u1, z0, z1, 2, proud=0.1, sill=False)
G, LG, P = FS["gable"], FS["loggia"], FS["portico"]
glazed_wall(f, LG["u0"], LG["u1"], LG["z0"], LG["z1"], LG["panes"], w=0.02)     # loggia glass, set back under the gable
f.box("cream", G["u0"] - 0.3, G["u0"], 0, 1.2, F2, G["eave"])                  # side cheeks of the loggia
f.box("cream", G["u1"], G["u1"] + 0.3, 0, 1.2, F2, G["eave"])
f.box("cream", G["u0"], G["u1"], 0, 1.2, G["eave"] - 0.3, G["eave"])           # lintel
f.box("cream", G["u0"] - 0.3, G["u1"] + 0.3, 1.2, 1.25, F2, LG["z0"])          # parapet under the glass
f.box("white", G["u0"] - 0.6, G["u1"] + 0.6, -0.1, 1.5, G["eave"], G["eave"] + 0.25)
gable(f, G["u0"] - 0.6, G["u1"] + 0.6, -0.1, 1.5, G["eave"] + 0.25, G["apex"])
# portico: glazed doors, 4 marble columns, marble beam, AC units on top
glazed_wall(f, P["u0"] + 0.2, P["u1"] - 0.2, F1, P["z0"], 6, w=0.02)
f.box("granite", P["u0"], P["u1"] + 0.4, 0, P["depth"], 0, F1)                 # entrance floor
for cu in P["columns"]:
    hw_ = P["col_w"] / 2
    f.box("marble", cu - hw_, cu + hw_, P["depth"] - 0.55, P["depth"] - 0.05, F1, P["z0"])
    f.box("vein", cu - 0.04, cu + 0.04, P["depth"] - 0.06, P["depth"] - 0.04, F1 + 0.6, P["z0"] - 0.8)
f.box("marble", P["u0"], P["u1"], 0, P["depth"], P["z0"], P["z1"])
for k in range(5):
    u = P["u0"] + 0.7 + k * 1.3
    f.box("vein", u, u + 0.6, P["depth"], P["depth"] + 0.01, P["z0"] + 0.15, P["z0"] + 0.2)
for cu in FS["ac_units"]:
    f.box("ac", cu - 0.4, cu + 0.4, 0.1, 0.7, P["z1"], P["z1"] + 0.55)
St = FS["steps"]
n = St["risers"]; tread = St["depth"] / n
for k in range(n):
    f.box("step", St["u0"] - 0.2, St["u1"], P["depth"], P["depth"] + St["depth"] - k * tread, k * F1 / n, (k + 1) * F1 / n)
for uu in (St["u0"] - 0.7, St["u1"] + 0.1):                                    # red cheek walls / planters
    f.box("step", uu, uu + 0.5, 0, P["depth"] + St["depth"], 0, F1 + 0.35)
# low wing south
LW = FS["low_wing"]
f.box("plinth", LW["u0"], LW["u1"], 0, 0.05, 0, 0.8)
window(f, LW["window"][0], LW["window"][1], LW["window"][2], LW["window"][3], 3, proud=0.0)
for u0, u1, kind in LW["doors"]:
    f.box("door_dark" if kind == "dark" else "grille", u0, u1, 0, 0.08, 0.3, 2.3)
    if kind == "grille":
        k = u0 + 0.08
        while k < u1:
            f.box("grille", k - 0.015, k + 0.015, 0.08, 0.12, 0.3, 2.3); k += 0.15
    f.box("granite", u0 - 0.2, u1 + 0.2, 0, 0.9, 0, 0.3)
d0, d1, dz0, dz1 = LW["duct"]
dc = (d0 + d1) / 2
B.tube("duct", tuple(f.P(dc, 0.5, dz0)), tuple(f.P(dc, 0.5, dz1)), (d1 - d0) / 2, 12)
B.tube("duct", tuple(f.P(dc, 0.5, dz1 - 0.2)), tuple(f.P(dc, -1.5, dz1 - 0.2)), (d1 - d0) / 2, 12)

# ================================================================== west face (TB3)
f = WEST
f.box("plinth", 0, FW["hall"][1], 0, 0.05, 0, 0.5)
hu0, hu1 = 0.8, FW["hall_recess"][0] - 0.5
for i in range(4):
    cu = hu0 + (hu1 - hu0) * (i + 0.5) / 4
    window(f, cu - 0.7, cu + 0.7, 2.6, 5.4, 2)
a, b = FW["hall_recess"]
f.box("recess", a, b, 0, 0.02, 0, EAVE)
E = FW["entrance"]
glazed_wall(f, E["u0"] + 0.3, E["u1"] - 0.3, F1, E["canopy_z"], 7, w=0.02)
window(f, E["u0"] + 1.0, E["u1"] - 1.0, 5.0, 6.3, 5, proud=0.0)
f.box("granite", E["u0"], E["u1"], 0, 3.0, 0, F1)
for cu in E["columns"]:
    p = f.P(cu, 2.6, 0)
    B.cylinder("white", p.x, p.y, F1, E["canopy_z"], E["col_d"] / 2, 16)
f.box("white", E["u0"], E["u1"], 0, 3.2, E["canopy_z"], E["canopy_z"] + E["canopy_t"])
s0, s1, ns = E["steps"]
for k in range(ns):
    f.box("granite", s0, s1, 3.0, 3.0 + 1.2 - k * 0.3, k * F1 / ns, (k + 1) * F1 / ns)
r0, r1 = FW["recess"]
f.box("recess", r0, r1, 0, 0.02, 0, PAR - 0.6)
T = FW["tb3_sign"]
f.box("sign_blue", T["u"], T["u"] + T["w"], 0, 0.05, T["z"], T["z"] + T["h"])
B.text(T["text"], f, T["u"] + T["w"] / 2, 0.05, T["z"] + T["h"] / 2, T["h"] * 0.6, "white", serif=False, extrude=0.01)

# ================================================================== north face (gable end, photo from the tennis court)
f = NORTH
FN = SPEC["faces"]["north"]
f.box("plinth", 0, f.W, 0, 0.05, 0, 0.5)
wz0, wz1 = FN["window_z"]
for u0, u1 in FN["windows"]:
    window(f, u0, u1, wz0, wz1, 2)
SN = FN["stair"]
sw = SN["w"]


def flight(ua, za, ub, zb, w0, w1):
    pts = []
    for uu, zz in ((ua, za), (ub, zb)):
        for ww in (w0, w1):
            for t in (-0.25, 0.0):
                pts.append(f.P(uu, ww, max(zz + t, 0.0)))
    B.hexa("cream", pts)
    pts = []
    for uu, zz in ((ua, za), (ub, zb)):
        for ww in (w1 - 0.1, w1):
            for t in (0.0, 0.95):
                pts.append(f.P(uu, ww, zz + t))
    B.hexa("cream_dark", pts)


flight(SN["u_lo"], 0.0, SN["u_mid"], SN["z_mid"], sw + 0.1, 2 * sw + 0.1)          # lower flight, outer
f.box("cream", SN["u_mid"] - 1.2, SN["u_mid"], 0, 2 * sw + 0.1, SN["z_mid"] - 0.25, SN["z_mid"])
f.box("cream", SN["u_mid"] - 1.2, SN["u_mid"] - 1.1, 0, 2 * sw + 0.1, 0, SN["z_mid"] - 0.25)   # landing support
flight(SN["u_mid"], SN["z_mid"], SN["u_lo"], SN["z_top"], 0.0, sw)                 # upper flight, against the wall
f.box("cream", SN["u_lo"], f.W, 0, sw + 0.2, SN["z_top"] - 0.25, SN["z_top"])     # top landing
f.box("cream_dark", SN["u_lo"], f.W, sw + 0.1, sw + 0.2, SN["z_top"], SN["z_top"] + 0.95)
d0, d1 = FN["upper_door"]
f.box("door_dark", d0, d1, 0, 0.06, SN["z_top"], SN["z_top"] + 2.2)

# ================================================================== east faces (assumed)
f = E_HALL
f.box("plinth", 14.0, f.W, 0, 0.05, 0, 0.5)
for i in range(8):
    cu = 14.5 + (f.W - 15.0) * (i + 0.5) / 8
    window(f, cu - 0.7, cu + 0.7, 2.6, 5.4, 2)
f = E_FRONT
for u0 in (8.0, 10.6):
    window(f, u0, u0 + 1.4, F2 + 1.2, F2 + 2.8, 2)
    window(f, u0, u0 + 1.4, 1.4, 3.0, 2)
f = E_WING
f.box("plinth", 0, f.W, 0, 0.05, 0, 0.8)
window(f, 2.0, 3.4, 1.0, 2.4, 2)
window(f, 4.6, 6.0, 1.0, 2.4, 2)

COLLIDERS = [
    (XJ0, FR[2], FR[1], FR[3], PAR),
    (FR[0], XJ0, RC[1], FR[3], PAR),
    (HX0, HX1, HY0, HY1, RIDGE),
    (WX0, WX1, WY0, WY1, WING["parapet"]),
    (cx - r, cx + r, cy - r, cy + r, ROT["top"]),
    (X0 + P["u0"], X0 + St["u1"] + 0.6, Y0 - P["depth"], Y0, F1),               # portico floor (walk-up)
]
B.finish((X0, Y0, X1, Y1), ROT["top"], "NHA_AN", COLLIDERS)
