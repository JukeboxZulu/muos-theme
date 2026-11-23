#!/usr/bin/env python3
"""Build the 'Ember' MustardOS theme for 640x480 (RG40XXV / RG40XXH)."""
import colorsys
import copy
import io
import math
import os
import shutil
import zipfile

from PIL import Image, ImageDraw, ImageFont

import app_icons

# ---------------------------------------------------------------- palette
BACKGROUND = "181715"
BUTTON = "2c2b2a"
TEXT = "E0E0E0"
ACCENT = "FFB43C"
MUTED_TEXT = "8C8580"   # derived: muted text / disabled items
SHADOW = "0a0908"       # derived: shadows / darker panels


def rgba(hex_colour, alpha=255):
    red, green, blue = (int(hex_colour[offset:offset + 2], 16) for offset in (0, 2, 4))
    return (red, green, blue, alpha)


SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
SUPERSAMPLE = 4          # draw the main menu this many times larger, then shrink for smooth edges
HEADER_HEIGHT = 36
FOOTER_HEIGHT = 36

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
THEME_DIR = os.path.join(REPO_DIR, "build", "Ember")
DIST_DIR = os.path.join(REPO_DIR, "dist")
FONT_DIR = os.path.join(REPO_DIR, "fonts")
MEDIUM_FONT_PATH = os.path.join(FONT_DIR, "Poppins-Medium.ttf")
BOLD_FONT_PATH = os.path.join(FONT_DIR, "Poppins-Bold.ttf")

# ---------------------------------------------------------------- main menu icons
# Each icon is drawn centred on (centre_x, centre_y), fitting inside a circle of the given
# radius, in supersampled pixels. tile_colour is the colour behind it, used for cut-outs.
def draw_explore_icon(draw, centre_x, centre_y, radius, colour, tile_colour):        # compass
    stroke = max(2, int(radius * 0.13))
    draw.ellipse([centre_x - radius, centre_y - radius, centre_x + radius, centre_y + radius],
                 outline=colour, width=stroke)
    needle = radius * 0.62
    draw.polygon([(centre_x, centre_y - needle), (centre_x + needle * 0.32, centre_y),
                  (centre_x, centre_y + needle), (centre_x - needle * 0.32, centre_y)], fill=colour)
    hub = radius * 0.1
    draw.ellipse([centre_x - hub, centre_y - hub, centre_x + hub, centre_y + hub], fill=tile_colour)


def draw_collections_icon(draw, centre_x, centre_y, radius, colour, tile_colour):    # star
    points = []
    for point_index in range(10):
        angle = -math.pi / 2 + point_index * math.pi / 5
        point_radius = radius if point_index % 2 == 0 else radius * 0.45
        points.append((centre_x + point_radius * math.cos(angle),
                       centre_y + point_radius * math.sin(angle) + radius * 0.06))
    draw.polygon(points, fill=colour)


def draw_history_icon(draw, centre_x, centre_y, radius, colour, tile_colour):        # clock with rewind arc
    stroke = max(2, int(radius * 0.13))
    draw.arc([centre_x - radius, centre_y - radius, centre_x + radius, centre_y + radius],
             start=-40, end=250, fill=colour, width=stroke)
    # arrow head where the arc starts (about 250 degrees)
    arrow_angle = math.radians(250)
    arrow_x = centre_x + radius * math.cos(arrow_angle)
    arrow_y = centre_y + radius * math.sin(arrow_angle)
    arrow_size = radius * 0.36
    draw.polygon([(arrow_x - arrow_size, arrow_y - arrow_size * 0.2),
                  (arrow_x + arrow_size * 0.5, arrow_y - arrow_size * 0.9),
                  (arrow_x + arrow_size * 0.4, arrow_y + arrow_size * 0.5)], fill=colour)
    draw.line([(centre_x, centre_y), (centre_x, centre_y - radius * 0.55)], fill=colour, width=stroke)   # minute hand
    draw.line([(centre_x, centre_y), (centre_x + radius * 0.42, centre_y + radius * 0.25)],
              fill=colour, width=stroke)                                                              # hour hand
    draw.ellipse([centre_x - stroke, centre_y - stroke, centre_x + stroke, centre_y + stroke], fill=colour)


def draw_apps_icon(draw, centre_x, centre_y, radius, colour, tile_colour):           # 2x2 tiles
    gap = radius * 0.18
    tile_size = (2 * radius - gap) / 2
    for column in range(2):
        for row in range(2):
            left = centre_x - radius + column * (tile_size + gap)
            top = centre_y - radius + row * (tile_size + gap)
            draw.rounded_rectangle([left, top, left + tile_size, top + tile_size],
                                   radius=tile_size * 0.28, fill=colour)


def draw_info_icon(draw, centre_x, centre_y, radius, colour, tile_colour):           # (i)
    stroke = max(2, int(radius * 0.13))
    draw.ellipse([centre_x - radius, centre_y - radius, centre_x + radius, centre_y + radius],
                 outline=colour, width=stroke)
    draw.ellipse([centre_x - radius * 0.13, centre_y - radius * 0.55,
                  centre_x + radius * 0.13, centre_y - radius * 0.29], fill=colour)        # dot
    draw.rounded_rectangle([centre_x - radius * 0.11, centre_y - radius * 0.15,
                            centre_x + radius * 0.11, centre_y + radius * 0.58],
                           radius=radius * 0.05, fill=colour)                           # stem


