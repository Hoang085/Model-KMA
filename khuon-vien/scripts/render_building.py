"""Render review shots for one building. Usage:
  blender -b blender/<id>.blend --python scripts/render_building.py -- <id>
Outputs in 02_toa_nha/<id>/3d/: ortho elevations, perspectives, photo-matched shots and compare sheets."""
import bpy, json, math, os, sys
import numpy as np
from mathutils import Vector

BID = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "tb2"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "02_toa_nha", BID, "3d")
os.makedirs(OUT, exist_ok=True)
L = json.load(open(os.path.join(ROOT, "layout", "campus_layout.json"), encoding="utf-8"))
RECT_OVERRIDE = {"hd": (-34.4, 99.1, 10.9, 147.0), "ta23": (-60.6, 15.7, -44.6, 108.6), "canteen": (47.1, 103.7, 78.0, 118.0), "ta4": (37.4, 134.1, 77.1, 153.7), "sports": (-12.0, 154.3, 80.9, 227.1)}  # TA4 incl. stair tower + curved bay                     # whole complex: tower + link + hall
X0, Y0, X1, Y1 = RECT_OVERRIDE.get(BID) or next(b["rect"] for b in L["buildings"] if b["id"] == BID)
CX, CY = (X0 + X1) / 2, (Y0 + Y1) / 2

# per-building framing: height, perspective cameras, photo-matched cameras (photo, cam, target, lens)
SHOTS = {
    "tb2": {
        "H": 73.0,
        "persp": [("phoi_canh_tay_bac", (X0 - 45, Y1 + 45, 18), (CX, CY, 30)),
                  ("phoi_canh_dong_nam", (X1 + 45, Y0 - 45, 12), (CX, CY, 30)),
                  ("phoi_canh_tren_cao", (X0 - 50, Y0 - 50, 95), (CX, CY, 25))],
        "photos": [("so_sanh_anh_sanh_chinh", "reference/tb2/tb2_mat_bac_sanh.png", (X0 + 4, Y1 + 30, 1.5), (X0 + 16, Y1 - 2, 32), 15),
                   ("so_sanh_anh_bon_nuoc", "reference/tb2/tb2_mat_tay_bon_nuoc.png", (-16.0, 14.0, 1.5), (X0, CY - 1, 32), 15)],
    },
    "hd": {
        "H": 59.0,
        "persp": [("phoi_canh_tay_nam", (X0 - 40, Y0 - 45, 14), (CX, CY - 8, 22)),
                  ("phoi_canh_dong_bac", (X1 + 50, Y1 + 30, 14), (CX, CY, 18)),
                  ("phoi_canh_tren_cao", (X1 + 60, Y0 - 60, 85), (CX, CY, 15))],
        "photos": [("so_sanh_anh_sanh_chinh", "reference/hd/hd_mat_dong_sanh.png", (-26.0, 72.0, 1.5), (-12.0, 99.1, 26), 15),
                   ("so_sanh_anh_mat_dong", "reference/hoi_truong/hd_va_hoi_truong_mat_dong.png", (38.0, 122.0, 1.5), (9.0, 125.0, 16), 15),
                   ("so_sanh_anh_hoi_truong_ben", "reference/hoi_truong/hoi_truong_mat_ben.png", (24.0, 160.0, 1.5), (0.0, 147.0, 7), 15)],
        "drawings": {"north": "thap_mat_bac", "east": "mat_dong_ca_cum", "south": "thap_mat_nam", "west": "thap_mat_tay"},
    },
    "ta23": {
        "H": 28.0,
        "persp": [("phoi_canh_dong_nam", (X1 + 45, Y0 - 20, 14), (CX, CY - 10, 10)),
                  ("phoi_canh_dong_bac", (X1 + 40, Y1 + 30, 16), (CX, CY + 20, 12)),
                  ("phoi_canh_tren_cao", (X1 + 70, Y0 - 30, 70), (CX, CY, 5))],
        "photos": [("so_sanh_anh_ta3", "reference/ta2_ta3/ta3_mat_dong_tu_san_hd.png", (-10.0, 93.0, 1.5), (-44.6, 92.0, 11.0), 14, (1280, 960)),
                   ("so_sanh_anh_ta2", "reference/ta2_ta3/ta2_mat_dong_san_ghe.png", (-27.0, 52.0, 1.5), (-48.6, 56.0, 7.0), 14, (1280, 960))],
    },
    "sports": {
        "H": 16.0,
        "context": [],
        "persp": [("phoi_canh_tay_nam", (X0 - 10, Y0 - 25, 25), (CX, CY, 0)),
                  ("phoi_canh_khan_dai", (45.0, 172.0, 1.7), (44.0, 220.0, 3.0)),
                  ("phoi_canh_tu_khan_dai", (44.0, 220.0, 4.5), (44.0, 185.0, 0.0)),
                  ("phoi_canh_bong_ro_chuyen", (22.0, 165.0, 6.0), (-2.0, 190.0, 1.0)),
                  ("phoi_canh_tren_cao", (CX, CY - 60, 90), (CX, CY, 0))],
        "photos": [],
    },
    "ta4": {
        "H": 26.0,
        "persp": [("phoi_canh_tay_nam", (X0 - 25, Y0 - 30, 8), (CX, CY, 10)),
                  ("phoi_canh_dong_nam", (X1 + 15, Y0 - 35, 10), (CX, CY, 10)),
                  ("phoi_canh_tren_cao", (X0 - 30, Y0 - 50, 55), (CX, CY, 5))],
        "photos": [("so_sanh_anh_mat_nam", "reference/ta4/ta4_mat_nam.png", (40.0, 113.0, 1.5), (56.0, 142.0, 10.0), 16, (1280, 960))],
    },
    "canteen": {
        "H": 16.0,
        "context": ["tennis", "nha_an"],
        "persp": [("phoi_canh_tay_nam", (X0 - 25, Y0 - 25, 7), (CX, CY, 6)),
                  ("phoi_canh_dong_bac", (X1 + 15, Y1 + 30, 9), (CX, CY, 6)),
                  ("phoi_canh_tren_cao", (X0 - 35, Y0 - 45, 40), (CX, CY - 12, 0))],
        "photos": [("so_sanh_anh_canteen", "reference/canteen_tennis/canteen_nhin_bac.png", (31.0, 95.5, 1.5), (55.0, 114.0, 7.0), 14, (1280, 960)),
                   ("so_sanh_anh_san_tennis", "reference/canteen_tennis/san_tennis_nhin_dong.png", (31.0, 93.0, 1.5), (60.0, 84.0, 4.0), 14, (1280, 960))],
    },
    "nha_an": {
        "H": 14.0,
        "persp": [("phoi_canh_tay_nam", (X0 - 25, Y0 - 25, 6), (CX, CY - 6, 4)),
                  ("phoi_canh_dong_bac", (X1 + 25, Y1 + 25, 8), (CX, CY, 4)),
                  ("phoi_canh_tren_cao", (X0 - 35, Y0 - 35, 40), (CX, CY, 2))],
        "photos": [("so_sanh_anh_sanh_chinh", "reference/nha_an/nha_an_mat_sanh.png", (54.0, 24.0, 1.5), (54.0, 40.0, 6.0), 14, (1280, 960)),
                   ("so_sanh_anh_tb3", "reference/nha_an/nha_an_mat_tb3.png", (24.0, 40.0, 1.5), (42.4, 49.0, 6.0), 15)],
    },
}
CFG = SHOTS[BID]
H = CFG["H"]

