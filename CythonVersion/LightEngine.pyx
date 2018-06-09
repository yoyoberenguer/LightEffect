"""
--------------------------------------------------------------------------------------------------------------------
This program creates 2D light effects onto a pygame surface/image (32 bit PNG file encoded with
alpha channels transparency).
The files radial4.png, RadialTrapezoid, RadialWarning are controlling the shape and light intensity
of the illuminated area (radial masks).

The class can be easily implemented into a 2D game (top down or horizontal/vertical scrolling) to enhanced
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

Please acknowledge and give reference if using the source code for your project

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


- ERRATA
 05/06/2018 Correction bug
 elif x > SIZE[1] - lx:
            w_high = SIZE[1] - x
 by ++>
  elif x > SIZE[0] - lx:
            w_high = SIZE[0] - x

  in update(self), below statements were wrongly placed.
  self.dt = 0
  self.counter += 1

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
import time
import multiprocessing
import ctypes


class CreateLight(object):

    time_passed_seconds = 0
    UPDATE = False

    """ Define a light source properties and methods."""

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
        self.color_index = 0

        self.mouse = mouse_
        # time between frames default 0ms
        # If animation is lagging, increase self.timing e.g 33ms
        self.timing = 30

    def gradient(self, index_: int)->numpy.ndarray:
        """ create a color gradient
        :param index_: index pointing to a specific color from a color gradient array (linear color gradient)
               The color gradient is build from two distinct colors (start_color_gradient and end_color_gradient).
               The colors along the line through those points are calculated using linear interpolation
        :return row:  return a color from a gradient (color at position index_).
        """

        assert isinstance(index_, int), \
            'Expecting int for argument index_ got %s ' % type(index_)

        diff_ = (array(self.end_color_gradient[:3]) - array(self.start_color_gradient[:3]))
        row = arange(256, dtype='float') / 256
        row = repeat(row[:, newaxis], [3], 1)
        diff_ = repeat(diff_[newaxis, :], [256], 0)
        row = numpy.add(array(self.start_color_gradient[:3], numpy.float), array((diff_ * row), dtype=numpy.float),
                        dtype=numpy.float).astype(dtype=numpy.uint8)

        return row[index_]


    def get_light_spot(self):
        """ return numpy.arrays and sizes representing the area flood with light. """

        # Light source position (x, y)
        x = self.position[0]
        y = self.position[1]

        # radius
        lx = self.light_shape[0] >> 1
        ly = self.light_shape[1] >> 1

        # Squaring the light source
        (w_low, w_high) = lx, lx
        (h_low, h_high) = ly, ly

        # Reshaping if close to the border(s).
        if x < lx:
            w_low = x
        elif x > SIZE[0] - lx:
            w_high = SIZE[0] - x

        if y < ly:
            h_low = y
        elif y > SIZE[1] - ly:
            h_high = SIZE[1] - y

        if isinstance(self.alpha_mask, list):
            mask = self.alpha_mask[0]
        else:
            mask = self.alpha_mask

        # Different method but not faster
        # rect = pygame.Rect(x-w_low, y-h_low, x + w_high, y + h_high)
        # surface = pygame.Surface((300, y + h_high), pygame.SRCALPHA, 32)
        # surface.blit(TEXTURE1, (0, 0), rect)
        # surface_chunk = pygame.surfarray.array3d(surface)
        # return surface_chunk, \
        #       mask[lx - w_low:lx + w_high, ly - h_low:ly + h_high, :], \
        #       (w_low + w_high, h_low + h_high)

        return RGB1[x - w_low:x + w_high, y - h_low:y + h_high, :], \
               mask[lx - w_low:lx + w_high, ly - h_low:ly + h_high, :], \
               (w_low + w_high, h_low + h_high)


    def spotlight(self, rgb_array: numpy.array, alpha_array: pygame.Color, color_index_):
        """
        Represent the light source with all its properties. (Variance, flickering aspect, rotating light,
        volume)

        :param rgb_array: numpy.ndarray representing the area flood with light
        :param alpha_array: numpy.ndarray representing the mask alpha (radial light intensity, check the mask type)
        :param color_index_: Index for the color gradient.
        """
        """
        assert isinstance(rgb_array, numpy.ndarray), \
            'Expecting numpy.ndarray for argument rgb_array got %s ' % type(rgb_array)
        assert isinstance(alpha_array, numpy.ndarray), \
            'Expecting numpy.ndarray for argument alpha_array got %s ' % type(alpha_array)
        assert isinstance(color_index_, int), \
            'Expecting int for argument color_index_ got %s ' % type(color_index_)
        """
        color = self.light_shade[:3]

        # progressive color change from two distinct colors (see Constants.py e.g LIGHT definition.)
        if self.light_variance:
            color = self.gradient(index_=color_index_)

        # self explanatory
        elif self.light_flickering:
            if random.randint(0, 1000) > 950:
                color = [color[0] >> 1, color[1] >> 1, color[2] >> 1]

        # Rotate the light with pre-calculated masks alpha.
        if self.light_rotating:
            if isinstance(self.alpha_mask, list):
                alpha_array = self.alpha_mask[self.counter % (len(self.alpha_mask) - 1)]

        # Add texture to the light for volumetric aspect.
        # The texture is loaded in the main loop and played sequentially (self.counter)

        # (self.light_volume and not self.mouse) --> if the mouse goes outside of the main window, the shape of
        # alpha_array and rgb_array will not match the array shape of the texture define by self.volume.
        # In short, the volumetric effect will be disable for dynamic light using the mouse position.
        # todo pixels3d / array3d choose the best format according to surface
        if self.logic1:
            volume_array = numpy.divide(self.V0[self.counter % len(self.volume)], 25)
            args = alpha_array * self.light_intensity * color * volume_array
        else:
            args = alpha_array * self.light_intensity * color

        # light resultant calculation
        new_array = numpy.multiply(rgb_array, args) #.astype(numpy.uint16)

        # Cap the array
        putmask(new_array, new_array > 255, 255)
        # putmask(new_array, new_array < 0, 0)

        # Build a 3d array (model RGB + A)
        new = numpy.dstack((new_array, alpha_array))

        # Build the pygame surface (RGBA model)
        self.image = pygame.image.frombuffer(new.transpose(1, 0, 2).copy('C').astype(numpy.uint8),
                                       (new.shape[:2][0], new.shape[:2][1]), 'RGBA')


    def flickering(self, rgb_array, alpha_array):
        assert isinstance(rgb_array, numpy.ndarray), \
            'Expecting numpy.ndarray for argument rgb_array got %s ' % type(rgb_array)
        assert isinstance(alpha_array, numpy.ndarray), \
            'Expecting numpy.ndarray for argument alpha_array got %s ' % type(alpha_array)

        color = [self.light_shade[0] >> 1, self.light_shade[1] >> 1, self.light_shade[2] >> 1 ]
        new_array = numpy.multiply(rgb_array, alpha_array * self.light_intensity * color,
                                   dtype=numpy.float)
        putmask(new_array, new_array > 255, 255)
        # putmask(new_array, new_array < 0, 0)
        new = numpy.dstack((new_array, alpha_array))
        return pygame.image.frombuffer(new.transpose(1, 0, 2).copy('C').astype(numpy.uint8),
                                       (new.shape[:2][0], new.shape[:2][1]), 'RGBA')

    def offset_calculation(self):
        if self.image.get_size() != self.light_shape:
            w, h = self.image.get_size()
            self.offset = pygame.math.Vector2(x=self.light_shape[0] - w
            if self.position[0] <= SCREENRECT.centerx >> 1 else (self.light_shape[0] - w) * -1,
                                              y=self.light_shape[1] - h if self.position[1] <= SCREENRECT.centery >> 1
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

        # pre assembled logic
        self.logic = self.light_variance or self.light_rotating or self.light_volume
        self.logic1 = self.light_volume and not self.mouse

        self.V0 = []
        if not self.mouse:
            if self.light_volume:
                i = 0
                # process the volumetric texture(resizing) to match the light flooded area.
                for surface in self.volume:
                    self.volume[i] = pygame.transform.smoothscale(surface, (surface_size[0], surface_size[1]))
                    i += 1
                # transform the surface into a numpy array
                for surface in self.volume:
                    self.V0.append(pygame.surfarray.pixels3d(surface))

            self.spotlight(self.chunk, self.alpha, 0)
            self.image_copy = self.image.copy()

            if self.light_flickering:
                self.image_flickering = self.flickering(self.chunk, self.alpha)

            self.offset_calculation()

        self.rect = self.image.get_rect(center=self.position + self.offset / 2)
        self.color_index = 0
        self.factor = 1

    def update(self):


        if self.dt > self.timing:


            # mouse cursor is a dynamic light source
            # and thus the area re-calculated every frames with 'self.spotlight'
            if self.mouse:
                self.position = CreateLight.MOUSE_POS
                self.spotlight(*self.get_light_spot()[:2], self.color_index)
                self.offset.x, self.offset.y = (0, 0)
                self.offset_calculation()
                self.rect = self.image.get_rect(center=self.position + self.offset / 2)

            # static light source
            else:

                # following effects require a constant re-calculation of the light flooded area.
                # self.logic = self.light_variance or self.light_rotating or self.light_volume
                if self.logic:
                    self.spotlight(self.chunk, self.alpha, self.color_index)

                elif self.light_flickering:
                    if random.randint(0, 1000) > 950:
                        self.image = self.image_flickering
                    else:
                        self.image = self.image_copy

                self.rect = self.image.get_rect(center=self.position + self.offset / 2)

                self.color_index += self.factor
                if self.color_index > 254 or self.color_index < 1:
                    self.factor *= -1


            self.dt = 0
            self.counter += 1
            CreateLight.UPDATE = True

        self.dt += CreateLight.time_passed_seconds

