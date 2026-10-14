"""Render preview shots of the gate (closed + open gates). Usage: blender -b kma_gate.blend --python render_preview.py"""
import bpy, os, math, sys
from mathutils import Vector

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "preview")
open_gates = "--open" in sys.argv
sc = bpy.context.scene
try:
    sc.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError:
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError as e:
        print(e)
sc.render.resolution_x, sc.render.resolution_y = 1280, 800
sc.render.film_transparent = False
world = sc.world or bpy.data.worlds.new("World")
sc.world = world
if world.node_tree is None:
    world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.55, 0.68, 0.85, 1); bg.inputs[1].default_value = 0.9
try:
    sc.view_settings.view_transform = "AgX"
except TypeError:
    pass

if open_gates:
    for ob in bpy.data.objects:
        if ob.name.startswith("KMA_Gate_") and ob.type == "MESH":
            ob.rotation_euler.z = math.radians(80 if ob.name.endswith("_Left") else -80)

cam_data = bpy.data.cameras.new("PreviewCam"); cam_data.lens = 28
cam = bpy.data.objects.new("PreviewCam", cam_data); sc.collection.objects.link(cam); sc.camera = cam

def shoot(name, loc, target):
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{OUT}/{name}{'_open' if open_gates else ''}.png"
    bpy.ops.render.render(write_still=True)

shoot("front", (0, -24, 4.0), (-2, 0, 3.0))
shoot("three_quarter", (14, -18, 7), (-2, 0, 2.5))
shoot("inside", (4, 22, 4.5), (-2, 0, 3.0))
shoot("gate_close", (2.5, -8, 2.2), (0, -1.6, 2.4))
