"""Draw the scaled 2D master plan from layout/campus_layout.json.
Outputs: 01_mat_bang/mat_bang_ty_le.png and 01_mat_bang/doi_chieu_ve_tinh.png
Usage: python3 scripts/draw_plan.py
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "01_mat_bang")
os.makedirs(OUT, exist_ok=True)
L = json.load(open(os.path.join(ROOT, "layout", "campus_layout.json"), encoding="utf-8"))

FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
def f(size, bold=False): return ImageFont.truetype(FONT_B if bold else FONT, size)

PPM = 6.0                     # pixels per metre
xs = [p[0] for p in L["boundary"]]; ys = [p[1] for p in L["boundary"]]
X0, X1, Y0, Y1 = min(xs) - 12, max(xs) + 12, min(ys) - 22, max(ys) + 8
MT, MB, ML, MR = 120, 150, 70, 300   # margins (title / scale bar / left / legend)
W = int((X1 - X0) * PPM) + ML + MR
H = int((Y1 - Y0) * PPM) + MT + MB

def P(x, y): return (ML + (x - X0) * PPM, MT + (Y1 - y) * PPM)
def R(rect): x0, y0, x1, y1 = rect; return [P(x0, y1), P(x1, y0)]

COL = dict(bg="#ffffff", ground="#f4f1ea", grid="#e6e1d6", grid5="#d2cbbd", wall="#2b2b2b",
           bld="#f8d9dc", bld_edge="#9a5560", tower="#f1bcc3", sport="#8fd9b0", sport_edge="#3f8f63",
           court="#5fb6c9", track="#c66a52", field="#4f9a5e", gate="#ffffff", text="#222222",
           muted="#6c665c", water="#7fb7d8", tree="#4a7d3a", warn="#c0392b")


def draw_plan(im, d, alpha_fill=True):
    # sports
    for s in L["sports"]:
        if s["type"] == "zone":
            d.rounded_rectangle(R(s["rect"]), radius=18, fill=COL["sport"] if alpha_fill else None,
                                outline=COL["sport_edge"], width=2)
    for s in L["sports"]:
        if s["type"] == "track_field":
            (a, b) = R(s["rect"])
            d.rounded_rectangle([a, b], radius=int(0.5 * (b[1] - a[1]) * 0.45), fill=COL["track"] if alpha_fill else None,
                                outline=COL["track"], width=2)
            ins = 6 * PPM
            d.rectangle([(a[0] + ins, a[1] + ins), (b[0] - ins, b[1] - ins)], fill=COL["field"] if alpha_fill else None,
                        outline="#ffffff", width=2)
        elif s["type"] == "court":
            d.rectangle(R(s["rect"]), fill=COL["court"] if alpha_fill else None, outline="#ffffff", width=2)
    # buildings
    for b in L["buildings"]:
        fill = COL["tower"] if (b["floors"] or 0) >= 9 else COL["bld"]
        if b.get("outside"):
            fill = "#ece7f5"
        d.rectangle(R(b["rect"]), fill=fill if alpha_fill else None, outline=COL["bld_edge"], width=2)
    # fountain
    for ft in L["features"]:
        cx, cy = P(*ft["center"]); rr = ft["radius"] * PPM
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=COL["water"] if alpha_fill else None, outline="#ffffff", width=2)
    # trees
    for t in L["trees"]:
        cx, cy = P(*t); rr = 3.2 * PPM
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=COL["tree"] if alpha_fill else None, outline="#2f5a24", width=2)
    # boundary wall
    pts = [P(*p) for p in L["boundary"]]
    gx0, gy0, gx1, gy1 = L["gate"]["rect"]
    d.line(pts + [pts[0]], fill=COL["wall"], width=4)
    # gate (white box breaking the wall)
    d.rectangle(R(L["gate"]["rect"]), fill=COL["gate"], outline=COL["wall"], width=3)


def labels(d, on_photo=False):
    for b in L["buildings"]:
        x0, y0, x1, y1 = b["rect"]
        (a, c) = R(b["rect"])
        cx, cy = (a[0] + c[0]) / 2, (a[1] + c[1]) / 2
        name = b["name"].split(" – ")[0]
        dims = f'{x1 - x0:.0f}×{y1 - y0:.0f} m' + (f' · {b["floors"]}T' if b["floors"] else "")
        vertical = (c[0] - a[0]) < 90
        txt_col = "#ffffff" if on_photo else COL["text"]
        if vertical:
            img = Image.new("RGBA", (int(c[1] - a[1]), 44), (0, 0, 0, 0))
            dd = ImageDraw.Draw(img)
            dd.text((img.width / 2, 12), name, font=f(17, True), fill=txt_col, anchor="mm", stroke_width=2 if on_photo else 0, stroke_fill="#000")
            dd.text((img.width / 2, 33), dims, font=f(13), fill=txt_col, anchor="mm", stroke_width=2 if on_photo else 0, stroke_fill="#000")
            img = img.rotate(90, expand=True)
            d._image.paste(img, (int(cx - img.width / 2), int(cy - img.height / 2)), img)
        else:
            d.text((cx, cy - 10), name, font=f(17, True), fill=txt_col, anchor="mm", stroke_width=2 if on_photo else 0, stroke_fill="#000")
            d.text((cx, cy + 11), dims, font=f(13), fill=txt_col, anchor="mm", stroke_width=2 if on_photo else 0, stroke_fill="#000")
    for s in L["sports"]:
        if s["id"] in ("gdtc",):
            continue
        (a, c) = R(s["rect"])
        d.text(((a[0] + c[0]) / 2, (a[1] + c[1]) / 2), s["name"], font=f(14, True), fill="#ffffff", anchor="mm",
               stroke_width=2, stroke_fill="#1d3d2a")
    (a, c) = R(L["gate"]["rect"])
    d.text(((a[0] + c[0]) / 2, c[1] + 16), "CỔNG", font=f(16, True), fill=COL["warn"] if not on_photo else "#fff",
           anchor="mm", stroke_width=2 if on_photo else 0, stroke_fill="#000")
    ft = L["features"][0]; cx, cy = P(*ft["center"])
    d.text((cx - 22, cy), "Bồn nước", font=f(13), fill=COL["text"] if not on_photo else "#fff", anchor="rm",
           stroke_width=2 if on_photo else 0, stroke_fill="#000")


# ------------------------------------------------------------- 1) clean scaled plan
im = Image.new("RGB", (W, H), COL["bg"])
d = ImageDraw.Draw(im)
pts = [P(*p) for p in L["boundary"]]
d.polygon(pts, fill=COL["ground"])
# 10 m grid inside drawing area
gx = math.floor(X0 / 10) * 10
while gx <= X1:
    d.line([P(gx, Y0), P(gx, Y1)], fill=COL["grid5"] if gx % 50 == 0 else COL["grid"], width=1); gx += 10
gy = math.floor(Y0 / 10) * 10
while gy <= Y1:
    d.line([P(X0, gy), P(X1, gy)], fill=COL["grid5"] if gy % 50 == 0 else COL["grid"], width=1); gy += 10
draw_plan(im, d)
labels(d)
# title
d.text((ML, 34), "MẶT BẰNG TỔNG THỂ – HỌC VIỆN KỸ THUẬT MẬT MÃ", font=f(28, True), fill=COL["text"])
d.text((ML, 74), "Bản B1 · tỷ lệ theo ảnh vệ tinh · lưới 10 m · gốc toạ độ (0,0) = tâm cổng", font=f(16), fill=COL["muted"])
# scale bar
sx, sy = ML, H - 80
for i in range(5):
    d.rectangle([sx + i * 10 * PPM, sy, sx + (i + 1) * 10 * PPM, sy + 10], fill="#222" if i % 2 == 0 else "#fff", outline="#222")
for i in (0, 2, 5):
    d.text((sx + i * 10 * PPM, sy + 18), f"{i * 10} m", font=f(13), fill=COL["text"], anchor="mt")
ext_w = max(xs) - min(xs); ext_h = max(ys) - min(ys)
d.text((sx + 340, sy + 4), f"Khuôn viên khoảng {ext_w:.0f} × {ext_h:.0f} m", font=f(15), fill=COL["muted"], anchor="lm")
# north arrow (plan is rotated: true north is north_deg counter-clockwise from up)
nx, ny = W - MR + 150, MT + 75
ang = math.radians(L["north_deg"])
ux, uy = -math.sin(ang), -math.cos(ang)            # unit vector towards true north (screen coords)
d.ellipse([nx - 52, ny - 52, nx + 52, ny + 52], outline="#999", width=2)
tip = (nx + ux * 44, ny + uy * 44); base = (nx - ux * 34, ny - uy * 34)
d.line([base, tip], fill="#222", width=4)
px_, py_ = -uy, ux
d.polygon([tip, (tip[0] - ux * 20 + px_ * 10, tip[1] - uy * 20 + py_ * 10), (tip[0] - ux * 20 - px_ * 10, tip[1] - uy * 20 - py_ * 10)], fill="#222")
d.text((nx + ux * 70, ny + uy * 70), "Bắc", font=f(17, True), fill="#222", anchor="mm")
# legend
lx, ly = W - MR + 40, MT + 170
items = [(COL["bld"], "Toà nhà"), ("#ece7f5", "Ngoài tường rào"), (COL["sport"], "Khu thể chất"),
         (COL["court"], "Sân thể thao"), (COL["tree"], "Cây (theo sơ đồ)"), (COL["water"], "Bồn nước")]
d.text((lx, ly - 34), "Chú thích", font=f(17, True), fill=COL["text"])
for i, (c, t) in enumerate(items):
    d.rectangle([lx, ly + i * 34, lx + 24, ly + i * 34 + 22], fill=c, outline="#555")
    d.text((lx + 36, ly + i * 34 + 11), t, font=f(14), fill=COL["text"], anchor="lm")
d.line([(lx, ly + 6 * 34 + 12), (lx + 24, ly + 6 * 34 + 12)], fill=COL["wall"], width=4)
d.text((lx + 36, ly + 6 * 34 + 12), "Tường rào", font=f(14), fill=COL["text"], anchor="lm")
d.text((lx, ly + 7 * 34 + 14), "Số tầng: bổ sung khi có\nảnh từng toà (B2)", font=f(13), fill=COL["muted"])
im.save(os.path.join(OUT, "mat_bang_ty_le.png"))

# ------------------------------------------------------------- 2) overlay on the rotated satellite
sat_path = os.path.join(ROOT, "research", "sat_rot44.png")
if os.path.exists(sat_path):
    sat = Image.open(sat_path).convert("RGBA")
    MPP, GX, GY = 20 / 70, 522, 1010
    ov = Image.new("RGBA", sat.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    def Q(x, y): return (GX + x / MPP, GY - y / MPP)
    def QR(rect): x0, y0, x1, y1 = rect; return [Q(x0, y1), Q(x1, y0)]
    for b in L["buildings"]:
        od.rectangle(QR(b["rect"]), outline=(255, 80, 120, 255), width=3, fill=(255, 80, 120, 40))
    for s in L["sports"]:
        od.rectangle(QR(s["rect"]), outline=(80, 255, 160, 255), width=2)
    od.line([Q(*p) for p in L["boundary"] + [L["boundary"][0]]], fill=(255, 230, 0, 255), width=3)
    od.rectangle(QR(L["gate"]["rect"]), outline=(255, 255, 255, 255), width=3)
    ft = L["features"][0]; cx, cy = Q(*ft["center"]); rr = ft["radius"] / MPP
    od.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(120, 200, 255, 255), width=3)
    for b in L["buildings"]:
        (a, c) = QR(b["rect"])
        od.text(((a[0] + c[0]) / 2, (a[1] + c[1]) / 2), b["name"].split(" – ")[0], font=f(14, True),
                fill=(255, 255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, 255))
    out = Image.alpha_composite(sat, ov).convert("RGB")
    # crop to campus
    xs_px = [Q(*p)[0] for p in L["boundary"]]; ys_px = [Q(*p)[1] for p in L["boundary"]]
    out = out.crop((int(min(xs_px)) - 60, int(min(ys_px)) - 60, int(max(xs_px)) + 60, int(max(ys_px)) + 60))
    out.save(os.path.join(OUT, "doi_chieu_ve_tinh.png"))
print("ok", W, H)
