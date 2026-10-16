"""Render TA1 review shots. Usage: blender -b blender/ta1.blend --python scripts/render_ta1.py
Outputs in 02_toa_nha/ta1/3d/: elevation renders (ortho), perspectives, photo-matched shots, compare sheets."""
import bpy, json, math, os
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "02_toa_nha", "ta1", "3d")
os.makedirs(OUT, exist_ok=True)
L = json.load(open(os.path.join(ROOT, "layout", "campus_layout.json"), encoding="utf-8"))
X0, Y0, X1, Y1 = next(b["rect"] for b in L["buildings"] if b["id"] == "ta1")
CX, CY = (X0 + X1) / 2, (Y0 + Y1) / 2
H = 40.0

sc = bpy.context.scene
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
try:                                                   # physical sky if this Blender has it
    sky = world.node_tree.nodes.new("ShaderNodeTexSky")
    types = [i.identifier for i in sky.bl_rna.properties["sky_type"].enum_items]
    sky.sky_type = next((t for t in types if t not in ("PREETHAM", "HOSEK_WILKIE")), types[0])
    for attr, val in (("sun_elevation", 0.75), ("sun_rotation", 2.4), ("sun_intensity", 0.4)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    world.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs[1].default_value = 0.35
except Exception as e:
    print("sky fallback:", e)

# ground + sun
me = bpy.data.meshes.new("Ground")
me.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 250, 0), (-200, 250, 0)], [], [(0, 1, 2, 3)])
g = bpy.data.objects.new("Ground", me); sc.collection.objects.link(g)
gm = bpy.data.materials.new("Ground"); gm.diffuse_color = (0.45, 0.44, 0.42, 1)
if gm.node_tree is None:
    gm.use_nodes = True
next(n for n in gm.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.32, 0.31, 0.29, 1)
me.materials.append(gm)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 4.0; sun.rotation_euler = (math.radians(52), 0, math.radians(35))
# 1.7 m person for scale
bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=1.45, location=(X1 + 4, CY, 0.72))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(X1 + 4, CY, 1.58))

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam


def aim(loc, target):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def shoot(name, res):
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    return sc.render.filepath


# orthographic elevations, each framed like the 2D drawing (left = viewer's left)
cam.data.type = "ORTHO"
elev = {
    "north": ((CX, Y1 + 60, H / 2), (CX, CY, H / 2), X1 - X0),
    "east": ((X1 + 60, CY, H / 2), (CX, CY, H / 2), Y1 - Y0),
    "south": ((CX, Y0 - 60, H / 2), (CX, CY, H / 2), X1 - X0),
    "west": ((X0 - 60, CY, H / 2), (CX, CY, H / 2), Y1 - Y0),
}
for k, (loc, tgt, wid) in elev.items():
    aim(loc, tgt)
    cam.data.ortho_scale = max(wid + 10, H + 6)
    shoot(f"3d_mat_{k}", (1000, 1000))

# perspectives
cam.data.type = "PERSP"; cam.data.lens = 24
aim((X1 + 38, Y1 + 34, 12), (CX, CY, 15)); shoot("phoi_canh_bac_dong", (1600, 1000))
aim((X1 + 30, Y0 - 32, 8), (CX, CY, 14)); shoot("phoi_canh_dong_nam", (1600, 1000))
aim((X0 - 30, Y1 + 30, 30), (CX, CY, 14)); shoot("phoi_canh_tren_cao", (1600, 1000))
# photo-matched (portrait, low wide angle like the phone photos)
cam.data.lens = 15
aim((X0 + 6, Y1 + 24, 1.5), (CX - 2, CY, 16)); shoot("goc_anh_sanh_chinh", (960, 1280))
aim((X1 + 22, Y0 + 6, 1.5), (X1, CY - 3, 16)); shoot("goc_anh_giap_cong", (960, 1280))


def load(path):
    im = bpy.data.images.load(path)
    a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)
    return a


def resize_nn(a, h):
    ys = (np.arange(h) * a.shape[0] / h).astype(int)
    w = int(a.shape[1] * h / a.shape[0])
    xs = (np.arange(w) * a.shape[1] / w).astype(int)
    return a[ys][:, xs]


def side(paths, out):
    arrs = [load(p) for p in paths]
    h = min(a.shape[0] for a in arrs)
    arrs = [resize_nn(a, h) for a in arrs]
    gap = np.ones((h, 24, 4), dtype=np.float32)
    parts = []
    for i, a in enumerate(arrs):
        parts += ([gap] if i else []) + [a]
    c = np.concatenate(parts, axis=1)
    img = bpy.data.images.new("cmp", c.shape[1], c.shape[0], alpha=False)
    img.pixels = c.ravel(); img.filepath_raw = out; img.file_format = "PNG"; img.save()


# drawing (2D, images are top-down in PIL; Blender pixels are bottom-up, load() handles both the same way)
D2 = os.path.join(ROOT, "02_toa_nha", "ta1")
for k, name in (("north", "bac"), ("east", "dong"), ("south", "nam"), ("west", "tay")):
    side([os.path.join(D2, f"mat_dung_{name}.png"), os.path.join(OUT, f"3d_mat_{k}.png")], os.path.join(OUT, f"so_sanh_2d_3d_{name}.png"))
side([os.path.join(ROOT, "reference", "ta1", "ta1_mat_sanh_chinh.png"), os.path.join(OUT, "goc_anh_sanh_chinh.png")],
     os.path.join(OUT, "so_sanh_anh_sanh_chinh.png"))
side([os.path.join(ROOT, "reference", "ta1", "ta1_mat_giap_cong.png"), os.path.join(OUT, "goc_anh_giap_cong.png")],
     os.path.join(OUT, "so_sanh_anh_giap_cong.png"))
print("RENDER DONE")
