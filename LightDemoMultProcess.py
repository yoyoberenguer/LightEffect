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



class LightSpot(multiprocessing.Process):

    def __init__(self, q_in, q_out, event_):
        super(multiprocessing.Process, self).__init__()

        self.Q_in = q_in
        self.Q_out = q_out
        self.event = event_
        self.stop = False

    def run(self):
        while not self.event.is_set():

            if self.Q_in is not None:
                queue = self.Q_in.get()
                position = queue[0]
                light_shape = queue[1]
                alpha_mask = queue[2]
                RGB1 = queue[3]

                # Light source position (x, y)
                x = position[0]
                y = position[1]

                # radius
                lx = light_shape[0] >> 1
                ly = light_shape[1] >> 1

                # Squaring the light source
                (w_low, w_high) = lx, lx
                (h_low, h_high) = ly, ly

                # Reshaping if close to the border(s).
                if x < lx:
                    w_low = x
                elif x > 1280 - lx:
                    w_high = 1280 - x

                if y < ly:
                    h_low = y
                elif y > 1024 - ly:
                    h_high = 1024 - y

                if isinstance(alpha_mask, list):
                    mask = alpha_mask[0]
                else:
                    mask = alpha_mask

                self.Q_out.put((RGB1[x - w_low:x + w_high, y - h_low:y + h_high, :],
                        mask[lx - w_low:lx + w_high, ly - h_low:ly + h_high, :],
                        (w_low + w_high, h_low + h_high))
                       )
            else:
                time.sleep(0.01)

        print('LightSpot %s is dead.')


class LightCalc(multiprocessing.Process):

    def __init__(self, q_in, q_out, event_):
        super(multiprocessing.Process, self).__init__()

        self.Q_in = q_in
        self.Q_out = q_out
        self.event = event_
        self.stop = False

    def gradient(self, index_: int, start_color_gradient, end_color_gradient):
        """ create a color gradient """
        assert isinstance(index_, int), \
            'Expecting int for argument index_ got %s ' % type(index_)

        value = 256
        diff_ = (array(end_color_gradient[:3]) - array(start_color_gradient[:3]))
        row = arange(value, dtype='float') / value
        row = repeat(row[:, newaxis], [3], 1)
        diff_ = repeat(diff_[newaxis, :], [value], 0)
        row = numpy.add(array(start_color_gradient[:3], numpy.float), array((diff_ * row), numpy.float),
                        dtype=numpy.float).astype(dtype=numpy.uint8)
        return row[index_]

    def run(self):
        while not self.event.is_set():

            if self.Q_in is not None:

                queue = self.Q_in.get()
                light_shade = queue[0]
                light_variance = queue[1]
                color_index_ = queue[2]
                start_color_gradient = queue[3]
                end_color_gradient = queue[4]

                light_flickering = queue[5]
                light_rotating = queue[6]
                alpha_mask = queue[7]
                counter = queue[8]
                light_volume = queue[9]
                mouse = queue[10]
                volume = queue[11]
                light_intensity = queue[12]
                rgb_array = queue[13]
                alpha_array = queue[14]


                color = light_shade[:3]

                # progressive color change from two distinct colors (see Constants.py e.g LIGHT definition.)
                if light_variance:
                    color = self.gradient(color_index_, start_color_gradient, end_color_gradient)

                # self explanatory
                elif light_flickering:
                    if random.randint(0, 1000) > 950:
                        color = [color[0] >> 1, color[1] >> 1, color[2] >> 1]

                # Rotate the light with pre-calculated masks alpha.
                if light_rotating:
                    if isinstance(alpha_mask, list):
                        alpha_array = alpha_mask[counter % (len(alpha_mask) - 1)]

                # Add texture to the light for volumetric aspect.
                # The texture is loaded in the main loop and played sequentially (self.counter)
                # (and not self.mouse) --> if the mouse goes outside of the main window, the shape of
                # alpha_array and rgb_array will not match the array shape of the texture define by self.volume.
                # In short, the volumetric effect will be disable for dynamic light using the mouse position.
                # todo pixels3d / array3d choose the best format according to surface
                elif light_volume and not mouse:
                    volume_array = volume[counter % len(volume)] >> 5

                # todo  alpha_array * self.light_intensity * color * volume_array
                # UnboundLocalError: local variable 'volume_array' referenced before assignment
                # default arguments
                # args = alpha_array * self.light_intensity * color if not self.light_volume else\
                #    alpha_array * self.light_intensity * color * volume_array
                if light_volume:
                    m = volume_array * light_intensity * color
                    args = numpy.multiply(alpha_array, m)
                else:
                    args = alpha_array * light_intensity * color

                # light resultant calculation
                new_array = numpy.multiply(rgb_array, args).astype(numpy.uint16)

                # Cap the the array
                putmask(new_array, new_array > 255, 255)
                # putmask(new_array, new_array < 0, 0)

                self.Q_out.put(numpy.dstack((new_array, alpha_array)))
            else:
                time.sleep(0.001)

        print('LightSpot %s is dead.')


