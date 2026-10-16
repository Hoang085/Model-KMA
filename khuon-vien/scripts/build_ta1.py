"""B4 – build TA1 in Blender from layout/buildings/ta1.json + layout/campus_layout.json.
World coords = campus plan coords (metres): origin at the main gate, +Y into the campus, Z up.
Usage: blender -b --factory-startup --python scripts/build_ta1.py
Outputs: blender/ta1.blend, export/TA1.fbx, export/TA1.glb
"""
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "ta1.json"), encoding="utf-8"))
LAYOUT = json.load(open(os.path.join(ROOT, "layout", "campus_layout.json"), encoding="utf-8"))
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
C = SPEC["colors"]
X0, Y0, X1, Y1 = next(b["rect"] for b in LAYOUT["buildings"] if b["id"] == "ta1")
NF, PL, GH, FH, PH = SPEC["floors"], SPEC["plinth_h"], SPEC["ground_h"], SPEC["floor_h"], SPEC["parapet_h"]


def level(n):
    return PL if n == 1 else PL + GH + (n - 2) * FH


ROOF = level(NF + 1)
TOP = ROOF + PH

# ------------------------------------------------------------------ scene + materials
bpy.ops.wm.read_homefile(use_empty=True)
COL = bpy.data.collections.new("TA1"); bpy.context.scene.collection.children.link(COL)


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


TEX = os.path.join(ROOT, "textures")
TILE = json.load(open(os.path.join(TEX, "tile_sizes.json"))) if os.path.exists(os.path.join(TEX, "tile_sizes.json")) else {}


