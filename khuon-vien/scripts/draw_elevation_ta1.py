"""B2 – scaled elevation drawings for TA1, read from layout/buildings/ta1.json.
Outputs in 02_toa_nha/ta1/: mat_dung_bac.png, mat_dung_dong.png, so_sanh_anh.png
Usage: python3 scripts/draw_elevation_ta1.py
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "ta1.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "02_toa_nha", "ta1")
os.makedirs(OUT, exist_ok=True)
C = SPEC["colors"]
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
def f(s, b=False): return ImageFont.truetype(FONT_B if b else FONT, s)

S = 18                                   # px per metre
NF, PL, GH, FH, PH = SPEC["floors"], SPEC["plinth_h"], SPEC["ground_h"], SPEC["floor_h"], SPEC["parapet_h"]
def level(n):                            # floor n (1-based) finished level
    return PL if n == 1 else PL + GH + (n - 2) * FH
ROOF = level(NF + 1)
TOP = ROOF + PH


class Sheet:
    def __init__(self, width_m, title, sub, mirror=False):
        self.mirror = mirror
        self.ML, self.MR, self.MT, self.MB = 120, 440, 110, 120
        self.w_m = width_m
        self.W = int(width_m * S) + self.ML + self.MR
        self.H = int((TOP + 3) * S) + self.MT + self.MB
        self.GY = self.H - self.MB
        self.im = Image.new("RGB", (self.W, self.H), "#ffffff")
        self.d = ImageDraw.Draw(self.im)
        self.d.text((self.ML, 30), title, font=f(26, True), fill="#222")
        self.d.text((self.ML, 68), sub, font=f(15), fill="#6c665c")
        self.notes = []

    def X(self, u): return self.ML + ((self.w_m - u) if self.mirror else u) * S
    def Y(self, z): return self.GY - z * S

    def rect(self, u0, z0, u1, z1, fill, outline=None, width=1):
        xa, xb = sorted((self.X(u0), self.X(u1)))
        self.d.rectangle([xa, self.Y(z1), xb, self.Y(z0)], fill=fill, outline=outline, width=width)

    def poly(self, pts, fill, outline=None):
        self.d.polygon([(self.X(u), self.Y(z)) for u, z in pts], fill=fill, outline=outline)

    def line(self, u0, z0, u1, z1, fill, width=1):
        self.d.line([(self.X(u0), self.Y(z0)), (self.X(u1), self.Y(z1))], fill=fill, width=width)

    def note(self, u, z, text):
        n = len(self.notes) + 1
        x, y = self.X(u), self.Y(z)
        self.d.ellipse([x - 13, y - 13, x + 13, y + 13], fill="#c0392b", outline="#fff", width=2)
        self.d.text((x, y), str(n), font=f(14, True), fill="#fff", anchor="mm")
        self.notes.append(text)

    def finish(self, path):
        d = self.d
        # ground line
        R = self.ML + self.w_m * S
        d.line([(self.ML - 40, self.GY), (R + 40, self.GY)], fill="#222", width=3)
        # level markers
        lx = R + 18
        for n in range(1, NF + 2):
            z = level(n)
            d.line([(lx, self.Y(z)), (lx + 14, self.Y(z))], fill="#888")
            lab = "Mái" if n == NF + 1 else f"T{n}"
            d.text((lx + 20, self.Y(z)), f"{lab}  +{z:.1f}", font=f(12), fill="#555", anchor="lm")
        d.text((lx + 20, self.Y(TOP)), f"Đỉnh  +{TOP:.1f}", font=f(12, True), fill="#333", anchor="lm")
        # width dimension
        y = self.GY + 34
        d.line([(self.ML, y), (R, y)], fill="#444", width=1)
        for x in (self.ML, R):
            d.line([(x, y - 7), (x, y + 7)], fill="#444", width=2)
        d.text(((self.ML + R) / 2, y + 16), f"{self.w_m:.1f} m", font=f(14, True), fill="#333", anchor="mm")
        # scale bar
        sx, sy = self.ML, self.GY + 72
        for i in range(5):
            d.rectangle([sx + i * 2 * S, sy, sx + (i + 1) * 2 * S, sy + 8], fill="#222" if i % 2 == 0 else "#fff", outline="#222")
        d.text((sx, sy + 14), "0", font=f(12), fill="#333", anchor="mt")
        d.text((sx + 10 * S, sy + 14), "10 m", font=f(12), fill="#333", anchor="mt")
        # 1.7 m person for scale
        px = R - 1.0 * S
        d.ellipse([px - 4, self.Y(1.7), px + 4, self.Y(1.7) + 8], fill="#2c6bd1")
        d.rectangle([px - 4, self.Y(1.45), px + 4, self.GY], fill="#2c6bd1")
        # notes
        nx, ny = R + 140, self.MT + 10
        d.text((nx, ny), "Ghi chú", font=f(17, True), fill="#222")
        for i, t in enumerate(self.notes):
            yy = ny + 36 + i * 68
            d.ellipse([nx, yy, nx + 22, yy + 22], fill="#c0392b")
            d.text((nx + 11, yy + 11), str(i + 1), font=f(12, True), fill="#fff", anchor="mm")
            d.multiline_text((nx + 32, yy + 1), t, font=f(13), fill="#333", spacing=3)
        self.im.save(path)
        return self.im


def wrap(t, n=26):
    words, lines, cur = t.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return "\n".join(lines + [cur])


# ===================================================================== north (main entrance)
def north():
    F = SPEC["faces"]["north"]
    Wm = F["width"]
    s = Sheet(Wm, "TA1 – MẶT ĐỨNG SẢNH CHÍNH", f'{F["title"]} · tỷ lệ theo mét · {NF} tầng')
    bay = Wm / F["bays"]
    left_w = F["left_zone_bays"] * bay
    # main wall
    s.rect(0, 0, Wm, ROOF, C["wall_main"])
    # plinth
    s.rect(0, 0, Wm, PL, C["steps"])
    # floor slab edges from grid floor
    for n in range(2, NF + 2):
        s.rect(0, level(n) - 0.15, Wm, level(n) + 0.1, C["slab"])
    # bays: louvers + windows
    for n in range(1, NF + 1):
        z0, z1 = level(n), level(n + 1)
        for b in range(F["bays"]):
            u0, u1 = b * bay, (b + 1) * bay
            in_left = u1 <= left_w + 1e-6
            start = F["left_zone_floors"] + 1 if in_left else F["grid_start_floor"]
            if n >= start:
                lw = (u1 - u0) * 0.66
                lu0 = u0 + F["fin_w"] / 2 + 0.12
                s.rect(lu0, z0 + 0.5, lu0 + lw, z1 - 0.7, C["louver"])
                k = z0 + 0.62
                while k < z1 - 0.75:
                    s.line(lu0, k, lu0 + lw, k, "#7c858e"); k += 0.16
                s.rect(lu0 + lw + 0.15, z0 + 0.9, u1 - F["fin_w"] / 2 - 0.12, z1 - 0.6, C["window"])
            elif in_left and n <= F["left_zone_floors"]:
                if n < F["left_zone_floors"] and b % 2 == 0:
                    cu = (u0 + u1) / 2 + bay / 2
                    s.rect(cu - 0.8, z0 + 1.2, cu + 0.8, z0 + 2.3, C["window"], "#d0d4d8", 2)
                    for k in range(1, 5):
                        s.line(cu - 0.8, z0 + 1.2 + k * 0.22, cu + 0.8, z0 + 1.2 + k * 0.22, "#58616a")
                if n == F["left_zone_floors"]:
                    cu = (u0 + u1) / 2
                    s.rect(cu - 0.45, z1 - 1.2, cu + 0.45, z1 - 0.6, "#e7e9eb", "#9aa1a8")
            elif not in_left and n == 2:
                cu = (u0 + u1) / 2
                s.rect(cu - 0.45, z0 + 1.3, cu + 0.45, z0 + 2.3, C["window"])
    # left zone: flat panels with thick pilasters on the lower floors
    zt = level(F["left_zone_floors"] + 1)
    for b in range(0, F["left_zone_bays"] + 1, 2):
        u = b * bay
        s.rect(u - 0.45, 0, u + 0.45, zt, C["fin"], "#9aa3ac")
    # fins (full height above the left zone / entrance)
    for i in range(F["bays"] + 1):
        u = i * bay
        z0 = zt if u <= left_w + 1e-6 else level(2)    # left zone: thick pilasters below, fins above
        s.rect(u - F["fin_w"] / 2, z0, u + F["fin_w"] / 2, TOP, C["fin"], "#9aa3ac")
    # parapet
    s.rect(0, ROOF, Wm, TOP, C["fin"], "#9aa3ac")
    # entrance: recessed lobby + glass doors
    E = F["entrance"]
    s.rect(E["u0"], PL, E["u1"], level(2) - 0.15, "#c5cbd0")
    for g0, g1 in E["door_groups"]:
        s.rect(g0, PL, g1, PL + E["door_h"], C["glass"], "#1d252c", 2)
        u = g0
        while u < g1 - 0.1:
            s.line(u, PL, u, PL + E["door_h"], "#1d252c", 2); u += 1.25
        s.line(g0, PL + 2.4, g1, PL + 2.4, "#1d252c", 2)
    # canopy
    Cn = F["canopy"]
    s.rect(Cn["u0"], Cn["z"], Cn["u1"], Cn["z"] + 0.28, "#d8dde1", "#7d868e", 2)
    for u in (Cn["u0"] + 1.5, (Cn["u0"] + Cn["u1"]) / 2, Cn["u1"] - 1.5):
        s.line(u, Cn["z"] + 0.28, u - 1.0, Cn["z"] + 1.6, "#7d868e", 2)
    # steps
    St = F["steps"]
    for k in range(St["risers"]):
        inset = k * 0.35
        s.rect(St["u0"] + inset, k * PL / St["risers"], St["u1"] - inset, (k + 1) * PL / St["risers"], "#9a9ea2", "#6f7377")
    # ramp + stainless railing
    R = F["ramp"]
    s.poly([(R["u0"], 0), (R["u1"], 0), (R["u1"], PL), (R["u0"], 0.05)], C["brick"])
    s.line(R["u0"], R["rail_h"], R["u1"], PL + R["rail_h"], C["rail"], 3)
    u = R["u0"]
    while u <= R["u1"]:
        zr = (u - R["u0"]) / (R["u1"] - R["u0"]) * PL
        s.line(u, zr, u, zr + R["rail_h"], C["rail"], 1); u += 0.25
    # notes
    s.note(Wm * 0.75, level(6) + 1.5, wrap("Lưới cột đứng + lam ngang che cục nóng điều hoà, 13 ô mỗi tầng"))
    s.note(left_w / 2, level(2) + 1.8, wrap("Khối thấp bên trái: tường phẳng, trụ dày, cửa sổ nhỏ có song"))
    s.note((E["u0"] + E["u1"]) / 2, level(2) + 1.2, wrap("Tầng 2 phía sảnh: hàng ô cửa vuông nhỏ"))
    s.note(Cn["u1"] - 2, Cn["z"] + 0.9, wrap("Mái kính đón sảnh, đua ra khoảng 3 m"))
    s.note((E["u0"] + E["u1"]) / 2, PL + 1.6, wrap("Sảnh chính: 2 cụm cửa kính khung đen"))
    s.note(R["u0"] + 4, 1.6, wrap("Dốc xe lăn lát gạch đỏ + lan can inox"))
    return s.finish(os.path.join(OUT, "mat_dung_bac.png"))


# ===================================================================== east (facing the gate)
def east():
    F = SPEC["faces"]["east"]
    Wm = F["width"]
    s = Sheet(Wm, "TA1 – MẶT ĐỨNG GIÁP CỔNG", f'{F["title"]} · tỷ lệ theo mét · {NF} tầng')
    s.rect(0, 0, Wm, TOP, C["wall_white"])
    # panel joints
    for u in F["panel_joints_u"]:
        s.line(u, level(2), u, TOP, C["wall_white_shade"], 2)
    for n in (2, 5, 8, NF + 1):
        s.line(0, level(n), Wm, level(n), C["wall_white_shade"], 2)
    s.rect(0, ROOF, Wm, TOP, "#dcdedd", C["wall_white_shade"])
    # ground floor under the band: recessed shade
    B = F["band_floor2"]
    s.rect(B["u0"], 0, B["u1"], level(2), "#c4c7c7")
    s.rect(B["u0"] + 0.2, 0, B["u0"] + 0.6, level(2), "#d6d8d7")       # column
    s.rect(B["u1"] - 0.6, 0, B["u1"] - 0.2, level(2), "#d6d8d7")
    # floor-2 band (cantilevered balcony with slotted parapet)
    z0 = level(2)
    s.rect(B["u0"], z0 - 0.4, B["u1"], level(3), "#7d8284")                 # recess behind the parapet
    s.rect(B["u0"], z0 - 0.4, B["u1"], z0 + B["parapet_h"], "#cfd2d1", "#a9adad", 2)
    slot_u = [B["u0"] + 1.2 + i * 0.7 for i in range(B["slots"] // 2)] + \
             [B["u1"] - 1.4 - i * 0.7 for i in range(B["slots"] - B["slots"] // 2)]
    for u in slot_u:
        s.rect(u, z0 + 0.3, u + 0.28, z0 + B["parapet_h"] - 0.25, C["opening"])
    s.rect(B["u0"] + 4.2, z0 + 0.3, B["u0"] + 6.2, z0 + B["parapet_h"] - 0.25, C["opening"])
    s.rect(B["u0"], level(3) - 0.35, B["u1"], level(3), "#d6d8d7")
    # stair/balcony core
    K = F["core"]
    s.rect(K["u0"], level(K["from_floor"]) - 0.4, K["u1"], TOP + K["top_extra"], "#c9cccc", "#a3a7a7", 2)
    for n in range(K["from_floor"], NF + 1):
        a, b = level(n), level(n + 1)
        s.rect(K["u0"] + 0.45, a + K["parapet_h"], K["u1"] - 0.45, b - 0.35, C["opening"])
        s.rect(K["u0"] + 0.45, a + K["parapet_h"], K["u1"] - 0.45, a + K["parapet_h"] + 0.5, "#4b5052")
    s.rect(K["u0"] + 0.45, ROOF + 0.2, K["u1"] - 0.45, TOP + K["top_extra"] - 0.4, "#9ea3a4")
    # entrance
    E = F["entrance"]
    s.rect(E["glass"][0], PL, E["glass"][1], PL + E["h"], C["glass"], "#1d252c", 2)
    s.line((E["glass"][0] + E["glass"][1]) / 2, PL, (E["glass"][0] + E["glass"][1]) / 2, PL + E["h"], "#1d252c", 2)
    s.rect(E["door"][0], PL, E["door"][1], PL + E["h"] - 0.2, "#f2f2f0", "#8a8f90", 2)
    s.rect(E["door"][0] + 0.2, PL + 1.6, E["door"][1] - 0.2, PL + 2.1, C["glass"])
    St = F["steps"]
    for k in range(St["risers"]):
        inset = k * 0.3
        s.rect(St["u0"] + inset, k * PL / St["risers"], St["u1"] - inset, (k + 1) * PL / St["risers"], "#9a9ea2", "#6f7377")
    # external stair up to the floor-2 balcony
    X = F["ext_stair"]
    zt = level(2) - 0.4
    s.poly([(X["u_bottom"], 0), (X["u_top"], zt), (X["u_top"], zt + X["wall_h"]), (X["u_bottom"], X["wall_h"])], "#e1e3e2", "#9da1a1")
    s.line(X["u_bottom"], 0, X["u_top"], zt, "#9da1a1", 2)
    # TA1 sign
    G = F["sign"]
    s.rect(G["u"], G["z"], G["u"] + G["w"], G["z"] + G["h"], C["sign_blue"], "#ffffff", 2)
    s.d.text((s.X(G["u"] + G["w"] / 2), s.Y(G["z"] + G["h"] / 2)), G["text"], font=f(int(G["h"] * S * 0.6), True), fill="#fff", anchor="mm")
    # notice board with red tile roof
    N = F["notice_board"]
    s.rect(N["u0"], N["z0"], N["u1"], N["z1"], C["board"], "#9a9a96", 2)
    s.poly([(N["u0"] - 0.3, N["z1"]), (N["u1"] + 0.3, N["z1"]), (N["u1"], N["z1"] + N["roof_h"]), (N["u0"], N["z1"] + N["roof_h"])], C["tile_red"])
    for i in range(6):
        u = N["u0"] + 0.6 + i * 1.5
        s.rect(u, N["z0"] + 0.5, u + 1.0, N["z0"] + 1.6, "#ffffff", "#cfcfca")
    s.rect(F["brick_strip"]["u0"], -0.05, F["brick_strip"]["u1"], 0.05, C["brick"])
    s.note(K["u1"] + 1.0, level(7), wrap("Lõi cầu thang / ban công mở, nhô khỏi mặt tường, cao vượt mái"))
    s.note(B["u0"] + 2.5, level(2) + 2.6, wrap("Ban công tầng 2 đua ra, lan can đặc có khe đứng"))
    s.note(X["u_top"] + 2.0, 3.5, wrap("Cầu thang ngoài lên tầng 2"))
    s.note((E["glass"][0] + E["door"][1]) / 2, PL + 3.6, wrap("Lối vào phụ: cửa kính + cửa trắng, 4 bậc"))
    s.note(G["u"] + G["w"] + 1.0, G["z"] + 0.3, wrap("Biển TA1 màu xanh"))
    s.note(N["u1"] - 1.0, N["z1"] + 1.4, wrap("Bảng tin có mái ngói đỏ"))
    s.note(Wm - 4, level(6), wrap("Tường bê tông sáng, đường ron chia mảng"))
    return s.finish(os.path.join(OUT, "mat_dung_dong.png"))


# ===================================================================== west (facing TA2)
def west():
    F = dict(SPEC["faces"]["east"]); Wf = SPEC["faces"]["west"]
    Wm = F["width"]
    s = Sheet(Wm, "TA1 – MẶT ĐỨNG TÂY", f'{Wf["title"]} · tỷ lệ theo mét · {NF} tầng', mirror=Wf["mirror"])
    s.rect(0, 0, Wm, TOP, C["wall_white"])
    for u in F["panel_joints_u"]:
        s.line(u, level(2), u, TOP, C["wall_white_shade"], 2)
    for n in (2, 5, 8, NF + 1):
        s.line(0, level(n), Wm, level(n), C["wall_white_shade"], 2)
    s.rect(0, ROOF, Wm, TOP, "#dcdedd", C["wall_white_shade"])
    s.rect(0, 0, Wm, PL, "#c4c7c7")

    def window(u0, u1, z0, z1):
        s.rect(u0, z0, u1, z1, C["glass"], "#e9ebea", 3)
        n = max(1, round((u1 - u0) / 1.2))
        for i in range(1, n):
            uu = u0 + (u1 - u0) * i / n
            s.line(uu, z0, uu, z1, "#1d252c", 2)
        s.rect(u0 - 0.15, z0 - 0.12, u1 + 0.15, z0, "#e9ebea")          # sill
    # former floor-2 balcony band and the ground floor under it: rows of windows
    B = F["band_floor2"]
    K = F["core"]
    for n in (1, 2):
        z0 = level(n) + Wf["window_sill"]
        for u0 in (B["u0"] + 1.0, B["u0"] + 4.2):
            window(u0, u0 + 2.4, z0, z0 + Wf["window_h"])
    # core: same projecting frame, every level glazed instead of open balconies
    s.rect(K["u0"], level(2) - 0.4, K["u1"], TOP + K["top_extra"], "#c9cccc", "#a3a7a7", 2)
    for n in range(2, NF + 1):
        z0 = level(n) + Wf["window_sill"]
        window(K["u0"] + 0.8, K["u1"] - 0.8, z0, z0 + Wf["window_h"])
    s.rect(K["u0"] + 0.45, ROOF + 0.2, K["u1"] - 0.45, TOP + K["top_extra"] - 0.4, "#b4b8b9")
    # side entrance kept under the core
    E = F["entrance"]
    s.rect(E["glass"][0], PL, E["glass"][1], PL + E["h"], C["glass"], "#1d252c", 2)
    s.line((E["glass"][0] + E["glass"][1]) / 2, PL, (E["glass"][0] + E["glass"][1]) / 2, PL + E["h"], "#1d252c", 2)
    s.rect(E["door"][0], PL, E["door"][1], PL + E["h"] - 0.2, "#f2f2f0", "#8a8f90", 2)
    St = F["steps"]
    for k in range(St["risers"]):
        inset = k * 0.3
        s.rect(St["u0"] + inset, k * PL / St["risers"], St["u1"] - inset, (k + 1) * PL / St["risers"], "#9a9ea2", "#6f7377")
    s.note((K["u0"] + K["u1"]) / 2, level(6) + 2.6, wrap("Lõi nhô ra như mặt giáp cổng, nhưng mỗi tầng là cửa sổ thay cho ban công mở"))
    s.note(B["u0"] + 3.5, level(2) + 2.9, wrap("Chỗ ban công tầng 2 → hàng cửa sổ (tầng 1 và tầng 2)"))
    s.note((E["glass"][0] + E["door"][1]) / 2, PL + 3.4, wrap("Lối vào phụ giữ nguyên, không có cầu thang ngoài"))
    s.note(Wm - 5, level(6), wrap("Tường bê tông sáng, đường ron chia mảng"))
    return s.finish(os.path.join(OUT, "mat_dung_tay.png"))


# ===================================================================== south (facing Nhà xe)
def south():
    F = SPEC["faces"]["north"]; Sf = SPEC["faces"]["south"]
    Wm = F["width"]
    s = Sheet(Wm, "TA1 – MẶT ĐỨNG NAM", f'{Sf["title"]} · tỷ lệ theo mét · {NF} tầng', mirror=True)
    bay = Wm / F["bays"]
    s.rect(0, 0, Wm, ROOF, C["wall_main"])
    s.rect(0, 0, Wm, PL, C["steps"])
    for n in range(2, NF + 2):
        s.rect(0, level(n) - 0.12, Wm, level(n) + 0.08, C["slab"])
    for n in range(1, NF + 1):
        z0 = level(n) + Sf["window_sill"] + (0.4 if n == 1 else 0)
        for b in range(F["bays"]):
            cu = (b + 0.5) * bay
            s.rect(cu - Sf["window_w"] / 2, z0, cu + Sf["window_w"] / 2, z0 + Sf["window_h"], C["window"], "#c9d0d6", 2)
            s.line(cu, z0, cu, z0 + Sf["window_h"], "#53606b", 2)
            s.rect(cu - Sf["window_w"] / 2 - 0.12, z0 - 0.1, cu + Sf["window_w"] / 2 + 0.12, z0, "#c9d0d6")
    s.rect(0, ROOF, Wm, TOP, C["fin"], "#9aa3ac")
    s.note(Wm * 0.5, level(6) + 2.9, wrap("Tường phẳng, cửa sổ thẳng hàng với 13 ô của mặt sảnh chính"))
    s.note(Wm * 0.2, level(1) + 3.3, wrap("Không có cửa ra vào, không lam, không mái kính"))
    s.note(Wm * 0.85, ROOF + 0.6, wrap("Tường chắn mái cao 1,2 m như các mặt khác"))
    return s.finish(os.path.join(OUT, "mat_dung_nam.png"))


def overview(images, path):
    h = max(im.height for im in images)
    scale = 0.5
    ims = [im.resize((int(im.width * scale), int(im.height * scale))) for im in images]
    W = sum(i.width for i in ims[:2]) + 20; H = max(i.height for i in ims[:2]) + max(i.height for i in ims[2:]) + 20
    sheet = Image.new("RGB", (W, H), "#ffffff")
    sheet.paste(ims[0], (0, 0)); sheet.paste(ims[1], (ims[0].width + 20, 0))
    y = max(i.height for i in ims[:2]) + 20
    sheet.paste(ims[2], (0, y)); sheet.paste(ims[3], (ims[2].width + 20, y))
    sheet.save(path)


def side_by_side(photo_rel, elev, out_name):
    ph = Image.open(os.path.join(ROOT, photo_rel)).convert("RGB")
    h = elev.height
    ph = ph.resize((int(ph.width * h / ph.height), h))
    sheet = Image.new("RGB", (ph.width + 30 + elev.width, h), "#ffffff")
    sheet.paste(ph, (0, 0)); sheet.paste(elev, (ph.width + 30, 0))
    sheet.save(os.path.join(OUT, out_name))


n_im = north()
e_im = east()
side_by_side(SPEC["faces"]["north"]["photo"], n_im, "so_sanh_mat_bac.png")
side_by_side(SPEC["faces"]["east"]["photo"], e_im, "so_sanh_mat_dong.png")
w_im = west()
s_im = south()
overview([n_im, e_im, s_im, w_im], os.path.join(OUT, "tong_hop_4_mat.png"))
print("ok", n_im.size, e_im.size, w_im.size, s_im.size)
