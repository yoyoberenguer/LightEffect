"""
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
__version__ = "2.0.0"
__maintainer__ = "Yoann Berenguer"
__email__ = "yoyoberenguer@hotmail.com"
__status__ = "Demo"

import numpy
import pygame


def make_array(rgb_array_: numpy.ndarray, alpha_: numpy.ndarray) -> numpy.ndarray:
    """
    This function is use for 32-24 bit texture with pixel alphas transparency

    make_array(RGB array, alpha array) -> RGBA array

    Return a 3D numpy array representing (R, G, B, A) values of a pixel alphas texture (numpy.uint8).
    Argument surface_ is a pixels3d containing RGB values and alpha is a 2D pixels_alpha array.

    :param rgb_array_: 3D numpy array created with pygame.surfarray_pixels3d() representing the
                       RGB values of the pixel alphas texture.
    :param alpha_:     2D numpy array created with pygame.surfarray.pixels_alpha() representing
                       the alpha pixels texture layer
    :return:           Return a numpy 3D array (numpy.uint8) storing a transparency value for every pixel
                       This allow the most precise transparency effects, but it is also the slowest.
                       Per pixel alphas cannot be mixed with surface alpha colorkeys (this will have
                       no effect).
    """
    assert isinstance(rgb_array_, numpy.ndarray), \
        'Expecting numpy.ndarray for argument rgb_array_ got %s ' % type(rgb_array_)
    assert isinstance(alpha_, numpy.ndarray), \
        'Expecting numpy.ndarray for argument alpha_ got %s ' % type(alpha_)

    return numpy.dstack((rgb_array_, alpha_)).astype(dtype=numpy.uint8)


def make_surface(rgba_array: numpy.ndarray) -> pygame.Surface:
    """
    This function is use for 32-24 bit texture with pixel alphas transparency only

    make_surface(RGBA array) -> Surface

    Return a Surface created with the method frombuffer
    Argument rgba_array is a numpy array containing RGB values + alpha channel.
    This method create a texture with per-pixel alpha values.
    'frombuffer' can display image with disproportional scaling (X&Y scale),
    but the image will be distorted. Use array = original_array.copy(order='C') to
    force frombuffer to accept disproportional image.
    Another method is to scale the original image with irregular X&Y values
    before processing the image with frombuffer (therefore this could create
    undesirable effect in sprite animation, sprite deformation etc).

    :param rgba_array: 3D numpy array created with the method surface.make_array.
                       Combine RGB values and alpha values.
    :return:           Return a pixels alpha texture.This texture contains a transparency value
                       for each pixels.
    """
    assert rgba_array.shape[:2][0] != 0, 'ValueError: Resolution must be positive values '
    assert rgba_array.shape[:2][1] != 0, 'ValueError: Resolution must be positive values '

    assert isinstance(rgba_array, numpy.ndarray), 'Expecting numpy.ndarray for ' \
                                                  'argument rgb_array got %s ' % type(rgba_array)
    return pygame.image.frombuffer((rgba_array.transpose(1, 0, 2)).copy(order='C').astype(numpy.uint8),
                                   (rgba_array.shape[:2][0], rgba_array.shape[:2][1]), 'RGBA')


class ERROR(BaseException):
    pass


def spread_sheet_per_pixel(file: str, chunk: int, rows_: int, columns_: int, tweak_: bool = False, *args) -> list:
    """
    Works only for 32-24/8 bit
    # Return a python list containing all images (Surface) from a given sprite sheet
    # Every images/surface from the list have a per-pixels texture transparency.
    # Method set_colorkey and set_alpha will have no effect.
    :param file: Path to the file
    :param chunk: Pixel SIZE of the chunk
    :param rows_: Number of rows in the sprite sheet
    :param columns_: Number of columns in the sprite sheet
    :param tweak_: Bool to adjust the block SIZE to copy (disproportional chunk)
    :return: Return a list of sprite with per-pixels transparency.
    """
    """Return a python list containing all images from a given sprite sheet."""
    assert isinstance(file, str), 'Expecting string for argument file got %s: ' % type(file)
    assert isinstance(chunk, int), 'Expecting int for argument number got %s: ' % type(chunk)
    assert isinstance(rows_, int) and isinstance(columns_, int), 'Expecting int for argument rows_ and columns_ ' \
                                                                 'got %s, %s ' % (type(rows_), type(columns_))
    try:
        # The returned Surface will contain the same color format,
        #  colorkey and alpha transparency as the file it came from.
        image_ = pygame.image.load(file)
        # Create arrays from surface and alpha channel (numpy array)
        surface_ = pygame.surfarray.pixels3d(image_)  # 3d numpy array with RGB values

        if image_.get_bitsize() == 32:
            alpha_ = pygame.surfarray.pixels_alpha(image_)
        elif image_.get_bitsize() in (24, 8):
            alpha_ = pygame.surfarray.array_alpha(image_)
        else:
            raise ERROR('\n[-] Texture is not 32-24/8 bit surface, got %s bit' % image_.get_bitsize())
        # Make a surface containing RGB and alpha values
        array = make_array(surface_, alpha_)
        animation = []
        # split sprite-sheet into many sprites
        for rows in range(rows_):
            for columns in range(columns_):
                if tweak_:
                    chunkx = args[0]
                    chunky = args[1]
                    array1 = array[columns * chunkx:(columns + 1) * chunkx, rows * chunky:(rows + 1) * chunky, :]
                else:
                    array1 = array[columns * chunk:(columns + 1) * chunk, rows * chunk:(rows + 1) * chunk, :]
                surface_ = make_surface(array1)
                animation.append(surface_)
        return animation
    except pygame.error:
        raise SystemExit('\n[-] Error : Could not load image %s %s ' % (file, pygame.get_error()))