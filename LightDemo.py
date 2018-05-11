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
import threading


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


class CreateLight(object):

    def __init__(self, light_name_, light_shape_, light_shade_, alpha_mask_, light_flickering_, light_variance_,
                 shadow_, start_color_gradient_, end_color_gradient_, light_intensity_, position_):
        self.light_name = light_name_
        self.light_shape = light_shape_
        self.light_shade = light_shade_
        self.alpha_mask = alpha_mask_
        self.light_flickering = light_flickering_
        self.light_variance = light_variance_
        self.shadow = shadow_
        self.start_color_gradient = start_color_gradient_
        self.end_color_gradient = end_color_gradient_
        self.light_intensity = light_intensity_
        self.position = position_
        self._id = id(self)

    def gradient(self, index_: int):
        """ create a color gradient """
        assert isinstance(index_, int), \
            'Expecting int for argument index_ got %s ' % type(index_)

        value = 256
        diff_ = (array(self.end_color_gradient[:3]) - array(self.start_color_gradient[:3])) * value / value
        row = arange(value, dtype='float') / value
        row = repeat(row[:, newaxis], [3], 1)
        diff_ = repeat(diff_[newaxis, :], [value], 0)
        row = numpy.add(array(self.start_color_gradient[:3], numpy.float), array((diff_ * row), numpy.float),
                        dtype=numpy.float).astype(dtype=numpy.uint8)
        return row[index_]

    def spotlight(self, rgb_array: numpy.array, alpha_array: pygame.Color, color_index_) -> pygame.Surface:
        """
        Add light effect to a selected area and return a pygame surface
        The light color & intensity can be change anytime by modifying Light_shade variable

        :param rgb_array: numpy.ndarray representing the selected area receiving the source light
        :param alpha_array: numpy.ndarray representing the mask alpha (radial light intensity)
        :param color_index_:
        :return: pygame.Surface, self explanatory
        """
        assert isinstance(rgb_array, numpy.ndarray), \
            'Expecting numpy.ndarray for argument rgb_array got %s ' % type(rgb_array)
        assert isinstance(alpha_array, numpy.ndarray), \
            'Expecting numpy.ndarray for argument alpha_array got %s ' % type(alpha_array)

        color = self.light_shade[:3]

        if self.light_variance:
            color = self.gradient(index_=color_index_)

        if self.shadow:
            new_array = numpy.subtract(rgb_array, color)
        else:
            new_array = numpy.multiply(rgb_array, alpha_array * self.light_intensity * numpy.array(color),
                                       dtype=numpy.float).astype(numpy.uint16)

        if self.light_flickering:
            if random.randint(0, 1000) > 900:
                new_array = numpy.multiply(rgb_array, self.light_intensity * numpy.array(color) / 2 * alpha_array
                                           ,dtype=numpy.float)

        putmask(new_array, new_array > 255, 255)
        putmask(new_array, new_array < 0, 0)
        return make_surface(make_array(new_array, alpha_array))