def draw_settings_icon(draw, centre_x, centre_y, radius, colour, tile_colour):       # gear
    tooth_count = 8
    points = []
    for point_index in range(tooth_count * 4):
        angle = 2 * math.pi * point_index / (tooth_count * 4)
        point_radius = radius if (point_index % 4) in (1, 2) else radius * 0.76
        points.append((centre_x + point_radius * math.cos(angle), centre_y + point_radius * math.sin(angle)))
    draw.polygon(points, fill=colour)
    hole = radius * 0.33
    draw.ellipse([centre_x - hole, centre_y - hole, centre_x + hole, centre_y + hole], fill=tile_colour)


def draw_restart_icon(draw, centre_x, centre_y, radius, colour, tile_colour):        # circular arrow
    stroke = max(2, int(radius * 0.14))
    arc_radius = radius * 0.9
    draw.arc([centre_x - arc_radius, centre_y - arc_radius, centre_x + arc_radius, centre_y + arc_radius],
             start=-60, end=230, fill=colour, width=stroke)
    arrow_angle = math.radians(-60)
    arrow_x = centre_x + radius * 0.9 * math.cos(arrow_angle)
    arrow_y = centre_y + radius * 0.9 * math.sin(arrow_angle)
    arrow_size = radius * 0.38
    draw.polygon([(arrow_x - arrow_size * 0.9, arrow_y - arrow_size * 0.3),
                  (arrow_x + arrow_size * 0.5, arrow_y - arrow_size * 0.6),
                  (arrow_x + arrow_size * 0.1, arrow_y + arrow_size * 0.8)], fill=colour)


def draw_shutdown_icon(draw, centre_x, centre_y, radius, colour, tile_colour):       # power symbol
    stroke = max(2, int(radius * 0.14))
    draw.arc([centre_x - radius * 0.9, centre_y - radius * 0.82, centre_x + radius * 0.9, centre_y + radius * 0.98],
             start=-55, end=235, fill=colour, width=stroke)
    draw.rounded_rectangle([centre_x - stroke / 2, centre_y - radius, centre_x + stroke / 2, centre_y + radius * 0.05],
                           radius=stroke / 2, fill=colour)


# Main menu items: file name MustardOS expects, label, icon, and row (0 = large top row).
MENU_ITEMS = [
    ("explore",    "Explore",     draw_explore_icon,     0),
    ("collection", "Collections", draw_collections_icon, 0),
    ("history",    "History",     draw_history_icon,     0),
    ("apps",       "Apps",        draw_apps_icon,        1),
    ("info",       "Info",        draw_info_icon,        1),
    ("config",     "Settings",    draw_settings_icon,    1),
    ("reboot",     "Restart",     draw_restart_icon,     1),
    ("shutdown",   "Shutdown",    draw_shutdown_icon,    1),
]

# ---------------------------------------------------------------- main menu layout
SCREEN_MARGIN = 16
TILE_GAP = 12
TOP_ROW_TOP, TOP_ROW_BOTTOM = HEADER_HEIGHT + 8, 318
BOTTOM_ROW_TOP, BOTTOM_ROW_BOTTOM = TOP_ROW_BOTTOM + TILE_GAP, SCREEN_HEIGHT - FOOTER_HEIGHT - 8


def row_tile_rects(tile_count, top, bottom):
    """Split the screen width into equal tiles, spreading any leftover pixels from the left."""
    available_width = SCREEN_WIDTH - 2 * SCREEN_MARGIN - TILE_GAP * (tile_count - 1)
    widths = [available_width // tile_count] * tile_count
    for tile_index in range(available_width - sum(widths)):
        widths[tile_index] += 1
    rects, left = [], SCREEN_MARGIN
    for width in widths:
        rects.append((left, top, left + width, bottom))
        left += width + TILE_GAP
    return rects


MENU_TILE_RECTS = (row_tile_rects(3, TOP_ROW_TOP, TOP_ROW_BOTTOM)
                   + row_tile_rects(5, BOTTOM_ROW_TOP, BOTTOM_ROW_BOTTOM))


def render_main_menu(focused_item, accent=None):
    """The whole main menu as one image, with focused_item highlighted in the accent colour."""
    accent = accent or ACCENT
    image = Image.new("RGBA", (SCREEN_WIDTH * SUPERSAMPLE, SCREEN_HEIGHT * SUPERSAMPLE), rgba(BACKGROUND))
    draw = ImageDraw.Draw(image)
    large_font = ImageFont.truetype(BOLD_FONT_PATH, 22 * SUPERSAMPLE)
    small_font = ImageFont.truetype(MEDIUM_FONT_PATH, 13 * SUPERSAMPLE)
    for (item_name, label, draw_icon, row), (left, top, right, bottom) in zip(MENU_ITEMS, MENU_TILE_RECTS):
        left, top = left * SUPERSAMPLE, top * SUPERSAMPLE
        right, bottom = right * SUPERSAMPLE, bottom * SUPERSAMPLE
        is_focused = item_name == focused_item
        tile_colour = rgba(accent) if is_focused else rgba(BUTTON)
        content_colour = rgba(BACKGROUND) if is_focused else rgba(TEXT)
        corner_radius = 14 * SUPERSAMPLE
        drop = 3 * SUPERSAMPLE
        draw.rounded_rectangle([left, top + drop, right, bottom + drop], radius=corner_radius, fill=rgba(SHADOW))
        draw.rounded_rectangle([left, top, right, bottom], radius=corner_radius, fill=tile_colour)
        centre_x = (left + right) / 2
        if row == 0:
            icon_radius = 46 * SUPERSAMPLE
            icon_centre_y = top + (bottom - top) * 0.42
            draw_icon(draw, centre_x, icon_centre_y, icon_radius, content_colour, tile_colour)
            label_width = draw.textlength(label, font=large_font)
            draw.text((centre_x - label_width / 2, bottom - 62 * SUPERSAMPLE), label,
                      font=large_font, fill=content_colour)
        else:
            icon_radius = 19 * SUPERSAMPLE
            icon_centre_y = top + (bottom - top) * 0.40
            draw_icon(draw, centre_x, icon_centre_y, icon_radius, content_colour, tile_colour)
            label_width = draw.textlength(label, font=small_font)
            draw.text((centre_x - label_width / 2, bottom - 30 * SUPERSAMPLE), label,
                      font=small_font, fill=content_colour)
    return image.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)


