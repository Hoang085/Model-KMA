"""B2 – elevations for the admin tower (HĐ) + link + assembly hall, read from layout/buildings/hd.json.
Outputs in 02_toa_nha/hd/. Usage: python3 scripts/draw_elevation_hd.py
"""
import json, math, os
from elev_lib import Sheet, wrap, side_by_side

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "hd.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "02_toa_nha", "hd")
os.makedirs(OUT, exist_ok=True)
C = SPEC["colors"]
T = SPEC["tower"]; LV = T["levels"]; NF = T["floors"]
SKY = "#cfdbe6"


def level(n):
    z = [LV["plinth"], LV["plinth"] + LV["ground_h"], LV["plinth"] + LV["ground_h"] + LV["f2_h"],
         LV["plinth"] + LV["ground_h"] + LV["f2_h"] + LV["f3_h"]]
    return z[n - 1] if n <= 4 else z[3] + (n - 4) * LV["typical_h"]


ROOF = level(NF + 1)
CROWN = ROOF + T["crown_h"]
LEVELS = [(f"T{n}", level(n)) for n in range(1, NF + 1)] + [("Mái", ROOF)]


def glass_grid(s, u0, u1, z0, z1, step=1.2, fill=None, line="#2f3b42"):
    s.rect(u0, z0, u1, z1, fill or C["glass"], line, 1)
    u = u0 + step
    while u < u1 - 0.05:
        s.line(u, z0, u, z1, line, 1); u += step


def crown(s, u0, u1):
    """Open frame on top of the tower: thin vertical slats against the sky, solid top beam."""
    s.rect(u0, ROOF, u1, CROWN, SKY)
    u = u0
    while u <= u1 + 1e-6:
        s.rect(u - 0.15, ROOF, u + 0.15, CROWN, C["fin"]); u += 1.0
    s.rect(u0, CROWN - 0.8, u1, CROWN, C["cream"], "#b9aa82")


