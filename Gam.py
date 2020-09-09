import pygame
from math import sin, radians, degrees, copysign
from pygame.math import Vector2
import sys
from Data.Raycast import Boundary, Particle


class Game:
    def __init__(self):
        # pygame initialisations
        pygame.init()
        pygame.mixer.init()
        pygame.key.set_repeat(20, 20)
        pygame.mixer.music.load("dejavu.mp3")
        pygame.mixer.music.play(-1)

        self.run = True
        self.width = 966
        self.height = 768
        self.screen = pygame.display.set_mode([self.width, self.height])
        self.screen.fill([0, 0, 0])

        # Objects
        self.car = Car([30, 30], "car.png", 0)
        self.walls = []
        self.walls.append(Boundary(Vector2(self.width, 0), Vector2(self.width, self.height)))
        self.walls.append(Boundary(Vector2(0, 0), Vector2(0, self.height)))
        self.walls.append(Boundary(Vector2(0, 0), Vector2(self.width, 0)))
        self.walls.append(Boundary(Vector2(0, self.height), Vector2(self.width, self.height)))

    def step(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False

        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP]:
            if self.car.velocity.x < 0:
                self.car.acceleration = self.car.decel
            else:
                self.car.acceleration = self.car.maxAccel
        elif keys[pygame.K_DOWN]:
            if self.car.velocity.x > 0:
                self.car.acceleration = -self.car.decel
            else:
                self.car.acceleration = -self.car.maxAccel
        elif keys[pygame.K_SPACE]:
            if self.car.velocity.x != 0:
                self.car.acceleration = copysign(self.car.maxAccel, -self.car.velocity.x)
        else:
            if abs(self.car.velocity.x) > dt * self.car.freeDecel:
                self.car.acceleration = -copysign(self.car.freeDecel, self.car.velocity.x)
            else:
                if dt != 0:
                    self.car.acceleration = -self.car.velocity.x / dt
        self.car.acceleration = max(-self.car.maxAccel, min(self.car.acceleration, self.car.maxAccel))

        if keys[pygame.K_RIGHT]:
            self.car.steering -= 30 * dt
        elif keys[pygame.K_LEFT]:
            self.car.steering += 30 * dt
        else:
            self.car.steering = 0
        self.car.steering = max(-self.car.maxSteer, min(self.car.steering, self.car.maxSteer))

        self.car.update(dt)
        print(dt)
        self.screen.fill([0, 0, 0])

        for i in self.walls:
            i.show()
        self.car.display(self.screen)
        pygame.display.flip()


class Car(pygame.sprite.Sprite):
    def __init__(self, pos, image, angle=0.0):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(image)
        self.rotated = self.image
        self.rect = self.rotated.get_rect()
        self.pos = Vector2(pos[0], pos[1])
        self.velocity = Vector2(0.0, 0.0)
        self.angle = angle
        self.length = 4
        self.acceleration = 0.0
        self.steering = 0.0

        self.maxVelocity = 320
        self.decel = 320
        self.freeDecel = 80
        self.maxAccel = 160
        self.maxSteer = 4

    def update(self, dt):
        self.velocity += (self.acceleration * dt, 0)
        self.velocity.x = max(-self.maxVelocity, min(self.velocity.x, self.maxVelocity))

        if self.steering:
            radius = self.length / sin(radians(self.steering))
            angularVelocity = self.velocity.x / radius
        else:
            angularVelocity = 0

        self.pos += self.velocity.rotate(-self.angle) * dt
        self.angle += degrees(angularVelocity) * dt

    def display(self, surface):
        self.rotated = pygame.transform.rotate(self.image, self.angle)
        self.rect = self.rotated.get_rect()
        surface.blit(self.rotated, self.pos - (self.rect.width / 2, self.rect.height / 2))


# car = Car([30, 30], "car.png", 0)
# clock = pygame.time.Clock()

# # Event Loop
# while True:
#     dt = clock.get_time() / 1000
#
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             sys.exit()
#
#     keys = pygame.key.get_pressed()
#     if keys[pygame.K_UP]:
#         if car.velocity.x < 0:
#             car.acceleration = car.decel
#         else:
#             car.acceleration  = car.maxAccel
#     elif keys[pygame.K_DOWN]:
#         if car.velocity.x > 0:
#             car.acceleration = -car.decel
#         else:
#             car.acceleration = -car.maxAccel
#     elif keys[pygame.K_SPACE]:
#         if car.velocity.x != 0:
#             car.acceleration = copysign(car.maxAccel, -car.velocity.x)
#     else:
#         if abs(car.velocity.x) > dt * car.freeDecel:
#             car.acceleration = -copysign(car.freeDecel, car.velocity.x)
#         else:
#             if dt != 0:
#                 car.acceleration = -car.velocity.x / dt
#     car.acceleration = max(-car.maxAccel, min(car.acceleration, car.maxAccel))
#
#     if keys[pygame.K_RIGHT]:
#         car.steering -= 30 * dt
#     elif keys[pygame.K_LEFT]:
#         car.steering += 30 * dt
#     else:
#         car.steering = 0
#     car.steering = max(-car.maxSteer, min(car.steering, car.maxSteer))
#
#     car.update(dt)
#     print(dt)
#     screen.fill([255, 255, 255])
#     car.display(screen)
#     pygame.display.flip()
#     pygame.time.delay(40)
#     clock.tick(60)

if __name__ == "__main__":
    clock = pygame.time.Clock()
    game = Game()

    while game.run == True:
        dt = clock.get_time() / 1000
        game.step(dt)
        pygame.time.delay(40)
        clock.tick(60)
    sys.exit()
