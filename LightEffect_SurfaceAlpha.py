"""

                   GNU GENERAL PUBLIC LICENSE

                       Version 3, 29 June 2007


 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>

 Everyone is permitted to copy and distribute verbatim copies

 of this license document, but changing it is not allowed.
 """

__author__ = "Yoann Berenguer"
__copyright__ = "Copyright 2007."
__credits__ = ["Yoann Berenguer"]
__license__ = "MIT License"
__version__ = "1.0.0"
__maintainer__ = "Yoann Berenguer"
__email__ = "yoyoberenguer@hotmail.com"
__status__ = "Demo"

import pygame
import numpy
from numpy import putmask, dstack, transpose, array, arange, repeat, newaxis
import timeit
import random


def make_array(rgb_array_: numpy.ndarray, alpha_: numpy.ndarray) -> numpy.ndarray:
    assert isinstance(rgb_array_, numpy.ndarray), \
        'Expecting numpy.ndarray for argument rgb_array_ got %s ' % type(rgb_array_)
    assert isinstance(alpha_, numpy.ndarray), \
        'Expecting numpy.ndarray for argument alpha_ got %s ' % type(alpha_)

    return numpy.dstack((rgb_array_, alpha_)).astype(dtype=numpy.uint8)


def make_surface(rgba_array: numpy.ndarray) -> pygame.Surface:
    assert isinstance(rgba_array, numpy.ndarray), 'Expecting numpy.ndarray for ' \
                                                  'argument rgb_array got %s ' % type(rgba_array)

    return pygame.image.frombuffer((rgba_array.transpose(1, 0, 2)).copy(order='C').astype(numpy.uint8),
                                   (rgba_array.shape[:2][0], rgba_array.shape[:2][1]), 'RGBA')


def gradient(index_: int):
    """ create a color gradient """
    assert isinstance(index_, int), \
        'Expecting int for argument index_ got %s ' % type(index_)

    value = 256
    diff_ = (array(GRAD_END_COLOR[:3]) - array(GRAD_START_COLOR[:3])) * value / value
    row = arange(value, dtype='float') / value
    row = repeat(row[:, newaxis], [3], 1)
    diff_ = repeat(diff_[newaxis, :], [value], 0)
    row = numpy.add(array(GRAD_START_COLOR[:3], numpy.float), array((diff_ * row), numpy.float),
                    dtype=numpy.float).astype(dtype=numpy.uint8)
    # return row[index_ % value]
    return row[index_]


def soft_radial_light(rgb1_: numpy.array, alpha2_: pygame.Color, color_index_) -> pygame.Surface:
    """
    Add light effect to a selected area and return a pygame surface
    The light color & intensity can be change anytime by modifying Light_shade variable

    :param rgb1_: numpy.ndarray representing the selected area receiving the source light
    :param alpha2_: numpy.ndarray representing the mask alpha (radial light intensity)
    :return: pygame.Surface, self explanatory
    """
    assert isinstance(rgb1_, numpy.ndarray), \
        'Expecting numpy.ndarray for argument rgb1_ got %s ' % type(rgb1_)
    assert isinstance(alpha2_, numpy.ndarray), \
        'Expecting numpy.ndarray for argument alpha2_ got %s ' % type(alpha2_)
    assert isinstance(LIGHT_SHADE, pygame.Color), \
        'Expecting pygame.Color for argument Light_shade got %s ' % type(LIGHT_SHADE)

    # Add the light source color to the entire array rgb1_ (area being lit)
    color = LIGHT_SHADE[:3]

    if LIGHT_VARIANCE:
        color = gradient(index_=color_index_)

    if SHADOW:
        # display a soft shadow using the mask alpha.
        # use set_alpha() to change the pixel transparency value,
        # otherwise the animation will be pitch black
        # e.g texture1.set_alpha(255) (main loop)
        color = LIGHT_SHADE[:3]
        new_array = numpy.subtract(rgb1_, color)
    else:
        new_array = numpy.multiply(rgb1_, alpha2_ * LIGHT_INTENSITY * numpy.array(color),
                                   dtype=numpy.float).astype(numpy.uint16)

    if LIGHT_FLICKERING:
        if random.randint(0, 1000) > 900:
            new_array = numpy.multiply(rgb1_, LIGHT_INTENSITY * numpy.array(color) / 2,
                                       dtype=numpy.float)

    # Cap the maximum to 255
    putmask(new_array, new_array > 255, 255)
    putmask(new_array, new_array < 0, 0)
    return make_surface(make_array(new_array, alpha2_))

        
