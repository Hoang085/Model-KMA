"""B2 – scaled elevation drawings for Nhà ăn hệ quân (TB3), read from layout/buildings/nha_an.json.
Outputs in 02_toa_nha/nha_an/. Usage: python3 scripts/draw_elevation_nha_an.py
"""
import json, math, os
from elev_lib import Sheet, wrap, side_by_side

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "nha_an.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "02_toa_nha", "nha_an")
os.makedirs(OUT, exist_ok=True)
C = SPEC["colors"]
B = SPEC["blocks"]
LV = SPEC["levels"]
F1, F2, PAR = LV["floor1"], LV["floor2"], LV["parapet"]
ROT = B["rotunda"]
HALL = B["hall"]
WING = B["low_wing"]
LEVELS = [("T1", F1), ("T2", F2), ("Diềm mái nhà ăn", HALL["eave"]), ("Mái", PAR), ("Nóc nhà ăn", HALL["ridge"])]
TOP = max(ROT["top"], HALL["ridge"])


def window(s, u0, u1, z0, z1, panes=2, frame=None):
    s.rect(u0, z0, u1, z1, C["glass"], frame or C["frame"], 2)
    for i in range(1, panes):
        uu = u0 + (u1 - u0) * i / panes
        s.line(uu, z0, uu, z1, frame or C["frame"], 1)


def rotunda(s, u0, u1):
    """Curved glass drum seen flat: mullions bunch towards the edges like a cylinder."""
    c0, c1 = ROT["cornice"]
    s.rect(u0, 0.3, u1, c0, C["glass_rot"])
    r, cu = (u1 - u0) / 2, (u0 + u1) / 2
    for k in range(-7, 8):
        uu = cu + r * math.sin(k / 7 * math.pi / 2)
        s.line(uu, 0.3, uu, c0, C["mullion"], 2)
    z = 1.2
    while z < c0:
        s.line(u0, z, u1, z, C["mullion"], 1); z += 1.25
    s.line(u0, F2, u1, F2, C["mullion"], 3)
    s.rect(u0 - 0.2, c0, u1 + 0.2, c1, C["cream"], C["cream_dark"], 2)


def stair_wall(s, W, falling_right):
    """Sloped cream wall of the outside stair wrapping the drum."""
    a, b = (W["z_hi"], W["z_lo"]) if falling_right else (W["z_lo"], W["z_hi"])
    s.poly([(W["u0"], 0), (W["u1"], 0), (W["u1"], b), (W["u0"], a)], C["cream"], C["cream_dark"])


def roof_long(s, u0, u1):
    """Gable roof seen from the long side: the near slope from the eave up to the ridge."""
    e, r, o = HALL["eave"], HALL["ridge"], HALL["overhang"]
    s.poly([(u0, e - 0.15), (u1, e - 0.15), (u1, r), (u0, r)], C["roof"], "#7a2c25")


def gable_end(s, u0, u1):
    """Gable wall with red-brown verge trim."""
    e, r, o = HALL["eave"], HALL["ridge"], HALL["overhang"]
    um = (u0 + u1) / 2
    s.poly([(u0 - o, e - 0.2), (um, r + 0.15), (u1 + o, e - 0.2), (u1 + o, e - 0.45), (um, r - 0.1), (u0 - o, e - 0.45)], "#7a2c25")
    s.poly([(u0, 0), (u1, 0), (u1, e - 0.3), (um, r - 0.15), (u0, e - 0.3)], C["cream"], C["cream_dark"])


def hall_windows(s, u0, u1, n):
    step = (u1 - u0) / n
    for i in range(n):
        cu = u0 + step * (i + 0.5)
        window(s, cu - 0.7, cu + 0.7, 2.6, 5.4, 2)


def plinth(s, u0, u1, h=0.6):
    s.rect(u0, 0, u1, h, C["plinth"])


