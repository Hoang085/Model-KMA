"""B2 – plan of the sports zone + grandstand section, read from layout/buildings/sports.json.
Outputs in 02_toa_nha/sports/. Usage: python3 scripts/draw_sports_plan.py
"""
import json, math, os
from PIL import Image, ImageDraw
from elev_lib import Sheet, wrap, font

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, "layout", "buildings", "sports.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "02_toa_nha", "sports")
os.makedirs(OUT, exist_ok=True)
C = S["colors"]


def rr_outline(x0, y0, x1, y1, r, n=10):
    """Rounded-rectangle outline, counter-clockwise, starting at the bottom-right corner arc."""
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def plan():
    PPM = 9
    bx0, by0, bx1, by1 = S["base"]
    M = 60
    W = int((bx1 - bx0) * PPM) + 2 * M + 420
    H = int((by1 - by0) * PPM) + 2 * M + 70
    im = Image.new("RGB", (W, H), "#ffffff")
    d = ImageDraw.Draw(im)
    P = lambda x, y: (M + (x - bx0) * PPM, M + 60 + (by1 - y) * PPM)
    R = lambda r: [P(r[0], r[3]), P(r[2], r[1])]
    d.text((M, 18), "KHU THỂ THAO – MẶT BẰNG", font=font(26, True), fill="#222")
    d.rectangle(R(S["base"]), fill=C["base"])
    # track
    T = S["track"]; tw = T["lanes"] * T["lane_w"]
    x0, y0, x1, y1 = T["rect"]
    d.polygon([P(*p) for p in rr_outline(x0, y0, x1, y1, T["corner_r"])], fill=C["track"])
    d.polygon([P(*p) for p in rr_outline(x0 + tw, y0 + tw, x1 - tw, y1 - tw, T["corner_r"] - tw)], fill=C["apron"])
    for k in range(1, T["lanes"]):
        o = k * T["lane_w"]
        d.line([P(*p) for p in rr_outline(x0 + o, y0 + o, x1 - o, y1 - o, T["corner_r"] - o)] + [P(*rr_outline(x0 + o, y0 + o, x1 - o, y1 - o, T["corner_r"] - o)[0])], fill=C["line"], width=1)
    d.line([P(T["start_x"], y0), P(T["start_x"], y0 + tw)], fill=C["line"], width=3)
    # two football fields (long axis north–south)
    F = S["field"]
    for fx0, fy0, fx1, fy1 in F["rects"]:
        y = fy0; i = 0
        while y < fy1 - 1e-6:
            d.rectangle(R([fx0, y, fx1, min(y + F["stripe_w"], fy1)]), fill=C["turf_a"] if i % 2 == 0 else C["turf_b"]); y += F["stripe_w"]; i += 1
        d.rectangle(R([fx0, fy0, fx1, fy1]), outline=C["line"], width=2)
        fcx, fcy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
        d.line([P(fx0, fcy), P(fx1, fcy)], fill=C["line"], width=2)
        rr = F["center_r"] * PPM; c = P(fcx, fcy)
        d.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], outline=C["line"], width=2)
        for side in (-1, 1):
            gy = fy0 if side < 0 else fy1
            dep, wid = F["penalty"]
            d.rectangle(R([fcx - wid / 2, min(gy, gy - side * dep), fcx + wid / 2, max(gy, gy - side * dep)]), outline=C["line"], width=2)
            gw = F["goal"][0]
            d.rectangle(R([fcx - gw / 2, min(gy, gy + side * F["goal"][2]), fcx + gw / 2, max(gy, gy + side * F["goal"][2])]), outline="#ffffff", width=3)
    # basketball
    Bk = S["basketball"]
    d.rectangle(R(Bk["surface"]), fill=C["basket"])
    bcx = (Bk["surface"][0] + Bk["surface"][2]) / 2; bcy = (Bk["surface"][1] + Bk["surface"][3]) / 2
    cw, cl = Bk["court"]
    d.rectangle(R([bcx - cw / 2, bcy - cl / 2, bcx + cw / 2, bcy + cl / 2]), outline=C["line"], width=2)
    d.line([P(bcx - cw / 2, bcy), P(bcx + cw / 2, bcy)], fill=C["line"], width=2)
    rr = Bk["circle_r"] * PPM; c = P(bcx, bcy)
    d.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], outline=C["line"], width=2)
    kd, kw = Bk["key"]
    for side in (-1, 1):
        by = bcy + side * cl / 2
        d.rectangle(R([bcx - kw / 2, min(by, by - side * kd), bcx + kw / 2, max(by, by - side * kd)]), fill=C["basket_key"], outline=C["line"], width=2)
        hy = by - side * 1.575
        rr = Bk["three_r"] * PPM; c = P(bcx, hy)
        box = [c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr]
        d.arc(box, 0, 180, fill=C["line"], width=2) if side > 0 else d.arc(box, 180, 360, fill=C["line"], width=2)
        p = P(bcx, hy); d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], outline=C["rim"], width=2)
    # volleyball
    V = S["volleyball"]
    d.rectangle(R(V["surface"]), fill=C["volley_out"])
    vcx = (V["surface"][0] + V["surface"][2]) / 2; vcy = (V["surface"][1] + V["surface"][3]) / 2
    vw, vl = V["court"]
    d.rectangle(R([vcx - vw / 2, vcy - vl / 2, vcx + vw / 2, vcy + vl / 2]), fill=C["volley"], outline=C["line"], width=2)
    for yy in (vcy, vcy - V["attack"], vcy + V["attack"]):
        d.line([P(vcx - vw / 2, yy), P(vcx + vw / 2, yy)], fill=C["line"], width=2 if yy != vcy else 4)
    # grandstand
    St = S["stand"]; sx0, sy0, sx1, sy1 = St["rect"]
    for k in range(St["tiers"]):
        yk = sy0 + k * St["tier_d"]
        d.rectangle(R([sx0, yk, sx1, yk + St["tier_d"]]), fill=C["seat_a"] if k % 2 == 0 else "#3a6fb8", outline="#1d3f70")
    for a in St["aisles"]:
        d.rectangle(R([a - St["aisle_w"] / 2, sy0, a + St["aisle_w"] / 2, sy0 + St["tiers"] * St["tier_d"]]), fill=C["concrete"])
    d.rectangle(R([sx0, sy0 - St["roof_over"], sx1, sy1 + 0.3]), outline="#666", width=2)
    for lx, ly in S["lights"]["poles"]:
        p = P(lx, ly); d.rectangle([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill="#f4c542", outline="#333")
    labels = [((28.0, 185.0 + 9), "Sân bóng 1\n27 × 42 m"), ((58.0, 185.0 + 9), "Sân bóng 2\n27 × 42 m"), ((43, y1 - 2.4), "Đường chạy 4 làn"),
              ((bcx, bcy + 6), "Bóng rổ\n28 × 15"), ((vcx, vcy + 5.5), "Bóng chuyền\n18 × 9"), (((sx0 + sx1) / 2, sy1 + 1.8), "Khán đài 6 bậc, mái che")]
    for (lx, ly), t in labels:
        d.multiline_text(P(lx, ly), t, font=font(14, True), fill="#ffffff", anchor="mm", align="center", stroke_width=2, stroke_fill="#000")
    nx = P(bx1, by1)[0] + 30
    notes = ["Vị trí theo ảnh vệ tinh khu GDTC; kích thước theo chuẩn sân",
             "Đường chạy 4 làn (mỗi làn 1,22 m), góc bo R 12 m, vạch xuất phát ở cạnh Nam",
             "2 sân bóng nhỏ nằm dọc (Bắc – Nam), mỗi sân 27 × 42 m, cỏ kẻ sọc, khung thành 3 × 2 m ở 2 đầu",
             "Bóng rổ: 1 sân chuẩn 28 × 15 m, trục Bắc – Nam, 2 cột rổ",
             "Bóng chuyền: sân 18 × 9 m, lưới cao 2,43 m",
             "Khán đài phía Bắc nhìn về phía Nam vào sân bóng: 6 bậc ngồi, 3 lối đi, mái tôn trên cột thép",
             "4 cột đèn pha cao 15 m ở 4 góc đường chạy"]
    d.text((nx, M + 60), "Ghi chú", font=font(17, True), fill="#222")
    for i, t in enumerate(notes):
        d.multiline_text((nx, M + 96 + i * 58), f"{i + 1}. " + wrap(t, 40), font=font(13), fill="#333", spacing=3)
    path = os.path.join(OUT, "mat_bang_khu_the_thao.png"); im.save(path)
    return im


def stand_section():
    St = S["stand"]
    D = St["rect"][3] - St["rect"][1] + St["roof_over"]
    s = Sheet(D, St["roof_back"] + 1, "KHÁN ĐÀI – MẶT CẮT (NHÌN TỪ PHÍA ĐÔNG)", "Trái = sân bóng (Nam), phải = phía Bắc",
              [("Bậc đầu", St["front_h"]), ("Bậc trên cùng", St["front_h"] + (St["tiers"] - 1) * St["tier_h"]),
               ("Mái trước", St["roof_front"]), ("Mái sau", St["roof_back"])], None, scale=60)
    o = St["roof_over"]
    for k in range(St["tiers"]):
        u0 = o + k * St["tier_d"]
        s.rect(u0, 0, D, St["front_h"] + k * St["tier_h"], C["concrete"], "#999")
        s.rect(u0 + 0.15, St["front_h"] + k * St["tier_h"], u0 + 0.55, St["front_h"] + k * St["tier_h"] + 0.42, C["seat_a"])
        s.rect(u0 + 0.5, St["front_h"] + k * St["tier_h"], u0 + 0.58, St["front_h"] + k * St["tier_h"] + 0.8, C["seat_a"])
    s.rect(o, St["front_h"], o + 0.06, St["front_h"] + 1.0, C["steel"])
    s.rect(D - 0.3, 0, D - 0.1, St["roof_back"], C["steel"])
    s.poly([(0, St["roof_front"]), (D, St["roof_back"]), (D, St["roof_back"] + 0.2), (0, St["roof_front"] + 0.2)], C["roof"], "#888")
    s.note(o + 2.0, St["front_h"] + 1.6, wrap("6 bậc ngồi cao 0,45 m, sâu 0,8 m, ghế nhựa xanh"))
    s.note(D - 0.8, 4.0, wrap("Cột thép phía sau mỗi 5,6 m"))
    s.note(D / 2, St["roof_back"] + 0.6, wrap("Mái tôn công-xôn, dốc về phía sau"))
    s.note(o, St["front_h"] + 1.3, wrap("Lan can thép phía trước"))
    return s.finish(os.path.join(OUT, "khan_dai_mat_cat.png"))


p = plan(); st = stand_section()
print("ok", p.size, st.size)
