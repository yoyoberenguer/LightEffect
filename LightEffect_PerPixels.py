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
"""

__author__ = "Yoann Berenguer"
__copyright__ = "Copyright 2007."
__credits__ = ["Yoann Berenguer"]
__license__ = "MIT License"
__version__ = "1.0.0"
__maintainer__ = "Yoann Berenguer"
__email__ = "yoyoberenguer@hotmail.com"
__status__ = "Demo"


'''
   Special thanks to Marcus Møller (https://github.com/marcusmoller) for its shadow algorithm 
'''

import pygame
from pygame import gfxdraw
import numpy
from numpy import putmask, dstack, transpose, array, arange, repeat, newaxis
import timeit
import random
import math


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

    color = LIGHT_SHADE[:3]

    if LIGHT_VARIANCE:
        color = gradient(index_=color_index_)

    blend = numpy.multiply(rgb1_, alpha2_ * LIGHT_INTENSITY * color,
                           dtype=numpy.float16).astype(numpy.uint16)

    numpy.putmask(blend, blend > 255, 255)
    new_array = numpy.add(rgb1_, blend, dtype=numpy.float16) # dtype=numpy.uint16)
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
        chunk = RGB[mouse_x - w_low:mouse_x + w_high, mouse_y - h_low:mouse_y + h_high, :]
        # select the entire mask alpha or just a portion, depends on the mouse coordinates.
        alpha = ALPHA2_RESHAPE[lx - w_low:lx + w_high, ly - h_low:ly + h_high, :]

        # chunk SIZE must be > 0
        if chunk.size > 0:
            self.image = soft_radial_light(chunk, alpha, self.color_index)

        self.rect.topleft = (mouse_x - w_low, mouse_y - h_low)
        self.color_index += self.factor
        if self.color_index >= 255 or self.color_index <= 0:
            self.factor *= -1
        pass


class Shadow:

    def __init__(self, screen, screenrect):
        self.screen = screen
        self.mouse_pos = mouse_pos
        self.intersects = []
        self.points = []
        self.segments = [
            # Border
            {"a": {"x": screenrect.topleft[0], "y": screenrect.topleft[1]},
             "b": {"x": screenrect.topright[0], "y": screenrect.topright[1]}},
            {"a": {"x": screenrect.topright[0], "y": screenrect.topright[1]},
             "b": {"x": screenrect.bottomright[0], "y": screenrect.bottomright[1]}},
            {"a": {"x": screenrect.bottomright[0], "y": screenrect.bottomright[1]},
             "b": {"x": screenrect.bottomleft[0], "y": screenrect.bottomleft[1]}},
            {"a": {"x": screenrect.bottomleft[0], "y": screenrect.bottomleft[1]},
             "b": {"x": screenrect.topleft[0], "y": screenrect.topleft[1]}},

            # Polygon #1
            {"a": {"x": 50, "y": 155}, "b": {"x": 240, "y": 153}},
            {"a": {"x": 240, "y": 153}, "b": {"x": 240, "y": 216}},
            {"a": {"x": 240, "y": 216}, "b": {"x": 50, "y": 216}},
            {"a": {"x": 50, "y": 216}, "b": {"x": 50, "y": 155}},

            # Polygon #2
            {"a": {"x": 333, "y": 66}, "b": {"x": 408, "y": 66}},
            {"a": {"x": 408, "y": 66}, "b": {"x": 408, "y": 123}},
            {"a": {"x": 408, "y": 123}, "b": {"x": 333, "y": 125}},
            {"a": {"x": 333, "y": 125}, "b": {"x": 333, "y": 66}},

            # Poly #3
            {"a": {"x": 333, "y": 154}, "b": {"x": 412, "y": 154}},
            {"a": {"x": 412, "y": 154}, "b": {"x": 412, "y": 216}},
            {"a": {"x": 412, "y": 216}, "b": {"x": 333, "y": 216}},
            {"a": {"x": 333, "y": 216}, "b": {"x": 333, "y": 154}},

            # Poly #4
            {"a": {"x": 296, "y": 280}, "b": {"x": 435, "y": 280}},
            {"a": {"x": 435, "y": 280}, "b": {"x": 435, "y": 344}},
            {"a": {"x": 435, "y": 344}, "b": {"x": 296, "y": 344}},
            {"a": {"x": 296, "y": 344}, "b": {"x": 296, "y": 280}},

            # Poly #5
            {"a": {"x": 43, "y": 335}, "b": {"x": 135, "y": 335}},
            {"a": {"x": 135, "y": 335}, "b": {"x": 135, "y": 375}},
            {"a": {"x": 135, "y": 375}, "b": {"x": 43, "y": 375}},
            {"a": {"x": 43, "y": 375}, "b": {"x": 43, "y": 335}},
        ]

    def get_intersection(self, ray, segment):

        ''' Find intersection of RAY & SEGMENT '''
        # RAY in parametric: Point + Direction*T1
        r_px = ray['a']['x']
        r_py = ray['a']['y']
        r_dx = ray['b']['x'] - r_px
        r_dy = ray['b']['y'] - r_py

        # SEGMENT in parametric: Point + Direction*T2
        s_px = segment['a']['x']
        s_py = segment['a']['y']
        s_dx = segment['b']['x'] - s_px
        s_dy = segment['b']['y'] - s_py

        # Are they parallel? If so, no intersect
        r_mag = r_dx ** 2 + r_dy ** 2
        s_mag = s_dx ** 2 + s_dy ** 2

        if r_dx / r_mag == s_dx / s_mag and r_dy / r_mag == s_dy / s_mag:
            return None

        try:
            T2 = (r_dx * (s_py - r_py) + r_dy * (r_px - s_px)) / (s_dx * r_dy - s_dy * r_dx)
        except ZeroDivisionError:
            T2 = (r_dx * (s_py - r_py) + r_dy * (r_px - s_px)) / (s_dx * r_dy - s_dy * r_dx - 0.01)


        try:
            T1 = (s_px + s_dx * T2 - r_px) / r_dx
        except ZeroDivisionError:
            T1 = (s_px + s_dx * T2 - r_px) / (r_dx - 0.01)

        # Must be within parametric whatever for RAY/SEGMENT
        # T1 < 0, intersection found behind the ray cast direction
        if T1 < 0:
            return None
        # T2 can be assimilate to a vector magnitude normalized and shall not
        # goes over 1.
        if T2 < 0 or T2 > 1:
            return None

        # Return the POINT OF INTERSECTION
        return {
            "x": r_px + r_dx * T1,
            "y": r_py + r_dy * T1,
            "T1": T1
        }

    def update(self):
        # Clear old points
        self.points = []
        # Get all unique points
        for segment in self.segments:
            self.points.append((segment['a'], segment['b']))
        # Just do a copy of self.points
        unique_points = self.points.copy()

        # Get all angles in radian
        unique_angles = []
        for point in unique_points:
            self.mouse_pos = mouse_pos
            angle = math.atan2(point[0]["y"] - self.mouse_pos[1], point[0]["x"] - self.mouse_pos[0])
            point[0]["angle"] = angle
            # For each (unique) line segment end point,
            # I cast a ray directly towards it,
            # plus two more rays offset by +/- 0.00001 radians.
            # The two extra rays are needed to hit the wall(s) behind any given segment corner.
            unique_angles.append(angle - 0.00001)
            unique_angles.append(angle)
            unique_angles.append(angle + 0.00001)

        # RAYS IN ALL DIRECTIONS
        self.intersects = []
        for angle in unique_angles:

            # Calculate dx & dy from angle
            dx = math.cos(angle)
            dy = math.sin(angle)
            # Ray,
            # segment (a) is the mouse position (also ray origin)
            # segment (b) is the slope or direction
            ray = {
                "a": {"x": self.mouse_pos[0], "y": self.mouse_pos[1]},
                "b": {"x": self.mouse_pos[0] + dx, "y": self.mouse_pos[1] + dy}
            }

            # Find CLOSEST intersection
            # With a given angle (angle between the point segment (a) and mouse position),
            # goes through all the segments (polygons and screen edges) and find the nearest segment
            # that collide with the Ray cast at that angle (mouse position).
            closest_intersect = None
            for segment in self.segments:

                # return the point of intersection (coordinates x, y, T1) if any (else return None)
                intersect = self.get_intersection(ray, segment)
                # if no intersection, loop back
                if not intersect:
                    continue
                # check that the current intersection point is now the nearest (by comparing T1
                # with the previous one recorded into closest_intersect).
                # T1 is the distance between the Ray origin and the intersection point.
                if not closest_intersect or intersect["T1"] < closest_intersect["T1"]:
                    closest_intersect = intersect

            # if no intersection, loop back (next angle selected from the list)
            if not closest_intersect:
                continue
            # found the nearest intersection,
            # update closest_intersect with an angle value
            closest_intersect["angle"] = angle

            # add the intersection point to the list
            self.intersects.append(closest_intersect)

        # complete the search through all angles and all segments.
        # sort the data by angle to create polygons.
        self.intersects = sorted(self.intersects, key=lambda k: k['angle'])

    def draw_polygon(self, polygon):
        # collect coordinates for a giant polygon
        points = []
        for intersect in polygon:
            points.append((intersect['x'], intersect['y']))
        pygame.gfxdraw.textured_polygon(self.screen, points, texture1_visible, 0, 0)

    def render_frame(self):
        self.draw_polygon(self.intersects)


if __name__ == '__main__':

    numpy.set_printoptions(threshold=numpy.nan)

    pygame.init()
    # Map SIZE
    size = (600, 600)
    SCREENRECT = pygame.Rect((0, 0), size)
    screen = pygame.display.set_mode(SCREENRECT.size, pygame.RESIZABLE, 32)
    # path to the background picture
    background = pygame.image.load('Assets\\background.png').convert()
    background = pygame.transform.smoothscale(background, size)
    screen.blit(background, (0, 0))

    # Background
    surface1 = 'Assets\\Base1.png'
    # Loading the per-pixel surface
    texture1 = pygame.image.load(surface1).convert_alpha()
    texture1 = pygame.transform.smoothscale(texture1, size)

    # Shadow texture
    texture1_visible = pygame.image.load(surface1).convert()
    texture1_visible = pygame.transform.smoothscale(texture1_visible, size)
    texture1_visible.set_colorkey((0, 0, 0, 0))
    texture1_visible.set_alpha(100)

    # loading the surface into an array
    RGB = pygame.surfarray.array3d(texture1)
    # Change the surface brightness
    RGB = numpy.multiply(RGB, 0.2, dtype=numpy.float16).astype(dtype=numpy.uint16)
    numpy.putmask(RGB, RGB < 0, 0)

    # load the surface alpha channel
    ALPHA = pygame.surfarray.array_alpha(texture1)
    ALPHA = numpy.multiply(ALPHA, 1).astype(dtype=numpy.uint8) # x1 no change
    # Create a new surface
    texture1 = make_surface(make_array(RGB, ALPHA))
    # display the new texture (low brightness)
    screen.blit(texture1, (0, 0))

    # Radial mask to use
    surface2 = 'Assets\\radial4.png'
    texture2 = pygame.image.load(surface2).convert_alpha()
    # lit area (x=200, y=200)
    LIGHT_SIZE_EFFECT = (400, 400)
    # set the light color and intensity
    LIGHT_SHADE = pygame.Color(180, 180, 200)
    texture2 = pygame.transform.smoothscale(texture2, LIGHT_SIZE_EFFECT)
    ALPHA2 = pygame.surfarray.array_alpha(texture2)
    # Reshape the array to work from a 3d array instead of 2d
    ALPHA2_RESHAPE = ALPHA2.reshape((LIGHT_SIZE_EFFECT[0], LIGHT_SIZE_EFFECT[1], 1))

    LIGHT_VARIANCE = True

    GRAD_END_COLOR = pygame.Color(128, 128, 250, 255)
    GRAD_START_COLOR = pygame.Color(80, 80, 80, 255)
    LIGHT_INTENSITY = 0.0008

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

    mouse_pos = SCREENRECT.center
    Sh = Shadow(screen, SCREENRECT)

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

            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos

            if keys[pygame.K_SPACE]:
                pass

            elif keys[pygame.K_PAUSE]:
                PAUSE = True
                print('Pauseed')

        screen.blit(background, (0, 0))
        screen.blit(texture1, (0, 0))

        Sh.update()
        Sh.render_frame()

        All.update()
        All.draw(screen)

        pygame.display.flip()
        TIME_PASSED_SECONDS = clock.tick(120)
        FRAME += 1

    pygame.quit()          
