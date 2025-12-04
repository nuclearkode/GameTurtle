"""
Component definitions - pure data structures with no behavior.

All components are dataclasses that hold state.
Systems operate on these components to implement game logic.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple
from enum import Enum


# ============================================================================
# CORE COMPONENTS
# ============================================================================

@dataclass
class Transform:
    """Position, velocity, and rotation."""
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    angle: float = 0.0  # degrees
    angular_velocity: float = 0.0  # degrees per second


@dataclass
class Physics:
    """Physical properties for movement."""
    mass: float = 1.0
    friction: float = 0.9  # 0 = no friction, 1 = instant stop
    max_speed: float = 200.0  # units per second
    acceleration: float = 500.0  # units per second^2
    can_rotate: bool = True
    rotation_speed: float = 180.0  # degrees per second


@dataclass
class Renderable:
    """Visual representation."""
    shape: str = "circle"  # circle, square, triangle, arrow, etc.
    color: str = "white"
    size: float = 1.0  # multiplier for shapesize
    layer: int = 0  # rendering order (higher = drawn later)
    visible: bool = True
    turtle_ref: Any = None  # reference to turtle object (managed by RenderSystem)


@dataclass
class Collider:
    """Collision detection."""
    radius: float = 10.0  # for circle colliders
    aabb: Optional[Tuple[float, float, float, float]] = None  # (x_min, y_min, x_max, y_max) for box colliders
    is_trigger: bool = False  # if True, detects collisions but doesn't block movement
    tags: set = field(default_factory=set)  # collision layers this object is on
    mask: set = field(default_factory=set)  # layers this object collides with
    

# ============================================================================
# COMBAT COMPONENTS
# ============================================================================

@dataclass
class Health:
    """Hit points and damage handling."""
    hp: float = 100.0
    max_hp: float = 100.0
    armor: float = 0.0  # damage reduction (0-1, where 0.5 = 50% reduction)
    invulnerable_time: float = 0.0  # current invulnerability timer
    invulnerable_duration: float = 0.0  # how long invulnerability lasts after hit
    is_dead: bool = False


@dataclass
class Shield:
    """Energy shield that regenerates."""
    hp: float = 50.0
    max_hp: float = 50.0
    recharge_rate: float = 10.0  # HP per second
    recharge_delay: float = 3.0  # seconds before recharge starts
    last_damage_time: float = 0.0  # time since last damage (for delay)


@dataclass
class Weapon:
    """Weapon firing capability."""
    fire_rate: float = 2.0  # shots per second
    cooldown: float = 0.0  # current cooldown timer
    damage: float = 10.0
    projectile_speed: float = 400.0
    spread: float = 0.0  # degrees of random spread
    bullet_count: int = 1  # bullets per shot (for shotgun)
    bullet_size: float = 5.0
    bullet_color: str = "yellow"
    bullet_lifetime: float = 2.0  # seconds
    projectile_piercing: int = 0  # how many enemies a bullet can pierce
    knockback: float = 0.0  # knockback force applied to hit entities


@dataclass
class Projectile:
    """Projectile-specific data."""
    owner_id: str = ""  # entity that fired this
    damage: float = 10.0
    lifetime: float = 2.0  # max lifetime in seconds
    time_alive: float = 0.0  # current age
    piercing: int = 0  # remaining pierce count
    hits: set = field(default_factory=set)  # entities already hit (for piercing)
    knockback: float = 0.0


# ============================================================================
# AI COMPONENTS
# ============================================================================

class AIBehavior(Enum):
    """Types of AI behaviors."""
    IDLE = "idle"
    CHASER = "chaser"
    TURRET = "turret"
    SWARM = "swarm"
    BOSS = "boss"


class AIState(Enum):
    """AI state machine states."""
    IDLE = "idle"
    PATROL = "patrol"
    CHASE = "chase"
    ATTACK = "attack"
    RETREAT = "retreat"
    DEAD = "dead"


@dataclass
class AIBrain:
    """AI decision-making data."""
    behavior_type: AIBehavior = AIBehavior.IDLE
    state: AIState = AIState.IDLE
    target_id: Optional[str] = None  # current target entity
    awareness_range: float = 300.0  # distance to detect targets
    attack_range: float = 200.0  # distance to start attacking
    personal_space: float = 30.0  # minimum distance to maintain from target
    
    # Cooldowns
    attack_cooldown: float = 0.0
    state_change_cooldown: float = 0.0
    
    # Path following
    path: list = field(default_factory=list)  # list of (x, y) waypoints
    path_index: int = 0
    
    # Swarm/flock behavior
    flock_radius: float = 50.0  # distance to consider neighbors
    max_neighbors: int = 10  # limit for performance
    
    # Custom behavior data (for boss phases, etc.)
    custom_data: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# ENTITY TYPE TAGS
# ============================================================================

@dataclass
class Player:
    """Tag component for the player."""
    score: int = 0
    lives: int = 3
    can_shoot: bool = True


@dataclass
class Enemy:
    """Tag component for enemies."""
    type: str = "basic"  # chaser, turret, swarm, boss
    threat_level: int = 1  # difficulty/cost for wave spawning
    points: int = 10  # score value


@dataclass
class Wall:
    """Tag component for walls/obstacles."""
    blocks_movement: bool = True
    blocks_los: bool = True  # line of sight


# ============================================================================
# STATUS EFFECTS
# ============================================================================

@dataclass
class StatusEffect:
    """
    Active status effects on an entity.
    
    Effects are stored as: effect_name -> (remaining_time, magnitude)
    """
    effects: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    def add_effect(self, name: str, duration: float, magnitude: float) -> None:
        """Add or refresh a status effect."""
        self.effects[name] = (duration, magnitude)
    
    def update(self, dt: float) -> None:
        """Update effect timers and remove expired effects."""
        expired = []
        for name, (time, mag) in self.effects.items():
            time -= dt
            if time <= 0:
                expired.append(name)
            else:
                self.effects[name] = (time, mag)
        
        for name in expired:
            del self.effects[name]
    
    def has_effect(self, name: str) -> bool:
        """Check if entity has a specific effect."""
        return name in self.effects
    
    def get_magnitude(self, name: str) -> float:
        """Get the magnitude of an effect, or 0 if not present."""
        return self.effects.get(name, (0, 0))[1]


# ============================================================================
# GAME STATE COMPONENTS
# ============================================================================

@dataclass
class WaveInfo:
    """Wave management data (typically on a singleton entity)."""
    current_wave: int = 0
    enemies_spawned: int = 0
    enemies_alive: int = 0
    wave_active: bool = False
    wave_complete: bool = False
    time_between_waves: float = 5.0
    time_until_next_wave: float = 0.0


@dataclass
class PowerUp:
    """Power-up pickup."""
    type: str = "health"  # health, shield, weapon_upgrade, speed, etc.
    value: float = 20.0
    lifetime: float = 10.0  # disappears after this time
    time_alive: float = 0.0


@dataclass
class Particle:
    """Visual particle effect."""
    lifetime: float = 1.0
    time_alive: float = 0.0
    fade_rate: float = 1.0  # alpha decrease per second
    shrink_rate: float = 0.0  # size decrease per second


# ============================================================================
# UTILITY COMPONENTS
# ============================================================================

@dataclass
class Lifetime:
    """Auto-destroy entity after a duration."""
    max_lifetime: float = 1.0
    time_alive: float = 0.0


@dataclass
class FollowTarget:
    """Make entity follow another entity."""
    target_id: str = ""
    offset_x: float = 0.0
    offset_y: float = 0.0


@dataclass
class Arena:
    """Arena bounds (typically on a singleton entity)."""
    min_x: float = -400.0
    max_x: float = 400.0
    min_y: float = -300.0
    max_y: float = 300.0
    
    def clamp_position(self, x: float, y: float) -> Tuple[float, float]:
        """Clamp a position to arena bounds."""
        x = max(self.min_x, min(self.max_x, x))
        y = max(self.min_y, min(self.max_y, y))
        return x, y
    
    def is_inside(self, x: float, y: float) -> bool:
        """Check if position is inside arena."""
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y


# Export all components
__all__ = [
    'Transform',
    'Physics',
    'Renderable',
    'Collider',
    'Health',
    'Shield',
    'Weapon',
    'Projectile',
    'AIBehavior',
    'AIState',
    'AIBrain',
    'Player',
    'Enemy',
    'Wall',
    'StatusEffect',
    'WaveInfo',
    'PowerUp',
    'Particle',
    'Lifetime',
    'FollowTarget',
    'Arena',
]