# ---------------------------------------------------------------- scheme files
def to_ini(scheme):
    lines = []
    for section, settings in scheme.items():
        lines.append(f"[{section}]")
        lines += [f"{key}={value}" for key, value in settings.items()]
        lines.append("")
    return "\n".join(lines)


NAV_BUTTONS = ("LR", "UD", "A", "B", "C", "X", "Y", "Z", "MENU")
NAV_BUTTON_SETTINGS = (("GLYPH", ACCENT), ("GLYPH_ALPHA", 255), ("GLYPH_RECOLOUR_ALPHA", 255),
                       ("TEXT", TEXT), ("TEXT_ALPHA", 255))

GLOBAL_SCHEME = {
    "background": {"BACKGROUND": BACKGROUND, "BACKGROUND_ALPHA": 255,
                   "BACKGROUND_GRADIENT_COLOR": BACKGROUND, "BACKGROUND_GRADIENT_DIRECTION": 0},
    "font": {"FONT_LIST_SIZE": 20, "FONT_HEADER_SIZE": 18, "FONT_FOOTER_SIZE": 16,
             "FONT_PANEL_SIZE": 16, "FONT_LIST_PAD_LEFT": 14, "FONT_LIST_PAD_RIGHT": 10,
             "FONT_LIST_PAD_TOP": 0, "FONT_LIST_PAD_BOTTOM": 0,
             "FONT_HEADER_PAD_TOP": 6, "FONT_HEADER_ICON_PAD_TOP": 0},
    "glyph": {"HEADER": 26},
    "status": {"ALIGN": 1, "PADDING_LEFT": 0, "PADDING_RIGHT": 10},
    "battery": {"BATTERY_NORMAL": TEXT, "BATTERY_ACTIVE": ACCENT, "BATTERY_LOW": "D35C54",
                "BATTERY_NORMAL_ALPHA": 255, "BATTERY_ACTIVE_ALPHA": 255, "BATTERY_LOW_ALPHA": 255},
    "network": {"NETWORK_NORMAL": MUTED_TEXT, "NETWORK_ACTIVE": ACCENT,
                "NETWORK_NORMAL_ALPHA": 255, "NETWORK_ACTIVE_ALPHA": 255},
    "bluetooth": {"BLUETOOTH_NORMAL": MUTED_TEXT, "BLUETOOTH_ACTIVE": ACCENT,
                  "BLUETOOTH_NORMAL_ALPHA": 255, "BLUETOOTH_ACTIVE_ALPHA": 255},
    "date": {"DATETIME_TEXT": TEXT, "DATETIME_ALPHA": 255, "DATETIME_ALIGN": 1,
             "PADDING_LEFT": 14, "PADDING_RIGHT": 0},
    "header": {"HEADER_HEIGHT": HEADER_HEIGHT, "HEADER_BACKGROUND": BACKGROUND, "HEADER_BACKGROUND_ALPHA": 255,
               "HEADER_TEXT": TEXT, "HEADER_TEXT_ALPHA": 255, "HEADER_TEXT_ALIGN": 2,
               "PADDING_LEFT": 0, "PADDING_RIGHT": 0},
    "footer": {"FOOTER_HEIGHT": FOOTER_HEIGHT, "FOOTER_BACKGROUND": BACKGROUND, "FOOTER_BACKGROUND_ALPHA": 255,
               "FOOTER_TEXT": TEXT, "FOOTER_TEXT_ALPHA": 255},
    "navigation": dict({"ALIGNMENT": 0, "SPACING": 8},
                       **{f"NAV_{button}_{setting}": value
                          for button in NAV_BUTTONS for setting, value in NAV_BUTTON_SETTINGS}),
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
        "LIST_DEFAULT_SHADOW_COLOUR": BACKGROUND, "LIST_DEFAULT_SHADOW_ALPHA": 1,
        "LIST_DEFAULT_SHADOW_X_OFFSET": 0, "LIST_DEFAULT_SHADOW_Y_OFFSET": 0,
        "LIST_DISABLED_TEXT": MUTED_TEXT, "LIST_DISABLED_TEXT_ALPHA": 255,
        "LIST_FOCUS_BACKGROUND": BUTTON, "LIST_FOCUS_BACKGROUND_ALPHA": 255,
        "LIST_FOCUS_GRADIENT_START": 0, "LIST_FOCUS_GRADIENT_STOP": 0, "LIST_FOCUS_GRADIENT_DIRECTION": 0,
        "LIST_FOCUS_BORDER_WIDTH": 4, "LIST_FOCUS_BORDER_SIDE": 4,
        "LIST_FOCUS_INDICATOR": ACCENT, "LIST_FOCUS_INDICATOR_ALPHA": 255,
        "LIST_FOCUS_TEXT": ACCENT, "LIST_FOCUS_TEXT_ALPHA": 255,
        "LIST_FOCUS_GLYPH_ALPHA": 255, "LIST_FOCUS_GLYPH_RECOLOUR": ACCENT,
        "LIST_FOCUS_GLYPH_RECOLOUR_ALPHA": 255,
        "LIST_FOCUS_SHADOW_COLOUR": SHADOW, "LIST_FOCUS_SHADOW_ALPHA": 160,
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
                 "DIALOGUE_CONTENT": TEXT, "DIALOGUE_OPTION": BACKGROUND, "DIALOGUE_DIM_ALPHA": 150,
                 "DIALOGUE_SELECTION": ACCENT, "DIALOGUE_SELECTION_ALPHA": 255,
                 "DIALOGUE_RADIUS_MAIN": 12, "DIALOGUE_RADIUS_SELECTED": 8,
                 "DIALOGUE_SHADOW_COLOUR": "000000", "DIALOGUE_SHADOW_ALPHA": 160,
                 "DIALOGUE_SHADOW_X_OFFSET": 0, "DIALOGUE_SHADOW_Y_OFFSET": 4,
                 "DIALOGUE_SHADOW_COLOUR_FOCUS": SHADOW, "DIALOGUE_SHADOW_ALPHA_FOCUS": 96,
                 "DIALOGUE_SHADOW_X_OFFSET_FOCUS": 0, "DIALOGUE_SHADOW_Y_OFFSET_FOCUS": 2},
    "grid": {"BACKGROUND": BACKGROUND, "BACKGROUND_ALPHA": 0},
    "charging": {"CHARGER_BACKGROUND": BACKGROUND, "CHARGER_BACKGROUND_ALPHA": 255,
                 "CHARGER_TEXT": ACCENT, "CHARGER_TEXT_ALPHA": 255, "CHARGER_Y_POS": 100},
    "verbose": {"VERBOSE_BOOT_BACKGROUND": BACKGROUND, "VERBOSE_BOOT_BACKGROUND_ALPHA": 255,
                "VERBOSE_BOOT_TEXT": TEXT, "VERBOSE_BOOT_TEXT_ALPHA": 255, "VERBOSE_BOOT_Y_POS": 165},
    "keyboard": {"OSK_BACKGROUND": BACKGROUND, "OSK_BACKGROUND_ALPHA": 255, "OSK_BORDER": ACCENT,
                 "OSK_BORDER_ALPHA": 255, "OSK_RADIUS": 12, "OSK_TEXT": TEXT, "OSK_TEXT_ALPHA": 255,
                 "OSK_TEXT_FOCUS": BACKGROUND, "OSK_TEXT_FOCUS_ALPHA": 255,
                 "OSK_ITEM_BACKGROUND": BUTTON, "OSK_ITEM_BACKGROUND_ALPHA": 255,
                 "OSK_ITEM_BACKGROUND_FOCUS": ACCENT, "OSK_ITEM_BACKGROUND_FOCUS_ALPHA": 255,
                 "OSK_ITEM_BORDER": BUTTON, "OSK_ITEM_BORDER_ALPHA": 0,
                 "OSK_ITEM_BORDER_FOCUS": ACCENT, "OSK_ITEM_BORDER_FOCUS_ALPHA": 255,
                 "OSK_ITEM_RADIUS": 6, "OSK_ITEM_SHADOW_COLOUR": SHADOW,
                 "OSK_ITEM_SHADOW_COLOUR_FOCUS": SHADOW},
    "notification": {"MSG_BACKGROUND": BUTTON, "MSG_BACKGROUND_ALPHA": 255, "MSG_BORDER": ACCENT,
                     "MSG_BORDER_ALPHA": 255, "MSG_RADIUS": 10, "MSG_TEXT": TEXT, "MSG_TEXT_ALPHA": 255,
                     # status colours stay fixed across accents
                     "MSG_LEVEL_SUCCESS": "7FCF8E", "MSG_LEVEL_WARNING": "F2C14E", "MSG_LEVEL_ERROR": "D35C54"},
    "bar": {"BAR_WIDTH": 600, "BAR_HEIGHT": 42, "BAR_BACKGROUND": BUTTON, "BAR_BACKGROUND_ALPHA": 255,
            "BAR_BORDER": BUTTON, "BAR_BORDER_ALPHA": 255, "BAR_RADIUS": 12,
            "BAR_PROGRESS_WIDTH": 520, "BAR_PROGRESS_HEIGHT": 14,
            "BAR_PROGRESS_BACKGROUND": BACKGROUND, "BAR_PROGRESS_BACKGROUND_ALPHA": 255,
            "BAR_PROGRESS_ACTIVE_BACKGROUND": ACCENT, "BAR_PROGRESS_ACTIVE_BACKGROUND_ALPHA": 255,
            "BAR_PROGRESS_RADIUS": 7, "BAR_ICON": ACCENT, "BAR_ICON_ALPHA": 255, "BAR_Y_POS": 392},
    "roll": {"ROLL_TEXT": TEXT, "ROLL_TEXT_ALPHA": 255, "ROLL_BACKGROUND": BUTTON,
             "ROLL_BACKGROUND_ALPHA": 255, "ROLL_RADIUS": 10, "ROLL_SELECT_TEXT": BACKGROUND,
             "ROLL_SELECT_TEXT_ALPHA": 255, "ROLL_SELECT_BACKGROUND": ACCENT,
             "ROLL_SELECT_BACKGROUND_ALPHA": 255, "ROLL_SELECT_RADIUS": 10,
             "ROLL_BORDER_COLOUR": ACCENT, "ROLL_BORDER_ALPHA": 255, "ROLL_BORDER_RADIUS": 12},
    "counter": {"COUNTER_ALIGNMENT": 2, "COUNTER_PADDING_AROUND": 6, "COUNTER_PADDING_SIDE": 10,
                "COUNTER_PADDING_TOP": 42, "COUNTER_BORDER_COLOUR": ACCENT, "COUNTER_BORDER_ALPHA": 0,
                "COUNTER_BORDER_WIDTH": 0, "COUNTER_RADIUS": 4, "COUNTER_BACKGROUND": BUTTON,
                "COUNTER_BACKGROUND_ALPHA": 230, "COUNTER_TEXT": ACCENT, "COUNTER_TEXT_ALPHA": 255,
                "COUNTER_TEXT_FADE_TIME": 50, "COUNTER_TEXT_SEPARATOR": " / "},
    "terminal": {"FONT_SIZE": 16, "FOREGROUND": TEXT, "BACKGROUND": BACKGROUND},
    "misc": {"ANTIALIASING": 1, "STATIC_ALIGNMENT": 0, "IMAGE_OVERLAY": 0},
}

