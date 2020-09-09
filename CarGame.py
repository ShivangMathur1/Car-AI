import pygame
from math import sin, radians, degrees, copysign
from pygame.math import Vector2
import sys

pygame.init()
pygame.mixer.init()
pygame.key.set_repeat(20, 20)
screen = pygame.display.set_mode([966, 768])

screen.fill([255, 255, 255])

pygame.mixer.music.load("dejavu.mp3")
pygame.mixer.music.play(-1)


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
        self.rotated = pygame.transform.rotate(car.image, car.angle)
        self.rect = self.rotated.get_rect()
        surface.blit(self.rotated, self.pos - (self.rect.width / 2, self.rect.height / 2))


car = Car([30, 30], "car.png", 0)
clock = pygame.time.Clock()

# Event Loop
while True:
    dt = clock.get_time() / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        if car.velocity.x < 0:
            car.acceleration = car.decel
        else:
            car.acceleration  = car.maxAccel
    elif keys[pygame.K_DOWN]:
        if car.velocity.x > 0:
            car.acceleration = -car.decel
        else:
            car.acceleration = -car.maxAccel
    elif keys[pygame.K_SPACE]:
        if car.velocity.x != 0:
            car.acceleration = copysign(car.maxAccel, -car.velocity.x)
    else:
        if abs(car.velocity.x) > dt * car.freeDecel:
            car.acceleration = -copysign(car.freeDecel, car.velocity.x)
        else:
            if dt != 0:
                car.acceleration = -car.velocity.x / dt
    car.acceleration = max(-car.maxAccel, min(car.acceleration, car.maxAccel))

    if keys[pygame.K_RIGHT]:
        car.steering -= 30 * dt
    elif keys[pygame.K_LEFT]:
        car.steering += 30 * dt
    else:
        car.steering = 0
    car.steering = max(-car.maxSteer, min(car.steering, car.maxSteer))

    car.update(dt)

    screen.fill([255, 255, 255])
    car.display(screen)
    pygame.display.flip()
    pygame.time.delay(40)
    print(car.velocity)
    clock.tick(60)
