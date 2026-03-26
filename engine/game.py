# engine/game.py

import pygame
import copy
from engine.board import Board
from engine.moves import get_valid_moves

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

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
SELECT_COLOR = (255, 255, 0)
MOVE_HINT = (80, 200, 120)
BG = (230, 230, 230)
TEXT = (20, 20, 20)
PANEL = (210, 210, 210)
BUTTON = (160, 160, 160)

POPUP_BG = (245, 240, 230)
POPUP_BORDER = (120, 95, 70)

WHITE_BTN = (236, 228, 213)
WHITE_BTN_HOVER = (246, 238, 223)

DARK_BTN = (92, 64, 51)
DARK_BTN_HOVER = (112, 79, 63)

WHITE_TEXT = (40, 40, 40)
DARK_TEXT = (245, 245, 245)

OVERLAY = (0, 0, 0, 90)

ui_icons = {}

piece_images = {}


def load_images():
    pieces = ["bB", "bK", "bN", "bP", "bQ", "bR", "wB", "wK", "wN", "wP", "wQ", "wR"]
    for p in pieces:
        img = pygame.image.load(f"assets/images/{p}.png")
        piece_images[p] = pygame.transform.scale(img, (SQ_SIZE, SQ_SIZE))
    ui_icons["reset"] = pygame.transform.smoothscale(
        pygame.image.load("screens/reset.png").convert_alpha(), (28, 28)
    )
    ui_icons["home"] = pygame.transform.smoothscale(
        pygame.image.load("screens/home.png").convert_alpha(), (28, 28)
    )
    ui_icons["trophy"] = pygame.transform.smoothscale(
        pygame.image.load("screens/trophy-star.png").convert_alpha(), (56, 56)
    )
    ui_icons["handshake"] = pygame.transform.smoothscale(
        pygame.image.load("screens/handshake.png").convert_alpha(), (56, 56)
    )

def draw_text(screen, text, size, color, x, y, center=False):
    font = pygame.font.Font("assets/font/Roboto-Regular.ttf", size)
    surface = font.render(text, True, color)
    rect = surface.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    screen.blit(surface, rect)