CONTENT_HEIGHT = SCREEN_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT - 8   # 400
DEFAULT_SCHEME = {
    "misc": {"CONTENT_PADDING_LEFT": 8, "CONTENT_PADDING_TOP": 2, "CONTENT_WIDTH": 624,
             "CONTENT_HEIGHT": CONTENT_HEIGHT, "CONTENT_ITEM_COUNT": 10, "CONTENT_ALIGNMENT": 0,
             "NAVIGATION_TYPE": 2},
}

# The main menu is drawn entirely by the static images, so the list it sits on is hidden.
HIDDEN_MAIN_MENU_LIST_SETTINGS = (
    "LIST_DEFAULT_BACKGROUND_ALPHA", "LIST_DEFAULT_INDICATOR_ALPHA",
    "LIST_DEFAULT_TEXT_ALPHA", "LIST_DEFAULT_GLYPH_ALPHA",
    "LIST_DEFAULT_GLYPH_RECOLOUR_ALPHA", "LIST_FOCUS_BACKGROUND_ALPHA",
    "LIST_FOCUS_INDICATOR_ALPHA", "LIST_FOCUS_TEXT_ALPHA",
    "LIST_FOCUS_GLYPH_ALPHA", "LIST_FOCUS_GLYPH_RECOLOUR_ALPHA",
    "LIST_DEFAULT_BORDER_WIDTH", "LIST_FOCUS_BORDER_WIDTH",
    "LIST_FOCUS_SHADOW_X_OFFSET", "LIST_FOCUS_SHADOW_Y_OFFSET",
)
MAIN_MENU_SCHEME = {
    "header": {"HEADER_BACKGROUND_ALPHA": 0, "HEADER_TEXT_ALPHA": 0},
    "footer": {"FOOTER_BACKGROUND_ALPHA": 0},
    "list": {setting: 0 for setting in HIDDEN_MAIN_MENU_LIST_SETTINGS},
    "misc": {"NAVIGATION_TYPE": 5, "STATIC_ALIGNMENT": 3, "CONTENT_ITEM_COUNT": 8},
}
MAIN_MENU_SCHEME["list"].update({"LIST_DEFAULT_SHADOW_ALPHA": 1, "LIST_FOCUS_SHADOW_ALPHA": 1})

