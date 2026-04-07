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

BOARD_X = LEFT_MARGIN + PANEL_W + GAP
BOARD_Y = MARGIN + TOP_BAR_HEIGHT + GAP

LIGHT = (255, 248, 220)  # Cream color for light squares
DARK = (139, 69, 19)    # Saddle brown for dark squares
SELECT_COLOR = (255, 215, 0)  # Gold for selection
MOVE_HINT = (50, 205, 50)     # Lime green for move hints
BG = (245, 245, 245)          # Light gray background
TEXT = (30, 30, 30)           # Dark gray text
PANEL = (220, 220, 220)       # Light panel color

# Hover colors
LIGHT_HOVER = (255, 255, 200)  # Light yellow for hover
DARK_HOVER = (160, 82, 45)     # Lighter brown for hover

# Shadow color
SHADOW_COLOR = (0, 0, 0, 50)  # Semi-transparent black

POPUP_BG = (245, 240, 230)
POPUP_BORDER = (120, 95, 70)

WHITE_BTN = (236, 228, 213)
WHITE_BTN_HOVER = (246, 238, 223)

DARK_BTN = (92, 64, 51)
DARK_BTN_HOVER = (112, 79, 63)

WHITE_TEXT = (40, 40, 40)
DARK_TEXT = (245, 245, 245)

OVERLAY = (0, 0, 0, 90)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, "assets", "font", "Roboto-Regular.ttf")

ui_icons = {}
piece_images = {}
font_cache = {}
sound_effects = {}
sound_channels = {}

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

    for p in pieces:
        img_path = os.path.join(BASE_DIR, "assets", "images", f"{p}.png")
        img = pygame.image.load(img_path).convert_alpha()
        piece_images[p] = pygame.transform.smoothscale(img, (SQ_SIZE, SQ_SIZE))

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

    channel.stop()
    channel.play(sound)


def play_move_sound():
    play_sound("move")


def play_capture_sound():
    play_sound("capture")


def play_click_sound():
    play_sound("click")


