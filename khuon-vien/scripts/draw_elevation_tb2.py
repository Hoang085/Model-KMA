"""B2 – scaled elevation drawings for TB2 (library + dormitory tower), read from layout/buildings/tb2.json.
Outputs in 02_toa_nha/tb2/. Usage: python3 scripts/draw_elevation_tb2.py
"""
import json, os, random
from elev_lib import Sheet, wrap, side_by_side

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "tb2.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "02_toa_nha", "tb2")
os.makedirs(OUT, exist_ok=True)
C = SPEC["colors"]
LV = SPEC["levels"]
NF = SPEC["floors"]


def level(n):
    if n == 1:
        return LV["plinth"]
    if n == 2:
        return LV["plinth"] + LV["ground_h"]
    return LV["plinth"] + LV["ground_h"] + LV["second_h"] + (n - 3) * LV["typical_h"]


PODIUM_TOP = level(LV["podium_floors"] + 1)
ROOF = level(NF + 1)
TOP_GREY = ROOF + SPEC["parapet"]["grey"]
TOP_CREAM = ROOF + SPEC["parapet"]["cream"]
LEVELS = [(f"T{n}", level(n)) for n in range(1, NF + 1)] + [("Mái", ROOF)]


def podium(s, u0, u1):
    s.rect(u0, 0, u1, PODIUM_TOP, C["podium"])
    z = 0.6
    while z < PODIUM_TOP:                                     # tile courses
        s.line(u0, z, u1, z, C["podium_line"]); z += 0.6
    s.rect(u0, 0, u1, LV["plinth"], C["steps"])


def grid_window(s, u0, u1, z0, z1, panes=4):
    s.rect(u0, z0, u1, z1, C["glass"], C["frame"], 2)
    for i in range(1, panes):
        uu = u0 + (u1 - u0) * i / panes
        s.line(uu, z0, uu, z1, C["frame"], 1)
    s.line(u0, z0 + (z1 - z0) * 0.62, u1, z0 + (z1 - z0) * 0.62, C["frame"], 1)
    k = z0 + 0.2                                              # security grille
    while k < z1 - 0.1:
        s.line(u0, k, u1, k, C["grille"], 1); k += 0.22


def small_window(s, cu, z0, w=1.1, h=1.0, ac=False):
    s.rect(cu - w / 2, z0, cu + w / 2, z0 + h, C["glass"], C["frame"], 2)
    s.line(cu, z0, cu, z0 + h, C["frame"], 1)
    if ac:
        s.rect(cu - 0.4, z0 - 0.55, cu + 0.4, z0 - 0.05, C["ac"], "#b8bcbf")


def long_tower(s, F):
    """Tower part of the long faces (north, south): grey ends + cream centre with window columns."""
    Wm = F["width"]
    g = F["grey_ends"]
    # tower body: grey ends, cream centre with window columns
    s.rect(0, PODIUM_TOP, g, TOP_GREY, C["grey"])
    s.rect(Wm - g, PODIUM_TOP, Wm, TOP_GREY, C["grey"])
    s.rect(g, PODIUM_TOP, Wm - g, TOP_CREAM, C["cream"])
    n, ww = F["window_columns"], F["window_col_w"]
    pier = (Wm - 2 * g - n * ww) / (n + 1)
    cols = [g + pier + i * (ww + pier) for i in range(n)]
    rnd = random.Random(3)
    for fl in range(LV["podium_floors"] + 1, NF + 1):
        z0 = level(fl)
        for c0 in cols:
            s.rect(c0, z0, c0 + ww, z0 + LV["typical_h"], "#c9bc9c")           # recessed strip
            grid_window(s, c0 + 0.15, c0 + ww - 0.15, z0 + 0.8, z0 + 2.8)
        for i in range(n + 1):                                                    # vents/AC on cream piers
            if rnd.random() < 0.45:
                pu = g + i * (ww + pier) + pier / 2
                s.rect(pu - 0.3, z0 + 1.5, pu + 0.3, z0 + 2.0, C["ac"], "#b8bcbf")
        for e0 in (0, Wm - g):
            for cu in F["grey_window_cols"]:
                small_window(s, e0 + cu, z0 + 1.0, 1.3, 1.5, ac=True)
    for fl in range(LV["podium_floors"] + 1, NF + 2):
        s.line(0, level(fl), Wm, level(fl), "#b9ac8c" if True else None, 1)