# Game lists: slim list on the left, the rest of the screen left free for box art.
GAME_LIST_WIDTH = 248


def game_list_scheme():
    return {
        "font": {"FONT_LIST_SIZE": 18, "FONT_LIST_PAD_LEFT": 12},
        "misc": {"CONTENT_PADDING_LEFT": 6, "CONTENT_WIDTH": GAME_LIST_WIDTH, "CONTENT_ITEM_COUNT": 12,
                 "CONTENT_HEIGHT": CONTENT_HEIGHT, "CONTENT_PADDING_TOP": 2},
        "list": {"LIST_DEFAULT_GLYPH_PAD_LEFT": 18},
    }


def grid_settings(column_count, row_count, label_offset_y, art_only=False, square=False):
    column_width = (SCREEN_WIDTH - 16) // column_count
    row_height = (SCREEN_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT - 8) // row_count
    grid_left = 8
    if square:                       # cells sized by row height, grid centred horizontally
        column_width = row_height
        grid_left = (SCREEN_WIDTH - column_count * column_width) // 2
    cell_gap = 8 if square else 10   # square: 192px cells, 184px inside the 4px border
    settings = {
        "NAVIGATION_TYPE": 2, "ALIGNMENT": 0, "ALIGNMENT_X_OFFSET": 0, "ALIGNMENT_Y_OFFSET": 0,
        "BACKGROUND": BACKGROUND, "BACKGROUND_ALPHA": 0,
        "LOCATION_X": grid_left, "LOCATION_Y": HEADER_HEIGHT + 4,
        "COLUMN_COUNT": column_count, "ROW_COUNT": row_count,
        "COLUMN_WIDTH": column_width, "ROW_HEIGHT": row_height,
        "COLUMN_PADDING": 0, "ROW_PADDING": 0, "CELL_COLUMN_ALIGN": 1, "CELL_ROW_ALIGN": 1,
        "CELL_WIDTH": column_width - cell_gap, "CELL_HEIGHT": row_height - cell_gap, "CELL_RADIUS": 4,
        "CELL_BORDER_WIDTH": 4, "CELL_IMAGE_PADDING_TOP": 8, "CELL_TEXT_PADDING_BOTTOM": 8,
        "CELL_TEXT_PADDING_SIDE": 8, "CELL_TEXT_LINE_SPACING": -2,
        "CELL_SHADOW": SHADOW, "CELL_SHADOW_WIDTH": 6, "CELL_SHADOW_X_OFFSET": 10, "CELL_SHADOW_Y_OFFSET": 10,
        "CELL_DEFAULT_BACKGROUND": BUTTON, "CELL_DEFAULT_BACKGROUND_ALPHA": 255,
        "CELL_DEFAULT_BACKGROUND_GRADIENT_COLOR": BUTTON, "CELL_DEFAULT_BACKGROUND_GRADIENT_DIRECTION": 0,
        "CELL_DEFAULT_BORDER": BUTTON, "CELL_DEFAULT_BORDER_ALPHA": 255,
        "CELL_DEFAULT_IMAGE_ALPHA": 255, "CELL_DEFAULT_IMAGE_RECOLOUR": TEXT,
        "CELL_DEFAULT_IMAGE_RECOLOUR_ALPHA": 0,
        "CELL_DEFAULT_TEXT": TEXT, "CELL_DEFAULT_TEXT_ALPHA": 255,
        "CELL_FOCUS_BACKGROUND": ACCENT, "CELL_FOCUS_BACKGROUND_ALPHA": 255,
        "CELL_FOCUS_BACKGROUND_GRADIENT_COLOR": ACCENT, "CELL_FOCUS_BACKGROUND_GRADIENT_DIRECTION": 0,
        "CELL_FOCUS_BORDER": ACCENT, "CELL_FOCUS_BORDER_ALPHA": 255,
        "CELL_FOCUS_IMAGE_ALPHA": 255, "CELL_FOCUS_IMAGE_RECOLOUR": ACCENT,
        "CELL_FOCUS_IMAGE_RECOLOUR_ALPHA": 0,
        "CELL_FOCUS_TEXT": ACCENT, "CELL_FOCUS_TEXT_ALPHA": 255,
        "CELL_FOCUS_GLOW": ACCENT, "CELL_FOCUS_GLOW_WIDTH": 0,
        "CURRENT_ITEM_LABEL_BACKGROUND_GRADIENT_COLOR": ACCENT, "CURRENT_ITEM_LABEL_SHADOW": SHADOW,
        # floating name of the focused item, hidden by default (cells carry their own label)
        "CURRENT_ITEM_LABEL_ALIGNMENT": 5, "CURRENT_ITEM_LABEL_WIDTH": 0, "CURRENT_ITEM_LABEL_HEIGHT": 0,
        "CURRENT_ITEM_LABEL_OFFSET_X": 0, "CURRENT_ITEM_LABEL_OFFSET_Y": label_offset_y,
        "CURRENT_ITEM_LABEL_RADIUS": 10, "CURRENT_ITEM_LABEL_BORDER_WIDTH": 0,
        "CURRENT_ITEM_LABEL_BORDER": ACCENT, "CURRENT_ITEM_LABEL_BORDER_ALPHA": 0,
        "CURRENT_ITEM_LABEL_BACKGROUND": ACCENT, "CURRENT_ITEM_LABEL_BACKGROUND_ALPHA": 0,
        "CURRENT_ITEM_LABEL_TEXT": BACKGROUND, "CURRENT_ITEM_LABEL_TEXT_ALPHA": 0,
        "CURRENT_ITEM_LABEL_TEXT_ALIGNMENT": 2,
    }
    if art_only:
        settings.update({
            # cards show only artwork, centred in the cell
            "CELL_DEFAULT_TEXT_ALPHA": 0, "CELL_FOCUS_TEXT_ALPHA": 0, "CELL_IMAGE_PADDING_TOP": 0,
            "CELL_TEXT_PADDING_BOTTOM": 0, "CELL_TEXT_PADDING_SIDE": 0,
            "CELL_DEFAULT_IMAGE_ALPHA": 255,
            # focused title scrolls in the header, between the clock and status icons
            "CURRENT_ITEM_LABEL_ALIGNMENT": 2, "CURRENT_ITEM_LABEL_WIDTH": 340,
            "CURRENT_ITEM_LABEL_HEIGHT": HEADER_HEIGHT - 4, "CURRENT_ITEM_LABEL_OFFSET_X": 0,
            "CURRENT_ITEM_LABEL_OFFSET_Y": 2, "CURRENT_ITEM_LABEL_LABEL_LONG_MODE": 1,
            "CURRENT_ITEM_LABEL_TEXT": ACCENT, "CURRENT_ITEM_LABEL_TEXT_ALPHA": 255,
            "CURRENT_ITEM_LABEL_TEXT_PADDING_TOP": 3, "CURRENT_ITEM_LABEL_TEXT_PADDING_BOTTOM": 0,
            "CURRENT_ITEM_LABEL_TEXT_PADDING_LEFT": 4, "CURRENT_ITEM_LABEL_TEXT_PADDING_RIGHT": 4,
        })
    return settings