sc = bpy.context.scene
CTX_OBJS = []
for ctx in CFG.get("context", []):                                      # neighbouring models for photo-matched shots
    with bpy.data.libraries.load(os.path.join(ROOT, "blender", f"{ctx}.blend")) as (src, dst):
        dst.objects = [n for n in src.objects if n == ctx.upper()]
    for ob in dst.objects:
        sc.collection.objects.link(ob); ob.hide_render = True; CTX_OBJS.append(ob)   # shown only in photo shots
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng; break
    except TypeError:
        pass
try:
    sc.view_settings.view_transform = "AgX"
except TypeError:
    pass
sc.render.film_transparent = False
world = bpy.data.worlds.new("W"); sc.world = world
if world.node_tree is None:
    world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.62, 0.72, 0.86, 1); bg.inputs[1].default_value = 1.0
try:
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

me = bpy.data.meshes.new("Ground")
me.from_pydata([(-250, -250, 0), (250, -250, 0), (250, 300, 0), (-250, 300, 0)], [], [(0, 1, 2, 3)])
g = bpy.data.objects.new("Ground", me); sc.collection.objects.link(g)
gm = bpy.data.materials.new("Ground")
if gm.node_tree is None:
    gm.use_nodes = True
next(n for n in gm.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.32, 0.31, 0.29, 1)
me.materials.append(gm)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 4.0; sun.rotation_euler = (math.radians(52), 0, math.radians(35))
bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=1.45, location=(X0 - 4, CY, 0.72))      # 1.7 m person
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(X0 - 4, CY, 1.58))
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_end = 2000


def aim(loc, target):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def shoot(name, res):
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    return sc.render.filepath


cam.data.type = "ORTHO"
elev = {"north": ((CX, Y1 + 90, H / 2), X1 - X0), "east": ((X1 + 90, CY, H / 2), Y1 - Y0),
        "south": ((CX, Y0 - 90, H / 2), X1 - X0), "west": ((X0 - 90, CY, H / 2), Y1 - Y0)}
for k, (loc, wid) in elev.items():
    aim(loc, (CX, CY, H / 2))
    cam.data.ortho_scale = max(wid + 10, H + 6)
    shoot(f"3d_mat_{k}", (1000, 1000))

cam.data.type = "PERSP"; cam.data.lens = 24
for name, loc, tgt in CFG["persp"]:
    aim(loc, tgt); shoot(name, (1600, 1000))


def load(path):
    im = bpy.data.images.load(path)
    return np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)


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


for ob in CTX_OBJS:
    ob.hide_render = False
for name, photo, loc, tgt, lens, *res in CFG["photos"]:
    if not os.path.exists(os.path.join(ROOT, photo)):                   # reference photos are not shipped in the repo
        print("skip photo shot (missing):", photo); continue
    cam.data.lens = lens
    aim(loc, tgt)
    r = shoot("_" + name, res[0] if res else (960, 1280))
    side([os.path.join(ROOT, photo), r], os.path.join(OUT, name + ".png"))
    os.remove(r)

D2 = os.path.join(ROOT, "02_toa_nha", BID)
VN = {"north": "bac", "east": "dong", "south": "nam", "west": "tay"}
for k, name in VN.items():
    p2 = os.path.join(D2, CFG["drawings"][k] + ".png") if "drawings" in CFG else os.path.join(D2, f"mat_dung_{name}.png")
    if os.path.exists(p2):
        side([p2, os.path.join(OUT, f"3d_mat_{k}.png")], os.path.join(OUT, f"so_sanh_2d_3d_{name}.png"))
print("RENDER DONE")
