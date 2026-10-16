"""B4 – build the sports zone (track + football field, basketball, volleyball, grandstand, floodlights)
from layout/buildings/sports.json.
Usage: blender -b --factory-startup --python scripts/build_sports.py
Outputs: blender/sports.blend, export/SPORTS.fbx, export/SPORTS.glb
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lib import Builder, ROOT
from mathutils import Vector

S = json.load(open(os.path.join(ROOT, "layout", "buildings", "sports.json"), encoding="utf-8"))
C = S["colors"]

B = Builder("SPORTS")
for key, rough, metal in (("base", 0.95, 0), ("track", 0.9, 0), ("line", 0.7, 0), ("turf_a", 0.95, 0), ("turf_b", 0.95, 0),
                          ("apron", 0.95, 0), ("basket", 0.8, 0), ("basket_key", 0.8, 0), ("volley", 0.8, 0), ("volley_out", 0.85, 0),
                          ("concrete", 0.9, 0), ("seat_a", 0.5, 0), ("seat_b", 0.5, 0), ("steel", 0.45, 0.8), ("roof", 0.4, 0.6),
                          ("post", 0.5, 0.3), ("net", 0.8, 0), ("board", 0.3, 0), ("rim", 0.4, 0.6)):
    B.material(key, C[key], rough, metal)
for key, alpha in (("net", 0.55),):                                       # see-through nets
    m = B.mat[key]
    next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"].default_value = alpha
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        if hasattr(m, attr):
            try:
                setattr(m, attr, val)
            except TypeError:
                pass

LW = 0.06                                                                 # painted line width


def rr_outline(x0, y0, x1, y1, r, n=12):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def ring(key, outer, inner, z0, z1):
    """Closed slab between two outlines with the same vertex count."""
    bm = B.bm[key]
    n = len(outer)
    ot = [bm.verts.new((x, y, z1)) for x, y in outer]; it = [bm.verts.new((x, y, z1)) for x, y in inner]
    ob = [bm.verts.new((x, y, z0)) for x, y in outer]; ib = [bm.verts.new((x, y, z0)) for x, y in inner]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ot[i], ot[j], it[j], it[i])); bm.faces.new((ob[i], ib[i], ib[j], ob[j]))
        bm.faces.new((ob[i], ob[j], ot[j], ot[i])); bm.faces.new((ib[i], it[i], it[j], ib[j]))


def disc_slab(key, outline, z0, z1):
    bm = B.bm[key]
    t = [bm.verts.new((x, y, z1)) for x, y in outline]; b = [bm.verts.new((x, y, z0)) for x, y in outline]
    bm.faces.new(t); bm.faces.new(b[::-1])
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        bm.faces.new((b[i], b[j], t[j], t[i]))


def circle_pts(cx, cy, r, a0=0.0, a1=2 * math.pi, n=40):
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def arc_line(cx, cy, r, a0, a1, z, n=32):
    outer = circle_pts(cx, cy, r + LW / 2, a0, a1, n); inner = circle_pts(cx, cy, r - LW / 2, a0, a1, n)
    bm = B.bm["line"]
    o = [bm.verts.new((x, y, z)) for x, y in outer]; i_ = [bm.verts.new((x, y, z)) for x, y in inner]
    for k in range(n):
        bm.faces.new((i_[k], o[k], o[k + 1], i_[k + 1]))


def rect_lines(x0, y0, x1, y1, z):
    for a, b, c, d in ((x0, x1, y0, y0), (x0, x1, y1, y1), (x0, x0, y0, y1), (x1, x1, y0, y1)):
        B.wbox("line", min(a, b) - LW / 2, max(a, b) + LW / 2, min(c, d) - LW / 2, max(c, d) + LW / 2, z, z + 0.004)


# ================================================================== base slab
bx0, by0, bx1, by1 = S["base"]
B.wbox("base", bx0, bx1, by0, by1, 0, 0.03)

# ================================================================== running track + infield
T = S["track"]; tw = T["lanes"] * T["lane_w"]
x0, y0, x1, y1 = T["rect"]
outer = rr_outline(x0, y0, x1, y1, T["corner_r"])
inner = rr_outline(x0 + tw, y0 + tw, x1 - tw, y1 - tw, T["corner_r"] - tw)
ring("track", outer, inner, 0.03, 0.06)
disc_slab("apron", inner, 0.03, 0.06)
for k in range(0, T["lanes"] + 1):
    o = k * T["lane_w"]
    lo = rr_outline(x0 + o - LW / 2, y0 + o - LW / 2, x1 - o + LW / 2, y1 - o + LW / 2, T["corner_r"] - o + LW / 2)
    li = rr_outline(x0 + o + LW / 2, y0 + o + LW / 2, x1 - o - LW / 2, y1 - o - LW / 2, T["corner_r"] - o - LW / 2)
    ring("line", lo, li, 0.06, 0.064)
B.wbox("line", T["start_x"] - 0.05, T["start_x"] + 0.05, y0, y0 + tw, 0.06, 0.065)

# ================================================================== two football fields, long axis north–south
F = S["field"]
gw, gh, gd = F["goal"]
zl = 0.065
GOALS = []
for fx0, fy0, fx1, fy1 in F["rects"]:
    y, i = fy0, 0
    while y < fy1 - 1e-6:                                                  # mowing stripes across the pitch
        B.wbox("turf_a" if i % 2 == 0 else "turf_b", fx0, fx1, y, min(y + F["stripe_w"], fy1), 0.06, 0.065)
        y += F["stripe_w"]; i += 1
    rect_lines(fx0, fy0, fx1, fy1, zl)
    fcx, fcy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
    B.wbox("line", fx0, fx1, fcy - LW / 2, fcy + LW / 2, zl, zl + 0.004)
    arc_line(fcx, fcy, F["center_r"], 0, 2 * math.pi, zl, 40)
    for side in (-1, 1):
        gy = fy0 if side < 0 else fy1
        dep, wid = F["penalty"]
        rect_lines(fcx - wid / 2, min(gy, gy - side * dep), fcx + wid / 2, max(gy, gy - side * dep), zl)
        sy = gy - side * 6.0                                               # penalty spot
        B.wbox("line", fcx - 0.1, fcx + 0.1, sy - 0.1, sy + 0.1, zl, zl + 0.004)
        by_ = gy + side * gd                                               # goal frame + see-through net
        for xx in (fcx - gw / 2, fcx + gw / 2):
            B.tube("post", (xx, gy, 0.06), (xx, gy, gh), 0.05, 8)
            B.tube("post", (xx, gy, gh), (xx, by_, 0.06), 0.03, 6)
            B.tube("post", (xx, by_, 0.06), (xx, gy, 0.06), 0.03, 6)
        B.tube("post", (fcx - gw / 2, gy, gh), (fcx + gw / 2, gy, gh), 0.05, 8)
        B.tube("post", (fcx - gw / 2, by_, 0.06), (fcx + gw / 2, by_, 0.06), 0.03, 6)
        bm = B.bm["net"]
        bm.faces.new([bm.verts.new(p) for p in ((fcx - gw / 2, gy, gh), (fcx + gw / 2, gy, gh), (fcx + gw / 2, by_, 0.06), (fcx - gw / 2, by_, 0.06))])
        for xx in (fcx - gw / 2, fcx + gw / 2):
            bm.faces.new([bm.verts.new(p) for p in ((xx, gy, 0.06), (xx, gy, gh), (xx, by_, 0.06))])
        GOALS.append((fcx - gw / 2, fcx + gw / 2, min(gy, by_), max(gy, by_), gh))

# ================================================================== basketball
Bk = S["basketball"]
B.wbox("basket", Bk["surface"][0], Bk["surface"][2], Bk["surface"][1], Bk["surface"][3], 0.03, 0.05)
bcx = (Bk["surface"][0] + Bk["surface"][2]) / 2; bcy = (Bk["surface"][1] + Bk["surface"][3]) / 2
cw, cl = Bk["court"]; zb = 0.05
rect_lines(bcx - cw / 2, bcy - cl / 2, bcx + cw / 2, bcy + cl / 2, zb)
B.wbox("line", bcx - cw / 2, bcx + cw / 2, bcy - LW / 2, bcy + LW / 2, zb, zb + 0.004)
arc_line(bcx, bcy, Bk["circle_r"], 0, 2 * math.pi, zb)
kd, kw = Bk["key"]
for side in (-1, 1):
    by = bcy + side * cl / 2
    ky0, ky1 = min(by, by - side * kd), max(by, by - side * kd)
    B.wbox("basket_key", bcx - kw / 2, bcx + kw / 2, ky0, ky1, zb, zb + 0.002)
    rect_lines(bcx - kw / 2, ky0, bcx + kw / 2, ky1, zb + 0.002)
    ft = by - side * kd
    arc_line(bcx, ft, Bk["circle_r"], 0, 2 * math.pi, zb + 0.002)
    hy = by - side * 1.575                                                # hoop centre
    r3 = Bk["three_r"]
    side_gap = cw / 2 - 0.9
    a = math.acos(side_gap / r3)
    if side > 0:
        arc_line(bcx, hy, r3, math.pi + a, 2 * math.pi - a, zb)
    else:
        arc_line(bcx, hy, r3, a, math.pi - a, zb)
    ycut = hy - side * r3 * math.sin(a)
    for xx in (bcx - side_gap, bcx + side_gap):
        B.wbox("line", xx - LW / 2, xx + LW / 2, min(by, ycut), max(by, ycut), zb, zb + 0.004)
    # hoop: post behind the baseline, arm, backboard, rim
    py = by + side * 1.0
    B.tube("steel", (bcx, py, 0.05), (bcx, py, 3.4), 0.08, 10)
    bb = by - side * 1.2
    B.tube("steel", (bcx, py, 3.3), (bcx, bb, 3.3), 0.05, 8)
    B.wbox("board", bcx - 0.9, bcx + 0.9, min(bb, bb + side * 0.05), max(bb, bb + side * 0.05), 2.9, 3.95)
    B.wbox("rim", bcx - 0.3, bcx + 0.3, min(bb, bb + side * 0.06), max(bb, bb + side * 0.06), 3.05, 3.5)
    rim = circle_pts(bcx, hy, 0.23, n=16)
    for k in range(16):
        (ax, ay), (cx2, cy2) = rim[k], rim[k + 1]
        B.tube("rim", (ax, ay, 3.05), (cx2, cy2, 3.05), 0.012, 4)

# ================================================================== volleyball
V = S["volleyball"]
B.wbox("volley_out", V["surface"][0], V["surface"][2], V["surface"][1], V["surface"][3], 0.03, 0.05)
vcx = (V["surface"][0] + V["surface"][2]) / 2; vcy = (V["surface"][1] + V["surface"][3]) / 2
vw, vl = V["court"]
B.wbox("volley", vcx - vw / 2, vcx + vw / 2, vcy - vl / 2, vcy + vl / 2, 0.05, 0.052)
rect_lines(vcx - vw / 2, vcy - vl / 2, vcx + vw / 2, vcy + vl / 2, 0.052)
for yy in (vcy, vcy - V["attack"], vcy + V["attack"]):
    B.wbox("line", vcx - vw / 2, vcx + vw / 2, yy - LW / 2, yy + LW / 2, 0.052, 0.056)
for xx in (vcx - vw / 2 - 0.8, vcx + vw / 2 + 0.8):
    B.tube("steel", (xx, vcy, 0.05), (xx, vcy, V["net_h"] + 0.1), 0.05, 8)
B.wbox("net", vcx - vw / 2 - 0.5, vcx + vw / 2 + 0.5, vcy - 0.01, vcy + 0.01, V["net_h"] - 1.0, V["net_h"])
B.wbox("board", vcx - vw / 2 - 0.5, vcx + vw / 2 + 0.5, vcy - 0.02, vcy + 0.02, V["net_h"] - 0.07, V["net_h"])

# ================================================================== grandstand (north side, faces the field)
St = S["stand"]; sx0, sy0, sx1, sy1 = St["rect"]
td, th, fh, n = St["tier_d"], St["tier_h"], St["front_h"], St["tiers"]
aw = St["aisle_w"]
segs = []                                                                 # seating blocks between aisles
edges = [sx0] + [e for a in St["aisles"] for e in (a - aw / 2, a + aw / 2)] + [sx1]
for k in range(0, len(edges), 2):
    segs.append((edges[k], edges[k + 1]))
for k in range(n):
    yk = sy0 + k * td
    zt = fh + k * th
    B.wbox("concrete", sx0, sx1, yk, sy1, 0, zt)                           # stepped terrace
    for si, (a, b) in enumerate(segs):                                     # plastic seat rows
        key = "seat_a" if (si + k) % 2 == 0 else "seat_b"
        B.wbox(key, a + 0.1, b - 0.1, yk + 0.15, yk + 0.55, zt, zt + 0.42)
        B.wbox(key, a + 0.1, b - 0.1, yk + 0.5, yk + 0.58, zt + 0.42, zt + 0.8)
for a in St["aisles"]:                                                     # half-step aisles
    for k in range(n):
        yk = sy0 + k * td
        zt = fh + k * th
        B.wbox("concrete", a - aw / 2, a + aw / 2, yk, yk + td / 2, zt, zt + th / 2)
for k in range(3):                                                         # steps up to the first tier
    B.wbox("concrete", sx0 + 2, sx0 + 4, sy0 - 0.9 + k * 0.3, sy0, 0, (k + 1) * fh / 3)
B.wbox("steel", sx0, sx1, sy0 - 0.03, sy0 + 0.03, fh + 0.95, fh + 1.0)    # front rail
x = sx0
while x <= sx1 + 1e-6:
    B.wbox("steel", x - 0.02, x + 0.02, sy0 - 0.02, sy0 + 0.02, fh, fh + 1.0); x += 1.4
topz = fh + (n - 1) * th
B.wbox("concrete", sx0, sx1, sy1 - 0.2, sy1, topz, topz + 1.2)            # back wall
for xx in (sx0, sx1 - 0.2):                                                # side walls
    bm = B.bm["concrete"]
    pts = [(xx, sy0, 0), (xx, sy1, 0), (xx, sy1, topz + 1.2), (xx, sy0, fh + 0.4)]
    vv = [bm.verts.new(p) for p in pts] + [bm.verts.new((p[0] + 0.2, p[1], p[2])) for p in pts]
    for fc in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vv[i] for i in fc])
x = sx0 + 0.3
while x <= sx1 - 0.2:                                                      # roof columns + raking beams
    B.tube("steel", (x, sy1 + 0.15, 0), (x, sy1 + 0.15, St["roof_back"]), 0.12, 8)
    B.tube("steel", (x, sy1 + 0.15, St["roof_back"] - 0.15), (x, sy0 - St["roof_over"], St["roof_front"] - 0.15), 0.07, 6)
    B.tube("steel", (x, sy1 + 0.15, topz + 1.2), (x, sy1 + 0.15 - 3.0, St["roof_back"] - 0.4), 0.05, 6)
    x += St["columns_step"]
pts = []
for xx in (sx0 - 0.3, sx1 + 0.3):
    for yy, zz in ((sy0 - St["roof_over"], St["roof_front"]), (sy1 + 0.4, St["roof_back"])):
        for t in (0.0, 0.1):
            pts.append(Vector((xx, yy, zz + t)))
B.hexa("roof", pts)

# ================================================================== floodlights
for lx, ly in S["lights"]["poles"]:
    h = S["lights"]["h"]
    B.tube("steel", (lx, ly, 0), (lx, ly, h), 0.18, 10)
    cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
    d = Vector((cx_ - lx, cy_ - ly, 0)).normalized()
    hx, hy = lx + d.x * 0.6, ly + d.y * 0.6
    B.wbox("board", hx - 1.0, hx + 1.0, hy - 0.25, hy + 0.25, h - 1.2, h)

COLLIDERS = [(sx0, sx1, sy0, sy1, topz + 1.2)]                             # only the grandstand blocks movement
COLLIDERS += GOALS
B.finish(S["base"], S["lights"]["h"], "SPORTS", COLLIDERS)
