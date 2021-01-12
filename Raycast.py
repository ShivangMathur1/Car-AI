import pygame
from pygame import Vector2
import sys
from math import cos, sin, radians
from random import randint


class Boundary(pygame.sprite.Sprite):
    def __init__(self, pointA, pointB, surface, color=None):
        pygame.sprite.Sprite.__init__(self) 
        self.a = pointA
        self.b = pointB
        self.surface = surface
        if color is None:
            color = [255, 255, 255]
        pygame.draw.line(self.surface, color, self.a, self.b)


class Ray:
    def __init__(self, position, direction):
        self.pos = position
        self.dir = direction
        self.intersection = None

    def point(self, newDir):
        self.dir = newDir - self.pos
        self.dir.scale_to_length(20)

    def show(self, surface, color=None):
        if color is None:
            color = [255, 255, 255]
        pygame.draw.line(surface, color, self.pos, self.pos + self.dir)

    def raycast(self, wall):
        x1 = wall.a.x
        y1 = wall.a.y
        x2 = wall.b.x
        y2 = wall.b.y

        x3 = self.pos.x
        y3 = self.pos.y
        x4 = self.pos.x + self.dir.x
        y4 = self.pos.y + self.dir.y

        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if den == 0:
            return None, None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den

        if 0 < t < 1 and u > 0:
            self.intersection = Vector2()
            self.intersection.x = float(x1 + t * (x2 - x1))
            self.intersection.y = float(y1 + t * (y2 - y1))
            return self.intersection, u
        else:
            return None, None


class Particle:
    def __init__(self, position, angle=0, rayCount=8, color=None):
        if color is None:
            color = [255, 255, 255]
        self.pos = position
        self.angle = angle
        self.color = color
        self.rays = []
        self.step = 360//rayCount
        for i in range(0, 360, self.step):
            self.rays.append(Ray(self.pos, 20 * Vector2(cos(radians(i)), sin(radians(i)))))

    def show(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), 4)

    def see(self, surface, walls, render):

        distances = []
        for ray in self.rays:
            dmin = 1000000000
            pt = None
            for wall in walls:
                p, d = ray.raycast(wall)
                if d is not None and d < dmin:
                    dmin = d
                    pt = p

            if pt is not None and render:
                pygame.draw.circle(surface, self.color, [int(pt.x), int(pt.y)], 4)
                pygame.draw.line(surface, self.color, self.pos, pt)
            distances.append(dmin)
        return distances

    def move(self, pos=None, angle=None):
        if pos == None:
            pos = self.pos
        if angle == None:
            angle = self.angle

        self.pos = pos
        for i in self.rays:
            i.pos = self.pos
        self.angle = angle
        for i in range(0, 360, self.step):
            self.rays[i//self.step].dir = Vector2(cos(radians(i - angle)), sin(radians(i - angle)))


if __name__ == '__main__':
    pygame.init()

    width = 1000
    height = 500
    screen = pygame.display.set_mode([width, height])

    walls = []
    for i in range(5):
        x1 = randint(0, width)
        y1 = randint(0, height)
        x2 = randint(0, width)
        y2 = randint(0, height)
        walls.append(Boundary(Vector2(x1, y1), Vector2(x2, y2)))


    walls.append(Boundary(Vector2(width, 0), Vector2(width, height)))
    walls.append(Boundary(Vector2(0, 0), Vector2(0, height)))
    walls.append(Boundary(Vector2(0, 0), Vector2(width, 0)))
    walls.append(Boundary(Vector2(0, height), Vector2(width, height)))

    p = Particle(Vector2((250, 250)))

    # Event Loop------------------------------------------------------------------------------------------------------------
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEMOTION:
                p.move(pos=Vector2(pygame.mouse.get_pos()))
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_RIGHT]:
                    p.move(angle=30)

        screen.fill([0, 0, 0])
        for i in walls:
            i.show(screen)
        p.show(screen)
        d = p.see(screen, walls, render=True)
        print(d)
        pygame.display.flip()