# ===================================================================== tower – south (main entrance)
def south():
    F = T["south"]; Wm = F["width"]
    s = Sheet(Wm, CROWN + 1, "TÒA ĐIỀU HÀNH – MẶT NAM (SẢNH CHÍNH)", f'{F["title"]} · tỷ lệ theo mét · {NF} tầng',
              LEVELS, ("Đỉnh khung", CROWN))
    s.rect(0, 0, Wm, ROOF, C["cream"])
    # ribbon zone: recessed, continuous glass bands
    r0, r1 = F["ribbon_zone"]
    s.rect(r0, level(3), r1, ROOF, C["cream_dark"])
    for n in range(3, NF + 1):
        glass_grid(s, r0 + 0.3, r1 - 0.3, level(n) + 0.9, level(n) + 2.7, 1.2, C["glass_light"])
    # fin zone: small windows between dark vertical fins
    f0, f1 = F["fin_zone"]
    for n in range(3, NF + 1):
        u = f0 + F["fin_step"] / 2
        while u < f1:
            s.rect(u - 0.4, level(n) + 1.0, u + 0.4, level(n) + 2.6, C["glass"]); u += F["fin_step"]
    u = f0
    while u <= f1 + 1e-6:
        s.rect(u - 0.25, 0, u + 0.25, CROWN, C["fin"]); u += F["fin_step"]
    # grid block (east end): windows above, grey frame + big glazing on the podium
    g0, g1 = F["grid_block"]
    for n in range(5, NF + 1):
        u = g0 + 1.0
        while u + 1.6 <= g1 - 0.6:
            s.rect(u, level(n) + 0.9, u + 1.6, level(n) + 2.8, C["glass"], "#f0eee8", 1); u += 2.25
    s.rect(g0, ROOF, g1, ROOF + 1.2, C["cream"], "#b9aa82")
    s.rect(g0, 0, g1, level(2) - 0.3, C["cream"])
    for c in F["grid_frame_cols"]:
        s.rect(c - 0.5, 0, c + 0.5, level(5), C["grey_frame"])
    for zb in (level(2), level(3), level(4), level(5)):
        s.rect(g0, zb - 0.35, g1, zb, C["grey_frame"])
    cols = F["grid_frame_cols"]
    for a, b in zip(cols[:-1], cols[1:]):
        for n in (2, 3, 4):
            glass_grid(s, a + 0.6, b - 0.6, level(n) + 0.2, level(n + 1) - 0.5, 1.4, C["glass_light"])
        for k in range(2):
            uu = a + 1.5 + k * 2.8
            s.rect(uu, 2.0, uu + 1.0, 2.6, C["glass"], "#ffffff", 1)
    OT = F["office_text"]
    s.text((OT["u0"] + OT["u1"]) / 2, OT["z"], OT["text"], OT["h"], C["red_text"])
    crown(s, 0, g0)
    # podium: lobby, canopy, stairs, planters, ramp
    L0, L1 = F["lobby"]
    glass_grid(s, L0, L1, LV["plinth"], level(2) + 3.0, 1.5, C["glass_light"])
    Cn = F["canopy"]
    for cu in Cn["columns"]:
        s.rect(cu - 0.35, LV["plinth"], cu + 0.35, Cn["z"], "#2b2d30")
    P_ = F["portal"]
    s.rect(P_["u0"], LV["plinth"], P_["u1"], LV["plinth"] + P_["h"], "#1f2124")
    s.rect(P_["u0"] + 0.5, LV["plinth"], P_["u1"] - 0.5, LV["plinth"] + P_["h"] - 0.5, "#3c4a52")
    s.rect(Cn["u0"], Cn["z"], Cn["u1"], Cn["z"] + Cn["thick"], C["white_panel"], "#8c8f92", 2)
    s.rect(Cn["u0"], Cn["z"], Cn["u1"], Cn["z"] + 0.25, "#9ea3a6")
    E = F["entry"]
    z1, z2, cap = E["tier1_z"], E["tier2_z"], E["cap"]
    T1 = E["tier1"]; RP = E["ramps"]
    # tier 1 (drop-off under the canopy) with short curved ramps both sides
    s.rect(T1["u0"], 0, T1["u1"], z1, C["ramp"], "#9a9a96")
    Rc = RP["len"] / (math.pi / 2)
    for u_top, sgn in ((T1["u1"], 1), (T1["u0"], -1)):
        top, wall = [], []
        for i in range(RP["segments"] + 1):
            phi = (math.pi / 2) * i / RP["segments"]
            uu = u_top + sgn * (Rc + RP["lane_w"] / 2) * math.sin(phi)
            z = max(0.02, z1 * (1 - i / RP["segments"]))
            top.append((uu, z)); wall.append((uu, z + E["wall_h"] * (1 - 0.3 * i / RP["segments"])))
        s.poly([(u_top, 0)] + top + [(top[-1][0], 0)], C["ramp"], "#9a9a96")
        s.poly([(u_top, 0)] + wall + [(wall[-1][0], 0)], C["cream"], "#b9aa82")
    # lower stair (ground -> tier 1) and upper stair (tier 1 -> door terrace)
    LS, US = E["lower_stair"], E["upper_stair"]
    h = z1 / LS["risers"]
    for k in range(LS["risers"]):
        s.rect(LS["u0"], k * h, LS["u1"], (k + 1) * h, C["steps"], "#6f7377")
    h = (z2 - z1) / US["risers"]
    for k in range(US["risers"]):
        s.rect(US["u0"] + 0.2, z1 + k * h, US["u1"] - 0.2, z1 + (k + 1) * h, C["steps"], "#6f7377")
    for a_, b_ in ((US["u0"] - 1.0, US["u0"]), (US["u1"], US["u1"] + 1.0)):
        s.rect(a_, z1, b_, z2 + 0.9, C["cream"], "#b9aa82")
        s.rect(a_, z2 + 0.75, b_, z2 + 0.9, cap)
    for uu in F["urns"]:
        s.rect(uu - 0.25, z2, uu + 0.25, z2 + 0.9, "#f2f2f0", "#9a9a96")
    if F.get("semi_basement_windows"):
        for uu in (31.5, 34.0, 38.5, 41.0):
            s.rect(uu, 0.5, uu + 1.4, 1.1, C["glass"], "#ffffff", 1)
    s.note((r0 + r1) / 2, level(9) + 1.8, wrap("Giữa lõm vào: dải kính chạy ngang suốt mỗi tầng"))
    s.note(f1 / 2, level(7), wrap("Đầu Tây: lam đứng màu nâu xám chạy suốt chiều cao, cửa sổ nhỏ"))
    s.note((g0 + g1) / 2, level(10), wrap("Đầu Đông: khối lưới cửa sổ; chân là khung xám + kính lớn"))
    s.note(15, CROWN + 0.2, wrap("Khung đỉnh rỗng: lam đứng, dầm trên cùng"))
    s.note((Cn["u0"] + Cn["u1"]) / 2, Cn["z"] + Cn["thick"] + 0.9, wrap("Mái đón dạng hộp dày, đua ra ~8,5 m che sàn xe, 2 cột tối"))
    s.note((LS["u0"] + LS["u1"]) / 2, z2 + 2.0, wrap("2 nấc: cầu thang giữa lên nấc 1 (+1,2), 7 bậc lên nấc 2 (+2,4) ở cửa; khung cửa đen, 2 bệ trắng"))
    s.note(T1["u1"] + 4, 2.6, wrap("Nấc 1 dưới mái đón; 2 làn xe cong 1/4 vòng hướng ra sân (~8 m)"))
    s.note((OT["u0"] + OT["u1"]) / 2, OT["z"] + 1.4, wrap("Chữ đỏ VĂN PHÒNG TUYỂN SINH trên kính"))
    return s.finish(os.path.join(OUT, "thap_mat_nam.png"))


