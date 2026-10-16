"""B4 – build the tennis court (surface, lines, net, fence, lights, shade + benches) from layout/buildings/canteen.json.
Usage: blender -b --factory-startup --python scripts/build_tennis.py
Outputs: blender/tennis.blend, export/TENNIS.fbx, export/TENNIS.glb
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lib import Builder, ROOT

SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "canteen.json"), encoding="utf-8"))
C, T = SPEC["colors"], SPEC["tennis"]
X0, Y0, X1, Y1 = T["rect"]
CX, CY = (X0 + X1) / 2, (Y0 + Y1) / 2
L, WD = T["court"]
SW = T["singles_w"]
SV = T["service_from_net"]
FH, CH = T["fence_h"], T["curb_h"]

B = Builder("TENNIS")
B.material("surround", C["surround"], 0.85)
B.material("court", C["court"], 0.85)
B.material("line", C["line"], 0.7)
B.material("curb", C["curb"], 0.8)
B.material("post", C["fence"], 0.5, 0.6)
B.material("mesh", C["mesh"], 0.6, 0.5)
B.material("net", "#1d1f20", 0.8)
B.material("lamp", "#f4c542", 0.4)
B.material("shade", C["shade"], 0.4, 0.6)
B.material("bench", C["bench"], 0.5)
for key, alpha in (("mesh", 0.35), ("net", 0.6)):                         # see-through chain-link and net
    m = B.mat[key]
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Alpha"].default_value = alpha
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        if hasattr(m, attr):
            try:
                setattr(m, attr, val)
            except TypeError:
                pass

# ------------------------------------------------------------------ surface + lines
B.wbox("surround", X0, X1, Y0, Y1, 0, 0.06)
B.wbox("court", CX - L / 2, CX + L / 2, CY - WD / 2, CY + WD / 2, 0.06, 0.07)
lw = 0.05
for yy in (CY - WD / 2, CY + WD / 2, CY - SW / 2, CY + SW / 2):
    B.wbox("line", CX - L / 2, CX + L / 2, yy - lw / 2, yy + lw / 2, 0.07, 0.075)
for xx in (CX - L / 2, CX + L / 2):
    B.wbox("line", xx - lw / 2, xx + lw / 2, CY - WD / 2, CY + WD / 2, 0.07, 0.075)
for xx in (CX - SV, CX + SV):
    B.wbox("line", xx - lw / 2, xx + lw / 2, CY - SW / 2, CY + SW / 2, 0.07, 0.075)
B.wbox("line", CX - SV, CX + SV, CY - lw / 2, CY + lw / 2, 0.07, 0.075)
for xx in (CX - L / 2, CX + L / 2):                                         # centre marks
    B.wbox("line", xx - 0.15 if xx > CX else xx, xx if xx > CX else xx + 0.15, CY - lw / 2, CY + lw / 2, 0.07, 0.075)
# net + posts
ny0, ny1 = CY - WD / 2 - 0.9, CY + WD / 2 + 0.9
B.wbox("net", CX - 0.01, CX + 0.01, ny0, ny1, 0.15, 0.95)
B.wbox("line", CX - 0.03, CX + 0.03, ny0, ny1, 0.91, 0.97)
for yy in (ny0, ny1):
    B.tube("post", (CX, yy, 0.06), (CX, yy, 1.07), 0.04, 8)

# ------------------------------------------------------------------ curb + fence
t = 0.25
B.wbox("curb", X0, X1, Y0, Y0 + t, 0, CH)
B.wbox("curb", X0, X1, Y1 - t, Y1, 0, CH)
B.wbox("curb", X0, X0 + t, Y0, Y1, 0, CH)
B.wbox("curb", X1 - t, X1, Y0, Y1, 0, CH)
g0, g1 = Y0 + T["gate"]["v0"], Y0 + T["gate"]["v1"]
mx = 0.125                                                                   # fence line sits on the curb centre
sides = [((X0, Y0 + mx), (X1, Y0 + mx)), ((X0, Y1 - mx), (X1, Y1 - mx)), ((X1 - mx, Y0), (X1 - mx, Y1)),
         ((X0 + mx, Y0), (X0 + mx, g0)), ((X0 + mx, g1), (X0 + mx, Y1))]
for (ax, ay), (bx, by) in sides:
    length = abs(bx - ax) + abs(by - ay)
    n = max(1, round(length / T["post_step"]))
    for i in range(n + 1):
        px, py = ax + (bx - ax) * i / n, ay + (by - ay) * i / n
        B.tube("post", (px, py, CH), (px, py, FH), 0.045, 8)
    for z in (CH + 1.2, FH - 0.03):
        B.tube("post", (ax, ay, z), (bx, by, z), 0.03, 6)
    if ax == bx:
        B.wbox("mesh", ax - 0.01, ax + 0.01, min(ay, by), max(ay, by), CH, FH)
    else:
        B.wbox("mesh", min(ax, bx), max(ax, bx), ay - 0.01, ay + 0.01, CH, FH)
B.tube("post", (X0 + mx, g0, FH), (X0 + mx, g1, FH), 0.03, 6)                  # gate lintel

# ------------------------------------------------------------------ floodlights, shade, benches
for lx, ly in T["lights"]:
    ix = lx + (mx if lx == X0 else -mx); iy = ly + (mx if ly == Y0 else -mx)
    B.tube("post", (ix, iy, 0), (ix, iy, T["light_h"]), 0.07, 8)
    B.wbox("lamp", ix - 0.35, ix + 0.35, iy - 0.2, iy + 0.2, T["light_h"] - 0.3, T["light_h"])
sr = T["shade"]["rect"]; sh = T["shade"]["h"]
for px in (sr[0] + 0.1, sr[2] - 0.1):
    for py in (sr[1] + 0.1, sr[3] - 0.1):
        B.tube("post", (px, py, 0.06), (px, py, sh), 0.04, 6)
B.wbox("shade", sr[0] - 0.2, sr[2] + 0.2, sr[1] - 0.2, sr[3] + 0.2, sh, sh + 0.06)
for bx, by in T["benches"]:
    B.wbox("bench", bx - 0.8, bx + 0.8, by - 0.22, by + 0.22, 0.42, 0.47)
    B.wbox("bench", bx - 0.8, bx + 0.8, by - 0.25, by - 0.2, 0.47, 0.85)
    for lx in (bx - 0.7, bx + 0.7):
        B.wbox("post", lx - 0.03, lx + 0.03, by - 0.2, by + 0.2, 0.06, 0.42)

COLLIDERS = [(X0, X1, Y0, Y0 + t, FH), (X0, X1, Y1 - t, Y1, FH), (X1 - t, X1, Y0, Y1, FH),
             (X0, X0 + t, Y0, g0, FH), (X0, X0 + t, g1, Y1, FH)]
B.finish((X0, Y0, X1, Y1), T["light_h"], "TENNIS", COLLIDERS)
