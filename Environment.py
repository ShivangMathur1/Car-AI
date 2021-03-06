import sys
from math import copysign, degrees, radians, sin
import pygame
from pygame.math import Vector2
from Raycast import Boundary, RayParticle

# Add done if long time no reward

# The layout of the environment
MAP = [[[20, 20], [120, 20], [180, 20], [240, 20], [300, 20], [400, 20], [700, 20], [850, 20], [950, 100], [950, 700], [900, 750], [100, 750], [20, 700], [20, 20]],
       [[90, 70], [120, 70], [180, 70], [240, 70], [300, 70], [400, 70], [700, 70], [800, 70], [870, 130], [870, 670], [830, 700], [150, 700], [100, 650], [90, 70]]]

# Environment class: For all your training needs
class Game:
    def __init__(self, maps=MAP):
        # pygame initialisations
        pygame.init()
        pygame.key.set_repeat(20, 20)

        self.done = False
        self.state = None
        self.reward = 0
        self.nActions = 13
        self.nInputs = 8

        # The screen, if you decide to render the environment
        self.width = 966
        self.height = 768
        self.screen = pygame.display.set_mode([self.width, self.height])
        self.screen.fill([0, 0, 0])

        # Objects: Car, Tracks, and Reward Gates
        self.car = Car([100, 50], "car.png", 0)
        self.walls = []
        self.tracks = []
        self.gates = RewardGates(maps, self.height, self.width)
        for map in maps:
            self.tracks.append(Track(map[1:], map[0], self.height, self.width, self.walls))
        
    # Update at each time delta (and not frame)
    def step(self, action, dt=0.015):
        # Need to have this code for pygame to work
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("No messing with the environment or all your weights will be re-initialised to -420 ಠ_ಠ")

        # Update
        self.car.update(dt, action)
        self.screen.fill([0, 0, 0])
        

        # Determine the state of the environment
        self.state = self.car.rayCaster.see(self.screen, self.walls, render=False)

        # Check for collisions and give rewards
        self.reward = 0
        if pygame.sprite.collide_mask(self.tracks[0], self.car) is not None or pygame.sprite.collide_mask(self.tracks[1], self.car) is not None:
            self.done = True
            self.reward = -50
        collided, done = self.gates.collide(self.car)
        if collided:
            self.reward = 50
            if done:
                self.reward += 100
                self.done = True

        return self.state, self.reward, self.done
    
    # To render or not to render
    def render(self):
        for track in self.tracks:
            track.display(self.screen)
        self.car.display(self.screen)
        self.gates.display(self.screen)
        pygame.display.flip()
    
    # Resetting the environment so that the fun never stops
    def reset(self):
        self.done = False
        self.car.reset()
        self.gates.reset()
        self.state = self.car.rayCaster.see(self.screen, self.walls, render=False)
        return self.state
    
    def close(self):
        sys.exit()

# *slaps roof* This bad boy can go 320 pixels/dt
# Car class with mask collision and in-built raycasting to view the environment
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
        self.rayCaster = RayParticle(self.pos)

    # Move the car one time delta's worth
    def update(self, dt, action):
        # Actions: [[0, Idle], [1, Forward], [2, Backward], [3, Left], [4, Right], [5, Brake],[6, Forward, Left],
        # [7, Forward, Right], [8, Backward, Left], [9, Backward, Right], [10, Brake, Left], [11, Brake, Right]]
        # Perform actions and determine variables
        self.action = action
        if self.action in [1, 6, 7]:        # Forward
            if self.velocity.x < 0:
                self.acceleration = self.decel
            else:
                self.acceleration = self.maxAccel
        elif self.action in [2, 8, 9]:       # Backward
            if self.velocity.x > 0:
                self.acceleration = -self.decel
            else:
                self.acceleration = -self.maxAccel
        elif self.action in [5, 10, 11]:     # Brakes
            if self.velocity.x != 0:
                self.acceleration = copysign(self.maxAccel, -self.velocity.x)
        else:
            if abs(self.velocity.x) > dt * self.freeDecel:
                self.acceleration = -copysign(self.freeDecel, self.velocity.x)
            else:
                if dt != 0:
                    self.acceleration = -self.velocity.x / dt
        #self.acceleration = max(-self.maxAccel, min(self.acceleration, self.maxAccel))

        if self.action in [3, 6, 8]:        # Left
            self.steering += 30 * dt
        elif self.action in [4, 7, 9]:      # Right
            self.steering -= 30 * dt
        else:
            self.steering = 0
        self.steering = max(-self.maxSteer, min(self.steering, self.maxSteer))

        self.velocity += (self.acceleration * dt, 0)
        self.velocity.x = max(-self.maxVelocity, min(self.velocity.x, self.maxVelocity))

        if self.steering:
            radius = self.length / sin(radians(self.steering))
            angularVelocity = self.velocity.x / radius
        else:
            angularVelocity = 0

        # Change state
        self.pos += self.velocity.rotate(-self.angle) * dt
        self.angle += degrees(angularVelocity) * dt
        self.rayCaster.move(self.pos, self.angle)
        self.rotated = pygame.transform.rotate(self.image, self.angle)
        self.rect = self.rotated.get_rect(center=self.pos)
        self.mask = pygame.mask.from_surface(self.rotated)
    
    # Resetting the car to it's original attributes in case of a game over or a success
    def reset(self):
        self.pos = Vector2(self.startPos)
        self.velocity = Vector2(0.0, 0.0)
        self.angle = self.startAngle
        self.acceleration = 0.0
        self.steering = 0.0
        self.rotated = pygame.transform.rotate(self.image, self.angle)
        self.rect = self.rotated.get_rect(center=self.pos)
        self.mask = pygame.mask.from_surface(self.rotated)

    def display(self, surface):
        surface.blit(self.rotated, self.pos - (self.rect.width / 2, self.rect.height / 2))

# You. Shall not. Pass. The white line of negative rewards.
# Basically a collidable object that must be avoided or else game over
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
    
    # If Collision happens with current gate, destroy and load next one
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

    # Even gates need some love and resetting from time to time
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
    game = Game()
    while not game.done:
        # Actions: [[0, Idle], [1, Forward], [2, Backward], [3, Left], [4, Right], [5, Brake],[6, Forward, Left], [7, Forward, Right], [8, Backward, Left], [9, Backward, Right], [10, Brake, Left], [11, Brake, Right]]
        
        # The keypresses dictionary
        keys = pygame.key.get_pressed()
        action = 0
        if keys[pygame.K_UP]:
            action = 1
            if keys[pygame.K_LEFT]:
                action = 6
            elif  keys[pygame.K_RIGHT]:
                action = 7
        
        elif keys[pygame.K_DOWN]:
            action = 2
            if keys[pygame.K_LEFT]:
                action = 8
            elif  keys[pygame.K_RIGHT]:
                action = 9
        elif keys[pygame.K_SPACE]:
            action = 5
            if keys[pygame.K_LEFT]:
                action = 10
            elif  keys[pygame.K_RIGHT]:
                action = 11
        else:
            if keys[pygame.K_LEFT]:
                    action = 3
            elif  keys[pygame.K_RIGHT]:
                    action = 4

        dt = clock.get_time() / 1000
        state, reward, done = game.step(action, dt)
        print(dt)
        game.render()
        # pygame.time.delay(20)
        clock.tick(60)

    game.close()
