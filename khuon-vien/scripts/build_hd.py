"""B4 – build the admin tower (HĐ) + link + assembly hall from layout/buildings/hd.json + layout/campus_layout.json.
Usage: blender -b --factory-startup --python scripts/build_hd.py
Outputs: blender/hd.blend, export/HD.fbx, export/HD.glb
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lib import Builder, Face, ROOT, TILE

SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "hd.json"), encoding="utf-8"))
LAYOUT = json.load(open(os.path.join(ROOT, "layout", "campus_layout.json"), encoding="utf-8"))
R = {b["id"]: b["rect"] for b in LAYOUT["buildings"]}
TX0, TY0, TX1, TY1 = R["toa_dieu_hanh"]
LX0, LY0, LX1, LY1 = R["khoi_noi_hd"]
HX0, HY0, HX1, HY1 = R["hoi_truong"]
C = SPEC["colors"]
T = SPEC["tower"]; LV = T["levels"]; NF = T["floors"]


def level(n):
    z = [LV["plinth"], LV["plinth"] + LV["ground_h"], LV["plinth"] + LV["ground_h"] + LV["f2_h"],
         LV["plinth"] + LV["ground_h"] + LV["f2_h"] + LV["f3_h"]]
    return z[n - 1] if n <= 4 else z[3] + (n - 4) * LV["typical_h"]


PL = LV["plinth"]
ROOF = level(NF + 1)
CROWN = ROOF + T["crown_h"]
HH = SPEC["hall"]["height"]
LH = SPEC["link"]["height"]

B = Builder("HD")
paint = TILE.get("paint", 4)
B.material("cream", C["cream"], 0.9, 0, "paint_hd_cream_albedo", "paint_normal", tile=paint)
B.material("cream_dark", C["cream_dark"], 0.9, 0, "paint_hd_cream_dark_albedo", "paint_normal", tile=paint)
B.material("frame", C["grey_frame"], 0.8, 0, "paint_hd_frame_albedo", "paint_normal", tile=paint)
B.material("fin", C["fin"], 0.7, 0.1, "paint_hd_fin_albedo", "paint_normal", tile=paint)
B.material("fin_grey", "#7d8287", 0.7, 0.1, "paint_hd_frame_albedo", "paint_normal", tile=paint)
B.material("glass", "#4f6a77", 0.04, 0.2)
B.material("glass_dark", "#2c3a42", 0.05, 0.15)
B.material("mullion", "#5a5f63", 0.4, 0.6)
B.material("white", "#f2f1ec", 0.6)
B.material("portal", "#1f2124", 0.4, 0.2)
B.material("steps", C["steps"], 0.75, 0, "granite_albedo", "granite_normal", 0.4, tile=TILE.get("granite", 1.5))
B.material("cap", SPEC["tower"]["south"]["entry"]["cap"], 0.6)
B.material("plant", C["plant"], 0.9)
B.material("pot", "#3c5a8a", 0.5)
B.material("ramp", C["ramp"], 0.9, 0, "granite_albedo", "granite_normal", 0.3, tile=TILE.get("granite", 1.5))
B.material("canopy", C["white_panel"], 0.5)
B.material("soffit", "#9ea3a6", 0.7)
B.material("gold", C["gold"], 0.3, 1.0)
B.material("red", C["red_text"], 0.5)
B.material("sign_blue", "#2b5fa8", 0.4)
B.material("opening", "#2f3c4a", 0.9)
B.material("banner", "#2c4f8a", 0.7)
B.material("ac", "#f2f2f0", 0.6)
B.material("roof", "#b4b6b4", 0.95, 0, "roof_albedo", "paint_normal", tile=TILE.get("roof", 6))

SOUTH = Face(B, (TX0, TY0, 0), (1, 0, 0), (0, -1, 0), TX1 - TX0)
EAST = Face(B, (TX1, TY0, 0), (0, 1, 0), (1, 0, 0), TY1 - TY0)
NORTH = Face(B, (TX1, TY1, 0), (-1, 0, 0), (0, 1, 0), TX1 - TX0)
WEST = Face(B, (TX0, TY1, 0), (0, -1, 0), (-1, 0, 0), TY1 - TY0)
L_EAST = Face(B, (LX1, LY0, 0), (0, 1, 0), (1, 0, 0), LY1 - LY0)
H_EAST = Face(B, (HX1, HY0, 0), (0, 1, 0), (1, 0, 0), HY1 - HY0)
H_NORTH = Face(B, (HX1, HY1, 0), (-1, 0, 0), (0, 1, 0), HX1 - HX0)
H_WEST = Face(B, (HX0, HY1, 0), (0, -1, 0), (-1, 0, 0), HY1 - HY0)


def glass_band(f, u0, u1, z0, z1, step=1.2, key="glass", proud=0.02):
    f.box(key, u0, u1, proud - 0.02, proud + 0.02, z0, z1)
    f.box("mullion", u0, u1, proud, proud + 0.07, z0 - 0.06, z0)
    f.box("mullion", u0, u1, proud, proud + 0.07, z1, z1 + 0.06)
    u = u0
    while u <= u1 + 1e-6:
        f.box("mullion", u - 0.03, u + 0.03, proud, proud + 0.07, z0, z1); u += step


def window(f, u0, u1, z0, z1, proud=0.0, frame="white", key="glass_dark", mull=True):
    f.box(key, u0, u1, proud - 0.02, proud + 0.02, z0, z1)
    t = 0.06
    for a, b, c, d in ((u0 - t, u1 + t, z0 - t, z0), (u0 - t, u1 + t, z1, z1 + t), (u0 - t, u0, z0, z1), (u1, u1 + t, z0, z1)):
        f.box(frame, a, b, proud, proud + 0.07, c, d)
    if mull:
        f.box(frame, (u0 + u1) / 2 - 0.025, (u0 + u1) / 2 + 0.025, proud, proud + 0.05, z0, z1)


def text(body, f, u, w, z, h, key, serif=True, extrude=0.03):
    B.text(body, f, u, w, z, h, key, serif=serif, extrude=extrude)


# ================================================================== tower body, roof, crown ring
B.wbox("cream", TX0, TX1, TY0, TY1, 0, ROOF)
B.wbox("roof", TX0 + 0.3, TX1 - 0.3, TY0 + 0.3, TY1 - 0.3, ROOF, ROOF + 0.05)
B.wbox("frame", TX0 + 16, TX0 + 24, TY0 + 8, TY0 + 15, ROOF, ROOF + 3.0)       # lift machine room
for i in range(3):
    B.cylinder("white", TX0 + 28 + i * 2.4, TY0 + 11, ROOF, ROOF + 2.2, 0.95)


def crown(f, u0, u1):
    u = u0
    while u <= u1 + 1e-6:
        f.box("fin", u - 0.12, u + 0.12, -0.6, 0.35, ROOF, CROWN - 0.8); u += 1.0
    f.box("cream", u0, u1, -0.6, 0.45, CROWN - 0.8, CROWN)


# ================================================================== tower – south (main entrance)
F = T["south"]; f = SOUTH
r0, r1 = F["ribbon_zone"]; f0, f1 = F["fin_zone"]; g0, g1 = F["grid_block"]
d = 0.5                                                                     # cladding thickness (ribbon zone reads recessed)
f.box("cream", f0, f1, 0, d, 0, ROOF)
f.box("cream", g0, g1, 0, d, level(5), ROOF + 1.2)
L0_, L1_ = F["lobby"]
f.box("cream", r0, L0_, 0, d, 0, level(3))                                  # podium cladding left of the lobby
f.box("cream", L1_, r1, 0, d, 0, level(3))                                  # ... right of the lobby
f.box("cream", L0_, L1_, 0, d, level(2) + 3.0, level(3))                    # ... above the lobby glazing
for n in range(3, NF + 1):
    glass_band(f, r0 + 0.3, r1 - 0.3, level(n) + 0.9, level(n) + 2.7)
    f.box("cream_dark", r0, r1, 0, 0.25, level(n) - 0.15, level(n) + 0.1)  # slab edge
for n in range(1, NF + 1):                                                  # fin zone windows
    u = f0 + F["fin_step"] / 2
    while u < f1:
        window(f, u - 0.4, u + 0.4, level(n) + 1.0, level(n) + 2.6, proud=d, mull=False); u += F["fin_step"]
u = f0
while u <= f1 + 1e-6:
    f.box("fin", max(f0, u - 0.25), u + 0.25, 0, 1.2, 0, CROWN); u += F["fin_step"]
for n in range(5, NF + 1):                                                  # grid block windows
    u = g0 + 1.0
    while u + 1.6 <= g1 - 0.6:
        window(f, u, u + 1.6, level(n) + 0.9, level(n) + 2.8, proud=d); u += 2.25
f.box("cream", g0, g1, 0, 0.3, 0, level(2) - 0.3)                           # semi-basement base
for uu in (31.5, 34.0, 38.5, 41.0):
    window(f, uu, uu + 1.4, 0.5, 1.1, proud=0.3, mull=False)
for c in F["grid_frame_cols"]:
    f.box("frame", c - 0.5, c + 0.5, 0, 0.9, 0, level(5))
for zb in (level(2), level(3), level(4), level(5)):
    f.box("frame", g0, g1, 0, 0.9, zb - 0.35, zb)
cols = F["grid_frame_cols"]
for a, b in zip(cols[:-1], cols[1:]):
    for n in (2, 3, 4):
        glass_band(f, a + 0.5, b - 0.5, level(n) + 0.05, level(n + 1) - 0.4, 1.4, proud=0.3)
OT = F["office_text"]
text(OT["text"], f, (OT["u0"] + OT["u1"]) / 2, 0.34, level(2) + 2.0, OT["h"], "red", serif=False, extrude=0.01)
crown(f, f0, g0)
# podium windows beside the lobby
for a, b in ((9.4, 13.0), (27.0, 29.6)):
    for n in (1, 2):
        window(f, a, b, level(n) + 1.0, level(n) + 3.0, proud=d)
# lobby + portal
L0, L1 = F["lobby"]
f.box("cream_dark", L0, L1, 0, 0.02, PL, level(3))
glass_band(f, L0, L1, PL, level(2) + 3.0, 1.5, proud=0.05)
P_ = F["portal"]
for a, b, c, e in ((P_["u0"], P_["u0"] + 0.5, PL, PL + P_["h"]), (P_["u1"] - 0.5, P_["u1"], PL, PL + P_["h"]),
                   (P_["u0"], P_["u1"], PL + P_["h"] - 0.5, PL + P_["h"])):
    f.box("portal", a, b, 0, 0.5, c, e)
# canopy (thick box, cantilevered) + 2 dark columns near the facade
Cn = F["canopy"]
f.box("canopy", Cn["u0"], Cn["u1"], 0, Cn["depth"], Cn["z"] + 0.15, Cn["z"] + Cn["thick"])
f.box("soffit", Cn["u0"] + 0.1, Cn["u1"] - 0.1, 0, Cn["depth"] - 0.1, Cn["z"], Cn["z"] + 0.15)
for cu in Cn["columns"]:
    f.box("portal", cu - 0.35, cu + 0.35, 0.6, 1.3, PL, Cn["z"])
# two-tier entrance: tier 1 = vehicle drop-off under the canopy with ramps both sides, tier 2 = door terrace
E = F["entry"]
z1, z2, WH = E["tier1_z"], E["tier2_z"], E["wall_h"]
RP = E["ramps"]
Tr, US, LS, T1 = E["terrace"], E["upper_stair"], E["lower_stair"], E["tier1"]
f.box("steps", Tr["u0"], Tr["u1"], Tr["w0"], Tr["w1"], 0, z2)                       # door terrace (+2.4)
w = Tr["w1"]
h = (z2 - z1) / US["risers"]
for k in range(US["risers"]):                                                         # upper stair down to tier 1
    f.box("steps", US["u0"], US["u1"], w, w + US["tread"], 0, z2 - (k + 1) * h + h); w += US["tread"]
t1_w0 = w
t1_w1 = t1_w0 + T1["depth"]
f.box("ramp", T1["u0"], T1["u1"], 0, t1_w1, 0, z1)                                    # tier 1 platform (+1.2)
for a, b in ((US["u0"] - 1.0, US["u0"]), (US["u1"], US["u1"] + 1.0)):                 # cheek walls of the upper stair
    f.box("cream", a, b, Tr["w1"], t1_w0, z1, z2 + 0.9)
    f.box("cap", a - 0.05, b + 0.05, Tr["w1"], t1_w0, z2 + 0.9, z2 + 1.02)
w = t1_w1
h = z1 / LS["risers"]
for k in range(LS["risers"]):                                                         # lower stair down to the ground
    f.box("steps", LS["u0"], LS["u1"], w, w + LS["tread"], 0, z1 - k * h); w += LS["tread"]
lower_end = w
for a, b in ((T1["u0"], LS["u0"]), (LS["u1"], T1["u1"])):                              # low walls beside the lower stair
    f.box("cream", a, b, t1_w1 - 0.25, t1_w1, 0, z1 + WH)
    f.box("cap", a - 0.05, b + 0.05, t1_w1 - 0.3, t1_w1 + 0.05, z1 + WH, z1 + WH + 0.1)
# curved vehicle ramps both sides: leave tier 1 sideways, then turn 90 degrees OUT towards the plaza
lane = RP["lane_w"]
Rc = RP["len"] / (math.pi / 2)                        # centre-line radius so the arc is RP["len"] long
w_mid = t1_w1 - lane / 2
w_c = w_mid + Rc                                      # turning centre, in front of tier 1
n_seg = RP["segments"]
for u_top, sgn in ((T1["u1"], 1), (T1["u0"], -1)):
    def pt(r, phi):
        return (u_top + sgn * r * math.sin(phi), w_c - r * math.cos(phi))
    for i in range(n_seg):
        pa, pb = (math.pi / 2) * i / n_seg, (math.pi / 2) * (i + 1) / n_seg
        za, zb = max(0.02, z1 * (1 - i / n_seg)), max(0.02, z1 * (1 - (i + 1) / n_seg))
        ri, ro = Rc - lane / 2 + 0.25, Rc + lane / 2 - 0.25
        q = [pt(ri, pa), pt(ro, pa), pt(ri, pb), pt(ro, pb)]
        B.hexa("ramp", [f.P(q[0][0], q[0][1], 0), f.P(q[0][0], q[0][1], za), f.P(q[1][0], q[1][1], 0), f.P(q[1][0], q[1][1], za),
                        f.P(q[2][0], q[2][1], 0), f.P(q[2][0], q[2][1], zb), f.P(q[3][0], q[3][1], 0), f.P(q[3][0], q[3][1], zb)])
        hwa, hwb = za + WH * (1 - 0.3 * i / n_seg), zb + WH * (1 - 0.3 * (i + 1) / n_seg)
        for r0, r1 in ((Rc - lane / 2, Rc - lane / 2 + 0.25), (Rc + lane / 2 - 0.25, Rc + lane / 2)):   # low walls both edges
            a0, a1, b0, b1 = pt(r0, pa), pt(r1, pa), pt(r0, pb), pt(r1, pb)
            B.hexa("cream", [f.P(a0[0], a0[1], 0), f.P(a0[0], a0[1], hwa), f.P(a1[0], a1[1], 0), f.P(a1[0], a1[1], hwa),
                             f.P(b0[0], b0[1], 0), f.P(b0[0], b0[1], hwb), f.P(b1[0], b1[1], 0), f.P(b1[0], b1[1], hwb)])
for uu in F["urns"]:
    p = f.P(uu, 1.0, 0)
    B.cylinder("white", p.x, p.y, z2, z2 + 0.9, 0.28, 12)
terr = t1_w1

# ================================================================== tower – east (with HĐ) and west (same, no sign)
Fe = T["east"]


def frame_face(f, sign):
    tw = f.W
    for c in Fe["frame_cols"]:
        f.box("frame", max(0, c - 0.5), min(tw, c + 0.5), 0, 0.9, 0, level(4))
    for zb in (level(2), level(3), level(4)):
        f.box("frame", 0, tw, 0, 0.9, zb - 0.4, zb)
    fc = Fe["frame_cols"]
    for a, b in zip(fc[:-1], fc[1:]):
        for n in (2, 3):
            glass_band(f, a + 0.5, b - 0.5, level(n) + 0.05, level(n + 1) - 0.45, 1.1, proud=0.3)
        for k in range(2):
            uu = a + 0.9 + k * 1.8
            window(f, uu, uu + 1.0, PL + 0.6, PL + 1.3, proud=0.0, mull=False)
            window(f, uu, uu + 1.0, 0.5, 1.0, proud=0.0, mull=False)                   # semi-basement
    f.box("frame", 0, tw, 0, 0.5, level(4), level(5))
    glass_band(f, 0.6, tw - 0.6, level(4) + 0.8, level(5) - 0.8, 1.6, key="glass_dark", proud=0.52)
    nwin = Fe["windows_per_floor"]; step = tw / nwin
    for n in range(5, NF + 1):
        for i in range(nwin):
            cu = (i + 0.5) * step
            window(f, cu - 0.9, cu + 0.9, level(n) + 0.8, level(n) + 2.8)
    for i in range(nwin + 1):
        f.box("fin", max(0, i * step - 0.2), min(tw, i * step + 0.2), 0, 0.6, level(5), ROOF)
    crown(f, 0, tw)
    if sign:
        HS = Fe["hd_sign"]
        f.box("sign_blue", HS["u"], HS["u"] + HS["w"], 0.9, 0.94, HS["z"], HS["z"] + HS["h"])
        text(HS["text"], f, HS["u"] + HS["w"] / 2, 0.94, HS["z"] + HS["h"] / 2, HS["h"] * 0.6, "white", serif=False, extrude=0.01)


frame_face(EAST, True)
frame_face(WEST, False)

# ================================================================== tower – north (ribbon windows, grey fins at the west end)
f = NORTH
Fn = T["north"]; fz0 = f.W - Fn["fin_zone_from_right"]
f.box("cream", fz0, f.W, 0, d, 0, ROOF)
for n in range(3, NF + 1):
    glass_band(f, 0.4, fz0 - 0.3, level(n) + 0.9, level(n) + 2.7)
for n in (1, 2):
    u = 9.0
    while u + 1.6 < fz0:
        window(f, u, u + 1.6, level(n) + 1.0, level(n) + 2.8); u += 2.6
for n in range(1, NF + 1):
    u = fz0 + 0.75
    while u < f.W:
        window(f, u - 0.4, u + 0.4, level(n) + 1.0, level(n) + 2.6, proud=d, mull=False); u += 1.5
u = fz0
while u <= f.W + 1e-6:
    f.box("fin_grey", u - 0.25, min(f.W, u + 0.25), 0, 1.2, 0, CROWN); u += 1.5
crown(f, 0, f.W)

# ================================================================== link block
B.wbox("cream", LX0, LX1, LY0, LY1, 0, LH)
B.wbox("frame", LX0 - 0.1, LX1 + 0.1, LY0, LY1, LH - 0.5, LH)
Lk = SPEC["link"]; f = L_EAST
v = Lk["vent"]
f.box("frame", v[0], v[1], 0, 0.05, v[2], v[3])
z = v[2] + 0.15
while z < v[3] - 0.1:
    f.box("white", v[0], v[1], 0.05, 0.12, z, z + 0.06); z += 0.25
f.box("white", Lk["door"][0], Lk["door"][1], 0, 0.08, 0, 2.6)
f.box("glass_dark", Lk["door"][0] + 0.2, Lk["door"][1] - 0.2, 0.08, 0.09, 0.4, 2.3)

# ================================================================== hall
B.wbox("cream", HX0, HX1, HY0, HY1, 0, HH)
B.wbox("roof", HX0 + 0.3, HX1 - 0.3, HY0 + 0.3, HY1 - 0.3, HH, HH + 0.05)
B.wbox("frame", HX0 - 0.15, HX1 + 0.15, HY0 - 0.15, HY1 + 0.15, HH - 0.7, HH)          # cornice ring
B.wbox("cream_dark", HX0 - 0.05, HX1 + 0.05, HY0 - 0.05, HY1 + 0.05, 0, 0.35)
Hf = SPEC["hall"]["front"]; f = H_EAST
for pu in Hf["pilasters"]:
    f.box("frame", max(0, pu - 0.6), min(f.W, pu + 0.6), 0, 0.6, 0, HH)
for a, b in ((0.6, 3.4), (14.6, 17.4)):
    glass_band(f, a, b, 3.8, 6.4, 1.4, key="glass_dark")
    glass_band(f, a, b, 7.4, 9.9, 1.4, key="glass_dark")
    f.box("ac", a + 0.3, a + 1.1, 0, 0.35, 1.6, 2.1)
Sh = Hf["stairs"]
f.box("opening", Sh["u0"], Sh["u1"], 0, 0.02, Sh["z_top"], 6.6)
f.box("banner", Sh["u0"] + 1.5, Sh["u1"] - 1.5, 0.02, 0.04, Sh["z_top"] + 0.6, 6.2)
rh = Sh["z_top"] / Sh["risers"]; tr = Sh["depth"] / Sh["risers"]
for k in range(Sh["risers"]):
    f.box("steps", Sh["u0"], Sh["u1"], k * tr, (k + 1) * tr, 0, Sh["z_top"] - k * rh)
for a, b in ((Sh["u0"] - 0.8, Sh["u0"]), (Sh["u1"], Sh["u1"] + 0.8)):
    B.hexa("cream", [f.P(u, ww, z) for u in (a, b) for ww, zt in ((0, Sh["z_top"] + 0.9), (Sh["depth"], 0.9)) for z in (0, zt)])
Cn = Hf["canopy"]
f.box("canopy", Cn["u0"], Cn["u1"], 0, Cn["depth"], Cn["z"], Cn["z"] + 0.5)
for tu in ((Sh["u0"] - 1.3, Sh["u1"] + 0.8) if Hf["canopy"].get("columns", True) else ()):   # steel lattice columns
    for du, dw in ((0, 0), (0.45, 0), (0, 0.45), (0.45, 0.45)):
        a = f.P(tu + du, Cn["depth"] - 0.6 + dw, 0); b = f.P(tu + du, Cn["depth"] - 0.6 + dw, Cn["z"])
        B.tube("mullion", a, b, 0.04, 6)
    zz = 0.0
    while zz < Cn["z"] - 0.6:
        B.tube("mullion", f.P(tu, Cn["depth"] - 0.6, zz), f.P(tu + 0.45, Cn["depth"] - 0.6, zz + 0.6), 0.025, 5)
        B.tube("mullion", f.P(tu, Cn["depth"] - 0.15, zz + 0.6), f.P(tu + 0.45, Cn["depth"] - 0.15, zz), 0.025, 5)
        zz += 0.6
glass_band(f, 4.6, 13.4, 7.5, 10.0, 1.1, key="glass_dark")
P = Hf["pediment"]
mid = (P["u0"] + P["u1"]) / 2
for ww0, ww1, key in ((-1.0, 0.4, "frame"),):
    pts = [(P["u0"], P["z0"]), (P["u0"], P["z0"] + 2.2), (mid, P["apex"]), (P["u1"], P["z0"] + 2.2), (P["u1"], P["z0"])]
    bm = B.bm[key]
    front = [bm.verts.new(f.P(u, ww1, z)) for u, z in pts]
    back = [bm.verts.new(f.P(u, ww0, z)) for u, z in pts]
    bm.faces.new(front); bm.faces.new(back[::-1])
    for i in range(5):
        j = (i + 1) % 5
        bm.faces.new((front[i], back[i], back[j], front[j]))
f.box("white", P["u0"] + 0.5, P["u1"] - 0.5, 0.4, 0.45, P["z0"] + 0.1, P["z0"] + 2.0)
TT = Hf["title_text"]
text(TT["text"], f, mid, 0.45, P["z0"] + 1.05, TT["h"], "gold", serif=True)
# north side: pilasters every 5 m, tall windows, small windows + AC units
Hn = SPEC["hall"]["north"]; f = H_NORTH
n = int(round(f.W / Hn["pilaster_step"]))
for i in range(n):
    a, b = i * Hn["pilaster_step"], (i + 1) * Hn["pilaster_step"]
    if i >= 1:
        glass_band(f, a + 1.3, b - 1.3, 4.0, 8.8, 1.2, key="glass_dark")
    window(f, a + 1.6, a + 2.4, 1.4, 2.0, mull=False)
    if i % 2 == 0:
        f.box("ac", b - 2.4, b - 1.6, 0, 0.35, 1.0, 1.6)
for i in range(n + 1):
    u = i * Hn["pilaster_step"]
    f.box("frame", max(0, u - 0.6), min(f.W, u + 0.6), 0, 0.6, 0, HH)
# west: solid wall with corner pilasters
f = H_WEST
for u in (0.0, f.W):
    f.box("frame", max(0, u - 0.6), min(f.W, u + 0.6), 0, 0.6, 0, HH)

# ================================================================== finish
Cs = T["south"]["canopy"]
colliders = [(TX0, TX1, TY0, TY1, CROWN), (LX0, LX1, LY0, LY1, LH), (HX0, HX1, HY0, HY1, HH),
             (TX0 + T1["u0"], TX0 + T1["u1"], TY0 - terr, TY0, z1),                        # tier 1 drop-off
             (TX0 + Tr["u0"], TX0 + Tr["u1"], TY0 - Tr["w1"], TY0, z2)]                     # door terrace
B.finish((TX0, TY0, HX1, HY1), CROWN, "HD", colliders=colliders)
