"""B2 – scaled elevation drawings for the TA2 + TA3 cluster, read from layout/buildings/ta23.json.
Outputs in 02_toa_nha/ta23/. Usage: python3 scripts/draw_elevation_ta23.py
"""
import json, os
from elev_lib import Sheet, wrap, side_by_side

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "ta23.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "02_toa_nha", "ta23")
os.makedirs(OUT, exist_ok=True)
C, A2, A3 = SPEC["colors"], SPEC["ta2"], SPEC["ta3"]
L2, L3 = A2["levels"], A3["levels"]


def lv2(n):
    return L2["plinth"] if n == 1 else L2["plinth"] + L2["ground_h"] + (n - 2) * L2["typical_h"]


def lv3(n):
    return 0.0 if n == 1 else L3["ground_h"] + (n - 2) * L3["typical_h"]


ROOF2, ROOF3 = lv2(A2["floors"] + 1), lv3(A3["floors"] + 1)
TOP2, TOP3 = ROOF2 + A2["parapet"], ROOF3 + A3["parapet"]
BOX3 = ROOF3 + A3["roof_box"]["h"]
LEVELS = [(f"TA2 T{n}", lv2(n)) for n in range(2, A2["floors"] + 1)] + [("Mái TA2", ROOF2)] + \
         [(f"TA3 T{n}", lv3(n)) for n in range(2, A3["floors"] + 1)] + [("Mái TA3", ROOF3)]
LEVELS.sort(key=lambda t: t[1])
X2 = A2["rect"]; X3 = A3["rect"]
TA2_LEN = X2[3] - X2[1]
EAST_W = X3[3] - X2[1]


def ta2_ribbons(s, u0, u1, shopfront=True):
    """TA2 glass-ribbon face: silver spandrel + full-width glass per floor, solid end panels."""
    e = A2["end_panel"]
    s.rect(u0, 0, u1, TOP2, C["white"], "#b9bec2")
    s.rect(u0, 0, u1, L2["plinth"], C["pilaster"])
    if shopfront:
        z0, z1 = L2["plinth"], lv2(2) - 0.5
        s.rect(u0 + e, z0, u1 - e, z1, C["glass_dark"])
        u = u0 + e
        while u < u1 - e - 0.1:
            s.rect(u, z0, min(u + 0.45, u1 - e), z1, C["pilaster"])
            for k in (1, 2):
                uu = u + 0.45 + (A2["pier_step"] - 0.45) * k / 3
                if uu < u1 - e:
                    s.line(uu, z0, uu, z1, C["frame"], 1)
            s.line(u, z0 + 2.4, min(u + A2["pier_step"], u1 - e), z0 + 2.4, C["frame"], 1)
            u += A2["pier_step"]
    s.rect(u0, lv2(2) - 0.5, u1, lv2(2), C["silver"])
    for n in range(2, A2["floors"] + 1):
        z0 = lv2(n)
        s.rect(u0, z0, u1, z0 + A2["spandrel"], C["silver"], "#aab0b5")
        s.rect(u0 + e, z0 + A2["spandrel"], u1 - e, z0 + L2["typical_h"], C["glass"])
        u = u0 + e
        while u < u1 - e:
            s.line(u, z0 + A2["spandrel"], u, z0 + L2["typical_h"], C["frame"], 1); u += 1.2
    s.rect(u0, ROOF2, u1, TOP2, C["white"], "#b9bec2")


def ta2_plain(s, u0, u1):
    s.rect(u0, 0, u1, TOP2, C["white"], "#b9bec2")
    s.rect(u0, 0, u1, L2["plinth"], C["pilaster"])
    for n in range(1, A2["floors"] + 1):
        z0 = lv2(n) + (1.0 if n > 1 else 0.9)
        u = u0 + 1.8
        while u + 1.5 < u1 - 0.8:
            s.rect(u, z0, u + 1.5, z0 + 1.6, C["glass_dark"], C["frame"]); u += A2["pier_step"]
        s.line(u0, lv2(n), u1, lv2(n), "#c9cdd0", 1)