# ===================================================================== south (main entrance, photo 1)
def south():
    F = SPEC["faces"]["south"]
    Wm = F["width"]
    s = Sheet(Wm, TOP + 1, "NHÀ ĂN HỆ QUÂN – MẶT ĐỨNG NAM (SẢNH CHÍNH)",
              f'{F["title"]} · tỷ lệ theo mét · 2 tầng', LEVELS, ("Đỉnh khối kính", ROT["top"]), scale=34)
    # front block body
    f0, f1 = F["front"]
    s.rect(f0, 0, f1, PAR, C["cream"], C["cream_dark"])
    s.line(f0, PAR - 0.25, f1, PAR - 0.25, C["cream_dark"], 1)
    r0, r1, rz = F["recess"]
    s.rect(r0, 0, r1, rz, C["recess"])
    GL = F["grey_left"]
    s.rect(GL["u0"], GL["z0"], GL["u1"], GL["z1"], C["grey_panel"])
    z = GL["z0"] + 1.2
    while z < GL["z1"]:
        s.line(GL["u0"], z, GL["u1"], z, "#5f6569", 1); z += 1.2
    window(s, *GL["window"][:2], *GL["window"][2:], 3)
    s.rect(GL["board"][0], GL["board"][2], GL["board"][1], GL["board"][3], "#3a3a3a", "#ddd")
    GR = F["grey_right"]
    s.rect(GR["u0"], GR["z0"], GR["u1"], GR["z1"], C["grey_panel"])
    for u0, u1, z0, z1 in GR["windows"]:
        window(s, u0, u1, z0, z1, 2)
    # gable over the glazed loggia
    G = F["gable"]
    LG = F["loggia"]
    s.rect(G["u0"], F2, G["u1"], G["eave"], C["cream"])
    window(s, LG["u0"], LG["u1"], LG["z0"], LG["z1"], LG["panes"])
    s.poly([(G["u0"] - 0.3, G["eave"]), (G["u1"] + 0.3, G["eave"]), ((G["u0"] + G["u1"]) / 2, G["apex"])],
           C["cream"], C["cream_dark"])
    s.rect(G["u0"] - 0.3, G["eave"] - 0.25, G["u1"] + 0.3, G["eave"], "#f1ead0", C["cream_dark"])
    # portico
    P = F["portico"]
    s.rect(P["u0"], F1, P["u1"], P["z0"], "#3b4246")                 # glazed doors behind
    for i in range(1, 8):
        uu = P["u0"] + (P["u1"] - P["u0"]) * i / 8
        s.line(uu, F1, uu, P["z0"], "#20262a", 1)
    for cu in P["columns"]:
        s.rect(cu - P["col_w"] / 2, F1, cu + P["col_w"] / 2, P["z0"], C["marble"], C["marble_vein"])
        s.line(cu - 0.1, F1 + 0.5, cu + 0.1, P["z0"] - 0.6, C["marble_vein"], 1)
    s.rect(P["u0"], P["z0"], P["u1"], P["z1"], C["marble"], C["marble_vein"], 2)
    for k in range(5):
        u = P["u0"] + 0.6 + k * 1.3
        s.line(u, P["z0"] + 0.1, u + 0.9, P["z1"] - 0.1, C["marble_vein"], 1)
    for cu in F["ac_units"]:
        s.rect(cu - 0.35, P["z1"], cu + 0.35, P["z1"] + 0.5, C["ac"], "#b8bcbf")
    St = F["steps"]
    for k in range(St["risers"]):
        s.rect(St["u0"] - (St["risers"] - k) * 0.15, k * F1 / St["risers"], St["u1"] + (St["risers"] - k) * 0.15,
               (k + 1) * F1 / St["risers"], C["step"], "#5a2a24")
    s.rect(St["u0"] - 0.9, 0, St["u0"] - 0.4, 1.1, C["step"])        # cheek walls
    s.rect(St["u1"] + 0.3, 0, St["u1"] + 1.0, 1.1, C["step"])
    # low wing
    LW = F["low_wing"]
    s.rect(LW["u0"], 0, LW["u1"], WING["parapet"], C["cream"], C["cream_dark"])
    plinth(s, LW["u0"], LW["u1"], 0.8)
    window(s, *LW["window"][:2], *LW["window"][2:], 3)
    for u0, u1, kind in LW["doors"]:
        s.rect(u0, 0.3, u1, 2.3, C["door_dark"] if kind == "dark" else "#9ea2a5", "#555", 1)
        if kind == "grille":
            k = u0 + 0.1
            while k < u1:
                s.line(k, 0.3, k, 2.3, "#555"); k += 0.15
    d0, d1, dz0, dz1 = LW["duct"]
    s.rect(d0, dz0, d1, dz1, C["duct"], "#8e9295")
    s.rect(d0 - 0.6, dz1 - 0.3, d1, dz1 + 0.5, C["duct"], "#8e9295")
    # rotunda + outside stair in front
    rotunda(s, *F["rotunda"])
    stair_wall(s, F["stair_wall"], falling_right=True)
    s.note(4.0, 8.0, wrap("Khối kính tròn góc Tây Nam, kính xanh đậm, gờ kem trên đỉnh, cao hơn mái"))
    s.note(3.2, 2.6, wrap("Tường kem chéo: cầu thang ngoài ôm quanh khối kính, lên tầng 2 ở phía Tây"))
    s.note(11.4, 5.0, wrap("Mảng ốp xám 2 bên sảnh, ô cửa nhỏ"))
    s.note(16.3, 8.4, wrap("Trán tam giác kem, đua mái, dưới là dải kính tầng 2 lùi vào"))
    s.note(16.3, 2.5, wrap("Sảnh 4 cột ốp đá trắng vân xám, dầm đá trên đỉnh, cục điều hoà trên mái sảnh"))
    s.note(17.6, 0.35, wrap("4 bậc tam cấp đá đỏ nâu, 2 bên có bồn cây"))
    s.note(24.3, 3.6, wrap("Cánh thấp 1 tầng: 2 cửa tối + cửa song sắt, ống thông gió bạc"))
    return s.finish(os.path.join(OUT, "mat_dung_nam.png"))


