"""Original line-style app icons for the Ember theme.

Drawn white on transparent so the theme can recolour them (amber when focused).
File names match each app's ICON value, which is what MustardOS uses to find
grid images in {theme}/catalogue/Application/grid/.

Every icon is designed on a 96x96 grid. Coordinates in the drawing functions
are in those design units and are scaled up for supersampling before drawing.
"""
import os

from PIL import Image, ImageDraw, ImageFont

BOLD_FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Poppins-Bold.ttf")
WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)
SUPERSAMPLE = 8          # draw this many times larger, then shrink for smooth edges
DESIGN_SIZE = 96         # icon design grid, in design units
STROKE_WIDTH = 7         # standard line thickness, in design units


def new_canvas():
    image = Image.new("RGBA", (DESIGN_SIZE * SUPERSAMPLE, DESIGN_SIZE * SUPERSAMPLE), TRANSPARENT)
    return image, ImageDraw.Draw(image)


def scale(design_units):
    """Convert design units to supersampled pixels."""
    return design_units * SUPERSAMPLE


def box(left, top, right, bottom):
    return [scale(left), scale(top), scale(right), scale(bottom)]


def outlined_rect(draw, left, top, right, bottom, corner_radius, stroke=STROKE_WIDTH):
    draw.rounded_rectangle(box(left, top, right, bottom), radius=scale(corner_radius),
                           outline=WHITE, width=scale(stroke))


def polyline(draw, points, stroke=STROKE_WIDTH):
    """Joined line through the points, with rounded ends."""
    draw.line([(scale(x), scale(y)) for x, y in points], fill=WHITE, width=scale(stroke), joint="curve")
    for x, y in (points[0], points[-1]):
        half = stroke / 2
        draw.ellipse(box(x - half, y - half, x + half, y + half), fill=WHITE)


def centred_text(draw, text, centre_x, centre_y, font_size):
    font = ImageFont.truetype(BOLD_FONT_PATH, scale(font_size))
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = right - left, bottom - top
    position = (scale(centre_x) - text_width / 2 - left, scale(centre_y) - text_height / 2 - top)
    draw.text(position, text, font=font, fill=WHITE)


def dot(draw, centre_x, centre_y, radius, fill=WHITE):
    draw.ellipse(box(centre_x - radius, centre_y - radius, centre_x + radius, centre_y + radius), fill=fill)


# ------------------------------------------------------------------ icons
def archive(draw):            # package with a down arrow
    outlined_rect(draw, 14, 30, 82, 84, 8)
    polyline(draw, [(14, 30), (24, 14), (72, 14), (82, 30)])
    polyline(draw, [(48, 40), (48, 70)])
    polyline(draw, [(36, 58), (48, 70), (60, 58)])


def terminal(draw):           # window with a prompt
    outlined_rect(draw, 10, 16, 86, 80, 10)
    polyline(draw, [(26, 38), (38, 48), (26, 58)])
    polyline(draw, [(46, 60), (66, 60)])


def task(draw):               # toolbox
    outlined_rect(draw, 12, 34, 84, 82, 8)
    polyline(draw, [(36, 34), (36, 22), (60, 22), (60, 34)])
    polyline(draw, [(12, 54), (84, 54)])
    draw.rounded_rectangle(box(42, 48, 54, 62), radius=scale(3), fill=WHITE)


def logo_2048(draw):          # tile with "2048"
    draw.rounded_rectangle(box(10, 10, 86, 86), radius=scale(14), fill=WHITE)
    draw.rounded_rectangle(box(18, 18, 78, 78), radius=scale(8), fill=TRANSPARENT)
    centred_text(draw, "2048", 48, 49, 21)


def ppsspp(draw):             # widescreen handheld
    outlined_rect(draw, 6, 28, 90, 70, 20)
    outlined_rect(draw, 30, 36, 66, 62, 3, stroke=5)
    draw.ellipse(box(14, 44, 22, 52), fill=WHITE)
    for button_x, button_y in ((78, 42), (78, 56), (72, 49), (84, 49)):
        dot(draw, button_x, button_y, 3)


def portmaster(draw):         # anchor
    draw.ellipse(box(40, 10, 56, 26), outline=WHITE, width=scale(6))
    polyline(draw, [(48, 26), (48, 84)])
    polyline(draw, [(34, 38), (62, 38)])
    draw.arc(box(18, 36, 78, 86), start=20, end=160, fill=WHITE, width=scale(STROKE_WIDTH))
    polyline(draw, [(14, 58), (22, 66), (30, 58)], stroke=6)
    polyline(draw, [(66, 58), (74, 66), (82, 58)], stroke=6)


