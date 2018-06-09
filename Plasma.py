
import pygame
from pygame import gfxdraw
import math
import timeit
import colorsys
import numpy
import time



def Generate_plasma():
    for x in range(w):
        for y in range(h):

            color = int(
                128.0 + (128.0 * math.sin(x / 16.0)) +
                128.0 + (128.0 * math.sin(y / 8.0)) +
                128.0 + (128.0 * math.sin(x + y) / 16.0) +
                128.0 + (128.0 * math.sin(math.sqrt(x ** 2 + y ** 2) / 8.0))
            ) / 4

            plasma[x][y] = color


def Generate_palette():
    """
    >> > import colorsys
    >> > colorsys.rgb_to_hsv(0.2, 0.4, 0.4)
    (0.5, 0.5, 0.4)
    >> > colorsys.hsv_to_rgb(0.5, 0.5, 0.4)
    (0.2, 0.4, 0.4)
    """

    for r in range(256):
        hsv = colorsys.hsv_to_rgb(r/255, 1, 1)
        palette[r] = tuple([int(c * 255) for c in hsv])
        # palette[r] = hsv


if __name__ == '__main__':
    w, h = 128, 128
    SCREENRECT = pygame.Rect(0, 0, w, h)
    screen = pygame.display.set_mode(SCREENRECT.size, pygame.FULLSCREEN, 8)

    pygame.display.init()

    # print(timeit.timeit("plasma()", "from __main__ import plasma", number=10)/10)
    plasma = numpy.zeros([w, h, 3], dtype=numpy.uint8)
    palette = [0] * 256
    Generate_palette()
    Generate_plasma()




    i = 0
    STOP_GAME = False
    PAUSE = False
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

            elif keys[pygame.K_PAUSE]:
                PAUSE = True
                print('Paused')


        for x in range(w):
            for y in range(h):
                # screen.set_at((x, y), palette[(plasma[x][y] + i) % w])

                gfxdraw.pixel(screen, x, y, palette[(plasma[x][y][0] + i) % 256])
        # pygame.display.set_palette(palette)

        pygame.display.flip()
        i += 1
    pygame.quit()
