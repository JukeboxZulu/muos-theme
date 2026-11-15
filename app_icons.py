"""Original line-style app icons for the Ember theme.

Drawn white on transparent so the theme can recolour them (amber when focused).
File names match each app's ICON value, which is what MustardOS uses to find
grid images in {theme}/catalogue/Application/grid/.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

FONT_BOLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Poppins-Bold.ttf")
WHITE = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)
S = 8          # supersampling
BASE = 96      # design grid; everything below is in these units


def _canvas():
    img = Image.new("RGBA", (BASE * S, BASE * S), CLEAR)
    return img, ImageDraw.Draw(img)


def u(v):      # design units -> supersampled pixels
    return v * S


def box(x0, y0, x1, y1):
    return [u(x0), u(y0), u(x1), u(y1)]


LW = 7         # standard stroke width in design units


def ring_rect(d, x0, y0, x1, y1, r, w=LW):
    d.rounded_rectangle(box(x0, y0, x1, y1), radius=u(r), outline=WHITE, width=u(w))


def line(d, pts, w=LW):
    d.line([(u(x), u(y)) for x, y in pts], fill=WHITE, width=u(w), joint="curve")
    for x, y in (pts[0], pts[-1]):  # round caps
        d.ellipse(box(x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=WHITE)


def text(d, s, cx, cy, size):
    f = ImageFont.truetype(FONT_BOLD, u(size))
    l, t, r, b = d.textbbox((0, 0), s, font=f)
    d.text((u(cx) - (r - l) / 2 - l, u(cy) - (b - t) / 2 - t), s, font=f, fill=WHITE)


# ------------------------------------------------------------------ icons
def archive(d):            # package with a down arrow
    ring_rect(d, 14, 30, 82, 84, 8)
    line(d, [(14, 30), (24, 14), (72, 14), (82, 30)])
    line(d, [(48, 40), (48, 70)])
    line(d, [(36, 58), (48, 70), (60, 58)])


def terminal(d):           # window with prompt
    ring_rect(d, 10, 16, 86, 80, 10)
    line(d, [(26, 38), (38, 48), (26, 58)])
    line(d, [(46, 60), (66, 60)])


def task(d):               # toolbox
    ring_rect(d, 12, 34, 84, 82, 8)
    line(d, [(36, 34), (36, 22), (60, 22), (60, 34)])
    line(d, [(12, 54), (84, 54)])
    d.rounded_rectangle(box(42, 48, 54, 62), radius=u(3), fill=WHITE)


def logo_2048(d):          # tile with 2048
    d.rounded_rectangle(box(10, 10, 86, 86), radius=u(14), fill=WHITE)
    d.rounded_rectangle(box(18, 18, 78, 78), radius=u(8), fill=CLEAR)
    text(d, "2048", 48, 49, 21)


def ppsspp(d):             # widescreen handheld
    ring_rect(d, 6, 28, 90, 70, 20)
    ring_rect(d, 30, 36, 66, 62, 3, w=5)
    d.ellipse(box(14, 44, 22, 52), fill=WHITE)
    for cx, cy in ((78, 42), (78, 56), (72, 49), (84, 49)):
        d.ellipse(box(cx - 3, cy - 3, cx + 3, cy + 3), fill=WHITE)


def portmaster(d):         # anchor
    d.ellipse(box(40, 10, 56, 26), outline=WHITE, width=u(6))
    line(d, [(48, 26), (48, 84)])
    line(d, [(34, 38), (62, 38)])
    d.arc(box(18, 36, 78, 86), start=20, end=160, fill=WHITE, width=u(LW))
    line(d, [(14, 58), (22, 66), (30, 58)], w=6)
    line(d, [(66, 58), (74, 66), (82, 58)], w=6)


def retroarch(d):          # gamepad
    d.rounded_rectangle(box(8, 28, 88, 72), radius=u(22), outline=WHITE, width=u(LW))
    line(d, [(22, 50), (38, 50)], w=6)
    line(d, [(30, 42), (30, 58)], w=6)
    d.ellipse(box(58, 40, 68, 50), fill=WHITE)
    d.ellipse(box(68, 50, 78, 60), fill=WHITE)


def scummvm(d):            # point-and-click cursor
    pts = [(28, 12), (28, 76), (44, 62), (54, 84), (64, 80), (54, 58), (74, 58)]
    d.polygon([(u(x), u(y)) for x, y in pts], outline=WHITE, width=u(6))
    d.line([(u(x), u(y)) for x, y in pts + [pts[0]]], fill=WHITE, width=u(6), joint="curve")


def musudoku(d):           # 3x3 grid with digits
    ring_rect(d, 10, 10, 86, 86, 10)
    # outline is drawn inward, so the inner area is 17..79
    for v in (37.7, 58.3):
        line(d, [(v, 17), (v, 79)], w=4)
        line(d, [(17, v), (79, v)], w=4)
    text(d, "1", 27.3, 27.3, 15)
    text(d, "5", 48, 48, 15)
    text(d, "9", 68.7, 68.7, 15)


def vtree(d):              # file tree
    d.rounded_rectangle(box(12, 12, 40, 32), radius=u(4), fill=WHITE)
    line(d, [(22, 32), (22, 72)], w=6)
    line(d, [(22, 48), (44, 48)], w=6)
    line(d, [(22, 72), (44, 72)], w=6)
    for y in (40, 64):
        d.rounded_rectangle(box(48, y, 84, y + 18), radius=u(4), outline=WHITE, width=u(6))


def scrappy(d):            # picture with download arrow
    ring_rect(d, 8, 14, 74, 70, 8)
    d.polygon([(u(x), u(y)) for x, y in [(16, 62), (34, 38), (48, 54), (56, 46), (66, 62)]], fill=WHITE)
    d.ellipse(box(50, 22, 60, 32), fill=WHITE)
    d.ellipse(box(54, 52, 90, 88), fill=CLEAR)
    d.ellipse(box(57, 55, 87, 85), fill=WHITE)
    line(d, [(72, 62), (72, 76)], w=4)
    d.polygon([(u(x), u(y)) for x, y in [(65, 71), (79, 71), (72, 79)]], fill=CLEAR)
    # redraw arrow as a cut-out for clarity
    d.line([(u(72), u(61)), (u(72), u(75))], fill=CLEAR, width=u(4))
    d.polygon([(u(x), u(y)) for x, y in [(64, 70), (80, 70), (72, 79)]], fill=CLEAR)


def artie(d):              # paint palette
    d.ellipse(box(8, 14, 88, 82), outline=WHITE, width=u(LW))
    d.ellipse(box(54, 52, 72, 70), fill=CLEAR)           # thumb hole area cleared
    d.ellipse(box(56, 54, 70, 68), outline=WHITE, width=u(5))
    for cx, cy in ((30, 36), (48, 28), (66, 34), (28, 56)):
        d.ellipse(box(cx - 6, cy - 6, cx + 6, cy + 6), fill=WHITE)


def default(d):            # fallback for apps without their own icon
    g, t = 8, 32
    for i in range(2):
        for j in range(2):
            x0 = 12 + i * (t + g); y0 = 12 + j * (t + g)
            d.rounded_rectangle(box(x0, y0, x0 + t, y0 + t), radius=u(8), outline=WHITE, width=u(6))


ICONS = {
    "archive": archive, "terminal": terminal, "task": task, "logo_2048": logo_2048,
    "ppsspp": ppsspp, "portmaster": portmaster, "retroarch": retroarch, "scummvm": scummvm,
    "musudoku": musudoku, "vtree": vtree, "scrappy": scrappy, "artie": artie, "default": default,
}


def render(name, size):
    img, d = _canvas()
    ICONS[name](d)
    return img.resize((size, size), Image.LANCZOS)
