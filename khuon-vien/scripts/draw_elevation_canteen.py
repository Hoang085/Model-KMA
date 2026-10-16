"""B2 – Canteen elevations + tennis court plan/elevation, read from layout/buildings/canteen.json.
Outputs in 02_toa_nha/canteen/. Usage: python3 scripts/draw_elevation_canteen.py
"""
import json, math, os
from PIL import Image, ImageDraw
from elev_lib import Sheet, wrap, side_by_side, font

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(ROOT, "layout", "buildings", "canteen.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "02_toa_nha", "canteen")
os.makedirs(OUT, exist_ok=True)
C, K, T = SPEC["colors"], SPEC["canteen"], SPEC["tennis"]
LV = K["levels"]
F1 = LV["plinth"]
F2 = F1 + LV["f1_h"]
F3 = F2 + LV["f2_h"]
EAVE = F3 + LV["f3_h"]
RIDGE = EAVE + K["roof"]["rise"]
OV = K["roof"]["overhang"]
X0, Y0, X1, Y1 = K["rect"]
LEN, DEP = X1 - X0, Y1 - Y0
AX0, AY0, AX1, AY1 = K["annex"]["rect"]
LEVELS = [("T1", F1), ("T2", F2), ("T3", F3), ("Diềm mái", EAVE), ("Nóc", RIDGE)]
BD = K["balcony"]


def arch_window(s, cu, z0, w, h):
    r = w / 2
    zs = z0 + h - r
    pts = [(cu - r, z0), (cu + r, z0), (cu + r, zs)] + \
          [(cu + r * math.cos(a), zs + r * math.sin(a)) for a in [math.pi * k / 12 for k in range(1, 12)]] + [(cu - r, zs)]
    o = 0.12
    s.poly([(cu - r - o, z0 - o), (cu + r + o, z0 - o), (cu + r + o, zs)] +
           [(cu + (r + o) * math.cos(a), zs + (r + o) * math.sin(a)) for a in [math.pi * k / 12 for k in range(1, 12)]] +
           [(cu - r - o, zs)], C["white_frame"])
    s.poly(pts, C["glass"])
    s.line(cu, z0, cu, zs + r, C["white_frame"], 2)
    s.line(cu - r, zs, cu + r, zs, C["white_frame"], 2)
    s.line(cu - r, z0 + (zs - z0) / 2, cu + r, z0 + (zs - z0) / 2, C["white_frame"], 1)


def rect_window(s, u0, u1, z0, z1):
    s.rect(u0, z0, u1, z1, C["glass"], C["white_frame"], 2)
    s.line((u0 + u1) / 2, z0, (u0 + u1) / 2, z1, C["white_frame"], 1)


def front_face(s, u0, u1, bays):
    """Arcaded face with the two balcony bands (south and west)."""
    s.rect(u0, 0, u1, EAVE, C["yellow"], C["yellow_dark"])
    s.rect(u0, 0, u1, F1, C["plinth"])
    step = (u1 - u0) / bays
    for i in range(bays):
        cu = u0 + step * (i + 0.5)
        arch_window(s, cu, F1 + 0.3, K["arch"]["w"], K["arch"]["h"])
        rect_window(s, cu - 0.8, cu + 0.8, F2 + 1.15, F2 + 2.7)
        rect_window(s, cu - 0.8, cu + 0.8, F3 + 0.3, F3 + 2.5)
    b0, b1 = K["band"]
    s.rect(u0, b0, u1, b1, C["stone_band"])
    for k in range(int((u1 - u0) / 0.6)):
        s.line(u0 + k * 0.6, b0, u0 + k * 0.6, b1, "#6a6d71", 1)
    s.rect(u0, F2, u1, F2 + BD["f2_parapet_h"], C["yellow"], C["yellow_dark"], 2)       # solid balcony parapet
    s.rect(u0, F3 - 0.3, u1, F3, C["yellow"], C["yellow_dark"])                          # F3 balcony slab edge
    s.rect(u0, F3 + BD["f3_rail_h"] - 0.06, u1, F3 + BD["f3_rail_h"], C["rail"])
    u = u0
    while u <= u1:
        s.line(u, F3, u, F3 + BD["f3_rail_h"], C["rail"], 1); u += 0.15
    s.rect(u0 - OV, EAVE - 0.3, u1 + OV, EAVE, C["yellow_dark"])


def plain_face(s, u0, u1, n):
    s.rect(u0, 0, u1, EAVE, C["yellow"], C["yellow_dark"])
    s.rect(u0, 0, u1, F1, C["plinth"])
    step = (u1 - u0) / n
    for z in (F1 + 1.0, F2 + 1.0, F3 + 1.0):
        for i in range(n):
            cu = u0 + step * (i + 0.5)
            rect_window(s, cu - 0.65, cu + 0.65, z, z + 1.5)
    s.rect(u0, F2 - 0.15, u1, F2 + 0.15, C["yellow_dark"])
    s.rect(u0 - OV, EAVE - 0.3, u1 + OV, EAVE, C["yellow_dark"])


def roof_long(s, u0, u1):
    hw = DEP / 2 + OV
    s.poly([(u0 - OV, EAVE), (u1 + OV, EAVE), (u1 + OV - hw, RIDGE), (u0 - OV + hw, RIDGE)], C["roof_tile"], "#7a2c25")


def roof_end(s, u0, u1):
    s.poly([(u0 - OV, EAVE), (u1 + OV, EAVE), ((u0 + u1) / 2, RIDGE)], C["roof_tile"], "#7a2c25")


def annex(s, u0, u1, shutters=True):
    h = K["annex"]["h"]
    s.rect(u0, 0, u1, h, C["annex"], "#4f826b")
    s.rect(u0 - 0.2, h, u1 + 0.2, h + 0.25, "#cfd2d4")
    if shutters:
        n = K["annex"]["shutters"]
        w = (u1 - u0) / n
        for i in range(n):
            a, b = u0 + i * w + 0.25, u0 + (i + 1) * w - 0.25
            s.rect(a, 0, b, h - 0.5, C["annex_shutter"], "#4f826b")
            z = 0.2
            while z < h - 0.5:
                s.line(a, z, b, z, "#7aa892", 1); z += 0.25


def south():
    W = AX1 - X0
    s = Sheet(W, RIDGE + 1, "CANTEEN – MẶT ĐỨNG NAM (VÒM CUỐN)", f'{SPEC["faces"]["south"]["title"]} · 3 tầng',
              LEVELS, None, scale=30)
    annex(s, LEN, W)
    roof_long(s, 0, LEN)
    front_face(s, 0, LEN, K["arch_bays_south"])
    s.note(3.0, F1 + 1.4, wrap("Tầng 1: 8 cửa vòm cuốn khung trắng, chân tường đá xám"))
    s.note(9.0, (K["band"][0] + K["band"][1]) / 2, wrap("Dải đá xám giữa tầng 1 và 2"))
    s.note(15.0, F2 + 0.5, wrap("Ban công tầng 2 lan can đặc màu vàng, đua ra 1,2 m"))
    s.note(21.0, F3 + 0.5, wrap("Ban công tầng 3 lan can sắt xanh"))
    s.note(LEN / 2, RIDGE - 1.0, wrap("Mái ngói đỏ 4 mái (theo vệ tinh)"))
    s.note((LEN + W) / 2, 2.0, wrap("Nhà kho 1 tầng cửa cuốn xanh ở đầu Đông"))
    return s.finish(os.path.join(OUT, "mat_dung_nam.png"))


def west():
    s = Sheet(DEP, RIDGE + 1, "CANTEEN – MẶT ĐỨNG TÂY", f'{SPEC["faces"]["west"]["title"]} · u = 118 − y',
              LEVELS, None, scale=30)
    roof_end(s, 0, DEP)
    front_face(s, 0, DEP, K["arch_bays_west"])
    s.note(3.0, F1 + 1.4, wrap("Vòm cuốn và 2 dải ban công bọc tiếp từ mặt Nam"))
    s.note(DEP / 2, RIDGE - 1.2, wrap("Đầu mái 4 mái"))
    return s.finish(os.path.join(OUT, "mat_dung_tay.png"))


def north():
    W = AX1 - X0                                         # u = 78.0 - x : annex on the left, behind
    s = Sheet(W, RIDGE + 1, "CANTEEN – MẶT ĐỨNG BẮC (GIẢ ĐỊNH)", f'{SPEC["faces"]["north"]["title"]} · chưa có ảnh',
              LEVELS, None, scale=30)
    annex(s, 0, AX1 - AX0, shutters=False)
    roof_long(s, AX1 - X1, W)
    plain_face(s, AX1 - X1, W, 8)
    s.note(W / 2, F2 + 1.7, wrap("Tường vàng, mỗi tầng 8 cửa sổ chữ nhật"))
    return s.finish(os.path.join(OUT, "mat_dung_bac.png"))


def east():
    s = Sheet(DEP, RIDGE + 1, "CANTEEN – MẶT ĐỨNG ĐÔNG (GIẢ ĐỊNH)", f'{SPEC["faces"]["east"]["title"]} · chưa có ảnh',
              LEVELS, None, scale=30)
    roof_end(s, 0, DEP)
    plain_face(s, 0, DEP, 4)
    annex(s, AY0 - Y0, AY1 - Y0, shutters=False)
    s.note(DEP / 2, F3 + 1.8, wrap("Tường vàng, cửa sổ chữ nhật"))
    s.note((AY0 + AY1) / 2 - Y0, 2.0, wrap("Nhà kho ghép phía trước, thấp 3,6 m"))
    return s.finish(os.path.join(OUT, "mat_dung_dong.png"))


# ===================================================================== tennis court: plan + side elevation
def tennis_plan():
    PPM = 22
    x0, y0, x1, y1 = T["rect"]
    W, H = x1 - x0, y1 - y0
    M = 70
    im = Image.new("RGB", (int(W * PPM) + 2 * M + 380, int(H * PPM) + 2 * M + 60), "#ffffff")
    d = ImageDraw.Draw(im)
    P = lambda x, y: (M + (x - x0) * PPM, M + 50 + (y1 - y) * PPM)
    d.text((M, 20), "SÂN TENNIS – MẶT BẰNG", font=font(26, True), fill="#222")
    d.rectangle([P(x0, y1), P(x1, y0)], fill=C["surround"], outline=C["fence"], width=4)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    L, Wd = T["court"]
    sw = T["singles_w"]
    d.rectangle([P(cx - L / 2, cy + Wd / 2), P(cx + L / 2, cy - Wd / 2)], fill=C["court"], outline=C["line"], width=3)
    d.line([P(cx - L / 2, cy + sw / 2), P(cx + L / 2, cy + sw / 2)], fill=C["line"], width=2)
    d.line([P(cx - L / 2, cy - sw / 2), P(cx + L / 2, cy - sw / 2)], fill=C["line"], width=2)
    sv = T["service_from_net"]
    for sx in (cx - sv, cx + sv):
        d.line([P(sx, cy + sw / 2), P(sx, cy - sw / 2)], fill=C["line"], width=2)
    d.line([P(cx - sv, cy), P(cx + sv, cy)], fill=C["line"], width=2)
    d.line([P(cx, cy + Wd / 2 + 0.9), P(cx, cy - Wd / 2 - 0.9)], fill="#111", width=4)               # net
    x = x0
    while x <= x1 + 1e-6:
        for yy in (y0, y1):
            p = P(x, yy); d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=C["fence"])
        x += T["post_step"]
    g0, g1 = T["gate"]["v0"], T["gate"]["v1"]
    d.line([P(x0, y0 + g0), P(x0, y0 + g1)], fill="#ffffff", width=6)
    for lx, ly in T["lights"]:
        p = P(lx, ly); d.rectangle([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7], fill="#f4c542", outline="#333")
    sr = T["shade"]["rect"]
    d.rectangle([P(sr[0], sr[3]), P(sr[2], sr[1])], fill=C["shade"], outline="#888", width=2)
    for bx, by in T["benches"]:
        d.rectangle([P(bx - 0.8, by + 0.25), P(bx + 0.8, by - 0.25)], fill=C["bench"])
    # dimensions + north hint
    d.text(((P(x0, y0)[0] + P(x1, y0)[0]) / 2, P(x0, y0)[1] + 24), f"{W:.1f} m (Đông – Tây)", font=font(15, True), fill="#333", anchor="mm")
    d.text((P(x1, cy)[0] + 16, P(x1, cy)[1]), f"{H:.1f} m", font=font(15, True), fill="#333", anchor="lm")
    nx = P(x1, y1)[0] + 120
    notes = ["1 sân đôi, lưới chạy Bắc–Nam, trục sân Đông–Tây",
             "Nền sân xanh, viền đỏ gạch, vạch trắng",
             f"Rào lưới mắt cáo cao {T['fence_h']:.0f} m, cột tối mỗi {T['post_step']} m",
             "Cửa vào ở góc Tây Nam (trắng)",
             f"4 đèn pha ở 4 góc, cao {T['light_h']} m (vàng)",
             "Mái che + ghế xanh dương ở cạnh Nam (giáp Nhà ăn)",
             f"Bó vỉa đỏ nâu cao {T['curb_h']} m quanh chân rào"]
    d.text((nx, M + 50), "Ghi chú", font=font(17, True), fill="#222")
    for i, t in enumerate(notes):
        d.multiline_text((nx, M + 86 + i * 46), f"{i + 1}. " + wrap(t, 34), font=font(13), fill="#333", spacing=3)
    path = os.path.join(OUT, "san_tennis_mat_bang.png"); im.save(path)
    return im


