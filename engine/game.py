import os
import time
import pygame
import copy
import threading
from engine.board import Board
from engine.moves import get_valid_moves
from engine.ai import find_best_move

# pygame.mixer.init()  # Initialize mixer for sounds - removed, using pre_init from main.py

WIDTH = 1120
HEIGHT = 860

LEFT_MARGIN = 40
RIGHT_MARGIN = LEFT_MARGIN
PANEL_W = 180
GAP = 40

MARGIN = 20
TOP_BAR_HEIGHT = 70
BOTTOM_BAR_HEIGHT = 65

BOARD_SIZE = 600
ROWS, COLS = 8, 8
SQ_SIZE = BOARD_SIZE // 8
PIECE_SCALE = 0.94

BOARD_X = LEFT_MARGIN + PANEL_W + GAP
BOARD_Y = MARGIN + TOP_BAR_HEIGHT + GAP

LIGHT = (234, 240, 225)  # Light square color
DARK = (192, 203, 178)   # Dark square color
SELECT_COLOR = (150, 168, 136)  # Warm highlight for selection
MOVE_HINT = (142, 173, 143)      # Soft green for move hints
BG_TOP = (248, 249, 244)
BG_BOTTOM = (230, 237, 224)
TEXT = (35, 45, 39)
PANEL = (244, 246, 239)

# Hover colors
LIGHT_HOVER = (238, 244, 229)
DARK_HOVER = (204, 216, 189)

# Shadow color
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
SETTINGS_MARGIN = 16
SETTINGS_PANEL_SIZE = (320, 240)
SETTINGS_PANEL_BG = (252, 252, 250)
SETTINGS_PANEL_BORDER = (204, 211, 196)
SETTINGS_TOGGLE_ON = (106, 136, 100)
SETTINGS_TOGGLE_OFF = (205, 210, 202)
SETTINGS_TOGGLE_LABEL = (68, 78, 72)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, "assets", "font", "Roboto-Regular.ttf")

ui_icons = {}
piece_images = {}
history_piece_images = {}
captured_piece_images = {}
font_cache = {}
sound_effects = {}
sound_channels = {}
click_sound_enabled = True
piece_sound_enabled = True

ANIMATION_SPEED = 0.16
AI_MOVE_DELAY = 300  # Giảm từ 500 xuống 300ms


def get_font(size):
    if size not in font_cache:
        font_cache[size] = pygame.font.Font(FONT_PATH, size)
    return font_cache[size]


def load_images():
    if piece_images and ui_icons:
        return

    pieces = ["bB", "bK", "bN", "bP", "bQ", "bR", "wB", "wK", "wN", "wP", "wQ", "wR"]

    history_icon_size = 24
    captured_icon_size = 30
    for p in pieces:
        img_path = os.path.join(BASE_DIR, "assets", "images", f"{p}.png")
        img = pygame.image.load(img_path).convert_alpha()
        target_size = int(SQ_SIZE * PIECE_SCALE)
        piece_images[p] = pygame.transform.smoothscale(img, (target_size, target_size))
        history_piece_images[p] = pygame.transform.smoothscale(img, (history_icon_size, history_icon_size))
        captured_piece_images[p] = pygame.transform.smoothscale(img, (captured_icon_size, captured_icon_size))

    ui_icons["reset"] = pygame.transform.smoothscale(
        pygame.image.load(os.path.join(BASE_DIR, "assets", "icon", "reset.png")).convert_alpha(),
        (28, 28)
    )
    ui_icons["home"] = pygame.transform.smoothscale(
        pygame.image.load(os.path.join(BASE_DIR, "assets", "icon", "home.png")).convert_alpha(),
        (28, 28)
    )
    ui_icons["trophy"] = pygame.transform.smoothscale(
        pygame.image.load(os.path.join(BASE_DIR, "assets", "icon", "trophy-star.png")).convert_alpha(),
        (56, 56)
    )
    ui_icons["handshake"] = pygame.transform.smoothscale(
        pygame.image.load(os.path.join(BASE_DIR, "assets", "icon", "handshake.png")).convert_alpha(),
        (56, 56)
    )
    ui_icons["settings"] = pygame.transform.smoothscale(
        pygame.image.load(os.path.join(BASE_DIR, "assets", "icon", "settings.png")).convert_alpha(),
        (48, 48)
    )


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
    for y in range(height):
        ratio = y / height
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * ratio)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * ratio)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (screen.get_width(), y))


