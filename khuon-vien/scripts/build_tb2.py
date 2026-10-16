"""B4 – build TB2 (library + dormitory tower) from layout/buildings/tb2.json + layout/campus_layout.json.
Usage: blender -b --factory-startup --python scripts/build_tb2.py
Outputs: blender/tb2.blend, export/TB2.fbx, export/TB2.glb
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lib import Builder, Face, ROOT, TILE

SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "tb2.json"), encoding="utf-8"))
LAYOUT = json.load(open(os.path.join(ROOT, "layout", "campus_layout.json"), encoding="utf-8"))
X0, Y0, X1, Y1 = next(b["rect"] for b in LAYOUT["buildings"] if b["id"] == "tb2")
C, LV, NF = SPEC["colors"], SPEC["levels"], SPEC["floors"]


def level(n):
    if n == 1:
        return LV["plinth"]
    if n == 2:
        return LV["plinth"] + LV["ground_h"]
    return LV["plinth"] + LV["ground_h"] + LV["second_h"] + (n - 3) * LV["typical_h"]


PL = LV["plinth"]
PODIUM_TOP = level(LV["podium_floors"] + 1)
ROOF = level(NF + 1)
TOP_GREY = ROOF + SPEC["parapet"]["grey"]
TOP_CREAM = ROOF + SPEC["parapet"]["cream"]
TOWER_FLOORS = range(LV["podium_floors"] + 1, NF + 1)

B = Builder("TB2")
paint = TILE.get("paint", 4)
B.material("grey", C["grey"], 0.9, 0, "paint_grey_albedo", "paint_normal", tile=paint)
B.material("cream", C["cream"], 0.9, 0, "paint_cream_albedo", "paint_normal", tile=paint)
B.material("cream_dark", "#8f8a80", 0.9, 0, "paint_cream_dark_albedo", "paint_normal", tile=paint)
B.material("podium", C["podium"], 0.6, 0, "podium_tile_albedo", "podium_tile_normal", 0.7, tile=TILE.get("podium", 1.2))
B.material("podium_dark", "#3f3430", 0.6)
B.material("glass", "#24303a", 0.04, 0.15)
B.material("frame", C["frame"], 0.5)
B.material("frame_dark", "#3a3f45", 0.45, 0.5)
B.material("grille", C["grille"], 0.45, 0.6)
B.material("ac", C["ac"], 0.6)
B.material("gold", C["gold"], 0.3, 1.0)
B.material("banner", C["banner"], 0.8)
B.material("star", "#f4d03f", 0.6)
B.material("canopy", C["canopy"], 0.4, 0.5)
B.material("steps", C["steps"], 0.75, 0, "granite_albedo", "granite_normal", 0.4, tile=TILE.get("granite", 1.5))
B.material("door_beige", "#d9cdb4", 0.7)
B.material("door_dark", "#2e2a28", 0.6)
B.material("sign_blue", C["sign_blue"], 0.4)
B.material("white", "#f2f2f0", 0.6)
B.material("roof", "#b4b6b4", 0.95, 0, "roof_albedo", "paint_normal", tile=TILE.get("roof", 6))
B.material("sky_frame", "#cfd6de", 0.9)

NORTH = Face(B, (X1, Y1, 0), (-1, 0, 0), (0, 1, 0), X1 - X0)
SOUTH = Face(B, (X0, Y0, 0), (1, 0, 0), (0, -1, 0), X1 - X0)
WEST = Face(B, (X0, Y1, 0), (0, -1, 0), (-1, 0, 0), Y1 - Y0)    # u = 0 at the north end
EAST = Face(B, (X1, Y1, 0), (0, -1, 0), (1, 0, 0), Y1 - Y0)     # same u as the west face


def window(f, u0, u1, z0, z1, panes=4, grille=True, proud=0.0, frame="frame"):
    t = 0.07
    f.box("glass", u0, u1, proud - 0.02, proud + 0.02, z0, z1)
    for a, b_, c, d in ((u0 - t, u1 + t, z0 - t, z0), (u0 - t, u1 + t, z1, z1 + t), (u0 - t, u0, z0, z1), (u1, u1 + t, z0, z1)):
        f.box(frame, a, b_, proud, proud + 0.08, c, d)
    for i in range(1, panes):
        uu = u0 + (u1 - u0) * i / panes
        f.box(frame, uu - 0.025, uu + 0.025, proud, proud + 0.06, z0, z1)
    f.box(frame, u0, u1, proud, proud + 0.06, z0 + (z1 - z0) * 0.62 - 0.025, z0 + (z1 - z0) * 0.62 + 0.025)
    if grille:
        k = z0 + 0.2
        while k < z1 - 0.1:
            f.box("grille", u0, u1, proud + 0.1, proud + 0.13, k, k + 0.025); k += 0.22
        for uu in (u0 + 0.05, u1 - 0.05):
            f.box("grille", uu - 0.02, uu + 0.02, proud + 0.08, proud + 0.13, z0, z1)
    f.box("white", u0 - 0.12, u1 + 0.12, proud, proud + 0.15, z0 - 0.12, z0 - t)


def small_window(f, cu, z0, w, h, ac=False, proud=0.0):
    window(f, cu - w / 2, cu + w / 2, z0, z0 + h, panes=2, grille=False, proud=proud)
    if ac:
        f.box("ac", cu - 0.42, cu + 0.42, proud, proud + 0.4, z0 - 0.7, z0 - 0.15)
        f.box("grille", cu - 0.28, cu + 0.28, proud + 0.4, proud + 0.42, z0 - 0.62, z0 - 0.23)


def podium_shell(f):
    f.box("podium", 0, f.W, 0, 0.1, 0, PODIUM_TOP)
    f.box("podium_dark", -0.1, f.W + 0.1, 0, 0.3, PODIUM_TOP - 0.35, PODIUM_TOP)          # podium cornice
    f.box("steps", 0, f.W, 0, 0.14, 0, PL)


# ------------------------------------------------------------------ body + roof
B.wbox("grey", X0, X1, Y0, Y1, 0, ROOF)
t = 0.25
for xa, xb, ya, yb in ((X0, X1, Y0, Y0 + t), (X0, X1, Y1 - t, Y1), (X0, X0 + t, Y0, Y1), (X1 - t, X1, Y0, Y1)):
    B.wbox("grey", xa, xb, ya, yb, ROOF, TOP_GREY)
B.wbox("roof", X0 + t, X1 - t, Y0 + t, Y1 - t, ROOF, ROOF + 0.05)
B.wbox("grey", X0 + 20, X0 + 27, Y0 + 7, Y0 + 13, ROOF, ROOF + 3.2)                    # lift machine room
B.wbox("white", X0 + 19.8, X0 + 27.2, Y0 + 6.8, Y0 + 13.2, ROOF + 3.2, ROOF + 3.35)
for i in range(4):
    B.cylinder("white", X0 + 31 + i * 2.4, Y0 + 10, ROOF, ROOF + 2.2, 0.95)

# ------------------------------------------------------------------ long faces: tower (north + south)
F = SPEC["faces"]["north"]
g, n, ww = F["grey_ends"], F["window_columns"], F["window_col_w"]
pier = (F["width"] - 2 * g - n * ww) / (n + 1)
COLS = [g + pier + i * (ww + pier) for i in range(n)]
rnd = random.Random(3)
for f in (NORTH, SOUTH):
    d = 0.14                                                     # cream cladding stands proud of the grey body
    f.box("cream", g, g + pier, 0, d, PODIUM_TOP, TOP_CREAM)
    for c0 in COLS:
        f.box("cream", c0 + ww, c0 + ww + pier, 0, d, PODIUM_TOP, TOP_CREAM)
        f.box("cream_dark", c0, c0 + ww, 0, 0.02, PODIUM_TOP, ROOF)                          # recessed strip
        f.box("cream", c0, c0 + ww, 0, d, ROOF, TOP_CREAM)                                   # parapet over the strip
    for fl in TOWER_FLOORS:
        z0 = level(fl)
        for c0 in COLS:
            window(f, c0 + 0.12, c0 + ww - 0.12, z0 + 0.45, z0 + 3.0, panes=4, grille=True, proud=0.03, frame="frame_dark")
            f.box("cream", c0, c0 + ww, 0, d - 0.04, z0 - 0.1, z0 + 0.12)                   # floor band across the strip
        for i in range(n + 1):
            if rnd.random() < 0.45:
                pu = g + i * (ww + pier) + pier / 2
                f.box("ac", pu - 0.3, pu + 0.3, d, d + 0.06, z0 + 1.5, z0 + 2.0)
                f.box("grille", pu - 0.22, pu + 0.22, d + 0.06, d + 0.07, z0 + 1.58, z0 + 1.92)
        for e0 in (0, f.W - g):
            for cu in F["grey_window_cols"]:
                small_window(f, e0 + cu, z0 + 1.0, 1.3, 1.5, ac=True)

# ------------------------------------------------------------------ short faces: tower (west + east)
Wf = SPEC["faces"]["west"]
for f in (WEST, EAST):
    for kind, u0, u1 in Wf["zones"]:
        if kind == "cream":
            f.box("cream", u0, u1, 0, 0.14, PODIUM_TOP, TOP_CREAM)
    b0, b1 = Wf["big_window_col"]
    for fl in TOWER_FLOORS:
        z0 = level(fl)
        window(f, b0, b1, z0 + 0.6, z0 + 2.9, panes=2, grille=True)
        for u0, u1, kind in Wf["small_window_cols"]:
            small_window(f, (u0 + u1) / 2, z0 + 1.1, u1 - u0, 1.0, ac=(kind == "ac"), proud=0.14 if kind == "ac" else 0.0)
    RF = Wf["roof_frame"]                                    # open frame on the roof corner
    depth = 3.0
    f.box("grey", RF["u0"], RF["u0"] + 0.45, -depth, 0, ROOF, ROOF + RF["h"])
    f.box("grey", RF["u1"] - 0.45, RF["u1"], -depth, 0, ROOF, ROOF + RF["h"])
    f.box("grey", RF["u0"], RF["u1"], -depth, 0, ROOF + RF["h"] - 0.5, ROOF + RF["h"])
    f.box("sky_frame", RF["u0"] + 0.45, RF["u1"] - 0.45, -depth, -depth + 0.2, ROOF, ROOF + RF["h"] - 0.5)

# ------------------------------------------------------------------ podium: north (library entrance)
f = NORTH
podium_shell(f)
SF = F["shopfront"]
u = SF["u0"]
while u + SF["pier_every"] <= SF["u1"] + 1e-6:
    window(f, u + 0.4, u + SF["pier_every"] - 0.4, PL + 0.3, PL + 3.6, panes=3, grille=False, proud=0.1)
    window(f, u + 0.4, u + SF["pier_every"] - 0.4, level(2) + 0.9, level(2) + 3.0, panes=3, grille=False, proud=0.1)
    u += SF["pier_every"]
E = F["entrance"]
f.box("podium_dark", E["u0"], E["u1"], 0.1, 0.12, PL, PL + E["door_h"] + 0.4)
window(f, E["u0"] + 0.2, E["u1"] - 0.2, PL, PL + E["door_h"], panes=6, grille=False, proud=0.12)
G2 = F["f2_glazing"]
window(f, G2["u0"], G2["u1"], level(2) + 0.5, level(2) + 3.3, panes=8, grille=False, proud=0.1)
Cn = F["canopy"]
f.box("canopy", Cn["u0"], Cn["u1"], 0, Cn["depth"], Cn["z"], Cn["z"] + 0.45)
if Cn.get("columns", True):
    for uu in (Cn["u0"] + 0.3, Cn["u1"] - 0.6):
        f.box("canopy", uu, uu + 0.3, Cn["depth"] - 0.5, Cn["depth"] - 0.2, 0, Cn["z"])
St = F["steps"]
for k in range(St["risers"]):
    h = PL / St["risers"]
    f.box("steps", St["u0"] + k * 0.3, St["u1"] - k * 0.3, 0, 2.2 - k * 0.32, k * h, (k + 1) * h)
for uu in (St["u0"] - 0.4, St["u1"]):                                   # side cheek walls
    f.box("podium", uu, uu + 0.4, 0, 2.2, 0, PL + 0.6)
SG = F["sign"]
f.box("podium_dark", SG["u0"], SG["u1"], 0.1, 0.22, SG["z"] - 0.1, SG["z"] + SG["h"] + 0.1)
B.text(SG["text"], f, (SG["u0"] + SG["u1"]) / 2, 0.22, SG["z"] + SG["h"] / 2, SG["h"] * 0.95, "gold", serif=True, extrude=0.03)
GL = F["stair_glazing"]
window(f, GL["u0"], GL["u1"], PL + 0.2, PODIUM_TOP - 0.45, panes=4, grille=False, proud=0.1)
if GL.get("banner", True):
    f.box("banner", GL["u0"] + 0.2, GL["u1"] - 0.2, 0.18, 0.2, PL + 0.2, PL + 1.2)

# ------------------------------------------------------------------ podium: south (solid ground floor)
f = SOUTH
podium_shell(f)
u = SF["u0"]
while u + SF["pier_every"] <= f.W - 1.0 + 1e-6:
    window(f, u + 0.4, u + SF["pier_every"] - 0.4, level(2) + 0.9, level(2) + 3.0, panes=3, grille=False, proud=0.1)
    u += SF["pier_every"]

# ------------------------------------------------------------------ podium: west (LIBRARY) and east
for f, is_west in ((WEST, True), (EAST, False)):
    podium_shell(f)
    GLw = Wf["stair_glazing"]
    window(f, GLw["u0"] + 0.2, GLw["u1"] - 0.2, PL + 0.2, PODIUM_TOP - 0.45, panes=3, grille=False, proud=0.1)
    for u0, u1 in Wf["f2_windows"]:
        window(f, u0, u1, level(2) + 0.6, level(2) + 2.0, panes=2, grille=False, proud=0.1)
    if not is_west:
        continue
    Bn = Wf.get("banners")
    if Bn:
        f.box("banner", Bn["u0"], Bn["u1"], 0.18, 0.2, Bn["z0"], Bn["z1"])
        B.text("★", f, (Bn["u0"] + Bn["u1"]) / 2, 0.2, (Bn["z0"] + Bn["z1"]) / 2, 0.75, "star", serif=False, extrude=0.005)
    LT = Wf["library_text"]
    B.text(LT["text"], f, (LT["u0"] + LT["u1"]) / 2, 0.1, LT["z"] + LT["h"] / 2, LT["h"] * 1.1, "gold", serif=True)
    T = Wf["tb2_sign"]
    f.box("sign_blue", T["u"], T["u"] + T["w"], 0.1, 0.14, T["z"], T["z"] + T["h"])
    B.text(T["text"], f, T["u"] + T["w"] / 2, 0.14, T["z"] + T["h"] / 2, T["h"] * 0.6, "white", serif=False, extrude=0.01)
    for u0, u1, kind in Wf["doors"]:
        key = {"beige": "door_beige", "dark": "door_dark", "grille": "white"}[kind]
        f.box("podium_dark", u0 - 0.12, u1 + 0.12, 0.1, 0.16, PL, PL + 2.62)
        f.box(key, u0, u1, 0.1, 0.18, PL, PL + 2.5)
        if kind == "grille":
            k = u0 + 0.1
            while k < u1:
                f.box("grille", k - 0.015, k + 0.015, 0.18, 0.21, PL, PL + 2.5); k += 0.15
        for k in range(3):
            f.box("steps", u0 - 0.3, u1 + 0.3, 0, 0.9 - k * 0.25, k * PL / 3, (k + 1) * PL / 3)

B.finish((X0, Y0, X1, Y1), TOP_CREAM, "TB2")
