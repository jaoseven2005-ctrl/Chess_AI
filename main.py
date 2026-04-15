import os
import ctypes
from dataclasses import dataclass

import pygame

from engine.game import (
    run_pvp,
    run_pve,
    load_sounds,
    play_click_sound,
    set_click_sound_enabled,
    set_piece_sound_enabled,
    set_display_mode,
    toggle_fullscreen,
    handle_resize,
)

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except AttributeError:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

WIDTH = 1120
HEIGHT = 860
MENU_BG_TOP = (235, 242, 232)
MENU_BG_BOTTOM = (217, 228, 214)
CARD = (250, 252, 249)
TEXT = (34, 44, 38)
BUTTON = (225, 236, 221)
BUTTON_HOVER = (205, 220, 200)
ACCENT = (92, 118, 86)
SETTINGS_BUTTON_SIZE = 48
SETTINGS_PANEL_SIZE = (340, 250)
SETTINGS_PANEL_BG = (250, 250, 245)
SETTINGS_PANEL_BORDER = (204, 211, 196)
SETTINGS_TOGGLE_ON = ACCENT
SETTINGS_TOGGLE_OFF = (205, 210, 202)
SETTINGS_TOGGLE_LABEL = (68, 78, 72)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, 'assets', 'font', 'Roboto-Regular.ttf')

font_cache = {}
raw_icons = {}
scaled_icon_cache = {}


@dataclass(frozen=True)
class MenuLayout:
    screen_width: int
    screen_height: int
    scale: float
    settings_rect: pygame.Rect
    title_y: int
    subtitle_y: int
    cards: tuple[pygame.Rect, pygame.Rect]
    level_buttons: tuple[pygame.Rect, pygame.Rect, pygame.Rect]
    panel_rect: pygame.Rect


def scaled(value, scale, minimum=1):
    return max(minimum, int(round(value * scale)))


def get_font(size, bold=False):
    key = (max(12, int(round(size))), bold)
    if key not in font_cache:
        font = pygame.font.Font(FONT_PATH, key[0])
        font.set_bold(bold)
        font_cache[key] = font
    return font_cache[key]


def load_icon(name):
    if name not in raw_icons:
        raw_icons[name] = pygame.image.load(os.path.join(BASE_DIR, 'assets', 'icon', name)).convert_alpha()
    return raw_icons[name]


def get_scaled_icon(name, size):
    key = (name, size)
    if key not in scaled_icon_cache:
        scaled_icon_cache[key] = pygame.transform.smoothscale(load_icon(name), (size, size))
    return scaled_icon_cache[key]


def invalidate_menu_cache():
    font_cache.clear()
    scaled_icon_cache.clear()


