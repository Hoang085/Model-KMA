"""Render review shots of the gate area: gate + guardhouse + barriers + boundary wall + fountain (TA1, TB2 as context).
Usage: blender -b --factory-startup --python scripts/render_gate_area.py
Outputs in 02_toa_nha/cong_tuong/."""
import bpy, math, os
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "02_toa_nha", "cong_tuong")
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene

with bpy.data.libraries.load(os.path.join(os.path.dirname(ROOT), "cong-truong", "blender", "kma_gate.blend")) as (src, dst):
    dst.collections = ["KMA_Gate"]
for c in dst.collections:
    sc.collection.children.link(c)
for bid in ("fountain", "ta1", "tb2", "ta23", "nha_an"):
    with bpy.data.libraries.load(os.path.join(ROOT, "blender", f"{bid}.blend")) as (src, dst):
        dst.objects = [n for n in src.objects if n == bid.upper()]
    for ob in dst.objects:
        sc.collection.objects.link(ob)

for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng; break
    except TypeError:
        pass
try:
    sc.view_settings.view_transform = "AgX"
except TypeError:
    pass
world = bpy.data.worlds.new("W"); sc.world = world
if world.node_tree is None:
    world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.62, 0.72, 0.86, 1); bg.inputs[1].default_value = 1.0
me = bpy.data.meshes.new("Ground")
me.from_pydata([(-300, -300, 0), (300, -300, 0), (300, 300, 0), (-300, 300, 0)], [], [(0, 1, 2, 3)])
g = bpy.data.objects.new("Ground", me); sc.collection.objects.link(g)
gm = bpy.data.materials.new("Ground")
if gm.node_tree is None:
    gm.use_nodes = True
next(n for n in gm.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.32, 0.31, 0.29, 1)
me.materials.append(gm)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 4.0; sun.rotation_euler = (math.radians(52), 0, math.radians(35))
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_end = 3000


def shoot(name, loc, tgt, lens, res=(1600, 1000)):
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    return sc.render.filepath


def load(path):
    im = bpy.data.images.load(path)
    return np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)


def side(photo, render, out):
    arrs = [load(photo), load(render)]
    h = min(a.shape[0] for a in arrs)
    res = []
    for a in arrs:
        ys = (np.arange(h) * a.shape[0] / h).astype(int); w = int(a.shape[1] * h / a.shape[0])
        res.append(a[ys][:, (np.arange(w) * a.shape[1] / w).astype(int)])
    c = np.concatenate([res[0], np.ones((h, 24, 4), dtype=np.float32), res[1]], axis=1)
    img = bpy.data.images.new("cmp", c.shape[1], c.shape[0], alpha=False)
    img.pixels = c.ravel(); img.filepath_raw = out; img.file_format = "PNG"; img.save()


r = shoot("_nbv", (-1.0, 13.0, 1.6), (-9.5, 2.5, 2.6), 14, (1280, 960))
side(os.path.join(ROOT, "reference/gate_fountain/nha_bao_ve_trong_truong.png"), r, os.path.join(OUT, "so_sanh_anh_nha_bao_ve.png")); os.remove(r)
r = shoot("_bn", (3.4, 18.2, 1.5), (5.5, 40.0, 3.5), 14, (1280, 960))
side(os.path.join(ROOT, "reference/gate_fountain/bon_nuoc.png"), r, os.path.join(OUT, "so_sanh_anh_bon_nuoc.png")); os.remove(r)
shoot("cong_tu_ngoai_duong", (6.0, -24.0, 1.7), (-1.0, 0.0, 3.0), 20)
shoot("nha_bao_ve_can_canh", (-1.5, 9.0, 2.0), (-9.0, 3.0, 2.2), 24)
shoot("tuong_bao_quanh_tren_cao", (130.0, -110.0, 170.0), (10.0, 100.0, 0.0), 24)
print("RENDER GATE DONE")
