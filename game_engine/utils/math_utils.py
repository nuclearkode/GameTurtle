"""
Math utilities for game calculations.
Vector math, distance, angles, etc.
"""

import math
from typing import Tuple


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Euclidean distance between two points"""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def distance_squared(x1: float, y1: float, x2: float, y2: float) -> float:
    """Squared distance (faster, no sqrt)"""
    return (x2 - x1) ** 2 + (y2 - y1) ** 2


def normalize(x: float, y: float) -> Tuple[float, float]:
    """Normalize a 2D vector"""
    length = math.sqrt(x * x + y * y)
    if length < 0.0001:
        return (0.0, 0.0)
    return (x / length, y / length)


def angle_between(x1: float, y1: float, x2: float, y2: float) -> float:
    """Angle in degrees from point 1 to point 2"""
    dx = x2 - x1
    dy = y2 - y1
    angle = math.degrees(math.atan2(dy, dx))
    return angle


def rotate_vector(x: float, y: float, angle_degrees: float) -> Tuple[float, float]:
    """Rotate a 2D vector by angle in degrees"""
    angle_rad = math.radians(angle_degrees)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    return (new_x, new_y)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b"""
    return a + (b - a) * clamp(t, 0.0, 1.0)


def deg_to_rad(degrees: float) -> float:
    """Convert degrees to radians"""
    return math.radians(degrees)


def rad_to_deg(radians: float) -> float:
    """Convert radians to degrees"""
    return math.degrees(radians)
