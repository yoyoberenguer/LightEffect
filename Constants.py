__author__ = "Yoann Berenguer"
__copyright__ = "Copyright 2007."
__credits__ = ["Yoann Berenguer"]
__license__ = "MIT License"
__version__ = "2.0.0"
__maintainer__ = "Yoann Berenguer"
__email__ = "yoyoberenguer@hotmail.com"
__status__ = "Demo"

import pygame
from LoadTextureFile import spread_sheet_per_pixel
import numpy


# Map size
SIZE = (600, 600)
SCREENRECT = pygame.Rect((0, 0), SIZE)
pygame.init()
SCREEN = pygame.display.set_mode(SCREENRECT.size, pygame.RESIZABLE, 32)
SCREEN.fill((0, 0, 0, 0))

TEXTURE1 = pygame.image.load('Assets\\Base1.png').convert()
assert isinstance(TEXTURE1, pygame.Surface), 'TEXTURE1 should be a pygame.Surface, got %s ' % type(TEXTURE1)
assert TEXTURE1.get_size() > (0, 0), 'TEXTURE1 requires dimensions > (0, 0).'
assert TEXTURE1.get_bitsize() >= 24, \
    'TEXTURE1 bit depth should be 24-32 bit depth pixel format, got %s ' % TEXTURE1.get_bitsize()

TEXTURE1 = pygame.transform.smoothscale(TEXTURE1, SIZE)
UNSHADOWED_TEXTURE1 = TEXTURE1.copy()
TEXTURE1.set_alpha(10)
UNSHADOWED_TEXTURE1.set_alpha(35)

RGB1 = pygame.surfarray.array3d(TEXTURE1)
assert isinstance(RGB1, numpy.ndarray), 'RGB1 should be a numpy.ndarray, got %s ' % type(RGB1)
assert RGB1.size > 0, 'RGB1 array size should be  > 0.'


MASK_ALPHA = pygame.image.load('Assets\\radial4.png').convert_alpha()
assert isinstance(MASK_ALPHA, pygame.Surface), 'MASK_ALPHA should be a pygame.Surface, got %s ' % type(MASK_ALPHA)
assert MASK_ALPHA.get_size() > (0, 0), \
    'MASK_ALPHA requires dimensions > (0, 0), got (%s, %s) ' % MASK_ALPHA.get_size()
assert MASK_ALPHA.get_bitsize() >= 24, \
    'MASK_ALPHA bit depth should be 24-32 bit depth pixel format, got %s ' % MASK_ALPHA.get_bitsize()

# Light volumetric texture (project animated patterns)
VOLUMES = [spread_sheet_per_pixel('Assets\\smoke1.png', 256, 8, 8),
           spread_sheet_per_pixel('Assets\\smoke1_inv.png', 256, 8, 8),
           spread_sheet_per_pixel('Assets\\plasma_blue.png', 128, 20, 18, False)]

assert len(VOLUMES) > 0, 'VOLUMES should not be empty if you are using volumetric textures.'
for i in range(len(VOLUMES)):
    for surface in VOLUMES[i]:

        assert isinstance(surface, pygame.Surface), \
            'Volumetric textures should be a pygame.Surface, got %s.' % type(surface)
        assert surface.get_size() > (0, 0), \
            'Volumetric texture with incorrect dimensions. (%s, %s) ' % surface.get_size()
        assert surface.get_bitsize() >= 24, \
            'Volumetric texture bit depth should be 24-32 bit depth pixel format, got %s ' % surface.get_bitsize()

# ***************************
# Light obstacles
# Create polygons into the scene for shadow projection
# ***************************

# Screen border segments
BORDER = [{"a": {"x": SCREENRECT.topleft[0], "y": SCREENRECT.topleft[1]},
           "b": {"x": SCREENRECT.topright[0], "y": SCREENRECT.topright[1]}},
          {"a": {"x": SCREENRECT.topright[0], "y": SCREENRECT.topright[1]},
           "b": {"x": SCREENRECT.bottomright[0], "y": SCREENRECT.bottomright[1]}},
          {"a": {"x": SCREENRECT.bottomright[0], "y": SCREENRECT.bottomright[1]},
           "b": {"x": SCREENRECT.bottomleft[0], "y": SCREENRECT.bottomleft[1]}},
          {"a": {"x": SCREENRECT.bottomleft[0], "y": SCREENRECT.bottomleft[1]},
           "b": {"x": SCREENRECT.topleft[0], "y": SCREENRECT.topleft[1]}}]

POLYGON1 = [{"a": {"x": 50, "y": 155}, "b": {"x": 240, "y": 153}},
            {"a": {"x": 240, "y": 153}, "b": {"x": 240, "y": 216}},
            {"a": {"x": 240, "y": 216}, "b": {"x": 50, "y": 216}},
            {"a": {"x": 50, "y": 216}, "b": {"x": 50, "y": 155}}]

