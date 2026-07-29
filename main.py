import asyncio # For the itch.io page oh no
import pygame
import random
import math
pygame.init()
pygame.font.init()
font = pygame.font.SysFont(None,96)
title_font = pygame.font.Font("PressStart2P.ttf", 72)
subtitle_font = pygame.font.Font("PressStart2P.ttf", 42)
card_font = pygame.font.SysFont(None,20)
ui_font = pygame.font.Font("VT323-Regular.ttf", 20)
small_font = ui_font = pygame.font.Font("VT323-Regular.ttf", 18)
WIDTH , HEIGHT = 1000 ,600
FPS =  60                
screen = pygame.display.set_mode((WIDTH,HEIGHT))
running = True
clock = pygame.time.Clock()
screen_color = (0,0,0)
particles = []
game_state = 0

#### Menu Stuff #####


class MenuButton():
    def __init__(self,text,center_x,center_y,width,height,target_state,color = (30,30,35)):
        self.text = text
        self.width = width
        self.height = height
        self.target_state = target_state

        self.rect = pygame.Rect(0,0,width,height)
        self.rect.center = (center_x,center_y)
        self.idle_color = color
        self.hover_color = (0,180,255)
    def draw(self,screen,font,mousepos):
        the_color = (0,0,0)
        if self.rect.collidepoint(mousepos):
            the_color = self.hover_color
        else:
            the_color = self.idle_color

        pygame.draw.rect(screen,the_color,self.rect,border_radius=8)
        pygame.draw.rect(screen,(255,255,255),self.rect,width=2,border_radius=8)

        text_surface = font.render(self.text,True,(255,255,255))
        text_rect = text_surface.get_rect(center = self.rect.center)
        screen.blit(text_surface,text_rect)

    def check_clicks(self,mouse_pos , mouse_pressed ):
        if self.rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            return True
        return False


##### Game Stuff #####
########### SHIPPY ##################
class Ship(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,image_path,damage,hp = 10,speed = 6,knockback = 0,pierce = 0):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.weapon_type = "Regular"
        self.image_path = image_path
        self.pierce = pierce
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))
        self.damage = 40
        self.hp = hp
        self.speed = speed
        if self.weapon_type != "Shotgun" and self.weapon_type != "Mine" :
            self.cooldown = 12
        elif self.weapon_type == "Shotgun":
            self.cooldown = 45
        elif self.weapon_type == "Mine":
            self.cooldown = 60
        self.max_cooldown = self.cooldown
        self.max_hp = hp
        self.knockback = knockback
        self.can_dash = True
        self.is_dashing = False
        self.dash_damage = 3
        self.dash_cooldown = 200
        red_rect = pygame.rect.Rect(self.rect.centerx,self.rect.centery + 25,5,100)
        green_rect = pygame.rect.Rect(self.rect.centerx,self.rect.centery + 25,5,(100/self.max_hp) * self.hp)
    def move(self):
        global keys,bugs
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        elif keys[pygame.K_RSHIFT] and self.can_dash and self.dash_cooldown <= 0:
            self.is_dashing = True
            self.dash_cooldown = 200
            dash_beam = pygame.Rect(self.rect.x,0,self.w,self.rect.y)
            for bug in bugs:
                if bug.rect.colliderect(dash_beam):
                    bug.hp -= self.dash_damage
            self.rect.y = 0
        elif keys[pygame.K_RSHIFT] and self.dash_cooldown <= 150:
            self.rect.y = 500
        
            
            self.is_dashing = False
        if self.dash_cooldown > 0 and self.can_dash:
            self.dash_cooldown -= 1

        if self.rect.x >= WIDTH - self.w:
            self.rect.x = WIDTH - self.w
        elif self.rect.x <= 0:
            self.rect.x =  0

        if self.rect.y <=  0:
            self.rect.y = 0

        if self.rect.y >= HEIGHT - self.h:
            self.rect.y = HEIGHT - self.h
    def update(self):
        global lives_left
        if self.hp <= 0:
            lives_left -= 1
            self.hp = self.max_hp
            self.rect.x = WIDTH // 2 - (self.w//2)
            self.rect.y = 400
    def shoot(self):
        global lasers,card_was_chosen
        if (keys[pygame.K_SPACE] or keys[pygame.K_e] or keys[pygame.K_q]) and self.cooldown <= 0:
            if self.weapon_type == "Regular":
                laser = Laser(self.rect.centerx,self.rect.top,5,5,damage=self.damage,knockback=self.knockback,pierce=self.pierce)
                lasers.append(laser)
                self.cooldown = self.max_cooldown
            elif self.weapon_type == "Double":
                laser = Laser(self.rect.x+3,self.rect.y+10,5,5,damage=self.damage,knockback=self.knockback,pierce=self.pierce)
                laser1 = Laser(self.rect.x+18,self.rect.y+10,5,5,damage=self.damage,knockback=self.knockback,pierce=self.pierce)
                lasers.append(laser)
                lasers.append(laser1)
                self.cooldown = self.max_cooldown

            elif self.weapon_type == "Shotgun":
                coord_pairs = [(-3.00,-5.20),(-1.55,-5.80),(0.00,-6.00),(1.55,-5.80),(3.00,-5.20)]
                for vx,vy in coord_pairs:
                    bullet = BossLaser(self.rect.centerx,self.rect.centery,vx ,vy,1,(0,255,0),speed=6)
                    lasers.append(bullet)

                self.cooldown = self.max_cooldown

            
        elif self.cooldown > 0 and card_was_chosen == True:
            
            self.cooldown -= 1
items = ["exception.png",
                                                "indentationerror.png",
                                                "indexerror.png",
                                                "memoryerror.png",
                                                "importerror.png",
                                                "brokenpipe.png","typeerror.png"]