def draw_text(screen, text, size, color, x, y, center=False):
    font = get_font(size)
    surface = font.render(text, True, color)
    rect = surface.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    screen.blit(surface, rect)


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def draw_board(screen, board_obj, valid_moves, check_king_pos=None, animation=None, hover_square=None):
    anim_start = None
    anim_end = None

    if animation and animation["active"]:
        anim_start = animation["start"]
        anim_end = animation["end"]

    for row in range(8):
        for col in range(8):
            base_color = LIGHT if (row + col) % 2 == 0 else DARK
            color = base_color

            # Hover effect
            if hover_square == (row, col):
                color = LIGHT_HOVER if (row + col) % 2 == 0 else DARK_HOVER

            rect = pygame.Rect(BOARD_X + col * SQ_SIZE, BOARD_Y + row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            pygame.draw.rect(screen, color, rect)

            # Draw shadow for pieces
            piece = board_obj.board[row][col]
            if piece != "--" and not (animation and animation["active"] and (row, col) == anim_start):
                shadow_rect = pygame.Rect(BOARD_X + col * SQ_SIZE + 2, BOARD_Y + row * SQ_SIZE + 2, SQ_SIZE, SQ_SIZE)
                shadow_surface = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
                shadow_surface.fill(SHADOW_COLOR)
                screen.blit(shadow_surface, shadow_rect)

            if check_king_pos == (row, col):
                s = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
                s.fill((255, 0, 0, 100))
                screen.blit(s, (BOARD_X + col * SQ_SIZE, BOARD_Y + row * SQ_SIZE))

            if board_obj.selected_square == (row, col):
                # Glow effect for selection
                glow_surface = pygame.Surface((SQ_SIZE + 8, SQ_SIZE + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (255, 215, 0, 150), glow_surface.get_rect(), border_radius=4)
                screen.blit(glow_surface, (BOARD_X + col * SQ_SIZE - 4, BOARD_Y + row * SQ_SIZE - 4))
                pygame.draw.rect(screen, SELECT_COLOR, rect, 3)

    for (r, c) in valid_moves:
        rect = pygame.Rect(BOARD_X + c * SQ_SIZE, BOARD_Y + r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        target_piece = board_obj.board[r][c]

        if target_piece != "--":
            # Red glow for captures
            glow_surface = pygame.Surface((SQ_SIZE + 8, SQ_SIZE + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (255, 0, 0, 150), glow_surface.get_rect(), border_radius=4)
            screen.blit(glow_surface, (BOARD_X + c * SQ_SIZE - 4, BOARD_Y + r * SQ_SIZE - 4))
            pygame.draw.rect(screen, (220, 50, 50), rect, 4)
        else:
            center_x = BOARD_X + c * SQ_SIZE + SQ_SIZE // 2
            center_y = BOARD_Y + r * SQ_SIZE + SQ_SIZE // 2
            pygame.draw.circle(screen, MOVE_HINT, (center_x, center_y), 12)
            pygame.draw.circle(screen, (255, 255, 255), (center_x, center_y), 6)

    for row in range(8):
        for col in range(8):
            piece = board_obj.board[row][col]
            if piece == "--":
                continue

            if animation and animation["active"] and (row, col) == anim_start:
                continue

            if animation and animation["active"] and animation["captured_piece"] != "--" and (row, col) == anim_end:
                continue

            # Draw shadow
            shadow_rect = pygame.Rect(BOARD_X + col * SQ_SIZE + 2, BOARD_Y + row * SQ_SIZE + 2, SQ_SIZE, SQ_SIZE)
            shadow_surface = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
            shadow_surface.fill(SHADOW_COLOR)
            screen.blit(shadow_surface, shadow_rect)

            screen.blit(piece_images[piece], (BOARD_X + col * SQ_SIZE, BOARD_Y + row * SQ_SIZE))

    if animation and animation["active"] and animation["piece"]:
        start_x = BOARD_X + anim_start[1] * SQ_SIZE
        start_y = BOARD_Y + anim_start[0] * SQ_SIZE
        end_x = BOARD_X + anim_end[1] * SQ_SIZE
        end_y = BOARD_Y + anim_end[0] * SQ_SIZE

        p = ease_in_out(animation["progress"])
        current_x = start_x + (end_x - start_x) * p
        current_y = start_y + (end_y - start_y) * p

        # Draw shadow for animated piece
        shadow_surface = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
        shadow_surface.fill(SHADOW_COLOR)
        screen.blit(shadow_surface, (current_x + 2, current_y + 2))

        screen.blit(piece_images[animation["piece"]], (current_x, current_y))

        # Capture effect: fade out captured piece
        if animation["captured_piece"] != "--":
            captured_alpha = int(255 * (1 - p))
            captured_img = piece_images[animation["captured_piece"]].copy()
            captured_img.set_alpha(captured_alpha)
            scale_factor = 1 + 0.2 * p  # Slight scale up
            scaled_size = int(SQ_SIZE * scale_factor)
            scaled_img = pygame.transform.smoothscale(captured_img, (scaled_size, scaled_size))
            offset = (scaled_size - SQ_SIZE) // 2
            screen.blit(scaled_img, (end_x - offset, end_y - offset))


def draw_icon_button(screen, rect, icon_key, bg_color, hover=False):
    if hover:
        color = WHITE_BTN_HOVER if bg_color == WHITE_BTN else DARK_BTN_HOVER
    else:
        color = bg_color

    pygame.draw.rect(screen, color, rect, border_radius=10)

    icon = ui_icons[icon_key]
    icon_rect = icon.get_rect(center=rect.center)
    screen.blit(icon, icon_rect)


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


def draw_side_panels(screen, board_obj):
    left_x = LEFT_MARGIN
    right_x = BOARD_X + BOARD_SIZE + GAP

    panel_y = BOARD_Y
    panel_h = BOARD_SIZE

    pygame.draw.rect(screen, PANEL, (left_x, panel_y, PANEL_W, panel_h), border_radius=12)
    draw_text(screen, "Quân trắng", 24, TEXT, left_x + PANEL_W // 2, panel_y + 30, center=True)
    draw_text(screen, "bị ăn", 24, TEXT, left_x + PANEL_W // 2, panel_y + 60, center=True)

    pygame.draw.rect(screen, PANEL, (right_x, panel_y, PANEL_W, panel_h), border_radius=12)
    draw_text(screen, "Quân đen", 24, TEXT, right_x + PANEL_W // 2, panel_y + 30, center=True)
    draw_text(screen, "bị ăn", 24, TEXT, right_x + PANEL_W // 2, panel_y + 60, center=True)

    icon_size = 32
    gap_icon = 8
    cols = 4
    start_y = panel_y + 95

    for i, piece in enumerate(board_obj.captured_white):
        row = i // cols
        col = i % cols
        x = left_x + 10 + col * (icon_size + gap_icon)
        y = start_y + row * (icon_size + gap_icon)

        if y + icon_size > panel_y + panel_h - 10:
            break

        small = pygame.transform.smoothscale(piece_images[piece], (icon_size, icon_size))
        screen.blit(small, (x, y))

    for i, piece in enumerate(board_obj.captured_black):
        row = i // cols
        col = i % cols
        x = right_x + 10 + col * (icon_size + gap_icon)
        y = start_y + row * (icon_size + gap_icon)

        if y + icon_size > panel_y + panel_h - 10:
            break

        small = pygame.transform.smoothscale(piece_images[piece], (icon_size, icon_size))
        screen.blit(small, (x, y))


def draw_top_bar(screen, white_to_move, turn_time, total_game_time, ai_level=None):
    top_rect = pygame.Rect(BOARD_X, MARGIN, BOARD_SIZE, TOP_BAR_HEIGHT)
    pygame.draw.rect(screen, PANEL, top_rect, border_radius=12)

    draw_text(
        screen,
        f"Tổng thời gian: {format_time(total_game_time)}",
        20,
        TEXT,
        top_rect.centerx,
        top_rect.y + 18,
        center=True
    )

    white_display = turn_time if white_to_move else 600
    black_display = turn_time if not white_to_move else 600

    draw_text(
        screen,
        f"Trắng: {format_time(white_display)}",
        28,
        TEXT,
        int(top_rect.x + top_rect.width * 0.25),
        top_rect.y + 48,
        center=True
    )

    draw_text(
        screen,
        f"Đen: {format_time(black_display)}",
        28,
        TEXT,
        int(top_rect.x + top_rect.width * 0.75),
        top_rect.y + 48,
        center=True
    )

    if ai_level is not None:
        level_names = {"easy": "Dễ", "normal": "Bình thường", "hard": "Khó"}
        level_text = level_names.get(ai_level, ai_level.title())
        level_surface = get_font(18).render(f"Độ khó: {level_text}", True, TEXT)
        level_rect = level_surface.get_rect(topright=(top_rect.right - 10, top_rect.y + 12))
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
    overlay.fill(OVERLAY)
    screen.blit(overlay, (0, 0))

    popup_w = 420
    popup_h = 320
    popup_rect = pygame.Rect((WIDTH - popup_w) // 2, (HEIGHT - popup_h) // 2, popup_w, popup_h)

    pygame.draw.rect(screen, POPUP_BG, popup_rect, border_radius=18)
    pygame.draw.rect(screen, POPUP_BORDER, popup_rect, 3, border_radius=18)

    center_x = popup_rect.centerx

    if winner == "Hòa":
        screen.blit(ui_icons["handshake"], ui_icons["handshake"].get_rect(center=(center_x, popup_rect.y + 52)))
        screen.blit(
            pygame.transform.smoothscale(piece_images["wK"], (64, 64)),
            pygame.Rect(center_x - 75, popup_rect.y + 88, 64, 64)
        )
        screen.blit(
            pygame.transform.smoothscale(piece_images["bK"], (64, 64)),
            pygame.Rect(center_x + 11, popup_rect.y + 88, 64, 64)
        )
        draw_text(screen, "Hòa", 34, TEXT, center_x, popup_rect.y + 175, center=True)
    else:
        king_piece = "wK" if winner == "Trắng" else "bK"
        screen.blit(ui_icons["trophy"], ui_icons["trophy"].get_rect(center=(center_x, popup_rect.y + 50)))
        screen.blit(
            pygame.transform.smoothscale(piece_images[king_piece], (78, 78)),
            pygame.Rect(center_x - 39, popup_rect.y + 88, 78, 78)
        )
        draw_text(screen, f"{winner} thắng", 34, TEXT, center_x, popup_rect.y + 185, center=True)

    button_w = 150
    button_h = 46
    spacing = 20
    start_x = popup_rect.centerx - (button_w * 2 + spacing) // 2

    replay_rect = pygame.Rect(start_x, popup_rect.y + 240, button_w, button_h)
    home_rect = pygame.Rect(start_x + button_w + spacing, popup_rect.y + 240, button_w, button_h)

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

    pygame.draw.rect(screen, PANEL, rect, border_radius=12)

    draw_text(
        screen,
        message,
        30,
        TEXT,
        rect.centerx,
        rect.centery,
        center=True
    )


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

    while True:
        screen.fill(BG)
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

        draw_side_panels(screen, board_obj)
        draw_board(screen, board_obj, valid_moves, check_king_pos, animation, hover_square)
        draw_bottom_bar(screen, message)

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
                        message = f"{piece_name(piece)} không thể đi vì đang bảo vệ vua"
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
        screen.fill(BG)
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

        draw_side_panels(screen, board_obj)
        draw_board(screen, board_obj, valid_moves, check_king_pos, animation, hover_square)
        draw_bottom_bar(screen, message)

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
                        message = f"{piece_name(piece)} không thể đi vì đang bảo vệ vua"
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