POLYGON2 = [
    {"a": {"x": 333, "y": 66}, "b": {"x": 408, "y": 66}},
    {"a": {"x": 408, "y": 66}, "b": {"x": 408, "y": 123}},
    {"a": {"x": 408, "y": 123}, "b": {"x": 333, "y": 125}},
    {"a": {"x": 333, "y": 125}, "b": {"x": 333, "y": 66}}]
POLYGON3 = [
    {"a": {"x": 333, "y": 154}, "b": {"x": 412, "y": 154}},
    {"a": {"x": 412, "y": 154}, "b": {"x": 412, "y": 216}},
    {"a": {"x": 412, "y": 216}, "b": {"x": 333, "y": 216}},
    {"a": {"x": 333, "y": 216}, "b": {"x": 333, "y": 154}}]
POLYGON4 = [
    {"a": {"x": 296, "y": 280}, "b": {"x": 435, "y": 280}},
    {"a": {"x": 435, "y": 280}, "b": {"x": 435, "y": 344}},
    {"a": {"x": 435, "y": 344}, "b": {"x": 296, "y": 344}},
    {"a": {"x": 296, "y": 344}, "b": {"x": 296, "y": 280}}]

POLYGON5 = [
    {"a": {"x": 43, "y": 335}, "b": {"x": 135, "y": 335}},
    {"a": {"x": 135, "y": 335}, "b": {"x": 135, "y": 375}},
    {"a": {"x": 135, "y": 375}, "b": {"x": 43, "y": 375}},
    {"a": {"x": 43, "y": 375}, "b": {"x": 43, "y": 335}}]

ALL_SEGMENTS = [*BORDER, *POLYGON1, *POLYGON2, *POLYGON3, *POLYGON4, *POLYGON5]

# ************************
# Light definition
# ************************


def light_preparation(light_shape_, mask_alpha_):
    """Adjust the mask alpha dimension to the light shape. """
    assert isinstance(light_shape_, tuple), \
        'Expecting tuple for argument light_shape_ got %s ' % type(light_shape_)
    assert isinstance(mask_alpha_, pygame.Surface), \
        'Expecting pygame.Surface for argument mask_alpha_ got %s ' % type(mask_alpha_)

    assert light_shape_ > (0, 0), 'argument light_shape_ should be a tuple above (0, 0)'
    assert mask_alpha_.get_size() > (0, 0), 'mask_alpha_ dimension should always be > (0, 0)'
    light_area_ = pygame.transform.smoothscale(mask_alpha_, light_shape_)
    sub_alpha_ = pygame.surfarray.array_alpha(light_area_)
    return sub_alpha_.reshape(*light_shape_, 1)


light_shape = (250, 250)
assert SIZE > light_shape, 'SCREEN size should be greater than the largest light_shape: ({},{}) '.format(*light_shape)
# Re-scaling all the volumetric textures
i = 0
for effect in VOLUMES:
    j = 0
    for surface in effect:
        VOLUMES[i][j] = pygame.transform.smoothscale(surface, light_shape)
        j += 1
    i += 1

"""
LIGHTS = []
from random import randint
for r in range (5):
    LIGHTS.append(('Spotlight'+str(r),                                     # light name
          light_shape,                                      # illuminated area from the source point
          pygame.Color(randint(0, 255), randint(0, 255), randint(0, 255), 5),                   # Light color (light_shade)
          light_preparation(light_shape, MASK_ALPHA),       # Create the mask alpha for a given dimension (shape)
          False,                                            # light flickering?
          True,                                             # light variance? (color gradient)
          False,                                            # light rotating?
          False,                                             # light with volume?
          pygame.Color(randint(0, 255), randint(0, 255), randint(0, 255)),                   # start color gradient
          pygame.Color(randint(0, 255), randint(0, 255), randint(0, 255)),                     # end color gradient
          0.7e-4,                                           # light intensity
          (randint(0, SIZE[0]), randint(0, SIZE[1])),                                        # Source coordinates in the plan (x,y)
          VOLUMES[randint(0,2)]

          ))
"""


LIGHT1 = ('Spotlight1',                                     # light name
          light_shape,                                      # illuminated area from the source point
          pygame.Color(150, 160, 201, 5),                   # Light color (light_shade)
          light_preparation(light_shape, MASK_ALPHA),       # Create the mask alpha for a given dimension (shape)
          False,                                            # light flickering?
          True,                                             # light variance? (color gradient)
          False,                                            # light rotating?
          True,                                             # light with volume?
          pygame.Color(150, 160, 201, 5),                   # start color gradient
          pygame.Color(20, 20, 20, 10),                     # end color gradient
          0.7e-4,                                           # light intensity
          (370, 94),                                        # Source coordinates in the plan (x,y)
          VOLUMES[0]

          )                                       # Volume texture to be used if volume is True