# ===================================================================== west (TB3 face, photo 2)
def west():
    F = SPEC["faces"]["west"]
    Wm = F["width"]
    s = Sheet(Wm, TOP + 1, "NHÀ ĂN HỆ QUÂN – MẶT ĐỨNG TÂY (BIỂN TB3)",
              f'{F["title"]} · tỷ lệ theo mét', LEVELS, ("Đỉnh khối kính", ROT["top"]), scale=26)
    h0, h1 = F["hall"]
    roof_long(s, h0 - HALL["overhang"], h1)
    s.rect(h0, 0, h1, HALL["eave"], C["cream"], C["cream_dark"])
    plinth(s, h0, h1, 0.5)
    hall_windows(s, h0 + 0.8, F["hall_recess"][0] - 0.5, 4)
    a, b = F["hall_recess"]
    s.rect(a, 0, b, HALL["eave"], C["recess"])
    E = F["entrance"]
    s.rect(E["u0"] + 0.3, F1, E["u1"] - 0.3, E["canopy_z"], "#3b4246")
    for i in range(1, 7):
        uu = E["u0"] + 0.3 + (E["u1"] - E["u0"] - 0.6) * i / 7
        s.line(uu, F1, uu, E["canopy_z"], "#20262a", 1)
    window(s, E["u0"] + 1.0, E["u1"] - 1.0, 5.0, 6.3, 5)
    for cu in E["columns"]:
        s.rect(cu - E["col_d"] / 2, F1, cu + E["col_d"] / 2, E["canopy_z"], "#f4f4f2", "#c8c8c4")
    s.rect(E["u0"], E["canopy_z"], E["u1"], E["canopy_z"] + E["canopy_t"], "#f4f4f2", "#b9b9b4", 2)
    s0, s1, n = E["steps"]
    for k in range(n):
        s.rect(s0 - (n - k) * 0.15, k * F1 / n, s1 + (n - k) * 0.15, (k + 1) * F1 / n, "#8b8f92", "#6f7377")
    f0, f1 = F["front"]
    s.rect(f0, 0, f1, PAR, C["cream"], C["cream_dark"])
    s.line(f0, PAR - 0.25, f1, PAR - 0.25, C["cream_dark"], 1)
    r0, r1 = F["recess"]
    s.rect(r0, 0, r1, PAR - 0.6, C["recess"])
    T = F["tb3_sign"]
    s.rect(T["u"], T["z"], T["u"] + T["w"], T["z"] + T["h"], C["sign_blue"], "#ffffff", 1)
    s.text(T["u"] + T["w"] / 2, T["z"] + T["h"] / 2, T["text"], T["h"] * 0.6, "#ffffff")
    rotunda(s, *F["rotunda"])
    stair_wall(s, F["stair_wall"], falling_right=True)
    s.note(6.0, 8.6, wrap("Nhà ăn lớn: diềm +6,5, mái tôn đỏ 2 mái, nóc +10,5 chạy Bắc–Nam"))
    s.note(17.3, 5.6, wrap("Sảnh phụ: mái bằng trắng trên 2 cột tròn, cửa kính, 4 bậc"))
    s.note(26.8, 8.3, wrap("Tường kem đặc cao 2 tầng, biển xanh TB3"))
    s.note(34.5, 8.0, wrap("Khối kính tròn (góc Tây Nam)"))
    s.note(33.0, 5.3, wrap("Tường cầu thang ngoài: cao ở phía Bắc, thấp dần về phía Nam"))
    s.note(6.0, 4.0, wrap("Cửa sổ cao: giả định (ảnh bị cây che)"))
    return s.finish(os.path.join(OUT, "mat_dung_tay.png"))


