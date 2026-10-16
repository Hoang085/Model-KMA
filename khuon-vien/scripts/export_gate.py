"""Export the gate model (cong-truong/blender/kma_gate.blend, collection KMA_Gate) as GLB for the campus web viewer.
Usage: blender -b ../cong-truong/blender/kma_gate.blend --python scripts/export_gate.py
Output: export/GATE.glb (gate, guardhouse, barriers, boundary wall; gate leaves stay separate objects)."""
import bpy, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
col = bpy.data.collections["KMA_Gate"]
for ob in bpy.context.view_layer.objects:
    ob.select_set(ob.name in col.all_objects)
out = os.path.join(ROOT, "export", "GATE.glb")
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_image_format="JPEG", export_jpeg_quality=85)
print("GATE GLB", out)