def tower_frame_face(s, F, u_off, sign=True):
    """Tower face with the 3-storey grey frame podium (east and west)."""
    tw = F["width"]
    s.rect(0, 0, tw, ROOF, C["cream"])
    s.rect(0, 0, tw, level(2) - 0.3, C["cream"])
    for c in F["frame_cols"]:
        s.rect(max(0, c - 0.5), 0, min(tw, c + 0.5), level(4), C["grey_frame"])
    for zb in (level(2), level(3), level(4)):
        s.rect(0, zb - 0.4, tw, zb, C["grey_frame"])
    fc = F["frame_cols"]
    for a, b in zip(fc[:-1], fc[1:]):
        for n in (2, 3):
            glass_grid(s, a + 0.6, b - 0.6, level(n) + 0.2, level(n + 1) - 0.6, 1.1, C["glass_light"])
        for k in range(2):
            uu = a + 0.9 + k * 1.8
            s.rect(uu, 2.2, uu + 1.0, 2.8, C["glass"], "#ffffff", 1)
    s.rect(0, level(4), tw, level(5), C["grey_frame"])
    glass_grid(s, 0.6, tw - 0.6, level(4) + 0.8, level(5) - 0.8, 1.6, C["glass"])
    if sign:
        HS = F["hd_sign"]
        s.rect(HS["u"], HS["z"], HS["u"] + HS["w"], HS["z"] + HS["h"], "#2b5fa8", "#ffffff", 1)
        s.text(HS["u"] + HS["w"] / 2, HS["z"] + HS["h"] / 2, HS["text"], HS["h"] * 0.6, "#ffffff")
    nwin = F["windows_per_floor"]
    step = tw / nwin
    for n in range(5, NF + 1):
        for i in range(nwin):
            cu = (i + 0.5) * step
            s.rect(cu - 0.9, level(n) + 0.8, cu + 0.9, level(n) + 2.8, C["glass"], "#f0eee8", 1)
    for i in range(nwin + 1):
        s.rect(i * step - 0.2, level(5), i * step + 0.2, ROOF, C["fin"])
    crown(s, 0, tw)


