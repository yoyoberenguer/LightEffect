"""
--------------------------------------------------------------------------------------------------------------------
This program creates 2D light effects onto a pygame surface/image (32 bit PNG file encoded with
alpha channels transparency).
The files radial4.png, RadialTrapezoid, RadialWarning are controlling the shape and light intensity
of the illuminated area (radial masks).

The algorithm can be easily implemented into a 2D game (top down or horizontal/vertical scrolling) to enhanced
the atmosphere and lighting environment.

This code comes with a MIT license.

Copyright (c) 2018 Yoann Berenguer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

Please acknowledge the source code and give reference if using the source code included in this project.

--------------------------------------------------------------------------------------------------------------------

Version 2 changes :

 - Added volumetric effect (animated smoke or plasma) in the illuminated area to set a specific ambiance.
        This effect can also be used for generating force field around a set point.

 - Added warning light (rotational lighting)

 - Implemented shadow projection effects from a light source coordinates (See file Shadows.py for more details and
        credit to Marcus Møller for its shadow algorithms (https://github.com/marcusmoller).

 - Code cleanup and split the code into different modules
    Constant.py
    LoadTextureFile.py
    Shadow.py
    LightDemo.py

Have a nice journey
"""


__author__ = "Yoann Berenguer"
__copyright__ = "Copyright 2007."
__credits__ = ["Yoann Berenguer"]
__license__ = "MIT License"
__version__ = "2.0.0"
__maintainer__ = "Yoann Berenguer"
__email__ = "yoyoberenguer@hotmail.com"
__status__ = "Demo"

import numpy
from numpy import putmask, array, arange, repeat, newaxis
import random
import threading
from Constants import *
from Shadows import Shadow


