#!/usr/bin/env python3
"""Build the 'Ember' MustardOS theme for 640x480 (RG40XXV / RG40XXH)."""
import colorsys, copy, math, os, shutil, zipfile
import app_icons
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- palette
BG     = "1D1C1B"
BUTTON = "353433"
TEXT   = "E0E0E0"
ACCENT = "F7B954"
DIM    = "8C8580"   # derived: muted text / disabled
DEEP   = "141312"   # derived: shadows / darker panels

def rgb(h, a=255):
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (a,)

W, H = 640, 480
S = 4                       # supersample factor for smooth edges
HEADER_H = 36
FOOTER_H = 36

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "build", "Ember")
DIST = os.path.join(ROOT, "dist")
FONT_DIR = os.path.join(ROOT, "fonts")
F_SEMI = os.path.join(FONT_DIR, "Poppins-Medium.ttf")
F_BOLD = os.path.join(FONT_DIR, "Poppins-Bold.ttf")

# ---------------------------------------------------------------- icons
# Each icon draws into a square box (cx, cy, r) in supersampled space.
def ic_explore(d, cx, cy, r, c, bg):          # compass
    w = max(2, int(r * 0.13))
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=c, width=w)
    n = r * 0.62
    d.polygon([(cx, cy-n), (cx+n*0.32, cy), (cx, cy+n), (cx-n*0.32, cy)], fill=c)
    d.ellipse([cx-r*0.1, cy-r*0.1, cx+r*0.1, cy+r*0.1], fill=bg)

def ic_collection(d, cx, cy, r, c, bg):       # star
    pts = []
    for i in range(10):
        a = -math.pi/2 + i * math.pi/5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr*math.cos(a), cy + rr*math.sin(a) + r*0.06))
    d.polygon(pts, fill=c)

def ic_history(d, cx, cy, r, c, bg):          # clock with rewind arc
    w = max(2, int(r * 0.13))
    d.arc([cx-r, cy-r, cx+r, cy+r], start=-40, end=250, fill=c, width=w)
    # arrow head at arc start (~250deg)
    a = math.radians(250)
    ax, ay = cx + r*math.cos(a), cy + r*math.sin(a)
    s = r * 0.36
    d.polygon([(ax - s, ay - s*0.2), (ax + s*0.5, ay - s*0.9), (ax + s*0.4, ay + s*0.5)], fill=c)
    d.line([(cx, cy), (cx, cy - r*0.55)], fill=c, width=w)
    d.line([(cx, cy), (cx + r*0.42, cy + r*0.25)], fill=c, width=w)
    d.ellipse([cx-w, cy-w, cx+w, cy+w], fill=c)

def ic_apps(d, cx, cy, r, c, bg):             # 2x2 tiles
    g = r * 0.18
    t = (2*r - g) / 2
    for i in range(2):
        for j in range(2):
            x0 = cx - r + i*(t+g); y0 = cy - r + j*(t+g)
            d.rounded_rectangle([x0, y0, x0+t, y0+t], radius=t*0.28, fill=c)

def ic_info(d, cx, cy, r, c, bg):             # (i)
    w = max(2, int(r * 0.13))
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=c, width=w)
    d.ellipse([cx-r*0.13, cy-r*0.55, cx+r*0.13, cy-r*0.29], fill=c)
    d.rounded_rectangle([cx-r*0.11, cy-r*0.15, cx+r*0.11, cy+r*0.58], radius=r*0.05, fill=c)

def ic_config(d, cx, cy, r, c, bg):           # gear
    teeth = 8
    pts = []
    for i in range(teeth * 4):
        a = 2*math.pi * i / (teeth*4)
        rr = r if (i % 4) in (1, 2) else r * 0.76
        pts.append((cx + rr*math.cos(a), cy + rr*math.sin(a)))
    d.polygon(pts, fill=c)
    d.ellipse([cx-r*0.33, cy-r*0.33, cx+r*0.33, cy+r*0.33], fill=bg)

def ic_reboot(d, cx, cy, r, c, bg):           # circular arrow
    w = max(2, int(r * 0.14))
    d.arc([cx-r*0.9, cy-r*0.9, cx+r*0.9, cy+r*0.9], start=-60, end=230, fill=c, width=w)
    a = math.radians(-60)
    ax, ay = cx + r*0.9*math.cos(a), cy + r*0.9*math.sin(a)
    s = r * 0.38
    d.polygon([(ax - s*0.9, ay - s*0.3), (ax + s*0.5, ay - s*0.6), (ax + s*0.1, ay + s*0.8)], fill=c)

def ic_shutdown(d, cx, cy, r, c, bg):         # power symbol
    w = max(2, int(r * 0.14))
    d.arc([cx-r*0.9, cy-r*0.82, cx+r*0.9, cy+r*0.98], start=-55, end=235, fill=c, width=w)
    d.rounded_rectangle([cx-w/2, cy-r, cx+w/2, cy+r*0.05], radius=w/2, fill=c)

