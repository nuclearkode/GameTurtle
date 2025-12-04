"""
Transform component - Position and rotation in 2D space.

This is the most fundamental spatial component.
Most entities that exist in the game world will have a Transform.
"""

from dataclasses import dataclass, field
import math


@dataclass
class Transform:
    """
    Represents position and orientation in 2D space.
    
    Attributes:
        x: X position in world units
        y: Y position in world units  
        angle: Rotation in degrees (0 = right, 90 = up)
        scale: Uniform scale factor (1.0 = normal)
    
    Coordinate System:
        - Origin (0, 0) is center of arena
        - X increases to the right
        - Y increases upward (standard math coordinates)
        - Angle 0 points right, increases counter-clockwise
    """
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0
    scale: float = 1.0
    
    def forward_vector(self) -> tuple[float, float]:
        """Get the unit vector pointing in the entity's forward direction."""
        rad = math.radians(self.angle)
        return (math.cos(rad), math.sin(rad))
    
    def right_vector(self) -> tuple[float, float]:
        """Get the unit vector pointing to the entity's right."""
        rad = math.radians(self.angle - 90)
        return (math.cos(rad), math.sin(rad))
    
    def distance_to(self, other_x: float, other_y: float) -> float:
        """Calculate distance to a point."""
        dx = other_x - self.x
        dy = other_y - self.y
        return math.sqrt(dx * dx + dy * dy)
    
    def angle_to(self, other_x: float, other_y: float) -> float:
        """Calculate angle (in degrees) to a point."""
        dx = other_x - self.x
        dy = other_y - self.y
        return math.degrees(math.atan2(dy, dx))
    
    def move_forward(self, distance: float) -> None:
        """Move the entity forward by the given distance."""
        fx, fy = self.forward_vector()
        self.x += fx * distance
        self.y += fy * distance
    
    def look_at(self, target_x: float, target_y: float) -> None:
        """Rotate to face a target point."""
        self.angle = self.angle_to(target_x, target_y)
    
    def copy(self) -> "Transform":
        """Create a copy of this transform."""
        return Transform(self.x, self.y, self.angle, self.scale)