# ===================================================================== whole complex – east (tower, link, hall)
def east():
    F = T["east"]; Lk = SPEC["link"]; Hf = SPEC["hall"]["front"]
    tw, lw, hw = F["width"], Lk["width"], Hf["width"]
    Wm = tw + lw + hw
    HH = SPEC["hall"]["height"]
    s = Sheet(Wm, CROWN + 1, "TÒA ĐIỀU HÀNH + HỘI TRƯỜNG – MẶT ĐÔNG",
              f"Tháp (trái) · khối nối · Hội trường (phải) · tỷ lệ theo mét · tháp {NF} tầng", LEVELS, ("Đỉnh khung", CROWN))
    tower_frame_face(s, F, 0.0, sign=True)
    # ---- link
    l0 = tw
    s.rect(l0, 0, l0 + lw, Lk["height"], C["cream"], "#b9aa82")
    v = Lk["vent"]
    s.rect(l0 + v[0], v[2], l0 + v[1], v[3], "#7d8287")
    z = v[2] + 0.2
    while z < v[3]:
        s.line(l0 + v[0], z, l0 + v[1], z, "#c9ccce", 1); z += 0.25
    d = Lk["door"]
    s.rect(l0 + d[0], 0, l0 + d[1], 2.6, "#e8eae8", "#6f7377", 2)
    # ---- hall front
    h0 = tw + lw
    s.rect(h0, 0, h0 + hw, HH, C["cream"])
    for pu in Hf["pilasters"]:
        s.rect(h0 + max(0, pu - 0.6), 0, h0 + min(hw, pu + 0.6), HH, C["grey_frame"])
    s.rect(h0, HH - 0.6, h0 + hw, HH, C["grey_frame"])
    for a, b in ((0.6, 3.4), (14.6, 17.4)):
        glass_grid(s, h0 + a, h0 + b, 3.8, 6.4, 1.4, C["glass"])
        glass_grid(s, h0 + a, h0 + b, 7.4, 9.9, 1.4, C["glass"])
        s.rect(h0 + a + 0.3, 1.6, h0 + a + 1.1, 2.1, "#f2f2f0", "#9a9a96")
    St = Hf["stairs"]
    s.rect(h0 + St["u0"], St["z_top"], h0 + St["u1"], 6.6, "#2f3c4a")                 # dark entrance hall
    s.rect(h0 + St["u0"] + 1.5, St["z_top"] + 0.6, h0 + St["u1"] - 1.5, 6.2, "#2c4f8a")  # banner inside
    hh = St["z_top"] / St["risers"]
    for k in range(St["risers"]):
        s.rect(h0 + St["u0"] - 0.6 + k * 0.05, k * hh, h0 + St["u1"] + 0.6 - k * 0.05, (k + 1) * hh, C["steps"], "#6f7377")
    for a in (St["u0"] - 1.4, St["u1"] + 0.6):
        s.rect(h0 + a, 0, h0 + a + 0.8, St["z_top"] + 0.6, C["cream"], "#b9aa82")      # stair cheek walls
    Cn = Hf["canopy"]
    s.rect(h0 + Cn["u0"], Cn["z"], h0 + Cn["u1"], Cn["z"] + 0.5, C["white_panel"], "#8c8f92")
    for tu in Hf.get("truss_cols", []):
        s.rect(h0 + tu - 0.35, 0, h0 + tu + 0.35, Cn["z"], None, "#6f7377", 2)
        z = 0.0
        while z < Cn["z"] - 0.5:
            s.line(h0 + tu - 0.35, z, h0 + tu + 0.35, z + 0.5, "#6f7377", 1); z += 0.5
    glass_grid(s, h0 + 4.6, h0 + 13.4, 7.5, 10.0, 1.1, C["glass"])
    P = Hf["pediment"]
    s.poly([(h0 + P["u0"], P["z0"]), (h0 + P["u0"], P["z0"] + 2.2), ((h0 + (P["u0"] + P["u1"]) / 2), P["apex"]),
            (h0 + P["u1"], P["z0"] + 2.2), (h0 + P["u1"], P["z0"])], C["grey_frame"])
    s.rect(h0 + P["u0"] + 0.5, P["z0"] + 0.1, h0 + P["u1"] - 0.5, P["z0"] + 2.0, C["white_panel"])
    TT = Hf["title_text"]
    s.text(h0 + (P["u0"] + P["u1"]) / 2, TT["z"], TT["text"], TT["h"], C["gold"])
    s.note(tw / 2, level(10), wrap("Tháp: lưới cửa sổ 7 ô/tầng, lam đứng tối"))
    s.note(tw / 2, level(3) + 1.6, wrap("Đế tháp: khung cột xám 3 tầng, kính lớn; chân tường kem cửa nhỏ"))
    HS = F["hd_sign"]
    s.note(HS["u"] + HS["w"] + 1.2, HS["z"] + 0.6, wrap("Biển HĐ"))
    s.note(l0 + lw / 2, Lk["height"] + 1.4, wrap("Khối nối 7 m: tường kem, ô lam thông gió, cửa đi"))
    s.note(h0 + (P["u0"] + P["u1"]) / 2, P["apex"] + 1.4, wrap("Trán tường Hội trường, chữ vàng HỘI TRƯỜNG"))
    s.note(h0 + St["u1"] + 1.4, 4.0, wrap("Cầu thang lớn 12 bậc lên tầng 2, mái đón công-xôn (không cột)"))
    s.note(h0 + 16, 8.6, wrap("Hai cánh: trụ xám, dải cửa kính 2 tầng"))
    return s.finish(os.path.join(OUT, "mat_dong_ca_cum.png"))


