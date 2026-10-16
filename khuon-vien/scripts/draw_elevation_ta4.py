"""B2 – scaled elevation drawings for TA4 (sign TB5), read from layout/buildings/ta4.json.
Outputs in 02_toa_nha/ta4/. Usage: python3 scripts/draw_elevation_ta4.py
"""
import json, os
from elev_lib import Sheet, wrap, side_by_side

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "ta4.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "02_toa_nha", "ta4")
os.makedirs(OUT, exist_ok=True)
C, G, LV = SPEC["colors"], SPEC["gallery"], SPEC["levels"]
X0, Y0, X1, Y1 = SPEC["rect"]
ST, GC, CB, RF = SPEC["stair_tower"], SPEC["glass_core"], SPEC["curved_bay"], SPEC["roof"]
NF = SPEC["floors"]


def lv(n):
    return 0.0 if n == 1 else LV["ground_h"] + (n - 2) * LV["typical_h"]


ROOF = lv(NF + 1)
TOP = ROOF + SPEC["parapet"]
LEVELS = [(f"T{n}", lv(n)) for n in range(2, NF + 1)] + [("Mái", ROOF), ("Nóc mái tôn", RF["ridge"])]


def gallery(s, u0, u1):
    """Open corridor face: concrete spandrel, railing, louver band, piers; colonnade at ground floor."""
    s.rect(u0, 0, u1, TOP, C["concrete"], C["concrete_dark"])
    s.rect(u0, 0, u1, lv(2) - 0.4, "#6d6a64")                                  # deep shadow of the colonnade
    for d in range(int((u1 - u0) / 3.0)):
        s.rect(u0 + 1.0 + d * 3.0, 0.1, u0 + 2.0 + d * 3.0, 2.4, C["door"])
    u = u0
    while u <= u1 + 1e-6:
        s.rect(max(u - 0.25, u0), 0, min(u + 0.25, u1), lv(2), C["pier"]); u += G["pier_step"]
    for n in range(2, NF + 1):
        z0 = lv(n)
        s.rect(u0, z0 - 0.4, u1, z0 + G["spandrel_h"], C["concrete"], C["concrete_dark"])
        s.rect(u0, z0 + G["spandrel_h"], u1, z0 + G["louver_from"], "#55524d")      # open corridor in shade
        s.line(u0, z0 + G["spandrel_h"] + 0.9, u1, z0 + G["spandrel_h"] + 0.9, C["rail"], 1)
        hb = (LV["typical_h"] - G["louver_from"])
        for k in range(G["slats"]):
            zz = z0 + G["louver_from"] + k * hb / G["slats"]
            s.rect(u0, zz, u1, zz + hb / G["slats"] * 0.6, C["louver"])
        u = u0
        while u <= u1 + 1e-6:
            s.rect(max(u - 0.2, u0), z0 + G["spandrel_h"], min(u + 0.2, u1), z0 + G["louver_from"], C["pier"]); u += G["pier_step"]
    s.rect(u0, ROOF, u1, TOP, C["concrete"], C["concrete_dark"])


def stair_tower(s, u0, u1):
    s.rect(u0, 0, u1, ROOF + 1.2, "#f1f1ef")                                   # open frame (sky behind)
    for uu in (u0 + 0.15, u1 - 0.15):
        s.rect(uu - 0.12, 0, uu + 0.12, ST["pylon_top"] if uu > u0 + 1 else ROOF + 1.2, C["steel"])
    for n in range(2, NF + 1):
        z = lv(n)
        s.rect(u0, z - 0.25, u1, z, C["rust"])
        s.rect(u0, z, u1, z + 1.0, None, C["steel"])
        s.line(u0, z - 1.7, u1, z - 0.2, C["steel"], 2)
    for k in range(4):                                                           # lattice pylon on top
        z = ROOF + 1.2 + k * (ST["pylon_top"] - ROOF - 1.2) / 4
        s.line(u0 + 0.2, z, u1 - 0.2, z + 1.5, C["steel"], 2)
        s.line(u1 - 0.2, z, u0 + 0.2, z + 1.5, C["steel"], 2)


