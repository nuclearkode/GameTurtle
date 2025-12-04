"""
Physics components - Movement, velocity, and physical properties.

These components work together with the PhysicsSystem to provide
smooth, time-based movement with acceleration, friction, and mass.
"""

from dataclasses import dataclass, field


@dataclass
class Velocity:
    """
    Linear and angular velocity.
    
    Attributes:
        vx: Velocity in X direction (units per second)
        vy: Velocity in Y direction (units per second)
        angular: Angular velocity (degrees per second)
    """
    vx: float = 0.0
    vy: float = 0.0
    angular: float = 0.0
    
    @property
    def speed(self) -> float:
        """Get the magnitude of linear velocity."""
        return (self.vx ** 2 + self.vy ** 2) ** 0.5
    
    def normalize(self) -> tuple[float, float]:
        """Get the normalized direction vector."""
        speed = self.speed
        if speed < 0.001:
            return (0.0, 0.0)
        return (self.vx / speed, self.vy / speed)


@dataclass 
class Physics:
    """
    Physical properties affecting movement.
    
    Attributes:
        mass: Mass affects acceleration from forces (higher = slower to accelerate)
        friction: Friction coefficient (0 = no friction, 1 = instant stop)
        drag: Air resistance (velocity multiplier per second, 0.9 = 10% speed loss)
        max_speed: Maximum linear speed (units per second)
        max_angular_speed: Maximum angular speed (degrees per second)
        acceleration: Base acceleration rate (units per second squared)
        angular_acceleration: Base angular acceleration (degrees per second squared)
        is_kinematic: If True, not affected by physics (manual control only)
        bounce: Elasticity for collisions (0 = no bounce, 1 = perfect bounce)
    
    Design Notes:
        - Friction is applied each frame: velocity *= (1 - friction * dt)
        - Drag is applied as: velocity *= drag ** dt  
        - The PhysicsSystem integrates acceleration into velocity each frame
    """
    mass: float = 1.0
    friction: float = 0.0
    drag: float = 0.98
    max_speed: float = 300.0
    max_angular_speed: float = 360.0
    acceleration: float = 500.0
    angular_acceleration: float = 720.0
    is_kinematic: bool = False
    bounce: float = 0.0
    
    # Current acceleration (set by input/AI, used by physics system)
    accel_x: float = 0.0
    accel_y: float = 0.0
    angular_accel: float = 0.0
    
    def apply_force(self, fx: float, fy: float) -> None:
        """
        Apply a force (acceleration = force / mass).
        Forces accumulate until the physics system processes them.
        """
        self.accel_x += fx / self.mass
        self.accel_y += fy / self.mass
    
    def apply_impulse(self, velocity: Velocity, ix: float, iy: float) -> None:
        """
        Apply an instant velocity change (impulse / mass).
        Directly modifies velocity, doesn't wait for physics step.
        """
        velocity.vx += ix / self.mass
        velocity.vy += iy / self.mass
    
    def clear_forces(self) -> None:
        """Reset accumulated forces/accelerations."""
        self.accel_x = 0.0
        self.accel_y = 0.0
        self.angular_accel = 0.0