def draw_piece_shadow(screen, x, y, size):
    shadow = pygame.Surface((size, size // 2), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 40), shadow.get_rect())
    screen.blit(shadow, (x + 6, y + size - size // 3))


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def draw_board(screen, board_obj, valid_moves, check_king_pos=None, animation=None, hover_square=None):
    anim_start = None
    anim_end = None
    last_move = board_obj.move_log[-1] if board_obj.move_log else None

    if animation and animation["active"]:
        anim_start = animation["start"]
        anim_end = animation["end"]

    board_rect = pygame.Rect(BOARD_X - 10, BOARD_Y - 10, BOARD_SIZE + 20, BOARD_SIZE + 20)
    board_bg = pygame.Surface((board_rect.width, board_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(board_bg, (*LIGHT, 14), board_bg.get_rect(), border_radius=24)
    pygame.draw.rect(board_bg, (255, 255, 255, 220), board_bg.get_rect(), 1, border_radius=24)
    screen.blit(board_bg, board_rect.topleft)

    if last_move:
        for square in (last_move["start"], last_move["end"]):
            square_rect = pygame.Rect(
                BOARD_X + square[1] * SQ_SIZE,
                BOARD_Y + square[0] * SQ_SIZE,
                SQ_SIZE,
                SQ_SIZE
            )
            overlay = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(overlay, LAST_MOVE_COLOR, overlay.get_rect(), border_radius=10)
            screen.blit(overlay, square_rect.topleft)

    for row in range(8):
        for col in range(8):
            base_color = LIGHT if (row + col) % 2 == 0 else DARK
            color = base_color

            if hover_square == (row, col):
                color = LIGHT_HOVER if (row + col) % 2 == 0 else DARK_HOVER

            square_rect = pygame.Rect(BOARD_X + col * SQ_SIZE, BOARD_Y + row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            pygame.draw.rect(screen, color, square_rect)

            if check_king_pos == (row, col):
                danger = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
                danger.fill((235, 83, 78, 160))
                screen.blit(danger, square_rect.topleft)

            if board_obj.selected_square == (row, col):
                glow_surface = pygame.Surface((SQ_SIZE + 14, SQ_SIZE + 14), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (194, 217, 182, 140), glow_surface.get_rect(), border_radius=12)
                screen.blit(glow_surface, (square_rect.x - 7, square_rect.y - 7))
                pygame.draw.rect(screen, SELECT_COLOR, square_rect, 3, border_radius=10)

    for (r, c) in valid_moves:
        rect = pygame.Rect(BOARD_X + c * SQ_SIZE, BOARD_Y + r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        target_piece = board_obj.board[r][c]

        if target_piece != "--":
            capture_surface = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(capture_surface, (*CAPTURE_HIGHLIGHT, 90), capture_surface.get_rect(), border_radius=10)
            screen.blit(capture_surface, rect.topleft)
            pygame.draw.circle(screen, CAPTURE_HIGHLIGHT, rect.center, 15, 3)
        else:
            pygame.draw.circle(screen, MOVE_HINT, rect.center, 10)
            pygame.draw.circle(screen, MOVE_DOT_COLOR, rect.center, 5)

    for row in range(8):
        for col in range(8):
            piece = board_obj.board[row][col]
            if piece == "--":
                continue

            if animation and animation["active"] and (row, col) == anim_start:
                continue

            if animation and animation["active"] and animation["captured_piece"] != "--" and (row, col) == anim_end:
                continue

            piece_img = piece_images[piece]
            piece_size = piece_img.get_width()
            pos_x = BOARD_X + col * SQ_SIZE + (SQ_SIZE - piece_size) // 2
            pos_y = BOARD_Y + row * SQ_SIZE + (SQ_SIZE - piece_size) // 2

            if board_obj.selected_square == (row, col):
                selection_scale = 1.04
                scaled_size = int(piece_size * selection_scale)
                piece_img = pygame.transform.smoothscale(piece_img, (scaled_size, scaled_size))
                pos_x = BOARD_X + col * SQ_SIZE + (SQ_SIZE - scaled_size) // 2
                pos_y = BOARD_Y + row * SQ_SIZE + (SQ_SIZE - scaled_size) // 2

            draw_piece_shadow(screen, pos_x, pos_y, piece_size)
            screen.blit(piece_img, (pos_x, pos_y))

    if animation and animation["active"] and animation["piece"]:
        start_x = BOARD_X + anim_start[1] * SQ_SIZE
        start_y = BOARD_Y + anim_start[0] * SQ_SIZE
        end_x = BOARD_X + anim_end[1] * SQ_SIZE
        end_y = BOARD_Y + anim_end[0] * SQ_SIZE

        p = ease_in_out(animation["progress"])
        current_x = start_x + (end_x - start_x) * p
        current_y = start_y + (end_y - start_y) * p

        animated_piece = piece_images[animation["piece"]]
        anim_size = animated_piece.get_width()
        pos_x = current_x + (SQ_SIZE - anim_size) / 2
        pos_y = current_y + (SQ_SIZE - anim_size) / 2

        draw_piece_shadow(screen, pos_x, pos_y, anim_size)
        screen.blit(animated_piece, (pos_x, pos_y))

        if animation["captured_piece"] != "--":
            captured_alpha = int(255 * (1 - p))
            captured_img = piece_images[animation["captured_piece"]].copy()
            captured_img.set_alpha(captured_alpha)
            scale_factor = 1 + 0.2 * p
            scaled_size = int(SQ_SIZE * scale_factor)
            scaled_img = pygame.transform.smoothscale(captured_img, (scaled_size, scaled_size))
            offset = (scaled_size - SQ_SIZE) // 2
            screen.blit(scaled_img, (end_x - offset, end_y - offset))



def draw_icon_button(screen, rect, icon_key, bg_color, hover=False):
    if hover:
        color = WHITE_BTN_HOVER if bg_color == WHITE_BTN else DARK_BTN_HOVER
    else:
        color = bg_color

    shadow_surface = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surface, (0, 0, 0, 35), shadow_surface.get_rect(), border_radius=14)
    screen.blit(shadow_surface, (rect.x - 4, rect.y - 4))

    pygame.draw.rect(screen, color, rect, border_radius=12)
    pygame.draw.rect(screen, (255, 255, 255, 30), rect, 1, border_radius=12)

    icon = ui_icons[icon_key]
    icon_rect = icon.get_rect(center=rect.center)
    screen.blit(icon, icon_rect)


def draw_settings_button(screen, rect, hover=False, pressed=False):
    bg_color = WHITE_BTN_HOVER if hover else WHITE_BTN
    if pressed:
        scale = 0.92
    elif hover:
        scale = 1.05
    else:
        scale = 1.0

    button_w = int(rect.width * scale)
    button_h = int(rect.height * scale)
    button_x = rect.x + (rect.width - button_w) // 2
    button_y = rect.y + (rect.height - button_h) // 2
    button_rect = pygame.Rect(button_x, button_y, button_w, button_h)

    shadow_surface = pygame.Surface((button_rect.width + 10, button_rect.height + 10), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surface, (0, 0, 0, 24), shadow_surface.get_rect(), border_radius=16)
    screen.blit(shadow_surface, (button_rect.x - 5, button_rect.y - 5))

    pygame.draw.rect(screen, bg_color, button_rect, border_radius=16)
    pygame.draw.rect(screen, (178, 191, 175), button_rect, 1, border_radius=16)

    icon = ui_icons["settings"]
    icon_rect = icon.get_rect(center=button_rect.center)
    screen.blit(icon, icon_rect)


def draw_settings_panel(screen, click_sound_enabled, piece_sound_enabled):
    panel_width, panel_height = SETTINGS_PANEL_SIZE
    panel_rect = pygame.Rect(
        (WIDTH - panel_width) // 2,
        (HEIGHT - panel_height) // 2,
        panel_width,
        panel_height,
    )

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 110))
    screen.blit(overlay, (0, 0))

    shadow = pygame.Surface((panel_rect.width + 20, panel_rect.height + 20), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 24), shadow.get_rect(), border_radius=16)
    screen.blit(shadow, (panel_rect.x - 10, panel_rect.y - 10))

    pygame.draw.rect(screen, SETTINGS_PANEL_BG, panel_rect, border_radius=14)
    pygame.draw.rect(screen, SETTINGS_PANEL_BORDER, panel_rect, 1, border_radius=14)

    draw_text(screen, "Cài đặt", 26, ACCENT, panel_rect.centerx, panel_rect.y + 34, center=True)

    toggle_width = 74
    toggle_height = 34
    toggle_x = panel_rect.right - toggle_width - 24

    toggle_y1 = panel_rect.y + 84
    toggle_y2 = panel_rect.y + 148

    draw_text(screen, "Click Sound", 20, SETTINGS_TOGGLE_LABEL, panel_rect.x + 24, toggle_y1 + 4, center=False)
    draw_text(screen, "Piece Move Sound", 20, SETTINGS_TOGGLE_LABEL, panel_rect.x + 24, toggle_y2 + 4, center=False)

    for idx, state in enumerate((click_sound_enabled, piece_sound_enabled)):
        toggle_y = toggle_y1 if idx == 0 else toggle_y2
        toggle_rect = pygame.Rect(toggle_x, toggle_y, toggle_width, toggle_height)
        fill = SETTINGS_TOGGLE_ON if state else SETTINGS_TOGGLE_OFF
        pygame.draw.rect(screen, fill, toggle_rect, border_radius=16)
        pygame.draw.rect(screen, SETTINGS_PANEL_BORDER, toggle_rect, 1, border_radius=16)

        knob_x = toggle_rect.x + 6 if not state else toggle_rect.right - toggle_height + 6
        knob_rect = pygame.Rect(knob_x, toggle_rect.y + 4, toggle_height - 8, toggle_height - 8)
        pygame.draw.ellipse(screen, (255, 255, 255), knob_rect)

        label = "ON" if state else "OFF"
        draw_text(screen, label, 16, TEXT if state else (90, 96, 92), toggle_rect.centerx, toggle_rect.centery, center=True)

    return panel_rect, pygame.Rect(toggle_x, toggle_y1, toggle_width, toggle_height), pygame.Rect(toggle_x, toggle_y2, toggle_width, toggle_height)


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
    if font.size(text)[0] <= max_width:
        return text

    # cắt trực tiếp, không thêm ...
    for i in range(len(text), 0, -1):
        if font.size(text[:i])[0] <= max_width:
            return text[:i]

    return ""


def draw_side_panels(screen, board_obj):
    left_x = LEFT_MARGIN
    right_x = BOARD_X + BOARD_SIZE + GAP

    panel_y = BOARD_Y
    panel_h = BOARD_SIZE

    pygame.draw.rect(screen, PANEL, (left_x, panel_y, PANEL_W, panel_h), border_radius=16)
    pygame.draw.rect(screen, PANEL, (right_x, panel_y, PANEL_W, panel_h), border_radius=16)

    draw_text(screen, "Lịch sử nước đi", 20, ACCENT, left_x + PANEL_W // 2, panel_y + 24, center=True)
    draw_text(screen, "Quân bị ăn", 20, ACCENT, right_x + PANEL_W // 2, panel_y + 24, center=True)

    # ===== MOVE HISTORY (2 LINE / TURN - BALANCED) =====

    history_start_y = panel_y + 52
    history_entries = []

    # --- Build history data (KHÔNG ĐỔI LOGIC) ---
    start_index = max(0, len(board_obj.move_log) - 10)
    if start_index % 2 == 1:
        start_index -= 1

    for idx in range(start_index, len(board_obj.move_log), 2):
        white_move_obj = board_obj.move_log[idx]
        white_move = format_move_notation(white_move_obj)
        white_piece = white_move_obj["moving_piece"]

        black_move = ""
        black_piece = None

        if idx + 1 < len(board_obj.move_log):
            black_move_obj = board_obj.move_log[idx + 1]
            black_move = format_move_notation(black_move_obj)
            black_piece = black_move_obj["moving_piece"]

        move_number = idx // 2 + 1
        history_entries.append((move_number, white_piece, white_move, black_piece, black_move))


    # --- Render UI (KHÔNG PHÁ LAYOUT) ---
    font = get_font(15)
    icon_size = 20
    icon_text_gap = 5

    entry_height = 24
    turn_gap = 6

    number_offset = 26
    content_offset = 40

    for i, (move_number, white_piece, white_move, black_piece, black_move) in enumerate(history_entries[-5:]):
        base_y = history_start_y + i * (entry_height * 2 + turn_gap)

        # ===== WHITE =====
        y1 = base_y
        text_y1 = y1 + (entry_height - font.get_height()) // 2
        icon_y1 = y1 + (entry_height - icon_size) // 2

        number_x = left_x + 14
        draw_text(screen, f"{move_number}.", 15, HISTORY_TEXT, number_x, text_y1)

        white_x = number_x + content_offset

        max_width = PANEL_W - content_offset - 20
        white_move = truncate_text(white_move, font, max_width)

        white_icon = history_piece_images.get(white_piece)
        if white_icon:
            screen.blit(white_icon, (white_x, icon_y1))

        draw_text(
            screen,
            white_move,
            15,
            HISTORY_TEXT,
            white_x + icon_size + icon_text_gap,
            text_y1
        )

        # ===== BLACK =====
        if black_piece and black_move:
            y2 = base_y + entry_height
            text_y2 = y2 + (entry_height - font.get_height()) // 2
            icon_y2 = y2 + (entry_height - icon_size) // 2

            black_x = white_x  # 👉 cân bằng tuyệt đối

            max_width = PANEL_W - content_offset - 20
            black_move = truncate_text(black_move, font, max_width)

            black_icon = history_piece_images.get(black_piece)
            if black_icon:
                screen.blit(black_icon, (black_x, icon_y2))

            draw_text(
                screen,
                black_move,
                15,
                HISTORY_TEXT,
                black_x + icon_size + icon_text_gap,
                text_y2
            )
    # Improved captured pieces panel with two equal sections
    header_height = 52  # Space for "Quân bị ăn" header
    section_height = (panel_h - header_height) // 2  # Two equal sections below header
    padding = 12
    title_font = get_font(18)
    icon_size = 30
    gap_icon = 8
    cols = 4
    
    # Calculate centered x position for grid
    total_grid_width = cols * icon_size + (cols - 1) * gap_icon  # 144px
    usable_width = PANEL_W - 2 * padding  # 156px
    grid_start_offset = (usable_width - total_grid_width) // 2  # 6px
    grid_x = right_x + padding + grid_start_offset
    
    # White captured pieces (top section)
    white_section_y = panel_y + header_height
    white_title_y = white_section_y + padding + 4
    white_content_y = white_section_y + padding + 32
    
    draw_text(screen, "Trắng", 18, TEXT, right_x + PANEL_W // 2, white_title_y, center=True)
    
    # Render white captured pieces with overflow handling
    white_pieces = board_obj.captured_white
    last_rendered_index = -1
    
    for i, piece in enumerate(white_pieces):
        row = i // cols
        col = i % cols
        x = grid_x + col * (icon_size + gap_icon)
        y = white_content_y + row * (icon_size + gap_icon)
        
        # Check if this row exceeds section bounds
        if y + icon_size > white_section_y + section_height - padding:
            break
        
        small = captured_piece_images[piece]
        screen.blit(small, (x, y))
        last_rendered_index = i
    
    # Show overflow count if there are more pieces AND at least 1 piece was rendered
    if last_rendered_index >= 0 and last_rendered_index < len(white_pieces) - 1:
        remaining = len(white_pieces) - last_rendered_index - 1
        overflow_text = f"+{remaining}"
        row = (last_rendered_index + 1) // cols
        col = (last_rendered_index + 1) % cols
        x = grid_x + col * (icon_size + gap_icon)
        y = white_content_y + row * (icon_size + gap_icon)
        
        # Draw semi-transparent background for overflow indicator
        overflow_bg = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        pygame.draw.rect(overflow_bg, (150, 168, 136, 180), overflow_bg.get_rect(), border_radius=4)
        screen.blit(overflow_bg, (x, y))
        
        # Draw overflow text
        draw_text(screen, overflow_text, 18, (255, 255, 255), x + icon_size // 2, y + icon_size // 2, center=True)
    
    # Divider line between sections
    divider_y = panel_y + header_height + section_height
    pygame.draw.line(screen, (200, 210, 200), (right_x + 12, divider_y), (right_x + PANEL_W - 12, divider_y), 1)
    
    # Black captured pieces (bottom section)
    black_section_y = panel_y + header_height + section_height
    black_title_y = black_section_y + padding + 4
    black_content_y = black_section_y + padding + 32
    
    draw_text(screen, "Đen", 18, TEXT, right_x + PANEL_W // 2, black_title_y, center=True)
    
    # Render black captured pieces with overflow handling
    black_pieces = board_obj.captured_black
    last_rendered_index = -1
    
    for i, piece in enumerate(black_pieces):
        row = i // cols
        col = i % cols
        x = grid_x + col * (icon_size + gap_icon)
        y = black_content_y + row * (icon_size + gap_icon)
        
        # Check if this row exceeds section bounds
        if y + icon_size > black_section_y + section_height - padding:
            break
        
        small = captured_piece_images[piece]
        screen.blit(small, (x, y))
        last_rendered_index = i
    
    # Show overflow count if there are more pieces AND at least 1 piece was rendered
    if last_rendered_index >= 0 and last_rendered_index < len(black_pieces) - 1:
        remaining = len(black_pieces) - last_rendered_index - 1
        overflow_text = f"+{remaining}"
        row = (last_rendered_index + 1) // cols
        col = (last_rendered_index + 1) % cols
        x = grid_x + col * (icon_size + gap_icon)
        y = black_content_y + row * (icon_size + gap_icon)
        
        # Draw semi-transparent background for overflow indicator
        overflow_bg = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        pygame.draw.rect(overflow_bg, (150, 168, 136, 180), overflow_bg.get_rect(), border_radius=4)
        screen.blit(overflow_bg, (x, y))
        
        # Draw overflow text
        draw_text(screen, overflow_text, 18, (255, 255, 255), x + icon_size // 2, y + icon_size // 2, center=True)


def draw_top_bar(screen, white_to_move, turn_time, total_game_time, ai_level=None):
    top_rect = pygame.Rect(BOARD_X, MARGIN, BOARD_SIZE, TOP_BAR_HEIGHT)
    pygame.draw.rect(screen, PANEL, top_rect, border_radius=18)
    pygame.draw.rect(screen, (255, 255, 255, 120), top_rect, 1, border_radius=18)

    draw_text(
        screen,
        f"Tổng thời gian: {format_time(total_game_time)}",
        18,
        ACCENT,
        top_rect.centerx,
        top_rect.y + 28,
        center=True
    )

    white_display = turn_time if white_to_move else 600
    black_display = turn_time if not white_to_move else 600

    white_bg = pygame.Rect(int(top_rect.x + 20), top_rect.y + 40, 170, 28)
    black_bg = pygame.Rect(int(top_rect.right - 20 - 170), top_rect.y + 40, 170, 28)

    pygame.draw.rect(screen, (255, 255, 255), white_bg, border_radius=14)
    pygame.draw.rect(screen, (255, 255, 255), black_bg, border_radius=14)
    pygame.draw.rect(screen, (210, 222, 201), white_bg, 1, border_radius=14)
    pygame.draw.rect(screen, (210, 222, 201), black_bg, 1, border_radius=14)

    draw_text(
        screen,
        f"Trắng: {format_time(white_display)}",
        20,
        TEXT,
        white_bg.centerx,
        white_bg.centery,
        center=True
    )

    draw_text(
        screen,
        f"Đen: {format_time(black_display)}",
        20,
        TEXT,
        black_bg.centerx,
        black_bg.centery,
        center=True
    )

    if ai_level is not None:
        level_names = {"easy": "Dễ", "normal": "Bình thường", "hard": "Khó"}
        level_text = level_names.get(ai_level, ai_level.title())
        level_surface = get_font(16).render(f"Độ khó: {level_text}", True, TEXT)
        level_rect = level_surface.get_rect(topright=(top_rect.right - 12, top_rect.y + 14))
        screen.blit(level_surface, level_rect)

    right_x = BOARD_X + BOARD_SIZE + GAP
    button_w = 78
    button_h = 46

    reset_rect = pygame.Rect(right_x, MARGIN, button_w, button_h)
    home_rect = pygame.Rect(right_x + PANEL_W - button_w, MARGIN, button_w, button_h)

    mouse_pos = pygame.mouse.get_pos()
    draw_icon_button(screen, reset_rect, "reset", WHITE_BTN, reset_rect.collidepoint(mouse_pos))
    draw_icon_button(screen, home_rect, "home", DARK_BTN, home_rect.collidepoint(mouse_pos))

    return reset_rect, home_rect


def draw_end_popup(screen, winner):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    popup_w = 420
    popup_h = 260
    popup_rect = pygame.Rect((WIDTH - popup_w) // 2, (HEIGHT - popup_h) // 2, popup_w, popup_h)

    pygame.draw.rect(screen, POPUP_BG, popup_rect, border_radius=20)
    pygame.draw.rect(screen, POPUP_BORDER, popup_rect, 2, border_radius=20)

    center_x = popup_rect.centerx

    if winner == "Hòa":
        draw_text(screen, "Draw", 36, TEXT, center_x, popup_rect.y + 80, center=True)
        draw_text(screen, "Game drawn", 22, TEXT, center_x, popup_rect.y + 130, center=True)
    else:
        draw_text(screen, "Checkmate", 38, TEXT, center_x, popup_rect.y + 72, center=True)
        result_text = "White wins" if winner == "Trắng" else "Black wins"
        draw_text(screen, result_text, 26, TEXT, center_x, popup_rect.y + 130, center=True)

    button_w = 150
    button_h = 46
    spacing = 20
    start_x = popup_rect.centerx - (button_w * 2 + spacing) // 2

    replay_rect = pygame.Rect(start_x, popup_rect.y + 180, button_w, button_h)
    home_rect = pygame.Rect(start_x + button_w + spacing, popup_rect.y + 180, button_w, button_h)

    mouse_pos = pygame.mouse.get_pos()
    draw_icon_button(screen, replay_rect, "reset", WHITE_BTN, replay_rect.collidepoint(mouse_pos))
    draw_icon_button(screen, home_rect, "home", DARK_BTN, home_rect.collidepoint(mouse_pos))

    return replay_rect, home_rect


def draw_bottom_bar(screen, message):
    rect = pygame.Rect(
        BOARD_X,
        BOARD_Y + BOARD_SIZE + GAP,
        BOARD_SIZE,
        BOTTOM_BAR_HEIGHT
    )

    pygame.draw.rect(screen, (248, 249, 244), rect, border_radius=16)
    pygame.draw.rect(screen, (214, 225, 199), rect, 1, border_radius=16)

    # Improved text alignment with proper spacing
    font = get_font(26)
    text_surface = font.render(message, True, TEXT)
    text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery))
    screen.blit(text_surface, text_rect)


def get_square_from_mouse(pos):
    mx, my = pos
    if BOARD_X <= mx < BOARD_X + BOARD_SIZE and BOARD_Y <= my < BOARD_Y + BOARD_SIZE:
        col = (mx - BOARD_X) // SQ_SIZE
        row = (my - BOARD_Y) // SQ_SIZE
        return row, col
    return None


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


def format_time(t):
    t = max(0, int(t))
    minutes = t // 60
    seconds = t % 60
    return f"{minutes:02}:{seconds:02}"


def run_pvp(screen):
    clock = pygame.time.Clock()
    board_obj = Board()
    load_images()
    load_sounds()

    turn_time = 600
    total_game_time = 0
    last_tick = pygame.time.get_ticks()

    valid_moves = []
    message = "Chọn quân để bắt đầu"
    winner = None
    check_king_pos = None
    animation = create_animation_state()
    settings_open = False
    settings_button_rect = pygame.Rect(SETTINGS_MARGIN, SETTINGS_MARGIN, SETTINGS_BUTTON_SIZE, SETTINGS_BUTTON_SIZE)
    click_toggle_rect = None
    piece_toggle_rect = None

    while True:
        draw_background_gradient(screen)
        current_color = "w" if board_obj.white_to_move else "b"
        current_name = "Trắng" if current_color == "w" else "Đen"

        now = pygame.time.get_ticks()
        delta = (now - last_tick) / 1000
        last_tick = now

        if winner is None and not animation["active"]:
            total_game_time += delta
            turn_time -= delta

        if animation["active"]:
            finished, turn_time, new_winner, new_message, new_check_king_pos = update_animation(
                board_obj, animation, turn_time
            )
            if finished:
                winner = new_winner
                message = new_message
                check_king_pos = new_check_king_pos
                valid_moves = []

        if winner is None and not animation["active"] and turn_time <= 0:
            turn_time = 600
            board_obj.white_to_move = not board_obj.white_to_move
            board_obj.selected_square = None
            valid_moves = []
            check_king_pos = None

            current_name = "Trắng" if board_obj.white_to_move else "Đen"
            message = f"Hết thời gian suy nghĩ, chuyển lượt sang {current_name}"

        if winner is None and not animation["active"]:
            current_color = "w" if board_obj.white_to_move else "b"
            current_name = "Trắng" if current_color == "w" else "Đen"

            if is_in_check(board_obj, current_color):
                check_king_pos = find_king(board_obj, current_color)

                if not has_any_legal_move(board_obj, current_color):
                    winner = "Đen" if current_color == "w" else "Trắng"
                    message = f"CHIẾU BÍ! {winner} thắng"
                else:
                    message = f"{current_name} đang bị chiếu!"
            else:
                check_king_pos = None

                if not has_any_legal_move(board_obj, current_color):
                    winner = "Hòa"
                    message = "HẾT NƯỚC ĐI! Kết quả hòa"
                else:
                    if board_obj.selected_square is None:
                        message = f"Lượt: {current_name}"

        reset_rect, home_rect = draw_top_bar(screen, board_obj.white_to_move, turn_time, total_game_time)
        popup_reset_rect = None
        popup_home_rect = None

        hover_square = get_square_from_mouse(pygame.mouse.get_pos())

        draw_settings_button(
            screen,
            settings_button_rect,
            settings_button_rect.collidepoint(pygame.mouse.get_pos()),
            settings_button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]
        )

        draw_side_panels(screen, board_obj)
        draw_board(screen, board_obj, valid_moves, check_king_pos, animation, hover_square)
        draw_bottom_bar(screen, message)

        panel_rect = None
        if settings_open:
            panel_rect, click_toggle_rect, piece_toggle_rect = draw_settings_panel(
                screen,
                click_sound_enabled,
                piece_sound_enabled,
            )

        if winner is not None:
            popup_reset_rect, popup_home_rect = draw_end_popup(screen, winner)

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                play_click_sound()
                pos = pygame.mouse.get_pos()

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
                    
                    # Only close if clicked outside panel (not on toggles)
                    if not panel_clicked and not toggle_clicked:
                        settings_open = False
                    continue

                if winner is not None:
                    if popup_reset_rect and click_button(
                        pos,
                        popup_reset_rect.x,
                        popup_reset_rect.y,
                        popup_reset_rect.width,
                        popup_reset_rect.height
                    ):
                        state = reset_game_state(board_obj)
                        valid_moves = state["valid_moves"]
                        message = state["message"]
                        winner = state["winner"]
                        check_king_pos = state["check_king_pos"]
                        turn_time = state["turn_time"]
                        total_game_time = state["total_game_time"]
                        last_tick = state["last_tick"]
                        clear_animation(animation)
                        continue

                    if popup_home_rect and click_button(
                        pos,
                        popup_home_rect.x,
                        popup_home_rect.y,
                        popup_home_rect.width,
                        popup_home_rect.height
                    ):
                        return "menu"

                    continue

                if animation["active"]:
                    continue

                if click_button(pos, reset_rect.x, reset_rect.y, reset_rect.width, reset_rect.height):
                    state = reset_game_state(board_obj)
                    valid_moves = state["valid_moves"]
                    message = state["message"]
                    winner = state["winner"]
                    check_king_pos = state["check_king_pos"]
                    turn_time = state["turn_time"]
                    total_game_time = state["total_game_time"]
                    last_tick = state["last_tick"]
                    clear_animation(animation)
                    continue

                if click_button(pos, home_rect.x, home_rect.y, home_rect.width, home_rect.height):
                    return "menu"

                square = get_square_from_mouse(pos)
                if square is None:
                    continue

                row, col = square
                piece = board_obj.get_piece(row, col)

                if board_obj.selected_square is None:
                    if piece == "--":
                        message = "Ô này đang trống"
                        continue

                    if board_obj.white_to_move and piece[0] != "w":
                        message = "Đang tới lượt Trắng"
                        continue

                    if (not board_obj.white_to_move) and piece[0] != "b":
                        message = "Đang tới lượt Đen"
                        continue

                    board_obj.selected_square = (row, col)
                    valid_moves = get_legal_moves(board_obj, row, col)

                    if len(valid_moves) == 0:
                        message = "Không thể đi được quân này"
                    else:
                        message = f"Đã chọn {piece_name(piece)}"

                    continue

                start = board_obj.selected_square

                if piece != "--":
                    selected_piece = board_obj.get_piece(start[0], start[1])
                    if piece[0] == selected_piece[0]:
                        board_obj.selected_square = (row, col)
                        valid_moves = get_legal_moves(board_obj, row, col)
                        message = f"Đổi chọn sang {piece_name(piece)}"
                        continue

                if (row, col) in valid_moves:
                    start_animation(animation, board_obj, start, (row, col))
                    board_obj.selected_square = None
                    valid_moves = []
                    message = f"{piece_name(animation['piece'])} đang di chuyển..."
                else:
                    board_obj.selected_square = None
                    valid_moves = []
                    message = "Nước đi không hợp lệ"


def run_pve(screen, ai_level="normal"):
    clock = pygame.time.Clock()
    board_obj = Board()
    load_images()
    load_sounds()

    turn_time = 600
    total_game_time = 0
    last_tick = pygame.time.get_ticks()

    valid_moves = []
    message = "Chọn quân để bắt đầu"
    winner = None
    check_king_pos = None

    human_color = "w"
    ai_color = "b"

    animation = create_animation_state()
    settings_open = False
    settings_button_rect = pygame.Rect(SETTINGS_MARGIN, SETTINGS_MARGIN, SETTINGS_BUTTON_SIZE, SETTINGS_BUTTON_SIZE)
    click_toggle_rect = None
    piece_toggle_rect = None

    ai_turn_started_at = None
    ai_thinking = False
    ai_move_result = {"move": None}
    ai_lock = threading.Lock()
    ai_task_id = {"current": 0}

    def ai_worker(board_snapshot, level, task_id):
        start_time = time.time()
        move = find_best_move(board_snapshot, level)
        elapsed = time.time() - start_time
        min_delay = {"easy": 0.3, "normal": 0.4, "hard": 0.5}.get(level, 0.4)
        if elapsed < min_delay:
            time.sleep(min_delay - elapsed)
        with ai_lock:
            if task_id != ai_task_id["current"]:
                return
            ai_move_result["move"] = move

    while True:
        draw_background_gradient(screen)
        current_color = "w" if board_obj.white_to_move else "b"
        current_name = "Trắng" if current_color == "w" else "Đen"

        now = pygame.time.get_ticks()
        delta = (now - last_tick) / 1000
        last_tick = now

        if winner is None and not animation["active"]:
            total_game_time += delta
            turn_time -= delta

        if animation["active"]:
            finished, turn_time, new_winner, new_message, new_check_king_pos = update_animation(
                board_obj, animation, turn_time
            )
            if finished:
                winner = new_winner
                message = new_message
                check_king_pos = new_check_king_pos
                valid_moves = []
                ai_turn_started_at = None

        current_color = "w" if board_obj.white_to_move else "b"
        current_name = "Trắng" if current_color == "w" else "Đen"

        if winner is None and not animation["active"]:
            if turn_time <= 0:
                if current_color == ai_color:
                    winner = "Trắng" if ai_color == "b" else "Đen"
                    message = f"Hết thời gian! {winner} thắng"
                    ai_thinking = False
                    ai_turn_started_at = None
                else:
                    winner = "Đen" if human_color == "w" else "Trắng"
                    message = f"Hết thời gian! {winner} thắng"
                    ai_thinking = False
                    ai_turn_started_at = None

        if winner is None and not animation["active"]:
            current_color = "w" if board_obj.white_to_move else "b"
            current_name = "Trắng" if current_color == "w" else "Đen"

            if is_in_check(board_obj, current_color):
                check_king_pos = find_king(board_obj, current_color)

                if not has_any_legal_move(board_obj, current_color):
                    winner = "Đen" if current_color == "w" else "Trắng"
                    message = f"CHIẾU BÍ! {winner} thắng"
                else:
                    if current_color == ai_color and ai_thinking:
                        message = "Máy đang suy nghĩ..."
                    else:
                        message = f"{current_name} đang bị chiếu!"
            else:
                check_king_pos = None

                if not has_any_legal_move(board_obj, current_color):
                    winner = "Hòa"
                    message = "HẾT NƯỚC ĐI! Kết quả hòa"
                elif current_color == ai_color:
                    if ai_thinking:
                        message = "Máy đang suy nghĩ..."
                    else:
                        message = "Máy chuẩn bị suy nghĩ..."
                else:
                    ai_turn_started_at = None
                    if board_obj.selected_square is None:
                        message = f"Lượt: {current_name}"

        if winner is None and not animation["active"] and current_color == ai_color:
            if not ai_thinking:
                if ai_turn_started_at is None:
                    ai_turn_started_at = pygame.time.get_ticks()

                if pygame.time.get_ticks() - ai_turn_started_at >= AI_MOVE_DELAY:
                    ai_thinking = True
                    with ai_lock:
                        ai_task_id["current"] += 1
                        current_task_id = ai_task_id["current"]
                        ai_move_result["move"] = None
                    board_snapshot = copy.deepcopy(board_obj)
                    threading.Thread(
                        target=ai_worker,
                        args=(board_snapshot, ai_level, current_task_id),
                        daemon=True
                    ).start()
            else:
                move = None
                with ai_lock:
                    move = ai_move_result["move"]

                if move is not None:
                    ai_thinking = False
                    with ai_lock:
                        ai_move_result["move"] = None

                    start_animation(animation, board_obj, move[0], move[1])
                    board_obj.selected_square = None
                    valid_moves = []
                    message = "Máy đang di chuyển..."
                    ai_turn_started_at = None

        reset_rect, home_rect = draw_top_bar(screen, board_obj.white_to_move, turn_time, total_game_time, ai_level)
        popup_reset_rect = None
        popup_home_rect = None

        hover_square = get_square_from_mouse(pygame.mouse.get_pos())

        draw_settings_button(
            screen,
            settings_button_rect,
            settings_button_rect.collidepoint(pygame.mouse.get_pos()),
            settings_button_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]
        )

        draw_side_panels(screen, board_obj)
        draw_board(screen, board_obj, valid_moves, check_king_pos, animation, hover_square)
        draw_bottom_bar(screen, message)

        panel_rect = None
        if settings_open:
            panel_rect, click_toggle_rect, piece_toggle_rect = draw_settings_panel(
                screen,
                click_sound_enabled,
                piece_sound_enabled,
            )

        if winner is not None:
            popup_reset_rect, popup_home_rect = draw_end_popup(screen, winner)

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                play_click_sound()
                pos = pygame.mouse.get_pos()

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
                    
                    # Only close if clicked outside panel (not on toggles)
                    if not panel_clicked and not toggle_clicked:
                        settings_open = False
                    continue

                if winner is not None:
                    if popup_reset_rect and click_button(
                        pos,
                        popup_reset_rect.x,
                        popup_reset_rect.y,
                        popup_reset_rect.width,
                        popup_reset_rect.height
                    ):
                        state = reset_game_state(board_obj)
                        valid_moves = state["valid_moves"]
                        message = state["message"]
                        winner = state["winner"]
                        check_king_pos = state["check_king_pos"]
                        turn_time = state["turn_time"]
                        total_game_time = state["total_game_time"]
                        last_tick = state["last_tick"]
                        clear_animation(animation)
                        ai_turn_started_at = None
                        ai_thinking = False
                        with ai_lock:
                            ai_task_id["current"] += 1
                            ai_move_result["move"] = None
                        continue

                    if popup_home_rect and click_button(
                        pos,
                        popup_home_rect.x,
                        popup_home_rect.y,
                        popup_home_rect.width,
                        popup_home_rect.height
                    ):
                        return "menu"
                    continue

                if click_button(pos, reset_rect.x, reset_rect.y, reset_rect.width, reset_rect.height):
                    state = reset_game_state(board_obj)
                    valid_moves = state["valid_moves"]
                    message = state["message"]
                    winner = state["winner"]
                    check_king_pos = state["check_king_pos"]
                    turn_time = state["turn_time"]
                    total_game_time = state["total_game_time"]
                    last_tick = state["last_tick"]
                    clear_animation(animation)
                    ai_turn_started_at = None
                    ai_thinking = False
                    with ai_lock:
                        ai_task_id["current"] += 1
                        ai_move_result["move"] = None
                    continue

                if click_button(pos, home_rect.x, home_rect.y, home_rect.width, home_rect.height):
                    return "menu"

                if animation["active"]:
                    continue

                if ai_thinking:
                    continue

                if ("w" if board_obj.white_to_move else "b") != human_color:
                    continue

                square = get_square_from_mouse(pos)
                if square is None:
                    continue

                row, col = square
                piece = board_obj.get_piece(row, col)

                if board_obj.selected_square is None:
                    if piece == "--":
                        message = "Ô này đang trống"
                        continue
                    if piece[0] != human_color:
                        message = "Đang tới lượt của bạn"
                        continue

                    board_obj.selected_square = (row, col)
                    valid_moves = get_legal_moves(board_obj, row, col)
                    if len(valid_moves) == 0:
                        message = "Quân này không có nước đi hợp lệ"
                    else:
                        message = f"Đã chọn {piece_name(piece)}"
                    continue

                start = board_obj.selected_square

                if piece != "--":
                    selected_piece = board_obj.get_piece(start[0], start[1])
                    if piece[0] == selected_piece[0]:
                        board_obj.selected_square = (row, col)
                        valid_moves = get_legal_moves(board_obj, row, col)
                        message = f"Đổi chọn sang {piece_name(piece)}"
                        continue

                if (row, col) in valid_moves:
                    start_animation(animation, board_obj, start, (row, col))
                    turn_time = 600
                    board_obj.selected_square = None
                    valid_moves = []
                    message = f"{piece_name(animation['piece'])} đang di chuyển..."
                    ai_turn_started_at = None
                else:
                    board_obj.selected_square = None
                    valid_moves = []
                    message = "Nước đi không hợp lệ"