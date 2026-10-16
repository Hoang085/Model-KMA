"""B4 – round fountain in front of TA1 (photo reference/gate_fountain/bon_nuoc.png), position from layout/campus_layout.json.
Usage: blender -b --factory-startup --python scripts/build_fountain.py
Outputs: blender/fountain.blend, export/FOUNTAIN.fbx, export/FOUNTAIN.glb
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lib import Builder, ROOT, TILE
from mathutils import Vector

L = json.load(open(os.path.join(ROOT, "layout", "campus_layout.json"), encoding="utf-8"))
F = next(f for f in L["features"] if f["id"] == "bon_nuoc")
CX, CY = F["center"]
R = F["radius"]
BASE_H, RIM_T, RIM_W, WATER_Z = 0.5, 0.15, 0.38, 0.32

B = Builder("FOUNTAIN")
B.material("stone", "#8c8a84", 0.8, 0, "granite_albedo", "granite_normal", 0.5, tile=TILE.get("granite", 1.5))
B.material("rim", "#f1f0ec", 0.4)
B.material("tile", "#e9eef0", 0.3)
B.material("water", "#5f6b3a", 0.05, 0.0)
B.material("pipe", "#9a9c9e", 0.4, 0.8)
m = B.mat["water"]                                                         # murky, slightly see-through water
next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"].default_value = 0.85
for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
    if hasattr(m, attr):
        try:
            setattr(m, attr, val)
        except TypeError:
            pass

SEG = 48


def ring(key, r0, r1, z0, z1):
    for i in range(SEG):
        a0, a1 = 2 * math.pi * i / SEG, 2 * math.pi * (i + 1) / SEG
        pts = [(CX + r * math.cos(a), CY + r * math.sin(a), z) for a in (a0, a1) for r in (r0, r1) for z in (z0, z1)]
        B.hexa(key, [Vector(p) for p in pts])


ring("stone", R - RIM_W + 0.05, R - 0.1, 0, BASE_H)                       # grey stone drum
ring("rim", R - RIM_W, R, BASE_H, BASE_H + RIM_T)                          # wide white rim, overhangs the drum
ring("tile", R - RIM_W, R - RIM_W + 0.06, 0.05, BASE_H)                    # tiled inner face
B.cylinder("tile", CX, CY, 0.0, 0.05, R - RIM_W + 0.06, SEG)               # basin floor
B.cylinder("water", CX, CY, 0.05, WATER_Z, R - RIM_W, SEG)
# nozzles: a ring pipe with 8 jets and a small centre cluster (fountain switched off, as in the photo)
rr = 1.05
for i in range(16):
    a0, a1 = 2 * math.pi * i / 16, 2 * math.pi * (i + 1) / 16
    B.tube("pipe", (CX + rr * math.cos(a0), CY + rr * math.sin(a0), WATER_Z + 0.03), (CX + rr * math.cos(a1), CY + rr * math.sin(a1), WATER_Z + 0.03), 0.025, 6)
for i in range(8):
    a = 2 * math.pi * i / 8
    B.cylinder("pipe", CX + rr * math.cos(a), CY + rr * math.sin(a), WATER_Z, WATER_Z + 0.12, 0.05, 8)
for dx, dy in ((0, 0), (0.25, 0), (-0.25, 0), (0, 0.25), (0, -0.25)):
    B.cylinder("pipe", CX + dx, CY + dy, WATER_Z, WATER_Z + 0.15, 0.04, 8)

B.finish((CX - R, CY - R, CX + R, CY + R), BASE_H + RIM_T, "FOUNTAIN", [(CX - R, CX + R, CY - R, CY + R, BASE_H + RIM_T)])
