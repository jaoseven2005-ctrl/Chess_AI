import os
import time
import math
import pygame
import copy
import threading
from dataclasses import dataclass
from engine.board import Board
from engine.moves import get_valid_moves
from engine.ai import find_best_move, evaluate_board
from engine.tutor import draw_evaluation_bar

WIDTH = 1120
HEIGHT = 860

LEFT_MARGIN = 40
RIGHT_MARGIN = LEFT_MARGIN
PANEL_W = 180
GAP = 40

TOP_MARGIN = 40
MARGIN = TOP_MARGIN
TOP_BAR_HEIGHT = 70
BOTTOM_BAR_HEIGHT = 65

BOARD_SIZE = 600
ROWS, COLS = 8, 8
SQ_SIZE = BOARD_SIZE // 8
PIECE_SCALE = 0.94

BOARD_X = LEFT_MARGIN + PANEL_W + GAP
BOARD_Y = MARGIN + TOP_BAR_HEIGHT + GAP

LIGHT = (234, 240, 225)
DARK = (192, 203, 178)
SELECT_COLOR = (150, 168, 136)
MOVE_HINT = (142, 173, 143)
BG_TOP = (248, 249, 244)
BG_BOTTOM = (230, 237, 224)
TEXT = (35, 45, 39)
PANEL = (244, 246, 239)

LIGHT_HOVER = (238, 244, 229)
DARK_HOVER = (204, 216, 189)

SHADOW_COLOR = (0, 0, 0, 40)
ACCENT = (106, 136, 100)
LAST_MOVE_COLOR = (140, 165, 123, 110)
CAPTURE_HIGHLIGHT = (205, 110, 98)
MOVE_DOT_COLOR = (255, 255, 255)
HISTORY_TEXT = (72, 82, 74)

POPUP_BG = (250, 247, 242)
POPUP_BORDER = (140, 110, 85)

WHITE_BTN = (236, 228, 213)
WHITE_BTN_HOVER = (246, 238, 223)

DARK_BTN = (92, 64, 51)
DARK_BTN_HOVER = (112, 79, 63)

WHITE_TEXT = (40, 40, 40)
DARK_TEXT = (245, 245, 245)

OVERLAY = (0, 0, 0, 90)

SETTINGS_BUTTON_SIZE = 48
SETTINGS_MARGIN = TOP_MARGIN
SETTINGS_PANEL_SIZE = (320, 240)
SETTINGS_PANEL_BG = (252, 252, 250)
SETTINGS_PANEL_BORDER = (204, 211, 196)
SETTINGS_TOGGLE_ON = (106, 136, 100)
SETTINGS_TOGGLE_OFF = (205, 210, 202)
SETTINGS_TOGGLE_LABEL = (68, 78, 72)

BASE_WINDOW_SIZE = (WIDTH, HEIGHT)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, "assets", "font", "Roboto-Regular.ttf")

ui_icons = {}
piece_images = {}
history_piece_images = {}
captured_piece_images = {}
raw_piece_images = {}
raw_ui_icons = {}
font_cache = {}
sound_effects = {}
sound_channels = {}
click_sound_enabled = True
piece_sound_enabled = True

ANIMATION_SPEED = 0.16
AI_MOVE_DELAY = 300
_is_fullscreen = False
_window_size = BASE_WINDOW_SIZE
_layout_cache = {}


@dataclass(frozen=True)
class LayoutConfig:
    screen_width: int
    screen_height: int
    scale: float
    margin: int
    gap: int
    panel_width: int
    top_bar_height: int
    bottom_bar_height: int
    board_size: int
    square_size: int
    board_x: int
    board_y: int
    left_panel_rect: pygame.Rect
    right_panel_rect: pygame.Rect
    board_rect: pygame.Rect
    top_bar_rect: pygame.Rect
    bottom_bar_rect: pygame.Rect
    settings_button_rect: pygame.Rect
    side_button_size: tuple[int, int]
    history_piece_size: int
    captured_piece_size: int
    main_piece_size: int
    settings_icon_size: int
    top_button_icon_size: int
    popup_icon_size: int


def scaled(base_value, scale, minimum=1):
    return max(minimum, int(round(base_value * scale)))


def current_screen():
    return pygame.display.get_surface()


def invalidate_ui_cache():
    _layout_cache.clear()
    piece_images.clear()
    history_piece_images.clear()
    captured_piece_images.clear()
    ui_icons.clear()
    font_cache.clear()


def is_fullscreen_enabled():
    return _is_fullscreen


def set_display_mode(fullscreen=None, size=None):
    global _is_fullscreen, _window_size
    if fullscreen is None:
        fullscreen = _is_fullscreen

    requested_size = size
    if requested_size is None:
        if fullscreen:
            info = pygame.display.Info()
            requested_size = (info.current_w, info.current_h)
        elif _window_size:
            requested_size = _window_size
        else:
            requested_size = BASE_WINDOW_SIZE

    width = max(BASE_WINDOW_SIZE[0] // 2, int(requested_size[0]))
    height = max(BASE_WINDOW_SIZE[1] // 2, int(requested_size[1]))
    _window_size = (width, height)
    _is_fullscreen = bool(fullscreen)

    screen = pygame.display.set_mode(_window_size, pygame.RESIZABLE)
    invalidate_ui_cache()
    return screen


def handle_resize(event):
    return set_display_mode(False, size=(event.w, event.h))


def toggle_fullscreen():
    if _is_fullscreen:
        return set_display_mode(False, size=BASE_WINDOW_SIZE)
    info = pygame.display.Info()
    return set_display_mode(True, size=(info.current_w, info.current_h))


def get_layout(screen=None):
    if screen is None:
        screen = current_screen()
    if screen is None:
        screen_width, screen_height = BASE_WINDOW_SIZE
    else:
        screen_width, screen_height = screen.get_size()

    key = (screen_width, screen_height)
    if key in _layout_cache:
        return _layout_cache[key]

    scale = min(screen_width / WIDTH, screen_height / HEIGHT)
    margin = scaled(MARGIN, scale)
    gap = scaled(GAP, scale)
    panel_width = scaled(PANEL_W, scale)
    top_bar_height = scaled(TOP_BAR_HEIGHT, scale)
    bottom_bar_height = scaled(BOTTOM_BAR_HEIGHT, scale)

    available_width = screen_width - (2 * margin + 2 * panel_width + 2 * gap)
    available_height = screen_height - (2 * margin + top_bar_height + bottom_bar_height + 2 * gap)
    board_size = max(8, min(available_width, available_height))
    board_size -= board_size % 8
    square_size = board_size // 8

    content_width = 2 * panel_width + 2 * gap + board_size
    board_x = (screen_width - content_width) // 2 + panel_width + gap
    vertical_used = 2 * margin + top_bar_height + gap + board_size + gap + bottom_bar_height
    board_y = (screen_height - vertical_used) // 2 + margin + top_bar_height + gap

    left_panel_rect = pygame.Rect(board_x - gap - panel_width, board_y, panel_width, board_size)
    right_panel_rect = pygame.Rect(board_x + board_size + gap, board_y, panel_width, board_size)
    board_rect = pygame.Rect(board_x, board_y, board_size, board_size)
    top_bar_rect = pygame.Rect(board_x, board_y - gap - top_bar_height, board_size, top_bar_height)
    bottom_bar_rect = pygame.Rect(board_x, board_y + board_size + gap, board_size, bottom_bar_height)
    settings_size = scaled(SETTINGS_BUTTON_SIZE, scale, minimum=32)
    settings_button_rect = pygame.Rect(margin, margin, settings_size, settings_size)

    layout = LayoutConfig(
        screen_width=screen_width,
        screen_height=screen_height,
        scale=scale,
        margin=margin,
        gap=gap,
        panel_width=panel_width,
        top_bar_height=top_bar_height,
        bottom_bar_height=bottom_bar_height,
        board_size=board_size,
        square_size=square_size,
        board_x=board_x,
        board_y=board_y,
        left_panel_rect=left_panel_rect,
        right_panel_rect=right_panel_rect,
        board_rect=board_rect,
        top_bar_rect=top_bar_rect,
        bottom_bar_rect=bottom_bar_rect,
        settings_button_rect=settings_button_rect,
        side_button_size=(scaled(78, scale, minimum=56), scaled(46, scale, minimum=38)),
        history_piece_size=scaled(24, scale, minimum=16),
        captured_piece_size=scaled(30, scale, minimum=20),
        main_piece_size=max(12, int(square_size * PIECE_SCALE)),
        settings_icon_size=scaled(48, scale, minimum=28),
        top_button_icon_size=scaled(28, scale, minimum=18),
        popup_icon_size=scaled(56, scale, minimum=30),
    )
    _layout_cache[key] = layout
    return layout


def get_font(size):
    size = max(12, int(round(size)))
    if size not in font_cache:
        font_cache[size] = pygame.font.Font(FONT_PATH, size)
    return font_cache[size]


def load_raw_images():
    if raw_piece_images and raw_ui_icons:
        return

    pieces = ["bB", "bK", "bN", "bP", "bQ", "bR", "wB", "wK", "wN", "wP", "wQ", "wR"]
    for piece_code in pieces:
        img_path = os.path.join(BASE_DIR, "assets", "images", f"{piece_code}.png")
        raw_piece_images[piece_code] = pygame.image.load(img_path).convert_alpha()

    for key, filename in {
        "reset": "reset.png",
        "home": "home.png",
        "trophy": "trophy-star.png",
        "handshake": "handshake.png",
        "settings": "settings.png",
    }.items():
        raw_ui_icons[key] = pygame.image.load(os.path.join(BASE_DIR, "assets", "icon", filename)).convert_alpha()


def load_images(layout=None):
    load_raw_images()
    layout = get_layout() if layout is None else layout
    cache_key = (layout.square_size, layout.history_piece_size, layout.captured_piece_size, layout.settings_icon_size, layout.top_button_icon_size, layout.popup_icon_size)
    if piece_images.get("_cache_key") == cache_key and ui_icons.get("_cache_key") == cache_key:
        return

    piece_images.clear()
    history_piece_images.clear()
    captured_piece_images.clear()
    ui_icons.clear()

    for piece_code, raw_image in raw_piece_images.items():
        piece_images[piece_code] = pygame.transform.smoothscale(raw_image, (layout.main_piece_size, layout.main_piece_size))
        history_piece_images[piece_code] = pygame.transform.smoothscale(raw_image, (layout.history_piece_size, layout.history_piece_size))
        captured_piece_images[piece_code] = pygame.transform.smoothscale(raw_image, (layout.captured_piece_size, layout.captured_piece_size))

    ui_icons["reset"] = pygame.transform.smoothscale(raw_ui_icons["reset"], (layout.top_button_icon_size, layout.top_button_icon_size))
    ui_icons["home"] = pygame.transform.smoothscale(raw_ui_icons["home"], (layout.top_button_icon_size, layout.top_button_icon_size))
    ui_icons["trophy"] = pygame.transform.smoothscale(raw_ui_icons["trophy"], (layout.popup_icon_size, layout.popup_icon_size))
    ui_icons["handshake"] = pygame.transform.smoothscale(raw_ui_icons["handshake"], (layout.popup_icon_size, layout.popup_icon_size))
    ui_icons["settings"] = pygame.transform.smoothscale(raw_ui_icons["settings"], (layout.settings_icon_size, layout.settings_icon_size))

    piece_images["_cache_key"] = cache_key
    ui_icons["_cache_key"] = cache_key


def load_sound_file(name):
    mp3_path = os.path.join(BASE_DIR, "assets", "sound", f"{name}.mp3")
    wav_path = os.path.join(BASE_DIR, "assets", "sound", f"{name}.wav")

    for path in (mp3_path, wav_path):
        if not os.path.exists(path):
            continue
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(0.4)
            return sound
        except (pygame.error, FileNotFoundError):
            continue

    return None


def load_sounds():
    if sound_effects:
        return

    try:
        pygame.mixer.set_num_channels(8)
    except pygame.error:
        pass

    sound_effects["move"] = load_sound_file("move-self")
    sound_effects["capture"] = load_sound_file("capture")
    sound_effects["click"] = load_sound_file("mouse-click")
    sound_effects["check"] = load_sound_file("check")

    sound_channels["move"] = pygame.mixer.Channel(1)
    sound_channels["capture"] = pygame.mixer.Channel(2)
    sound_channels["click"] = pygame.mixer.Channel(3)
    sound_channels["check"] = pygame.mixer.Channel(4)


def play_sound(key):
    sound = sound_effects.get(key)
    channel = sound_channels.get(key)

    if not sound or channel is None:
        return

    if key == "click" and not click_sound_enabled:
        return

    if key in ("move", "capture") and not piece_sound_enabled:
        return

    channel.stop()
    channel.play(sound)


def play_move_sound():
    play_sound("move")


def play_capture_sound():
    play_sound("capture")


def play_click_sound():
    play_sound("click")


def set_click_sound_enabled(value):
    global click_sound_enabled
    click_sound_enabled = bool(value)


def set_piece_sound_enabled(value):
    global piece_sound_enabled
    piece_sound_enabled = bool(value)


def draw_text(screen, text, size, color, x, y, center=False):
    font = get_font(size)
    surface = font.render(text, True, color)
    rect = surface.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    screen.blit(surface, rect)


def draw_background_gradient(screen):
    height = screen.get_height()
    width = screen.get_width()
    for y in range(height):
        ratio = y / max(1, height)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * ratio)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * ratio)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (width, y))