# ===================================================================== north (main library entrance)
def north():
    F = SPEC["faces"]["north"]
    Wm = F["width"]
    s = Sheet(Wm, TOP_CREAM + 1, "TB2 – MẶT ĐỨNG BẮC (SẢNH THƯ VIỆN)",
              f'{F["title"]} · tỷ lệ theo mét · {NF} tầng', LEVELS, ("Đỉnh", TOP_CREAM))
    g = F["grey_ends"]
    long_tower(s, F)
    # podium
    podium(s, 0, Wm)
    SF = F["shopfront"]
    u = SF["u0"]
    while u + SF["pier_every"] <= SF["u1"] + 1e-6:
        grid_window(s, u + 0.4, u + SF["pier_every"] - 0.4, LV["plinth"] + 0.3, LV["plinth"] + 3.6, 3)
        grid_window(s, u + 0.4, u + SF["pier_every"] - 0.4, level(2) + 0.9, level(2) + 3.0, 3)
        u += SF["pier_every"]
    E = F["entrance"]
    s.rect(E["u0"], LV["plinth"], E["u1"], LV["plinth"] + E["door_h"] + 0.4, "#3a3532")
    grid_window(s, E["u0"] + 0.2, E["u1"] - 0.2, LV["plinth"], LV["plinth"] + E["door_h"], 6)
    G2 = F["f2_glazing"]
    grid_window(s, G2["u0"], G2["u1"], level(2) + 0.5, level(2) + 3.3, 8)
    Cn = F["canopy"]
    s.rect(Cn["u0"], Cn["z"], Cn["u1"], Cn["z"] + 0.45, C["canopy"], "#8c9196", 2)
    St = F["steps"]
    for k in range(St["risers"]):
        s.rect(St["u0"] + k * 0.3, k * LV["plinth"] / St["risers"], St["u1"] - k * 0.3,
               (k + 1) * LV["plinth"] / St["risers"], "#9a9ea2", "#6f7377")
    SG = F["sign"]
    s.rect(SG["u0"], SG["z"] - 0.1, SG["u1"], SG["z"] + SG["h"] + 0.1, "#4a3d38")
    s.text((SG["u0"] + SG["u1"]) / 2, SG["z"] + SG["h"] / 2, SG["text"], SG["h"] * 0.9, C["gold"])
    GL = F["stair_glazing"]
    grid_window(s, GL["u0"], GL["u1"], LV["plinth"] + 0.2, PODIUM_TOP - 0.3, 4)
    if GL.get("banner", True):
        s.rect(GL["u0"] + 0.2, LV["plinth"] + 0.2, GL["u1"] - 0.2, LV["plinth"] + 1.2, C["banner"])
    s.note(Wm / 2, level(12), wrap("Phần giữa màu kem: 6 cột cửa sổ có song, lõm vào so với trụ"))
    s.note(g / 2, level(9), wrap("Hai đầu xám xanh: 2 cột cửa sổ khung trắng + cục điều hoà"))
    s.note((SG["u0"] + SG["u1"]) / 2, SG["z"] + 1.6, wrap("Chữ vàng THƯ VIỆN HỌC VIỆN KỸ THUẬT MẬT MÃ trên nền nâu"))
    s.note(Cn["u0"] - 1.2, Cn["z"] + 0.3, wrap("Mái đón sảnh phẳng, công-xôn (không cột), đua ra 3,5 m; bậc tam cấp 5 bậc"))
    s.note((GL["u0"] + GL["u1"]) / 2, PODIUM_TOP - 2.0, wrap("Vách kính cầu thang 2 tầng"))
    s.note(10, level(2) + 2.0, wrap("Đế 2 tầng ốp gạch nâu, cửa kính khung lớn"))
    return s.finish(os.path.join(OUT, "mat_dung_bac.png"))


