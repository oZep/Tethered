import pygame
import math
import random

from scripts.particle import Particle
from scripts.spark import Spark

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        '''
        initializes entities
        (game, entitiy type, position, size)
        '''
        self.game = game
        self.type = e_type
        self.pos = list(pos) #make sure each entitiy has it's own list, (x,y)
        self.size = size
        self.velocity = [0,0]
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        self.action = ''
        self.anim_offset = (-3, -3) #renders with an offset to pad the animation against the hitbox
        self.flip = False
        self.set_action('idle')

        self.last_movement = [0, 0]

    def rect(self):
        '''
        creates a rectangle at the entitiies current postion
        '''
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        '''
        sets a new action to change animation
        (string of animation name) -> animation
        '''
        if action != self.action: # if action has changed
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()


    
    def update(self, tilemap, movement=(0,0)):
        '''
        updates frames and entitiy position 
        '''
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False} # this value will be reset every frame, used to stop constant increase of velocity

        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect() # getting the entities rectange

        # move tile based on collision on y axis
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0: # if moving right and you collide with tile
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0: # if moving left
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        # Note: Y-axis collision handling comes after X-axis handling
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()  # Update entity rectangle for y-axis handling
        # move tile based on collision on y axis
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0: # if moving right and you collide with tile
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0: # if moving left
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        # find when to flip img for animation
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement # keeps track of movement

        # gravity aka terminal falling velocity "VERTICLE"
        self.velocity[1] = min(5, self.velocity[1] + 0.1) # (max velocity downwards, ) pos+ is downwards in pygame, from 5 to 0

        if self.collisions['down'] or self.collisions['up']: # if object hit, stop velocity
            self.velocity[1] = 0

        self.animation.update() # update animation


    def render(self, surf, offset={0,0}):
        '''
        renders entitiy asset
        '''
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1])) # fliping agasint horizontal axis



class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates plauer entity
        (game, position, size)
        '''
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0

    def update(self, tilemap, movement=(0,0)):
        '''
        updates players animations depending on movement
        '''
        super().update(tilemap, movement=movement)

        self.air_time += 1

        # falling, falling, and well, falling
        if self.air_time > 120:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)  # apply screenshake
            self.game.dead += 1

        if self.collisions['down']: # collide with the floor
            self.air_time = 0
            # restore the jumps
            self.jumps = 1

        self.wall_slide = False # reset every frame
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4: # if player connects with a wall
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5) # slow down falling
            if self.collisions['right']: # determine which animation to show
                self.flip = False
                self.set_action('wall_slide')
            else:
                self.flip = True
                self.set_action('wall_slide')

        if not self.wall_slide: 
            if self.air_time > 4: # in air for some time (highest priority)
                self.set_action('jump')
            elif movement[0] != 0: # if moving horizontally
                self.set_action('run')
            else:
                self.set_action('idle')
        

        if abs(self.dashing) in (60, 50): # if at start or end of dash
            for i in range(20): # do 20 times
                # for burst of particles
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5 # random from 0.5 to 1
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        # dash cooldown
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        # dash mechanism (only works in first 10 frames of 'dashing')
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8 #dash/dash gives direction which is applied to speed
            if abs(self.dashing) == 51: # slow down dash after 10 frames
                self.velocity[0] *= 0.1
            # trail of particles in the middle of dash
            pvelocity = [abs(self.dashing)/self.dashing * random.random() * 3, 0] # particles move in the direction of the dash
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))

        
        # normalize horizontal vel "HORIZONTAL"
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0) # right falling to left
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0) # left falling to to right

    def render(self, surf, offset={0,0}):
        '''
        partly overriding rendering for dashing
        '''
        if abs(self.dashing) <= 50: # not in first 10 frames of dash
            super().render(surf, offset=offset) # show player

    def jump(self):
        '''
        makes player jump
        -> bool if jump occurs
        '''
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0: # facing left and last movement is towards left wall
                self.velocity[0] = 3.5 
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps -1) # allows player to always wall jump, but we want to consume a jump if they have it, max so min = 0
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps -1) 
                return True
        elif self.jumps: # if jump = 0, returns false
            self.velocity[1] = -3
            self.jumps -= 1 # count down jumps
            self.air_time = 5 # allows jump animation to start
            return True
    
    def dash(self):
        '''
        makes the player dash
        '''
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60 # how long the dash is + it's direction
            

class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates the enemies
        (game, position: tuple, size)
        '''
        super().__init__(game, 'enemy', pos, size)
        self.walking = 0
    
    def update(self, tilemap, movement=(0,0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)): # Enemy (self) scans out in from of him, and into the ground & checks if tile is there
                if (self.collisions['right'] or self.collisions['left']): # if wall in front of enemy
                    self.flip = not self.flip
                else: # no wall
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1]) # y axis movement remains the same
            else: # nothing solid so turn enemy around
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1) # we will get one frame where it goes to zero, where the value of self.walking = false
            if not self.walking:
                # calc distance btwn enemy and player
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if (abs(dis[1])) < 16: # y axis less then 16 pixels
                    if (self.flip and dis[0] < 0): # player is left of enemy, and enemy is looking left
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random())) # getting pos from projectiles in it's list, facing left
                    if (not self.flip and dis[0] > 0):
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random())) # facing right

        elif random.random() < 0.01: # 1 in every 6.1 seconds
            self.walking = random.randint(30, 120)

        super().update(tilemap, movement=movement)

        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()): # if enemy hitbox collides with player
                self.game.screenshake = max(16, self.game.screenshake)  # apply screenshake
                self.game.sfx['hit'].play()
                for i in range(30): # enemy death effect
                    # on death sparks
                    angle = random.random() * math.pi * 2 # random angle in a circle
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random())) 
                    # on death particles
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle +math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random())) # left
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random())) # right
                return True # [**]
                

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)

        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1])) # renders the gun in the player
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))

    

        


        