def draw_board(screen, board_obj, valid_moves, check_king_pos=None):
    for row in range(8):
        for col in range(8):
            color = LIGHT if (row + col) % 2 == 0 else DARK
            rect = pygame.Rect(BOARD_X + col*SQ_SIZE, BOARD_Y + row*SQ_SIZE, SQ_SIZE, SQ_SIZE)
            pygame.draw.rect(screen, color, rect)

            # highlight vua bị chiếu
            if check_king_pos == (row, col):
                s = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
                s.fill((255, 0, 0, 100))
                screen.blit(s, (BOARD_X + col*SQ_SIZE, BOARD_Y + row*SQ_SIZE))

            # ô đang chọn
            if board_obj.selected_square == (row, col):
                pygame.draw.rect(screen, SELECT_COLOR, rect, 4)

    for (r, c) in valid_moves:
        rect = pygame.Rect(BOARD_X + c*SQ_SIZE, BOARD_Y + r*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        target_piece = board_obj.board[r][c]

        if target_piece != "--":
            pygame.draw.rect(screen, (220, 50, 50), rect, 5)
        else:
            center_x = BOARD_X + c * SQ_SIZE + SQ_SIZE // 2
            center_y = BOARD_Y + r * SQ_SIZE + SQ_SIZE // 2
            pygame.draw.circle(screen, MOVE_HINT, (center_x, center_y), 10)

    for row in range(8):
        for col in range(8):
            piece = board_obj.board[row][col]
            if piece != "--":
                screen.blit(piece_images[piece], (BOARD_X + col*SQ_SIZE, BOARD_Y + row*SQ_SIZE))

def draw_icon_button(screen, rect, label, icon_key, bg_color, text_color, hover=False):
    color = bg_color
    if hover:
        if bg_color == WHITE_BTN:
            color = WHITE_BTN_HOVER
        else:
            color = DARK_BTN_HOVER

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

        small = pygame.transform.scale(piece_images[piece], (icon_size, icon_size))
        screen.blit(small, (x, y))

    for i, piece in enumerate(board_obj.captured_black):
        row = i // cols
        col = i % cols
        x = right_x + 10 + col * (icon_size + gap_icon)
        y = start_y + row * (icon_size + gap_icon)

        if y + icon_size > panel_y + panel_h - 10:
            break

        small = pygame.transform.scale(piece_images[piece], (icon_size, icon_size))
        screen.blit(small, (x, y))

def draw_top_bar(screen, white_to_move, turn_time, total_game_time):
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
    right_x = BOARD_X + BOARD_SIZE + GAP
    button_w = 78
    button_h = 46

    reset_rect = pygame.Rect(
        right_x,
        MARGIN,
        button_w,
        button_h
    )

    home_rect = pygame.Rect(
        right_x + PANEL_W - button_w,
        MARGIN,
        button_w,
        button_h
    )

    mouse_pos = pygame.mouse.get_pos()
    draw_icon_button(
        screen, reset_rect, "Reset", "reset",
        WHITE_BTN, WHITE_TEXT, reset_rect.collidepoint(mouse_pos)
    )
    draw_icon_button(
        screen, home_rect, "Home", "home",
        DARK_BTN, DARK_TEXT, home_rect.collidepoint(mouse_pos)
    )

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
    draw_icon_button(
        screen, replay_rect, "Chơi lại", "reset",
        WHITE_BTN, WHITE_TEXT, replay_rect.collidepoint(mouse_pos)
    )
    draw_icon_button(
        screen, home_rect, "Home", "home",
        DARK_BTN, DARK_TEXT, home_rect.collidepoint(mouse_pos)
    )

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

            # Tốt: chỉ tính ô ăn chéo, không tính ô đi thẳng
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

        # Sau move_piece thì lượt đã đổi, nhưng ta chỉ cần check vua của quân vừa đi
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
    return x <= mx <= x+w and y <= my <= y+h

def run_pvp(screen):
    clock = pygame.time.Clock()
    board_obj = Board()
    load_images()
    
    turn_time = 600
    total_game_time = 0
    last_tick = pygame.time.get_ticks()

    running = True
    valid_moves = []
    message = "Chọn quân để bắt đầu"
    winner = None
    check_king_pos = None

    while running:
        screen.fill(BG)
        current_color = "w" if board_obj.white_to_move else "b"
        current_name = "Trắng" if current_color == "w" else "Đen"
        
        now = pygame.time.get_ticks()
        delta = (now - last_tick) / 1000
        last_tick = now

        if winner is None:
            total_game_time += delta
            turn_time -= delta

        if winner is None and turn_time <= 0:
            turn_time = 600
            board_obj.white_to_move = not board_obj.white_to_move
            board_obj.selected_square = None
            valid_moves = []
            check_king_pos = None

            current_name = "Trắng" if board_obj.white_to_move else "Đen"
            message = f"Hết thời gian suy nghĩ, chuyển lượt sang {current_name}"
        
        if winner is None:
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
                    message = f"Lượt: {current_name}"

        reset_rect, home_rect = draw_top_bar(screen, board_obj.white_to_move, turn_time, total_game_time)
        popup_reset_rect = None
        popup_home_rect = None  
        draw_side_panels(screen, board_obj)
        draw_board(screen, board_obj, valid_moves, check_king_pos)
        draw_bottom_bar(screen, message)

        if winner is not None:
            popup_reset_rect, popup_home_rect = draw_end_popup(screen, winner)
        
        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                # vẫn cho reset / back sau khi game kết thúc
                if click_button(pos, reset_rect.x, reset_rect.y, reset_rect.width, reset_rect.height):
                    board_obj.reset()
                    valid_moves = []
                    message = "Đã reset bàn cờ"
                    winner = None
                    check_king_pos = None

                    turn_time = 600
                    total_game_time = 0
                    last_tick = pygame.time.get_ticks()
                    continue

                if click_button(pos, home_rect.x, home_rect.y, home_rect.width, home_rect.height):
                    return "menu"
                
                if winner is not None:
                    if popup_reset_rect and click_button(
                        pos, popup_reset_rect.x, popup_reset_rect.y, popup_reset_rect.width, popup_reset_rect.height
                    ):
                        board_obj.reset()
                        valid_moves = []
                        message = "Đã reset bàn cờ"
                        winner = None
                        check_king_pos = None
                        turn_time = 600
                        total_game_time = 0
                        last_tick = pygame.time.get_ticks()
                        continue

                    if popup_home_rect and click_button(
                        pos, popup_home_rect.x, popup_home_rect.y, popup_home_rect.width, popup_home_rect.height
                    ):
                        return "menu"
                    continue

                # khóa click bàn cờ khi đã kết thúc
                if winner is not None:
                    continue

                square = get_square_from_mouse(pos)
                if square is None:
                    continue

                row, col = square
                piece = board_obj.get_piece(row, col)

                # chưa chọn ô nào
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

                # đã chọn rồi
                start = board_obj.selected_square

                # click lại quân cùng màu -> đổi quân chọn
                if piece != "--":
                    selected_piece = board_obj.get_piece(start[0], start[1])
                    if piece[0] == selected_piece[0]:
                        board_obj.selected_square = (row, col)
                        valid_moves = get_legal_moves(board_obj, row, col)
                        message = f"Đổi chọn sang {piece_name(piece)}"
                        continue

                # thử đi
                if (row, col) in valid_moves:
                    moving_piece = board_obj.get_piece(start[0], start[1])
                    board_obj.move_piece(start, (row, col))
                    turn_time = 600
                    board_obj.selected_square = None
                    valid_moves = []

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
                            message = f"{piece_name(moving_piece)} di chuyển thành công"
                else:
                    board_obj.selected_square = None
                    valid_moves = []
                    message = "Nước đi không hợp lệ"
def format_time(t):
    t = max(0, int(t))
    minutes = t // 60
    seconds = t % 60
    return f"{minutes:02}:{seconds:02}"