class Bug(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,image_path,damage,hp ,speed,y_speed = 0.5 ):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image_path = items[image_path]
        self.damage = damage
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))
        self.movetox = 0
        self.movetoy = 0
        self.float_y = self.y
        self.y_speed = y_speed
        self.og_y_speed = y_speed
        self.creation_cooldown = 100
        self.max_creation_cooldown = self.creation_cooldown
        self.cooldown = 75
        self.max_cooldown = 75
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
        global bugs,enemy_lasers,current_level
        memory_error_alive = any(bug.image_path == "memoryerror.png" for bug in bugs)
        if memory_error_alive == True:
            self.image.set_alpha(100)
            self.y_speed = 0.5 * self.og_y_speed
            self.max_creation_cooldown = 200
        else:
            self.max_creation_cooldown = 100
        for laser in lasers:
            memory_error_alive = any(bug.image_path == "memoryerror.png" for bug in bugs)
            if memory_error_alive == False or self.image_path == "memoryerror.png":
                self.y_speed = self.og_y_speed
                self.image.set_alpha(255)
                if self.rect.colliderect(laser):
                    self.hp -= laser.damage
                    self.float_y -= laser.knockback
                    for bug in bugs:
                        if self.x == bug.x:
                            bug.float_y -= laser.knockback
                    if laser in lasers:
                        if laser.pierce <= 0 or self.hp > 0 :
                            lasers.remove(laser)
                        elif self.hp <= 0:
                            laser.pierce -= 1
            elif memory_error_alive == True:
                self.image.set_alpha(100)
                self.y_speed = 0.5 * self.og_y_speed
        if self.hp <= 0:
            self.kill()
            color = (0,255,0)
            if self.image_path == "exception.png":
                color = (0,255,0)
            elif self.image_path == "indentationerrorlow.png" or self.image_path == "indentationerror .png":
                color = (0,0,255)
            elif self.image_path == "indexerror.png":
                color = (255,165,0)
            elif self.image_path == "memoryerror.png":
                 color = (0,255,0)
                 for i in range(9):
                    particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-3,3),random.randint(-3,3)] , random.randint(4,8),random.choice([(0,255,0),(255,0,0),(255,255,0)])])
            elif self.image_path == "importerror.png":
                color = (165,42,42)
            elif self.image_path == "brokenpipe.png":
                color = (255,255,255)
            elif self.image_path == "typeerror.png":
                color = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
        
            for i in range(9):
                particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-3,3),random.randint(-3,3)] , random.randint(4,8), color])
        for ship in pro_ships:
            if self.rect.colliderect(ship.rect):
                if ship.is_dashing == False:
                    self.hp = 0
                    ship.hp -= self.damage
                else:
                    self.hp -= ship.dash_damage
        for file in files:
            if current_level != 20:
                if self.rect.colliderect(file.rect):
                    self.hp = 0
                    file.hp -= self.damage
        global spacer
        if self.hp <= self.max_hp * 0.5 and self.image_path == "indentationerror.png":
            self.image_path = "indentationerrorlow.png"
            self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(self.w,self.h))
            self.rect = self.image.get_rect(topleft = (self.rect.x,self.rect.y))
        if self.image_path == "importerror.png":
            if self.creation_cooldown <= 0:
                child_bug = Bug(self.rect.x, self.rect.bottom,24,24,0,1,1,1)
                bugs.add(child_bug)
                self.creation_cooldown = self.max_creation_cooldown
            else:
                self.creation_cooldown -= 1

        if self.image_path == "brokenpipe.png" and self.cooldown <= 0:
            enemy_laser = EnemyLaser(self.rect.centerx - 2, self.float_y,9,9,damage=0.5,speed=6)
            enemy_lasers.append(enemy_laser)
            self.cooldown = self.max_cooldown
        elif self.image_path == "brokenpipe.png" and self.cooldown > 0:
            self.cooldown -= 1




        if self.rect.bottom >= HEIGHT:
            self.kill()
class EnemyLaser(pygame.rect.Rect):
    def __init__(self,x,y,w,h,color = (0,0,255),speed = 9, damage = 1, knockback = 0,pierce = 0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.speed = speed
        self.damage = damage
        self.knockback = knockback
        self.pierce = pierce
    def draw(self):
        laser = pygame.rect.Rect(self.x,self.y,self.w,self.h)
        pygame.draw.rect(screen,self.color,laser)
    def update(self):
        global enemy_lasers
        self.y += self.speed
        if self.colliderect(ship.rect):
            enemy_lasers.remove(self)
            ship.hp -= self.damage
class MemoryError(Bug):
    def __init__(self, x, y, w, h, image_path, damage, hp, speed, y_speed=0.5):
        super().__init__(x, y, w, h, image_path, damage, hp, speed, y_speed)

class Mine(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,damage,xv,yv,speed,final_dest_x,final_dest_y):
        super().__init__()
        self.x = x
        self.float_x = float(x)
        self.y = y
        self.float_y = float(y)
        self.w = w
        self.image_path = "mine.png"
        self.h = h
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))
        self.color = (0,165,255)
        self.explosion_radius = 60
        self.damage = damage
        self.tx = final_dest_x
        self.ty = final_dest_y

        self.is_stuck = False
        self.slide_speed = 0.05
    def update(self):
        global bugs,bosses
        if not self.is_stuck:
            dx = self.tx - self.float_x
            dy = self.ty - self.float_y

            self.float_x += dx * self.slide_speed
            self.float_y += dy * self.slide_speed

            self.rect.x = int(self.float_x)
            self.rect.y = int(self.float_y)

            if math.hypot(self.float_x-self.tx,self.float_y - self.ty) < 1.5:
                self.rect.centerx = int(self.float_x)
                self.rect.centery = int(self.float_y)
                self.is_stuck = True

        if self.is_stuck:
            for bug in bugs:

                distance = math.hypot(bug.rect.centerx - self.rect.centerx,bug.rect.centery - self.rect.centery)
                if distance <= 35 or self.rect.colliderect(bug.rect):
                    self.explode(bugs)
                    break

    def explode(self,bugs_group):
        global bosses
        for bug in bugs_group:
            dist = math.hypot(bug.rect.centerx - self.rect.centerx,bug.rect.centery - self.rect.centery)
            if dist <= self.explosion_radius or self.rect.colliderect(bug.rect):
                bug.hp -= self.damage
        for i in range(20):
            particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-4,4),random.randint(-4,4)] , random.randint(3,8), (255,0,0)])
        self.kill()
                



        
