import pygame
pygame.init()
WIDTH , HEIGHT = 1000 ,600
FPS = 60
screen = pygame.display.set_mode((WIDTH,HEIGHT))
running = True
clock = pygame.time.Clock()
screen_color = (0,0,0)



while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(screen_color)
        pygame.display.flip()