LIGHT2 = ('Spotlight2', light_shape, pygame.Color(165, 162, 180, 0),
          light_preparation(light_shape, MASK_ALPHA),
          False, False, False, False, pygame.Color(150, 160, 201, 0), pygame.Color(150, 160, 201, 0),
          2e-4, (370, 186), None)

light_shape = (300, 180)
LIGHT3 = ('Spotlight3', light_shape, pygame.Color(150, 160, 201, 0),
          light_preparation(light_shape, MASK_ALPHA),
          False, False, False, True, pygame.Color(150, 160, 201, 0), pygame.Color(22, 25, 35, 0),
          0.8e-4, (88, 357), VOLUMES[1])

light_shape = (400, 400)
LIGHT4 = ('Spotlight4', light_shape, pygame.Color(200, 50, 61, 0),
          light_preparation(light_shape, MASK_ALPHA),
          False, False, False, False, pygame.Color(220, 98, 101, 0), pygame.Color(30, 5, 8, 0),
          0.7e-4, (480, 269), None)

light_shape = (400, 400)
LIGHT6 = ('Spotlight6', light_shape, pygame.Color(200, 200, 10, 0),
          light_preparation(light_shape, MASK_ALPHA),
          False, True, False, False, pygame.Color(220, 220, 10, 0), pygame.Color(230, 18, 0, 0),
          1e-4, (150, 200), None)

light_shape = (600, 600)
LIGHT5 = ('Spotlight5', light_shape, pygame.Color(200, 200, 200, 0),
          light_preparation(light_shape, pygame.image.load('Assets\\radialTrapezoid.png').convert_alpha()),
          False, False, False, False, pygame.Color(220, 210, 212, 0), pygame.Color(20, 20, 21, 0),
          0.6e-4, SCREENRECT.center, None)

# Yellow rotating light
light7_rotation = []
light_shape = (100, 100)
MASK_ALPHA_ = pygame.image.load('Assets\\RadialWarning.png').convert_alpha()
light_area_org = pygame.transform.smoothscale(MASK_ALPHA_, light_shape)
for r in range(360):
    light_area = pygame.transform.rotate(light_area_org.copy(), r * 6)
    light_area = pygame.transform.smoothscale(light_area, light_shape)
    sub_alpha = pygame.surfarray.array_alpha(light_area)
    sub_alpha_reshape = sub_alpha.reshape(*light_shape, 1)
    light7_rotation.append(sub_alpha_reshape)

LIGHT7 = ('Spotlight7', light_shape, pygame.Color(120, 170, 21, 0), light7_rotation,
          False, False, True, False, pygame.Color(220, 150, 10, 0), pygame.Color(220, 150, 10, 0),
          1.8e-4, (190, 360), None)

light8_rotation = []
light_shape = (100, 100)
MASK_ALPHA_ = pygame.image.load('Assets\\Radial4.png').convert_alpha()
light_area_org = pygame.transform.smoothscale(MASK_ALPHA_, light_shape)
for r in range(360):
    light_area = pygame.transform.rotate(light_area_org.copy(), r * 6)
    light_area = pygame.transform.smoothscale(light_area, light_shape)
    sub_alpha = pygame.surfarray.array_alpha(light_area)
    sub_alpha_reshape = sub_alpha.reshape(*light_shape, 1)
    light8_rotation.append(sub_alpha_reshape)

LIGHT8 = ('Spotlight8', light_shape, pygame.Color(150, 125, 220, 0), light8_rotation,
          False, False, True, False, pygame.Color(20, 12, 220, 0), pygame.Color(20, 12, 220, 0),
          1.8e-4, (368, 313), None)


light_shape = (300, 300)
LIGHT9 = ('MOUSE_CURSOR', light_shape, pygame.Color(138, 222, 219, 0), light_preparation(light_shape, MASK_ALPHA),
          False, False, False, False, pygame.Color(220, 150, 10, 0), pygame.Color(220, 150, 10, 0),
          1.8e-4, (190, 360), None, True)


LIGHTS = [LIGHT1, LIGHT2, LIGHT3, LIGHT4, LIGHT5, LIGHT6, LIGHT7, LIGHT8, LIGHT9]

# LIGHTS = [LIGHT1]

# cleaning up
del LIGHT1, LIGHT2, LIGHT3, LIGHT4, LIGHT5, LIGHT6, LIGHT7, light7_rotation, light8_rotation, light_area_org
del light_shape, light_area, sub_alpha, sub_alpha_reshape, MASK_ALPHA_


STOP_GAME = False
PAUSE = False
FRAME = 0
TIME_PASSED_SECONDS = 0
MOUSE_POS = SCREENRECT.center

assert len(ALL_SEGMENTS) > 0, 'At least one polygon need to be define for the shadow projection algorithm.'
assert len(LIGHTS) > 0, 'At least one light source needs to be define.'