import bpy, os, time, sys
t = time.time()
bpy.ops.wm.read_homefile(use_empty=True)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(ROOT, "scripts", "build_kma_gate.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "blender", "kma_gate.blend"))
print("BUILD OK in %.1fs" % (time.time() - t))
