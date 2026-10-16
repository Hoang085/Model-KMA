"""Shared helpers for B2 elevation sheets (scaled facade drawings with level marks, notes and a scale bar)."""
import os
from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def wrap(text, n=28):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return "\n".join(lines + [cur])


class Sheet:
    """One elevation drawing. u = metres from the viewer's left, z = metres above grade."""

    def __init__(self, width_m, height_m, title, sub, levels, top_label=None, scale=None, mirror=False):
        self.S = scale or max(8, min(18, int(820 / max(height_m, 1))))
        self.w_m, self.h_m, self.mirror = width_m, height_m, mirror
        self.levels, self.top_label = levels, top_label
        self.ML, self.MR, self.MT, self.MB = 110, 500, 110, 120
        self.W = int(width_m * self.S) + self.ML + self.MR
        self.H = int((height_m + 3) * self.S) + self.MT + self.MB
        self.GY = self.H - self.MB
        self.im = Image.new("RGB", (self.W, self.H), "#ffffff")
        self.d = ImageDraw.Draw(self.im)
        self.d.text((self.ML, 30), title, font=font(26, True), fill="#222")
        self.d.text((self.ML, 68), sub, font=font(15), fill="#6c665c")
        self.notes = []

    def X(self, u):
        return self.ML + ((self.w_m - u) if self.mirror else u) * self.S

    def Y(self, z):
        return self.GY - z * self.S

    def rect(self, u0, z0, u1, z1, fill, outline=None, width=1):
        xa, xb = sorted((self.X(u0), self.X(u1)))
        self.d.rectangle([xa, self.Y(z1), xb, self.Y(z0)], fill=fill, outline=outline, width=width)

    def poly(self, pts, fill, outline=None):
        self.d.polygon([(self.X(u), self.Y(z)) for u, z in pts], fill=fill, outline=outline)

    def line(self, u0, z0, u1, z1, fill, width=1):
        self.d.line([(self.X(u0), self.Y(z0)), (self.X(u1), self.Y(z1))], fill=fill, width=width)

    def text(self, u, z, s, size_m, fill, bold=True):
        px = max(8, int(size_m * self.S))
        self.d.text((self.X(u), self.Y(z)), s, font=font(px, bold), fill=fill, anchor="mm")

    def note(self, u, z, text):
        n = len(self.notes) + 1
        x, y = self.X(u), self.Y(z)
        self.d.ellipse([x - 13, y - 13, x + 13, y + 13], fill="#c0392b", outline="#fff", width=2)
        self.d.text((x, y), str(n), font=font(14, True), fill="#fff", anchor="mm")
        self.notes.append(text)

    def finish(self, path):
        d, S = self.d, self.S
        R = self.ML + self.w_m * S
        d.line([(self.ML - 40, self.GY), (R + 40, self.GY)], fill="#222", width=3)
        lx = R + 18
        last_y = None
        for name, z in self.levels:
            y = self.Y(z)
            if last_y is not None and abs(last_y - y) < 13:
                continue                                      # skip labels that would overlap
            d.line([(lx, y), (lx + 14, y)], fill="#888")
            d.text((lx + 20, y), f"{name}  +{z:.1f}", font=font(12), fill="#555", anchor="lm")
            last_y = y
        if self.top_label:
            d.text((lx + 20, self.Y(self.top_label[1])), f"{self.top_label[0]}  +{self.top_label[1]:.1f}",
                   font=font(12, True), fill="#333", anchor="lm")
        y = self.GY + 34
        d.line([(self.ML, y), (R, y)], fill="#444", width=1)
        for x in (self.ML, R):
            d.line([(x, y - 7), (x, y + 7)], fill="#444", width=2)
        d.text(((self.ML + R) / 2, y + 16), f"{self.w_m:.1f} m", font=font(14, True), fill="#333", anchor="mm")
        sx, sy = self.ML, self.GY + 72
        for i in range(5):
            d.rectangle([sx + i * 2 * S, sy, sx + (i + 1) * 2 * S, sy + 8], fill="#222" if i % 2 == 0 else "#fff", outline="#222")
        d.text((sx, sy + 14), "0", font=font(12), fill="#333", anchor="mt")
        d.text((sx + 10 * S, sy + 14), "10 m", font=font(12), fill="#333", anchor="mt")
        px = R - 1.0 * S
        d.ellipse([px - 3, self.Y(1.7), px + 3, self.Y(1.7) + 6], fill="#2c6bd1")
        d.rectangle([px - 3, self.Y(1.45), px + 3, self.GY], fill="#2c6bd1")
        nx, ny = R + 200, self.MT + 10
        d.text((nx, ny), "Ghi chú", font=font(17, True), fill="#222")
        for i, t in enumerate(self.notes):
            yy = ny + 36 + i * 68
            d.ellipse([nx, yy, nx + 22, yy + 22], fill="#c0392b")
            d.text((nx + 11, yy + 11), str(i + 1), font=font(12, True), fill="#fff", anchor="mm")
            d.multiline_text((nx + 32, yy + 1), t, font=font(13), fill="#333", spacing=3)
        self.im.save(path)
        return self.im


def side_by_side(photo_path, elev, out_path):
    ph = Image.open(photo_path).convert("RGB")
    h = elev.height
    ph = ph.resize((int(ph.width * h / ph.height), h))
    sheet = Image.new("RGB", (ph.width + 30 + elev.width, h), "#ffffff")
    sheet.paste(ph, (0, 0)); sheet.paste(elev, (ph.width + 30, 0))
    sheet.save(out_path)
