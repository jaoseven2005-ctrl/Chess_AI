import os
import pygame
from engine.game import run_pvp, run_pve, load_sounds, play_click_sound, set_click_sound_enabled, set_piece_sound_enabled

# DPI Awareness for Windows scaling
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Windows 8.1+
except AttributeError:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # Windows Vista+
    except:
        pass  # Fallback if not available

WIDTH = 1120
HEIGHT = 860
BG = (246, 248, 244)
MENU_BG_TOP = (235, 242, 232)
MENU_BG_BOTTOM = (217, 228, 214)
CARD = (250, 252, 249)
CARD_HOVER = (234, 243, 230)
TEXT = (34, 44, 38)
BUTTON = (225, 236, 221)
BUTTON_HOVER = (205, 220, 200)
ACCENT = (92, 118, 86)

SETTINGS_BUTTON_SIZE = 48
TOP_MARGIN = 40  # Safe margin from top edge for title bar and DPI scaling
SETTINGS_MARGIN = TOP_MARGIN
SETTINGS_PANEL_SIZE = (320, 240)
SETTINGS_PANEL_BG = (250, 250, 245)
SETTINGS_PANEL_BORDER = (204, 211, 196)
SETTINGS_TOGGLE_ON = ACCENT
SETTINGS_TOGGLE_OFF = (205, 210, 202)
SETTINGS_TOGGLE_LABEL = (68, 78, 72)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "assets", "font", "Roboto-Regular.ttf")

font_cache = {}


def get_font(size, bold=False):
    key = (size, bold)
    if key not in font_cache:
        font = pygame.font.Font(FONT_PATH, size)
        font.set_bold(bold)
        font_cache[key] = font
    return font_cache[key]


def load_icon(*parts, size=None):
    path = os.path.join(BASE_DIR, *parts)
    img = pygame.image.load(path).convert_alpha()
    if size is not None:
        img = pygame.transform.smoothscale(img, size)
    return img


def draw_text(screen, text, size, color, x, y, center=False, bold=False):
    font = get_font(size, bold=bold)
    surface = font.render(text, True, color)

    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    screen.blit(surface, rect)


def draw_title(screen, x, y):
    title_font = get_font(40, bold=True)
    subtitle_font = get_font(40, bold=False)

    chess_surface = title_font.render("Chess", True, ACCENT)
    premium_surface = subtitle_font.render(" Premium", True, (51, 72, 52))

    total_width = chess_surface.get_width() + premium_surface.get_width()
    start_x = x - total_width // 2

    screen.blit(chess_surface, (start_x, y))
    screen.blit(premium_surface, (start_x + chess_surface.get_width(), y))


def draw_menu_button(screen, rect, label, active=False, hover=False):
    if active:
        bg_color = ACCENT
        border_color = ACCENT
        text_color = (255, 255, 255)
    else:
        bg_color = BUTTON_HOVER if hover else BUTTON
        border_color = ACCENT if hover else (178, 191, 175)
        text_color = ACCENT if not hover else (56, 72, 56)

    pygame.draw.rect(screen, bg_color, rect, border_radius=20)
    pygame.draw.rect(screen, border_color, rect, 2, border_radius=20)
    draw_text(screen, label, 18, text_color, rect.centerx, rect.centery, center=True)


def draw_card_with_shadow(screen, rect, fill_color, border_color, hover=False, radius=28):
    shadow_surface = pygame.Surface((rect.width + 18, rect.height + 18), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surface, (18, 35, 26, 40), shadow_surface.get_rect(), border_radius=radius)
    screen.blit(shadow_surface, (rect.x + 6, rect.y + 6))

    fill = tuple(min(255, c + 12) for c in fill_color) if hover else fill_color
    pygame.draw.rect(screen, fill, rect, border_radius=radius)
    pygame.draw.rect(screen, border_color, rect, 1, border_radius=radius)


def draw_menu_background(screen):
    height = screen.get_height()
    for y in range(height):
        ratio = y / height
        r = int(MENU_BG_TOP[0] + (MENU_BG_BOTTOM[0] - MENU_BG_TOP[0]) * ratio)
        g = int(MENU_BG_TOP[1] + (MENU_BG_BOTTOM[1] - MENU_BG_TOP[1]) * ratio)
        b = int(MENU_BG_TOP[2] + (MENU_BG_BOTTOM[2] - MENU_BG_TOP[2]) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))


