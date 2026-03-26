# main.py

import pygame
from engine.game import run_pvp

WIDTH = 1120
HEIGHT = 860
BG = (235, 235, 235)
CARD = (210, 210, 210)
TEXT = (20, 20, 20)


def draw_text(screen, text, size, color, x, y, center=False):
    font = pygame.font.Font("assets/font/Roboto-Regular.ttf", size)
    surface = font.render(text, True, color)

    rect = surface.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    screen.blit(surface, rect)


def draw_menu(screen):
    screen.fill(BG)

    draw_text(screen, "CHESS PREMIUM", 36, TEXT, 470, 120)

    # card 2 người chơi
    pygame.draw.rect(screen, CARD, (250, 220, 280, 250), border_radius=16)
    draw_text(screen, "2 Người Chơi", 36, TEXT, 390, 320, center=True)
    draw_text(screen, "(PVP)", 28, TEXT, 390, 370, center=True)

    # card 1 người chơi
    pygame.draw.rect(screen, CARD, (670, 220, 280, 250), border_radius=16)
    draw_text(screen, "Đấu với máy", 36, TEXT, 710, 300)
    draw_text(screen, "(AI)", 28, TEXT, 740, 350)


def menu_loop():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess AI")
    clock = pygame.time.Clock()

    running = True
    while running:
        draw_menu(screen)
        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()

                # card PVP
                if 250 <= x <= 530 and 220 <= y <= 470:
                    result = run_pvp(screen)
                    if result == "quit":
                        running = False

    pygame.quit()


if __name__ == "__main__":
    menu_loop()