def south():
    W = X1 - ST["rect"][0]
    o = X0 - ST["rect"][0]                                                       # building starts at u = o
    s = Sheet(W, ST["pylon_top"] + 1, "TA4 (BIỂN TB5) – MẶT ĐỨNG NAM", f'{SPEC["faces"]["south"]["title"]} · {NF} tầng',
              LEVELS, ("Đỉnh khung thép", ST["pylon_top"]), scale=24)
    r0, r1 = RF["x"][0] - ST["rect"][0], RF["x"][1] - ST["rect"][0]
    s.poly([(r0 - RF["overhang"], ROOF), (r1 + RF["overhang"], ROOF), ((r0 + r1) / 2, RF["ridge"] + 0.3)], C["roof"])
    s.poly([(r0, ROOF), (r1, ROOF), ((r0 + r1) / 2, RF["ridge"])], C["glass_green"], "#2f6052")     # glazed south gable
    m = (r0 + r1) / 2
    for k in range(1, 8):
        uu = r0 + (r1 - r0) * k / 8
        zt = ROOF + (RF["ridge"] - ROOF) * (1 - abs(uu - m) / (m - r0))
        s.line(uu, ROOF, uu, zt, "#2f6052", 1)
    g0, g1 = GC["x"][0] - ST["rect"][0], GC["x"][1] - ST["rect"][0]
    c0 = CB["center"][0] - CB["radius"] - ST["rect"][0]
    c1 = CB["center"][0] + CB["radius"] - ST["rect"][0]
    gallery(s, o, g0)
    s.rect(g0, 0, g1, TOP, C["glass_green"], "#2f6052")
    for n in range(2, NF + 2):
        s.line(g0, lv(n), g1, lv(n), "#2f6052", 2)
    gallery(s, c1, W)
    s.rect(c0 - 0.4, 0, c1 + 0.4, ROOF + 0.6, C["louver"])                    # curved louvered bay
    z = lv(2)
    while z < ROOF:
        s.line(c0 - 0.4, z, c1 + 0.4, z, "#6c7176", 1); z += 0.35
    s.rect(c0 - 0.6, ROOF + 0.1, c1 + 0.6, ROOF + 0.7, C["concrete"], C["concrete_dark"])
    s.rect(c0 - 1.0, CB["canopy_z"] - 0.35, c1 + 1.0, CB["canopy_z"], C["concrete"], C["concrete_dark"])
    for uu in (c0 + 0.5, (c0 + c1) / 2, c1 - 0.5):
        s.rect(uu - 0.2, 0, uu + 0.2, CB["canopy_z"] - 0.35, C["pier"])
    stair_tower(s, 0, o)
    SG = SPEC["sign"]
    su, sz = SG["x"] - ST["rect"][0], lv(SG["floor"]) + 0.2
    s.rect(su, sz, su + SG["w"], sz + SG["h"], C["sign_blue"], "#fff")
    s.text(su + SG["w"] / 2, sz + SG["h"] / 2, SG["text"], SG["h"] * 0.6, "#ffffff")
    s.note(o / 2, ST["pylon_top"] - 2.5, wrap("Tháp thang thép ngoài 4 tầng chiếu nghỉ, khung giàn trên đỉnh"))
    s.note(o + 6.0, lv(4) + 2.6, wrap("Hành lang hở: lan can bê tông, dải lam ngang tối, trụ xám"))
    s.note(o + 3.0, 1.4, wrap("Tầng 1 hiên cột, cửa gỗ nâu phía trong"))
    s.note((g0 + g1) / 2, lv(3) + 1.5, wrap("Lõi thang kính xanh suốt chiều cao"))
    s.note((c0 + c1) / 2, lv(4), wrap("Khối cong nhô ra 4,5 m, bọc lam kín, sảnh có mái cong + cột"))
    s.note(m, ROOF + 2.0, wrap("Mái tôn cam 2 mái, đầu hồi Nam lắp kính xanh (theo vệ tinh + ảnh)"))
    s.note(su + 0.5, sz + 1.5, wrap("Biển xanh TB5"))
    return s.finish(os.path.join(OUT, "mat_dung_nam.png"))