class Laser(pygame.rect.Rect):
    def __init__(self,x,y,w,h,color=(255,0,255),speed = 9,damage = 1,knockback = 0,pierce = 0,vx = 0 ,vy = 0):
        super().__init__(x,y,w,h)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.speed = speed
        self.damage = damage
        self.knockback = knockback
        self.pierce = pierce
        self.xv = vx
        self.yv = vy
    def draw(self):
        laser = pygame.rect.Rect(self.x,self.y,self.w,self.h)
        pygame.draw.rect(screen,self.color,laser)
    def update(self):
        global enemy_lasers,ship,lasers
        self.y -= self.speed
        for enlaser in enemy_lasers:
            if self.colliderect(enlaser):
                lasers.remove(self)
                try:
                    enemy_lasers.remove(enlaser)
                except:
                    pass

        if self.top <= 0 :
            lasers.remove(self)
            print("Removed.")
            coord_pairs = [(-4.24,4.24),(-3.00,5.20),(-1.55,5.80),(0.00,6.00),(1.55,5.80),(3.00,5.20),(4.24,4.24)]

        
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
        self.heal = 0
    def update(self):
        global files_destroyed,enemy_lasers
        if self.hp <= 0:
            self.kill()
            files_destroyed = True
        red_rect = pygame.rect.Rect(self.rect.x + 10,self.rect.top - 25,50,5)
        green_rect = pygame.rect.Rect(self.rect.x + 10,self.rect.top - 25,(50/self.max_hp) * self.hp,5)
        pygame.draw.rect(screen,(255,0,0),red_rect)
        pygame.draw.rect(screen,(0,255,0),green_rect)
        for laser in enemy_lasers:
            if self.rect.colliderect(laser):
                self.hp -= laser.damage
                enemy_lasers.remove(laser)
        if self.hp < self.max_hp:
            self.hp += self.heal
class SymbolSprite(pygame.sprite.Sprite):
    def __init__(self, x,y,w,h,image_path):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image_path = image_path
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))


class UpgradeCard(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, typeofcard, upgradeitem, amounttoadd, lineupnum,upgrade_name = "Laser"):
        super().__init__() 
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.typeofcard = typeofcard
        self.upgradeitem = upgradeitem
        self.amounttoadd = amounttoadd
        self.x_values = [100, 400, 700]
        self.lineupnum = lineupnum
        self.upgrade_name = upgrade_name
        self.the_color = (255,255,255)
        
    def draw(self):
        
        self.x = self.x_values[self.lineupnum]
        card_rect = pygame.Rect(self.x, self.y, self.w, self.h)
        

        pygame.draw.rect(screen, (142, 142, 142), card_rect)


        symbol = self.typeofcard
        if symbol == "Triangle":
            symbol = SymbolSprite(self.x, self.y, 70, 70, "redtriangle.png")
            self.the_color = (255,0,0)
        elif symbol == "Square":
            symbol = SymbolSprite(self.x, self.y, 70, 70, "orangesquare.png")
            self.the_color = (255,165,0)
        elif symbol == "Circle":
            symbol = SymbolSprite(self.x, self.y, 50, 50, "yellowcircle.png")
            self.the_color = (255,255,0)
        elif symbol == "Pentagon":
            symbol = SymbolSprite(self.x, self.y, 50, 50, "greenpentagon.png")
            self.the_color = (0,255,0)
        elif symbol == "Hexagon":
            symbol = SymbolSprite(self.x, self.y, 50, 50, "bluehexagon.png")
            self.the_color = (0,0,255)

        symbol.rect.center = (card_rect.centerx, card_rect.top + 60)
        symbols.add(symbol)

        type_text = card_font.render(f"Item Upgrading : {self.upgrade_name}", True, self.the_color)
        stat_text = card_font.render(f"Stat Upgrading : {self.upgradeitem}", True, self.the_color)
        description = card_font.render(f"Upgrade {self.upgradeitem} by {self.amounttoadd}", True, self.the_color)
 
        text_rect = description.get_rect()
        stat_rect = stat_text.get_rect()
        type_rect = type_text.get_rect()
        
      
        text_rect.center = (card_rect.centerx, card_rect.bottom - 30) 
        stat_rect.center = (card_rect.centerx, card_rect.bottom - 65) 
        type_rect.center = (card_rect.centerx, card_rect.bottom - 100) 

    
        screen.blit(description, text_rect)
        screen.blit(stat_text, stat_rect)
        screen.blit(type_text, type_rect)
    def effect(self,pressed_key):
        ################## ALL CARD UPGRADES ############################
        if (self.lineupnum == 0 and  pressed_key == pygame.K_1) or (self.lineupnum == 1 and  pressed_key == pygame.K_2) or (self.lineupnum == 2 and pressed_key == pygame.K_3):
            if self.upgradeitem == "Cooldown":
                ship.max_cooldown += self.amounttoadd
                return True
            elif self.upgradeitem == "Ship Atk":
                ship.damage += self.amounttoadd
                return True
            elif self.upgradeitem == "Ship Speed":
                ship.speed += self.amounttoadd
                return True
            elif self.upgradeitem == "Tower Health":
                for file in files.sprites():
                    file.hp += self.amounttoadd
                    file.max_hp += self.amounttoadd
                return True
            elif self.upgradeitem == "Knockback":
                ship.knockback += self.amounttoadd
                return True
            elif self.upgradeitem == "Pierce":
                ship.pierce += self.amounttoadd
                card_options.remove(pierce_1)
                return True
            elif self.upgradeitem == "Dash":
                ship.can_dash = True
                ship.dash_damage += self.amounttoadd
                card_options.remove(dash_1)
                return True
            elif self.upgradeitem == "Heal":
                for file in files.sprites():
                    file.heal += self.amounttoadd
                card_options.remove(heal_1)
                return True
            elif self.upgradeitem == "Double":
                    ship.weapon_type = "Double"
                    try:
                        card_options.remove(shotgun_1)
                        card_options.remove(mines_1)
                        card_options.remove(double_1)
                    except:
                        pass
                    return True
            elif self.upgradeitem == "Shotgun":
                    ship.weapon_type = "Shotgun"
                    try:
                        card_options.remove(shotgun_1)
                        card_options.remove(mines_1)
                        card_options.remove(double_1)
                    except:
                        pass

                    return True
            elif self.upgradeitem == "Mines":
                    ship.weapon_type = "Mine"
                    try:
                        card_options.remove(shotgun_1)
                        card_options.remove(mines_1)
                        card_options.remove(double_1)
                    except:
                        pass
                    return True
        return False