def tennis_side():
    x0, y0, x1, y1 = T["rect"]
    W = x1 - x0
    s = Sheet(W, T["light_h"] + 1, "SÂN TENNIS – MẶT ĐỨNG NAM (NHÌN TỪ NHÀ ĂN)", "Rào lưới, cột, đèn pha, mái che ghế",
              [("Bó vỉa", T["curb_h"]), ("Đỉnh rào", T["fence_h"]), ("Đèn pha", T["light_h"])], None, scale=30)
    s.rect(0, 0, W, T["curb_h"], C["curb"])
    s.rect(0, T["curb_h"], W, T["fence_h"], "#e9eeec")
    u = 0.0
    while u <= W:
        s.line(u, T["curb_h"], u + 1.0, T["fence_h"], C["mesh"], 1); s.line(u + 1.0, T["curb_h"], u, T["fence_h"], C["mesh"], 1)
        u += 0.5
    u = 0.0
    while u <= W + 1e-6:
        s.rect(u - 0.06, 0, u + 0.06, T["fence_h"], C["fence"]); u += T["post_step"]
    for z in (T["curb_h"] + 1.2, T["fence_h"] - 0.05):
        s.rect(0, z - 0.04, W, z + 0.04, C["fence"])
    for u in (0, W):
        s.rect(u - 0.08, 0, u + 0.08, T["light_h"], C["fence"])
        s.rect(u - 0.5, T["light_h"] - 0.3, u + 0.5, T["light_h"], "#f4c542", "#333")
    sr = T["shade"]["rect"]
    s.rect(sr[0] - x0, T["shade"]["h"] - 0.12, sr[2] - x0, T["shade"]["h"], C["shade"], "#888")
    s.note(5, T["fence_h"] - 1.0, wrap("Rào lưới mắt cáo cao 4 m, cột tối"))
    s.note(W - 1.5, T["light_h"] + 0.4, wrap("Đèn pha trên cột góc"))
    s.note((sr[0] + sr[2]) / 2 - x0, T["shade"]["h"] + 0.5, wrap("Mái che ghế (phía sau rào)"))
    return s.finish(os.path.join(OUT, "san_tennis_mat_dung.png"))