def retroarch(draw):          # gamepad
    draw.rounded_rectangle(box(8, 28, 88, 72), radius=scale(22), outline=WHITE, width=scale(STROKE_WIDTH))
    polyline(draw, [(22, 50), (38, 50)], stroke=6)
    polyline(draw, [(30, 42), (30, 58)], stroke=6)
    draw.ellipse(box(58, 40, 68, 50), fill=WHITE)
    draw.ellipse(box(68, 50, 78, 60), fill=WHITE)


def scummvm(draw):            # point-and-click cursor
    outline = [(28, 12), (28, 76), (44, 62), (54, 84), (64, 80), (54, 58), (74, 58)]
    draw.polygon([(scale(x), scale(y)) for x, y in outline], outline=WHITE, width=scale(6))
    draw.line([(scale(x), scale(y)) for x, y in outline + [outline[0]]],
              fill=WHITE, width=scale(6), joint="curve")


def musudoku(draw):           # 3x3 grid with digits
    outlined_rect(draw, 10, 10, 86, 86, 10)
    # the outline is drawn inward, so the inner area spans 17..79
    for grid_line in (37.7, 58.3):
        polyline(draw, [(grid_line, 17), (grid_line, 79)], stroke=4)
        polyline(draw, [(17, grid_line), (79, grid_line)], stroke=4)
    centred_text(draw, "1", 27.3, 27.3, 15)
    centred_text(draw, "5", 48, 48, 15)
    centred_text(draw, "9", 68.7, 68.7, 15)


def vtree(draw):              # file tree
    draw.rounded_rectangle(box(12, 12, 40, 32), radius=scale(4), fill=WHITE)
    polyline(draw, [(22, 32), (22, 72)], stroke=6)
    polyline(draw, [(22, 48), (44, 48)], stroke=6)
    polyline(draw, [(22, 72), (44, 72)], stroke=6)
    for branch_top in (40, 64):
        draw.rounded_rectangle(box(48, branch_top, 84, branch_top + 18), radius=scale(4),
                               outline=WHITE, width=scale(6))


def scrappy(draw):            # picture with a download badge
    outlined_rect(draw, 8, 14, 74, 70, 8)
    mountains = [(16, 62), (34, 38), (48, 54), (56, 46), (66, 62)]
    draw.polygon([(scale(x), scale(y)) for x, y in mountains], fill=WHITE)
    draw.ellipse(box(50, 22, 60, 32), fill=WHITE)            # sun
    draw.ellipse(box(54, 52, 90, 88), fill=TRANSPARENT)      # gap around the badge
    draw.ellipse(box(57, 55, 87, 85), fill=WHITE)            # badge
    polyline(draw, [(72, 62), (72, 76)], stroke=4)
    arrow_head = [(65, 71), (79, 71), (72, 79)]
    draw.polygon([(scale(x), scale(y)) for x, y in arrow_head], fill=TRANSPARENT)
    # cut the arrow out of the badge
    draw.line([(scale(72), scale(61)), (scale(72), scale(75))], fill=TRANSPARENT, width=scale(4))
    arrow_head_cutout = [(64, 70), (80, 70), (72, 79)]
    draw.polygon([(scale(x), scale(y)) for x, y in arrow_head_cutout], fill=TRANSPARENT)


def artie(draw):              # paint palette
    draw.ellipse(box(8, 14, 88, 82), outline=WHITE, width=scale(STROKE_WIDTH))
    draw.ellipse(box(54, 52, 72, 70), fill=TRANSPARENT)     # clear space for the thumb hole
    draw.ellipse(box(56, 54, 70, 68), outline=WHITE, width=scale(5))
    for paint_x, paint_y in ((30, 36), (48, 28), (66, 34), (28, 56)):
        dot(draw, paint_x, paint_y, 6)


def default(draw):            # fallback for apps without their own icon
    gap, tile_size = 8, 32
    for column in range(2):
        for row in range(2):
            left = 12 + column * (tile_size + gap)
            top = 12 + row * (tile_size + gap)
            draw.rounded_rectangle(box(left, top, left + tile_size, top + tile_size), radius=scale(8),
                                   outline=WHITE, width=scale(6))


ICONS = {
    "archive": archive, "terminal": terminal, "task": task, "logo_2048": logo_2048,
    "ppsspp": ppsspp, "portmaster": portmaster, "retroarch": retroarch, "scummvm": scummvm,
    "musudoku": musudoku, "vtree": vtree, "scrappy": scrappy, "artie": artie, "default": default,
}


def render(icon_name, size):
    image, draw = new_canvas()
    ICONS[icon_name](draw)
    return image.resize((size, size), Image.LANCZOS)
