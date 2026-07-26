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
        self.cooldown = 20
        self.max_cooldown = self.cooldown
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
        if self.rect.x >= WIDTH - self.w:
            self.rect.x = WIDTH - self.w
        elif self.rect.x <= 0:
            self.rect.x =  0

        if self.rect.y <= 0.66 * HEIGHT:
            self.rect.y = 0.66 * HEIGHT

        if self.rect.y >= HEIGHT - self.h:
            self.rect.y = HEIGHT - self.h

    def shoot(self):
        global lasers
        if keys[pygame.K_SPACE] and self.cooldown <= 0:
            laser = Laser(self.rect.centerx,self.rect.top,5,5)
            lasers.append(laser)
            self.cooldown = self.max_cooldown
        elif self.cooldown > 0 :
            self.cooldown -= 1

class Bug(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)

class Laser(pygame.rect.Rect):
    def __init__(self,x,y,w,h,color=(255,0,255),speed = 9):
        super().__init__(x,y,w,h)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.speed = speed
    def draw(self):
        laser = pygame.rect.Rect(self.x,self.y,self.w,self.h)
        pygame.draw.rect(screen,self.color,laser)
    def update(self):
        self.y -= self.speed
        
pro_ships = pygame.sprite.Group()
ship = Ship(100,100,27,33,"ship.png",1,10)
pro_ships.add(ship)
lasers = []

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    screen.fill(screen_color)
    pro_ships.draw(screen)
    for laser in lasers:
        laser.draw()
        laser.update()
    for ship in pro_ships:
        ship.move()
        ship.shoot()
    
    pygame.display.flip()