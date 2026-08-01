import pygame
import random
import math
pygame.init()
WIDTH , HEIGHT = 1000 ,600
FPS = 60
screen = pygame.display.set_mode((WIDTH,HEIGHT))
global_trail_surf = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
running = True
clock = pygame.time.Clock()
screen_color = (0,0,0) 

class Ball:
    def __init__(self,color,x,y,radius,speed):
        self.color = color
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed

        self.angle = random.uniform(0,2* math.pi)
        self.vx = self.speed * math.cos(self.angle)
        self.vy = self.speed * math.sin(self.angle)
        self.history = []
        self.max_trail_len = 12
    
    def move(self):
        self.history.append((int(self.x),int(self.y)))
        if len(self.history) > self.max_trail_len:
            self.history.pop(0)
        
        self.x += self.vx
        self.y += self.vy

        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx *= -1

        elif self.x + self.radius >= WIDTH:
            self.x = WIDTH - self.radius
            self.vx *= -1

        if self.y - self.radius >= HEIGHT:
            self.y = HEIGHT - self.radius
            self.vy *= -1

        elif self.y - self.radius <= 0:
            self.y = self.radius
            self.vy *= -1

    def draw(self,screen=screen):

        for i, pos in enumerate(self.history):
            factor = i / len(self.history)

            alpha = int(factor * 180)
            trail_color = (self.color[0],self.color[1],self.color[2],alpha)
            trail_radius = int(self.radius * (0.4 + 0.6 * factor))
            pygame.draw.circle(global_trail_surf,trail_color,pos,trail_radius)


        
        pygame.draw.circle(screen,self.color,(int(self.x),int(self.y)),self.radius)



balls = []
for i in range(100):
    basic = Ball((255,0,0),random.randint(30,WIDTH - 30),random.randint(30,HEIGHT-30),10,6)
    balls.append(basic)

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(screen_color)
    screen.blit(global_trail_surf, (0,0))
    global_trail_surf.fill((0,0,0,0))

    for ball in balls:
        ball.draw()
        ball.move()

    pygame.display.flip()