"""Export a combined GLB of finished buildings, kept at their campus positions.
Usage: blender -b --factory-startup --python scripts/export_combo.py -- ta1 tb2   ("gate" loads ../cong-truong/blender/kma_gate.blend)"""
import bpy, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ids = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["ta1", "tb2"]
bpy.ops.wm.read_homefile(use_empty=True)
for bid in ids:
    if bid == "gate":                                                  # gate model lives in the parent kma-gate project
        with bpy.data.libraries.load(os.path.join(os.path.dirname(ROOT), "cong-truong", "blender", "kma_gate.blend")) as (src, dst):
            dst.collections = ["KMA_Gate"]
        for c in dst.collections:
            for ob in c.all_objects:
                bpy.context.scene.collection.objects.link(ob)
        continue
    path = os.path.join(ROOT, "blender", f"{bid}.blend")
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [n for n in src.objects if n == bid.upper()]
    for ob in dst.objects:
        bpy.context.scene.collection.objects.link(ob)
for ob in bpy.context.scene.objects:
    ob.select_set(True)
out = os.path.join(ROOT, "export", "campus_" + "_".join(ids) + ".glb")
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_image_format="JPEG", export_jpeg_quality=85)
print("COMBO", out, [o.name for o in bpy.context.scene.objects])