# ===================================================================== north (hall gable end, photo from the tennis court)
def north():
    F = SPEC["faces"]["north"]
    Wm = F["width"]
    s = Sheet(Wm, TOP + 1, "NHÀ ĂN HỆ QUÂN – MẶT ĐỨNG BẮC (ĐẦU HỒI)",
              f'{F["title"]} · theo ảnh sân tennis', LEVELS, None, scale=34)
    s.rect(2.0, HALL["eave"], 22.0, PAR, "#d8cda2", C["cream_dark"])   # front block behind (mostly hidden)
    gable_end(s, 0, Wm)
    plinth(s, 0, Wm)
    z0, z1 = F["window_z"]
    for u0, u1 in F["windows"]:
        window(s, u0, u1, z0, z1, 2)
    St = F["stair"]
    s.poly([(St["u_lo"], 0), (St["u_lo"] + St["w"], 0), (St["u_mid"] + St["w"], St["z_mid"]), (St["u_mid"], St["z_mid"])], "#ece4c4", C["cream_dark"])
    s.poly([(St["u_mid"], St["z_mid"]), (St["u_mid"] + St["w"], St["z_mid"]), (St["u_lo"] + St["w"], St["z_top"]), (St["u_lo"], St["z_top"])], "#ece4c4", C["cream_dark"])
    s.rect(St["u_mid"] - 0.4, St["z_mid"] - 0.2, St["u_mid"] + St["w"], St["z_mid"], "#ece4c4", C["cream_dark"])
    s.rect(St["u_lo"] - 0.2, St["z_top"] - 0.2, Wm, St["z_top"], "#ece4c4", C["cream_dark"])
    d0, d1 = F["upper_door"]
    s.rect(d0, St["z_top"], d1, St["z_top"] + 2.2, C["door_dark"], "#555")
    s.note(11.0, 9.2, wrap("Đầu hồi tam giác, viền mái nâu đỏ, mái tôn đỏ 2 mái"))
    s.note(5.0, 6.6, wrap("Hàng 5 cửa sổ cao"))
    s.note(18.5, 1.4, wrap("Cầu thang ngoài 2 vế lên cửa tầng trên ở đầu Tây"))
    return s.finish(os.path.join(OUT, "mat_dung_bac.png"))