ITEMS = [  # name, label, icon fn, row
    ("explore",    "Explore",     ic_explore,    0),
    ("collection", "Collections", ic_collection, 0),
    ("history",    "History",     ic_history,    0),
    ("apps",       "Apps",        ic_apps,       1),
    ("info",       "Info",        ic_info,       1),
    ("config",     "Settings",    ic_config,     1),
    ("reboot",     "Restart",     ic_reboot,     1),
    ("shutdown",   "Shutdown",    ic_shutdown,   1),
]

# ---------------------------------------------------------------- layout
MARGIN = 16
GAP = 12
TOP_Y0, TOP_Y1 = HEADER_H + 8, 318
BOT_Y0, BOT_Y1 = TOP_Y1 + GAP, H - FOOTER_H - 8

def row_rects(n, y0, y1):
    total = W - 2*MARGIN - GAP*(n-1)
    widths = [total // n] * n
    for i in range(total - sum(widths)):
        widths[i] += 1
    rects, x = [], MARGIN
    for w in widths:
        rects.append((x, y0, x + w, y1)); x += w + GAP
    return rects

RECTS = row_rects(3, TOP_Y0, TOP_Y1) + row_rects(5, BOT_Y0, BOT_Y1)

def render_launch(focus, accent=None):
    accent = accent or ACCENT
    img = Image.new("RGBA", (W*S, H*S), rgb(BG))
    d = ImageDraw.Draw(img)
    f_big = ImageFont.truetype(F_BOLD, 22*S)
    f_small = ImageFont.truetype(F_SEMI, 13*S)
    for (name, label, fn, row), (x0, y0, x1, y1) in zip(ITEMS, RECTS):
        X0, Y0, X1, Y1 = x0*S, y0*S, x1*S, y1*S
        on = name == focus
        fill = rgb(accent) if on else rgb(BUTTON)
        fg = rgb(BG) if on else rgb(TEXT)
        # soft drop shadow
        d.rounded_rectangle([X0, Y0+3*S, X1, Y1+3*S], radius=14*S, fill=rgb(DEEP))
        d.rounded_rectangle([X0, Y0, X1, Y1], radius=14*S, fill=fill)
        cx = (X0 + X1) / 2
        if row == 0:
            r = 46*S
            cy = Y0 + (Y1 - Y0) * 0.42
            fn(d, cx, cy, r, fg, fill)
            tw = d.textlength(label, font=f_big)
            d.text((cx - tw/2, Y1 - 62*S), label, font=f_big, fill=fg)
        else:
            r = 19*S
            cy = Y0 + (Y1 - Y0) * 0.40
            fn(d, cx, cy, r, fg, fill)
            tw = d.textlength(label, font=f_small)
            d.text((cx - tw/2, Y1 - 30*S), label, font=f_small, fill=fg)
    return img.resize((W, H), Image.LANCZOS)

# ---------------------------------------------------------------- scheme files
def ini(sections):
    out = []
    for sec, kv in sections.items():
        out.append(f"[{sec}]")
        out += [f"{k}={v}" for k, v in kv.items()]
        out.append("")
    return "\n".join(out)

GLOBAL = {
    "background": {"BACKGROUND": BG, "BACKGROUND_ALPHA": 255,
                   "BACKGROUND_GRADIENT_COLOR": BG, "BACKGROUND_GRADIENT_DIRECTION": 0},
    "font": {"FONT_LIST_SIZE": 20, "FONT_HEADER_SIZE": 18, "FONT_FOOTER_SIZE": 16,
             "FONT_PANEL_SIZE": 16, "FONT_LIST_PAD_LEFT": 14, "FONT_LIST_PAD_RIGHT": 10,
             "FONT_LIST_PAD_TOP": 0, "FONT_LIST_PAD_BOTTOM": 0,
             "FONT_HEADER_PAD_TOP": 3, "FONT_HEADER_ICON_PAD_TOP": 0},
    "glyph": {"HEADER": 26},
    "status": {"ALIGN": 1, "PADDING_LEFT": 0, "PADDING_RIGHT": 10},
    "battery": {"BATTERY_NORMAL": TEXT, "BATTERY_ACTIVE": ACCENT, "BATTERY_LOW": "D35C54",
                "BATTERY_NORMAL_ALPHA": 255, "BATTERY_ACTIVE_ALPHA": 255, "BATTERY_LOW_ALPHA": 255},
    "network": {"NETWORK_NORMAL": DIM, "NETWORK_ACTIVE": ACCENT,
                "NETWORK_NORMAL_ALPHA": 255, "NETWORK_ACTIVE_ALPHA": 255},
    "bluetooth": {"BLUETOOTH_NORMAL": DIM, "BLUETOOTH_ACTIVE": ACCENT,
                  "BLUETOOTH_NORMAL_ALPHA": 255, "BLUETOOTH_ACTIVE_ALPHA": 255},
    "date": {"DATETIME_TEXT": TEXT, "DATETIME_ALPHA": 255, "DATETIME_ALIGN": 1,
             "PADDING_LEFT": 14, "PADDING_RIGHT": 0},
    "header": {"HEADER_HEIGHT": HEADER_H, "HEADER_BACKGROUND": BG, "HEADER_BACKGROUND_ALPHA": 255,
               "HEADER_TEXT": TEXT, "HEADER_TEXT_ALPHA": 255, "HEADER_TEXT_ALIGN": 2,
               "PADDING_LEFT": 0, "PADDING_RIGHT": 0},
    "footer": {"FOOTER_HEIGHT": FOOTER_H, "FOOTER_BACKGROUND": BG, "FOOTER_BACKGROUND_ALPHA": 255,
               "FOOTER_TEXT": TEXT, "FOOTER_TEXT_ALPHA": 255},
    "navigation": dict({"ALIGNMENT": 0, "SPACING": 8},
        **{f"NAV_{b}_{p}": v for b in ("LR", "UD", "A", "B", "C", "X", "Y", "Z", "MENU")
           for p, v in (("GLYPH", ACCENT), ("GLYPH_ALPHA", 255), ("GLYPH_RECOLOUR_ALPHA", 255),
                        ("TEXT", TEXT), ("TEXT_ALPHA", 255))}),
    "list": {
        "LIST_DEFAULT_RADIUS": 8,
        "LIST_DEFAULT_BACKGROUND": BUTTON, "LIST_DEFAULT_BACKGROUND_ALPHA": 0,
        "LIST_DEFAULT_GRADIENT_START": 0, "LIST_DEFAULT_GRADIENT_STOP": 0, "LIST_DEFAULT_GRADIENT_DIRECTION": 0,
        "LIST_DEFAULT_BORDER_WIDTH": 0, "LIST_DEFAULT_BORDER_SIDE": 0,
        "LIST_DEFAULT_INDICATOR": BUTTON, "LIST_DEFAULT_INDICATOR_ALPHA": 0,
        "LIST_DEFAULT_TEXT": TEXT, "LIST_DEFAULT_TEXT_ALPHA": 255,
        "LIST_DEFAULT_GLYPH_PAD_LEFT": 22, "LIST_DEFAULT_GLYPH_PAD_RIGHT": 8,
        "LIST_DEFAULT_GLYPH_ALPHA": 255, "LIST_DEFAULT_GLYPH_RECOLOUR": TEXT,
        "LIST_DEFAULT_GLYPH_RECOLOUR_ALPHA": 255, "LIST_DEFAULT_LABEL_LONG_MODE": 1,
        "LIST_DEFAULT_SHADOW_COLOUR": BG, "LIST_DEFAULT_SHADOW_ALPHA": 1,
        "LIST_DEFAULT_SHADOW_X_OFFSET": 0, "LIST_DEFAULT_SHADOW_Y_OFFSET": 0,
        "LIST_DISABLED_TEXT": DIM, "LIST_DISABLED_TEXT_ALPHA": 255,
        "LIST_FOCUS_BACKGROUND": BUTTON, "LIST_FOCUS_BACKGROUND_ALPHA": 255,
        "LIST_FOCUS_GRADIENT_START": 0, "LIST_FOCUS_GRADIENT_STOP": 0, "LIST_FOCUS_GRADIENT_DIRECTION": 0,
        "LIST_FOCUS_BORDER_WIDTH": 4, "LIST_FOCUS_BORDER_SIDE": 4,
        "LIST_FOCUS_INDICATOR": ACCENT, "LIST_FOCUS_INDICATOR_ALPHA": 255,
        "LIST_FOCUS_TEXT": ACCENT, "LIST_FOCUS_TEXT_ALPHA": 255,
        "LIST_FOCUS_GLYPH_ALPHA": 255, "LIST_FOCUS_GLYPH_RECOLOUR": ACCENT,
        "LIST_FOCUS_GLYPH_RECOLOUR_ALPHA": 255,
        "LIST_FOCUS_SHADOW_COLOUR": DEEP, "LIST_FOCUS_SHADOW_ALPHA": 160,
        "LIST_FOCUS_SHADOW_X_OFFSET": 0, "LIST_FOCUS_SHADOW_Y_OFFSET": 2,
    },
    "image_list": {"IMAGE_LIST_ALPHA": 255, "IMAGE_LIST_RADIUS": 10, "IMAGE_LIST_RECOLOUR": ACCENT,
                   "IMAGE_LIST_RECOLOUR_ALPHA": 0, "IMAGE_PREVIEW_ALPHA": 255,
                   "IMAGE_PREVIEW_RADIUS": 10, "IMAGE_PREVIEW_RECOLOUR": ACCENT,
                   "IMAGE_PREVIEW_RECOLOUR_ALPHA": 0},
    "help": {"HELP_BACKGROUND": BUTTON, "HELP_BACKGROUND_ALPHA": 255, "HELP_BORDER": ACCENT,
             "HELP_BORDER_ALPHA": 255, "HELP_CONTENT": TEXT, "HELP_TITLE": ACCENT, "HELP_RADIUS": 10},
    "dialogue": {"DIALOGUE_BACKGROUND": BUTTON, "DIALOGUE_BACKGROUND_ALPHA": 255,
                 "DIALOGUE_BORDER": ACCENT, "DIALOGUE_BORDER_ALPHA": 255, "DIALOGUE_TITLE": ACCENT,
                 "DIALOGUE_CONTENT": TEXT, "DIALOGUE_OPTION": BG, "DIALOGUE_DIM_ALPHA": 150,
                 "DIALOGUE_SELECTION": ACCENT, "DIALOGUE_SELECTION_ALPHA": 255,
                 "DIALOGUE_RADIUS_MAIN": 12, "DIALOGUE_RADIUS_SELECTED": 8,
                 "DIALOGUE_SHADOW_COLOUR": "000000", "DIALOGUE_SHADOW_ALPHA": 160,
                 "DIALOGUE_SHADOW_X_OFFSET": 0, "DIALOGUE_SHADOW_Y_OFFSET": 4,
                 "DIALOGUE_SHADOW_COLOUR_FOCUS": DEEP, "DIALOGUE_SHADOW_ALPHA_FOCUS": 96,
                 "DIALOGUE_SHADOW_X_OFFSET_FOCUS": 0, "DIALOGUE_SHADOW_Y_OFFSET_FOCUS": 2},
    "grid": {"BACKGROUND": BG, "BACKGROUND_ALPHA": 0},
    "charging": {"CHARGER_BACKGROUND": BG, "CHARGER_BACKGROUND_ALPHA": 255,
                 "CHARGER_TEXT": ACCENT, "CHARGER_TEXT_ALPHA": 255, "CHARGER_Y_POS": 100},
    "verbose": {"VERBOSE_BOOT_BACKGROUND": BG, "VERBOSE_BOOT_BACKGROUND_ALPHA": 255,
                "VERBOSE_BOOT_TEXT": TEXT, "VERBOSE_BOOT_TEXT_ALPHA": 255, "VERBOSE_BOOT_Y_POS": 165},
    "keyboard": {"OSK_BACKGROUND": BG, "OSK_BACKGROUND_ALPHA": 255, "OSK_BORDER": ACCENT,
                 "OSK_BORDER_ALPHA": 255, "OSK_RADIUS": 12, "OSK_TEXT": TEXT, "OSK_TEXT_ALPHA": 255,
                 "OSK_TEXT_FOCUS": BG, "OSK_TEXT_FOCUS_ALPHA": 255,
                 "OSK_ITEM_BACKGROUND": BUTTON, "OSK_ITEM_BACKGROUND_ALPHA": 255,
                 "OSK_ITEM_BACKGROUND_FOCUS": ACCENT, "OSK_ITEM_BACKGROUND_FOCUS_ALPHA": 255,
                 "OSK_ITEM_BORDER": BUTTON, "OSK_ITEM_BORDER_ALPHA": 0,
                 "OSK_ITEM_BORDER_FOCUS": ACCENT, "OSK_ITEM_BORDER_FOCUS_ALPHA": 255,
                 "OSK_ITEM_RADIUS": 6, "OSK_ITEM_SHADOW_COLOUR": DEEP,
                 "OSK_ITEM_SHADOW_COLOUR_FOCUS": DEEP},
    "notification": {"MSG_BACKGROUND": BUTTON, "MSG_BACKGROUND_ALPHA": 255, "MSG_BORDER": ACCENT,
                     "MSG_BORDER_ALPHA": 255, "MSG_RADIUS": 10, "MSG_TEXT": TEXT, "MSG_TEXT_ALPHA": 255,
                     # status colours stay fixed across accents
                     "MSG_LEVEL_SUCCESS": "7FCF8E", "MSG_LEVEL_WARNING": "F2C14E", "MSG_LEVEL_ERROR": "D35C54"},
    "bar": {"BAR_WIDTH": 600, "BAR_HEIGHT": 42, "BAR_BACKGROUND": BUTTON, "BAR_BACKGROUND_ALPHA": 255,
            "BAR_BORDER": BUTTON, "BAR_BORDER_ALPHA": 255, "BAR_RADIUS": 12,
            "BAR_PROGRESS_WIDTH": 520, "BAR_PROGRESS_HEIGHT": 14,
            "BAR_PROGRESS_BACKGROUND": BG, "BAR_PROGRESS_BACKGROUND_ALPHA": 255,
            "BAR_PROGRESS_ACTIVE_BACKGROUND": ACCENT, "BAR_PROGRESS_ACTIVE_BACKGROUND_ALPHA": 255,
            "BAR_PROGRESS_RADIUS": 7, "BAR_ICON": ACCENT, "BAR_ICON_ALPHA": 255, "BAR_Y_POS": 392},
    "roll": {"ROLL_TEXT": TEXT, "ROLL_TEXT_ALPHA": 255, "ROLL_BACKGROUND": BUTTON,
             "ROLL_BACKGROUND_ALPHA": 255, "ROLL_RADIUS": 10, "ROLL_SELECT_TEXT": BG,
             "ROLL_SELECT_TEXT_ALPHA": 255, "ROLL_SELECT_BACKGROUND": ACCENT,
             "ROLL_SELECT_BACKGROUND_ALPHA": 255, "ROLL_SELECT_RADIUS": 10,
             "ROLL_BORDER_COLOUR": ACCENT, "ROLL_BORDER_ALPHA": 255, "ROLL_BORDER_RADIUS": 12},
    "counter": {"COUNTER_ALIGNMENT": 2, "COUNTER_PADDING_AROUND": 6, "COUNTER_PADDING_SIDE": 10,
                "COUNTER_PADDING_TOP": 42, "COUNTER_BORDER_COLOUR": ACCENT, "COUNTER_BORDER_ALPHA": 0,
                "COUNTER_BORDER_WIDTH": 0, "COUNTER_RADIUS": 4, "COUNTER_BACKGROUND": BUTTON,
                "COUNTER_BACKGROUND_ALPHA": 230, "COUNTER_TEXT": ACCENT, "COUNTER_TEXT_ALPHA": 255,
                "COUNTER_TEXT_FADE_TIME": 50, "COUNTER_TEXT_SEPARATOR": " / "},
    "terminal": {"FONT_SIZE": 16, "FOREGROUND": TEXT, "BACKGROUND": BG},
    "misc": {"ANTIALIASING": 1, "STATIC_ALIGNMENT": 0, "IMAGE_OVERLAY": 0},
}

CONTENT_H = H - HEADER_H - FOOTER_H - 8   # 400
DEFAULT_640 = {
    "misc": {"CONTENT_PADDING_LEFT": 8, "CONTENT_PADDING_TOP": 2, "CONTENT_WIDTH": 624,
             "CONTENT_HEIGHT": CONTENT_H, "CONTENT_ITEM_COUNT": 10, "CONTENT_ALIGNMENT": 0,
             "NAVIGATION_TYPE": 2},
}

LAUNCH = {
    "header": {"HEADER_BACKGROUND_ALPHA": 0, "HEADER_TEXT_ALPHA": 0},
    "footer": {"FOOTER_BACKGROUND_ALPHA": 0},
    "list": {k: 0 for k in ("LIST_DEFAULT_BACKGROUND_ALPHA", "LIST_DEFAULT_INDICATOR_ALPHA",
                            "LIST_DEFAULT_TEXT_ALPHA", "LIST_DEFAULT_GLYPH_ALPHA",
                            "LIST_DEFAULT_GLYPH_RECOLOUR_ALPHA", "LIST_FOCUS_BACKGROUND_ALPHA",
                            "LIST_FOCUS_INDICATOR_ALPHA", "LIST_FOCUS_TEXT_ALPHA",
                            "LIST_FOCUS_GLYPH_ALPHA", "LIST_FOCUS_GLYPH_RECOLOUR_ALPHA",
                            "LIST_DEFAULT_BORDER_WIDTH", "LIST_FOCUS_BORDER_WIDTH",
                            "LIST_FOCUS_SHADOW_X_OFFSET", "LIST_FOCUS_SHADOW_Y_OFFSET")},
    "misc": {"NAVIGATION_TYPE": 5, "STATIC_ALIGNMENT": 3, "CONTENT_ITEM_COUNT": 8},
}
LAUNCH["list"].update({"LIST_DEFAULT_SHADOW_ALPHA": 1, "LIST_FOCUS_SHADOW_ALPHA": 1})

# Game lists: slim list on the left, the rest of the screen left free for box art.
LIST_W = 248
def content_list():
    return {
        "font": {"FONT_LIST_SIZE": 18, "FONT_LIST_PAD_LEFT": 12},
        "misc": {"CONTENT_PADDING_LEFT": 6, "CONTENT_WIDTH": LIST_W, "CONTENT_ITEM_COUNT": 12,
                 "CONTENT_HEIGHT": CONTENT_H, "CONTENT_PADDING_TOP": 2},
        "list": {"LIST_DEFAULT_GLYPH_PAD_LEFT": 18},
    }

def grid_block(cols, rows, label_offset, art_only=False, square=False):
    col_w = (W - 16) // cols
    row_h = (H - HEADER_H - FOOTER_H - 8) // rows
    loc_x = 8
    if square:                       # equal 8px gaps, cells sized by row height
        col_w = row_h
        loc_x = (W - cols * col_w) // 2
    cell_gap = 8 if square else 10   # square: 192px cells, 184px inside the 4px border
    g = {
        "NAVIGATION_TYPE": 2, "ALIGNMENT": 0, "ALIGNMENT_X_OFFSET": 0, "ALIGNMENT_Y_OFFSET": 0,
        "BACKGROUND": BG, "BACKGROUND_ALPHA": 0,
        "LOCATION_X": loc_x, "LOCATION_Y": HEADER_H + 4,
        "COLUMN_COUNT": cols, "ROW_COUNT": rows, "COLUMN_WIDTH": col_w, "ROW_HEIGHT": row_h,
        "COLUMN_PADDING": 0, "ROW_PADDING": 0, "CELL_COLUMN_ALIGN": 1, "CELL_ROW_ALIGN": 1,
        "CELL_WIDTH": col_w - cell_gap, "CELL_HEIGHT": row_h - cell_gap, "CELL_RADIUS": 4,
        "CELL_BORDER_WIDTH": 4, "CELL_IMAGE_PADDING_TOP": 8, "CELL_TEXT_PADDING_BOTTOM": 8,
        "CELL_TEXT_PADDING_SIDE": 8, "CELL_TEXT_LINE_SPACING": -2,
        "CELL_SHADOW": DEEP, "CELL_SHADOW_WIDTH": 6, "CELL_SHADOW_X_OFFSET": 0, "CELL_SHADOW_Y_OFFSET": 3,
        "CELL_DEFAULT_BACKGROUND": BUTTON, "CELL_DEFAULT_BACKGROUND_ALPHA": 255,
        "CELL_DEFAULT_BACKGROUND_GRADIENT_COLOR": BUTTON, "CELL_DEFAULT_BACKGROUND_GRADIENT_DIRECTION": 0,
        "CELL_DEFAULT_BORDER": BUTTON, "CELL_DEFAULT_BORDER_ALPHA": 255,
        "CELL_DEFAULT_IMAGE_ALPHA": 255, "CELL_DEFAULT_IMAGE_RECOLOUR": TEXT,
        "CELL_DEFAULT_IMAGE_RECOLOUR_ALPHA": 0,
        "CELL_DEFAULT_TEXT": TEXT, "CELL_DEFAULT_TEXT_ALPHA": 255,
        "CELL_FOCUS_BACKGROUND": BUTTON, "CELL_FOCUS_BACKGROUND_ALPHA": 255,
        "CELL_FOCUS_BACKGROUND_GRADIENT_COLOR": BUTTON, "CELL_FOCUS_BACKGROUND_GRADIENT_DIRECTION": 0,
        "CELL_FOCUS_BORDER": ACCENT, "CELL_FOCUS_BORDER_ALPHA": 255,
        "CELL_FOCUS_IMAGE_ALPHA": 255, "CELL_FOCUS_IMAGE_RECOLOUR": ACCENT,
        "CELL_FOCUS_IMAGE_RECOLOUR_ALPHA": 0,
        "CELL_FOCUS_TEXT": ACCENT, "CELL_FOCUS_TEXT_ALPHA": 255,
        "CELL_FOCUS_GLOW": ACCENT, "CELL_FOCUS_GLOW_WIDTH": 0,
        "CURRENT_ITEM_LABEL_BACKGROUND_GRADIENT_COLOR": ACCENT, "CURRENT_ITEM_LABEL_SHADOW": DEEP,
        # floating name of the focused item, hidden by default (cells carry their own label)
        "CURRENT_ITEM_LABEL_ALIGNMENT": 5, "CURRENT_ITEM_LABEL_WIDTH": 0, "CURRENT_ITEM_LABEL_HEIGHT": 0,
        "CURRENT_ITEM_LABEL_OFFSET_X": 0, "CURRENT_ITEM_LABEL_OFFSET_Y": label_offset,
        "CURRENT_ITEM_LABEL_RADIUS": 10, "CURRENT_ITEM_LABEL_BORDER_WIDTH": 0,
        "CURRENT_ITEM_LABEL_BORDER": ACCENT, "CURRENT_ITEM_LABEL_BORDER_ALPHA": 0,
        "CURRENT_ITEM_LABEL_BACKGROUND": ACCENT, "CURRENT_ITEM_LABEL_BACKGROUND_ALPHA": 0,
        "CURRENT_ITEM_LABEL_TEXT": BG, "CURRENT_ITEM_LABEL_TEXT_ALPHA": 0,
        "CURRENT_ITEM_LABEL_TEXT_ALIGNMENT": 2,
    }
    if art_only:
        g.update({
            # cards show only artwork, centred in the cell
            "CELL_DEFAULT_TEXT_ALPHA": 0, "CELL_FOCUS_TEXT_ALPHA": 0, "CELL_IMAGE_PADDING_TOP": 0,
            "CELL_TEXT_PADDING_BOTTOM": 0, "CELL_TEXT_PADDING_SIDE": 0,
            "CELL_DEFAULT_IMAGE_ALPHA": 255,
            # focused title scrolls in the header, between the clock and status icons
            "CURRENT_ITEM_LABEL_ALIGNMENT": 2, "CURRENT_ITEM_LABEL_WIDTH": 340,
            "CURRENT_ITEM_LABEL_HEIGHT": HEADER_H - 4, "CURRENT_ITEM_LABEL_OFFSET_X": 0,
            "CURRENT_ITEM_LABEL_OFFSET_Y": 2, "CURRENT_ITEM_LABEL_LABEL_LONG_MODE": 1,
            "CURRENT_ITEM_LABEL_TEXT": ACCENT, "CURRENT_ITEM_LABEL_TEXT_ALPHA": 255,
            "CURRENT_ITEM_LABEL_TEXT_PADDING_TOP": 3, "CURRENT_ITEM_LABEL_TEXT_PADDING_BOTTOM": 0,
            "CURRENT_ITEM_LABEL_TEXT_PADDING_LEFT": 4, "CURRENT_ITEM_LABEL_TEXT_PADDING_RIGHT": 4,
        })
    return g

ART_SCREEN = {
    "header": {"HEADER_TEXT_ALPHA": 0, "HEADER_BACKGROUND_ALPHA": 0},
    "counter": {"COUNTER_ALIGNMENT": 2, "COUNTER_PADDING_SIDE": 6,
                "COUNTER_PADDING_TOP": H - FOOTER_H + 4, "COUNTER_PADDING_AROUND": 4},
}
PLORE = content_list(); PLORE["grid"] = grid_block(3, 2, -44, art_only=True, square=True); PLORE.update(ART_SCREEN)
COLLECT = content_list(); COLLECT["grid"] = grid_block(3, 2, -44, art_only=True, square=True); COLLECT.update(ART_SCREEN)
HISTORY = content_list(); HISTORY["grid"] = grid_block(3, 2, -44, art_only=True, square=True); HISTORY.update(ART_SCREEN)
APP_ICON = 64
APP = {"grid": grid_block(4, 3, -44)}                               # apps: 4x3, icon + name
APP["grid"].update({
    "CELL_IMAGE_PADDING_TOP": 14, "CELL_TEXT_PADDING_BOTTOM": 10, "CELL_TEXT_PADDING_SIDE": 6,
    # icons are white line art; tint them text-grey normally and amber when focused
    "CELL_DEFAULT_IMAGE_RECOLOUR": TEXT, "CELL_DEFAULT_IMAGE_RECOLOUR_ALPHA": 255,
    "CELL_FOCUS_IMAGE_RECOLOUR": ACCENT, "CELL_FOCUS_IMAGE_RECOLOUR_ALPHA": 255,
})

# ---------------------------------------------------------------- user overrides
# Settings tuned on-device (override-Selection.zip). Applied last, so they win.
GLYPH_30 = {"glyph": {"FOOTER": 30, "HEADER": 30}}
GRID_SELECTION = {
    "grid": {
        # focused title: left-aligned in the header, after the clock
        "CURRENT_ITEM_LABEL_ALIGNMENT": 1, "CURRENT_ITEM_LABEL_BACKGROUND": "000000",
        "CURRENT_ITEM_LABEL_BACKGROUND_ALPHA": 0, "CURRENT_ITEM_LABEL_LABEL_LONG_MODE": 1,
        "CURRENT_ITEM_LABEL_WIDTH": 400, "CURRENT_ITEM_LABEL_HEIGHT": 40,
        "CURRENT_ITEM_LABEL_OFFSET_X": 80, "CURRENT_ITEM_LABEL_OFFSET_Y": 3,
        "CURRENT_ITEM_LABEL_TEXT_ALIGNMENT": 2, "CURRENT_ITEM_LABEL_TEXT": "EEEEEE",
        "CURRENT_ITEM_LABEL_TEXT_ALPHA": 255,
        # focused card: art faded over a white card with a gold border
        "CELL_FOCUS_BACKGROUND": "FFFFFF", "CELL_FOCUS_BACKGROUND_ALPHA": 255,
        "CELL_FOCUS_IMAGE_RECOLOUR_ALPHA": 0, "CELL_FOCUS_IMAGE_ALPHA": 100,
        "CELL_FOCUS_IMAGE_RECOLOUR": "000000", "CELL_FOCUS_BORDER": "FFC53B",
        "CELL_FOCUS_BORDER_ALPHA": 255, "CELL_RADIUS": 4, "CELL_DEFAULT_TEXT_ALPHA": 0,
    },
    "header": {"HEADER_TEXT_ALPHA": 0, "HEADER_BACKGROUND_ALPHA": 0},
    **GLYPH_30,
}
USER_OVERRIDES = [
    (LAUNCH, GLYPH_30), (APP, GLYPH_30),
    (PLORE, GRID_SELECTION), (HISTORY, GRID_SELECTION),
]

def merge(dst, src):
    for sec, kv in src.items():
        dst.setdefault(sec, {}).update(kv)

for target, ovr in USER_OVERRIDES:
    merge(target, ovr)

# ---------------------------------------------------------------- accent alternatives
# Each one appears under Customisation > Alternative Theme.
ACCENTS = {
    "Amber":     "F7B954",
    "Tangerine": "F28F55",
    "Rose":      "F08CA8",
    "Lavender":  "B8A2F0",
    "Sky":       "79BEF0",
    "Teal":      "5FCDC3",
    "Mint":      "86D69A",
    "Lime":      "C3D663",
}
BRIGHT_BORDER = "FFC53B"   # brighter gold used on the game-grid focus border

def brighten(hexc):
    """Same shift Amber -> FFC53B: a touch more saturation, full value."""
    r, g, b = (int(hexc[i:i+2], 16) / 255 for i in (0, 2, 4))
    h, sat, v = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(h, min(1.0, sat * 1.17), 1.0)
    return "".join(f"{round(c * 255):02X}" for c in (r, g, b))

def recolour(data, accent):
    out = copy.deepcopy(data)
    if accent.upper() == ACCENT.upper():
        return out          # base palette, including the hand-picked FFC53B border
    for kv in out.values():
        for k, v in kv.items():
            if isinstance(v, str) and v.upper() == ACCENT.upper():
                kv[k] = accent
            elif isinstance(v, str) and v.upper() == BRIGHT_BORDER:
                kv[k] = brighten(accent)
    return out

def build_accents(res):
    """alternate/<Name>.muxalt holds every accent-dependent file. Choosing an alternative
    extracts it over the theme (MustardOS 2606.0 behaviour), replacing the schemes and the
    main-menu tiles; Amber's archive puts the original files back."""
    alt_root = os.path.join(OUT, "alternate")
    os.makedirs(alt_root)
    schemes = {"scheme/global.ini": GLOBAL, "640x480/scheme/default.ini": DEFAULT_640,
               "640x480/scheme/muxlaunch.ini": LAUNCH, "640x480/scheme/muxplore.ini": PLORE,
               "640x480/scheme/muxcollect.ini": COLLECT, "640x480/scheme/muxhistory.ini": HISTORY,
               "640x480/scheme/muxapp.ini": APP}
    tmp = os.path.join(OUT, ".tmp.png")
    for name, accent in ACCENTS.items():
        with zipfile.ZipFile(os.path.join(alt_root, f"{name}.muxalt"), "w", zipfile.ZIP_DEFLATED) as z:
            for path, data in schemes.items():
                z.writestr(path, ini(recolour(data, accent)))
            for item, *_ in ITEMS:
                render_launch(item, accent).convert("RGB").save(tmp, optimize=True)
                z.write(tmp, f"640x480/image/static/muxlaunch/{item}.png")
    os.remove(tmp)

# ---------------------------------------------------------------- build
def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    res = os.path.join(OUT, "640x480")
    os.makedirs(os.path.join(OUT, "scheme"))
    os.makedirs(os.path.join(res, "scheme"))
    os.makedirs(os.path.join(res, "image", "static", "muxlaunch"))
    os.makedirs(os.path.join(res, "image", "wall"))
    os.makedirs(os.path.join(OUT, "font"))
    app_dir = os.path.join(OUT, "catalogue", "Application", "grid")
    os.makedirs(app_dir)
    # user-supplied artwork: console cards, collection art, extra app icons
    user_cat = os.path.join(ROOT, "assets", "catalogue")
    for sub in ("Folder", "Collection"):
        src = os.path.join(user_cat, sub)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(OUT, "catalogue", sub))
    extra = os.path.join(user_cat, "Application", "grid", "extra")
    if os.path.isdir(extra):
        for fn in os.listdir(extra):          # only icons this theme doesn't draw itself
            if os.path.splitext(fn)[0] not in app_icons.ICONS:
                im = Image.open(os.path.join(extra, fn)).convert("RGBA")
                im.thumbnail((APP_ICON, APP_ICON), Image.LANCZOS)   # match the drawn icons
                im.save(os.path.join(app_dir, fn), optimize=True)
    for icon in app_icons.ICONS:
        app_icons.render(icon, APP_ICON).save(os.path.join(app_dir, f"{icon}.png"), optimize=True)

    for name, *_ in ITEMS:
        render_launch(name).convert("RGB").save(
            os.path.join(res, "image", "static", "muxlaunch", f"{name}.png"), optimize=True)

    Image.new("RGB", (W, H), rgb(BG)[:3]).save(os.path.join(res, "image", "wall", "default.png"))

    prev = Image.open(os.path.join(res, "image", "static", "muxlaunch", "explore.png"))
    prev.resize((288, 216), Image.LANCZOS).save(os.path.join(res, "preview.png"))

    files = {
        os.path.join(OUT, "scheme", "global.ini"): GLOBAL,
        os.path.join(res, "scheme", "default.ini"): DEFAULT_640,
        os.path.join(res, "scheme", "muxlaunch.ini"): LAUNCH,
        os.path.join(res, "scheme", "muxplore.ini"): PLORE,
        os.path.join(res, "scheme", "muxcollect.ini"): COLLECT,
        os.path.join(res, "scheme", "muxhistory.ini"): HISTORY,
        os.path.join(res, "scheme", "muxapp.ini"): APP,
    }
    for path, data in files.items():
        with open(path, "w") as fh:
            fh.write(ini(data))

    shutil.copy(F_SEMI, os.path.join(OUT, "font", "default.ttf"))
    shutil.copy(os.path.join(FONT_DIR, "OFL.txt"), os.path.join(OUT, "font-license.txt"))
    build_accents(res)
    with open(os.path.join(OUT, "name.txt"), "w") as fh: fh.write("Ember\n")
    with open(os.path.join(OUT, "version.txt"), "w") as fh: fh.write("2606.0\n")
    with open(os.path.join(OUT, "credits.txt"), "w") as fh:
        fh.write("Ember theme for MustardOS (640x480 - RG40XXV / RG40XXH)\n"
                 "Main menu layout inspired by OneTwo by bulkh.\n"
                 "Font: Poppins by Indian Type Foundry, SIL Open Font License 1.1.\n")

    os.makedirs(DIST, exist_ok=True)
    pkg = os.path.join(DIST, "Ember.muxthm")
    with zipfile.ZipFile(pkg, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, _, fns in os.walk(OUT):
            for fn in fns:
                full = os.path.join(dp, fn)
                z.write(full, os.path.relpath(full, OUT))
    print("built", pkg)

if __name__ == "__main__":
    build()