class MySprite1(pygame.sprite.Sprite):

    containers = None
    images = None

    def __init__(self):

        pygame.sprite.Sprite.__init__(self, self.containers)

        assert isinstance(self.images, pygame.Surface), \
            'Expecting pygame.Surface for argument self.images, got %s ' % type(self.images)

        self.images_copy = self.images.copy()
        self.image = self.images_copy[0] if isinstance(self.images_copy, list) else self.images_copy
        assert isinstance(SCREENRECT, pygame.Rect), \
            '\n[-] SCREENRECT must be a pygame.Rect'
        self.rect = self.image.get_rect(midbottom=SCREENRECT.center)
        self.color_index = 0
        self.factor = 1
        
    def update(self):

        mouse_x = pygame.mouse.get_pos()[0]
        mouse_y = pygame.mouse.get_pos()[1]

        # mouse_x = 128
        # mouse_y = 128
        lx = LIGHT_SIZE_EFFECT[0] // 2
        ly = LIGHT_SIZE_EFFECT[1] // 2

        # set the default values
        (w_low, w_high) = lx, lx  # map(lambda x: x // 2, light_size_effect)
        (h_low, h_high) = ly, ly  # map(lambda x: x // 2, light_size_effect)

        # alter the default values according to
        # the mouse (x, y) coordinates.
        if mouse_x < lx:
            w_low = mouse_x
        elif mouse_x > size[1] - lx:
            w_high = size[1] - mouse_x
        # print(w_low, w_high)

        if mouse_y < ly:
            h_low = mouse_y
        elif mouse_y > size[1] - ly:
            h_high = size[1] - mouse_y
        # copy a portion of the screen
        chunk = RGB1[mouse_x - w_low:mouse_x + w_high, mouse_y - h_low:mouse_y + h_high, :]
        # select the entire mask alpha or just a portion, depends on the mouse coordinates.
        alpha = ALPHA2_RESHAPE[lx - w_low:lx + w_high, ly - h_low:ly + h_high, :]

        # chunk size must be > 0
        if chunk.size > 0:
            self.image = soft_radial_light(chunk, alpha, self.color_index)

        self.rect.topleft = (mouse_x - w_low, mouse_y - h_low)
        self.color_index += self.factor
        if self.color_index >= 255 or self.color_index <= 0:
            self.factor *= -1
        pass


if __name__ == '__main__':

    numpy.set_printoptions(threshold=numpy.nan)

    pygame.init()
    # Map size
    size = (600, 600)
    SCREENRECT = pygame.Rect((0, 0), size)
    screen = pygame.display.set_mode(SCREENRECT.size, pygame.RESIZABLE, 32)
    # path to the background picture
    background = pygame.image.load('background.png').convert()
    background = pygame.transform.smoothscale(background, size)
    # screen.blit(background, (0, 0))
    screen.fill((0, 0, 0, 0))

    # background picture
    surface1 = 'Base1.png'
    texture1 = pygame.image.load(surface1).convert()
    texture1 = pygame.transform.smoothscale(texture1, size)


    #texture1.set_colorkey((255, 255, 255, 128))
    texture1.set_alpha(10)
    screen.blit(texture1, (0, 0))
    RGB1 = pygame.surfarray.array3d(texture1)

    # Radial mask to use
    surface2 = 'radial4.png'
    texture2 = pygame.image.load(surface2).convert_alpha()
    # lit area (x=200, y=200)
    LIGHT_SIZE_EFFECT = (300, 300)
    # set the light color and intensity
    LIGHT_SHADE = pygame.Color(220, 220, 220)
    texture2 = pygame.transform.smoothscale(texture2, LIGHT_SIZE_EFFECT)
    ALPHA2 = pygame.surfarray.array_alpha(texture2)
    # Reshape the array to work from a 3d array instead of 2d
    ALPHA2_RESHAPE = ALPHA2.reshape((LIGHT_SIZE_EFFECT[0], LIGHT_SIZE_EFFECT[1], 1))
    LIGHT_FLICKERING = True
    LIGHT_VARIANCE = True
    SHADOW = False
    GRAD_END_COLOR = pygame.Color(150, 160, 201, 0) # 188, 195, 255)
    GRAD_START_COLOR = pygame.Color(20, 20, 20, 255)
    LIGHT_INTENSITY = 0.0001# 0.4

    pygame.display.flip()
    
    clock = pygame.time.Clock()

    mysprite1 = pygame.sprite.Group()
    All = pygame.sprite.RenderUpdates()

    TIME_PASSED_SECONDS = 0

    MySprite1.images = pygame.Surface((10, 10), 32)
    MySprite1.containers = mysprite1, All
    MySprite1()

    STOP_GAME = False
    PAUSE = False
    FRAME = 0    

    while not STOP_GAME:

        while PAUSE:
            for event in pygame.event.get():
                keys = pygame.key.get_pressed()
                # print(keys)
                if keys[pygame.K_PAUSE]:
                    PAUSE = False

        for event in pygame.event.get():  # User did something
            keys = pygame.key.get_pressed()

            if event.type == pygame.QUIT:
                print('Quitting')
                STOP_GAME = True
            if keys[pygame.K_SPACE]:
                pass

            elif keys[pygame.K_PAUSE]:
                PAUSE = True
                print('Pauseed')

        screen.fill((0, 0, 0, 0))
        # screen.blit(background, (0, 0))
        screen.blit(texture1, (0, 0))
        All.update()
        All.draw(screen)
        pygame.display.flip()
        TIME_PASSED_SECONDS = clock.tick(120)
        FRAME += 1

    pygame.quit()          