class CreateLight(object):
    """ Define light source properties and methods."""

    UPDATE = False

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
        self.timing = 30


    def flickering(self, rgb_array, alpha_array):
        assert isinstance(rgb_array, numpy.ndarray), \
            'Expecting numpy.ndarray for argument rgb_array got %s ' % type(rgb_array)
        assert isinstance(alpha_array, numpy.ndarray), \
            'Expecting numpy.ndarray for argument alpha_array got %s ' % type(alpha_array)

        color = numpy.array(self.light_shade[:3]) / 2
        new_array = numpy.multiply(rgb_array, alpha_array * self.light_intensity * color,
                                   dtype=numpy.float).astype(numpy.uint16)
        putmask(new_array, new_array > 255, 255)
        # putmask(new_array, new_array < 0, 0)
        new = numpy.dstack((new_array, alpha_array)) # .astype(dtype=numpy.uint8)
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
        self.color_index = 0

        # self.chunk, self.alpha, surface_size = self.get_light_spot()

        Q_in.put((self.position, self.light_shape, self.alpha_mask, RGB1))
        Queue = Q_out.get()
        self.chunk = Queue[0]
        self.alpha = Queue[1]
        surface_size = Queue[2]

        self.V0 = []
        if not self.mouse:
            if self.light_volume:
                i = 0
                for surface in self.volume:
                    self.volume[i] = pygame.transform.smoothscale(surface, (surface_size[0], surface_size[1]))
                    i += 1

                for surface in self.volume:
                    self.V0.append(pygame.surfarray.pixels3d(surface))


            Q_in_c.put((self.light_shade,
            self.light_variance,
            self.color_index,
            self.start_color_gradient, self.end_color_gradient,
            self.light_flickering,
            self.light_rotating,

            self.alpha_mask,
            self.counter,
            self.light_volume,
            self.mouse,
            self.V0,    # cannot pickle surface
            self.light_intensity,
            self.chunk,
            self.alpha))

            new = Q_out_c.get()
            self.image = pygame.image.frombuffer(new.transpose(1, 0, 2).copy('C').astype(numpy.uint8),
                                       (new.shape[:2][0], new.shape[:2][1]), 'RGBA')

            self.image_copy = self.image.copy()

            if self.light_flickering:
                self.image_flickering = self.flickering(self.chunk, self.alpha)

            self.offset_calculation()

        self.rect = self.image.get_rect(center=self.position + self.offset // 2)
        self.color_index = 0
        self.factor = 1


    def update(self):
        t = time.time()
        if self.dt > self.timing:

            # mouse cursor is a dynamic light source
            if self.mouse:
                self.position = MOUSE_POS
                self.chunk, self.alpha, surface_size = self.get_light_spot()
                self.offset = pygame.math.Vector2(0, 0)
                self.offset_calculation()
                self.rect = self.image.get_rect(center=self.position + self.offset // 2)

            # static light source
            else:

                # following effects require a constant re-calculation of the light flooded area.
                if self.light_variance or self.light_rotating or self.light_volume:

                    Q_in_c.put((self.light_shade,
                                self.light_variance,
                                self.color_index,
                                self.start_color_gradient, self.end_color_gradient,
                                self.light_flickering,
                                self.light_rotating,
                                self.alpha_mask,
                                self.counter,
                                self.light_volume,
                                self.mouse,
                                self.V0,  # cannot pickle surface
                                self.light_intensity,
                                self.chunk,
                                self.alpha))

                    new = Q_out_c.get()
                    self.image = pygame.image.frombuffer(new.transpose(1, 0, 2).copy('C').astype(numpy.uint8),
                                                         (new.shape[:2][0], new.shape[:2][1]), 'RGBA')


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
            CreateLight.UPDATE = True

        print(time.time() - t)
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

    Q_out = multiprocessing.Queue()
    Q_in = multiprocessing.Queue()
    Q_out_c = multiprocessing.Queue()
    Q_in_c = multiprocessing.Queue()
    event = multiprocessing.Event()
    LightSpot(Q_in, Q_out, event).start()
    LightCalc(Q_in_c, Q_out_c, event).start()

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

        All.update()

        if CreateLight.UPDATE:

            SCREEN.fill((0, 0, 0, 255))
            SCREEN.blit(TEXTURE1, (0, 0))
            All.draw(SCREEN)
            CreateLight.UPDATE = False
            for shadow in shadows:
                shadow.update(MOUSE_POS)
                shadow.render_frame()

            pygame.display.flip()
        """    
        SCREEN.fill((0, 0, 0, 255))
        SCREEN.blit(TEXTURE1, (0, 0))

        for shadow in shadows:
            shadow.update(MOUSE_POS)
            shadow.render_frame()

        All.update()
        All.draw(SCREEN)
        
        
        pygame.display.flip()
        """
        TIME_PASSED_SECONDS = clock.tick(120)
        FRAME += 1

    pygame.quit()