def narrow_tower(s, F):
    """Tower part of the short faces (west, east): grey / cream / grey zones and the roof frame."""
    Wm = F["width"]
    for kind, u0, u1 in F["zones"]:
        s.rect(u0, PODIUM_TOP, u1, TOP_CREAM if kind == "cream" else TOP_GREY, C[kind])
    b0, b1 = F["big_window_col"]
    for fl in range(LV["podium_floors"] + 1, NF + 1):
        z0 = level(fl)
        grid_window(s, b0, b1, z0 + 0.6, z0 + 2.9, 2)
        for u0, u1, kind in F["small_window_cols"]:
            small_window(s, (u0 + u1) / 2, z0 + 1.1, u1 - u0, 1.0, ac=(kind == "ac"))
        s.line(0, z0, Wm, z0, "#8f9aab", 1)
    RF = F["roof_frame"]
    s.rect(RF["u0"], ROOF, RF["u1"], ROOF + RF["h"], C["grey"])
    s.rect(RF["u0"] + 0.4, ROOF + 0.3, RF["u1"] - 0.4, ROOF + RF["h"] - 0.5, "#cfd6de")      # open frame (sky)


# ===================================================================== west (LIBRARY face, towards the fountain)
def west():
    F = SPEC["faces"]["west"]
    Wm = F["width"]
    s = Sheet(Wm, TOP_CREAM + F["roof_frame"]["h"] + 1, "TB2 – MẶT ĐỨNG TÂY (CHỮ LIBRARY)",
              f'{F["title"]} · tỷ lệ theo mét · {NF} tầng', LEVELS, ("Đỉnh khung mái", ROOF + F["roof_frame"]["h"]))
    narrow_tower(s, F)
    RF = F["roof_frame"]
    podium(s, 0, Wm)
    GL = F["stair_glazing"]
    grid_window(s, GL["u0"] + 0.2, GL["u1"] - 0.2, LV["plinth"] + 0.2, PODIUM_TOP - 0.3, 3)
    B = F.get("banners")
    if B:
        s.rect(B["u0"], B["z0"], B["u1"], B["z1"], C["banner"])
        s.text((B["u0"] + B["u1"]) / 2, (B["z0"] + B["z1"]) / 2, "★", 0.8, "#f4d03f")
    LT = F["library_text"]
    s.text((LT["u0"] + LT["u1"]) / 2, LT["z"] + LT["h"] / 2, LT["text"], LT["h"] * 1.1, C["gold"])
    T = F["tb2_sign"]
    s.rect(T["u"], T["z"], T["u"] + T["w"], T["z"] + T["h"], C["sign_blue"], "#ffffff", 1)
    s.text(T["u"] + T["w"] / 2, T["z"] + T["h"] / 2, T["text"], T["h"] * 0.6, "#ffffff")
    for u0, u1 in F["f2_windows"]:
        grid_window(s, u0, u1, level(2) + 0.6, level(2) + 2.0, 2)
    for u0, u1, kind in F["doors"]:
        fill = {"beige": "#d9cdb4", "dark": "#2e2a28", "grille": "#cfd2d4"}[kind]
        s.rect(u0, LV["plinth"], u1, LV["plinth"] + 2.5, fill, "#6a625c", 2)
        if kind == "grille":
            k = u0 + 0.1
            while k < u1:
                s.line(k, LV["plinth"], k, LV["plinth"] + 2.5, "#7b7f83"); k += 0.15
        if kind == "beige":
            s.line((u0 + u1) / 2, LV["plinth"], (u0 + u1) / 2, LV["plinth"] + 2.5, "#6a625c", 2)
    s.note(2.25, level(11), wrap("Cột cửa sổ lớn 2 cánh chạy suốt chiều cao (đầu Bắc)"))
    s.note(7.8, level(15) + 1.6, wrap("Dải giữa màu kem, cửa sổ nhỏ + cục điều hoà mỗi tầng"))
    s.note(16.5, level(8), wrap("Dải xám phía Nam, cửa sổ nhỏ khung trắng"))
    s.note((RF["u0"] + RF["u1"]) / 2, ROOF + RF["h"] + 1.0, wrap("Khung rỗng trên mái (góc Tây Nam)"))
    s.note((LT["u0"] + LT["u1"]) / 2, LT["z"] + 1.6, wrap("Chữ vàng LIBRARY, biển xanh TB2 bên dưới"))
    s.note(2.25, PODIUM_TOP - 1.5, wrap("Vách kính cầu thang"))
    s.note(10.3, LV["plinth"] + 3.4, wrap("3 cửa: cửa đôi màu be, cửa tối, cửa song sắt"))
    return s.finish(os.path.join(OUT, "mat_dung_tay.png"))


