"""
Math utilities for game calculations.

Provides vector operations, distance calculations, angle conversions, etc.
"""

import math
from typing import Tuple


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Euclidean distance between two points."""
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)


def distance_squared(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate squared distance (faster, good for comparisons)."""
    dx = x2 - x1
    dy = y2 - y1
    return dx * dx + dy * dy


def normalize(x: float, y: float) -> Tuple[float, float]:
    """
    Normalize a vector to unit length.
    Returns (0, 0) if input is zero vector.
    """
    length = math.sqrt(x * x + y * y)
    if length < 1e-6:
        return 0.0, 0.0
    return x / length, y / length


def magnitude(x: float, y: float) -> float:
    """Calculate the magnitude (length) of a vector."""
    return math.sqrt(x * x + y * y)


def dot(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate dot product of two vectors."""
    return x1 * x2 + y1 * y2


def angle_to(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calculate angle in degrees from (x1, y1) to (x2, y2).
    Returns angle in range [-180, 180].
    0 degrees = right, 90 = up, -90 = down, 180 = left.
    """
    dx = x2 - x1
    dy = y2 - y1
    return math.degrees(math.atan2(dy, dx))


def angle_difference(angle1: float, angle2: float) -> float:
    """
    Calculate the shortest angular difference between two angles.
    Returns value in range [-180, 180].
    """
    diff = angle2 - angle1
    while diff > 180:
        diff -= 360
    while diff < -180:
        diff += 360
    return diff


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + (b - a) * t


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def rotate_vector(x: float, y: float, angle_deg: float) -> Tuple[float, float]:
    """Rotate a vector by angle (in degrees)."""
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    return new_x, new_y


def move_toward_angle(current_angle: float, target_angle: float, max_delta: float) -> float:
    """
    Rotate current_angle toward target_angle by at most max_delta degrees.
    Handles wrap-around correctly.
    """
    diff = angle_difference(current_angle, target_angle)
    if abs(diff) <= max_delta:
        return target_angle
    return current_angle + math.copysign(max_delta, diff)


def circle_circle_collision(x1: float, y1: float, r1: float, 
                           x2: float, y2: float, r2: float) -> bool:
    """Check if two circles are colliding."""
    dist_sq = distance_squared(x1, y1, x2, y2)
    radius_sum = r1 + r2
    return dist_sq < radius_sum * radius_sum


def aabb_aabb_collision(x1: float, y1: float, w1: float, h1: float,
                        x2: float, y2: float, w2: float, h2: float) -> bool:
    """Check if two axis-aligned bounding boxes are colliding."""
    return (x1 < x2 + w2 and
            x1 + w1 > x2 and
            y1 < y2 + h2 and
            y1 + h1 > y2)


def point_in_circle(px: float, py: float, cx: float, cy: float, radius: float) -> bool:
    """Check if point (px, py) is inside circle at (cx, cy) with given radius."""
    return distance_squared(px, py, cx, cy) < radius * radius


def line_circle_intersection(x1: float, y1: float, x2: float, y2: float,
                             cx: float, cy: float, radius: float) -> bool:
    """
    Check if line segment from (x1, y1) to (x2, y2) intersects circle.
    Uses closest point on line segment approach.
    """
    # Vector from point1 to point2
    dx = x2 - x1
    dy = y2 - y1
    
    # Vector from point1 to circle center
    fx = cx - x1
    fy = cy - y1
    
    # Project circle center onto line segment
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-6:
        # Line segment is a point
        return point_in_circle(x1, y1, cx, cy, radius)
    
    t = max(0, min(1, (fx * dx + fy * dy) / length_sq))
    
    # Closest point on line segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    return point_in_circle(closest_x, closest_y, cx, cy, radius)


def random_in_range(min_val: float, max_val: float) -> float:
    """Generate random float in range [min_val, max_val]."""
    import random
    return random.uniform(min_val, max_val)


def random_unit_vector() -> Tuple[float, float]:
    """Generate random unit vector."""
    import random
    angle = random.uniform(0, 2 * math.pi)
    return math.cos(angle), math.sin(angle)


def wrap_angle(angle: float) -> float:
    """Wrap angle to range [-180, 180]."""
    while angle > 180:
        angle -= 360
    while angle < -180:
        angle += 360
    return angle