# ===================================================================== hall – north side
def hall_north():
    Hn = SPEC["hall"]["north"]; Wm = Hn["width"]; HH = SPEC["hall"]["height"]
    lv = [("Sân", 0.0), ("Tầng 2", 3.2), ("Mái", HH)]
    s = Sheet(Wm, HH + 3, "HỘI TRƯỜNG – MẶT BẮC (MẶT BÊN)", f'{Hn["title"]} · tỷ lệ theo mét', lv, None, scale=18)
    s.rect(0, 0, Wm, HH, C["cream"])
    s.rect(0, HH - 0.7, Wm, HH, C["grey_frame"])
    s.rect(0, 0, Wm, 0.35, C["cream_dark"])
    n = int(round(Wm / Hn["pilaster_step"]))
    for i in range(n):
        a, b = i * Hn["pilaster_step"], (i + 1) * Hn["pilaster_step"]
        if i >= 1:
            glass_grid(s, a + 1.3, b - 1.3, 4.0, 8.8, 1.2, C["glass"])
            s.rect(a + 1.3, 8.8, b - 1.3, 9.2, C["cream_dark"])
        s.rect(a + 1.6, 1.4, a + 2.4, 2.0, C["glass"], "#ffffff", 1)
        if i % 2 == 0:
            s.rect(b - 2.4, 1.0, b - 1.6, 1.6, "#f2f2f0", "#9a9a96")                     # AC unit
    for i in range(n + 1):
        u = i * Hn["pilaster_step"]
        s.rect(max(0, u - 0.6), 0, min(Wm, u + 0.6), HH, C["grey_frame"])
    s.note(Hn["pilaster_step"] * 0.5, 6.0, wrap("Đầu Đông: góc trán tường và mái đón (mặt tiền)"))
    s.note(Hn["pilaster_step"] * 3.5, 6.4, wrap("Trụ xám mỗi 5 m, giữa là cửa kính cao 2 tầng"))
    s.note(Hn["pilaster_step"] * 5.5, 1.7, wrap("Chân tường kem: cửa nhỏ, cục nóng điều hoà"))
    s.note(Wm - 3, HH + 0.9, wrap("Gờ mái xám chạy suốt"))
    return s.finish(os.path.join(OUT, "hoi_truong_mat_bac.png"))


# ===================================================================== tower – north (towards the hall)
def north():
    F = T["north"]; Wm = F["width"]; Lk = SPEC["link"]
    s = Sheet(Wm, CROWN + 1, "TÒA ĐIỀU HÀNH – MẶT BẮC", f'{F["title"]} · tỷ lệ theo mét · {NF} tầng', LEVELS, ("Đỉnh khung", CROWN))
    s.rect(0, 0, Wm, ROOF, C["cream"])
    fz0 = Wm - F["fin_zone_from_right"]
    s.rect(0, level(3), fz0, ROOF, C["cream_dark"])
    for n in range(3, NF + 1):
        glass_grid(s, 0.4, fz0 - 0.3, level(n) + 0.9, level(n) + 2.7, 1.2, C["glass_light"])
    for n in (1, 2):
        u = 9.0
        while u + 1.6 < fz0:
            s.rect(u, level(n) + 1.0, u + 1.6, level(n) + 2.8, C["glass"], "#f0eee8", 1); u += 2.6
    for n in range(1, NF + 1):
        u = fz0 + 0.75
        while u < Wm:
            s.rect(u - 0.4, level(n) + 1.0, u + 0.4, level(n) + 2.6, C["glass"]); u += 1.5
    u = fz0
    while u <= Wm + 1e-6:
        s.rect(u - 0.25, 0, u + 0.25, CROWN, "#7d8287"); u += 1.5
    for uu in (10.0, 14.0, 18.0, 22.0, 26.0):
        s.rect(uu, 0.6, uu + 1.4, 1.2, C["glass"], "#ffffff", 1)
    s.rect(0, 0, Lk["width"], Lk["height"], C["cream"], "#b9aa82")                 # link block (east end)
    for z0 in (3.0, 7.0):
        s.rect(1.5, z0, 5.5, z0 + 1.8, C["glass"], "#f0eee8", 1)
    crown(s, 0, Wm)
    s.note(fz0 / 2, level(9) + 1.8, wrap("Dải kính chạy ngang suốt mỗi tầng (như phần giữa mặt Nam)"))
    s.note(fz0 + 4.5, level(7), wrap("Đầu Tây: lam đứng xám"))
    s.note(Lk["width"] / 2, Lk["height"] + 1.4, wrap("Khối nối sang Hội trường"))
    s.note(Wm / 2, CROWN + 0.2, wrap("Khung đỉnh rỗng chạy suốt"))
    return s.finish(os.path.join(OUT, "thap_mat_bac.png"))


