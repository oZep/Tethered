import math
import pygame

class Spark:
    def __init__(self, pos, angle, speed):
        '''
        initializing spark
        (position: tuple. angle, speed)
        '''
        self.pos = list(pos)
        self.angle = angle
        self.speed = speed

    def update(self):
        '''
        update function
        '''
        self.pos[0] += math.cos(self.angle) * self.speed
        self.pos[1] += math.sin(self.angle) * self.speed

        self.speed = max(0, self.speed - 0.1)
        return not self.speed # when speed = 0, returns true therefore removing it from the list of sparks
    
    def render(self, surf, offset=(0,0)):
        '''
        renders the spark visible in a polygon shape
        (surface, offect=(0,0))
        '''
        render_points = [
            (self.pos[0] + math.cos(self.angle) * self.speed * 3 - offset[0], self.pos[1] + math.sin(self.angle) * self.speed * 3 - offset[1]), # want one part of the spark to be longer
            (self.pos[0] + math.cos(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[0], self.pos[1] + math.sin(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi) * self.speed * 3 - offset[0], self.pos[1] + math.sin(self.angle + math.pi) * self.speed * 3 - offset[1]), # want one part of the spark to be longer
            (self.pos[0] + math.cos(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[0], self.pos[1] + math.sin(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[1])

        ]

        pygame.draw.polygon(surf, (255, 255, 255), render_points)
