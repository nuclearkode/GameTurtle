"""
Weapon and Projectile components - Combat mechanics.

Weapons fire projectiles, projectiles deal damage on collision.
The WeaponSystem handles firing logic, cooldowns, and bullet patterns.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List


class WeaponType(Enum):
    """Predefined weapon types with different firing patterns."""
    SINGLE = auto()      # Single shot
    SHOTGUN = auto()     # Multiple spread shots
    BURST = auto()       # Multiple shots in quick succession
    BEAM = auto()        # Continuous damage ray
    ROCKET = auto()      # Slow but explosive
    RAPID = auto()       # Fast fire rate


@dataclass
class Weapon:
    """
    Weapon configuration and state.
    
    Attributes:
        weapon_type: Type of weapon (affects firing pattern)
        damage: Base damage per projectile
        fire_rate: Shots per second (e.g., 5.0 = 5 shots/sec)
        projectile_speed: Speed of fired projectiles
        spread: Spread angle in degrees (for shotgun/inaccuracy)
        bullet_count: Bullets per shot (for shotgun)
        burst_count: Shots per burst (for burst fire)
        burst_delay: Delay between burst shots
        range: Maximum projectile lifetime distance
        projectile_size: Size of projectiles (for rendering/collision)
        
    Cooldown Logic:
        - cooldown tracks time until next shot is ready
        - cooldown = 1.0 / fire_rate after each shot
        - WeaponSystem decrements cooldown by dt each frame
        
    Ammo (optional):
        - If max_ammo > 0, weapon uses ammo
        - ammo decrements on fire
        - reload_time for reloading
    """
    weapon_type: WeaponType = WeaponType.SINGLE
    damage: float = 10.0
    fire_rate: float = 3.0
    projectile_speed: float = 500.0
    spread: float = 0.0
    bullet_count: int = 1
    burst_count: int = 1
    burst_delay: float = 0.05
    range: float = 800.0
    projectile_size: float = 0.4
    projectile_color: str = "yellow"
    
    # State
    cooldown: float = 0.0
    is_firing: bool = False
    burst_remaining: int = 0
    burst_cooldown: float = 0.0
    
    # Optional ammo system
    ammo: int = -1  # -1 = infinite
    max_ammo: int = -1
    reload_time: float = 1.5
    reload_timer: float = 0.0
    is_reloading: bool = False
    
    @property
    def can_fire(self) -> bool:
        """Check if weapon can fire right now."""
        if self.cooldown > 0:
            return False
        if self.is_reloading:
            return False
        if self.max_ammo > 0 and self.ammo <= 0:
            return False
        return True
    
    def start_reload(self) -> bool:
        """Start reloading if needed. Returns True if reload started."""
        if self.max_ammo <= 0:
            return False  # Infinite ammo
        if self.ammo >= self.max_ammo:
            return False  # Already full
        if self.is_reloading:
            return False  # Already reloading
        
        self.is_reloading = True
        self.reload_timer = self.reload_time
        return True


@dataclass
class Projectile:
    """
    Projectile component - attached to bullet/missile entities.
    
    Attributes:
        owner_id: Entity ID that fired this projectile
        damage: Damage dealt on hit
        lifetime: Maximum time before despawn (seconds)
        time_alive: Current age of projectile
        pierce_count: How many enemies it can hit (0 = destroy on first hit)
        is_explosive: If True, deals AoE damage on impact
        explosion_radius: Radius of explosion damage
        
    Projectile Lifecycle:
        1. Created by WeaponSystem when weapon fires
        2. PhysicsSystem moves it each frame
        3. CollisionSystem checks for hits
        4. On hit: DamageEvent emitted, pierce_count decremented
        5. If pierce_count < 0 or lifetime exceeded: destroy
    """
    owner_id: str = ""
    damage: float = 10.0
    lifetime: float = 2.0
    time_alive: float = 0.0
    
    # Advanced projectile properties
    pierce_count: int = 0
    is_explosive: bool = False
    explosion_radius: float = 50.0
    
    # Bouncing projectiles
    bounce_count: int = 0
    
    # Homing projectiles
    is_homing: bool = False
    homing_strength: float = 0.0
    target_id: Optional[str] = None
    
    # Hit tracking (to prevent multi-hit on same frame)
    hit_entities: List[str] = field(default_factory=list)
    
    @property
    def is_expired(self) -> bool:
        """Check if projectile should be destroyed."""
        return self.time_alive >= self.lifetime
    
    def register_hit(self, entity_id: str) -> bool:
        """
        Register a hit on an entity.
        
        Returns:
            True if this is a new hit, False if already hit this entity
        """
        if entity_id in self.hit_entities:
            return False
        
        self.hit_entities.append(entity_id)
        
        # Check if we've exceeded pierce count
        if self.pierce_count >= 0 and len(self.hit_entities) > self.pierce_count:
            return True  # Hit registered, projectile should be destroyed
        
        return True  # Hit registered, can continue if piercing
