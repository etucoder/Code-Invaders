import pygame
pygame.init()
WIDTH , HEIGHT = 1000 ,600
FPS = 60
screen = pygame.display.set_mode((WIDTH,HEIGHT))
running = True
clock = pygame.time.Clock()
screen_color = (0,0,0)

class Ship(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,image_path,damage,hp,speed = 6):
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
        self.max_hp = hp
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
    def update(self):
        if self.hp <= 0:
            self.cooldown = self.max_cooldown * 10
            self.hp = self.max_hp
    def shoot(self):
        global lasers
        if keys[pygame.K_SPACE] and self.cooldown <= 0:
            laser = Laser(self.rect.centerx,self.rect.top,5,5)
            lasers.append(laser)
            self.cooldown = self.max_cooldown
        elif self.cooldown > 0 :
            self.cooldown -= 1

class Bug(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,image_path,damage,hp ,speed,y_speed = 0.5 ):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image_path = image_path
        self.damage = damage
        self.hp = hp
        self.speed = speed
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))
        self.movetox = 0
        self.movetoy = 0
        self.float_y = self.y
        self.y_speed = y_speed
    def move(self,axis = "n",amount = 0):
        if axis == "x":
            self.movetox = amount
            if amount > 0:
                if self.speed > self.movetox:
                    self.rect.x += self.movetox
                    self.movetox -= self.movetox
                else:
                    self.rect.x += self.speed
                    self.movetox -= self.speed
            elif amount < 0:
                if self.speed < self.movetox:
                    self.rect.x -= self.movetox
                    self.movetox += self.movetox
                else:
                    self.rect.x -= self.speed
                    self.movetox += self.speed

        self.float_y += self.y_speed
        self.rect.y = int(self.float_y)
    
    def check_for_collisions(self):
        for laser in lasers:
            if self.rect.colliderect(laser):
                self.hp -= laser.damage
                if laser in lasers:
                    lasers.remove(laser)
            if self.hp <= 0:
                self.kill()

        for ship in pro_ships:
            if self.rect.colliderect(ship.rect):
                self.kill()
                ship.hp -= self.damage
                for bug in bugs:
                    bug.float_y -= 75

        
        

class Laser(pygame.rect.Rect):
    def __init__(self,x,y,w,h,color=(255,0,255),speed = 9,damage = 1):
        super().__init__(x,y,w,h)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.speed = speed
        self.damage = damage
    def draw(self):
        laser = pygame.rect.Rect(self.x,self.y,self.w,self.h)
        pygame.draw.rect(screen,self.color,laser)
    def update(self):
        self.y -= self.speed
        
pro_ships = pygame.sprite.Group()
bugs = pygame.sprite.Group()
ship = Ship(100,100,27,33,"ship.png",1,1)
pro_ships.add(ship)
lasers = []
level1 = [["e","e","e","e","e"],["e","e","e","e","e"],["e","e","e","e","e"],["e","e","e","e","e"]]
level2 = [["e","e","e","e","e","e","e"],["e","e","e","e","e","e","e"],["e","e","e","e","e","e","e"],["e","e","e","e","e","e","e"]]
level = level1
startx = (WIDTH // 2) - 75
starty = 0
rowindex = 0
colindex = 0
spacer = 35
startx = (WIDTH // 2) - ((len(level[0]) / 2) * spacer)
for row in level:
    for exception in row:
        bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,"exception.png",3,1,1)
        bugs.add(bug)
        rowindex += 1
    colindex -= spacer
    rowindex = 0

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    screen.fill(screen_color)
    pro_ships.draw(screen)
    bugs.draw(screen)
    for laser in lasers:
        laser.draw()
        laser.update()
    for ship in pro_ships:
        ship.move()
        ship.shoot()
        ship.update()
    for bug in bugs:
        bug.move()
        bug.check_for_collisions()
    
    pygame.display.flip()