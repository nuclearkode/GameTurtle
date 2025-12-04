"""
Tag components - Marker components for entity categorization.

Tag components contain no data; they exist purely to mark
an entity as belonging to a category. This enables fast
filtering in queries.

Using tag components instead of string tags:
- Type-safe
- IDE autocomplete
- Can be queried like any component
"""

from dataclasses import dataclass


@dataclass
class PlayerTag:
    """Marks an entity as the player."""
    player_number: int = 1


@dataclass
class EnemyTag:
    """Marks an entity as an enemy."""
    enemy_type: str = "basic"
    wave_spawned: int = 0
    point_value: int = 100


@dataclass
class ProjectileTag:
    """Marks an entity as a projectile."""
    is_player_owned: bool = True


@dataclass
class ObstacleTag:
    """Marks an entity as a static obstacle/wall."""
    blocks_movement: bool = True
    blocks_projectiles: bool = True
    destructible: bool = False


@dataclass
class PowerupTag:
    """Marks an entity as a power-up pickup."""
    powerup_type: str = "health"
    value: float = 25.0
    respawn_time: float = 10.0


@dataclass 
class BossTag:
    """Marks an entity as a boss enemy."""
    boss_name: str = "Boss"
    is_main_boss: bool = True


@dataclass
class SpawnerTag:
    """Marks an entity as an enemy spawner."""
    spawn_type: str = "chaser"
    spawn_rate: float = 2.0
    max_spawned: int = 5
    current_spawned: int = 0


@dataclass
class TriggerTag:
    """Marks an entity as a trigger zone."""
    trigger_type: str = "zone"
    trigger_data: str = ""
    one_shot: bool = True
    triggered: bool = False