# Box-art screens: transparent header so the floating title shows, counter in the footer corner.
BOX_ART_SCREEN = {
    "header": {"HEADER_TEXT_ALPHA": 0, "HEADER_BACKGROUND_ALPHA": 0},
    "counter": {"COUNTER_ALIGNMENT": 2, "COUNTER_PADDING_SIDE": 6,
                "COUNTER_PADDING_TOP": SCREEN_HEIGHT - FOOTER_HEIGHT + 4, "COUNTER_PADDING_AROUND": 4},
}


def box_art_scheme():
    scheme = game_list_scheme()
    scheme["grid"] = grid_settings(3, 2, -44, art_only=True, square=True)
    scheme.update(BOX_ART_SCREEN)
    return scheme


EXPLORE_SCHEME = box_art_scheme()
COLLECTIONS_SCHEME = box_art_scheme()
HISTORY_SCHEME = box_art_scheme()

APP_ICON_SIZE = 64
APPS_SCHEME = {"grid": grid_settings(4, 3, -44)}                    # 4x3, icon + name
APPS_SCHEME["grid"].update({
    "CELL_IMAGE_PADDING_TOP": 14, "CELL_TEXT_PADDING_BOTTOM": 10, "CELL_TEXT_PADDING_SIDE": 6,
    # icons are white line art; tint them text-grey normally and accent-coloured when focused
    "CELL_DEFAULT_IMAGE_RECOLOUR": TEXT, "CELL_DEFAULT_IMAGE_RECOLOUR_ALPHA": 255,
    "CELL_FOCUS_IMAGE_RECOLOUR": ACCENT, "CELL_FOCUS_IMAGE_RECOLOUR_ALPHA": 255,
})