def overview(images, path):
    sc = 0.5
    ims = [im.resize((int(im.width * sc), int(im.height * sc))) for im in images]
    W = max(ims[0].width + ims[1].width, ims[2].width + ims[3].width, ims[4].width + ims[5].width) + 20
    rows = [(ims[0], ims[1]), (ims[2], ims[3]), (ims[4], ims[5])]
    H = sum(max(a.height, b.height) for a, b in rows) + 40
    sheet = Image.new("RGB", (W, H), "#ffffff")
    y = 0
    for a, b in rows:
        sheet.paste(a, (0, y)); sheet.paste(b, (a.width + 20, y)); y += max(a.height, b.height) + 20
    sheet.save(path)


s_im = south()
side_by_side(os.path.join(ROOT, SPEC["faces"]["south"]["photo"]), s_im, os.path.join(OUT, "so_sanh_mat_nam.png"))
w_im = west()
n_im = north(); e_im = east()
tp = tennis_plan(); ts = tennis_side()
side_by_side(os.path.join(ROOT, SPEC["faces"]["west"]["photo"]), tp, os.path.join(OUT, "so_sanh_san_tennis.png"))
overview([s_im, w_im, n_im, e_im, tp, ts], os.path.join(OUT, "tong_hop.png"))
print("ok eave", round(EAVE, 2), "ridge", round(RIDGE, 2))
