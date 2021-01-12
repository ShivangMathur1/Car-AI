import sys
from math import copysign, degrees, radians, sin
import pygame
from pygame.math import Vector2
from pygame.transform import threshold

from Raycast import Boundary, Particle


class Game:
    def __init__(self, maps):
        # pygame initialisations
        pygame.init()
        #pygame.mixer.init()
        pygame.key.set_repeat(20, 20)
        #pygame.mixer.music.load("dejavu.mp3")
        #pygame.mixer.music.play(-1)

        self.done = False
        self.width = 966
        self.height = 768
        self.screen = pygame.display.set_mode([self.width, self.height])
        self.screen.fill([0, 0, 0])

        # Objects: Car, Track
        self.car = Car([100, 50], "car.png", 0)
        self.walls = []
        self.tracks = []
        self.gates = RewardGates(maps, self.height, self.width)
        for map in maps:
            self.tracks.append(Track(map[1:], map[0], self.height, self.width, self.walls))
        

    def step(self, dt, actions):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        self.actions = actions

        if actions[0] == 1:
            if self.car.velocity.x < 0:
                self.car.acceleration = self.car.decel
            else:
                self.car.acceleration = self.car.maxAccel
        elif actions[0] == -1:
            if self.car.velocity.x > 0:
                self.car.acceleration = -self.car.decel
            else:
                self.car.acceleration = -self.car.maxAccel
        elif actions[1] == 1:
            if self.car.velocity.x != 0:
                self.car.acceleration = copysign(self.car.maxAccel, -self.car.velocity.x)
        else:
            if abs(self.car.velocity.x) > dt * self.car.freeDecel:
                self.car.acceleration = -copysign(self.car.freeDecel, self.car.velocity.x)
            else:
                if dt != 0:
                    self.car.acceleration = -self.car.velocity.x / dt
        self.car.acceleration = max(-self.car.maxAccel, min(self.car.acceleration, self.car.maxAccel))

        if actions[2] == 1:
            self.car.steering -= 30 * dt
        elif actions[2] == -1:
            self.car.steering += 30 * dt
        else:
            self.car.steering = 0
        self.car.steering = max(-self.car.maxSteer, min(self.car.steering, self.car.maxSteer))

        # Update
        self.car.update(dt)
        self.screen.fill([0, 0, 0])
        

        # Determine the state of the environment
        self.state = self.car.particle.see(self.screen, self.walls, render=False)

        # Check for collisions and give rewards
        self.reward = 0
        if pygame.sprite.collide_mask(self.tracks[0], self.car)is not None or pygame.sprite.collide_mask(self.tracks[1], self.car) is not None:
            self.done = True
            self.reward = -10
        collided, done = self.gates.collide(self.car)
        if collided:
            self.reward = 20
            if done:
                self.reward += 100
                self.done = True

        return self.state, self.reward, self.done
    
    def render(self):
        for track in self.tracks:
            track.display(self.screen)
        self.car.display(self.screen)
        self.gates.display(self.screen)
        pygame.display.flip()
    
    def reset(self):
        self.done = False
        self.car.reset()
        self.gates.reset()
        state = self.car.particle.see(self.screen, self.walls, render=False)
        return state

class Car(pygame.sprite.Sprite):
    def __init__(self, pos, image, angle=0.0):
        pygame.sprite.Sprite.__init__(self)
        
        # Physical parameters
        self.image = pygame.image.load(image)
        self.rotated = pygame.transform.rotate(self.image, angle)
        self.mask = pygame.mask.from_surface(self.rotated)
        self.pos = Vector2(pos[0], pos[1])
        self.rect = self.rotated.get_rect(center=self.pos)
        self.velocity = Vector2(0.0, 0.0)
        self.angle = angle
        self.acceleration = 0.0
        self.steering = 0.0

        self.startPos = Vector2(pos[0], pos[1])
        self.startAngle = angle
        self.length = 4
        self.maxVelocity = 320
        self.decel = 320
        self.freeDecel = 80
        self.maxAccel = 160
        self.maxSteer = 4
        self.particle = Particle(self.pos)

    def reset(self):
        self.pos = Vector2(self.startPos)
        self.velocity = Vector2(0.0, 0.0)
        self.angle = self.startAngle
        self.acceleration = 0.0
        self.steering = 0.0
        self.rotated = pygame.transform.rotate(self.image, self.angle)
        self.rect = self.rotated.get_rect(center=self.pos)
        self.mask = pygame.mask.from_surface(self.rotated)

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
        self.particle.move(self.pos, self.angle)
        self.rotated = pygame.transform.rotate(self.image, self.angle)
        self.rect = self.rotated.get_rect(center=self.pos)
        self.mask = pygame.mask.from_surface(self.rotated)

    def display(self, surface):
        surface.blit(self.rotated, self.pos - (self.rect.width / 2, self.rect.height / 2))