# ---------------------------------------------------------------- user overrides
# Settings tuned on-device (override-Selection.zip). Applied last, so they win.
LARGER_GLYPHS = {"glyph": {"FOOTER": 30, "HEADER": 30}}
GRID_SELECTION_STYLE = {
    "grid": {
        # focused title: left-aligned in the header, after the clock
        "CURRENT_ITEM_LABEL_ALIGNMENT": 1, "CURRENT_ITEM_LABEL_BACKGROUND": "000000",
        "CURRENT_ITEM_LABEL_BACKGROUND_ALPHA": 0, "CURRENT_ITEM_LABEL_LABEL_LONG_MODE": 1,
        "CURRENT_ITEM_LABEL_WIDTH": 400, "CURRENT_ITEM_LABEL_HEIGHT": 40,
        "CURRENT_ITEM_LABEL_OFFSET_X": 80, "CURRENT_ITEM_LABEL_OFFSET_Y": 3,
        "CURRENT_ITEM_LABEL_TEXT_ALIGNMENT": 2, "CURRENT_ITEM_LABEL_TEXT": "EEEEEE",
        "CURRENT_ITEM_LABEL_TEXT_ALPHA": 255,
        # focused card: art faded over an accent-coloured card with a gold border
        "CELL_FOCUS_BACKGROUND": ACCENT, "CELL_FOCUS_BACKGROUND_ALPHA": 255,
        "CELL_FOCUS_IMAGE_RECOLOUR_ALPHA": 0, "CELL_FOCUS_IMAGE_ALPHA": 100,
        "CELL_FOCUS_IMAGE_RECOLOUR": "000000", "CELL_FOCUS_BORDER": "FFC53B",
        "CELL_FOCUS_BORDER_ALPHA": 255, "CELL_RADIUS": 4, "CELL_DEFAULT_TEXT_ALPHA": 0,
    },
    "header": {"HEADER_TEXT_ALPHA": 0, "HEADER_BACKGROUND_ALPHA": 0},
    **LARGER_GLYPHS,
}
USER_OVERRIDES = [
    (MAIN_MENU_SCHEME, LARGER_GLYPHS), (APPS_SCHEME, LARGER_GLYPHS),
    (EXPLORE_SCHEME, GRID_SELECTION_STYLE), (HISTORY_SCHEME, GRID_SELECTION_STYLE),
]


def merge_scheme(target, overrides):
    for section, settings in overrides.items():
        target.setdefault(section, {}).update(settings)


for target_scheme, overrides in USER_OVERRIDES:
    merge_scheme(target_scheme, overrides)

# ---------------------------------------------------------------- accent alternatives
# Each one appears under Customisation > Alternative Theme.
ACCENTS = {
    "Amber":     "F7B954",
    "Tangerine": "F28F55",
    "Red": "FF5555",
    "Bubblegum": "F08CA8",
    "Lavender":  "B8A2F0",
    "Sky":       "79BEF0",
    "Cyan":      "5BD6D6",
    "Mint":      "7CDC94",
    "Gameboy Green":      "A0C765",
}
BRIGHT_BORDER = "FFC53B"   # brighter gold used on the game-grid focus border


def brighten(hex_colour):
    """Same shift as Amber -> FFC53B: a touch more saturation, full brightness."""
    red, green, blue = (int(hex_colour[offset:offset + 2], 16) / 255 for offset in (0, 2, 4))
    hue, saturation, _brightness = colorsys.rgb_to_hsv(red, green, blue)
    red, green, blue = colorsys.hsv_to_rgb(hue, min(1.0, saturation * 1.17), 1.0)
    return "".join(f"{round(channel * 255):02X}" for channel in (red, green, blue))


def recolour(scheme, accent):
    """Copy of a scheme with the base accent (and the bright border) swapped for another accent."""
    recoloured = copy.deepcopy(scheme)
    if accent.upper() == ACCENT.upper():
        return recoloured          # base palette, including the hand-picked FFC53B border
    for settings in recoloured.values():
        for key, value in settings.items():
            if isinstance(value, str) and value.upper() == ACCENT.upper():
                settings[key] = accent
            elif isinstance(value, str) and value.upper() == BRIGHT_BORDER:
                settings[key] = brighten(accent)
    return recoloured


# Where each scheme lives inside the theme.
SCHEME_FILES = {
    "scheme/global.ini": GLOBAL_SCHEME,
    "640x480/scheme/default.ini": DEFAULT_SCHEME,
    "640x480/scheme/muxlaunch.ini": MAIN_MENU_SCHEME,
    "640x480/scheme/muxplore.ini": EXPLORE_SCHEME,
    "640x480/scheme/muxcollect.ini": COLLECTIONS_SCHEME,
    "640x480/scheme/muxhistory.ini": HISTORY_SCHEME,
    "640x480/scheme/muxapp.ini": APPS_SCHEME,
}