def draw_settings_button(screen, rect, hover=False, pressed=False):
    if pressed:
        scale = 0.92
    elif hover:
        scale = 1.05
    else:
        scale = 1.0

    width = int(rect.width * scale)
    height = int(rect.height * scale)
    x = rect.x + (rect.width - width) // 2
    y = rect.y + (rect.height - height) // 2
    button_rect = pygame.Rect(x, y, width, height)

    shadow_surface = pygame.Surface((button_rect.width + 10, button_rect.height + 10), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surface, (0, 0, 0, 18), shadow_surface.get_rect(), border_radius=16)
    screen.blit(shadow_surface, (button_rect.x - 5, button_rect.y - 5))

    pygame.draw.rect(screen, (255, 255, 255, 24), button_rect, 1, border_radius=16)
    pygame.draw.rect(screen, ACCENT if hover else (178, 191, 175), button_rect, 1, border_radius=16)

    icon_center = button_rect.center
    pygame.draw.circle(screen, ACCENT, icon_center, 2)
    icon_rect = settings_icon.get_rect(center=button_rect.center)
    screen.blit(settings_icon, icon_rect)


def draw_settings_panel(screen, click_enabled, piece_enabled):
    panel_w, panel_h = SETTINGS_PANEL_SIZE
    panel_rect = pygame.Rect((WIDTH - panel_w) // 2, (HEIGHT - panel_h) // 2, panel_w, panel_h)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 110))
    screen.blit(overlay, (0, 0))

    draw_card_with_shadow(screen, panel_rect, SETTINGS_PANEL_BG, SETTINGS_PANEL_BORDER, hover=False, radius=20)

    close_rect = pygame.Rect(panel_rect.right - 34, panel_rect.y + 18, 18, 18)
    pygame.draw.line(screen, (102, 118, 92), (close_rect.left, close_rect.top), (close_rect.right, close_rect.bottom), 2)
    pygame.draw.line(screen, (102, 118, 92), (close_rect.left, close_rect.bottom), (close_rect.right, close_rect.top), 2)

    draw_text(screen, "Cài đặt", 26, ACCENT, panel_rect.centerx, panel_rect.y + 38, center=True, bold=True)

    label_x = panel_rect.x + 24
    toggle_x = panel_rect.right - 24 - 74
    toggle_h = 36
    toggle_y1 = panel_rect.y + 94
    toggle_y2 = panel_rect.y + 162

    draw_text(screen, "Click Sound", 18, SETTINGS_TOGGLE_LABEL, label_x, toggle_y1 + 4, center=False)
    draw_text(screen, "Piece Move Sound", 18, SETTINGS_TOGGLE_LABEL, label_x, toggle_y2 + 4, center=False)

    toggle_rect1 = pygame.Rect(toggle_x, toggle_y1, 74, toggle_h)
    toggle_rect2 = pygame.Rect(toggle_x, toggle_y2, 74, toggle_h)

    for rect, state in ((toggle_rect1, click_enabled), (toggle_rect2, piece_enabled)):
        fill = SETTINGS_TOGGLE_ON if state else SETTINGS_TOGGLE_OFF
        pygame.draw.rect(screen, fill, rect, border_radius=18)
        pygame.draw.rect(screen, SETTINGS_PANEL_BORDER, rect, 1, border_radius=18)

        knob_x = rect.x + 6 if not state else rect.right - toggle_h + 6
        knob_rect = pygame.Rect(knob_x, rect.y + 4, toggle_h - 8, toggle_h - 8)
        pygame.draw.ellipse(screen, (255, 255, 255), knob_rect)

        label = "ON" if state else "OFF"
        draw_text(screen, label, 16, TEXT, rect.centerx, rect.centery, center=True)

    return panel_rect, toggle_rect1, toggle_rect2, close_rect


def click_button(pos, x, y, w, h):
    mx, my = pos
    return x <= mx <= x + w and y <= my <= y + h


def draw_menu(screen, icon_knight_white, icon_knight_black, icon_swords, icon_bot, selected_level):
    draw_menu_background(screen)

    mouse = pygame.mouse.get_pos()

    draw_title(screen, WIDTH // 2, 80)
    draw_text(screen, "Modern minimal chess with thoughtful UI details", 18, (83, 100, 86), WIDTH // 2, 128, center=True)

    card_width = 300
    card_height = 260
    gap = 70

    total_width = card_width * 2 + gap
    start_x = (WIDTH - total_width) // 2

    card1 = pygame.Rect(start_x, 220, card_width, card_height)
    card2 = pygame.Rect(start_x + card_width + gap, 220, card_width, card_height)

    for rect, icons, label in [
        (card1, [icon_knight_white, icon_swords, icon_knight_black], "2 Người Chơi"),
        (card2, [icon_knight_white, icon_swords, icon_bot], "Đấu với máy")
    ]:
        hover = rect.collidepoint(mouse)
        draw_card_with_shadow(screen, rect, CARD, ACCENT if hover else (210, 221, 209), hover=hover)

        center_x = rect.centerx
        center_y = rect.y + 98
        screen.blit(icons[0], icons[0].get_rect(center=(center_x - 74, center_y)))
        screen.blit(icons[1], icons[1].get_rect(center=(center_x, center_y)))
        screen.blit(icons[2], icons[2].get_rect(center=(center_x + 74, center_y)))
        draw_text(screen, label, 26, ACCENT, center_x, rect.y + 180, center=True)

    level_labels = {"easy": "Dễ", "normal": "Bình thường", "hard": "Khó"}
    draw_text(screen, f"Độ khó: {level_labels.get(selected_level, selected_level)}", 20, (95, 110, 96), card2.centerx, card2.y + 220, center=True)

    level_buttons = []
    levels = [("easy", "Dễ"), ("normal", "Bình thường"), ("hard", "Khó")]
    button_w = 180
    button_h = 56
    button_gap = 28
    button_x = (WIDTH - (button_w * 3 + button_gap * 2)) // 2
    button_y = 540

    draw_text(screen, "Chọn độ khó AI", 24, ACCENT, WIDTH // 2, button_y - 34, center=True)

    for idx, (level, label) in enumerate(levels):
        rect = pygame.Rect(button_x + idx * (button_w + button_gap), button_y, button_w, button_h)
        hover = rect.collidepoint(mouse)
        draw_menu_button(screen, rect, label, active=(level == selected_level), hover=hover)
        level_buttons.append((level, rect))

    return card1, card2, level_buttons


def menu_loop():
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.init()
    load_sounds()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess AI")
    clock = pygame.time.Clock()

    icon_knight_white = load_icon("assets", "icon", "white-chess-knight.png", size=(64, 64))
    icon_knight_black = load_icon("assets", "icon", "black-chess-knight.png", size=(64, 64))
    icon_swords = load_icon("assets", "icon", "two-swords.png", size=(48, 48))
    icon_bot = load_icon("assets", "icon", "user-robot-xmarks.png", size=(64, 64))
    global settings_icon
    settings_icon = load_icon("assets", "icon", "settings.png", size=(48, 48))

    selected_level = "normal"
    settings_open = False
    settings_button_rect = pygame.Rect(SETTINGS_MARGIN, SETTINGS_MARGIN, SETTINGS_BUTTON_SIZE, SETTINGS_BUTTON_SIZE)
    click_toggle_rect = None
    piece_toggle_rect = None
    click_sound_enabled = True
    piece_sound_enabled = True
    running = True
    while running:
        panel_rect = None
        card1, card2, level_buttons = draw_menu(
            screen,
            icon_knight_white,
            icon_knight_black,
            icon_swords,
            icon_bot,
            selected_level
        )

        settings_hover = settings_button_rect.collidepoint(pygame.mouse.get_pos())
        settings_pressed = settings_hover and pygame.mouse.get_pressed()[0]
        draw_settings_button(screen, settings_button_rect, settings_hover, settings_pressed)

        if settings_open:
            panel_rect, click_toggle_rect, piece_toggle_rect, close_rect = draw_settings_panel(
                screen,
                click_sound_enabled,
                piece_sound_enabled,
            )

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                play_click_sound()
                x, y = pygame.mouse.get_pos()

                if settings_button_rect.collidepoint(x, y):
                    settings_open = not settings_open
                    continue

                if settings_open:
                    if panel_rect and panel_rect.collidepoint(x, y):
                        if close_rect and close_rect.collidepoint(x, y):
                            settings_open = False
                            continue
                        if click_toggle_rect and click_button(
                            (x, y),
                            click_toggle_rect.x,
                            click_toggle_rect.y,
                            click_toggle_rect.width,
                            click_toggle_rect.height,
                        ):
                            click_sound_enabled = not click_sound_enabled
                            set_click_sound_enabled(click_sound_enabled)
                            continue
                        if piece_toggle_rect and click_button(
                            (x, y),
                            piece_toggle_rect.x,
                            piece_toggle_rect.y,
                            piece_toggle_rect.width,
                            piece_toggle_rect.height,
                        ):
                            piece_sound_enabled = not piece_sound_enabled
                            set_piece_sound_enabled(piece_sound_enabled)
                            continue
                        continue
                    settings_open = False
                    continue

                for level, rect in level_buttons:
                    if rect.collidepoint(x, y):
                        selected_level = level
                        break

                if card1.collidepoint(x, y):
                    result = run_pvp(screen)
                    if result == "quit":
                        running = False
                    elif result == "menu":
                        continue

                if card2.collidepoint(x, y):
                    result = run_pve(screen, selected_level)
                    if result == "quit":
                        running = False
                    elif result == "menu":
                        continue

    pygame.quit()


if __name__ == "__main__":
    menu_loop()