def draw_piece_shadow(screen, x, y, size, layout):
    shadow_w = max(12, int(size * 0.78))
    shadow_h = max(6, int(size * 0.24))
    shadow = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 44), shadow.get_rect())
    shadow_x = int(x + (size - shadow_w) / 2)
    shadow_y = int(y + size - shadow_h * 0.55)
    screen.blit(shadow, (shadow_x, shadow_y))


def draw_panel_card(screen, rect, radius, fill=PANEL, border=(255, 255, 255, 120), shadow_alpha=22):
    shadow_pad = max(6, radius // 3)
    shadow_surface = pygame.Surface((rect.width + shadow_pad * 2, rect.height + shadow_pad * 2), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surface, (0, 0, 0, shadow_alpha), shadow_surface.get_rect(), border_radius=radius)
    screen.blit(shadow_surface, (rect.x - shadow_pad // 2, rect.y - shadow_pad // 2))
    pygame.draw.rect(screen, fill, rect, border_radius=radius)
    pygame.draw.rect(screen, border, rect, 1, border_radius=radius)


def truncate_with_ellipsis(text, font, max_width):
    if font.size(text)[0] <= max_width:
        return text
    if max_width <= font.size('...')[0]:
        return ''
    stripped = text.rstrip()
    while stripped and font.size(stripped + '...')[0] > max_width:
        stripped = stripped[:-1]
    return stripped + '...' if stripped else ''


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def draw_board(screen, board_obj, valid_moves, check_king_pos=None, animation=None, hover_square=None):
    layout = get_layout(screen)
    load_images(layout)
    anim_start = animation['start'] if animation and animation['active'] else None
    anim_end = animation['end'] if animation and animation['active'] else None
    last_move = board_obj.move_log[-1] if board_obj.move_log else None

    board_outer = layout.board_rect.inflate(scaled(20, layout.scale), scaled(20, layout.scale))
    draw_panel_card(screen, board_outer, scaled(24, layout.scale), fill=(*LIGHT, 255), border=(255, 255, 255, 220), shadow_alpha=28)

    if last_move:
        for square in (last_move['start'], last_move['end']):
            square_rect = pygame.Rect(
                layout.board_x + square[1] * layout.square_size,
                layout.board_y + square[0] * layout.square_size,
                layout.square_size,
                layout.square_size,
            )
            overlay = pygame.Surface((layout.square_size, layout.square_size), pygame.SRCALPHA)
            pygame.draw.rect(overlay, LAST_MOVE_COLOR, overlay.get_rect(), border_radius=scaled(10, layout.scale))
            screen.blit(overlay, square_rect.topleft)

    move_hint_radius = max(6, layout.square_size // 8)
    move_dot_radius = max(3, layout.square_size // 16)
    capture_radius = max(10, layout.square_size // 5)
    square_radius = scaled(10, layout.scale)

    for row in range(8):
        for col in range(8):
            base_color = LIGHT if (row + col) % 2 == 0 else DARK
            color = LIGHT_HOVER if hover_square == (row, col) and (row + col) % 2 == 0 else base_color
            if hover_square == (row, col) and (row + col) % 2 == 1:
                color = DARK_HOVER

            square_rect = pygame.Rect(layout.board_x + col * layout.square_size, layout.board_y + row * layout.square_size, layout.square_size, layout.square_size)
            pygame.draw.rect(screen, color, square_rect)

            if check_king_pos == (row, col):
                danger = pygame.Surface((layout.square_size, layout.square_size), pygame.SRCALPHA)
                danger.fill((235, 83, 78, 160))
                screen.blit(danger, square_rect.topleft)

            if board_obj.selected_square == (row, col):
                glow_pad = scaled(7, layout.scale)
                glow_surface = pygame.Surface((layout.square_size + glow_pad * 2, layout.square_size + glow_pad * 2), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (194, 217, 182, 140), glow_surface.get_rect(), border_radius=square_radius)
                screen.blit(glow_surface, (square_rect.x - glow_pad, square_rect.y - glow_pad))
                pygame.draw.rect(screen, SELECT_COLOR, square_rect, max(2, scaled(3, layout.scale)), border_radius=square_radius)

    for row, col in valid_moves:
        rect = pygame.Rect(layout.board_x + col * layout.square_size, layout.board_y + row * layout.square_size, layout.square_size, layout.square_size)
        target_piece = board_obj.board[row][col]
        if target_piece != '--':
            capture_surface = pygame.Surface((layout.square_size, layout.square_size), pygame.SRCALPHA)
            pygame.draw.rect(capture_surface, (*CAPTURE_HIGHLIGHT, 90), capture_surface.get_rect(), border_radius=square_radius)
            screen.blit(capture_surface, rect.topleft)
            pygame.draw.circle(screen, CAPTURE_HIGHLIGHT, rect.center, capture_radius, max(2, scaled(3, layout.scale)))
        else:
            pygame.draw.circle(screen, MOVE_HINT, rect.center, move_hint_radius)
            pygame.draw.circle(screen, MOVE_DOT_COLOR, rect.center, move_dot_radius)

    for row in range(8):
        for col in range(8):
            piece = board_obj.board[row][col]
            if piece == '--':
                continue
            if animation and animation['active'] and (row, col) == anim_start:
                continue
            if animation and animation['active'] and animation['captured_piece'] != '--' and (row, col) == anim_end:
                continue

            piece_img = piece_images[piece]
            piece_size = piece_img.get_width()
            pos_x = layout.board_x + col * layout.square_size + (layout.square_size - piece_size) // 2
            pos_y = layout.board_y + row * layout.square_size + (layout.square_size - piece_size) // 2

            if board_obj.selected_square == (row, col):
                selection_scale = 1.04
                scaled_size = int(piece_size * selection_scale)
                piece_img = pygame.transform.smoothscale(piece_img, (scaled_size, scaled_size))
                pos_x = layout.board_x + col * layout.square_size + (layout.square_size - scaled_size) // 2
                pos_y = layout.board_y + row * layout.square_size + (layout.square_size - scaled_size) // 2

            draw_piece_shadow(screen, pos_x, pos_y, piece_img.get_width(), layout)
            screen.blit(piece_img, (pos_x, pos_y))

    if animation and animation['active'] and animation['piece']:
        start_x = layout.board_x + anim_start[1] * layout.square_size
        start_y = layout.board_y + anim_start[0] * layout.square_size
        end_x = layout.board_x + anim_end[1] * layout.square_size
        end_y = layout.board_y + anim_end[0] * layout.square_size

        progress = ease_in_out(animation['progress'])
        current_x = start_x + (end_x - start_x) * progress
        current_y = start_y + (end_y - start_y) * progress

        animated_piece = piece_images[animation['piece']]
        anim_size = animated_piece.get_width()
        pos_x = current_x + (layout.square_size - anim_size) / 2
        pos_y = current_y + (layout.square_size - anim_size) / 2

        draw_piece_shadow(screen, pos_x, pos_y, anim_size, layout)
        screen.blit(animated_piece, (pos_x, pos_y))

        if animation['captured_piece'] != '--':
            captured_alpha = int(255 * (1 - progress))
            captured_img = piece_images[animation['captured_piece']].copy()
            captured_img.set_alpha(captured_alpha)
            scale_factor = 1 + 0.2 * progress
            scaled_size = int(layout.square_size * scale_factor)
            scaled_img = pygame.transform.smoothscale(captured_img, (scaled_size, scaled_size))
            offset = (scaled_size - layout.square_size) // 2
            screen.blit(scaled_img, (end_x - offset, end_y - offset))


def draw_icon_button(screen, rect, icon_key, bg_color, hover=False):
    layout = get_layout(screen)
    color = WHITE_BTN_HOVER if hover and bg_color == WHITE_BTN else bg_color
    if hover and bg_color == DARK_BTN:
        color = DARK_BTN_HOVER

    shadow_pad = scaled(8, layout.scale)
    shadow_surface = pygame.Surface((rect.width + shadow_pad, rect.height + shadow_pad), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surface, (0, 0, 0, 35), shadow_surface.get_rect(), border_radius=scaled(14, layout.scale))
    screen.blit(shadow_surface, (rect.x - shadow_pad // 2, rect.y - shadow_pad // 2))

    pygame.draw.rect(screen, color, rect, border_radius=scaled(12, layout.scale))
    pygame.draw.rect(screen, (255, 255, 255, 30), rect, 1, border_radius=scaled(12, layout.scale))

    icon = ui_icons[icon_key]
    screen.blit(icon, icon.get_rect(center=rect.center))


def draw_settings_button(screen, rect, hover=False, pressed=False):
    layout = get_layout(screen)
    bg_color = WHITE_BTN_HOVER if hover else WHITE_BTN
    scale_factor = 0.92 if pressed else 1.05 if hover else 1.0

    button_w = int(rect.width * scale_factor)
    button_h = int(rect.height * scale_factor)
    button_rect = pygame.Rect(rect.x + (rect.width - button_w) // 2, rect.y + (rect.height - button_h) // 2, button_w, button_h)

    shadow_surface = pygame.Surface((button_rect.width + scaled(10, layout.scale), button_rect.height + scaled(10, layout.scale)), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surface, (0, 0, 0, 24), shadow_surface.get_rect(), border_radius=scaled(16, layout.scale))
    screen.blit(shadow_surface, (button_rect.x - scaled(5, layout.scale), button_rect.y - scaled(5, layout.scale)))

    pygame.draw.rect(screen, bg_color, button_rect, border_radius=scaled(16, layout.scale))
    pygame.draw.rect(screen, (178, 191, 175), button_rect, 1, border_radius=scaled(16, layout.scale))
    screen.blit(ui_icons['settings'], ui_icons['settings'].get_rect(center=button_rect.center))


def draw_settings_panel(screen, click_sound_enabled, piece_sound_enabled):
    layout = get_layout(screen)
    panel_width = scaled(SETTINGS_PANEL_SIZE[0], layout.scale, minimum=300)
    panel_height = scaled(SETTINGS_PANEL_SIZE[1], layout.scale, minimum=240)
    panel_rect = pygame.Rect((layout.screen_width - panel_width) // 2, (layout.screen_height - panel_height) // 2, panel_width, panel_height)

    overlay = pygame.Surface((layout.screen_width, layout.screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 110))
    screen.blit(overlay, (0, 0))

    draw_panel_card(screen, panel_rect, scaled(20, layout.scale), fill=SETTINGS_PANEL_BG, border=SETTINGS_PANEL_BORDER, shadow_alpha=24)
    draw_text(screen, 'Cài đặt', scaled(26, layout.scale), ACCENT, panel_rect.centerx, panel_rect.y + scaled(34, layout.scale), center=True)

    title_font = get_font(scaled(18, layout.scale))
    label_x = panel_rect.x + scaled(24, layout.scale)
    toggle_w = scaled(78, layout.scale)
    toggle_h = scaled(36, layout.scale)
    toggle_x = panel_rect.right - scaled(24, layout.scale) - toggle_w
    row_gap = scaled(68, layout.scale)
    toggle_y1 = panel_rect.y + scaled(84, layout.scale)
    toggle_y2 = toggle_y1 + row_gap

    rows = [
        ('Click Sound', click_sound_enabled, pygame.Rect(toggle_x, toggle_y1, toggle_w, toggle_h)),
        ('Piece Move Sound', piece_sound_enabled, pygame.Rect(toggle_x, toggle_y2, toggle_w, toggle_h)),
    ]

    for label, state, rect in rows:
        fitted = truncate_with_ellipsis(label, title_font, rect.x - label_x - scaled(16, layout.scale))
        draw_text(screen, fitted, scaled(18, layout.scale), SETTINGS_TOGGLE_LABEL, label_x, rect.y + (rect.height - title_font.get_height()) // 2)
        fill = SETTINGS_TOGGLE_ON if state else SETTINGS_TOGGLE_OFF
        pygame.draw.rect(screen, fill, rect, border_radius=rect.height // 2)
        pygame.draw.rect(screen, SETTINGS_PANEL_BORDER, rect, 1, border_radius=rect.height // 2)
        knob_size = rect.height - scaled(8, layout.scale)
        knob_x = rect.x + scaled(4, layout.scale) if not state else rect.right - knob_size - scaled(4, layout.scale)
        knob_rect = pygame.Rect(knob_x, rect.y + scaled(4, layout.scale), knob_size, knob_size)
        pygame.draw.ellipse(screen, (255, 255, 255), knob_rect)
        draw_text(screen, 'ON' if state else 'OFF', scaled(14, layout.scale), TEXT, rect.centerx, rect.centery, center=True)

    hint = 'F11: Fullscreen'
    draw_text(screen, hint, scaled(14, layout.scale), HISTORY_TEXT, panel_rect.centerx, panel_rect.bottom - scaled(24, layout.scale), center=True)
    return panel_rect, rows[0][2], rows[1][2]


def piece_name(piece_code):
    names = {
        "wP": "Tốt trắng",
        "wR": "Xe trắng",
        "wN": "Mã trắng",
        "wB": "Tượng trắng",
        "wQ": "Hậu trắng",
        "wK": "Vua trắng",
        "bP": "Tốt đen",
        "bR": "Xe đen",
        "bN": "Mã đen",
        "bB": "Tượng đen",
        "bQ": "Hậu đen",
        "bK": "Vua đen",
    }
    return names.get(piece_code, piece_code)


def coord_to_notation(pos):
    row, col = pos
    file = chr(ord('a') + col)
    rank = str(8 - row)
    return f"{file}{rank}"


def format_move_notation(move):
    piece = move["moving_piece"]
    symbol = piece[1] if piece[1] != "P" else ""
    start = coord_to_notation(move["start"])
    end = coord_to_notation(move["end"])
    return f"{symbol}{start}-{end}"


def truncate_text(text, font, max_width):
    return truncate_with_ellipsis(text, font, max_width)


def draw_move_history_entry(screen, font, panel_rect, y, move_number, piece_code, notation):
    icon = history_piece_images.get(piece_code)
    icon_size = icon.get_width() if icon else font.get_height()
    padding_x = max(10, panel_rect.width // 14)
    gap_x = max(4, panel_rect.width // 36)
    number_text = f'{move_number}.' if move_number != '' else ''
    content_x = panel_rect.x + padding_x
    if number_text:
        number_surface = font.render(number_text, True, HISTORY_TEXT)
        number_rect = number_surface.get_rect(topleft=(panel_rect.x + padding_x, y))
        screen.blit(number_surface, number_rect)
        content_x = number_rect.right + gap_x * 2

    if icon:
        icon_rect = icon.get_rect(topleft=(content_x, y + max(0, (font.get_height() - icon_size) // 2)))
        screen.blit(icon, icon_rect)
        text_x = icon_rect.right + gap_x
    else:
        text_x = content_x

    max_width = panel_rect.right - padding_x - text_x
    fitted = truncate_with_ellipsis(notation, font, max_width)
    draw_text(screen, fitted, font.get_height(), HISTORY_TEXT, text_x, y)


def draw_captured_section(screen, layout, section_rect, title, pieces):
    header_font = get_font(scaled(18, layout.scale))
    padding = scaled(12, layout.scale)
    draw_text(screen, title, scaled(18, layout.scale), TEXT, section_rect.centerx, section_rect.y + padding + header_font.get_height() // 2, center=True)

    icon_size = layout.captured_piece_size
    gap_icon = scaled(8, layout.scale)
    top_gap = padding + header_font.get_height() + scaled(12, layout.scale)
    usable_width = section_rect.width - padding * 2
    cols = max(1, (usable_width + gap_icon) // max(1, icon_size + gap_icon))
    total_grid_width = cols * icon_size + max(0, cols - 1) * gap_icon
    start_x = section_rect.x + padding + max(0, (usable_width - total_grid_width) // 2)

    overflow_index = None
    for index, piece in enumerate(pieces):
        row = index // cols
        col = index % cols
        x = start_x + col * (icon_size + gap_icon)
        y = section_rect.y + top_gap + row * (icon_size + gap_icon)
        if y + icon_size > section_rect.bottom - padding:
            overflow_index = index
            break
        screen.blit(captured_piece_images[piece], (x, y))

    if overflow_index is not None:
        remaining = len(pieces) - overflow_index
        row = overflow_index // cols
        col = overflow_index % cols
        x = start_x + col * (icon_size + gap_icon)
        y = section_rect.y + top_gap + row * (icon_size + gap_icon)
        overflow_bg = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        pygame.draw.rect(overflow_bg, (150, 168, 136, 180), overflow_bg.get_rect(), border_radius=scaled(6, layout.scale))
        screen.blit(overflow_bg, (x, y))
        draw_text(screen, f'+{remaining}', scaled(16, layout.scale), (255, 255, 255), x + icon_size // 2, y + icon_size // 2, center=True)


def draw_side_panels(screen, board_obj):
    layout = get_layout(screen)
    load_images(layout)
    panel_radius = scaled(16, layout.scale)
    left_rect = layout.left_panel_rect
    right_rect = layout.right_panel_rect
    draw_panel_card(screen, left_rect, panel_radius)
    draw_panel_card(screen, right_rect, panel_radius)

    header_font_size = scaled(20, layout.scale)
    draw_text(screen, 'Lịch sử nước đi', header_font_size, ACCENT, left_rect.centerx, left_rect.y + scaled(24, layout.scale), center=True)
    draw_text(screen, 'Quân bị ăn', header_font_size, ACCENT, right_rect.centerx, right_rect.y + scaled(24, layout.scale), center=True)

    history_font = get_font(scaled(15, layout.scale))
    entry_gap = scaled(6, layout.scale)
    line_height = max(history_font.get_height(), layout.history_piece_size) + scaled(4, layout.scale)
    history_top = left_rect.y + scaled(52, layout.scale)
    history_bottom = left_rect.bottom - scaled(16, layout.scale)
    available_turns = max(1, (history_bottom - history_top + entry_gap) // (line_height * 2 + entry_gap))

    history_entries = []
    start_index = max(0, len(board_obj.move_log) - available_turns * 2)
    if start_index % 2 == 1:
        start_index -= 1

    for idx in range(start_index, len(board_obj.move_log), 2):
        white_move_obj = board_obj.move_log[idx]
        black_move_obj = board_obj.move_log[idx + 1] if idx + 1 < len(board_obj.move_log) else None
        history_entries.append((
            idx // 2 + 1,
            white_move_obj['moving_piece'],
            format_move_notation(white_move_obj),
            black_move_obj['moving_piece'] if black_move_obj else None,
            format_move_notation(black_move_obj) if black_move_obj else '',
        ))

    for row_index, (move_number, white_piece, white_move, black_piece, black_move) in enumerate(history_entries[-available_turns:]):
        base_y = history_top + row_index * (line_height * 2 + entry_gap)
        draw_move_history_entry(screen, history_font, left_rect, base_y, move_number, white_piece, white_move)
        if black_piece and black_move:
            draw_move_history_entry(screen, history_font, left_rect, base_y + line_height, '', black_piece, black_move)

    header_height = scaled(52, layout.scale)
    section_height = (right_rect.height - header_height) // 2
    divider_y = right_rect.y + header_height + section_height
    pygame.draw.line(screen, (200, 210, 200), (right_rect.x + scaled(12, layout.scale), divider_y), (right_rect.right - scaled(12, layout.scale), divider_y), 1)

    white_rect = pygame.Rect(right_rect.x, right_rect.y + header_height, right_rect.width, section_height)
    black_rect = pygame.Rect(right_rect.x, divider_y, right_rect.width, right_rect.bottom - divider_y)
    draw_captured_section(screen, layout, white_rect, 'Trắng', board_obj.captured_white)
    draw_captured_section(screen, layout, black_rect, 'Đen', board_obj.captured_black)


def draw_top_bar(screen, white_to_move, turn_time, total_game_time, ai_level=None):
    layout = get_layout(screen)
    load_images(layout)
    top_rect = layout.top_bar_rect
    draw_panel_card(screen, top_rect, scaled(18, layout.scale))

    draw_text(screen, f'Tổng thời gian: {format_time(total_game_time)}', scaled(18, layout.scale), ACCENT, top_rect.centerx, top_rect.y + scaled(20, layout.scale), center=True)

    white_display = turn_time if white_to_move else 600
    black_display = turn_time if not white_to_move else 600
    timer_width = max(scaled(170, layout.scale), (top_rect.width - scaled(64, layout.scale)) // 2)
    timer_height = scaled(28, layout.scale)
    timer_y = top_rect.bottom - timer_height - scaled(10, layout.scale)
    inset = scaled(20, layout.scale)
    white_bg = pygame.Rect(top_rect.x + inset, timer_y, timer_width, timer_height)
    black_bg = pygame.Rect(top_rect.right - inset - timer_width, timer_y, timer_width, timer_height)

    for rect in (white_bg, black_bg):
        pygame.draw.rect(screen, (255, 255, 255), rect, border_radius=rect.height // 2)
        pygame.draw.rect(screen, (210, 222, 201), rect, 1, border_radius=rect.height // 2)

    draw_text(screen, f'Trắng: {format_time(white_display)}', scaled(18, layout.scale), TEXT, white_bg.centerx, white_bg.centery, center=True)
    draw_text(screen, f'Đen: {format_time(black_display)}', scaled(18, layout.scale), TEXT, black_bg.centerx, black_bg.centery, center=True)

    if ai_level is not None:
        level_names = {'easy': 'Dễ', 'normal': 'Bình thường', 'hard': 'Khó'}
        level_text = level_names.get(ai_level, ai_level.title())
        level_surface = get_font(scaled(14, layout.scale)).render(f'Độ khó: {level_text}', True, TEXT)
        level_rect = level_surface.get_rect(topright=(top_rect.right - scaled(12, layout.scale), top_rect.y + scaled(10, layout.scale)))
        screen.blit(level_surface, level_rect)

    button_w, button_h = layout.side_button_size
    right_x = layout.right_panel_rect.x
    top_y = top_rect.y + (top_rect.height - button_h) // 2
    reset_rect = pygame.Rect(right_x, top_y, button_w, button_h)
    home_rect = pygame.Rect(layout.right_panel_rect.right - button_w, top_y, button_w, button_h)
    mouse_pos = pygame.mouse.get_pos()
    draw_icon_button(screen, reset_rect, 'reset', WHITE_BTN, reset_rect.collidepoint(mouse_pos))
    draw_icon_button(screen, home_rect, 'home', DARK_BTN, home_rect.collidepoint(mouse_pos))
    return reset_rect, home_rect


def draw_end_popup(screen, winner):
    layout = get_layout(screen)
    load_images(layout)
    overlay = pygame.Surface((layout.screen_width, layout.screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    popup_w = min(scaled(420, layout.scale), layout.screen_width - scaled(64, layout.scale))
    popup_h = min(scaled(260, layout.scale), layout.screen_height - scaled(64, layout.scale))
    popup_rect = pygame.Rect((layout.screen_width - popup_w) // 2, (layout.screen_height - popup_h) // 2, popup_w, popup_h)
    draw_panel_card(screen, popup_rect, scaled(20, layout.scale), fill=POPUP_BG, border=POPUP_BORDER, shadow_alpha=36)

    center_x = popup_rect.centerx
    icon_key = 'handshake' if winner == 'Hòa' else 'trophy'
    icon_rect = ui_icons[icon_key].get_rect(center=(center_x, popup_rect.y + scaled(54, layout.scale)))
    screen.blit(ui_icons[icon_key], icon_rect)

    if winner == 'Hòa':
        draw_text(screen, 'Draw', scaled(34, layout.scale), TEXT, center_x, popup_rect.y + scaled(104, layout.scale), center=True)
        draw_text(screen, 'Game drawn', scaled(20, layout.scale), TEXT, center_x, popup_rect.y + scaled(144, layout.scale), center=True)
    else:
        draw_text(screen, 'Checkmate', scaled(36, layout.scale), TEXT, center_x, popup_rect.y + scaled(100, layout.scale), center=True)
        result_text = 'White wins' if winner == 'Trắng' else 'Black wins'
        draw_text(screen, result_text, scaled(22, layout.scale), TEXT, center_x, popup_rect.y + scaled(144, layout.scale), center=True)

    button_w = scaled(150, layout.scale)
    button_h = scaled(46, layout.scale)
    spacing = scaled(20, layout.scale)
    total_width = button_w * 2 + spacing
    start_x = popup_rect.centerx - total_width // 2
    button_y = popup_rect.bottom - button_h - scaled(24, layout.scale)
    replay_rect = pygame.Rect(start_x, button_y, button_w, button_h)
    home_rect = pygame.Rect(start_x + button_w + spacing, button_y, button_w, button_h)
    mouse_pos = pygame.mouse.get_pos()
    draw_icon_button(screen, replay_rect, 'reset', WHITE_BTN, replay_rect.collidepoint(mouse_pos))
    draw_icon_button(screen, home_rect, 'home', DARK_BTN, home_rect.collidepoint(mouse_pos))
    return replay_rect, home_rect


def draw_bottom_bar(screen, message):
    layout = get_layout(screen)
    rect = layout.bottom_bar_rect
    draw_panel_card(screen, rect, scaled(16, layout.scale), fill=(248, 249, 244), border=(214, 225, 199))
    font = get_font(scaled(24, layout.scale))
    fitted = truncate_with_ellipsis(message, font, rect.width - scaled(32, layout.scale))
    surface = font.render(fitted, True, TEXT)
    screen.blit(surface, surface.get_rect(center=rect.center))


def get_square_from_mouse(pos):
    layout = get_layout()
    mx, my = pos
    if layout.board_x <= mx < layout.board_x + layout.board_size and layout.board_y <= my < layout.board_y + layout.board_size:
        col = (mx - layout.board_x) // layout.square_size
        row = (my - layout.board_y) // layout.square_size
        return int(row), int(col)
    return None


def get_best_move(board_obj, level="normal"):
    return find_best_move(board_obj, level)


def get_square_rect_from_layout(layout, square):
    row, col = square
    return pygame.Rect(
        layout.board_x + col * layout.square_size,
        layout.board_y + row * layout.square_size,
        layout.square_size,
        layout.square_size,
    )


def normalize_move(move):
    if move is None:
        return None
    if isinstance(move, dict):
        start = move.get("start") or move.get("start_sq")
        end = move.get("end") or move.get("end_sq")
        return (start, end) if start and end else None
    if hasattr(move, "start_sq") and hasattr(move, "end_sq"):
        return move.start_sq, move.end_sq
    if isinstance(move, (tuple, list)) and len(move) == 2:
        return move[0], move[1]
    return None


def draw_hint_overlay(screen, hint_move, alpha=160, score=None):
    normalized = normalize_move(hint_move)
    if not normalized:
        return

    layout = get_layout(screen)
    start, end = normalized
    start_rect = get_square_rect_from_layout(layout, start)
    end_rect = get_square_rect_from_layout(layout, end)
    alpha = max(80, min(220, int(alpha)))
    width = max(3, scaled(4, layout.scale))
    radius = scaled(10, layout.scale)

    overlay = pygame.Surface((layout.screen_width, layout.screen_height), pygame.SRCALPHA)
    glow_pad = scaled(8, layout.scale)
    start_glow = start_rect.inflate(glow_pad * 2, glow_pad * 2)
    end_glow = end_rect.inflate(glow_pad * 2, glow_pad * 2)

    pygame.draw.rect(overlay, (0, 255, 120, alpha // 3), start_glow, border_radius=radius + glow_pad)
    pygame.draw.rect(overlay, (255, 220, 80, alpha // 3), end_glow, border_radius=radius + glow_pad)
    pygame.draw.rect(overlay, (0, 255, 120, min(190, alpha)), start_rect, width, border_radius=radius)
    pygame.draw.rect(overlay, (255, 220, 80, min(210, alpha)), end_rect, width, border_radius=radius)

    start_point = pygame.Vector2(start_rect.center)
    end_point = pygame.Vector2(end_rect.center)
    direction = end_point - start_point
    if direction.length_squared() > 0:
        direction = direction.normalize()
        arrow_start = start_point + direction * (layout.square_size * 0.22)
        arrow_end = end_point - direction * (layout.square_size * 0.22)
        arrow_color = (24, 93, 78, min(230, alpha + 35))
        pygame.draw.line(overlay, arrow_color, arrow_start, arrow_end, width)

        head_size = max(10, scaled(16, layout.scale))
        left = arrow_end - direction.rotate(28) * head_size
        right = arrow_end - direction.rotate(-28) * head_size
        pygame.draw.polygon(overlay, arrow_color, [arrow_end, left, right])

    screen.blit(overlay, (0, 0))

    if score is not None:
        score_text = f"{score:+.1f}"
        font = get_font(scaled(14, layout.scale))
        surface = font.render(score_text, True, (34, 72, 54))
        label_rect = surface.get_rect(center=(end_rect.centerx, end_rect.y + scaled(14, layout.scale)))
        bg_rect = label_rect.inflate(scaled(12, layout.scale), scaled(6, layout.scale))
        pygame.draw.rect(screen, (248, 249, 244), bg_rect, border_radius=bg_rect.height // 2)
        pygame.draw.rect(screen, (24, 132, 86), bg_rect, 1, border_radius=bg_rect.height // 2)
        screen.blit(surface, label_rect)

def draw_hint_control(screen, active=False, thinking=False):
    layout = get_layout(screen)
    rect = pygame.Rect(
        layout.right_panel_rect.x,
        layout.bottom_bar_rect.y,
        layout.right_panel_rect.width,
        layout.bottom_bar_rect.height,
    )
    mouse_pos = pygame.mouse.get_pos()
    hover = rect.collidepoint(mouse_pos)
    fill = (228, 247, 235) if active else (248, 249, 244)
    if hover:
        fill = (238, 248, 240)
    border = (24, 132, 86) if active else (214, 225, 199)

    draw_panel_card(screen, rect, scaled(16, layout.scale), fill=fill, border=border, shadow_alpha=18)
    label = "Đang nghĩ..." if thinking else "Gợi ý (H)"
    color = (24, 105, 72) if active else TEXT
    draw_text(screen, label, scaled(18, layout.scale), color, rect.centerx, rect.centery, center=True)
    return rect


def draw_blunder_warning(screen, blunder_move, score_before=None, score_after=None):
    layout = get_layout(screen)
    normalized = normalize_move(blunder_move)
    if normalized:
        for square in normalized:
            rect = get_square_rect_from_layout(layout, square)
            overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (235, 58, 58, 72), overlay.get_rect(), border_radius=scaled(10, layout.scale))
            screen.blit(overlay, rect.topleft)
            pygame.draw.rect(screen, (230, 35, 35), rect.inflate(-4, -4), max(3, scaled(4, layout.scale)), border_radius=scaled(10, layout.scale))

    warning_w = min(layout.board_rect.width - scaled(32, layout.scale), scaled(420, layout.scale))
    warning_h = scaled(54, layout.scale)
    warning_rect = pygame.Rect(
        layout.board_rect.centerx - warning_w // 2,
        layout.board_rect.y + scaled(14, layout.scale),
        warning_w,
        warning_h,
    )
    draw_panel_card(screen, warning_rect, scaled(14, layout.scale), fill=(255, 244, 240), border=(222, 90, 82), shadow_alpha=28)
    pygame.draw.circle(screen, (220, 44, 44), (warning_rect.x + scaled(28, layout.scale), warning_rect.centery), scaled(16, layout.scale))
    draw_text(screen, "?", scaled(24, layout.scale), (255, 255, 255), warning_rect.x + scaled(28, layout.scale), warning_rect.centery - scaled(1, layout.scale), center=True)

    if score_before is not None and score_after is not None:
        detail = f"{score_before:+.1f} -> {score_after:+.1f}"
    else:
        detail = "Mất lợi thế"
    draw_text(screen, "Nước đi này khiến bạn mất lợi thế!", scaled(16, layout.scale), (116, 36, 32), warning_rect.x + scaled(54, layout.scale), warning_rect.y + scaled(13, layout.scale))
    draw_text(screen, detail, scaled(13, layout.scale), (142, 66, 58), warning_rect.x + scaled(54, layout.scale), warning_rect.y + scaled(32, layout.scale))

def find_king(board_obj, color):
    king = color + "K"
    for row in range(8):
        for col in range(8):
            if board_obj.board[row][col] == king:
                return (row, col)
    return None


def is_square_attacked(board_obj, target_row, target_col, attacker_color):
    board = board_obj.board

    for row in range(8):
        for col in range(8):
            piece = board[row][col]

            if piece == "--" or piece[0] != attacker_color:
                continue

            kind = piece[1]

            if kind == "P":
                direction = -1 if attacker_color == "w" else 1
                for dc in [-1, 1]:
                    r = row + direction
                    c = col + dc
                    if (r, c) == (target_row, target_col):
                        return True
            else:
                moves = get_valid_moves(board_obj, row, col)
                if (target_row, target_col) in moves:
                    return True

    return False


def is_in_check(board_obj, color):
    king_pos = find_king(board_obj, color)
    if king_pos is None:
        return False

    enemy = "b" if color == "w" else "w"
    return is_square_attacked(board_obj, king_pos[0], king_pos[1], enemy)


def get_legal_moves(board_obj, row, col):
    piece = board_obj.get_piece(row, col)
    if piece == "--":
        return []

    color = piece[0]
    raw_moves = get_valid_moves(board_obj, row, col)
    legal_moves = []

    for move in raw_moves:
        temp_board = copy.deepcopy(board_obj)
        temp_board.move_piece((row, col), move)

        if not is_in_check(temp_board, color):
            legal_moves.append(move)

    return legal_moves


def has_any_legal_move(board_obj, color):
    for row in range(8):
        for col in range(8):
            piece = board_obj.get_piece(row, col)
            if piece != "--" and piece[0] == color:
                if get_legal_moves(board_obj, row, col):
                    return True
    return False


def click_button(pos, x, y, w, h):
    mx, my = pos
    return x <= mx <= x + w and y <= my <= y + h


def reset_game_state(board_obj):
    board_obj.reset()
    return {
        "valid_moves": [],
        "message": "Đã reset bàn cờ",
        "winner": None,
        "check_king_pos": None,
        "turn_time": 600,
        "total_game_time": 0,
        "last_tick": pygame.time.get_ticks(),
    }


def create_animation_state():
    return {
        "active": False,
        "progress": 0.0,
        "start": None,
        "end": None,
        "piece": None,
        "captured_piece": "--",
        "move_data": None,
    }


def start_animation(animation, board_obj, start, end):
    animation["active"] = True
    animation["progress"] = 0.0
    animation["start"] = start
    animation["end"] = end
    animation["piece"] = board_obj.get_piece(start[0], start[1])
    animation["captured_piece"] = board_obj.get_piece(end[0], end[1])
    animation["move_data"] = (start, end)


def clear_animation(animation):
    animation["active"] = False
    animation["progress"] = 0.0
    animation["start"] = None
    animation["end"] = None
    animation["piece"] = None
    animation["captured_piece"] = "--"
    animation["move_data"] = None


def apply_post_move_state(board_obj, moving_piece):
    current_color = "w" if board_obj.white_to_move else "b"
    current_name = "Trắng" if current_color == "w" else "Đen"

    if is_in_check(board_obj, current_color):
        check_king_pos = find_king(board_obj, current_color)
        if not has_any_legal_move(board_obj, current_color):
            winner = "Đen" if current_color == "w" else "Trắng"
            message = f"CHIẾU BÍ! {winner} thắng"
        else:
            winner = None
            message = f"{current_name} đang bị chiếu!"
    else:
        check_king_pos = None
        if not has_any_legal_move(board_obj, current_color):
            winner = "Hòa"
            message = "HẾT NƯỚC ĐI! Kết quả hòa"
        else:
            winner = None
            message = f"{piece_name(moving_piece)} di chuyển thành công"

    return winner, message, check_king_pos


def update_animation(board_obj, animation, turn_time):
    if not animation["active"]:
        return False, turn_time, None, None, None

    animation["progress"] += ANIMATION_SPEED

    if animation["progress"] < 1.0:
        return False, turn_time, None, None, None

    start, end = animation["move_data"]
    moving_piece = board_obj.get_piece(start[0], start[1])
    captured_piece = board_obj.get_piece(end[0], end[1])
    board_obj.move_piece(start, end)
    clear_animation(animation)

    # Play sound effects
    if captured_piece != "--":
        play_capture_sound()
    else:
        play_move_sound()

    turn_time = 600
    winner, message, check_king_pos = apply_post_move_state(board_obj, moving_piece)

    # Play check sound if in check
    if check_king_pos and sound_effects.get("check"):
        sound_effects["check"].play()

    return True, turn_time, winner, message, check_king_pos


def check_game_state(board_obj, player):
    """
    Check the current game state for the given player.
    Returns: "checkmate", "stalemate", or "normal"
    """
    color = "w" if player == "white" else "b"
    in_check = is_in_check(board_obj, color)
    has_moves = has_any_legal_move(board_obj, color)
    
    if in_check and not has_moves:
        return "checkmate"
    elif not in_check and not has_moves:
        return "stalemate"
    else:
        return "normal"


def can_castle(board, king_pos, rook_pos):
    """
    Check if castling is possible between king and rook.
    king_pos and rook_pos are (row, col) tuples.
    """
    kr, kc = king_pos
    rr, rc = rook_pos
    if kr != rr:  # Same row
        return False
    
    color = board.board[kr][kc][0]
    enemy = "b" if color == "w" else "w"
    
    # Check if king or rook has moved
    if (board.piece_states.get(king_pos, {}).get('has_moved', False) or
        board.piece_states.get(rook_pos, {}).get('has_moved', False)):
        return False
    
    # Check path is clear
    start_col = min(kc, rc) + 1
    end_col = max(kc, rc)
    for c in range(start_col, end_col):
        if board.board[kr][c] != "--":
            return False
    
    # Check king is not in check
    if is_in_check(board, color):
        return False
    
    # Check squares king passes through are not attacked
    king_path = [kc, kc + 1] if rc > kc else [kc, kc - 1, kc - 2]
    for c in king_path:
        if c != kc:  # Don't check current position again
            # Simulate king at this position
            original_piece = board.board[kr][c]
            board.board[kr][c] = color + "K"
            board.board[kr][kc] = "--"
            attacked = is_square_attacked(board, kr, c, enemy)
            board.board[kr][c] = original_piece
            board.board[kr][kc] = color + "K"
            if attacked:
                return False
    
    return True



def is_move_safe(board, move, player):
    """
    Check if a move is safe (doesn't leave own king in check).
    move is (start_row, start_col, end_row, end_col)
    """
    sr, sc, er, ec = move
    color = "w" if player == "white" else "b"
    
    # Simulate the move
    temp_board = copy.deepcopy(board)
    temp_board.move_piece((sr, sc), (er, ec))
    
    return not is_in_check(temp_board, color)


def run_pvp(screen):
    clock = pygame.time.Clock()
    board_obj = Board()
    load_images(get_layout(screen))
    load_sounds()

    turn_time = 600
    total_game_time = 0
    last_tick = pygame.time.get_ticks()

    valid_moves = []
    message = 'Chọn quân để bắt đầu'
    winner = None
    check_king_pos = None
    animation = create_animation_state()
    settings_open = False
    click_toggle_rect = None
    piece_toggle_rect = None

    while True:
        layout = get_layout(screen)
        load_images(layout)
        settings_button_rect = layout.settings_button_rect

        draw_background_gradient(screen)
        current_color = 'w' if board_obj.white_to_move else 'b'
        current_name = 'Trắng' if current_color == 'w' else 'Đen'

        now = pygame.time.get_ticks()
        delta = (now - last_tick) / 1000
        last_tick = now

        if winner is None and not animation['active']:
            total_game_time += delta
            turn_time -= delta

        if animation['active']:
            finished, turn_time, new_winner, new_message, new_check_king_pos = update_animation(board_obj, animation, turn_time)
            if finished:
                winner = new_winner
                message = new_message
                check_king_pos = new_check_king_pos
                valid_moves = []

        if winner is None and not animation['active'] and turn_time <= 0:
            turn_time = 600
            board_obj.white_to_move = not board_obj.white_to_move
            board_obj.selected_square = None
            valid_moves = []
            check_king_pos = None
            current_name = 'Trắng' if board_obj.white_to_move else 'Đen'
            message = f'Hết thời gian suy nghĩ, chuyển lượt sang {current_name}'

        if winner is None and not animation['active']:
            current_color = 'w' if board_obj.white_to_move else 'b'
            current_name = 'Trắng' if current_color == 'w' else 'Đen'
            if is_in_check(board_obj, current_color):
                check_king_pos = find_king(board_obj, current_color)
                if not has_any_legal_move(board_obj, current_color):
                    winner = 'Đen' if current_color == 'w' else 'Trắng'
                    message = f'CHIẾU BÍ! {winner} thắng'
                else:
                    message = f'{current_name} đang bị chiếu!'
            else:
                check_king_pos = None
                if not has_any_legal_move(board_obj, current_color):
                    winner = 'Hòa'
                    message = 'HẾT NƯỚC ĐI! Kết quả hòa'
                elif board_obj.selected_square is None:
                    message = f'Lượt: {current_name}'

        reset_rect, home_rect = draw_top_bar(screen, board_obj.white_to_move, turn_time, total_game_time)
        hover_square = get_square_from_mouse(pygame.mouse.get_pos())
        draw_settings_button(screen, settings_button_rect, settings_button_rect.collidepoint(pygame.mouse.get_pos()), settings_button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0])
        draw_side_panels(screen, board_obj)
        draw_board(screen, board_obj, valid_moves, check_king_pos, animation, hover_square)
        draw_bottom_bar(screen, message)

        panel_rect = None
        if settings_open:
            panel_rect, click_toggle_rect, piece_toggle_rect = draw_settings_panel(screen, click_sound_enabled, piece_sound_enabled)

        popup_reset_rect = None
        popup_home_rect = None
        if winner is not None:
            popup_reset_rect, popup_home_rect = draw_end_popup(screen, winner)

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                screen = toggle_fullscreen()
                last_tick = pygame.time.get_ticks()
                break
            if event.type == pygame.VIDEORESIZE:
                screen = handle_resize(event)
                last_tick = pygame.time.get_ticks()
                break
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                play_click_sound()
                pos = event.pos

                if settings_button_rect.collidepoint(pos):
                    settings_open = not settings_open
                    continue

                if settings_open:
                    panel_clicked = panel_rect and panel_rect.collidepoint(pos)
                    toggle_clicked = False
                    if panel_clicked:
                        if click_toggle_rect and click_toggle_rect.collidepoint(pos):
                            set_click_sound_enabled(not click_sound_enabled)
                            toggle_clicked = True
                        elif piece_toggle_rect and piece_toggle_rect.collidepoint(pos):
                            set_piece_sound_enabled(not piece_sound_enabled)
                            toggle_clicked = True
                    if not panel_clicked and not toggle_clicked:
                        settings_open = False
                    continue

                if winner is not None:
                    if popup_reset_rect and click_button(pos, popup_reset_rect.x, popup_reset_rect.y, popup_reset_rect.width, popup_reset_rect.height):
                        state = reset_game_state(board_obj)
                        valid_moves = state['valid_moves']
                        message = state['message']
                        winner = state['winner']
                        check_king_pos = state['check_king_pos']
                        turn_time = state['turn_time']
                        total_game_time = state['total_game_time']
                        last_tick = state['last_tick']
                        clear_animation(animation)
                        continue
                    if popup_home_rect and click_button(pos, popup_home_rect.x, popup_home_rect.y, popup_home_rect.width, popup_home_rect.height):
                        return 'menu'
                    continue

                if animation['active']:
                    continue
                if click_button(pos, reset_rect.x, reset_rect.y, reset_rect.width, reset_rect.height):
                    state = reset_game_state(board_obj)
                    valid_moves = state['valid_moves']
                    message = state['message']
                    winner = state['winner']
                    check_king_pos = state['check_king_pos']
                    turn_time = state['turn_time']
                    total_game_time = state['total_game_time']
                    last_tick = state['last_tick']
                    clear_animation(animation)
                    continue
                if click_button(pos, home_rect.x, home_rect.y, home_rect.width, home_rect.height):
                    return 'menu'

                square = get_square_from_mouse(pos)
                if square is None:
                    continue

                row, col = square
                piece = board_obj.get_piece(row, col)
                if board_obj.selected_square is None:
                    if piece == '--':
                        message = 'Ô này đang trống'
                        continue
                    if board_obj.white_to_move and piece[0] != 'w':
                        message = 'Đang tới lượt Trắng'
                        continue
                    if (not board_obj.white_to_move) and piece[0] != 'b':
                        message = 'Đang tới lượt Đen'
                        continue
                    board_obj.selected_square = (row, col)
                    valid_moves = get_legal_moves(board_obj, row, col)
                    message = 'Không thể đi được quân này' if len(valid_moves) == 0 else f'Đã chọn {piece_name(piece)}'
                    continue

                start_square = board_obj.selected_square
                if piece != '--':
                    selected_piece = board_obj.get_piece(start_square[0], start_square[1])
                    if piece[0] == selected_piece[0]:
                        board_obj.selected_square = (row, col)
                        valid_moves = get_legal_moves(board_obj, row, col)
                        message = f'Đổi chọn sang {piece_name(piece)}'
                        continue

                if (row, col) in valid_moves:
                    start_animation(animation, board_obj, start_square, (row, col))
                    board_obj.selected_square = None
                    valid_moves = []
                    message = f"{piece_name(animation['piece'])} đang di chuyển..."
                else:
                    board_obj.selected_square = None
                    valid_moves = []
                    message = 'Nước đi không hợp lệ'



BLUNDER_THRESHOLD = 0.8
EVAL_BAR_VISUAL_SCALE = 3.0

def run_pve(screen, ai_level='normal'):
    clock = pygame.time.Clock()
    board_obj = Board()
    load_images(get_layout(screen))
    load_sounds()

    turn_time = 600
    total_game_time = 0
    last_tick = pygame.time.get_ticks()

    valid_moves = []
    message = 'Chọn quân để bắt đầu'
    winner = None
    check_king_pos = None

    ai_score = evaluate_board(board_obj, ai_level)
    display_score = ai_score
    pending_blunder_prev_score = None
    is_blunder = False
    blunder_timer = 0.0
    blunder_move = None
    blunder_score_before = None
    blunder_score_after = None

    show_hint = False
    hint_timer = 0.0
    hint_move = None
    hint_score = None
    hint_thinking = False
    last_hint_board = None

    human_color = 'w'
    ai_color = 'b'

    animation = create_animation_state()
    settings_open = False
    click_toggle_rect = None
    piece_toggle_rect = None

    ai_turn_started_at = None
    ai_thinking = False
    ai_move_result = {'move': None}
    ai_lock = threading.Lock()
    ai_task_id = {'current': 0}

    hint_move_result = {'move': None, 'score': None, 'done': False}
    hint_lock = threading.Lock()
    hint_task_id = {'current': 0}

    def ai_worker(board_snapshot, level, task_id):
        start_time = time.time()
        move = find_best_move(board_snapshot, level)
        elapsed = time.time() - start_time
        min_delay = {'easy': 0.3, 'normal': 0.4, 'hard': 0.5}.get(level, 0.4)
        if elapsed < min_delay:
            time.sleep(min_delay - elapsed)
        with ai_lock:
            if task_id != ai_task_id['current']:
                return
            ai_move_result['move'] = move

    def hint_worker(board_snapshot, task_id):
        start_time = time.time()
        move = None
        score = None
        try:
            move = find_best_move(board_snapshot, "hard")
            if move is not None:
                score_board = copy.deepcopy(board_snapshot)
                score_board.move_piece(move[0], move[1])
                score = evaluate_board(score_board, "hard")
                if human_color == 'b':
                    score = -score
        except Exception:
            move = None
            score = None

        elapsed = time.time() - start_time
        min_time = 0.4
        if elapsed < min_time:
            time.sleep(min_time - elapsed)

        with hint_lock:
            if task_id != hint_task_id['current']:
                return
            hint_move_result['move'] = move
            hint_move_result['score'] = score
            hint_move_result['done'] = True

    def request_hint():
        nonlocal hint_thinking, show_hint, hint_timer, hint_move, hint_score, last_hint_board, message
        if show_hint and hint_move is not None and not hint_thinking:
            show_hint = False
            hint_timer = 0.0
            message = 'Đã tắt gợi ý'
            return
        if winner is not None or animation['active'] or ai_thinking or hint_thinking:
            return
        if ('w' if board_obj.white_to_move else 'b') != human_color:
            return

        board_state = str(board_obj.board) + str(board_obj.white_to_move)
        if board_state == last_hint_board and hint_move is not None:
            show_hint = True
            hint_timer = 0.0
            message = 'Đã hiển thị lại gợi ý đã lưu'
            return

        hint_thinking = True
        show_hint = False
        hint_move = None
        hint_score = None
        hint_timer = 0.0
        last_hint_board = board_state
        message = 'Đang tính gợi ý mạnh...'

        with hint_lock:
            hint_task_id['current'] += 1
            current_task_id = hint_task_id['current']
            hint_move_result['move'] = None
            hint_move_result['score'] = None
            hint_move_result['done'] = False

        board_snapshot = copy.deepcopy(board_obj)
        threading.Thread(target=hint_worker, args=(board_snapshot, current_task_id), daemon=True).start()

    def clear_tutor_ui_state():
        nonlocal show_hint, hint_timer, hint_move, hint_score, hint_thinking, last_hint_board
        nonlocal is_blunder, blunder_timer, blunder_move, blunder_score_before, blunder_score_after

        show_hint = False
        hint_timer = 0.0
        hint_move = None
        hint_score = None
        hint_thinking = False
        last_hint_board = None

        is_blunder = False
        blunder_timer = 0.0
        blunder_move = None
        blunder_score_before = None
        blunder_score_after = None

        with hint_lock:
            hint_task_id['current'] += 1
            hint_move_result['move'] = None
            hint_move_result['score'] = None
            hint_move_result['done'] = False

    while True:
        layout = get_layout(screen)
        load_images(layout)
        settings_button_rect = layout.settings_button_rect

        draw_background_gradient(screen)
        current_color = 'w' if board_obj.white_to_move else 'b'
        current_name = 'Trắng' if current_color == 'w' else 'Đen'
        move_made = False

        now = pygame.time.get_ticks()
        delta = (now - last_tick) / 1000
        last_tick = now

        if show_hint or hint_move is not None or hint_thinking:
            hint_timer += delta

        if is_blunder:
            blunder_timer += delta
            if blunder_timer > 3.0:
                is_blunder = False
                blunder_timer = 0.0
                blunder_move = None
                blunder_score_before = None
                blunder_score_after = None

        if winner is None and not animation['active']:
            total_game_time += delta
            turn_time -= delta

        if animation['active']:
            finished, turn_time, new_winner, new_message, new_check_king_pos = update_animation(board_obj, animation, turn_time)
            if finished:
                winner = new_winner
                message = new_message
                check_king_pos = new_check_king_pos
                valid_moves = []
                ai_turn_started_at = None
                move_made = True
                

        current_color = 'w' if board_obj.white_to_move else 'b'
        current_name = 'Trắng' if current_color == 'w' else 'Đen'

        if move_made:
            ai_score = evaluate_board(board_obj, ai_level)
            display_score = display_score * 0.9 + ai_score * 0.1
            last_move = board_obj.move_log[-1] if board_obj.move_log else None
            if last_move and last_move.get('moving_piece', '--')[0] == human_color and pending_blunder_prev_score is not None:
                score_before = pending_blunder_prev_score
                score_after = ai_score
                human_before = score_before if human_color == 'w' else -score_before
                human_after = score_after if human_color == 'w' else -score_after
                score_drop = human_before - human_after

                if score_drop > BLUNDER_THRESHOLD:
                    is_blunder = True
                    blunder_timer = 0.0
                    blunder_move = (last_move['start'], last_move['end'])
                    blunder_score_before = human_before
                    blunder_score_after = human_after
                    message = 'Nước đi này khiến bạn mất lợi thế!'

                pending_blunder_prev_score = None

        if winner is None and not animation['active'] and turn_time <= 0:
            winner = 'Trắng' if current_color == ai_color else 'Đen'
            message = f'Hết thời gian! {winner} thắng'
            ai_thinking = False
            ai_turn_started_at = None

        if winner is None and not animation['active']:
            current_color = 'w' if board_obj.white_to_move else 'b'
            current_name = 'Trắng' if current_color == 'w' else 'Đen'

            if is_in_check(board_obj, current_color):
                check_king_pos = find_king(board_obj, current_color)
                if not has_any_legal_move(board_obj, current_color):
                    winner = 'Đen' if current_color == 'w' else 'Trắng'
                    message = f'CHIẾU BÍ! {winner} thắng'
                else:
                    message = 'Máy đang suy nghĩ...' if current_color == ai_color and ai_thinking else f'{current_name} đang bị chiếu!'
            else:
                check_king_pos = None
                if not has_any_legal_move(board_obj, current_color):
                    winner = 'Hòa'
                    message = 'HẾT NƯỚC ĐI! Kết quả hòa'
                elif current_color == ai_color:
                    if not is_blunder:
                        message = 'Máy đang suy nghĩ...' if ai_thinking else 'Máy chuẩn bị suy nghĩ...'
                elif board_obj.selected_square is None:
                    message = f'Lượt: {current_name}'

        if winner is None and not animation['active'] and current_color == ai_color:
            if not ai_thinking:
                if ai_turn_started_at is None:
                    ai_turn_started_at = pygame.time.get_ticks()
                if pygame.time.get_ticks() - ai_turn_started_at >= AI_MOVE_DELAY:
                    ai_thinking = True
                    with ai_lock:
                        ai_task_id['current'] += 1
                        current_task_id = ai_task_id['current']
                        ai_move_result['move'] = None
                    board_snapshot = copy.deepcopy(board_obj)
                    threading.Thread(target=ai_worker, args=(board_snapshot, ai_level, current_task_id), daemon=True).start()
            else:
                with ai_lock:
                    move = ai_move_result['move']
                if move is not None:
                    ai_thinking = False
                    with ai_lock:
                        ai_move_result['move'] = None
                    start_animation(animation, board_obj, move[0], move[1])
                    board_obj.selected_square = None
                    valid_moves = []
                    message = 'Máy đang di chuyển...'
                    ai_turn_started_at = None

        with hint_lock:
            hint_done = hint_move_result.get('done', False)
            computed_hint_move = hint_move_result.get('move')
            computed_hint_score = hint_move_result.get('score')
            if hint_done:
                hint_move_result['done'] = False
                hint_move_result['move'] = None
                hint_move_result['score'] = None

        if hint_done:
            hint_thinking = False
            hint_move = computed_hint_move
            hint_score = computed_hint_score
            show_hint = hint_move is not None
            hint_timer = 0.0
            message = 'Đã hiển thị gợi ý nước đi tốt nhất' if show_hint else 'Không có nước gợi ý hợp lệ'

        display_score = display_score * 0.75 + ai_score * 0.25

        reset_rect, home_rect = draw_top_bar(screen, board_obj.white_to_move, turn_time, total_game_time, ai_level)
        hover_square = get_square_from_mouse(pygame.mouse.get_pos())
        draw_settings_button(
            screen,
            settings_button_rect,
            settings_button_rect.collidepoint(pygame.mouse.get_pos()),
            settings_button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0],
        )
        draw_side_panels(screen, board_obj)
        draw_board(screen, board_obj, valid_moves, check_king_pos, animation, hover_square)

        bar_width = max(14, scaled(18, layout.scale))
        visual_score = max(-10.0, min(10.0, display_score * EVAL_BAR_VISUAL_SCALE))
        draw_evaluation_bar(
            screen,
            visual_score,
            layout.board_rect.right + scaled(10, layout.scale),
            layout.board_rect.y,
            bar_width,
            layout.board_rect.height,
            white_color=(248, 248, 244),
            black_color=(54, 64, 58),
            border_color=(37, 47, 41),
        )

        if show_hint and hint_move:
            hint_alpha = int(120 + 80 * math.sin(hint_timer * 4))
            draw_hint_overlay(screen, hint_move, hint_alpha, hint_score)

        if is_blunder:
            draw_blunder_warning(screen, blunder_move, blunder_score_before, blunder_score_after)

        draw_bottom_bar(screen, message)
        hint_button_rect = draw_hint_control(screen, active=show_hint or hint_thinking, thinking=hint_thinking)

        panel_rect = None
        if settings_open:
            panel_rect, click_toggle_rect, piece_toggle_rect = draw_settings_panel(screen, click_sound_enabled, piece_sound_enabled)

        popup_reset_rect = None
        popup_home_rect = None
        if winner is not None:
            popup_reset_rect, popup_home_rect = draw_end_popup(screen, winner)

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    screen = toggle_fullscreen()
                    last_tick = pygame.time.get_ticks()
                    break
                if event.key == pygame.K_h:
                    request_hint()
                    continue

            if event.type == pygame.VIDEORESIZE:
                screen = handle_resize(event)
                last_tick = pygame.time.get_ticks()
                break

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                play_click_sound()
                pos = event.pos

                if settings_button_rect.collidepoint(pos):
                    settings_open = not settings_open
                    continue

                if settings_open:
                    panel_clicked = panel_rect and panel_rect.collidepoint(pos)
                    toggle_clicked = False
                    if panel_clicked:
                        if click_toggle_rect and click_toggle_rect.collidepoint(pos):
                            set_click_sound_enabled(not click_sound_enabled)
                            toggle_clicked = True
                        elif piece_toggle_rect and piece_toggle_rect.collidepoint(pos):
                            set_piece_sound_enabled(not piece_sound_enabled)
                            toggle_clicked = True
                    if not panel_clicked and not toggle_clicked:
                        settings_open = False
                    continue

                if winner is not None:
                    if popup_reset_rect and click_button(pos, popup_reset_rect.x, popup_reset_rect.y, popup_reset_rect.width, popup_reset_rect.height):
                        state = reset_game_state(board_obj)
                        valid_moves = state['valid_moves']
                        message = state['message']
                        winner = state['winner']
                        check_king_pos = state['check_king_pos']
                        turn_time = state['turn_time']
                        total_game_time = state['total_game_time']
                        last_tick = state['last_tick']
                        clear_animation(animation)
                        ai_turn_started_at = None
                        ai_thinking = False
                        with ai_lock:
                            ai_task_id['current'] += 1
                            ai_move_result['move'] = None
                        ai_score = evaluate_board(board_obj, ai_level)
                        display_score = ai_score
                        pending_blunder_prev_score = None
                        clear_tutor_ui_state()
                        continue
                    if popup_home_rect and click_button(pos, popup_home_rect.x, popup_home_rect.y, popup_home_rect.width, popup_home_rect.height):
                        return 'menu'
                    continue

                if hint_button_rect.collidepoint(pos):
                    request_hint()
                    continue

                if click_button(pos, reset_rect.x, reset_rect.y, reset_rect.width, reset_rect.height):
                    state = reset_game_state(board_obj)
                    valid_moves = state['valid_moves']
                    message = state['message']
                    winner = state['winner']
                    check_king_pos = state['check_king_pos']
                    turn_time = state['turn_time']
                    total_game_time = state['total_game_time']
                    last_tick = state['last_tick']
                    clear_animation(animation)
                    ai_turn_started_at = None
                    ai_thinking = False
                    with ai_lock:
                        ai_task_id['current'] += 1
                        ai_move_result['move'] = None
                    ai_score = evaluate_board(board_obj, ai_level)
                    display_score = ai_score
                    pending_blunder_prev_score = None
                    clear_tutor_ui_state()
                    continue

                if click_button(pos, home_rect.x, home_rect.y, home_rect.width, home_rect.height):
                    return 'menu'

                if animation['active'] or ai_thinking:
                    continue

                if ('w' if board_obj.white_to_move else 'b') != human_color:
                    continue

                square = get_square_from_mouse(pos)
                if square is None:
                    continue

                row, col = square
                piece = board_obj.get_piece(row, col)

                if board_obj.selected_square is None:
                    if piece == '--':
                        message = 'Ô này đang trống'
                        continue
                    if piece[0] != human_color:
                        message = 'Đang tới lượt của bạn'
                        continue
                    board_obj.selected_square = (row, col)
                    valid_moves = get_legal_moves(board_obj, row, col)
                    message = 'Quân này không có nước đi hợp lệ' if len(valid_moves) == 0 else f'Đã chọn {piece_name(piece)}'
                    continue

                start_square = board_obj.selected_square
                if piece != '--':
                    selected_piece = board_obj.get_piece(start_square[0], start_square[1])
                    if piece[0] == selected_piece[0]:
                        board_obj.selected_square = (row, col)
                        valid_moves = get_legal_moves(board_obj, row, col)
                        message = f'Đổi chọn sang {piece_name(piece)}'
                        continue

                if (row, col) in valid_moves:
                    pending_blunder_prev_score = evaluate_board(board_obj, ai_level)
                    clear_tutor_ui_state()
                    start_animation(animation, board_obj, start_square, (row, col))
                    turn_time = 600
                    board_obj.selected_square = None
                    valid_moves = []
                    message = f"{piece_name(animation['piece'])} đang di chuyển..."
                    ai_turn_started_at = None
                else:
                    board_obj.selected_square = None
                    valid_moves = []
                    message = 'Nước đi không hợp lệ'

def format_time(t):
    t = max(0, int(t))
    minutes = t // 60
    seconds = t % 60
    return f"{minutes:02}:{seconds:02}"