class CreateLight(object):
    """ Define light source properties and methods."""

    def __init__(self, light_name_, light_shape_, light_shade_, alpha_mask_, light_flickering_, light_variance_,
                 light_rotating_, light_volume_, start_color_gradient_, end_color_gradient_,
                 light_intensity_, position_, volume_, mouse_=False):

        assert isinstance(light_name_, str), 'Expecting str for ' \
                                             'argument light_name_ got %s ' % type(light_name_)
        assert isinstance(light_shape_, tuple), 'Expecting tuple for ' \
                                                'argument light_shape_ got %s ' % type(light_shape_)
        assert isinstance(light_shade_, pygame.Color), 'Expecting pygame.Color for ' \
                                                       'argument light_shade_ got %s ' % type(light_shade_)
        assert isinstance(alpha_mask_, (numpy.ndarray, list)), 'Expecting numpy.ndarray or list for ' \
                                                               'argument alpha_mask_ got %s ' % type(alpha_mask_)
        assert isinstance(light_flickering_, bool), 'Expecting bool for ' \
                                                    'argument light_flickering_ got %s ' % type(light_flickering_)
        assert isinstance(light_variance_, bool), 'Expecting bool for ' \
                                                  'argument light_variance_ got %s ' % type(light_variance_)

        # Light source properties (see module Constants.py for more details about the light source creation)
        self.light_name = light_name_
        self.light_shape = light_shape_
        self.light_shade = light_shade_
        self.alpha_mask = alpha_mask_
        self.light_flickering = light_flickering_
        self.light_variance = light_variance_
        self.light_rotating = light_rotating_
        self.light_volume = light_volume_
        self.start_color_gradient = start_color_gradient_
        self.end_color_gradient = end_color_gradient_
        self.light_intensity = light_intensity_
        self.position = position_
        self.volume = volume_
        self._id = id(self)
        self.counter = 0
        self.dt = 0

        self.mouse = mouse_
        # time between frames default 0ms
        # If animation is lagging, increase self.timing e.g 33ms
        self.timing = 0

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

    def get_light_spot(self):
        """ return numpy.arrays and sizes representing the area flood with light. """

        # Light source position (x, y)
        x = self.position[0]
        y = self.position[1]

        # radius
        lx = self.light_shape[0] // 2
        ly = self.light_shape[1] // 2

        # Squaring the light source
        (w_low, w_high) = lx, lx
        (h_low, h_high) = ly, ly

        # Reshaping if close to the border(s).
        if x < lx:
            w_low = x
        elif x > SIZE[1] - lx:
            w_high = SIZE[1] - x

        if y < ly:
            h_low = y
        elif y > SIZE[1] - ly:
            h_high = SIZE[1] - y

        if isinstance(self.alpha_mask, list):
            mask = self.alpha_mask[0]
        else:
            mask = self.alpha_mask

        surface_chunk = RGB1[x - w_low:x + w_high, y - h_low:y + h_high, :]
        alpha_chunk = mask[lx - w_low:lx + w_high, ly - h_low:ly + h_high, :]
        surface_size = (w_low + w_high, h_low + h_high)

        return surface_chunk, alpha_chunk, surface_size

    def spotlight(self, rgb_array: numpy.array, alpha_array: pygame.Color, color_index_) -> pygame.Surface:
        """
        Represent the light source with all its properties. (Variance, flickering aspect, rotating light,
        volume)

        :param rgb_array: numpy.ndarray representing the area flood with light
        :param alpha_array: numpy.ndarray representing the mask alpha (radial light intensity, check the mask type)
        :param color_index_: Index for the color gradient.
        :return: pygame.Surface, light source effect representation.
        """
        assert isinstance(rgb_array, numpy.ndarray), \
            'Expecting numpy.ndarray for argument rgb_array got %s ' % type(rgb_array)
        assert isinstance(alpha_array, numpy.ndarray), \
            'Expecting numpy.ndarray for argument alpha_array got %s ' % type(alpha_array)
        assert isinstance(color_index_, int), \
            'Expecting int for argument color_index_ got %s ' % type(color_index_)

        color = self.light_shade[:3]

        # progressive color change from two distinct colors (see Constants.py e.g LIGHT definition.)
        if self.light_variance:
            color = self.gradient(index_=color_index_)

        # self explanatory
        elif self.light_flickering:
            if random.randint(0, 1000) > 950:
                color = numpy.array(color) / 2

        # Rotate the light with pre-calculated masks alpha.
        if self.light_rotating:
            if isinstance(self.alpha_mask, list):
                alpha_array = self.alpha_mask[self.counter % (len(self.alpha_mask) - 1)]

        # Add texture to the light for volumetric aspect.
        # The texture is loaded in the main loop and played sequentially (self.counter)
        elif self.light_volume and not self.mouse:
            volume_array = pygame.surfarray.array3d(self.volume[self.counter % len(self.volume)])
            volume_array[:, :, :] = volume_array[:, :, :] // 25

        # default arguments
        args = alpha_array * self.light_intensity * color if not self.light_volume else\
            alpha_array * self.light_intensity * color * volume_array

        # light resultant calculation
        new_array = numpy.multiply(rgb_array, args, dtype=numpy.float).astype(numpy.uint16)

        # Cap the the array
        putmask(new_array, new_array > 255, 255)
        putmask(new_array, new_array < 0, 0)

        # Build a 3d array (model RGB + A)
        new = numpy.dstack((new_array, alpha_array)).astype(dtype=numpy.uint8)
        # Create a pygame surface
        return pygame.image.frombuffer(new.transpose(1, 0, 2).copy('C').astype(numpy.uint8),
                                       (new.shape[:2][0], new.shape[:2][1]), 'RGBA')

    def flickering(self, rgb_array, alpha_array):
        assert isinstance(rgb_array, numpy.ndarray), \
            'Expecting numpy.ndarray for argument rgb_array got %s ' % type(rgb_array)
        assert isinstance(alpha_array, numpy.ndarray), \
            'Expecting numpy.ndarray for argument alpha_array got %s ' % type(alpha_array)

        color = numpy.array(self.light_shade[:3]) / 2
        new_array = numpy.multiply(rgb_array, alpha_array * self.light_intensity * color,
                                   dtype=numpy.float).astype(numpy.uint16)
        putmask(new_array, new_array > 255, 255)
        putmask(new_array, new_array < 0, 0)
        new = numpy.dstack((new_array, alpha_array)).astype(dtype=numpy.uint8)
        return pygame.image.frombuffer(new.transpose(1, 0, 2).copy('C').astype(numpy.uint8),
                                       (new.shape[:2][0], new.shape[:2][1]), 'RGBA')

    def offset_calculation(self):
        w, h = self.image.get_width(), self.image.get_height()
        if (w, h) != self.light_shape:
            self.offset = pygame.math.Vector2(x=self.light_shape[0] - w
            if self.position[0] <= SCREENRECT.centerx // 2 else (self.light_shape[0] - w) * -1,
                                              y=self.light_shape[1] - h if self.position[1] <= SCREENRECT.centery // 2
                                              else (self.light_shape[1] - h) * -1)