class ShowLight(pygame.sprite.Sprite, CreateLight):
    containers = None
    images = None
    _mouse_control = False

    def __init__(self, light_settings):

        pygame.sprite.Sprite.__init__(self, self.containers)
        CreateLight.__init__(self, *light_settings)

        assert isinstance(self.images, pygame.Surface), \
            'Expecting pygame.Surface for argument self.images, got %s ' % type(self.images)

        self.images_copy = self.images.copy()
        self.image = self.images_copy[0] if isinstance(self.images_copy, list) else self.images_copy
        assert isinstance(SCREENRECT, pygame.Rect), \
            '\n[-] SCREENRECT must be a pygame.Rect'
        self.rect = self.image.get_rect(midbottom=(-100, -100))
        self.color_index = 0
        self.factor = 1
        self.mouse_control = self._mouse_control

    def update(self):

        if self.mouse_control:
            mouse_x = pygame.mouse.get_pos()[0]
            mouse_y = pygame.mouse.get_pos()[1]
            ShowLight._mouse_control = False
        else:
            mouse_x = self.position[0]
            mouse_y = self.position[1]

        lx = self.light_shape[0] // 2
        ly = self.light_shape[1] // 2

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
        alpha = self.alpha_mask[lx - w_low:lx + w_high, ly - h_low:ly + h_high, :]

        # chunk size must be > 0
        if chunk.size > 0:
            self.image = self.spotlight(chunk, alpha, self.color_index)

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
    # background = pygame.image.load('background.png').convert()
    # background = pygame.transform.smoothscale(background, size)
    # screen.blit(background, (0, 0))
    screen.fill((0, 0, 0, 0))

    surface1 = 'Base1.png'
    texture1 = pygame.image.load(surface1).convert()
    texture1 = pygame.transform.smoothscale(texture1, size)
    texture1.set_alpha(20)
    screen.blit(texture1, (0, 0))
    pygame.display.flip()

    RGB1 = pygame.surfarray.array3d(texture1)
    mask_alpha = pygame.image.load('radial4.png').convert_alpha()
    light_shape = (300, 300)
    light_area = pygame.transform.smoothscale(mask_alpha, light_shape)
    sub_alpha = pygame.surfarray.array_alpha(light_area)
    sub_alpha_reshape = sub_alpha.reshape(*light_shape, 1)

    light1 = ('Spotlight1', light_shape, pygame.Color(150, 160, 201, 0), sub_alpha_reshape,
              True, False, False, pygame.Color(150, 160, 201, 0), pygame.Color(20, 20, 20, 255),
              1e-4, (370, 94))

    light2 = ('Spotlight2', light_shape, pygame.Color(165, 162, 180, 0), sub_alpha_reshape,
              False, True, False, pygame.Color(150, 160, 201, 0), pygame.Color(150, 160, 201, 0),
              2e-4, (370, 186))

    light_shape = (300, 180)
    light_area = pygame.transform.smoothscale(mask_alpha, light_shape)
    sub_alpha = pygame.surfarray.array_alpha(light_area)
    sub_alpha_reshape = sub_alpha.reshape(*light_shape, 1)
    light3 = ('Spotlight3', light_shape, pygame.Color(150, 160, 201, 0), sub_alpha_reshape,
              True, True, False, pygame.Color(150, 160, 201, 0), pygame.Color(22, 25, 35, 0),
              0.8e-4, (88, 357))

    light_shape = (400, 400)
    light_area = pygame.transform.smoothscale(mask_alpha, light_shape)
    sub_alpha = pygame.surfarray.array_alpha(light_area)
    sub_alpha_reshape = sub_alpha.reshape(*light_shape, 1)
    light4 = ('Spotlight4', light_shape, pygame.Color(200, 50, 61, 0), sub_alpha_reshape,
              False, True, False, pygame.Color(220, 98, 101, 0), pygame.Color(30, 5, 8, 0),
              0.7e-4, (480, 269))

    light_shape = (400, 400)
    light_area = pygame.transform.smoothscale(mask_alpha, light_shape)
    sub_alpha = pygame.surfarray.array_alpha(light_area)
    sub_alpha_reshape = sub_alpha.reshape(*light_shape, 1)
    light6 = ('Spotlight6', light_shape, pygame.Color(200, 200, 10, 0), sub_alpha_reshape,
              False, True, False, pygame.Color(220, 220, 10, 0), pygame.Color(18, 18, 0, 0),
              1e-4, (0, 0))

    light_shape = (600, 600)
    mask_alpha = pygame.image.load('radialTrapezoid.png').convert_alpha()
    light_area = pygame.transform.smoothscale(mask_alpha, light_shape)
    sub_alpha = pygame.surfarray.array_alpha(light_area)
    sub_alpha_reshape = sub_alpha.reshape(*light_shape, 1)
    light5 = ('Spotlight5', light_shape, pygame.Color(200, 200, 200, 0), sub_alpha_reshape,
              False, True, False, pygame.Color(220, 210, 212, 0), pygame.Color(20, 20, 21, 0),
              1.3e-4, SCREENRECT.center)

    light_group = pygame.sprite.Group()
    All = pygame.sprite.RenderUpdates()
    ShowLight.images = pygame.Surface((10, 10), 32)
    ShowLight.containers = light_group, All

    threading.Timer(random.randint(3, 7), ShowLight, args=(light1,)).start()
    ShowLight(light2)
    threading.Timer(random.randint(1, 5), ShowLight, args=(light3,)).start()
    ShowLight(light4)

    threading.Timer(random.randint(2, 7), ShowLight, args=(light5,)).start()
    ShowLight._mouse_control = True
    ShowLight(light6)

    # threading.Timer(1, MySprite1, args=((370, 184), (300, 300), pygame.Color(100, 100, 220))).start()

    STOP_GAME = False
    PAUSE = False
    FRAME = 0
    clock = pygame.time.Clock()
    TIME_PASSED_SECONDS = 0

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