class RecursionBoss(pygame.sprite.Sprite):
    def __init__(self, x,y,w,h,image_path,damage,hp):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.hp = 400
        self.image_path = image_path
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))
        self.damage = damage

        self.max_hp = 400
        self.create_child_cooldown = 300
        self.max_create_chile_cooldown = self.create_child_cooldown
        self.laser_cooldown = 125
        self.max_laser_cooldwon = self.laser_cooldown
        self.stage = "Base"
        self.direction = "None"
        self.speed = 2.4
        self.float_x = self.x
        self.float_y = self.y
        self.phase = "Movement"
        self.frame_shoot_delay = 5
        self.burst_count = 0
        self.max_burst_count = 4
        self.beam_count = 0
        self.max_beam_count = 20
        self.shoot_style = 2
        self.started_shooting = False
        self.giant_beam_count = 0 
        self.max_giant_beam_count = 3
        self.shots_fired = 0
    def update(self):
        global bugs
        if self.stage == "Moving":
            self.shoot_style = random.choice((1,2,3))
            if self.direction == "None":
                self.direction = random.choice(("Left","Right"))
            if self.direction == "Left":
                self.float_x -= self.speed
                self.rect.x = int(self.float_x)
                if self.rect.left <= 0:
                    self.direction = "Right"
            if self.direction == "Right":
                self.float_x += self.speed
                self.rect.x = int(self.float_x)
                if self.rect.right >= WIDTH:
                    self.direction = "Left"
            
            self.rect.y = int(self.float_y) 
        if self.hp <= 0:
            self.kill()
            bugs.empty()
            for i in range(90):
                particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-10,10),random.randint(-10,10)] , random.randint(4,20), (0,255,0)])
            for i in range(90):
                particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-10,10),random.randint(-10,10)] , random.randint(4,20), (0,0,255)])
            for i in range(90):
                particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-10,10),random.randint(-10,10)] , random.randint(4,20), (255,0,0)])

            for i in range(90):
                particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-10,10),random.randint(-10,10)] , random.randint(4,20), (128,0,128)])


        red_rect = pygame.rect.Rect(self.rect.centerx  - self.w // 2 + 50,self.rect.top - 25,150,5)
        green_rect = pygame.rect.Rect(self.rect.centerx  - self.w // 2 + 50,self.rect.top - 25,(150/self.max_hp) * self.hp,5)
        pygame.draw.rect(screen,(255,0,0),red_rect)
        pygame.draw.rect(screen,(0,255,0),green_rect)


    def check_for_collisions(self):
            global bugs,enemy_lasers
            memory_error_alive = any(bug.image_path == "memoryerror.png" for bug in bugs)
            if memory_error_alive == True:
                self.image.set_alpha(100)
                self.y_speed = 0
                self.max_creation_cooldown = 200
            else:
                self.max_creation_cooldown = 100
            for laser in lasers:
                memory_error_alive = any(bug.image_path == "memoryerror.png" for bug in bugs)
                if memory_error_alive == False or self.image_path == "memoryerror.png":
                    self.image.set_alpha(255)
                    if self.rect.colliderect(laser):
                        for i in range(2):
                            particles.append([[laser.centerx, laser.centery] , [random.randint(-2,2),random.randint(-2,2)] , random.randint(4,8), (0,255,0)])
                        for i in range(2):
                            particles.append([[laser.centerx, laser.centery] , [random.randint(-2,2),random.randint(-2,2)] , random.randint(4,8), (0,0,255)])
                        for i in range(2):
                            particles.append([[laser.centerx, laser.centery] , [random.randint(-2,2),random.randint(-2,2)] , random.randint(4,8), (255,0,0)])

                        for i in range(2):
                            particles.append([[laser.centerx, laser.centery] , [random.randint(-2,2),random.randint(-2,2)] , random.randint(4,8), (128,0,128)])
                        self.hp -= laser.damage
                        self.float_y -= laser.knockback
                        for bug in bugs:
                            if self.x == bug.x:
                                bug.float_y -= laser.knockback
                        if laser in lasers:
                            if laser.pierce <= 0 or self.hp > 0 :
                                lasers.remove(laser)
                            elif self.hp <= 0:
                                laser.pierce -= 1
                elif memory_error_alive == True:
                    self.image.set_alpha(100)
                    self.y_speed = 0
    def shoot(self):
        coord_pairs = [(-4.24,4.24),(-3.00,5.20),(-1.55,5.80),(0.00,6.00),(1.55,5.80),(3.00,5.20),(4.24,4.24)]
        self.speed = 0
        if self.hp <= 200:
            self.max_cooldown = 62.5
        if self.laser_cooldown <= 0:
            
            self.stage = "Shooting"
            if self.shoot_style == 1:
                for vx,vy in coord_pairs:
                    bullet = BossLaser(self.rect.x+147,self.rect.centery,vx ,vy,1,(255,0,0),speed=6)
                    boss_lasers.append(bullet)

                self.burst_count += 1

                if self.burst_count < self.max_burst_count:
                    self.laser_cooldown = self.frame_shoot_delay
                    if self.burst_count == 1:
                        if self.hp <= 499:
                            if self.hp <= 499 and self.shots_fired >= 3:
                                self.shots_fired = 0
                                for i in range(5):
                                    the_choice = random.choice(("exception.png",
                                                    "indentationerror.png",
                                                    "indexerror.png",
                                                    "memoryerror.png",
                                                    "importerror.png",
                                                    "brokenpipe.png","typeerror.png"))
                                    
                                    if the_choice == "exception.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,0,1,1,1)
                                                                        
                                    elif the_choice == "indentationerror.png":
                                            bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,1,1.5,3,0.8)

                                    elif the_choice == "indexerror.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,2,1,1,1,y_speed = 1.2)
                                    elif the_choice == "memoryerror.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,3,3,10,0.4,y_speed = 0.2)
                                    elif the_choice == "importerror.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,4,3,15,0.25,y_speed = 0.2)

                                    elif the_choice == "brokenpipe.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,5,3,1,0.4,y_speed = 0.5)

                                    elif the_choice == "typeerror.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,6,random.randint(1,7),random.randint(1,7),0.4,y_speed = random.uniform(0.5,1.5))
                                    bugs.add(bug)

                else:
                    self.burst_count = 0
                    self.laser_cooldown = self.max_laser_cooldwon
                    self.stage = "Moving"
                    self.shots_fired += 1
            elif self.shoot_style == 2:
                self.stage = "Shooting"
                bullet1 = BossLaser(self.rect.centerx - 22,self.rect.centery,0,8,1,(255,255,0),9)
                bullet2 = BossLaser(self.rect.centerx + 22,self.rect.centery,0,8,1,(255,255,0),9)
                boss_lasers.append(bullet1)
                boss_lasers.append(bullet2)

                self.beam_count += 1

                if self.beam_count < self.max_beam_count:
                    self.laser_cooldown = 1
                    if self.beam_count == 1:
                        if self.hp <= 499  and self.shots_fired >= 3:
                            for i in range(5):
                                the_choice = random.choice(("exception.png",
                                                "indentationerror.png",
                                                "indexerror.png",
                                                "memoryerror.png",
                                                "importerror.png",
                                                "brokenpipe.png","typeerror.png"))
                                
                                if the_choice == "exception.png":
                                    bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,0,1,1,1)
                                                                    
                                elif the_choice == "indentationerror.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,1,1.5,3,0.8)

                                elif the_choice == "indexerror.png":
                                    bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,2,1,1,1,y_speed = 1.2)
                                elif the_choice == "memoryerror.png":
                                    bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,3,3,10,0.4,y_speed = 0.2)
                                elif the_choice == "importerror.png":
                                    bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,4,3,15,0.25,y_speed = 0.2)

                                elif the_choice == "brokenpipe.png":
                                    bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,5,3,1,0.4,y_speed = 0.5)

                                elif the_choice == "typeerror.png":
                                    bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,6,random.randint(1,7),random.randint(1,7),0.4,y_speed = random.uniform(0.5,1.5))
                                bugs.add(bug)
                    
                else:
                    self.beam_count = 0
                    self.laser_cooldown = self.max_laser_cooldwon
                    self.stage = "Moving"
                    self.shots_fired += 1
            elif self.shoot_style == 3:
                bullet1 = BossLaser(random.randint(self.rect.x,self.rect.right-24),self.rect.centery,0,8,10,(255,255,0),9,w=48,h=48)
                boss_lasers.append(bullet1)

                self.giant_beam_count += 1

                if self.giant_beam_count < self.max_giant_beam_count:
                    self.laser_cooldown = 30
                else:
                    self.laser_cooldown = self.max_laser_cooldwon
                    self.giant_beam_count = 0
                    self.stage = "Moving"
                    self.shots_fired += 1

        
        elif self.laser_cooldown > 0:
            self.laser_cooldown -= 1


        

        self.speed = 2.4



    
        