# ===================================================================== east (boundary side, assumed)
def east():
    F = SPEC["faces"]["east"]
    Wm = F["width"]
    s = Sheet(Wm, TOP + 1, "NHÀ ĂN HỆ QUÂN – MẶT ĐỨNG ĐÔNG (GIẢ ĐỊNH)",
              f'{F["title"]} · chưa có ảnh', LEVELS, ("Đỉnh khối kính", ROT["top"]), scale=26)
    # u = y - 38.6 (left = south)
    roof_long(s, 14.0, Wm + HALL["overhang"])
    s.rect(14.0, 0, Wm, HALL["eave"], C["cream"], C["cream_dark"])
    plinth(s, 14.0, Wm)
    hall_windows(s, 14.5, Wm - 0.5, 8)
    s.rect(0, 0, 14.0, PAR, C["cream"], C["cream_dark"])           # front block, set back
    for u0 in (8.0, 10.6):
        window(s, u0, u0 + 1.4, F2 + 1.2, F2 + 2.8, 2)
        window(s, u0, u0 + 1.4, 1.4, 3.0, 2)
    s.rect(1.0, ROT["cornice"][0], 0.0, ROT["top"], C["cream"])     # rotunda cap peeking out
    s.rect(0, 0, 7.0, WING["parapet"], C["cream"], C["cream_dark"])  # low wing in front
    plinth(s, 0, 7.0, 0.8)
    window(s, 2.0, 3.4, 1.0, 2.4, 2)
    window(s, 4.6, 6.0, 1.0, 2.4, 2)
    s.note(3.5, 3.6, wrap("Cánh thấp 1 tầng ở đầu Nam"))
    s.note(11.0, 8.5, wrap("Khối trước 2 tầng (lùi vào 5,6 m)"))
    s.note(26.0, 6.2, wrap("Thân nhà ăn: 8 cửa sổ cao, mái tôn đỏ 2 mái"))
    return s.finish(os.path.join(OUT, "mat_dung_dong.png"))


def overview(images, path):
    from PIL import Image
    sc = 0.5
    ims = [im.resize((int(im.width * sc), int(im.height * sc))) for im in images]
    row1 = ims[0].width + ims[1].width + 20
    row2 = ims[2].width + ims[3].width + 20
    H = max(ims[0].height, ims[1].height) + max(ims[2].height, ims[3].height) + 20
    sheet = Image.new("RGB", (max(row1, row2), H), "#ffffff")
    sheet.paste(ims[0], (0, 0)); sheet.paste(ims[1], (ims[0].width + 20, 0))
    y = max(ims[0].height, ims[1].height) + 20
    sheet.paste(ims[2], (0, y)); sheet.paste(ims[3], (ims[2].width + 20, y))
    sheet.save(path)


s_im = south()
w_im = west()
side_by_side(os.path.join(ROOT, SPEC["faces"]["south"]["photo"]), s_im, os.path.join(OUT, "so_sanh_mat_nam.png"))
side_by_side(os.path.join(ROOT, SPEC["faces"]["west"]["photo"]), w_im, os.path.join(OUT, "so_sanh_mat_tay.png"))
n_im = north()
side_by_side(os.path.join(ROOT, SPEC["faces"]["north"]["photo"]), n_im, os.path.join(OUT, "so_sanh_mat_bac.png"))
e_im = east()
overview([s_im, w_im, n_im, e_im], os.path.join(OUT, "tong_hop_4_mat.png"))
print("ok", s_im.size, w_im.size, n_im.size, e_im.size)