class ShowLight(pygame.sprite.Sprite, CreateLight):
    containers = None
    images = None

    def __init__(self, light_settings):

        pygame.sprite.Sprite.__init__(self, self.containers)
        CreateLight.__init__(self, *light_settings)

        assert isinstance(SCREENRECT, pygame.Rect), \
            '\n[-] SCREENRECT must be a pygame.Rect'

        print('[+] %s started' % self.light_name)

        self.offset = pygame.math.Vector2(0, 0)

        self.image = ShowLight.images
        self.rect = self.image.get_rect()

        self.chunk, self.alpha, surface_size = self.get_light_spot()
        if not self.mouse:
            if self.light_volume:
                i = 0
                for surface in self.volume:
                    self.volume[i] = pygame.transform.smoothscale(surface, (surface_size[0], surface_size[1]))
                    i += 1

            self.image = self.spotlight(self.chunk, self.alpha, 0)
            self.image_copy = self.image.copy()

            if self.light_flickering:
                self.image_flickering = self.flickering(self.chunk, self.alpha)

            self.offset_calculation()

        self.rect = self.image.get_rect(center=self.position + self.offset // 2)
        self.color_index = 0
        self.factor = 1

    def update(self):

        if self.dt > self.timing:

            # mouse cursor is a dynamic light source
            if self.mouse:
                self.position = MOUSE_POS
                self.chunk, self.alpha, surface_size = self.get_light_spot()
                self.image = self.spotlight(self.chunk, self.alpha, 0)
                self.offset = pygame.math.Vector2(0, 0)
                self.offset_calculation()
                self.rect = self.image.get_rect(center=self.position + self.offset // 2)

            # static light source
            else:

                # following effects require a constant re-calculation of the light flooded area.
                if self.light_variance or self.light_rotating or self.light_volume:
                    self.image = self.spotlight(self.chunk, self.alpha, self.color_index)

                elif self.light_flickering:
                    if random.randint(0, 1000) > 950:
                        self.image = self.image_flickering
                    else:
                        self.image = self.image_copy

                self.rect = self.image.get_rect(center=self.position + self.offset // 2)

                self.color_index += self.factor
                if self.color_index >= 255 or self.color_index <= 0:
                    self.factor *= -1

                self.dt = 0
                self.counter += 1

        self.dt += TIME_PASSED_SECONDS


if __name__ == '__main__':

    numpy.set_printoptions(threshold=numpy.nan)

    SCREEN.blit(TEXTURE1, (0, 0))
    pygame.display.flip()

    LIGHT_GROUP = pygame.sprite.Group()
    All = pygame.sprite.RenderUpdates()
    ShowLight.containers = LIGHT_GROUP, All
    # create a dummy surface
    ShowLight.images = pygame.Surface((1, 1), 32)

    for light in LIGHTS:

        if light[0] == 'Spotlight5':
            threading.Timer(random.randint(2, 7), ShowLight, args=(light,)).start()
        else:
            ShowLight(light)

    def segment_adjustment(polygon):
        segments = ALL_SEGMENTS.copy()
        for seg in polygon:
            segments.remove(seg)
        return segments


    # list(map(lambda x: LIGHT1_SEGMENTS.remove(x), list(POLYGON2)))

    # Project shadows for specific light sources
    shadows = [Shadow(segment_adjustment(POLYGON2), static_=True, location_=(370, 94)),    # LIGHT1
               Shadow(segment_adjustment(POLYGON1), static_=True, location_=(150, 185)),   # LIGHT6
               Shadow(ALL_SEGMENTS, static_=True, location_=(333, 595))                    # LIGHT5
               ]

    clock = pygame.time.Clock()

    while not STOP_GAME:

        pygame.event.pump()

        while PAUSE:
            event = pygame.event.wait()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_PAUSE]:
                PAUSE = False
                pygame.event.clear()
                keys = None
            break

        for event in pygame.event.get():

            keys = pygame.key.get_pressed()

            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                print('Quitting')
                STOP_GAME = True

            elif event.type == pygame.MOUSEMOTION:
                MOUSE_POS = event.pos

            elif keys[pygame.K_PAUSE]:
                PAUSE = True
                print('Paused')

        SCREEN.fill((0, 0, 0, 0))
        SCREEN.blit(TEXTURE1, (0, 0))

        for shadow in shadows:
            shadow.update(MOUSE_POS)
            shadow.render_frame()

        All.update()
        All.draw(SCREEN)

        pygame.display.flip()
        TIME_PASSED_SECONDS = clock.tick(120)
        FRAME += 1

    pygame.quit()