class BossLaser(pygame.rect.Rect):
    def __init__(self,x,y,xv,yv,damage,color,speed,w=6,h=6):
        super().__init__(x,y,w,h)
        self.x = x
        self.y = y
        self.xv = xv
        self.yv = yv
        self.w = w
        self.h = h
        self.damage = damage
        self.color = color
        self.speed = speed
        self.float_x = x
        self.float_y = y
        self.knockback = 0
        self.pierce = 0 
    def update(self):
        global boss_lasers,ship,lasers
        self.float_x += self.xv
        self.float_y += self.yv

        self.x = int(self.float_x)
        self.y = int(self.float_y)

        if (self.top < 0 or       
        self.bottom > HEIGHT or     
        self.left > 1280 or  
        self.right < 0):       
        
            try:
                boss_lasers.remove(self)
                
            except:
                try:
                    lasers.remove(self)
                except:
                    pass

        if self.colliderect(ship.rect) and self.color == (255,0,0):
            try:
                boss_lasers.remove(self)
                ship.hp -= self.damage
            except:
                try:
                    lasers.remove(self)
                except:
                    pass

    
    def draw(self):
        laser = pygame.rect.Rect(self.x,self.y,self.w,self.h)
        pygame.draw.rect(screen,self.color,laser)

pro_ships = pygame.sprite.Group()

ship = Ship(100,100,27,33,"ship.png",1,10)       
    