# ===================================================================== south (towards the gate / TB1)
def south():
    F = dict(SPEC["faces"]["north"]); Wm = F["width"]
    s = Sheet(Wm, TOP_CREAM + 1, "TB2 – MẶT ĐỨNG NAM",
              f'{SPEC["faces"]["south"]["title"]} · tỷ lệ theo mét · {NF} tầng', LEVELS, ("Đỉnh", TOP_CREAM), mirror=True)
    long_tower(s, F)
    podium(s, 0, Wm)
    SF = F["shopfront"]
    u = SF["u0"]
    while u + SF["pier_every"] <= Wm - 1.0 + 1e-6:                     # floor-2 windows only
        grid_window(s, u + 0.4, u + SF["pier_every"] - 0.4, level(2) + 0.9, level(2) + 3.0, 3)
        u += SF["pier_every"]
    s.note(Wm / 2, level(12), wrap("Tháp giống mặt Bắc: giữa màu kem 6 cột cửa sổ, hai đầu xám xanh"))
    s.note(Wm / 2, level(2) + 2.0, wrap("Tầng 2 của đế: hàng cửa sổ như mặt Bắc"))
    s.note(Wm * 0.3, LV["plinth"] + 2.0, wrap("Tầng 1: tường đặc ốp gạch nâu, không cửa, không sảnh"))
    return s.finish(os.path.join(OUT, "mat_dung_nam.png"))


# ===================================================================== east (back short face)
def east():
    F = dict(SPEC["faces"]["west"]); Wm = F["width"]
    s = Sheet(Wm, TOP_CREAM + F["roof_frame"]["h"] + 1, "TB2 – MẶT ĐỨNG ĐÔNG",
              f'{SPEC["faces"]["east"]["title"]} · tỷ lệ theo mét · {NF} tầng', LEVELS,
              ("Đỉnh khung mái", ROOF + F["roof_frame"]["h"]), mirror=True)
    narrow_tower(s, F)
    podium(s, 0, Wm)
    GL = F["stair_glazing"]
    grid_window(s, GL["u0"] + 0.2, GL["u1"] - 0.2, LV["plinth"] + 0.2, PODIUM_TOP - 0.3, 3)
    for u0, u1 in F["f2_windows"]:
        grid_window(s, u0, u1, level(2) + 0.6, level(2) + 2.0, 2)
    s.note(2.25, level(11), wrap("Như mặt Tây, đối xứng: cột cửa sổ lớn ở đầu Bắc"))
    s.note(7.8, level(15) + 1.6, wrap("Dải giữa màu kem, cửa sổ nhỏ + điều hoà"))
    s.note(2.25, PODIUM_TOP - 1.5, wrap("Vách kính cầu thang ở đầu Bắc"))
    s.note(11.5, LV["plinth"] + 2.0, wrap("Không có cửa ra vào, không chữ LIBRARY / biển TB2"))
    return s.finish(os.path.join(OUT, "mat_dung_dong.png"))


def overview(images, path):
    from PIL import Image
    sc = 0.5
    ims = [im.resize((int(im.width * sc), int(im.height * sc))) for im in images]
    W = ims[0].width + ims[1].width + 20
    H = max(ims[0].height, ims[1].height) + max(ims[2].height, ims[3].height) + 20
    sheet = Image.new("RGB", (max(W, ims[2].width + ims[3].width + 20), H), "#ffffff")
    sheet.paste(ims[0], (0, 0)); sheet.paste(ims[1], (ims[0].width + 20, 0))
    y = max(ims[0].height, ims[1].height) + 20
    sheet.paste(ims[2], (0, y)); sheet.paste(ims[3], (ims[2].width + 20, y))
    sheet.save(path)


n_im = north()
w_im = west()
side_by_side(os.path.join(ROOT, SPEC["faces"]["north"]["photo"]), n_im, os.path.join(OUT, "so_sanh_mat_bac.png"))
side_by_side(os.path.join(ROOT, SPEC["faces"]["west"]["photo"]), w_im, os.path.join(OUT, "so_sanh_mat_tay.png"))
s_im = south()
e_im = east()
overview([n_im, w_im, s_im, e_im], os.path.join(OUT, "tong_hop_4_mat.png"))
print("ok", n_im.size, w_im.size, s_im.size, e_im.size, "roof", round(ROOF, 1), "top", round(TOP_CREAM, 1))
