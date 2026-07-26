import pygame
pygame.init()
WIDTH , HEIGHT = 1000 ,600
FPS = 60
screen = pygame.display.set_mode((WIDTH,HEIGHT))
running = True
clock = pygame.time.Clock()
screen_color = (0,0,0)

class Ship(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,image_path,damage,hp,speed = 8):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image_path = image_path
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))
        self.damage = damage
        self.hp = hp
        self.speed = speed
    def move(self):
        global keys
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        elif keys[pygame.K_DOWN]:
            self.rect.y += self.speed
        elif keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        elif keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
            
pro_ships = pygame.sprite.Group()
ship = Ship(100,100,40,40,"ship.png",1,10)
pro_ships.add(ship)

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    screen.fill(screen_color)
    pro_ships.draw(screen)
    for ship in pro_ships:
        ship.move()
    pygame.display.flip()