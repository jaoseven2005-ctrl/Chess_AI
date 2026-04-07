import os
import pygame
from engine.game import run_pvp, run_pve, load_sounds, play_click_sound

WIDTH = 1120
HEIGHT = 860
BG = (235, 235, 235)
CARD = (210, 210, 210)
TEXT = (20, 20, 20) 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "assets", "font", "Roboto-Regular.ttf")

font_cache = {}


def get_font(size):
    if size not in font_cache:
        font_cache[size] = pygame.font.Font(FONT_PATH, size)
    return font_cache[size]


def load_icon(*parts, size=None):
    path = os.path.join(BASE_DIR, *parts)
    img = pygame.image.load(path).convert_alpha()
    if size is not None:
        img = pygame.transform.smoothscale(img, size)
    return img


def draw_text(screen, text, size, color, x, y, center=False):
    font = get_font(size)
    surface = font.render(text, True, color)

    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    screen.blit(surface, rect)


def draw_menu(screen, icon_knight_white, icon_knight_black, icon_swords, icon_bot, selected_level):
    screen.fill(BG)

    mouse = pygame.mouse.get_pos()

    draw_text(screen, "CHESS PREMIUM", 36, TEXT, WIDTH // 2, 90, center=True)

    card_width = 280
    card_height = 250
    gap = 60

    total_width = card_width * 2 + gap
    start_x = (WIDTH - total_width) // 2

    # CARD 1
    card1 = pygame.Rect(start_x, 220, card_width, card_height)
    color1 = (200, 200, 200) if card1.collidepoint(mouse) else CARD
    pygame.draw.rect(screen, color1, card1, border_radius=16)

    center_x = card1.centerx
    center_y = card1.y + 90

    screen.blit(icon_knight_white, icon_knight_white.get_rect(center=(center_x - 70, center_y)))
    screen.blit(icon_swords, icon_swords.get_rect(center=(center_x, center_y)))
    screen.blit(icon_knight_black, icon_knight_black.get_rect(center=(center_x + 70, center_y)))

    draw_text(screen, "2 Người Chơi", 28, TEXT, center_x, card1.y + 170, center=True)

    # CARD 2
    card2 = pygame.Rect(start_x + card_width + gap, 220, card_width, card_height)
    color2 = (200, 200, 200) if card2.collidepoint(mouse) else CARD
    pygame.draw.rect(screen, color2, card2, border_radius=16)

    center_x = card2.centerx
    center_y = card2.y + 90

    screen.blit(icon_knight_white, icon_knight_white.get_rect(center=(center_x - 70, center_y)))
    screen.blit(icon_swords, icon_swords.get_rect(center=(center_x, center_y)))
    screen.blit(icon_bot, icon_bot.get_rect(center=(center_x + 70, center_y)))

    draw_text(screen, "Đấu với máy", 28, TEXT, center_x, card2.y + 150, center=True)

    level_labels = {"easy": "Dễ", "normal": "Bình thường", "hard": "Khó"}
    draw_text(screen, f"Độ khó: {level_labels.get(selected_level, selected_level)}", 20, TEXT, center_x, card2.y + 195, center=True)

    level_buttons = []
    levels = [("easy", "Dễ"), ("normal", "Bình thường"), ("hard", "Khó")]
    button_w = 180
    button_h = 52
    button_gap = 30
    button_x = (WIDTH - (button_w * 3 + button_gap * 2)) // 2
    button_y = 520

    draw_text(screen, "Chọn độ khó AI", 26, TEXT, WIDTH // 2, button_y - 36, center=True)

    for idx, (level, label) in enumerate(levels):
        rect = pygame.Rect(button_x + idx * (button_w + button_gap), button_y, button_w, button_h)
        selected = level == selected_level
        color = (180, 220, 180) if selected else CARD
        if rect.collidepoint(mouse):
            color = (190, 190, 190)
        pygame.draw.rect(screen, color, rect, border_radius=14)
        draw_text(screen, label, 22, TEXT, rect.centerx, rect.centery, center=True)
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

    selected_level = "normal"
    running = True
    while running:
        card1, card2, level_buttons = draw_menu(
            screen,
            icon_knight_white,
            icon_knight_black,
            icon_swords,
            icon_bot,
            selected_level
        )
        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                play_click_sound()
                x, y = pygame.mouse.get_pos()

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