# ===================================================================== tower – west (like the east face)
def west():
    F = T["east"]
    s = Sheet(F["width"], CROWN + 1, "TÒA ĐIỀU HÀNH – MẶT TÂY", f'{T["west"]["title"]} · như mặt Đông, không biển HĐ · tỷ lệ theo mét',
              LEVELS, ("Đỉnh khung", CROWN))
    tower_frame_face(s, F, 0.0, sign=False)
    s.note(F["width"] / 2, level(10), wrap("Như phần tháp ở mặt Đông: lưới cửa sổ 7 ô/tầng, lam đứng"))
    s.note(F["width"] / 2, level(3) + 1.6, wrap("Đế: khung cột xám 3 tầng, kính lớn"))
    return s.finish(os.path.join(OUT, "thap_mat_tay.png"))


# ===================================================================== hall – west (solid wall)
def hall_west():
    Hw = SPEC["hall"]["west"]; Wm = Hw["width"]; HH = SPEC["hall"]["height"]
    s = Sheet(Wm, HH + 3, "HỘI TRƯỜNG – MẶT TÂY", f'{Hw["title"]} · tường đặc · tỷ lệ theo mét', [("Sân", 0.0), ("Mái", HH)], None, scale=18)
    s.rect(0, 0, Wm, HH, C["cream"])
    s.rect(0, 0, Wm, 0.35, C["cream_dark"])
    s.rect(0, HH - 0.7, Wm, HH, C["grey_frame"])
    for u in (0.0, Wm):
        s.rect(max(0, u - 0.6), 0, min(Wm, u + 0.6), HH, C["grey_frame"])
    s.note(Wm / 2, HH / 2, wrap("Tường đặc màu kem, trụ xám hai góc, gờ mái xám"))
    return s.finish(os.path.join(OUT, "hoi_truong_mat_tay.png"))


def overview(images, path, cols=2, sc=0.5):
    from PIL import Image
    ims = [im.resize((int(im.width * sc), int(im.height * sc))) for im in images]
    rows = [ims[i:i + cols] for i in range(0, len(ims), cols)]
    W = max(sum(i.width for i in r) + 20 * (len(r) - 1) for r in rows)
    H = sum(max(i.height for i in r) for r in rows) + 20 * (len(rows) - 1)
    sheet = Image.new("RGB", (W, H), "#ffffff")
    y = 0
    for r in rows:
        x = 0
        for im in r:
            sheet.paste(im, (x, y)); x += im.width + 20
        y += max(i.height for i in r) + 20
    sheet.save(path)


a = south(); b = east(); c = hall_north()
n_ = north(); w_ = west(); hw_ = hall_west()
overview([a, n_, w_], os.path.join(OUT, "tong_hop_thap.png"), cols=3)
overview([b, c, hw_], os.path.join(OUT, "tong_hop_hoi_truong_va_mat_dong.png"), cols=3)
side_by_side(os.path.join(ROOT, T["north"]["photo"]), n_, os.path.join(OUT, "so_sanh_thap_mat_bac.png"))
side_by_side(os.path.join(ROOT, T["south"]["photo"]), a, os.path.join(OUT, "so_sanh_thap_mat_nam.png"))
side_by_side(os.path.join(ROOT, SPEC["hall"]["front"]["photo"]), b, os.path.join(OUT, "so_sanh_mat_dong_ca_cum.png"))
side_by_side(os.path.join(ROOT, SPEC["hall"]["north"]["photo"]), c, os.path.join(OUT, "so_sanh_hoi_truong_mat_bac.png"))
print("ok roof", round(ROOF, 1), "crown", round(CROWN, 1))
