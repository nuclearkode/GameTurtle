"""
Component dataclasses - pure data structures, no methods.
All game state is stored in components.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class Component:
    """Base class for all components (marker only)"""
    pass


class AIBehaviorType(Enum):
    """AI behavior types"""
    CHASER = "chaser"
    TURRET = "turret"
    SWARM = "swarm"
    BOSS = "boss"


@dataclass
class Transform(Component):
    """Position, velocity, and rotation"""
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0  # velocity x
    vy: float = 0.0  # velocity y
    angle: float = 0.0  # rotation in degrees
    angular_velocity: float = 0.0  # degrees per second


@dataclass
class Renderable(Component):
    """Rendering information"""
    shape: str = "circle"  # turtle shape name
    color: str = "white"
    size: float = 1.0  # size multiplier
    turtle_ref: Optional[Any] = None  # turtle.Turtle instance


@dataclass
class Collider(Component):
    """Collision detection"""
    radius: float = 10.0  # circular collider radius
    mask: int = 0xFFFF  # collision mask (bit flags)
    tags: set = field(default_factory=set)  # string tags for filtering


@dataclass
class Physics(Component):
    """Physics properties"""
    mass: float = 1.0
    friction: float = 0.9  # velocity multiplier per frame
    max_speed: float = 200.0  # pixels per second
    acceleration: float = 500.0  # pixels per second^2


@dataclass
class Health(Component):
    """Health and damage"""
    hp: float = 100.0
    max_hp: float = 100.0
    armor: float = 0.0  # damage reduction (0-1)


@dataclass
class Weapon(Component):
    """Weapon properties"""
    fire_rate: float = 1.0  # shots per second
    damage: float = 10.0
    projectile_speed: float = 300.0  # pixels per second
    spread: float = 0.0  # degrees of spread
    bullet_count: int = 1  # bullets per shot (shotgun)
    cooldown: float = 0.0  # time until can fire again
    range: float = 1000.0  # max range


@dataclass
class Projectile(Component):
    """Projectile properties"""
    owner_id: str = ""  # entity that fired this
    damage: float = 10.0
    lifetime: float = 2.0  # seconds
    time_alive: float = 0.0
    pierce_count: int = 0  # how many enemies can pierce through


@dataclass
class AIBrain(Component):
    """AI behavior and state"""
    behavior_type: AIBehaviorType = AIBehaviorType.CHASER
    state: str = "idle"  # state machine state
    target_id: Optional[str] = None  # target entity ID
    awareness_range: float = 300.0  # detection range
    attack_range: float = 200.0  # attack range
    cooldowns: Dict[str, float] = field(default_factory=dict)  # named cooldowns
    phase: int = 1  # for boss multi-phase
    last_attack_time: float = 0.0


@dataclass
class Shield(Component):
    """Shield protection"""
    hp: float = 0.0
    max_hp: float = 0.0
    recharge_rate: float = 10.0  # hp per second
    last_damage_time: float = 0.0
    recharge_delay: float = 2.0  # seconds before recharge starts


@dataclass
class StatusEffects(Component):
    """Status effect timers"""
    slow_timer: float = 0.0  # seconds remaining
    stun_timer: float = 0.0
    burn_timer: float = 0.0
    slow_magnitude: float = 0.5  # speed multiplier (0-1)
    burn_dps: float = 5.0  # damage per second


@dataclass
class WaveInfo(Component):
    """Wave progression info (attached to player or global)"""
    current_wave: int = 0
    enemies_remaining: int = 0
