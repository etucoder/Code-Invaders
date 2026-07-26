import asyncio # For the itch.io page oh no
import pygame
pygame.init()
pygame.font.init()
font = pygame.font.SysFont(None,96)

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
        self.cooldown = 12
        self.max_cooldown = self.cooldown
        self.max_hp = hp
        red_rect = pygame.rect.Rect(self.rect.centerx,self.rect.centery + 25,5,100)
        green_rect = pygame.rect.Rect(self.rect.centerx,self.rect.centery + 25,5,(100/self.max_hp) * self.hp)
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
        for file in files:
            if self.rect.colliderect(file.rect):
                self.kill()
                file.hp -= self.damage

        if self.hp == 1 and self.image_path == "indentationerror.png":
            self.image_path = "indentationerrorlow.png"
            self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(self.w,self.h))
            self.rect = self.image.get_rect(topleft = (self.rect.x,self.rect.y))
        
        

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


class FileTower(pygame.sprite.Sprite):
    def __init__(self, x,y,w,h,image_path,hp):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h 
        self.image_path = image_path
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))
        self.hp = hp
        self.max_hp = hp
        red_rect = pygame.rect.Rect(self.rect.centerx,self.rect.centery + 25,5,100)
        green_rect = pygame.rect.Rect(self.rect.centerx,self.rect.centery + 25,5,(100/self.max_hp) * self.hp)
    def update(self):
        if self.hp <= 0:
            self.kill()
        red_rect = pygame.rect.Rect(self.rect.x + 10,self.rect.top - 25,50,5)
        green_rect = pygame.rect.Rect(self.rect.x + 10,self.rect.top - 25,(50/self.max_hp) * self.hp,5)
        pygame.draw.rect(screen,(255,0,0),red_rect)
        pygame.draw.rect(screen,(0,255,0),green_rect)
        
keys = pygame.key.get_pressed()
files = pygame.sprite.Group()
main = FileTower(WIDTH//2 - 40 , HEIGHT - 130,80,120,"main.png",10)
server = FileTower(WIDTH//2 - 140 , HEIGHT - 130,80,120,"server.png",5)
client = FileTower(WIDTH//2 + 60 , HEIGHT - 130,80,120,"client.png",5)
image_folder = FileTower(WIDTH//2 + 160 , HEIGHT - 120,120,110,"game_sprites.png",5)
spritesheets = FileTower(WIDTH//2 - 280 , HEIGHT - 120,120,110,"spritesheets.png",5)
devlog = FileTower(WIDTH//2 - 380 , HEIGHT - 130,80,120,"devlog.png",5)
error_log = FileTower(WIDTH//2 + 300 , HEIGHT - 130,100,120,"error_log.png",5)
readme = FileTower(WIDTH//2 - 480 , HEIGHT - 130,80,120,"readme.png",5)
gitignore = FileTower(WIDTH//2 + 410 , HEIGHT - 130,80,120,"gitignore.png",5)
files.add(readme)
files.add(devlog)
files.add(spritesheets)
files.add(server)
files.add(main)
files.add(client)
files.add(image_folder)
files.add(error_log)
files.add(gitignore)
pro_ships = pygame.sprite.Group()
bugs = pygame.sprite.Group()
ship = Ship(100,100,27,33,"ship.png",1,1)
pro_ships.add(ship)
lasers = []
current_level = 6
level1 = [["e","e","e","e","e"],["e","e","e","e","e"],["e","e","e","e","e"],["e","e","e","e","e"]]
level2 = [["e","e","e","e","e","e","e"],["e","e","e","e","e","e","e"],["e","e","e","e","e","e","e"],["e","e","e","e","e","e","e"]]
level3 = [['i','i','i','i','i','i'],["e","e","e","e","e","e",],['i','i','i','i','i','i'],["e","e","e","e","e","e",]]
level4 = [['e','e','e','e','e','e'],["e","e","e","e","e","e",],['i','i','i','i','i','i'],["i","i","i","i","i","i",],["i","i","i","i","i","i",]]
level5 = [['i','i','i','i','i','i'],["e","e","e","e","e","e",],["e","e","e","e","e","e",],['x','x','x','x','x','x']]
level6 = [['i','i','i','i','i','i'],["x","x","x","x","x","x",],["e","e","e","e","e","e",],['x','x','x','x','x','x']]
level7 = [['i','i','i','i','i','i','i','i','i','i','i','i'],['i','i','i','i','i','i','i','i','i','i','i','i'],]
level_list = [level1,level2,level3,level4,level5,level6,level7]
level = level_list[current_level-1]
startx = (WIDTH // 2) - 75
starty = 0
rowindex = 0
colindex = 0
spacer = 35
startx = (WIDTH // 2) - ((len(level[0]) / 2) * spacer)
for row in level:
    for exception in row:
        bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,"exception.png",1,1,1)
        bugs.add(bug)
        rowindex += 1
    colindex -= spacer
    rowindex = 0
async def main():
    global current_level,keys,running,files,pro_ships,lasers,level_list,level,startx,starty,rowindex,colindex,spacer,bugs
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
        files.draw(screen)
        for file in files:
            file.update()
        for laser in lasers:
            laser.draw()
            laser.update()
        for ship in pro_ships:
            ship.move()
            ship.shoot()
            ship.update()
        bugsnum = 0
        for bug in bugs:
            bug.move()
            bug.check_for_collisions()
            bugsnum += 1
        if bugsnum == 0:
            current_level += 1
            try:
                level = level_list[current_level-1]
                colindex = 0
                for row in level:
                    for exception in row:
                        if exception == "e":
                            bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,"exception.png",1,1,1)
                        
                        elif exception == "i":
                            bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,"indentationerror.png",1.5,2,1)

                        elif exception == "x":
                            bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,"indexerror.png",1,1,1,y_speed = 1.5)
                        bugs.add(bug)
                        rowindex += 1
                    colindex -= spacer
                    rowindex = 0
            except Exception as e:
                print(e)
                win  = font.render(f"YOU WIN (for now)",True , (0,255,0))
                screen.blit(win,(WIDTH//2 - 300,HEIGHT//2  - 100))
                     
        pygame.display.flip()
        await asyncio.sleep(0)
asyncio.run(main())