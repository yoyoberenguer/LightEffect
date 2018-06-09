"""
   Special thanks to Marcus Møller (https://github.com/marcusmoller) for its shadow algorithm
"""

__author__ = "Yoann Berenguer"
__copyright__ = "Copyright 2007."
__credits__ = ["Yoann Berenguer"]
__license__ = "MIT License"
__version__ = "2.0.0"
__maintainer__ = "Yoann Berenguer"
__email__ = "yoyoberenguer@hotmail.com"
__status__ = "Demo"

import pygame
from pygame import gfxdraw
import math
from Constants import UNSHADOWED_TEXTURE1, MOUSE_POS, SCREEN


class Shadow:

    def __init__(self, polygons_, static_=False, location_=None):
        assert isinstance(polygons_, list), 'Expecting list for ' \
                                            'argument polygons_ got %s ' % type(polygons_)
        assert isinstance(static_, bool), 'Expecting bool for ' \
                                          'argument static_ got %s ' % type(static_)
        assert isinstance(location_, (type(None), tuple)), 'Expecting tuple or None for ' \
                                                           'argument location_ got %s ' % type(location_)
        self.static = static_
        if self.static is True:
            assert isinstance(location_, tuple), 'Expecting tuple for ' \
                                                           'argument location_ got %s ' % type(location_)
        self.location = location_
        self.intersects = []
        self.points = []
        self.segments = polygons_

    @staticmethod
    def get_intersection(ray, segment):

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

        # Lines are parallel if they have the same angle (cos and sin)
        # if the sum of their angle is equal to 180 degrees
        # if their slopes are equal
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

    def update(self, mouse_position):
        assert isinstance(mouse_position, tuple), 'Expecting tuple for ' \
                                            'argument mouse_position got %s ' % type(mouse_position)
        # Clear old points
        self.points = []
        for segment in self.segments:
            self.points.append((segment['a'], segment['b']))

        unique_points = self.points.copy()

        # Get all angles in radian
        unique_angles = []
        for point in unique_points:
            if self.static:
                angle = math.atan2(point[0]["y"] - self.location[1], point[0]["x"] - self.location[0])
            else:
                angle = math.atan2(point[0]["y"] - mouse_position[1], point[0]["x"] - mouse_position[0])
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

            dx = math.cos(angle)
            dy = math.sin(angle)
            # Ray,
            # segment (a) is the mouse position (also ray origin)
            # segment (b) is the slope or direction

            if self.static:
                ray = {
                    "a": {"x": self.location[0], "y": self.location[1]},
                    "b": {"x": self.location[0] + dx, "y": self.location[1] + dy}
                }
            else:
                ray = {
                    "a": {"x": mouse_position[0], "y": mouse_position[1]},
                    "b": {"x": mouse_position[0] + dx, "y": mouse_position[1] + dy}
                }

            # Find CLOSEST intersection
            closest_intersect = None
            for segment in self.segments:

                # return the point of intersection (coordinates x, y, T1) if any (else return None)
                intersect = self.get_intersection(ray, segment)
                # if no intersection, loop back
                if not intersect:
                    continue

                if not closest_intersect or intersect["T1"] < closest_intersect["T1"]:
                    closest_intersect = intersect

            if not closest_intersect:
                continue

            closest_intersect["angle"] = angle
            self.intersects.append(closest_intersect)
        self.intersects = sorted(self.intersects, key=lambda k: k['angle'])

    @staticmethod
    def draw_polygon(polygon):
        assert isinstance(polygon, list), 'Expecting list for ' \
                                                  'argument polygon got %s ' % type(polygon)
        points = []
        for intersect in polygon:
            points.append((intersect['x'], intersect['y']))
        pygame.gfxdraw.textured_polygon(SCREEN, points, UNSHADOWED_TEXTURE1, 0, 0)

    def render_frame(self):
        self.draw_polygon(self.intersects)
