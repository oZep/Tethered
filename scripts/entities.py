import pygame
import math
import random

from scripts.particle import Particle
from scripts.spark import Spark
from scripts.UI import UI

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
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))



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
        self.catnip = 3
    

    def update(self, tilemap, movement=(0,0)):
        '''
        updates players animations depending on movement
        '''
        super().update(tilemap, movement=movement)

        self.air_time += 1

        # falling, falling, and well, falling
        if self.air_time > 300:
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
            if self.air_time > 10: # in air for some time (highest priority)
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
                self.game.particles.append(Particle(self.game, 'particle_2', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        # dash cooldown
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        # dash mechanism (only works in first 10 frames of 'dashing')
        if abs(self.dashing) > 50 and self.catnip > 0:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8 #dash/dash gives direction which is applied to speed
            if abs(self.dashing) == 51: # slow down dash after 10 frames # ==
                self.velocity[0] *= 0.1
                self.catnip -= 1 # only happens for one frame
            # trail of particles in the middle of dash
            pvelocity = [abs(self.dashing)/self.dashing * random.random() * 3, 0] # particles move in the direction of the dash
            self.game.particles.append(Particle(self.game, 'particle_2', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))

        
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

        # rendering the hearts, we want 6 heart levels, gold heart is a shield, red is actually hit
        cn_1 = UI(self.game.assets['catnip'].copy(), [250, 10], 15)
        cn_2 = UI(self.game.assets['catnip'].copy(), [270, 10], 15)
        cn_3 = UI(self.game.assets['catnip'].copy(), [290, 10], 15)
        if self.catnip > 2:
            cn_1.render(self.game.display_black)
        if self.catnip > 1:
            cn_2.render(self.game.display_black)
        if self.catnip > 0:
            cn_3.render(self.game.display_black)



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

    def rect(self):
        '''
        creates a rectangle at the entitiies current postion
        '''
        return pygame.Rect(self.pos[0] + 7, self.pos[1], self.size[0], self.size[1])
    
            

class Cat(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates the enemies
        (game, position: tuple, size)
        '''
        super().__init__(game, 'enemy', pos, size)
        self.timer = 100
        self.walking =0
        self.shoot_anim = 0
        self.stun = 0

    
    def update(self, tilemap, movement=(0,0)):
        if self.timer > 0:
            self.timer -= 1

    def update(self, tilemap, movement=(0, 0)):
        if self.walking and not self.stun:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if (self.collisions['right'] or self.collisions['left']):
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if (abs(dis[1]) < 15):
                    if (self.flip and dis[0] < 0):
                        self.set_action('shoot')
                        self.shoot_anim = 20
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx, self.rect().centery], -1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
                    if (not self.flip and dis[0] > 0):
                        self.set_action('shoot')
                        self.shoot_anim = 20
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx, self.rect().centery], 1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
       
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)
        
        super().update(tilemap, movement=movement)
        
        if self.shoot_anim > 0 and not self.stun:
            self.set_action('shoot')
        elif self.stun:
            self.set_action('stun')
        else:
            if movement[0] != 0 and not self.shoot_anim:
                self.set_action('run')
            else:
                self.set_action('idle')
        
        if self.shoot_anim > 0:
            self.shoot_anim -= 1
        if self.stun > 0:
            self.stun -= 1
            
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx['hit'].play()
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle_2', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                self.set_action('stun')
                self.walking = random.randint(150, 240) # reset walking timer bigger timer
                self.stun = self.walking

        
class Trap(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates the enemies
        (game, position: tuple, size)
        '''
        super().__init__(game, 'trap', pos, size)


    def update(self, tilemap, movement=(0,0)):
        super().update(tilemap, (0, 0))


class Prize(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates the enemies
        (game, position: tuple, size)
        '''
        super().__init__(game, 'prize', pos, size)
        self.dead = -1
        self.lower = 0
        self.start = 0


    def update(self, tilemap, movement=(0,0)):
        if self.rect().colliderect(self.game.player.rect()): # if enemy hitbox collides with player
            self.game.screenshake = max(16, self.game.screenshake)  # apply screenshake
            self.dead = 0 # false
            self.start = 1 # activate end scene countndown
            for i in range(30): # enemy death effect
                # on death sparks
                angle = random.random() * math.pi * 4 # random angle in a circle
                speed = random.random() * 8
                self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random())) 
                # on death particles
                self.game.particles.append(Particle(self.game, 'confetti', self.rect().center, velocity=[math.cos(angle +math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))
            self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random())) # left
            self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random())) # right]

        if self.lower == 1:   # if cat furball hits the rope
            self.velocity[1] = -0.5

        if self.start and  self.game.win_delay > 0:
            self.game.win_delay -= 1

        if self.game.wind:
            self.set_action('wind')
        else:
            self.set_action('idle')
    
    def rect(self):
        '''
        creates a rectangle at the entitiies current postion
        '''
        if self.game.wind: # updated prize hit box when wind is activated
            return pygame.Rect(self.pos[0] + 10, self.pos[1] + 90, self.size[0], self.size[1] - 60)
        else:
            return pygame.Rect(self.pos[0], self.pos[1] + 30, self.size[0], self.size[1])


    

class CatnipRecharge(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates the enemies
        (game, position: tuple, size)
        '''
        super().__init__(game, 'catnip', pos, size)
        self.timer = 150


    def update(self, tilemap, movement=(0,0)):
        if abs(self.game.player.dashing) <= 50:
            if self.rect().colliderect(self.game.player.rect()) and not self.timer and self.game.player.catnip != 3: # if enemy hitbox collides with player
                self.game.screenshake = max(10, self.game.screenshake)  # apply screenshake
                self.game.player.catnip = min(3, self.game.player.catnip +1) # just to be sure
                self.timer = 150
                for i in range(10): # enemy death effect
                    # on death sparks
                    angle = random.random() * math.pi * 2 # random angle in a circle
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random())) 
                    self.game.particles.append(Particle(self.game, 'confetti', self.rect().center, velocity=[math.cos(angle +math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))
        
        if self.timer > 0:
            self.timer -= 1

        def rect(self):
            '''
            creates a rectangle at the entitiies current postion
            '''
            return pygame.Rect(self.pos[0] - 6, self.pos[1], self.size[0], self.size[1])


class Button(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates 
        (game, position: tuple, size)
        '''
        super().__init__(game, 'button', pos, size)
        self.timer = 0
        self.activate = 0
    
    def update(self, tilemap, movement=(0,0)):
        
        # if player collides with button activate it
        if self.rect().colliderect(self.game.player.rect()) or self.activate:
            self.activate = 0
            self.timer = 200

        if self.timer > 0:
            self.timer -= 1
            self.set_action('on')
            self.game.wind = 1
        else:
            self.set_action('idle')
            self.game.wind = 0
            self.activate = 0
            
        
        if self.timer > 0:
            self.timer -= 1

    def rect(self):
        '''
        creates a rectangle at the entitiies current postion
        '''
        return pygame.Rect(self.pos[0] + 6, self.pos[1], self.size[0], self.size[1])

    
class Turbine(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates 
        (game, position: tuple, size)
        '''
        super().__init__(game, 'wind', pos, size)

        
    def update(self, tilemap, movement=(0,0)):
        
        if self.game.wind:
            self.set_action('on')
        else:
            self.set_action('idle')

    
    
class Toy(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates 
        (game, position: tuple, size)
        '''
        super().__init__(game, 'toy', pos, size)

    def update(self, tilemap, movement=(0,0)):
        '''
        updates UI
        '''
        if self.game.pickup:
            self.pos = (self.game.player.pos[0], self.game.player.pos[1])
            toy = UI(self.game.assets['toy'].copy(), [13, 10], 15)
            toy.render(self.game.display_black)

    def pickup(self):
        '''
        picks up toy
        '''
        if not self.rect().colliderect(self.game.player.rect()):
            pass
        else:
            self.game.pickup = 1

    def drop(self):
        '''
        drops toy
        '''
        if self.game.pickup:
            self.game.pickup = 0