def ta3_face(s, u0, u1, louver=True, ground=True):
    st = A3["louver"]["post_step"]
    s.rect(u0, 0, u1, TOP3, C["ta3_wall"], "#a9a59e")
    if ground:
        u, i = u0, 0
        while u < u1 - 0.1:
            b = min(u + st, u1)
            s.rect(u + 0.5, 0.2, b - 0.2, 3.0, C["shutter"] if i % 3 else C["window_dark"], "#888")
            u, i = b, i + 1
    for n in range(2, A3["floors"] + 1):
        z0 = lv3(n)
        u = u0 + 1.2
        while u + 1.4 < u1:
            s.rect(u, z0 + 1.0, u + 1.4, z0 + 2.3, C["window_dark"]); u += st
    if louver:
        z = lv3(2) - 0.2
        while z < ROOF3:
            s.rect(u0, z, u1, z + A3["louver"]["slat"], C["louver"]); z += A3["louver"]["pitch"]
    u = u0
    while u <= u1 + 1e-6:
        s.rect(max(u - 0.15, u0), 0, min(u + 0.15, u1), ROOF3, C["louver_dark"]); u += st
    s.rect(u0 - 0.1, ROOF3, u1 + 0.1, TOP3, C["white"], "#b9bec2")


def roof_box(s, u0, u1, z, h):
    s.rect(u0, z, u1, z + h, C["white"], "#b9bec2")


# ===================================================================== east (courtyard)
def east():
    s = Sheet(EAST_W, BOX3 + 1, "TA2 + TA3 – MẶT ĐỨNG ĐÔNG (HƯỚNG RA SÂN)",
              f'{SPEC["faces"]["east"]["title"]} · tỷ lệ theo mét · TA2 {A2["floors"]} tầng, TA3 {A3["floors"]} tầng',
              LEVELS, ("Đỉnh buồng máy TA3", BOX3), scale=13)
    rb = A2["roof_box"]["rect"]
    roof_box(s, rb[1] - X2[1], rb[3] - X2[1], TOP2, A2["roof_box"]["h"])
    ta2_ribbons(s, 0, TA2_LEN)
    SL = A2["slogan"]
    zs = lv2(SL["floor"]) + (A2["spandrel"] - SL["h"]) / 2
    s.text(SL["u_center"], zs + SL["h"] / 2, SL["text"], SL["h"], C["gold"])
    t0 = X3[1] - X2[1]
    rb = A3["roof_box"]["rect"]
    roof_box(s, rb[1] - X2[1], rb[3] - X2[1], ROOF3, A3["roof_box"]["h"])
    ta3_face(s, t0, EAST_W)
    SG = A3["sign"]
    su = t0 + SG["u_from_south"]; sz = lv3(SG["floor"]) + 2.6
    s.rect(su, sz, su + SG["w"], sz + SG["h"], C["sign_blue"], "#fff")
    s.text(su + SG["w"] / 2, sz + SG["h"] / 2, SG["text"], SG["h"] * 0.6, "#ffffff")
    s.note(12, lv2(3) + 2.4, wrap("TA2: mỗi tầng một dải kính chạy suốt, dải ốp bạc ở dưới"))
    s.note(SL["u_center"], zs + 1.5, wrap("Chữ vàng DẠY TỐT - HỌC TỐT trên dải ốp tầng 4"))
    s.note(50, 2.4, wrap("Tầng 1 TA2: vách kính khung tối, trụ ốp đá"))
    s.note(40, TOP2 + 1.5, wrap("TA2 5 tầng mái bằng (giả định, ảnh bị cây che)"))
    s.note(t0 + 6, lv3(5), wrap("TA3 7 tầng, nhô ra sân 4 m: lam ngang xám nâu bọc kín mặt, cửa sổ nhỏ phía sau, buồng máy trên mái"))
    s.note(t0 + 4, 1.6, wrap("Tầng 1 TA3: trụ tối, cửa cuốn + cửa đi"))
    s.note(su - 1.5, sz + 0.3, wrap("Biển xanh TA3"))
    return s.finish(os.path.join(OUT, "mat_dung_dong.png"))