class Track(pygame.sprite.Sprite):
    def __init__(self, map, last, height, width, walls):
        pygame.sprite.Sprite.__init__(self)

        self.height = height
        self.width = width
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.surface.get_rect(center=(self.width/2, self.height/2))
        self.walls = walls

        for i in map:
            self.walls.append(Boundary(Vector2(last[0], last[1]), Vector2(i[0], i[1]), self.surface))
            last = i
        
        self.mask = pygame.mask.from_surface(self.surface)
    
    def display(self, screen):
        screen.blit(self.surface, [0, 0])

# Giving rewards based on checkpoints
class RewardGates(pygame.sprite.Sprite):
    def __init__(self, map, height, width):
        pygame.sprite.Sprite.__init__(self)

        self.height = height
        self.width = width
        self.map = list(zip(map[0], map[1]))
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.surface.get_rect(center=(self.width/2, self.height/2))
        self.gates = self.map[:]
        self.finish = self.gates.pop(0)
        if len(self.gates) > 0:    
            self.gate = Boundary(Vector2(self.gates[0][0]), Vector2(self.gates[0][1]), self.surface)
            self.gates.pop(0)
        self.mask = pygame.mask.from_surface(self.surface)
    
    def collide(self, car):
        if pygame.sprite.collide_mask(self, car):
            self.surface.fill([0, 0, 0, 0])
            l = len(self.gates)
            if l > 0:    
                self.gate = Boundary(Vector2(self.gates[0][0]), Vector2(self.gates[0][1]), self.surface)
                self.gates.pop(0)
            self.mask = pygame.mask.from_surface(self.surface)
            
            if l > 0:
                return True, False
            else:
                return True, True
        return False, False

    def reset(self):
        self.gates = self.map[:]
        self.finish = self.gates.pop(0)
        self.surface.fill([0, 0, 0, 0])
        if len(self.gates) > 0:    
            self.gate = Boundary(Vector2(self.gates[0][0]), Vector2(self.gates[0][1]), self.surface)
            self.gates.pop(0)
        self.mask = pygame.mask.from_surface(self.surface)

    def display(self, screen):
        screen.blit(self.surface, [0, 0])

# Testing -----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    clock = pygame.time.Clock()
    game = Game([[[20, 20], [130, 20], [180, 20], [240, 20], [300, 20], [400, 20], [700, 20], [850, 20], [950, 100], [950, 700], [900, 750], [100, 750], [20, 700], [20, 20]],
                 [[90, 70], [130, 70], [180, 70], [240, 70], [300, 70], [400, 70], [700, 70], [800, 70], [870, 130], [870, 670], [830, 700], [150, 700], [100, 650], [90, 70]]])
    while not game.done:
        actions = [0, 0, 0]
        
        # Keypresses
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP]:
            actions[0] = 1
        elif keys[pygame.K_DOWN]:
            actions[0] = -1
        elif keys[pygame.K_SPACE]:
            actions[1] = 1
        if keys[pygame.K_RIGHT]:
            actions[2] = 1
        elif keys[pygame.K_LEFT]:
            actions[2] = -1

        dt = clock.get_time() / 1000
        state, reward, done = game.step(dt, actions)
        game.render()
        pygame.time.delay(40)
        clock.tick(60)
        if game.done:
           game.reset()
    sys.exit()
