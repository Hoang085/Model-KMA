"""Shared Blender helpers for the campus building scripts (B4).
World coords = campus plan coords (metres): origin at the main gate, +Y into the campus, Z up.
"""
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "textures")
TILE = json.load(open(os.path.join(TEX, "tile_sizes.json"))) if os.path.exists(os.path.join(TEX, "tile_sizes.json")) else {}
FONT_SERIF = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
FONT_SANS = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


class Builder:
    def __init__(self, prefix):
        bpy.ops.wm.read_homefile(use_empty=True)
        self.prefix = prefix
        self.col = bpy.data.collections.new(prefix)
        bpy.context.scene.collection.children.link(self.col)
        self.mat, self.bm, self.uv_tile, self.extra = {}, {}, {}, []

    # ------------------------------------------------------------ materials
    def material(self, key, hexcol, rough=0.85, metal=0.0, albedo=None, normal=None, normal_strength=0.6, tile=2.0):
        m = bpy.data.materials.new(f"{self.prefix}_{key}")
        if m.node_tree is None:
            m.use_nodes = True
        nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = srgb(hexcol)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        m.diffuse_color = srgb(hexcol)
        if albedo and os.path.exists(os.path.join(TEX, albedo + ".png")):
            t = nt.nodes.new("ShaderNodeTexImage")
            t.image = bpy.data.images.load(os.path.join(TEX, albedo + ".png"), check_existing=True)
            nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
        if normal and os.path.exists(os.path.join(TEX, normal + ".png")):
            t = nt.nodes.new("ShaderNodeTexImage")
            t.image = bpy.data.images.load(os.path.join(TEX, normal + ".png"), check_existing=True)
            t.image.colorspace_settings.name = "Non-Color"
            nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = normal_strength
            nt.links.new(t.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        self.mat[key] = m
        self.bm[key] = bmesh.new()
        self.uv_tile[key] = tile
        return m

    # ------------------------------------------------------------ primitives
    def hexa(self, key, pts):
        bm = self.bm[key]
        v = [bm.verts.new(p) for p in pts]
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            bm.faces.new([v[i] for i in f])

    def wbox(self, key, x0, x1, y0, y1, z0, z1):
        self.hexa(key, [Vector((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])

    def tube(self, key, p0, p1, r, seg=8):
        bm = self.bm[key]
        p0, p1 = Vector(p0), Vector(p1)
        d = (p1 - p0).normalized()
        s = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized()
        t = d.cross(s)
        ring = lambda p: [bm.verts.new(p + (s * math.cos(2 * math.pi * k / seg) + t * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)]
        a, b = ring(p0), ring(p1)
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
        bm.faces.new(a[::-1]); bm.faces.new(b)

    def cylinder(self, key, cx, cy, z0, z1, r, seg=16):
        bmesh.ops.create_cone(self.bm[key], cap_ends=True, segments=seg, radius1=r, radius2=r, depth=z1 - z0,
                              matrix=Matrix.Translation((cx, cy, (z0 + z1) / 2)))

    def text(self, body, face, u, w, z, height, key, serif=True, extrude=0.03):
        """Raised letters on a facade, centred at (u, z), reading left-to-right for a viewer outside."""
        cu = bpy.data.curves.new("txt", "FONT")
        cu.body = body; cu.size = height; cu.extrude = extrude; cu.align_x = "CENTER"; cu.align_y = "CENTER"
        cu.resolution_u = 3
        fp = FONT_SERIF if serif else FONT_SANS
        if os.path.exists(fp):
            cu.font = bpy.data.fonts.load(fp, check_existing=True)
        ob = bpy.data.objects.new("txt", cu); self.col.objects.link(ob)
        c = face.P(u, w + extrude, z)
        U, Z, N = face.U, Vector((0, 0, 1)), face.N
        ob.matrix_world = Matrix(((U.x, Z.x, N.x, c.x), (U.y, Z.y, N.y, c.y), (U.z, Z.z, N.z, c.z), (0, 0, 0, 1)))
        bpy.context.view_layer.update()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        mw = ob.matrix_world.copy()
        bpy.data.objects.remove(ob); bpy.data.curves.remove(cu)
        me.materials.clear(); me.materials.append(self.mat[key])
        t = bpy.data.objects.new(f"{self.prefix}_text", me); self.col.objects.link(t); t.matrix_world = mw
        self.extra.append(t)

    # ------------------------------------------------------------ finish
    def finish(self, footprint, top, export_name, colliders=None):
        objs = []
        for key, bm in self.bm.items():
            if not bm.verts:
                bm.free(); continue
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            uvl = bm.loops.layers.uv.new("UVMap")
            ts = self.uv_tile.get(key, 2.0)
            for face in bm.faces:
                n = face.normal
                ax = max(range(3), key=lambda i: abs(n[i]))
                for lp in face.loops:
                    co = lp.vert.co
                    if ax == 0:
                        uv = (co.y * (1 if n.x > 0 else -1), co.z)
                    elif ax == 1:
                        uv = (co.x * (-1 if n.y > 0 else 1), co.z)
                    else:
                        uv = (co.x, co.y)
                    lp[uvl].uv = (uv[0] / ts, uv[1] / ts)
            me = bpy.data.meshes.new(f"{self.prefix}_{key}")
            bm.to_mesh(me); bm.free()
            me.materials.append(self.mat[key])
            ob = bpy.data.objects.new(f"{self.prefix}_{key}", me); self.col.objects.link(ob); objs.append(ob)
        objs += self.extra
        with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs):
            bpy.ops.object.join()
        main = objs[0]; main.name = self.prefix; main.data.name = self.prefix
        x0, y0, x1, y1 = footprint
        centre = Vector(((x0 + x1) / 2, (y0 + y1) / 2, 0))
        main.data.transform(Matrix.Translation(-centre)); main.location = centre
        bm = bmesh.new()
        for cx0, cx1, cy0, cy1, cz1 in (colliders or [(x0, x1, y0, y1, top)]):
            r = bmesh.ops.create_cube(bm, size=1.0)
            for v in r["verts"]:
                v.co = Vector((cx0 if v.co.x < 0 else cx1, cy0 if v.co.y < 0 else cy1, 0 if v.co.z < 0 else cz1)) - centre
        cme = bpy.data.meshes.new(f"{self.prefix}_Collider"); bm.to_mesh(cme); bm.free()
        col = bpy.data.objects.new(f"{self.prefix}_Collider", cme); self.col.objects.link(col)
        col.location = centre; col.hide_render = True; col.display_type = "WIRE"
        os.makedirs(os.path.join(ROOT, "blender"), exist_ok=True)
        os.makedirs(os.path.join(ROOT, "export"), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "blender", f"{export_name.lower()}.blend"))
        for ob in bpy.context.view_layer.objects:
            ob.select_set(ob.name in (main.name, col.name))
        bpy.ops.export_scene.fbx(filepath=os.path.join(ROOT, "export", f"{export_name}.fbx"), use_selection=True,
                                 object_types={"MESH"}, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                                 bake_space_transform=True, mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
                                 path_mode="COPY", embed_textures=True)
        for ob in bpy.context.view_layer.objects:
            ob.select_set(ob.name == main.name)
        bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, "export", f"{export_name}.glb"), export_format="GLB",
                                  use_selection=True, export_image_format="JPEG", export_jpeg_quality=85)
        print(f"{export_name} faces:", len(main.data.polygons), "| size:", tuple(round(v, 2) for v in main.dimensions))
        return main


class Face:
    """Local facade frame: u along the face (from the viewer's left), w outward, z up."""
    def __init__(self, B, origin, u_dir, normal, width):
        self.B = B
        self.O, self.U, self.N, self.W = Vector(origin), Vector(u_dir), Vector(normal), width

    def P(self, u, w, z):
        return self.O + self.U * u + self.N * w + Vector((0, 0, z))

    def box(self, key, u0, u1, w0, w1, z0, z1):
        self.B.hexa(key, [self.P(u, w, z) for u in (u0, u1) for w in (w0, w1) for z in (z0, z1)])
