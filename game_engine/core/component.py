"""Component dataclasses - pure data structures with no methods."""

from dataclasses import dataclass, field
from typing import Optional, Set, Dict, Any
import math


@dataclass
class Component:
    """Base class for all components."""
    pass


@dataclass
class Transform(Component):
    """Position, velocity, and rotation."""
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    angle: float = 0.0  # degrees
    angular_velocity: float = 0.0  # degrees per second
    
    def distance_to(self, other: 'Transform') -> float:
        """Calculate distance to another transform."""
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx * dx + dy * dy)
    
    def angle_to(self, other: 'Transform') -> float:
        """Calculate angle to another transform in degrees."""
        dx = other.x - self.x
        dy = other.y - self.y
        return math.degrees(math.atan2(dy, dx))


@dataclass
class Renderable(Component):
    """Rendering information."""
    shape: str = "circle"  # turtle shape name
    color: str = "white"
    size: float = 1.0
    turtle_ref: Optional[Any] = None  # Managed by render system


@dataclass
class Collider(Component):
    """Collision detection data.
    
    Collision layers (bit flags):
    - 0x0001: Projectile layer
    - 0x0002: Enemy layer
    - 0x0004: Player layer
    
    A collider's mask indicates which layers it can collide with.
    For example, mask=0x0006 means it collides with enemy (0x0002) and player (0x0004).
    """
    radius: float = 10.0
    mask: int = 0xFFFF  # Bitmask for collision layers
    tags: Set[str] = field(default_factory=set)
    
    def collides_with(self, other: 'Collider') -> bool:
        """Check if collision masks allow collision.
        
        Two colliders collide if:
        - self.mask has bits set for other's layer, AND
        - other.mask has bits set for self's layer
        
        For simplicity, we check if masks overlap (both have common bits).
        """
        return bool(self.mask & other.mask)


@dataclass
class Physics(Component):
    """Physics properties."""
    mass: float = 1.0
    friction: float = 0.95  # Velocity multiplier per frame
    max_speed: float = 200.0
    acceleration: float = 100.0  # Units per second squared


@dataclass
class Health(Component):
    """Health and damage."""
    hp: float = 100.0
    max_hp: float = 100.0
    armor: float = 0.0  # Damage reduction (0-1)
    
    def is_alive(self) -> bool:
        """Check if entity is alive."""
        return self.hp > 0


@dataclass
class Weapon(Component):
    """Weapon properties."""
    fire_rate: float = 2.0  # Shots per second
    damage: float = 10.0
    projectile_speed: float = 300.0
    spread: float = 0.0  # Degrees
    bullet_count: int = 1
    cooldown_remaining: float = 0.0
    weapon_type: str = "single"  # "single", "shotgun", "burst", "beam"
    
    def can_fire(self) -> bool:
        """Check if weapon can fire."""
        return self.cooldown_remaining <= 0.0


@dataclass
class Projectile(Component):
    """Projectile data."""
    owner_id: str = ""
    damage: float = 10.0
    lifetime: float = 2.0  # seconds
    time_alive: float = 0.0
    piercing: bool = False
    bounce: bool = False
    targets_hit: Set[str] = field(default_factory=set)  # Track pierced targets


@dataclass
class AIBrain(Component):
    """AI behavior data."""
    behavior_type: str = "chaser"  # "chaser", "turret", "swarm", "boss"
    state: str = "idle"
    target_id: Optional[str] = None
    awareness_range: float = 300.0
    attack_range: float = 200.0
    cooldowns: Dict[str, float] = field(default_factory=dict)
    phase: int = 1  # For boss enemies
    last_attack_time: float = 0.0


@dataclass
class Shield(Component):
    """Shield protection."""
    hp: float = 50.0
    max_hp: float = 50.0
    recharge_rate: float = 10.0  # HP per second
    recharge_delay: float = 2.0  # Seconds before recharge starts
    time_since_damage: float = 0.0
    
    def is_active(self) -> bool:
        """Check if shield has any HP."""
        return self.hp > 0


@dataclass
class StatusEffects(Component):
    """Status effect timers."""
    slow: float = 1.0  # Movement speed multiplier (1.0 = normal)
    slow_duration: float = 0.0
    stun: float = 0.0  # Stun timer
    burn: float = 0.0  # Burn damage per second
    burn_duration: float = 0.0


@dataclass
class WaveInfo(Component):
    """Wave progression data."""
    current_wave: int = 1
    enemies_remaining: int = 0
    difficulty_budget: float = 10.0
