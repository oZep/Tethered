import sys
import os
import math
import random
import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Cat, Trap, Prize, CatnipRecharge, Button, Turbine, Toy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark
from scripts.UI import Levelbar

class Game:
    def __init__(self):
        '''
        initializes Game
        '''
        pygame.init()

        # change the window caption
        pygame.display.set_caption("Mouse Disconnected")

        # create window
        self.screen = pygame.display.set_mode((640,480))

        # icon
        pygame.display.set_icon(pygame.image.load("data/images/endScene/2.png").convert())

        self.display = pygame.Surface((320, 240), pygame.SRCALPHA) # render on smaller resolution then scale it up to bigger screen
        self.display_black = pygame.Surface((320, 240), pygame.SRCALPHA) # render on smaller resolution then scale it up to bigger screen
        self.display_2 = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()
        
        self.movement = [False, False, False, False]

        self.assets = {
            'grass': load_images('tiles/grass'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player/player.png'),
            'background': load_image('background.png'),
            'story1': load_image('intro/Story1.png'),
            'story2': load_image('intro/Story2.png'),
            'story3': load_image('intro/Story3.png'),
            'story4': load_image('intro/Story4.png'),
            'story5': load_image('intro/Story5.png'),
            '1': load_image('endScene/1.png'),
            '2': load_image('endScene/2.png'),
            '3': load_image('endScene/3.png'),
            '4': load_image('endScene/4.png'),
            'clouds': load_images('clouds'),
            'catnip': load_image('UI/catnipUI.png'),
            'toy': load_image('UI/toy.png'),
            'catnip/idle': Animation(load_images('entities/catnip/catnip')),
            'toy/idle': Animation(load_images('entities/toy/idle')),
            'button/idle': Animation(load_images('entities/button/idle')),
            'button/on': Animation(load_images('entities/button/on')),
            'wind/idle': Animation(load_images('entities/windturbine/idle')),
            'wind/on': Animation(load_images('entities/windturbine/powered')),
            'trap/idle': Animation(load_images('entities/trap/idle')),
            'prize/idle': Animation(load_images('entities/prize/idle')),
            'prize/wind': Animation(load_images('entities/prize/wind')),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=10),
            'player/run': Animation(load_images('entities/player/run'), img_dur=6),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'enemy/stun': Animation(load_images('entities/cat/stun')),
            'enemy/run': Animation(load_images('entities/cat/run'), img_dur=8),
            'enemy/idle': Animation(load_images('entities/cat/idle'), img_dur=8),
            'enemy/shoot': Animation(load_images('entities/cat/shoot'), img_dur=4),
            'enemy/run': Animation(load_images('entities/cat/run'), img_dur=8),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'particle/particle_2': Animation(load_images('particles/particle_2'), img_dur=6, loop=False),
            'particle/confetti': Animation(load_images('particles/confetti'), img_dur=3, loop=False),
            'projectile': load_image('entities/cat/projectile.png'),
        }

        # adding sound
        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'win': pygame.mixer.Sound('data/sfx/win.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'bad': pygame.mixer.Sound('data/sfx/bad.mp3'),
            'get': pygame.mixer.Sound('data/sfx/get.mp3'),
            'stun': pygame.mixer.Sound('data/sfx/stun.wav'),
            'transition': pygame.mixer.Sound('data/sfx/transition.wav'),
            'pickup': pygame.mixer.Sound('data/sfx/pickup.wav'),
            'drop': pygame.mixer.Sound('data/sfx/drop.wav'),
            'button': pygame.mixer.Sound('data/sfx/button.wav'),

        }
        
        self.sfx['win'].set_volume(0.3)
        self.sfx['transition'].set_volume(0.3)
        self.sfx['bad'].set_volume(0.7)
        self.sfx['get'].set_volume(0.4)
        self.sfx['pickup'].set_volume(0.4)
        self.sfx['drop'].set_volume(0.6)
        self.sfx['stun'].set_volume(0.6)
        self.sfx['button'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.5)
        self.sfx['jump'].set_volume(0.7)

        self.clouds = Clouds(self.assets['clouds'], count=4)

        # initalizing player
        self.player = Player(self, (100, 100), (15, 14))

        # initalizing tilemap
        self.tilemap = Tilemap(self, tile_size=16)

        # tracking level
        self.level = 0
        self.max_level = len(os.listdir('data/maps')) - 1 # max level
        # loading the level
        self.load_level(self.level)

        # screen shake
        self.screenshake = 0

        self.story_timer = 0 #500
        self.bad_ending = 1000
        self.win_delay = 100

        self.music = 1


    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')

        # keep track
        self.particles = []

        self.dead = 0

        # reset wind
        self.wind = 0
        self.bad_ending = 600
        self.win_delay = 100

        self.projectiles = []
        self.sparks = []

        # transition for levels
        self.transition = -30


        # spawn the ememies
        self.enemies = []
        self.trap = []
        self.prize = []
        self.catnip = []
        self.button = []
        self.turbine= []
        self.toy = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2), ('spawners', 3), ('spawners', 4), ('spawners', 5), ('spawners', 6), ('spawners', 7)]):
            if spawner['variant'] == 0: 
                self.player.pos = spawner['pos']
            elif spawner['variant'] == 1:
                self.enemies.append(Cat(self, spawner['pos'], (16, 13)))
            elif spawner['variant'] == 2:
                self.trap.append(Trap(self, spawner['pos'], (10, 16)))
            elif spawner['variant'] == 3:
                self.prize.append(Prize(self, spawner['pos'], (17, 100)))
            elif spawner['variant'] == 4:
                self.catnip.append(CatnipRecharge(self, spawner['pos'], (14, 16)))
            elif spawner['variant'] == 5:
                self.button.append(Button(self, (spawner['pos'][0]+2, spawner['pos'][1] + 3), (8, 16)))
            elif spawner['variant'] == 6:
                self.turbine.append(Turbine(self,spawner['pos'], (100, 300)))
            else:
                self.toy.append(Toy(self, spawner['pos'], (16, 16)))

        # creating 'camera' 
        self.scroll = [self.prize[0].pos[0] + 100, self.prize[0].pos[1]]

        self.player.catnip = 3

        self.pickup = 0 # toy pickup
    
    def playmusic(self, play):
        '''
        plays game music once and loops it
        '''
        if self.music == 1 and play:
            pygame.mixer.music.load('data/music.mp3')
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play(-1)
            self.music = 0

        if self.prize[0].dead == 1:
            self.music = 1 # reset music and stop it
            pygame.mixer.music.stop()
            

    def run(self):
        '''
        runs the Game
        '''
        #pygame.mixer.music.load('data/music.wav')
        #pygame.mixer.music.set_volume(0.5)
        #pygame.mixer.music.play(-1)

        #self.sfx['ambience'].play(-1)

        # creating an infinite game loop
        while True:
            self.display.fill((0, 0, 0, 0))    # outlines
            if self.story_timer > 0:
                if self.story_timer > 400:
                    self.screen.blit(self.assets['story1'], (0,0)) # no outline

                elif self.story_timer > 300:
                    self.screen.blit(self.assets['story2'], (0,0)) # no outline

                elif self.story_timer > 200:
                    self.screen.blit(self.assets['story3'], (0,0)) # no outline

                elif self.story_timer > 100:
                    # clear the screen for new image generation in loop
                    self.screen.blit(self.assets['story4'], (0,0)) # no outline
                    # text = pygame.font.SysFont('', 300).render("Bruh?", True, (255, 255, 255)) # tired to get it to be less fuzzy
                    # scaled_text = pygame.transform.scale(text, (text.get_width() * 0.1, text.get_height() * 0.1))
                    # self.screen.blit(scaled_text, (self.screen.get_width()/4 - 60, 410))
                else:
                    self.screen.blit(self.assets['story5'], (0,0)) # no outline
                    # text = pygame.font.SysFont('FFF Forward', 30).render("Bruh.", False, (255, 255, 255))
                    # self.screen.blit(text, (self.screen.get_width()/4 + 20, 410))
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: # have to code the window closing
                        pygame.quit()
                        sys.exit()
                self.story_timer -= 1 

            
            elif self.prize[0].dead == 1: # when prize = 1 --> Lose
                self.playmusic(0)
                if self.bad_ending > 340:
                    self.screen.blit(self.assets['1'], (0,0)) # no outline   # change to noot noot

                elif self.bad_ending > 90:
                    self.screen.blit(self.assets['2'], (0,0)) # no outline
                else:
                    # clear the screen for new image generation in loop
                    self.screen.blit(self.assets['3'], (0,0)) # no outline
                
                if self.bad_ending == 0: # end game kick people out
                    self.load_level(self.level)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT: # have to code the window closing
                        pygame.quit()
                        sys.exit()
                self.bad_ending -= 1 
            
            elif self.prize[0].dead == 0 and not self.win_delay and self.level == self.max_level:  # when prize = 0 --> win
                self.sfx['transition'].play()
                self.screen.blit(self.assets['4'], (0,0)) # no outline       # change to you win! nice picture with mouses together
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: # have to code the window closing
                        pygame.quit()
                        sys.exit()

            elif self.prize[0].dead == 0 and not self.win_delay:
                self.transition += 1 # start timer, increasing value past 0
                if self.transition > 30: 
                    self.level = min(self.level + 1, self.max_level) # increase level
                    self.sfx['transition'].play()
                    self.load_level(self.level) # self.load_level(self.level) 
                if self.transition < 0:
                    self.transition += 1 # goes up automatically until 0

            else:

                self.playmusic(1)

                # clear the screen for new image generation in loop
                self.display_black.fill((0, 0, 0, 0))    # black outlines
                self.display_2.blit(self.assets['background'], (0,0)) # no outline

                self.screenshake = max(0, self.screenshake-1) # resets screenshake value

                if self.dead: # get hit once
                    self.dead += 1
                    if self.dead >= 10: # to make the level transitions smoother
                        self.transition = min(self.transition + 1, 30) # go as high as it can without changing level
                    if self.dead > 40: # timer that starts when you die
                        self.load_level(self.level) # self.level

                # move 'camera' to focus on player, make him the center of the screen
                # scroll = current scroll + (where we want the camera to be - what we have/can see currently) 
                self.scroll[0] += (self.player.rect().centerx - self.display.get_width()/2 - self.scroll[0])  / 30  # x axis
                self.scroll[1] += (self.player.rect().centery - self.display.get_height()/2 - self.scroll[1]) / 30

                # fix the jitter
                render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

                self.clouds.update() # updates clouds before the rest of the tiles
                self.clouds.render(self.display_2, offset=render_scroll)

                self.prize[0].update(self.tilemap)
                self.prize[0].render(self.display_black, offset=render_scroll) # render prize

                self.tilemap.render(self.display_black, offset=render_scroll)

                # for testing
                #pygame.draw.rect(self.display_black, (255, 0, 0), (self.prize[0].pos[0] - render_scroll[0], self.prize[0].pos[1] - render_scroll[1] + 30, self.prize[0].size[0], self.prize[0].size[1]), 3)
                #pygame.draw.rect(self.display_black, (0, 225, 0), (self.prize[0].pos[0] - render_scroll[0] + 10, self.prize[0].pos[1] - render_scroll[1] + 90, self.prize[0].size[0], self.prize[0].size[1] - 60), 3)
                
                # render turbine before everything
                self.turbine[0].update(self.tilemap)
                self.turbine[0].render(self.display_2, offset=render_scroll)


                # render the enemies
                for enemy in self.enemies.copy():
                    enemy.update(self.tilemap, (0,0))
                    enemy.render(self.display, offset=render_scroll)

                # render the enemies
                for recharge in self.catnip.copy():
                    recharge.update(self.tilemap, (0,0))
                    recharge.render(self.display_black, offset=render_scroll)
                    # hitbox testing
                    #pygame.draw.rect(self.display_black, (255, 0, 0), (recharge.pos[0] - render_scroll[0] - 6, recharge.pos[1] - render_scroll[1], recharge.size[0], recharge.size[1]), 3)


                # render/spawn bullet projectiles
                # [[x, y], direction, timer]
                for projectile in self.projectiles.copy():
                    projectile[0][0] += projectile[1]
                    projectile[2] += 1
                    img = self.assets['projectile']
                    self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1])) # spawns it the center of the projectile
                    
                    if self.tilemap.solid_check(projectile[0]): # if location is a solid tile
                        self.projectiles.remove(projectile)
                        for i in range(4):
                            self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random())) # (math.pi if projectile[1] > 0 else 0), sparks bounce in oppositie direction if hit wall which depends on projectile direction
                    elif projectile[2] > 360: #if timer > 6 seconds
                        self.projectiles.remove(projectile)
                    elif abs(self.player.dashing) < 50: # if not in dash
                        if self.player.rect().collidepoint(projectile[0]):
                            self.projectiles.remove(projectile)
                            self.dead += 1
                            self.sfx['hit'].play()
                            self.screenshake = max(16, self.screenshake)  # apply screenshake, larger wont be overrided by a smaller screenshake
                            for i in range(5): # when projectile hits player
                                # on death sparks
                                angle = random.random() * math.pi * 2 # random angle in a circle
                                speed = random.random() * 5
                                self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random())) 
                                # on death particles
                                self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle +math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                    
                    if self.prize[0].rect().collidepoint(projectile[0]): # cat hits traps, code that activates bad ending
                        self.prize[0].lower = 1 # lower prize
                        self.screenshake = max(10, self.screenshake)  # apply screenshake, larger wont be overrided by a smaller screenshake
                    
                    if self.button[0].rect().collidepoint(projectile[0]): # cat hits traps, code that activates bad ending
                        self.button[0].activate = 1
                    

                # render the enemies
                for enemy in self.trap.copy():
                    kill =  enemy.update(self.tilemap, (0,0))
                    enemy.render(self.display_black, offset=render_scroll) # change outline here
                    # for testing
                    #pygame.draw.rect(self.display_black, (255, 0, 0), (enemy.pos[0] - render_scroll[0] + 8, enemy.pos[1] - render_scroll[1] + 5, enemy.size[0], enemy.size[1]), 3)
                    if abs(self.player.dashing) < 50: # not dashing
                        if self.player.rect().colliderect(enemy): # player collides with enemy
                            self.dead += 1 # die
                            self.sfx['hit'].play()
                            self.screenshake = max(16, self.screenshake)  # apply screenshake, larger wont be overrided by a smaller screenshake
                            for i in range(10): # when projectile hits player
                                # on death sparks
                                angle = random.random() * math.pi * 2 # random angle in a circle
                                speed = random.random() * 5
                                self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random())) 
                                # on death particles
                                self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))

                    if self.prize[0].rect().colliderect(enemy): # cat hits traps, code that activates bad ending
                        self.prize[0].dead = True # prize dies
                        self.sfx['bad'].play()
                        self.screenshake = max(16, self.screenshake)  # apply screenshake, larger wont be overrided by a smaller screenshake
                        for i in range(10): # when projectile hits player
                            # on death sparks
                            angle = random.random() * math.pi * 2 # random angle in a circle
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random())) 
                            # on death particles
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))


                if not self.dead:
                    # update player movement
                    self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                    self.player.render(self.display_black, offset=render_scroll)
                    # hitbox testing
                    # pygame.draw.rect(self.display_black, (255, 0, 0), (self.player.pos[0] - render_scroll[0], self.player.pos[1] - render_scroll[1], self.player.size[0], self.player.size[1]), 3)


                # render the enemies
                for enemy in self.prize.copy():
                    kill =  enemy.update(self.tilemap, [0,0])
                    enemy.render(self.display_black, offset=render_scroll) # change outline here
                    # add mechanics later

                self.toy[0].update(self.tilemap, (0,0)) # update cat toy
                if not self.pickup: # if not picked up, render
                    self.toy[0].render(self.display_black, offset=render_scroll)
                    # for hitbox testing
                    # pygame.draw.rect(self.display_black, (255, 0, 0), (self.toy[0].pos[0] - render_scroll[0], self.toy[0].pos[1] - render_scroll[1], self.toy[0].size[0], self.toy[0].size[1]), 3)
                else:
                    pass

                self.button[0].update(self.tilemap)
                self.button[0].render(self.display_2, offset=render_scroll)
                # for testing
                # pygame.draw.rect(self.display_black, (255, 0, 0), (self.button[0].pos[0] - render_scroll[0] + 6, self.button[0].pos[1] - render_scroll[1], self.button[0].size[0], self.button[0].size[1]), 3)

                # spark affect
                for spark in self.sparks.copy():
                    kill = spark.update()
                    spark.render(self.display, offset=render_scroll)
                    if kill:
                        self.sparks.remove(spark)
                
                level_bar = Levelbar(self.level, pos=(self.display_black.get_width() // 2 - 25, 13))
                level_bar.render(self.display_black, 22)

                # black ouline based on display_black
                display_mask = pygame.mask.from_surface(self.display_black)
                display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0)) # 180 opaque, 0 transparent
                self.display_2.blit(display_sillhouette, (0, 0))
                for offset in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                    self.display_2.blit(display_sillhouette, offset) # putting what we drew onframe back into display

                # ouline based on display
                display_mask = pygame.mask.from_surface(self.display)
                display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0)) # 180 opaque, 0 transparent
                self.display_2.blit(display_sillhouette, (0, 0))
                for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    self.display_2.blit(display_sillhouette, offset) # putting what we drew onframe back into display
                

                for particle in self.particles.copy():
                    kill = particle.update()
                    particle.render(self.display, offset=render_scroll)
                    if particle.type == 'leaf':
                        particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3 # making the parlitcle move back and forth smooth'y
                    if kill:
                        self.particles.remove(particle)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT: # have to code the window closing
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_a: # referencing WASD
                            self.movement[0] = True
                        if event.key == pygame.K_d:
                            self.movement[1] = True
                        if event.key == pygame.K_SPACE:
                            if self.player.jump():  # velocity pointing upwards, gravity will pull player back down over time
                                self.sfx['jump'].play()
                        if event.key == pygame.K_e:
                            self.player.dash()
                        if event.key == pygame.K_s:
                            self.toy[0].pickup()
                        if event.key == pygame.K_f:
                            self.toy[0].drop()
                    if event.type == pygame.KEYUP: # when key is released
                        if event.key == pygame.K_a: # referencing WASD
                            self.movement[0] = False
                        if event.key == pygame.K_d:
                            self.movement[1] = False
                        if event.key == pygame.K_w:
                            self.movement[2] = False
                
                if self.transition == 1:
                    transition_surf = pygame.Surface(self.display_black.get_size())
                    pygame.draw.circle(transition_surf, (255, 255, 255), (self.display_black.get_width() // 2, self.display_black.get_height() // 2), (30 - abs(self.transition)) * 8) # display center of screen, 30 is the timer we chose, 30 * 8 = 180
                    transition_surf.set_colorkey((255, 255, 255)) # making the circle transparent now
                    self.display.blit(transition_surf, (0, 0))

                self.display_2.blit(self.display_black, (0, 0)) # black 
                self.display_2.blit(self.display, (0, 0)) # cast display 2 on display
                screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
                self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset) # render (now scaled) display image on big screen

            pygame.display.update()
            self.clock.tick(60) # run at 60 fps, like a sleep


# returns the game then runs it
Game().run()