def west():
    W = Y1 - Y0                                                                 # u = 153.7 − y (left = north)
    s = Sheet(W, ST["pylon_top"] + 1, "TA4 – MẶT ĐỨNG TÂY", SPEC["faces"]["west"]["title"],
              LEVELS, ("Đỉnh khung thép", ST["pylon_top"]), scale=30)
    s.rect(0, 0, W, TOP, C["concrete"], C["concrete_dark"])
    for n in range(2, NF + 1):
        for cu in (3.0, 6.0):
            s.rect(cu - 0.6, lv(n) + 1.0, cu + 0.6, lv(n) + 2.4, C["glass"], "#eee")
    stair_tower(s, Y1 - ST["rect"][3], Y1 - ST["rect"][1])
    s.rect(W - G["depth"], 0, W, TOP, "#cfc9ba")                              # gallery end, louvers seen edge-on
    s.note(4.5, lv(3) + 2.0, wrap("Tường đầu hồi, cửa sổ nhỏ (giả định)"))
    s.note((2 * Y1 - ST["rect"][1] - ST["rect"][3]) / 2, ST["pylon_top"] - 2.5, wrap("Tháp thang thép nhìn chính diện"))
    return s.finish(os.path.join(OUT, "mat_dung_tay.png"))


def north():
    W = X1 - X0                                                                 # u = 77.1 − x (left = east)
    s = Sheet(W, RF["ridge"] + 1, "TA4 – MẶT ĐỨNG BẮC (GIẢ ĐỊNH)", SPEC["faces"]["north"]["title"],
              LEVELS, None, scale=24)
    r0, r1 = X1 - RF["x"][1], X1 - RF["x"][0]
    s.poly([(r0 - RF["overhang"], ROOF), (r1 + RF["overhang"], ROOF), ((r0 + r1) / 2, RF["ridge"])], C["roof"], "#8a3f24")
    s.rect(0, 0, W, TOP, C["concrete"], C["concrete_dark"])
    for n in range(1, NF + 1):
        u = 1.5
        while u + 1.8 < W - 1.0:
            s.rect(u, lv(n) + 1.0, u + 1.8, lv(n) + 2.6, C["glass"], "#eee"); u += 3.8
        s.line(0, lv(n), W, lv(n), C["concrete_dark"], 1)
    s.note(W / 2, lv(3) + 1.8, wrap("Mỗi tầng một hàng cửa sổ lớp học"))
    s.note(W / 2, RF["ridge"] - 1.2, wrap("Đầu hồi Bắc mái tôn"))
    return s.finish(os.path.join(OUT, "mat_dung_bac.png"))


def east():
    W = Y1 - Y0                                                                 # u = y − 138.6 (left = south)
    s = Sheet(W, RF["ridge"] + 1, "TA4 – MẶT ĐỨNG ĐÔNG (GIẢ ĐỊNH)", SPEC["faces"]["east"]["title"],
              LEVELS, None, scale=30)
    s.rect(0, 0, W, TOP, C["concrete"], C["concrete_dark"])
    s.rect(0, 0, G["depth"], TOP, "#cfc9ba")
    for n in range(2, NF + 1):
        s.rect(8.0, lv(n) + 1.0, 9.2, lv(n) + 2.4, C["glass"], "#eee")
    s.note(8.6, lv(4) + 2.2, wrap("Tường trơn, 1 cột cửa sổ"))
    return s.finish(os.path.join(OUT, "mat_dung_dong.png"))


def overview(images, path):
    from PIL import Image
    sc = 0.5
    ims = [im.resize((int(im.width * sc), int(im.height * sc))) for im in images]
    W = max(ims[0].width + ims[1].width, ims[2].width + ims[3].width) + 20
    H = max(ims[0].height, ims[1].height) + max(ims[2].height, ims[3].height) + 20
    sheet = Image.new("RGB", (W, H), "#ffffff")
    sheet.paste(ims[0], (0, 0)); sheet.paste(ims[1], (ims[0].width + 20, 0))
    y = max(ims[0].height, ims[1].height) + 20
    sheet.paste(ims[2], (0, y)); sheet.paste(ims[3], (ims[2].width + 20, y))
    sheet.save(path)


s_im = south()
side_by_side(os.path.join(ROOT, SPEC["faces"]["south"]["photo"]), s_im, os.path.join(OUT, "so_sanh_mat_nam.png"))
w_im = west(); n_im = north(); e_im = east()
overview([s_im, w_im, n_im, e_im], os.path.join(OUT, "tong_hop_4_mat.png"))
print("ok roof", round(ROOF, 2))
