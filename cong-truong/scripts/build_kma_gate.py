"""
Build the KMA (Học viện Kỹ thuật Mật mã) front gate + front wall for a Unity 3rd-person game.

Run inside Blender:  exec(open("<this file>").read())
Units: 1 Blender unit = 1 m. Outside (street) is -Y, campus is +Y, Z up.
Gate leaves are separate objects with their origin on the hinge axis so they can swing in Unity.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

ROOT_DIR = os.environ.get("KMA_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"

# ---------------------------------------------------------------- parameters
P = dict(
    p=0.8,          # pillar width
    ph=3.2,         # pillar height (top of cap = spring line of arches)
    oc=5.0,         # centre opening width
    os=3.2,         # side opening width
    depth=4.0,      # gate block depth (front face to back face)
    ft=5.2,         # top of white frieze / eave height
    fth=0.3,        # frieze thickness
    rc=0.95,        # centre arch rise
    rs=0.75,        # side arch rise
    gw=4.2,         # guardhouse width
    ov=0.6,         # roof overhang
    pitch=28.0,     # roof pitch (deg)
    wh=2.4,         # wall height
    wt=0.3,         # wall thickness
    wall_r=18.0,    # wall length right of the gate
    wall_l=12.0,    # wall length left of the guardhouse
    step=3.6,       # wall post spacing
    gh=2.3,         # gate leaf height
)
p, ph, D, FT = P["p"], P["ph"], P["depth"], P["ft"]
W = 4 * p + P["oc"] + 2 * P["os"]
YF, YB = -D / 2, D / 2
YFC, YBC = YF + p / 2, YB - p / 2          # front / back pillar row centre
XG0, XG1 = -W / 2 - P["gw"], -W / 2        # guardhouse x range
TAN = math.tan(math.radians(P["pitch"]))


# ---------------------------------------------------------------- helpers
def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


def mat(name, hexcol, rough=0.85, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    col = srgb(hexcol)
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    m.diffuse_color = col
    m.roughness = rough
    m.metallic = metal
    return m


M = {
    "cream": mat("KMA_Cream", "#D6BD8C"),
    "cream_dark": mat("KMA_CreamDark", "#A38D66"),
    "white": mat("KMA_White", "#EEEBE3"),
    "tile": mat("KMA_RoofTile", "#A63E2E", 0.7),
    "ridge": mat("KMA_RidgeTile", "#86301F", 0.7),
    "iron": mat("KMA_Iron", "#161616", 0.45, 0.7),
    "gold": mat("KMA_Gold", "#C9A04A", 0.35, 1.0),
    "bronze": mat("KMA_LetterBronze", "#4C3A28", 0.5, 0.6),
    "glass": mat("KMA_Glass", "#1F2B35", 0.08, 0.2),
    "red": mat("KMA_SignRed", "#B3221E", 0.6),
    "door": mat("KMA_DoorMetal", "#5F655F", 0.5, 0.4),
    "ground": mat("KMA_Concrete", "#8E8C86", 0.95),
}


def get_collection(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    return col


COL = get_collection("KMA_Gate")
for o in list(COL.all_objects):
    bpy.data.objects.remove(o, do_unlink=True)
GROUPS = {}


def box_bm(bm, x0, x1, y0, y1, z0, z1):
    ret = bmesh.ops.create_cube(bm, size=1.0)
    for v in ret["verts"]:
        v.co = Vector((x0 if v.co.x < 0 else x1, y0 if v.co.y < 0 else y1, z0 if v.co.z < 0 else z1))


def prism_x_bm(bm, x0, x1, yc, hw, z0, hh):
    """Gable-shaped prism along X (wall coping)."""
    pts = [(yc - hw, z0), (yc + hw, z0), (yc, z0 + hh)]
    a = [bm.verts.new((x0, y, z)) for y, z in pts]
    b = [bm.verts.new((x1, y, z)) for y, z in pts]
    bm.faces.new(a[::-1]); bm.faces.new(b)
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((a[i], a[j], b[j], b[i]))


def pyramid_bm(bm, cx, cy, z0, hw, hd, hh):
    base = [bm.verts.new((cx + sx * hw, cy + sy * hd, z0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    apex = bm.verts.new((cx, cy, z0 + hh))
    bm.faces.new(base[::-1])
    for i in range(4):
        bm.faces.new((base[i], base[(i + 1) % 4], apex))


def tube_bm(bm, p0, p1, r, seg=10):
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0).normalized()
    s = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized()
    t = d.cross(s)
    r0, r1 = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        off = (s * math.cos(a) + t * math.sin(a)) * r
        r0.append(bm.verts.new(p0 + off)); r1.append(bm.verts.new(p1 + off))
    for k in range(seg):
        bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    bm.faces.new(r0[::-1]); bm.faces.new(r1)


def halfround_bm(bm, p0, p1, n, r, seg=4):
    """Half-round roof tile rib lying on a surface with normal n."""
    d = (p1 - p0).normalized()
    s = d.cross(n).normalized()
    r0, r1 = [], []
    for k in range(seg + 1):
        a = math.pi * k / seg
        off = s * math.cos(a) * r + n * math.sin(a) * r
        r0.append(bm.verts.new(p0 + off)); r1.append(bm.verts.new(p1 + off))
    for k in range(seg):
        bm.faces.new((r0[k], r1[k], r1[k + 1], r0[k + 1]))
    bm.faces.new((r0[seg], r1[seg], r1[0], r0[0]))
    bm.faces.new(r0); bm.faces.new(r1[::-1])


def arch_ring_bm(bm, xc, zc, R, half_deg, width, y0, y1, n=28):
    """Arch moulding (archivolt) in the XZ plane, thickness y0..y1."""
    rings = []
    for i in range(n + 1):
        t = math.radians(90 - half_deg + 2 * half_deg * i / n)
        c, s = math.cos(t), math.sin(t)
        ring = []
        for rr in (R, R + width):
            for y in (y0, y1):
                ring.append(bm.verts.new((xc + rr * c, y, zc + rr * s)))
        rings.append(ring)  # inner-y0, inner-y1, outer-y0, outer-y1
    for i in range(n):
        a, b = rings[i], rings[i + 1]
        bm.faces.new((a[0], b[0], b[2], a[2]))
        bm.faces.new((a[1], a[3], b[3], b[1]))
        bm.faces.new((a[2], b[2], b[3], a[3]))
        bm.faces.new((a[0], a[1], b[1], b[0]))
    for r in (rings[0], rings[-1]):
        bm.faces.new((r[0], r[2], r[3], r[1]))


def obj(name, bm, m, group, loc=(0, 0, 0), matrix=None, bevel=0.0, recalc=True):
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    if m:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    COL.objects.link(ob)
    if matrix is not None:
        ob.matrix_world = matrix
    else:
        ob.location = loc
    if bevel > 0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = bevel; md.segments = 2; md.limit_method = "ANGLE"
    if group:
        GROUPS.setdefault(group, []).append(ob)
    return ob


def apply_mods(ob):
    if not ob.modifiers:
        return
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    me.name = old.name
    bpy.data.meshes.remove(old)


def boolean_cut(target, cutters):
    for c in cutters:
        md = target.modifiers.new("Cut", "BOOLEAN")
        md.operation = "DIFFERENCE"
        md.solver = "EXACT"
        md.object = c
    apply_mods(target)


def join(name, objs):
    for o in objs:
        apply_mods(o)
    with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs):
        bpy.ops.object.join()
    ob = objs[0]
    ob.name = name; ob.data.name = name
    return ob


_font = None


def text_mesh(name, body, size, m, loc, rot=(90, 0, 0), extrude=0.02, group=None):
    global _font
    if _font is None and os.path.exists(FONT_PATH):
        _font = bpy.data.fonts.load(FONT_PATH, check_existing=True)
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    if _font:
        cu.font = _font
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.space_line = 1.1
    cu.resolution_u = 3          # keep glyph curves light for a game mesh
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    COL.objects.link(tmp)
    tmp.location = loc
    tmp.rotation_euler = [math.radians(a) for a in rot]
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    mw = tmp.matrix_world.copy()
    bpy.data.objects.remove(tmp); bpy.data.curves.remove(cu)
    me.name = name
    me.materials.clear(); me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    COL.objects.link(ob)
    ob.matrix_world = mw
    if group:
        GROUPS.setdefault(group, []).append(ob)
    return ob


def face_matrix(origin, normal):
    """Local frame on a wall face: x along the face, y = outward normal, z = up."""
    n = Vector(normal).normalized(); up = Vector((0, 0, 1)); u = n.cross(up)
    o = Vector(origin)
    return Matrix(((u.x, n.x, up.x, o.x), (u.y, n.y, up.y, o.y), (u.z, n.z, up.z, o.z), (0, 0, 0, 1)))


# ---------------------------------------------------------------- layout
def layout():
    pillars, ops = [], []
    x = -W / 2
    for wdt, rise in ((P["os"], P["rs"]), (P["oc"], P["rc"]), (P["os"], P["rs"])):
        pillars.append(x); x += p
        ops.append((x, x + wdt, rise)); x += wdt
    pillars.append(x)
    return pillars, ops


PILLARS, OPENINGS = layout()


# ---------------------------------------------------------------- gate block
def build_pillar(x0, yc):
    cx = x0 + p / 2
    bm = bmesh.new(); box_bm(bm, cx - p / 2 - 0.06, cx + p / 2 + 0.06, yc - p / 2 - 0.06, yc + p / 2 + 0.06, 0, 0.45)
    obj("pl_base", bm, M["cream_dark"], "Structure", bevel=0.012)
    bm = bmesh.new(); box_bm(bm, cx - p / 2 - 0.03, cx + p / 2 + 0.03, yc - p / 2 - 0.03, yc + p / 2 + 0.03, 0.45, 0.55)
    obj("pl_base2", bm, M["cream"], "Structure", bevel=0.01)
    bm = bmesh.new(); box_bm(bm, cx - p / 2, cx + p / 2, yc - p / 2, yc + p / 2, 0.55, ph - 0.24)
    obj("pl_shaft", bm, M["cream"], "Structure", bevel=0.012)
    bm = bmesh.new()
    box_bm(bm, cx - p / 2 - 0.04, cx + p / 2 + 0.04, yc - p / 2 - 0.04, yc + p / 2 + 0.04, ph - 0.24, ph - 0.16)
    box_bm(bm, cx - p / 2 - 0.09, cx + p / 2 + 0.09, yc - p / 2 - 0.09, yc + p / 2 + 0.09, ph - 0.16, ph)
    obj("pl_cap", bm, M["cream"], "Structure", bevel=0.01)


def build_frieze(y0, y1, face_y, out):
    """One arcade face. out = -1 for street side, +1 for campus side."""
    bm = bmesh.new(); box_bm(bm, -W / 2, W / 2, y0, y1, ph, FT)
    fr = obj("frieze", bm, M["white"], "Structure")
    cutters = []
    for a, b, rise in OPENINGS:
        c = b - a; xc = (a + b) / 2
        R = (c * c / 4 + rise * rise) / (2 * rise)
        zc = ph + rise - R
        half = math.degrees(math.asin(min(1.0, (c / 2) / R)))
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=128, radius1=R, radius2=R, depth=(y1 - y0) + 0.6,
                              matrix=Matrix.Translation((xc, (y0 + y1) / 2, zc)) @ Matrix.Rotation(math.radians(90), 4, "X"))
        cutters.append(obj("cutter", bm, None, None))
        # archivolt moulding on the outer face
        bm = bmesh.new()
        ya, yb = sorted((face_y + out * 0.05, face_y - out * 0.01))
        arch_ring_bm(bm, xc, zc, R, half, 0.17, ya, yb)
        obj("archivolt", bm, M["white"], "Structure")
        # keystone
        bm = bmesh.new()
        kz = ph + rise
        ya, yb = sorted((face_y + out * 0.08, face_y - out * 0.01))
        box_bm(bm, xc - 0.13, xc + 0.13, ya, yb, kz - 0.02, kz + 0.32)
        obj("keystone", bm, M["cream"], "Structure", bevel=0.01)
    boolean_cut(fr, cutters)
    for c in cutters:
        bpy.data.objects.remove(c)


def build_gate_block():
    for x0 in PILLARS:
        build_pillar(x0, YFC)
        build_pillar(x0, YBC)
    build_frieze(YF, YF + P["fth"], YF, -1)
    build_frieze(YB - P["fth"], YB, YB, +1)
    # right end plate above the side passage
    bm = bmesh.new(); box_bm(bm, W / 2 - P["fth"], W / 2, YF, YB, ph, FT)
    obj("end_plate", bm, M["white"], "Structure")
    # ceiling under the roof
    bm = bmesh.new(); box_bm(bm, -W / 2, W / 2, YF, YB, FT - 0.25, FT)
    obj("ceiling", bm, M["white"], "Structure")
    # cornice bands + attic around the whole block (gate + guardhouse)
    bm = bmesh.new()
    box_bm(bm, XG0 - 0.09, W / 2 + 0.09, YF - 0.09, YB + 0.09, FT - 0.22, FT - 0.08)
    box_bm(bm, XG0 - 0.05, W / 2 + 0.05, YF - 0.05, YB + 0.05, FT - 0.08, FT)
    box_bm(bm, XG0, W / 2, YF, YB, FT, FT + P["ov"] * TAN + 0.02)
    obj("cornice", bm, M["white"], "Structure", bevel=0.008)
    # string course just above the pillar caps (front + back)
    for yy, out in ((YF, -1), (YB, 1)):
        bm = bmesh.new()
        ya, yb = sorted((yy + out * 0.04, yy - out * 0.01))
        box_bm(bm, -W / 2, W / 2, ya, yb, FT - 0.42, FT - 0.36)
        obj("string_course", bm, M["white"], "Structure")


# ---------------------------------------------------------------- guardhouse
def build_window(origin, normal, w=1.3, hr=1.3, sill=1.0, host=()):
    Mx = face_matrix(origin, normal)
    r = w / 2
    zc = sill + hr
    cut = []
    bm = bmesh.new(); box_bm(bm, -r, r, -0.12, 0.3, sill, zc)
    cut.append(obj("wcut", bm, None, None, matrix=Mx))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=r, radius2=r, depth=0.42,
                          matrix=Matrix.Translation((0, 0.09, zc)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    cut.append(obj("wcut", bm, None, None, matrix=Mx))
    for h in host:
        boolean_cut(h, cut)
    for c in cut:
        bpy.data.objects.remove(c)
    # glass
    bm = bmesh.new(); box_bm(bm, -r, r, -0.115, -0.1, sill, zc + r)
    obj("glass", bm, M["glass"], "Guardhouse", matrix=Mx)
    # grille
    bm = bmesh.new()
    n = 8
    for i in range(1, n):
        x = -r + 2 * r * i / n
        top = zc + math.sqrt(max(0.0, r * r - x * x))
        box_bm(bm, x - 0.012, x + 0.012, -0.07, -0.045, sill, top)
    for z in (sill + 0.45, sill + 0.9, zc):
        box_bm(bm, -r, r, -0.075, -0.04, z - 0.015, z + 0.015)
    arch_ring_bm(bm, 0, zc, r * 0.45, 90, 0.025, -0.075, -0.04, n=16)
    obj("grille", bm, M["iron"], "Guardhouse", matrix=Mx)
    # trim
    bm = bmesh.new()
    arch_ring_bm(bm, 0, zc, r, 90, 0.11, -0.01, 0.04)
    box_bm(bm, -r - 0.11, -r, -0.01, 0.04, sill, zc)
    box_bm(bm, r, r + 0.11, -0.01, 0.04, sill, zc)
    box_bm(bm, -r - 0.17, r + 0.17, -0.02, 0.09, sill - 0.09, sill)
    box_bm(bm, -0.09, 0.09, -0.01, 0.07, zc + r - 0.02, zc + r + 0.2)  # keystone
    obj("wtrim", bm, M["white"], "Guardhouse", matrix=Mx)


def build_door(origin, normal, host=()):
    Mx = face_matrix(origin, normal)
    bm = bmesh.new(); box_bm(bm, -0.5, 0.5, -0.1, 0.3, -0.1, 2.2)
    c = obj("dcut", bm, None, None, matrix=Mx)
    for h in host:
        boolean_cut(h, [c])
    bpy.data.objects.remove(c)
    bm = bmesh.new()
    box_bm(bm, -0.5, 0.5, -0.095, -0.06, 0.0, 2.2)
    obj("door", bm, M["door"], "Guardhouse", matrix=Mx, bevel=0.005)
    bm = bmesh.new()
    box_bm(bm, -0.36, 0.36, -0.06, -0.05, 1.3, 2.0)
    obj("door_glass", bm, M["glass"], "Guardhouse", matrix=Mx)
    bm = bmesh.new()
    box_bm(bm, 0.32, 0.42, -0.06, -0.01, 1.0, 1.04)
    obj("door_handle", bm, M["gold"], "Guardhouse", matrix=Mx)
    bm = bmesh.new()
    box_bm(bm, -0.6, -0.5, -0.01, 0.04, 0, 2.3)
    box_bm(bm, 0.5, 0.6, -0.01, 0.04, 0, 2.3)
    box_bm(bm, -0.6, 0.6, -0.01, 0.05, 2.2, 2.32)
    obj("door_trim", bm, M["white"], "Guardhouse", matrix=Mx)


def build_guardhouse():
    bm = bmesh.new(); box_bm(bm, XG0 - 0.05, XG1, YF - 0.05, YB + 0.05, 0, 0.45)
    plinth = obj("gh_plinth", bm, M["cream_dark"], "Guardhouse", bevel=0.01)
    bm = bmesh.new(); box_bm(bm, XG0, XG1, YF, YB, 0.45, ph - 0.16)
    body = obj("gh_body", bm, M["cream"], "Guardhouse")
    bm = bmesh.new()
    box_bm(bm, XG0 - 0.06, XG1, YF - 0.06, YB + 0.06, ph - 0.24, ph - 0.16)
    box_bm(bm, XG0 - 0.1, XG1, YF - 0.1, YB + 0.1, ph - 0.16, ph)
    obj("gh_band", bm, M["cream"], "Guardhouse", bevel=0.01)
    bm = bmesh.new(); box_bm(bm, XG0, XG1, YF, YB, ph, FT - 0.2)
    obj("gh_upper", bm, M["white"], "Guardhouse")
    cx = (XG0 + XG1) / 2
    build_window((cx, YF, 0), (0, -1, 0), host=(body,))                  # street side
    build_window((XG0, 0.0, 0), (-1, 0, 0), host=(body,))                # left side
    build_window((XG1, 0.0, 0), (1, 0, 0), w=1.0, hr=1.0, sill=1.1, host=(body,))  # looks into the gate passage
    build_door((XG0 + 1.2, YB, 0), (0, 1, 0), host=(body, plinth))       # campus side
    # CCTV camera on the street face
    Mx = face_matrix((XG1 - 0.35, YF, 0), (0, -1, 0))
    bm = bmesh.new()
    box_bm(bm, -0.04, 0.04, 0.0, 0.2, 2.86, 2.92)
    box_bm(bm, -0.07, 0.07, 0.12, 0.42, 2.74, 2.86)
    obj("cctv", bm, M["white"], "Guardhouse", matrix=Mx, bevel=0.01)
    bm = bmesh.new(); tube_bm(bm, (0, 0.42, 2.8), (0, 0.45, 2.8), 0.04, 12)
    obj("cctv_lens", bm, M["glass"], "Guardhouse", matrix=Mx)


# ---------------------------------------------------------------- roof
def build_roof():
    a = D / 2 + P["ov"]
    xL, xR = XG0 - P["ov"], W / 2 + P["ov"]
    ze = FT
    h = a * TAN
    th = math.radians(P["pitch"])
    # roof sheet
    bm = bmesh.new()
    A = bm.verts.new((xL, -a, ze)); B = bm.verts.new((xR, -a, ze))
    C = bm.verts.new((xR, a, ze)); Dd = bm.verts.new((xL, a, ze))
    R1 = bm.verts.new((xL + a, 0, ze + h)); R2 = bm.verts.new((xR - a, 0, ze + h))
    bm.faces.new((A, B, R2, R1)); bm.faces.new((C, Dd, R1, R2))
    bm.faces.new((Dd, A, R1)); bm.faces.new((B, C, R2))
    sheet = obj("roof_sheet", bm, M["tile"], "Roof")
    md = sheet.modifiers.new("Solid", "SOLIDIFY"); md.thickness = 0.1; md.offset = -1
    # tile courses (small steps) + half-round ribs
    sp, rr = 0.24, 0.065
    ribs = bmesh.new()
    nF = Vector((0, -math.sin(th), math.cos(th))); nB = Vector((0, math.sin(th), math.cos(th)))
    nL = Vector((-math.sin(th), 0, math.cos(th))); nR = Vector((math.sin(th), 0, math.cos(th)))
    sink = 0.02
    x = xL + sp / 2
    while x < xR:
        run = min(a, x - xL, xR - x)
        if run > 0.08:
            for sgn, n in ((-1, nF), (1, nB)):
                p0 = Vector((x, sgn * a, ze)) - n * sink
                p1 = Vector((x, sgn * (a - run), ze + run * TAN)) - n * sink
                halfround_bm(ribs, p0, p1, n, rr)
        x += sp
    y = -a + sp / 2
    while y < a:
        run = a - abs(y)
        if run > 0.08:
            for sgn, n, x0 in ((-1, nL, xL), (1, nR, xR)):
                p0 = Vector((x0, y, ze)) - n * sink
                p1 = Vector((x0 - sgn * run, y, ze + run * TAN)) - n * sink
                halfround_bm(ribs, p0, p1, n, rr)
        y += sp
    obj("roof_ribs", ribs, M["tile"], "Roof")
    # course lips every 0.34 m along the slope
    lips = bmesh.new()
    k = 1
    while True:
        run = k * 0.34 * math.cos(th)
        if run >= a - 0.1:
            break
        z = ze + run * TAN
        hw = 0.012
        for sgn, n in ((-1, nF), (1, nB)):
            yy = sgn * (a - run)
            box_bm(lips, xL + run, xR - run, yy - hw, yy + hw, z, z + rr * 1.1)
        for sgn, n in ((-1, nL), (1, nR)):
            xx = (xL + run) if sgn < 0 else (xR - run)
            box_bm(lips, xx - hw, xx + hw, -(a - run), a - run, z, z + rr * 1.1)
        k += 1
    obj("roof_courses", lips, M["ridge"], "Roof")
    # ridge + hips
    caps = bmesh.new()
    lift = Vector((0, 0, 0.06))
    ridge = [Vector((xL + a, 0, ze + h)), Vector((xR - a, 0, ze + h))]
    tube_bm(caps, ridge[0] + lift, ridge[1] + lift, 0.12, 12)
    for corner, top in (((xL, -a), ridge[0]), ((xL, a), ridge[0]), ((xR, -a), ridge[1]), ((xR, a), ridge[1])):
        tube_bm(caps, Vector((corner[0], corner[1], ze)) + lift, top + lift, 0.1, 10)
    for pt in ridge:
        bmesh.ops.create_uvsphere(caps, u_segments=12, v_segments=8, radius=0.17,
                                  matrix=Matrix.Translation(pt + lift * 1.6))
    obj("roof_ridges", caps, M["ridge"], "Roof")
    # fascia board
    bm = bmesh.new()
    t = 0.05
    box_bm(bm, xL - t, xR + t, -a - t, -a, ze - 0.2, ze + 0.03)
    box_bm(bm, xL - t, xR + t, a, a + t, ze - 0.2, ze + 0.03)
    box_bm(bm, xL - t, xL, -a, a, ze - 0.2, ze + 0.03)
    box_bm(bm, xR, xR + t, -a, a, ze - 0.2, ze + 0.03)
    obj("fascia", bm, M["white"], "Roof")


# ---------------------------------------------------------------- signage
def build_signage():
    text_mesh("sign_main", "HỌC VIỆN KỸ THUẬT MẬT MÃ", 0.66, M["bronze"],
              (0, YF - 0.03, (ph + P["rc"] + 0.3 + FT - 0.42) / 2), extrude=0.03, group="Signage")
    # black name plaque on the pillar right of the centre opening
    px = PILLARS[2] + p / 2
    bm = bmesh.new(); box_bm(bm, px - 0.3, px + 0.3, YF - 0.04, YF + 0.01, 1.35, 2.45)
    obj("plaque", bm, M["iron"], "Signage", bevel=0.008)
    bm = bmesh.new()
    for x0, x1, z0, z1 in ((px - 0.27, px + 0.27, 2.39, 2.41), (px - 0.27, px + 0.27, 1.39, 1.41),
                           (px - 0.27, px - 0.25, 1.39, 2.41), (px + 0.25, px + 0.27, 1.39, 2.41)):
        box_bm(bm, x0, x1, YF - 0.05, YF - 0.035, z0, z1)
    obj("plaque_border", bm, M["gold"], "Signage")
    text_mesh("plaque_text", "HỌC VIỆN\nKỸ THUẬT\nMẬT MÃ", 0.095, M["gold"], (px, YF - 0.045, 1.95),
              extrude=0.004, group="Signage")
    # small red notice board on the pillar left of the centre opening
    px = PILLARS[1] + p / 2
    bm = bmesh.new(); box_bm(bm, px - 0.24, px + 0.24, YF - 0.03, YF + 0.01, 1.0, 1.32)
    obj("notice", bm, M["red"], "Signage")


# ---------------------------------------------------------------- gate leaves
def build_leaf(name, width, d, hx, hy):
    H, z0, t = P["gh"], 0.04, 0.07
    bm = bmesh.new()

    def B(a, b, y0, y1, c0, c1):
        box_bm(bm, min(a * d, b * d), max(a * d, b * d), y0, y1, c0, c1)

    B(0, t, -t / 2, t / 2, z0, z0 + H)
    B(width - t, width, -t / 2, t / 2, z0, z0 + H)
    for zr in (z0, z0 + 0.8, z0 + H - 0.4, z0 + H - t):
        B(t, width - t, -t / 2 + 0.006, t / 2 - 0.006, zr, zr + t)
    B(t, width - t, -0.012, 0.012, z0 + t, z0 + 0.8)                    # bottom sheet
    inner = width - 2 * t
    n = max(2, int(inner / 0.115))
    spx = inner / n
    for i in range(1, n):
        x = t + i * spx
        B(x - 0.013, x + 0.013, -0.013, 0.013, z0 + 0.8 + t, z0 + H + 0.06)
        pyramid_bm(bm, x * d, 0, z0 + H + 0.06, 0.026, 0.026, 0.1)       # spear tip
    # decorative rings between upper rails
    for i in range(n):
        x = t + (i + 0.5) * spx
        zc = z0 + H - 0.4 + t + (0.4 - 2 * t) / 2
        arch_ring_bm(bm, x * d, zc, 0.035, 180, 0.012, -0.01, 0.01, n=12)
    for zz in (z0 + 0.3, z0 + H - 0.3):                                  # hinge barrels
        tube_bm(bm, (-0.03 * d, 0, zz - 0.1), (-0.03 * d, 0, zz + 0.1), 0.035, 10)
    B(width - 0.12, width - 0.04, -t / 2 - 0.05, -t / 2, z0 + 1.0, z0 + 1.04)  # latch handle
    leaf = obj(name, bm, M["iron"], None, loc=(hx, hy, 0))
    # KMA plaque
    cx = hx + d * width / 2
    bm = bmesh.new(); box_bm(bm, cx - 0.3, cx + 0.3, hy - 0.035, hy - 0.012, z0 + 0.32, z0 + 0.58)
    pl = obj(name + "_plaque", bm, M["gold"], None, bevel=0.006)
    tx = text_mesh(name + "_kma", "KMA", 0.2, M["iron"], (cx, hy - 0.04, z0 + 0.45), extrude=0.006)
    return join(name, [leaf, pl, tx])


def build_gates():
    leaves = []
    names = ("L", "C", "R")
    for (a, b, _), tag in zip(OPENINGS, names):
        wl = (b - a) / 2 - 0.02
        leaves.append(build_leaf(f"KMA_Gate_{tag}_Left", wl, +1, a + 0.01, YFC))
        leaves.append(build_leaf(f"KMA_Gate_{tag}_Right", wl, -1, b - 0.01, YFC))
    return leaves


# ---------------------------------------------------------------- front wall
def build_wall(group, x0, x1, yc, skip_start_post):
    wt, wh = P["wt"], P["wh"]
    bm = bmesh.new()
    box_bm(bm, x0, x1, yc - wt / 2 - 0.03, yc + wt / 2 + 0.03, 0, 0.35)
    obj("w_plinth", bm, M["cream_dark"], group, bevel=0.008)
    bm = bmesh.new()
    box_bm(bm, x0, x1, yc - wt / 2, yc + wt / 2, 0.35, wh)
    box_bm(bm, x0, x1, yc - wt / 2 - 0.03, yc + wt / 2 + 0.03, wh - 0.55, wh - 0.47)
    obj("w_body", bm, M["cream"], group)
    bm = bmesh.new()
    box_bm(bm, x0, x1, yc - wt / 2 - 0.06, yc + wt / 2 + 0.06, wh, wh + 0.05)
    obj("w_cap", bm, M["white"], group)
    bm = bmesh.new()
    prism_x_bm(bm, x0, x1, yc, wt / 2 + 0.1, wh + 0.05, 0.16)
    obj("w_coping", bm, M["tile"], group)
    # posts
    xs = []
    lo, hi = min(x0, x1), max(x0, x1)
    nseg = max(1, round((hi - lo) / P["step"]))
    for i in range(nseg + 1):
        xs.append(lo + (hi - lo) * i / nseg)
    start = x0
    bmP, bmB, bmC, bmT = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    for x in xs:
        if skip_start_post and abs(x - start) < 1e-4:
            continue
        hw, hd = 0.25, wt / 2 + 0.1
        box_bm(bmB, x - hw - 0.04, x + hw + 0.04, yc - hd - 0.04, yc + hd + 0.04, 0, 0.42)
        box_bm(bmP, x - hw, x + hw, yc - hd, yc + hd, 0.42, wh + 0.2)
        box_bm(bmC, x - hw - 0.05, x + hw + 0.05, yc - hd - 0.05, yc + hd + 0.05, wh + 0.2, wh + 0.27)
        pyramid_bm(bmT, x, yc, wh + 0.27, hw + 0.08, hd + 0.08, 0.2)
    obj("w_post_base", bmB, M["cream_dark"], group, bevel=0.01)
    obj("w_post", bmP, M["cream"], group, bevel=0.012)
    obj("w_post_cap", bmC, M["white"], group, bevel=0.008)
    obj("w_post_roof", bmT, M["tile"], group)


# ---------------------------------------------------------------- run
build_gate_block()
build_guardhouse()
build_roof()
build_signage()
gates = build_gates()
build_wall("Wall_Right", W / 2, W / 2 + P["wall_r"], YFC, True)
build_wall("Wall_Left", XG0, XG0 - P["wall_l"], YFC, True)

result = {}
for g in ("Structure", "Guardhouse", "Roof", "Signage", "Wall_Right", "Wall_Left"):
    result[g] = join("KMA_" + g, GROUPS[g])

root = bpy.data.objects.get("KMA_Gate_Root")
if root is None:
    root = bpy.data.objects.new("KMA_Gate_Root", None)
    root.empty_display_type = "ARROWS"
if root.name not in COL.objects:
    COL.objects.link(root)
for ob in list(result.values()) + gates:
    ob.parent = root
    for poly in ob.data.polygons:
        poly.use_smooth = False

# preview-only objects (not exported)
PRE = get_collection("Preview")
if "Preview_Ground" not in bpy.data.objects:
    bm = bmesh.new(); box_bm(bm, -40, 40, -25, 30, -0.1, 0.0)
    me = bpy.data.meshes.new("Preview_Ground"); bm.to_mesh(me); bm.free(); me.materials.append(M["ground"])
    PRE.objects.link(bpy.data.objects.new("Preview_Ground", me))
if "Preview_Sun" not in bpy.data.objects:
    ld = bpy.data.lights.new("Preview_Sun", "SUN"); ld.energy = 3.5
    sun = bpy.data.objects.new("Preview_Sun", ld); sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
    PRE.objects.link(sun)

bpy.data.orphans_purge(do_recursive=True)
total = 0
for ob in COL.objects:
    if ob.type == "MESH":
        total += len(ob.data.polygons)
        print(f"{ob.name:28s} faces={len(ob.data.polygons):6d} dims={tuple(round(v, 2) for v in ob.dimensions)}")
print("TOTAL faces:", total, "| gate width W =", round(W, 2))