# ===================================================================== west (boundary side)
def west():
    s = Sheet(EAST_W, BOX3 + 1, "TA2 + TA3 – MẶT ĐỨNG TÂY (GIẢ ĐỊNH)",
              f'{SPEC["faces"]["west"]["title"]} · chưa có ảnh', LEVELS, ("Đỉnh buồng máy TA3", BOX3), scale=13, mirror=True)
    t0 = X3[1] - X2[1]
    rb = A3["roof_box"]["rect"]
    roof_box(s, rb[1] - X2[1], rb[3] - X2[1], ROOF3, A3["roof_box"]["h"])
    ta3_face(s, t0, EAST_W, louver=False, ground=False)
    ta2_plain(s, 0, TA2_LEN)
    s.note(30, lv2(3) + 2.0, wrap("TA2: tường trắng, mỗi tầng một hàng cửa sổ"))
    s.note(t0 + 12, lv3(6), wrap("TA3: lùi vào 3,5 m, tường kem xám, không lam"))
    return s.finish(os.path.join(OUT, "mat_dung_tay.png"))


# ===================================================================== north (TA3 end, towards HĐ)
def north():
    W = X3[2] - X2[0]                                   # u = -44.6 - x
    s = Sheet(W, BOX3 + 1, "TA2 + TA3 – MẶT ĐỨNG BẮC (GIẢ ĐỊNH)",
              f'{SPEC["faces"]["north"]["title"]} · chưa có ảnh', LEVELS, ("Đỉnh buồng máy TA3", BOX3), scale=30)
    ta2_plain(s, X3[2] - X3[0], W)
    rb = A3["roof_box"]["rect"]
    roof_box(s, X3[2] - rb[2], X3[2] - rb[0], ROOF3, A3["roof_box"]["h"])
    ta3_face(s, 0, X3[2] - X3[0])
    s.note(6, lv3(5), wrap("Lam ngang bọc tiếp từ mặt Đông"))
    s.note(14.3, lv2(4), wrap("Đầu Bắc TA2 thấp hơn, lùi sau"))
    return s.finish(os.path.join(OUT, "mat_dung_bac.png"))


# ===================================================================== south (TA2 end, towards TA1)
def south():
    W = X3[2] - X2[0]                                   # u = x + 60.6
    s = Sheet(W, BOX3 + 1, "TA2 + TA3 – MẶT ĐỨNG NAM (GIẢ ĐỊNH)",
              f'{SPEC["faces"]["south"]["title"]} · chưa có ảnh', LEVELS, ("Đỉnh buồng máy TA3", BOX3), scale=30)
    ta3_face(s, X3[0] - X2[0], W, ground=False)
    ta2_ribbons(s, 0, X2[2] - X2[0])
    s.note(6, lv2(4), wrap("Đầu Nam TA2: dải kính bọc tiếp từ mặt Đông"))
    s.note(14, lv3(6), wrap("TA3 cao hơn phía sau, phần nhô 4 m thấy hết chiều cao"))
    return s.finish(os.path.join(OUT, "mat_dung_nam.png"))


def overview(images, path):
    from PIL import Image
    sc = 0.5
    ims = [im.resize((int(im.width * sc), int(im.height * sc))) for im in images]
    W = max(ims[0].width, ims[1].width, ims[2].width + ims[3].width + 20)
    H = ims[0].height + ims[1].height + max(ims[2].height, ims[3].height) + 40
    sheet = Image.new("RGB", (W, H), "#ffffff")
    sheet.paste(ims[0], (0, 0)); sheet.paste(ims[1], (0, ims[0].height + 20))
    y = ims[0].height + ims[1].height + 40
    sheet.paste(ims[2], (0, y)); sheet.paste(ims[3], (ims[2].width + 20, y))
    sheet.save(path)


e_im = east()
P = SPEC["faces"]["east"]["photos"]
side_by_side(os.path.join(ROOT, P[0]), e_im, os.path.join(OUT, "so_sanh_mat_dong_ta2.png"))
side_by_side(os.path.join(ROOT, P[1]), e_im, os.path.join(OUT, "so_sanh_mat_dong_ta3.png"))
w_im = west(); n_im = north(); s_im = south()
overview([e_im, w_im, n_im, s_im], os.path.join(OUT, "tong_hop_4_mat.png"))
print("ok", e_im.size, "roof TA2", round(ROOF2, 2), "roof TA3", round(ROOF3, 2))