boss_lasers = []
enemy_lasers = []
keys = pygame.key.get_pressed()
mines = pygame.sprite.Group()
files = pygame.sprite.Group()
symbols = pygame.sprite.Group()
main = FileTower(WIDTH//2 - 40 , HEIGHT - 130,80,120,"main.png",10)
server = FileTower(WIDTH//2 - 140 , HEIGHT - 130,80,120,"server.png",5)
client = FileTower(WIDTH//2 + 60 , HEIGHT - 130,80,120,"client.png",5)
image_folder = FileTower(WIDTH//2 + 160 , HEIGHT - 120,120,110,"game_sprites.png",5)
spritesheets = FileTower(WIDTH//2 - 280 , HEIGHT - 120,120,110,"spritesheets.png",5)
devlog = FileTower(WIDTH//2 - 380 , HEIGHT - 130,80,120,"devlog.png",5)
error_log = FileTower(WIDTH//2 + 300 , HEIGHT - 130,100,120,"error_log.png",5)
readme = FileTower(WIDTH//2 - 480 , HEIGHT - 130,80,120,"readme.png",5)
gitignore = FileTower(WIDTH//2 + 410 , HEIGHT - 130,80,120,"gitignore.png",5)
cards = []
cooldown_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Square","Cooldown",-((ship.max_cooldown / 15) * 0.5) ,0)
################ ALL CARDS ####################################
atk_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Square","Ship Atk",+0.5,1)
ship_speed_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Triangle","Ship Speed",+1,2,upgrade_name="Ship")
tower_hp_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Circle","Tower Health",+2.5,2,upgrade_name="File Towers")
pierce_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Pentagon","Pierce",+1,2,upgrade_name="Laser")
dash_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Triangle","Dash",+3,2,upgrade_name="Ship")
heal_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Circle","Heal",+0.00083,2,upgrade_name="File Tower")
double_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Hexagon","Double",+1,2,upgrade_name="Weapons")
shotgun_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Hexagon","Shotgun",+1,2,upgrade_name="Weapons")
mines_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Hexagon","Mines",+1,2,upgrade_name="Weapons")
###################################################################
card_options = [cooldown_1,atk_1,ship_speed_1,tower_hp_1]
files_destroyed = False
files.add(readme)
files.add(devlog)
files.add(spritesheets)
files.add(server)
files.add(main)
files.add(client)
files.add(image_folder)
files.add(error_log)
files.add(gitignore)

ship.rect.x = WIDTH // 2 - (ship.w//2)
ship.rect.y = 400
pro_ships.add(ship)
lasers = []

mouse_pos = ()
mouse_pressed = False

########################ALL LEVELS######################333333
current_level = 19
level1 = [["e","e","e","e","e"],["e","e","e","e","e"],["e","e","e","e","e"],["e","e","e","e","e"]]
level2 = [["e","e","e","e","e","e","e"],["e","e","e","e","e","e","e"],["e","e","e","e","e","e","e"],["e","e","e","e","e","e","e"]]
level3 = [["i","i","i","i","i","i"],["e","e","e","e","e","e",],["i","i","i","i","i","i"],["e","e","e","e","e","e",]]
level4 = [["e","e","e","e","e","e"],["e","e","e","e","e","e",],["i","i","i","i","i","i"],["i","i","i","i","i","i",],["i","i","i","i","i","i",]]
level5 = [["i","i","i","i","i","i"],["e","e","e","e","e","e",],["e","e","e","e","e","e",],["x","x","x","x","x","x"]]
level6 = [["i","i","i","i","i","i"],["x","x","x","x","x","x",],["e","e","e","e","e","e",],["x","x","x","x","x","x"]]
level7 = [["i","i","i","i","i","i","i","i","i","i","i"],["i","i","i","i","i","i","i","i","i","i"]]
level9 = [["e","e","x","x","e","e","","","","e","e","x","x","e","e"],["i","i","i","i","i","i","","","","i","i","i","i","i","i"]]
level8 = [["i","e","x","i","e","x","i","e","x","i","e","x"],["i","e","x","i","e","x","i","e","x","i","e","x"],["i","e","x","i","e","x","i","e","x","i","e","x"]]
level10 = [["e","e","e","m","m","e","e","e"],["x",'i',"x",'i',"x",'i',"x",'i'],['e','e','e','e','e','e','e','e']]
level11 = [["m","e","e","e","e","e","e","m"],["x",'m',"x",'i',"x",'i',"x",'m'],['e','e','e','m','m','e','e','e']]
level12 = [["x","x","x"],["m","m","m"],["x","x","x"],["x","x","x"],["x","x","x"],["x","x","x"],["x","x","x"],]
level13 = [['x','x','x','x','x'],['x','x','x','x','x'],['p','p','p','p','p']]
level14 = [['p','p','p','p','p'],['e','e','e','e','e'],['e','e','e','e','e'],[""],[""],["i","i","i","i","i"]]
level15 = [["x","x","x","x","x","x","x","x"],["x","x","x","x","x","x","x","x"],["x","x","x","x","x","x","x","x"],["x","x","x","x","x","x","x","x"]]
level16 = [['b','b','b','b','b','b','b'],['i','i','i','i','i','i','i']]
level17 = [["","m","m","m",""],["b","b","b","b","b"],["b","b","b","b","b"]]
level18 = [["b","b","b","b","b"],["b","b","b","b","b"],["b","b","b","b","b"],["b","b","b","b","b"]]
level19 = [["b","b","b","b","b"],["b","b","b","b","b"],["t","t","t","t","t"]]
level20 = [["BOSS"]]

level21 = [["t","t","t","t","t"],["t","t","t","t","t"],["t","t","t","t","t"]]
level_list = [level1,level2,level3,level4,level5,level6,level7,level8,level9,level10,level11,level12,level13,level14,level15,level16,level17,level18,level19,level20,level21]
level = level_list[current_level-1]
###########################################################################################################33










startx = (WIDTH // 2) - 75
starty = 0
rowindex = 0
colindex = 0
spacer = 30
startx = (WIDTH // 2) - ((len(level[0]) / 2) * spacer)
card_was_chosen = True
cards_were_shuffled = False
bugsnum = 0
bugs = pygame.sprite.Group()

bosses = pygame.sprite.Group()
add_pierce_possible = True
dash_possible = 2
heal_possible = True

############# More start menu stuff ###############

menu_buttons = [
    MenuButton("Start Programming (Play Game)",WIDTH//2,320,320,55,1),
    MenuButton("Read README.md (Tutorial)", WIDTH // 2 , 410, 320,55, 2),
    MenuButton("View Error Log (See Enemy Stats)", WIDTH // 2 , 500,320,55,3)
]

back_button = MenuButton("Return to IDE (Start Menu)" ,WIDTH//2 + 290 , 205,320,55,0)



lives_left = 3

current_enemy = 0

full_title = "CODE INVADERS"
current_typed = ""
typed_frame = 0
type_letter = 0
typer_speed = 10



ship_image = pygame.image.load("ship.png").convert_alpha()
ship_image = pygame.transform.scale(ship_image,(27,33))


async def main():
    ################# GLOBAL VARIABLES :0 #######################################
    global shotgun_1,double_1,mines_1,lives_left,ship_image,boss_lasers,keys,current_enemy,full_title,current_typed,typed_frame,type_letter,typer_speed,menu_buttons,back_button,game_state,mouse_pressed,mouse_pos,heal_1,heal_possible,server,enemy_lasers,particles,dash_possible,add_pierce_possible,ship,pierce_1,files_destroyed,bugsnum,cards_were_shuffled,card_options,card_was_chosen,symbols,current_level,keys,running,files,pro_ships,lasers,level_list,level,startx,starty,rowindex,colindex,spacer,bugs
    if current_level == 20:
        lives_left = 3
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if game_state == 3:
                    if event.key == pygame.K_RIGHT:
                        current_enemy += 1
                        if current_enemy > 5:
                            current_enemy = 0
                        
                    elif event.key == pygame.K_LEFT:
                        current_enemy -= 1
                        if current_enemy < -6:
                            current_enemy = 5
                for card  in cards:
                    if card.effect(event.key):
                        print("Upgrade Completed!")
                        card_was_chosen = True
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button:
                if game_state == 0:
                    mouse_pressed = pygame.mouse.get_pressed()
                    for btn in menu_buttons:
                        if btn.check_clicks(mouse_pos,mouse_pressed):
                            game_state = btn.target_state
                elif game_state == 2 or game_state == 3:
                     if back_button.check_clicks(mouse_pos,mouse_pressed):
                        game_state = back_button.target_state

        screen.fill(screen_color)
        keys = pygame.key.get_pressed()
        if game_state == 0:
            if type_letter < len(full_title):
                typed_frame += 1

                if typed_frame >= typer_speed:
                    current_typed += full_title[type_letter]
                    type_letter += 1
                    typed_frame = 0

            title_surface = title_font.render(current_typed,True,(0,255,80))
            screen.blit(title_surface,title_surface.get_rect(center = (WIDTH // 2 ,180)))
            for btn in menu_buttons:
                btn.draw(screen,ui_font,mouse_pos)

        elif game_state == 2:
            tutorial_title = subtitle_font.render("README.md (How to play)",True,(0,180,255))
            screen.blit(tutorial_title,tutorial_title.get_rect(center = (WIDTH//2, 100)))
            pygame.draw.rect(screen, (20, 20, 25), (70, 160, 900, 420), border_radius=24)
            pygame.draw.rect(screen, (0, 255, 0), (70, 160, 900, 420), width=8, border_radius=12)

            tutorial_text = [
                "Controls : WASD or Arrow Keys to Control Ship Movement",
                "Controls : Spacebar, Q, or E to fire lasers",
                "Controls : Press Right Shift to Dash (Once Unlocked)",
                "Goal : Protect your code files at the bottom from the endless waves of bugs (like in real programming...)!\n If they reach 0 HP , the game is over!",
                "Upgrades : After you clear a wave of bugs, you get to choose one of 2-3 upgrade cards to upgrade your stats.\n Press 1 to pick card 1, press 2 to pick card 2, and 3 to pick card 3",
                "Upgrades : Some upgrades can only be unlocked after using others (ex. Pierce need ATK+ and Cooldown+)",
                "Waves : There are 16 Waves (So Far). Beat all of them to finally finish your program :)",
                "IRL : If you like the game , play the real version... by learning Python! (Or just play the game again...)"
            ]

            for i, line in enumerate(tutorial_text):
                txt = small_font.render(line,True,(240,240,240))
                screen.blit(txt,(100,200 + i * 45))
            back_button.draw(screen, ui_font, mouse_pos)
            if back_button.check_clicks(mouse_pos,mouse_pressed):
                game_state = back_button.target_state

        elif game_state == 3:
            error_log_title = subtitle_font.render("SYSTEM ERROR LOG \n(Enemy Index)",True,(0,255,100))
            screen.blit(error_log_title,error_log_title.get_rect(center = (WIDTH//2 , 60)))
            continue_text = ui_font.render("Use Left and Right Arrows to scroll through enemies.",True,(0,255,100))
            error_list = [ 

                "Exception : The basic enemy. HP : 1, ATK : 1, Speed : 0.5",
                "IndentationError : A stronger enemy. HP : 3, ATK : 1.5, Speed : 0.5",
                "IndexError : A fast, rusher enemy. HP : 1 , ATK : 1, Speed : 1",
                "MemoryError : A Highly Tanky spotlight enemy. You have to defeat this error to be able to attack any other one.\n HP : 10 , ATK : 3 , Speed : 0.5",
                "ImportError : A Highly Tanky Spawner error. It spawns Exceptions every few seconds. HP : 15 , ATK : 5, Speed : 0.5",
                "BrokenPipeError : A fragile shooter error. It shoots projectiles straight toward you and your files. HP : 1 , ATK : 0.5 , Speed : 0.5"

            ]

            image_list = [
                "exception.png",
                "indentationerror.png",
                "indexerror.png",
                "memoryerror.png",
                "importerror.png",
                "brokenpipe.png"
            ]


            text = ui_font.render(error_list[int(current_enemy)],True,(255,255,255))
            image = pygame.image.load(image_list[int(current_enemy)]).convert_alpha()
            image = pygame.transform.scale(image,(96,96))
            screen.blit(text,text.get_rect(center = (WIDTH//2 , 400)))
            screen.blit(image,(WIDTH//2 - (image.width //2),200))
            screen.blit(continue_text,continue_text.get_rect(center = (WIDTH//2 , 350)))
            if back_button.check_clicks(mouse_pos,mouse_pressed):
                game_state = back_button.target_state
            # if keys[pygame.K_RIGHT]:
            #     current_enemy += 0.25
            #     if current_enemy > 5:
            #         current_enemy = 0
            # elif keys[pygame.K_LEFT]:
            #     current_enemy -= 0.25
            back_button.draw(screen, ui_font, mouse_pos)
        elif game_state == 1:
            for i in range(lives_left):
                screen.blit(ship_image,(i*30,5))
            if (not card_options.__contains__(pierce_1)) and ship.damage > 1 and ship.cooldown < 15 and add_pierce_possible:
                card_options.append(pierce_1)
                add_pierce_possible = False
            if ship.speed >= 8 and dash_possible > 0:
                    card_options.append(dash_1)
                    card_options.append(dash_1)
                    dash_possible = 0
            if server.max_hp > 5 and heal_possible == True:
                card_options.append(heal_1)
                card_options.append(heal_1)
                heal_possible = False
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            pro_ships.draw(screen)
            bugs.draw(screen)
            if not current_level == 20:
                files.draw(screen)

            mouse_state = pygame.mouse.get_pressed()
            if mouse_state[0] and ship.weapon_type == "Mine":
                    if ship.cooldown <= 0 and card_was_chosen:
                        print("Steve")
                        mine = Mine(ship.rect.x,ship.rect.y,8,8,6,0,0,6,mouse_pos[0],mouse_pos[1])
                        mines.add(mine)
                        ship.cooldown = ship.max_cooldown
                    
            if not files_destroyed:
                mines.draw(screen)
                mines.update()
                for file in files:
                    if current_level != 20:
                        file.update()
                for laser in lasers:
                    laser.draw()
                    laser.update()
                    print(ship.rect.y - laser.y)
                    if ship.weapon_type == "Shotgun":
                        if laser.y < ship.rect.y - 150:
                            try:
                                lasers.remove(laser)
                                print("Wow")
                            except:
                                pass
                for ship in pro_ships:
                    ship.move()
                    ship.shoot()
                    ship.update()
                previous_bugsnum = bugsnum
                if card_was_chosen == True:
                    bugsnum = 0
                for bug in bugs:
                    if bug.image_path != "recursionboss.png":
                        bug.move()
                        bug.check_for_collisions()
                    bugsnum += 1
                for card in cards:
                    card.draw()
                for enlaser in enemy_lasers:
                    enlaser.draw()
                    enlaser.update()
                
                symbols.draw(screen)

                if bugsnum == 0 :
                    bugs.empty()
                    lasers.clear()
                    enemy_lasers.clear()
                    if card_was_chosen == True and previous_bugsnum > 0:
                        card_was_chosen = False
                        cards_were_shuffled = False
                    if not cards_were_shuffled:
                        card_options_current = card_options[:]
                        if current_level != 20:
                            card1= random.choice(card_options_current)
                            card_options_current.remove(card1)
                            card2= random.choice(card_options_current)
                            card_options_current.remove(card2)
                            card3= random.choice(card_options_current)
                            card_options_current.remove(card3)
                        else:
                            card1= shotgun_1
                            card2= double_1
                            card3= mines_1
                        card1.lineupnum = 0
                        card2.lineupnum = 1
                        card3.lineupnum = 2
                        cards.append(card1)
                        cards.append(card2)
                        cards.append(card3)
                        cards_were_shuffled = True
                    if card_was_chosen == True:
                        cards.clear()
                        symbols.empty()
                    if card_was_chosen == True and current_level < len(level_list):
                        current_level += 1
                        level = level_list[current_level-1]
                        startx = (WIDTH // 2) - ((len(level[0]) / 2) * spacer)
                        colindex = 0
                        for row in level:
                            for exception in row:
                                if exception == "e":
                                    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,0,1,1,1)
                                
                                elif exception == "i":
                                    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,1,1.5,3,0.8)

                                elif exception == "x":
                                    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,2,1,1,1,y_speed = 1.2)
                                elif exception == "m":
                                    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,3,3,10,0.4,y_speed = 0.2)
                                elif exception == "p":
                                    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,4,3,15,0.25,y_speed = 0.2)

                                elif exception == "b":
                                    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,5,3,1,0.4,y_speed = 0.5)

                                elif exception == "t":
                                    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,6,random.randint(1,7),random.randint(1,7),0.4,y_speed = random.uniform(0.5,1.5))
                                elif exception == "BOSS":
                                    bug = RecursionBoss(WIDTH//2 - 150,50,240,120,"recursionboss.png",1,100)
                                    bosses.add(bug)
                                
                                bugs.add(bug)
                                rowindex += 1
                            colindex -= spacer
                            rowindex = 0
                    elif current_level >= len(level_list):
                        win  = title_font.render(f"YOU WIN \n(for now)",True , (0,255,0))
                        screen.blit(win,(WIDTH//2 - 300,HEIGHT//2  - 100))
                    else:
                        pass  

            bosses.draw(screen)
            bosses.update()
            for laser in boss_lasers:
                laser.draw()
                laser.update()
            for boss in bosses:
                boss.check_for_collisions()
                boss.shoot()
            for particle in particles[:]:
                particle[0][0] += particle[1][0] # Adding the x velocity to the x
                particle[0][1] += particle[1][1] # Adding the y velocity to the y
                particle[2] -= 0.1 # Decrease particle size
                rect_particle = pygame.rect.Rect(particle[0][0],particle[0][1],particle[2],particle[2])
                try:
                    color = particle[3]
                    pygame.draw.rect(screen,particle[3],rect_particle)
                except:
                    pygame.draw.rect(screen,(0,200,100),rect_particle)

                if particle[2] <= 0:
                    particles.remove(particle) 



            if files_destroyed or lives_left <= 0:
                win  = title_font.render(f"YOU LOSE...",True , (255,0,0))
                screen.blit(win,win.get_rect(center = (WIDTH//2 , 200)))
                current_level = 0
                ship = Ship(100,100,27,33,"ship.png",1,1)
        pygame.display.flip()
        await asyncio.sleep(0)
asyncio.run(main())