def build_accent_alternatives():
    """alternate/<Name>.muxalt holds every accent-dependent file. Choosing an alternative
    extracts it over the theme (MustardOS 2606.0 behaviour), replacing the schemes and the
    main-menu tiles; Amber's archive puts the original files back.

    Newer MustardOS builds cache parsed scheme files and only re-read one when its
    modification time changes. Extraction gives each file the timestamp stored in the
    archive, so every accent gets its own fixed timestamp; otherwise files built in the
    same few seconds look unchanged and the old colours stay in use."""
    alternate_dir = os.path.join(THEME_DIR, "alternate")
    os.makedirs(alternate_dir)
    for accent_index, (accent_name, accent) in enumerate(ACCENTS.items()):
        timestamp = (2020, 1, 1, 0, accent_index + 1, 0)    # distinct per accent, never the build time

        def add_file(archive, archive_path, data):
            entry = zipfile.ZipInfo(archive_path, date_time=timestamp)
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)

        archive_path = os.path.join(alternate_dir, f"{accent_name}.muxalt")
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for scheme_path, scheme in SCHEME_FILES.items():
                add_file(archive, scheme_path, to_ini(recolour(scheme, accent)))
            for item_name, *_ in MENU_ITEMS:
                image_bytes = io.BytesIO()
                render_main_menu(item_name, accent).convert("RGB").save(image_bytes, "PNG", optimize=True)
                add_file(archive, f"640x480/image/static/muxlaunch/{item_name}.png", image_bytes.getvalue())


# ---------------------------------------------------------------- build
def copy_user_artwork(app_icon_dir):
    """Console cards, collection art and extra app icons from assets/catalogue."""
    user_catalogue = os.path.join(REPO_DIR, "assets", "catalogue")
    for folder in ("Folder", "Collection"):
        source = os.path.join(user_catalogue, folder)
        if os.path.isdir(source):
            shutil.copytree(source, os.path.join(THEME_DIR, "catalogue", folder))
    extra_icons = os.path.join(user_catalogue, "Application", "grid", "extra")
    if os.path.isdir(extra_icons):
        for file_name in os.listdir(extra_icons):
            if os.path.splitext(file_name)[0] in app_icons.ICONS:
                continue          # this theme draws its own icon for that app
            icon = Image.open(os.path.join(extra_icons, file_name)).convert("RGBA")
            icon.thumbnail((APP_ICON_SIZE, APP_ICON_SIZE), Image.LANCZOS)   # match the drawn icons
            icon.save(os.path.join(app_icon_dir, file_name), optimize=True)


def build():
    if os.path.exists(THEME_DIR):
        shutil.rmtree(THEME_DIR)
    resolution_dir = os.path.join(THEME_DIR, "640x480")
    main_menu_image_dir = os.path.join(resolution_dir, "image", "static", "muxlaunch")
    wallpaper_dir = os.path.join(resolution_dir, "image", "wall")
    app_icon_dir = os.path.join(THEME_DIR, "catalogue", "Application", "grid")
    for directory in (os.path.join(THEME_DIR, "scheme"), os.path.join(resolution_dir, "scheme"),
                      main_menu_image_dir, wallpaper_dir, os.path.join(THEME_DIR, "font"), app_icon_dir):
        os.makedirs(directory)

    copy_user_artwork(app_icon_dir)
    for icon_name in app_icons.ICONS:
        app_icons.render(icon_name, APP_ICON_SIZE).save(os.path.join(app_icon_dir, f"{icon_name}.png"), optimize=True)

    for item_name, *_ in MENU_ITEMS:
        render_main_menu(item_name).convert("RGB").save(
            os.path.join(main_menu_image_dir, f"{item_name}.png"), optimize=True)

    Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), rgba(BACKGROUND)[:3]).save(
        os.path.join(wallpaper_dir, "default.png"))

    preview = Image.open(os.path.join(main_menu_image_dir, "explore.png"))
    preview.resize((288, 216), Image.LANCZOS).save(os.path.join(resolution_dir, "preview.png"))

    for scheme_path, scheme in SCHEME_FILES.items():
        with open(os.path.join(THEME_DIR, scheme_path), "w") as scheme_file:
            scheme_file.write(to_ini(scheme))

    shutil.copy(MEDIUM_FONT_PATH, os.path.join(THEME_DIR, "font", "default.ttf"))
    shutil.copy(os.path.join(FONT_DIR, "OFL.txt"), os.path.join(THEME_DIR, "font-license.txt"))
    build_accent_alternatives()
    with open(os.path.join(THEME_DIR, "name.txt"), "w") as name_file:
        name_file.write("Ember\n")
    with open(os.path.join(THEME_DIR, "version.txt"), "w") as version_file:
        version_file.write("2606.0\n")
    with open(os.path.join(THEME_DIR, "credits.txt"), "w") as credits_file:
        credits_file.write("Ember theme for MustardOS (640x480 - RG40XXV / RG40XXH)\n"
                           "Main menu layout inspired by OneTwo by bulkh.\n"
                           "Font: Poppins by Indian Type Foundry, SIL Open Font License 1.1.\n")

    os.makedirs(DIST_DIR, exist_ok=True)
    package_path = os.path.join(DIST_DIR, "Ember.muxthm")
    with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as package:
        for directory, _subdirectories, file_names in os.walk(THEME_DIR):
            for file_name in file_names:
                full_path = os.path.join(directory, file_name)
                package.write(full_path, os.path.relpath(full_path, THEME_DIR))
    print("built", package_path)


if __name__ == "__main__":
    build()
