import random

class Cloud:
    def __init__(self, pos, img, speed, depth):
        '''
        initializes the clouds
        (position, image, movement speed, cloud depth on screen)
        '''
        self.pos = list(pos)
        self.img = img
        self.speed = speed
        self.depth = depth

    def update(self):
        '''
        updates clouds position to move a little
        '''
        self.pos[0] += self.speed

    def render(self, surf, offset=(0,0)):
        '''
        renders cloud at new position
        '''
        render_pos = (self.pos[0] - offset[0] * self.depth, self.pos[1] - offset[1] * self.depth)
        surf.blit(self.img, (render_pos[0] % (surf.get_width() + self.img.get_width()) - self.img.get_width(), render_pos[1] % (surf.get_height() + self.img.get_height()) - self.img.get_height())) # doesnt remove the could until it passes fully off of screen

class Clouds:
    '''
    stores all the clouds
    '''
    def __init__(self, cloud_images, count=16):
        '''
        initializes the cloud collection
        '''
        self.clouds = []
        for i in range(count): # generates all the clouds
            self.clouds.append(Cloud((random.random() * 99999, random.random() * 99999), random.choice(cloud_images), random.random() * 0.05 + 0.05, random.random() * 0.6 + 0.2))

        self.clouds.sort(key= lambda x: x.depth) # telling python to sort the objects by depth, ones at deepest level loads first -> behind other clouds

    def update(self):
        '''
        updates each cloud in collection 
        '''
        for cloud in self.clouds:
            cloud.update()
    
    def render(self, surf, offset=(0,0)):
        '''
        renders the list of clouds
        (surface, camera offset)
        '''
        for cloud in self.clouds:
            cloud.render(surf, offset=offset)




