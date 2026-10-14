"""Export the KMA_Gate collection to FBX for Unity (Y-up, transforms baked, hinge pivots kept)."""
import bpy, os
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "export", "KMA_Gate.fbx")
col = bpy.data.collections["KMA_Gate"]
for ob in bpy.context.view_layer.objects:
    ob.select_set(ob.name in col.all_objects)
bpy.ops.export_scene.fbx(
    filepath=OUT, use_selection=True, object_types={"EMPTY", "MESH"},
    apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
    axis_forward="-Z", axis_up="Y", bake_space_transform=True,
    mesh_smooth_type="FACE", use_mesh_modifiers=True, add_leaf_bones=False,
    bake_anim=False, path_mode="AUTO",
)
print("EXPORTED", OUT)