def material(name, hexcol, rough=0.85, metal=0.0, albedo=None, normal=None, normal_strength=0.6):
    m = bpy.data.materials.new("TA1_" + name)
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = srgb(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    m.diffuse_color = srgb(hexcol)
    if albedo and os.path.exists(os.path.join(TEX, albedo + ".png")):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(TEX, albedo + ".png"), check_existing=True)
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    if normal and os.path.exists(os.path.join(TEX, normal + ".png")):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(TEX, normal + ".png"), check_existing=True)
        t.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = normal_strength
        nt.links.new(t.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


MAT = {
    "wall": material("Wall", C["wall_main"], 0.9, 0, "paint_wall_albedo", "paint_normal"),
    "fin": material("Fin", C["fin"], 0.85, 0, "paint_fin_albedo", "paint_normal"),
    "slab": material("Slab", C["slab"], 0.85, 0, "paint_slab_albedo", "paint_normal"),
    "louver": material("Louver", C["louver"], 0.45, 0.6, "metal_albedo"),
    "ac_back": material("LouverBack", "#3b4148", 0.9),
    "frame": material("WindowFrame", "#2b3036", 0.4, 0.6),
    "glass": material("Glass", "#22313d", 0.04, 0.15),
    "opening": material("Opening", C["opening"], 1.0, 0, "paint_dark_albedo", "paint_normal"),
    "lobby": material("LobbyWall", "#e4e6e6", 0.8),
    "steps": material("Steps", C["steps"], 0.75, 0, "granite_albedo", "granite_normal", 0.4),
    "rail": material("Steel", "#c9ced3", 0.25, 1.0),
    "white": material("White", "#f1f1ef", 0.6),
    "sign": material("SignBlue", C["sign_blue"], 0.4),
    "tile": material("RoofTile", C["tile_red"], 0.7, 0, "tile_albedo", "tile_normal", 0.8),
    "board": material("Board", C["board"], 0.8),
    "brick": material("Brick", C["brick"], 0.9, 0, "brick_albedo", "brick_normal", 0.8),
    "roof": material("RoofSlab", "#b9bcbc", 0.95, 0, "roof_albedo", "paint_normal"),
}
# metres covered by one texture repeat, per material
UV_TILE = {"wall": TILE.get("paint", 4), "fin": TILE.get("paint", 4), "slab": TILE.get("paint", 4),
           "opening": TILE.get("paint", 4), "roof": TILE.get("roof", 6), "steps": TILE.get("granite", 1.5),
           "louver": TILE.get("metal", 2), "brick": TILE.get("brick", 1), "tile": TILE.get("tile", 1)}
BM = {k: bmesh.new() for k in MAT}


# ------------------------------------------------------------------ geometry helpers
def hexa(key, pts):
    """8 corner points (local box order) -> closed hexahedron in bmesh[key]."""
    bm = BM[key]
    v = [bm.verts.new(p) for p in pts]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([v[i] for i in f])


def wbox(key, x0, x1, y0, y1, z0, z1):
    hexa(key, [Vector((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])


def tube(key, p0, p1, r, seg=8):
    bm = BM[key]
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0).normalized()
    s = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized()
    t = d.cross(s)
    a = [bm.verts.new(p0 + (s * math.cos(2 * math.pi * k / seg) + t * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)]
    b = [bm.verts.new(p1 + (s * math.cos(2 * math.pi * k / seg) + t * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)]
    for k in range(seg):
        bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bm.faces.new(a[::-1]); bm.faces.new(b)


class Face:
    """Local facade frame: u along the face, w outward from the facade plane, z up."""
    def __init__(self, origin, u_dir, normal, width):
        self.O, self.U, self.N, self.W = Vector(origin), Vector(u_dir), Vector(normal), width

    def P(self, u, w, z):
        return self.O + self.U * u + self.N * w + Vector((0, 0, z))

    def box(self, key, u0, u1, w0, w1, z0, z1):
        hexa(key, [self.P(u, w, z) for u in (u0, u1) for w in (w0, w1) for z in (z0, z1)])

    def window(self, u0, u1, z0, z1, mullions=1, frame="frame", proud=0.0):
        t = 0.06
        self.box("glass", u0, u1, proud - 0.02, proud + 0.02, z0, z1)
        self.box(frame, u0 - t, u1 + t, proud, proud + 0.08, z0 - t, z0)
        self.box(frame, u0 - t, u1 + t, proud, proud + 0.08, z1, z1 + t)
        self.box(frame, u0 - t, u0, proud, proud + 0.08, z0, z1)
        self.box(frame, u1, u1 + t, proud, proud + 0.08, z0, z1)
        for i in range(1, mullions + 1):
            uu = u0 + (u1 - u0) * i / (mullions + 1)
            self.box(frame, uu - 0.025, uu + 0.025, proud, proud + 0.06, z0, z1)
        self.box("white", u0 - 0.14, u1 + 0.14, proud, proud + 0.16, z0 - 0.12, z0 - t)    # sill

    def steps(self, u0, u1, risers, depth0, inset_u=0.3, inset_w=0.32):
        h = PL / risers
        for k in range(risers):
            self.box("steps", u0 + k * inset_u, u1 - k * inset_u, 0, depth0 - k * inset_w, k * h, (k + 1) * h)

    def joints(self, us, levels):
        for u in us:
            self.box("slab", u - 0.02, u + 0.02, 0, 0.012, level(2), ROOF)
        for n in levels:
            self.box("slab", 0, self.W, 0, 0.012, level(n) - 0.02, level(n) + 0.02)


NORTH = Face((X1, Y1, 0), (-1, 0, 0), (0, 1, 0), X1 - X0)
EAST = Face((X1, Y0, 0), (0, 1, 0), (1, 0, 0), Y1 - Y0)
SOUTH = Face((X0, Y0, 0), (1, 0, 0), (0, -1, 0), X1 - X0)
WEST = Face((X0, Y0, 0), (0, 1, 0), (-1, 0, 0), Y1 - Y0)       # same u as the east face (core at the south end)

# ------------------------------------------------------------------ body, plinth, roof
wbox("wall", X0, X1, Y0, Y1, 0, ROOF)
wbox("steps", X0 - 0.05, X1 + 0.05, Y0 - 0.05, Y1 + 0.05, 0, PL)
t = 0.25
for xa, xb, ya, yb in ((X0, X1, Y0, Y0 + t), (X0, X1, Y1 - t, Y1), (X0, X0 + t, Y0, Y1), (X1 - t, X1, Y0, Y1)):
    wbox("wall", xa, xb, ya, yb, ROOF, TOP)
wbox("fin", X0 - 0.06, X1 + 0.06, Y0 - 0.06, Y0 + t, TOP, TOP + 0.08)
wbox("fin", X0 - 0.06, X1 + 0.06, Y1 - t, Y1 + 0.06, TOP, TOP + 0.08)
wbox("fin", X0 - 0.06, X0 + t, Y0, Y1, TOP, TOP + 0.08)
wbox("fin", X1 - t, X1 + 0.06, Y0, Y1, TOP, TOP + 0.08)
wbox("roof", X0 + t, X1 - t, Y0 + t, Y1 - t, ROOF, ROOF + 0.05)
# rooftop: lift machine room + water tanks
wbox("wall", X0 + 13, X0 + 19.5, Y0 + 9, Y0 + 14, ROOF, ROOF + 3.0)
wbox("fin", X0 + 12.8, X0 + 19.7, Y0 + 8.8, Y0 + 14.2, ROOF + 3.0, ROOF + 3.15)
for i in range(3):
    cx, cy = X0 + 24 + i * 2.2, Y0 + 20
    bm = BM["white"]
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.9, radius2=0.9, depth=2.2,
                          matrix=Matrix.Translation((cx, cy, ROOF + 1.4)))
    wbox("steps", cx - 1.0, cx + 1.0, cy - 1.0, cy + 1.0, ROOF, ROOF + 0.3)

# ------------------------------------------------------------------ north face (main entrance)
F = SPEC["faces"]["north"]
f = NORTH
bay = f.W / F["bays"]
left_w = F["left_zone_bays"] * bay
zt = level(F["left_zone_floors"] + 1)
for n in range(2, NF + 1):
    f.box("slab", 0, f.W, 0, 0.18, level(n) - 0.15, level(n) + 0.1)
for b in range(0, F["left_zone_bays"] + 1, 2):                      # thick pilasters, lower left zone
    f.box("fin", b * bay - 0.45, b * bay + 0.45, 0, 0.3, 0, zt)
for i in range(F["bays"] + 1):                                       # vertical fins
    u = i * bay
    z0 = zt if u <= left_w + 1e-6 else level(2)
    f.box("fin", max(0, u - F["fin_w"] / 2), min(f.W, u + F["fin_w"] / 2), 0, F["fin_depth"], z0, ROOF)
for n in range(1, NF + 1):
    z0, z1 = level(n), level(n + 1)
    for b in range(F["bays"]):
        u0, u1 = b * bay, (b + 1) * bay
        in_left = u1 <= left_w + 1e-6
        start = F["left_zone_floors"] + 1 if in_left else F["grid_start_floor"]
        if n >= start:
            lu0 = u0 + F["fin_w"] / 2 + 0.12
            lu1 = lu0 + (u1 - u0) * 0.66
            f.box("ac_back", lu0, lu1, 0, 0.05, z0 + 0.5, z1 - 0.7)
            k = z0 + 0.62
            while k < z1 - 0.75:
                f.box("louver", lu0, lu1, 0.24, 0.36, k, k + 0.05); k += 0.16
            f.box("louver", lu0 - 0.04, lu0, 0, 0.38, z0 + 0.5, z1 - 0.7)
            f.box("louver", lu1, lu1 + 0.04, 0, 0.38, z0 + 0.5, z1 - 0.7)
            f.window(lu1 + 0.2, u1 - F["fin_w"] / 2 - 0.15, z0 + 0.9, z1 - 0.6, mullions=0)
        elif in_left and n < F["left_zone_floors"]:
            if b % 2 == 0:
                cu = u1                                              # centred between two pilasters
                f.window(cu - 0.8, cu + 0.8, z0 + 1.2, z0 + 2.3, mullions=1)
                for k in range(1, 5):
                    f.box("frame", cu - 0.8, cu + 0.8, 0.06, 0.09, z0 + 1.2 + k * 0.22, z0 + 1.2 + k * 0.22 + 0.03)
        elif in_left and n == F["left_zone_floors"]:
            cu = (u0 + u1) / 2
            f.box("white", cu - 0.45, cu + 0.45, 0, 0.35, z1 - 1.25, z1 - 0.6)          # AC outdoor unit
            f.box("frame", cu - 0.3, cu + 0.3, 0.35, 0.37, z1 - 1.15, z1 - 0.7)
        elif not in_left and n == 2:
            cu = (u0 + u1) / 2
            f.window(cu - 0.45, cu + 0.45, z0 + 1.3, z0 + 2.3, mullions=0)
E = F["entrance"]
f.box("lobby", E["u0"], E["u1"], 0, 0.01, PL, level(2) - 0.15)
for g0, g1 in E["door_groups"]:
    f.box("glass", g0, g1, 0.0, 0.03, PL, PL + E["door_h"])
    u = g0
    while u <= g1 + 1e-6:
        f.box("frame", u - 0.04, u + 0.04, 0, 0.1, PL, PL + E["door_h"]); u += (g1 - g0) / 6
    for zz in (PL, PL + 2.4, PL + E["door_h"] - 0.08):
        f.box("frame", g0, g1, 0, 0.1, zz, zz + 0.08)
Cn = F["canopy"]
f.box("glass", Cn["u0"], Cn["u1"], 0, Cn["depth"], Cn["z"], Cn["z"] + 0.06)
f.box("rail", Cn["u0"], Cn["u1"], Cn["depth"] - 0.12, Cn["depth"], Cn["z"] - 0.12, Cn["z"] + 0.1)
for u in (Cn["u0"], Cn["u1"] - 0.1):
    f.box("rail", u, u + 0.1, 0, Cn["depth"], Cn["z"] - 0.12, Cn["z"] + 0.1)
for u in (Cn["u0"] + 1.5, Cn["u0"] + 7.0, Cn["u1"] - 7.0, Cn["u1"] - 1.5):
    tube("rail", f.P(u, Cn["depth"] - 0.1, Cn["z"] + 0.1), f.P(u, 0, Cn["z"] + 1.7), 0.03)
St = F["steps"]
f.steps(St["u0"], St["u1"], St["risers"], 1.7, inset_u=0.35)
R = F["ramp"]
hexa("brick", [f.P(u, w, z) for u, zt_ in ((R["u0"], 0.02), (R["u1"], PL)) for w in (0, 1.6) for z in (0, zt_)])
for u in [R["u0"] + i for i in range(int(R["u1"] - R["u0"]) + 1)]:
    zr = (u - R["u0"]) / (R["u1"] - R["u0"]) * PL
    tube("rail", f.P(u, 1.5, zr), f.P(u, 1.5, zr + R["rail_h"]), 0.025, 6)
for hh in (R["rail_h"], R["rail_h"] * 0.55):
    tube("rail", f.P(R["u0"], 1.5, hh), f.P(R["u1"], 1.5, PL + hh), 0.025, 6)

# ------------------------------------------------------------------ east face (facing the gate)
F = SPEC["faces"]["east"]
f = EAST
f.joints(F["panel_joints_u"], (5, 8))
K = F["core"]
kd = K["depth"]
f.box("wall", K["u0"], K["u0"] + 0.45, 0, kd, level(K["from_floor"]) - 0.4, TOP + K["top_extra"])
f.box("wall", K["u1"] - 0.45, K["u1"], 0, kd, level(K["from_floor"]) - 0.4, TOP + K["top_extra"])
f.box("opening", K["u0"] + 0.45, K["u1"] - 0.45, 0, 0.01, level(K["from_floor"]), ROOF)
for n in range(K["from_floor"], NF + 2):
    z = level(n)
    f.box("wall", K["u0"], K["u1"], 0, kd, z - 0.4, z)                                   # floor slab edge
    if n <= NF:
        f.box("wall", K["u0"] + 0.45, K["u1"] - 0.45, kd - 0.15, kd, z, z + K["parapet_h"])  # balcony parapet
f.box("wall", K["u0"], K["u1"], 0, kd, TOP + K["top_extra"] - 0.4, TOP + K["top_extra"])
B = F["band_floor2"]
z2 = level(2)
f.box("wall", B["u0"], B["u1"], 0, B["depth"], z2 - 0.4, z2)                            # cantilever slab
f.box("wall", B["u0"], B["u1"], 0, B["depth"], level(3) - 0.4, level(3))                 # balcony roof slab
f.box("opening", B["u0"], B["u1"], 0, 0.01, z2, level(3) - 0.4)
cuts = sorted([(B["u0"] + 1.2 + i * 0.7, 0.28) for i in range(B["slots"] // 2)] +
              [(B["u1"] - 1.4 - i * 0.7, 0.28) for i in range(B["slots"] - B["slots"] // 2)] +
              [(B["u0"] + 4.2, 2.0)])
pz0, pz1 = z2 + 0.3, z2 + B["parapet_h"] - 0.25
wf0, wf1 = B["depth"] - 0.15, B["depth"]
f.box("wall", B["u0"], B["u1"], wf0, wf1, z2, pz0)
f.box("wall", B["u0"], B["u1"], wf0, wf1, pz1, z2 + B["parapet_h"])
prev = B["u0"]
for cu, cw in cuts:
    if cu > prev:
        f.box("wall", prev, cu, wf0, wf1, pz0, pz1)
    prev = cu + cw
f.box("wall", prev, B["u1"], wf0, wf1, pz0, pz1)
f.box("wall", B["u1"] - 0.15, B["u1"], 0, B["depth"], z2, z2 + B["parapet_h"])           # end wall
for u in (B["u0"] + 0.2, B["u1"] - 0.6):
    f.box("wall", u, u + 0.4, B["depth"] - 0.4, B["depth"], 0, z2 - 0.4)                  # columns
En = F["entrance"]
f.window(En["glass"][0], En["glass"][1], PL, PL + En["h"], mullions=1, proud=0.0)
f.box("white", En["door"][0], En["door"][1], 0, 0.06, PL, PL + En["h"] - 0.2)
f.box("glass", En["door"][0] + 0.2, En["door"][1] - 0.2, 0.06, 0.07, PL + 1.6, PL + 2.1)
f.box("frame", En["door"][1] - 0.2, En["door"][1] - 0.1, 0.06, 0.12, PL + 1.0, PL + 1.05)
St = F["steps"]
f.steps(St["u0"], St["u1"], St["risers"], 1.3, inset_u=0.3, inset_w=0.25)
# external stair: landing beyond the south end + straight flight up to the floor-2 balcony
X = F["ext_stair"]
wl0, wl1 = B["depth"] + 0.1, B["depth"] + 0.1 + X["width"]
f.box("wall", -1.6, 0.0, 0, wl1, z2 - 0.3, z2)                                            # landing
f.box("wall", -1.6, -1.45, 0, wl1, z2, z2 + 1.0)
f.box("wall", -1.6, 0.0, wl1 - 0.15, wl1, z2, z2 + 1.0)
f.box("wall", -1.6, -1.2, wl1 - 0.4, wl1, 0, z2 - 0.3)                                     # landing column
nst = math.ceil(z2 / 0.17); run = X["u_bottom"] / nst; hs = z2 / nst
for i in range(nst):
    ua, ub = X["u_bottom"] - (i + 1) * run, X["u_bottom"] - i * run
    f.box("steps", ua, ub, wl0, wl1, max(0.0, (i + 1) * hs - 0.4), (i + 1) * hs)
for wa, wb in ((wl0 - 0.15, wl0), (wl1 - 0.15, wl1)):                                      # solid side walls
    hexa("wall", [f.P(u, w, z) for u, zz in ((X["u_bottom"], 0.0), (0.0, z2)) for w in (wa, wb)
                  for z in (max(0.0, zz - 0.45), zz + X["wall_h"])])
# sign + notice board + brick strip
G = F["sign"]
f.box("sign", G["u"], G["u"] + G["w"], 0, 0.04, G["z"], G["z"] + G["h"])
N = F["notice_board"]
f.box("board", N["u0"], N["u1"], 0, 0.12, N["z0"], N["z1"])
for i in range(6):
    u = N["u0"] + 0.6 + i * 1.5
    f.box("white", u, u + 1.0, 0.12, 0.13, N["z0"] + 0.5, N["z0"] + 1.6)
ztop = {0.0: N["z1"] + N["roof_h"], 0.75: N["z1"]}                                       # roof slopes away from the wall
hexa("tile", [f.P(u, w, z) for u in (N["u0"] - 0.3, N["u1"] + 0.3) for w in (0.0, 0.75)
              for z in (ztop[w] - 0.06, ztop[w])])
Bs = F["brick_strip"]
f.box("brick", Bs["u0"], Bs["u1"], 0, Bs["depth"], 0, 0.02)

# ------------------------------------------------------------------ west face (facing TA2)
Wf = SPEC["faces"]["west"]
f = WEST
f.joints(F["panel_joints_u"], (5, 8))
f.box("wall", K["u0"], K["u0"] + 0.45, 0, kd, level(2) - 0.4, TOP + K["top_extra"])
f.box("wall", K["u1"] - 0.45, K["u1"], 0, kd, level(2) - 0.4, TOP + K["top_extra"])
for n in range(2, NF + 2):
    z = level(n)
    f.box("wall", K["u0"], K["u1"], 0, kd, z - 0.35, z)
    if n <= NF:
        za, zb = z + Wf["window_sill"], z + Wf["window_sill"] + Wf["window_h"]
        f.box("wall", K["u0"] + 0.45, K["u1"] - 0.45, 0, kd, z, za)
        f.box("wall", K["u0"] + 0.45, K["u1"] - 0.45, 0, kd, zb, level(n + 1) - 0.35)
        f.box("wall", K["u0"] + 0.45, K["u0"] + 0.8, 0, kd, za, zb)
        f.box("wall", K["u1"] - 0.8, K["u1"] - 0.45, 0, kd, za, zb)
        f.window(K["u0"] + 0.8, K["u1"] - 0.8, za, zb, mullions=1, proud=kd - 0.12)
f.box("wall", K["u0"], K["u1"], 0, kd, TOP + K["top_extra"] - 0.4, TOP + K["top_extra"])
for n in (1, 2):
    za = level(n) + Wf["window_sill"]
    for u0 in (B["u0"] + 1.0, B["u0"] + 4.2):
        f.window(u0, u0 + 2.4, za, za + Wf["window_h"], mullions=1)
f.window(En["glass"][0], En["glass"][1], PL, PL + En["h"], mullions=1)
f.box("white", En["door"][0], En["door"][1], 0, 0.06, PL, PL + En["h"] - 0.2)
f.steps(St["u0"], St["u1"], St["risers"], 1.3, inset_u=0.3, inset_w=0.25)

# ------------------------------------------------------------------ south face (facing Nhà xe)
Sf = SPEC["faces"]["south"]
f = SOUTH
for n in range(2, NF + 1):
    f.box("slab", 0, f.W, 0, 0.1, level(n) - 0.12, level(n) + 0.08)
sbay = f.W / SPEC["faces"]["north"]["bays"]
for n in range(1, NF + 1):
    za = level(n) + Sf["window_sill"] + (0.4 if n == 1 else 0)
    for b in range(SPEC["faces"]["north"]["bays"]):
        cu = (b + 0.5) * sbay
        f.window(cu - Sf["window_w"] / 2, cu + Sf["window_w"] / 2, za, za + Sf["window_h"], mullions=1)

# ------------------------------------------------------------------ meshes -> one object (+ text sign)
objs = []
for key, bm in BM.items():
    if not bm.verts:
        bm.free(); continue
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # world-space box-projected UVs: one texture repeat = UV_TILE[key] metres on every face
    uvl = bm.loops.layers.uv.new("UVMap")
    ts = UV_TILE.get(key, 2.0)
    for face in bm.faces:
        n = face.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for lp in face.loops:
            co = lp.vert.co
            if ax == 0:
                uv = (co.y * (1 if n.x > 0 else -1), co.z)
            elif ax == 1:
                uv = (co.x * (-1 if n.y > 0 else 1), co.z)
            else:
                uv = (co.x, co.y)
            lp[uvl].uv = (uv[0] / ts, uv[1] / ts)
    me = bpy.data.meshes.new("TA1_" + key)
    bm.to_mesh(me); bm.free()
    me.materials.append(MAT[key])
    ob = bpy.data.objects.new("TA1_" + key, me)
    COL.objects.link(ob); objs.append(ob)

# "TA1" letters on the blue sign (east face, reading direction = +Y)
G = SPEC["faces"]["east"]["sign"]
cu = bpy.data.curves.new("TA1_text", "FONT")
cu.body = G["text"]; cu.size = G["h"] * 0.62; cu.extrude = 0.015; cu.align_x = "CENTER"; cu.align_y = "CENTER"
cu.resolution_u = 3
if os.path.exists(FONT_PATH):
    cu.font = bpy.data.fonts.load(FONT_PATH)
tob = bpy.data.objects.new("TA1_text", cu); COL.objects.link(tob)
center = EAST.P(G["u"] + G["w"] / 2, 0.06, G["z"] + G["h"] / 2)
tob.matrix_world = Matrix(((0, 0, 1, center.x), (1, 0, 0, center.y), (0, 1, 0, center.z), (0, 0, 0, 1)))
bpy.context.view_layer.update()
tme = bpy.data.meshes.new_from_object(tob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
mw = tob.matrix_world.copy()
bpy.data.objects.remove(tob); bpy.data.curves.remove(cu)
tme.materials.clear(); tme.materials.append(MAT["white"])
tobj = bpy.data.objects.new("TA1_text", tme); COL.objects.link(tobj); tobj.matrix_world = mw
objs.append(tobj)

with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs):
    bpy.ops.object.join()
ta1 = objs[0]
ta1.name = "TA1"; ta1.data.name = "TA1"
# origin at the footprint centre on the ground (keeps world placement)
centre = Vector(((X0 + X1) / 2, (Y0 + Y1) / 2, 0))
ta1.data.transform(Matrix.Translation(-centre))
ta1.location = centre

# simple collider (body + entrance steps + stair ramp), hidden in renders
bm = bmesh.new()
for x0_, x1_, y0_, y1_, z0_, z1_ in ((X0, X1, Y0, Y1, 0, TOP),):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((x0_ if v.co.x < 0 else x1_, y0_ if v.co.y < 0 else y1_, z0_ if v.co.z < 0 else z1_))
cme = bpy.data.meshes.new("TA1_Collider"); bm.to_mesh(cme); bm.free()
col_ob = bpy.data.objects.new("TA1_Collider", cme); COL.objects.link(col_ob)
cme.transform(Matrix.Translation(-centre)); col_ob.location = centre
col_ob.hide_render = True; col_ob.display_type = "WIRE"

os.makedirs(os.path.join(ROOT, "blender"), exist_ok=True)
os.makedirs(os.path.join(ROOT, "export"), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "blender", "ta1.blend"))
for ob in bpy.context.view_layer.objects:
    ob.select_set(ob.name in ("TA1", "TA1_Collider"))
bpy.ops.export_scene.fbx(filepath=os.path.join(ROOT, "export", "TA1.fbx"), use_selection=True, object_types={"MESH"},
                         apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y", bake_space_transform=True,
                         mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
                         path_mode="COPY", embed_textures=True)
for ob in bpy.context.view_layer.objects:
    ob.select_set(ob.name == "TA1")
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, "export", "TA1.glb"), export_format="GLB", use_selection=True,
                          export_image_format="JPEG", export_jpeg_quality=85)
print("TA1 faces:", len(ta1.data.polygons), "| size:", tuple(round(v, 2) for v in ta1.dimensions),
      "| height to parapet:", round(TOP, 2))