def get_layout(screen):
    screen_width, screen_height = screen.get_size()
    scale = min(screen_width / WIDTH, screen_height / HEIGHT)
    settings_size = scaled(SETTINGS_BUTTON_SIZE, scale, minimum=32)
    margin = scaled(40, scale)
    settings_rect = pygame.Rect(margin, margin, settings_size, settings_size)
    title_y = scaled(78, scale)
    subtitle_y = title_y + scaled(52, scale)

    card_width = scaled(300, scale)
    card_height = scaled(260, scale)
    gap = scaled(70, scale)
    total_width = card_width * 2 + gap
    start_x = (screen_width - total_width) // 2
    card_y = max(subtitle_y + scaled(72, scale), (screen_height - card_height - scaled(220, scale)) // 2)
    card1 = pygame.Rect(start_x, card_y, card_width, card_height)
    card2 = pygame.Rect(start_x + card_width + gap, card_y, card_width, card_height)

    button_w = scaled(180, scale)
    button_h = scaled(56, scale)
    button_gap = scaled(28, scale)
    total_button_w = button_w * 3 + button_gap * 2
    button_x = (screen_width - total_button_w) // 2
    button_y = min(card_y + card_height + scaled(68, scale), screen_height - button_h - scaled(54, scale))
    level_buttons = tuple(
        pygame.Rect(button_x + idx * (button_w + button_gap), button_y, button_w, button_h)
        for idx in range(3)
    )

    panel_w = min(scaled(SETTINGS_PANEL_SIZE[0], scale, minimum=300), screen_width - scaled(48, scale))
    panel_h = min(scaled(SETTINGS_PANEL_SIZE[1], scale, minimum=230), screen_height - scaled(48, scale))
    panel_rect = pygame.Rect((screen_width - panel_w) // 2, (screen_height - panel_h) // 2, panel_w, panel_h)
    return MenuLayout(screen_width, screen_height, scale, settings_rect, title_y, subtitle_y, (card1, card2), level_buttons, panel_rect)


def draw_text(screen, text, size, color, x, y, center=False, bold=False):
    surface = get_font(size, bold=bold).render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)


def truncate_text(text, font, max_width):
    if font.size(text)[0] <= max_width:
        return text
    if max_width <= font.size('...')[0]:
        return ''
    while text and font.size(text + '...')[0] > max_width:
        text = text[:-1]
    return text + '...' if text else ''


def draw_menu_background(screen):
    width, height = screen.get_size()
    for y in range(height):
        ratio = y / max(1, height)
        r = int(MENU_BG_TOP[0] + (MENU_BG_BOTTOM[0] - MENU_BG_TOP[0]) * ratio)
        g = int(MENU_BG_TOP[1] + (MENU_BG_BOTTOM[1] - MENU_BG_TOP[1]) * ratio)
        b = int(MENU_BG_TOP[2] + (MENU_BG_BOTTOM[2] - MENU_BG_TOP[2]) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (width, y))


def draw_card_with_shadow(screen, rect, fill_color, border_color, radius, hover=False):
    shadow_pad = max(8, radius // 3)
    shadow = pygame.Surface((rect.width + shadow_pad * 2, rect.height + shadow_pad * 2), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (18, 35, 26, 40), shadow.get_rect(), border_radius=radius)
    screen.blit(shadow, (rect.x - shadow_pad // 2, rect.y - shadow_pad // 3))
    fill = tuple(min(255, c + 12) for c in fill_color) if hover else fill_color
    pygame.draw.rect(screen, fill, rect, border_radius=radius)
    pygame.draw.rect(screen, border_color, rect, 1, border_radius=radius)


def draw_menu_button(screen, rect, label, scale, active=False, hover=False):
    bg_color = ACCENT if active else BUTTON_HOVER if hover else BUTTON
    border_color = ACCENT if active or hover else (178, 191, 175)
    text_color = (255, 255, 255) if active else ACCENT if not hover else (56, 72, 56)
    radius = scaled(20, scale)
    pygame.draw.rect(screen, bg_color, rect, border_radius=radius)
    pygame.draw.rect(screen, border_color, rect, 2, border_radius=radius)
    draw_text(screen, label, scaled(18, scale), text_color, rect.centerx, rect.centery, center=True)


def draw_title(screen, layout):
    title_font = get_font(scaled(40, layout.scale), bold=True)
    subtitle_font = get_font(scaled(40, layout.scale))
    chess_surface = title_font.render('Chess', True, ACCENT)
    premium_surface = subtitle_font.render(' Premium', True, (51, 72, 52))
    total_width = chess_surface.get_width() + premium_surface.get_width()
    start_x = layout.screen_width // 2 - total_width // 2
    screen.blit(chess_surface, (start_x, layout.title_y))
    screen.blit(premium_surface, (start_x + chess_surface.get_width(), layout.title_y))
    draw_text(screen, 'Modern minimal chess with thoughtful UI details', scaled(18, layout.scale), (83, 100, 86), layout.screen_width // 2, layout.subtitle_y, center=True)


def draw_settings_button(screen, rect, icon, scale, hover=False, pressed=False):
    scale_factor = 0.92 if pressed else 1.05 if hover else 1.0
    width = int(rect.width * scale_factor)
    height = int(rect.height * scale_factor)
    button_rect = pygame.Rect(rect.x + (rect.width - width) // 2, rect.y + (rect.height - height) // 2, width, height)
    shadow = pygame.Surface((button_rect.width + scaled(10, scale), button_rect.height + scaled(10, scale)), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 18), shadow.get_rect(), border_radius=scaled(16, scale))
    screen.blit(shadow, (button_rect.x - scaled(5, scale), button_rect.y - scaled(5, scale)))
    pygame.draw.rect(screen, (255, 255, 255), button_rect, border_radius=scaled(16, scale))
    pygame.draw.rect(screen, ACCENT if hover else (178, 191, 175), button_rect, 1, border_radius=scaled(16, scale))
    screen.blit(icon, icon.get_rect(center=button_rect.center))


def draw_toggle(screen, rect, state, scale):
    fill = SETTINGS_TOGGLE_ON if state else SETTINGS_TOGGLE_OFF
    pygame.draw.rect(screen, fill, rect, border_radius=rect.height // 2)
    pygame.draw.rect(screen, SETTINGS_PANEL_BORDER, rect, 1, border_radius=rect.height // 2)
    knob_size = rect.height - scaled(8, scale)
    knob_x = rect.x + scaled(4, scale) if not state else rect.right - knob_size - scaled(4, scale)
    knob_rect = pygame.Rect(knob_x, rect.y + scaled(4, scale), knob_size, knob_size)
    pygame.draw.ellipse(screen, (255, 255, 255), knob_rect)
    draw_text(screen, 'ON' if state else 'OFF', scaled(14, scale), TEXT, rect.centerx, rect.centery, center=True)


def draw_settings_panel(screen, layout, click_enabled, piece_enabled):
    overlay = pygame.Surface((layout.screen_width, layout.screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 110))
    screen.blit(overlay, (0, 0))
    radius = scaled(20, layout.scale)
    draw_card_with_shadow(screen, layout.panel_rect, SETTINGS_PANEL_BG, SETTINGS_PANEL_BORDER, radius)
    draw_text(screen, 'Cài đặt', scaled(26, layout.scale), ACCENT, layout.panel_rect.centerx, layout.panel_rect.y + scaled(34, layout.scale), center=True, bold=True)

    label_font = get_font(scaled(18, layout.scale))
    label_x = layout.panel_rect.x + scaled(24, layout.scale)
    toggle_w = scaled(78, layout.scale)
    toggle_h = scaled(36, layout.scale)
    toggle_x = layout.panel_rect.right - scaled(24, layout.scale) - toggle_w
    y1 = layout.panel_rect.y + scaled(84, layout.scale)
    y2 = y1 + scaled(68, layout.scale)
    click_rect = pygame.Rect(toggle_x, y1, toggle_w, toggle_h)
    piece_rect = pygame.Rect(toggle_x, y2, toggle_w, toggle_h)

    for label, rect, state in [('Click Sound', click_rect, click_enabled), ('Piece Move Sound', piece_rect, piece_enabled)]:
        fitted = truncate_text(label, label_font, rect.x - label_x - scaled(16, layout.scale))
        draw_text(screen, fitted, scaled(18, layout.scale), SETTINGS_TOGGLE_LABEL, label_x, rect.y + (rect.height - label_font.get_height()) // 2)
        draw_toggle(screen, rect, state, layout.scale)

    draw_text(screen, 'F11: Fullscreen', scaled(14, layout.scale), SETTINGS_TOGGLE_LABEL, layout.panel_rect.centerx, layout.panel_rect.bottom - scaled(24, layout.scale), center=True)
    return layout.panel_rect, click_rect, piece_rect


def draw_menu(screen, layout, selected_level):
    draw_menu_background(screen)
    draw_title(screen, layout)
    mouse = pygame.mouse.get_pos()

    icon_size = scaled(64, layout.scale)
    swords_size = scaled(48, layout.scale)
    icon_knight_white = get_scaled_icon('white-chess-knight.png', icon_size)
    icon_knight_black = get_scaled_icon('black-chess-knight.png', icon_size)
    icon_swords = get_scaled_icon('two-swords.png', swords_size)
    icon_bot = get_scaled_icon('user-robot-xmarks.png', icon_size)
    settings_icon = get_scaled_icon('settings.png', scaled(28, layout.scale, minimum=24))

    for rect, icons, label in [
        (layout.cards[0], [icon_knight_white, icon_swords, icon_knight_black], '2 Người Chơi'),
        (layout.cards[1], [icon_knight_white, icon_swords, icon_bot], 'Đấu với máy'),
    ]:
        hover = rect.collidepoint(mouse)
        draw_card_with_shadow(screen, rect, CARD, ACCENT if hover else (210, 221, 209), scaled(28, layout.scale), hover=hover)
        center_x = rect.centerx
        center_y = rect.y + scaled(98, layout.scale)
        offset = scaled(74, layout.scale)
        screen.blit(icons[0], icons[0].get_rect(center=(center_x - offset, center_y)))
        screen.blit(icons[1], icons[1].get_rect(center=(center_x, center_y)))
        screen.blit(icons[2], icons[2].get_rect(center=(center_x + offset, center_y)))
        draw_text(screen, label, scaled(26, layout.scale), ACCENT, center_x, rect.y + scaled(180, layout.scale), center=True)

    level_labels = {'easy': 'Dễ', 'normal': 'Bình thường', 'hard': 'Khó'}
    draw_text(screen, f"Độ khó: {level_labels.get(selected_level, selected_level)}", scaled(20, layout.scale), (95, 110, 96), layout.cards[1].centerx, layout.cards[1].y + scaled(220, layout.scale), center=True)
    draw_text(screen, 'Chọn độ khó AI', scaled(24, layout.scale), ACCENT, layout.screen_width // 2, layout.level_buttons[0].y - scaled(34, layout.scale), center=True)

    for rect, (level, label) in zip(layout.level_buttons, [('easy', 'Dễ'), ('normal', 'Bình thường'), ('hard', 'Khó')]):
        draw_menu_button(screen, rect, label, layout.scale, active=(level == selected_level), hover=rect.collidepoint(mouse))

    settings_hover = layout.settings_rect.collidepoint(mouse)
    settings_pressed = settings_hover and pygame.mouse.get_pressed()[0]
    draw_settings_button(screen, layout.settings_rect, settings_icon, layout.scale, settings_hover, settings_pressed)
    return settings_icon


def menu_loop():
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.init()
    load_sounds()
    screen = set_display_mode(False)
    pygame.display.set_caption('Chess AI')
    clock = pygame.time.Clock()

    selected_level = 'normal'
    settings_open = False
    click_sound_enabled = True
    piece_sound_enabled = True
    running = True

    while running:
        layout = get_layout(screen)
        draw_menu(screen, layout, selected_level)
        panel_rect = click_toggle_rect = piece_toggle_rect = None
        if settings_open:
            panel_rect, click_toggle_rect, piece_toggle_rect = draw_settings_panel(screen, layout, click_sound_enabled, piece_sound_enabled)

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                screen = toggle_fullscreen()
                invalidate_menu_cache()
                break
            elif event.type == pygame.VIDEORESIZE:
                screen = handle_resize(event)
                invalidate_menu_cache()
                break
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                play_click_sound()
                pos = event.pos
                if layout.settings_rect.collidepoint(pos):
                    settings_open = not settings_open
                    continue

                if settings_open:
                    if panel_rect and panel_rect.collidepoint(pos):
                        if click_toggle_rect and click_toggle_rect.collidepoint(pos):
                            click_sound_enabled = not click_sound_enabled
                            set_click_sound_enabled(click_sound_enabled)
                            continue
                        if piece_toggle_rect and piece_toggle_rect.collidepoint(pos):
                            piece_sound_enabled = not piece_sound_enabled
                            set_piece_sound_enabled(piece_sound_enabled)
                            continue
                    settings_open = False
                    continue

                for rect, level in zip(layout.level_buttons, ['easy', 'normal', 'hard']):
                    if rect.collidepoint(pos):
                        selected_level = level
                        break

                if layout.cards[0].collidepoint(pos):
                    result = run_pvp(screen)
                    screen = pygame.display.get_surface() or screen
                    invalidate_menu_cache()
                    if result == 'quit':
                        running = False
                    elif result == 'menu':
                        continue

                if layout.cards[1].collidepoint(pos):
                    result = run_pve(screen, selected_level)
                    screen = pygame.display.get_surface() or screen
                    invalidate_menu_cache()
                    if result == 'quit':
                        running = False
                    elif result == 'menu':
                        continue

    pygame.quit()


if __name__ == '__main__':
    menu_loop()
