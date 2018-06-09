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
import time
import multiprocessing
from lightEngine import *
from Shadows import *
import ctypes


if __name__ == '__main__':

    numpy.set_printoptions(threshold=numpy.nan)

    SCREEN.blit(TEXTURE1, (0, 0))
    pygame.display.flip()

    LIGHT_GROUP = pygame.sprite.Group()
    All = pygame.sprite.RenderUpdates()
    ShowLight.containers = LIGHT_GROUP, All
    # create a dummy surface
    ShowLight.images = pygame.Surface((1, 1), 32)
    TIME_PASSED_SECONDS = 0
    Tid = id(TIME_PASSED_SECONDS)

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
                CreateLight.MOUSE_POS = event.pos

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

        CreateLight.time_passed_seconds = clock.tick(300)
        print(round(clock.get_fps()))

        FRAME += 1

    pygame.quit()
