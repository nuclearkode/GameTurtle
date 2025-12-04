"""
Game Configuration - Constants and tunable parameters.

Centralizes all game configuration for easy tweaking.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class PlayerConfig:
    """Player configuration."""
    max_hp: float = 100.0
    max_shield: float = 50.0
    shield_recharge: float = 5.0
    shield_delay: float = 3.0
    move_speed: float = 200.0
    acceleration: float = 600.0
    turn_speed: float = 360.0
    friction: float = 0.15
    drag: float = 0.92
    size: float = 1.0
    color: str = "#00ff88"
    outline_color: str = "#00aa55"


@dataclass
class WeaponConfig:
    """Default weapon configuration."""
    damage: float = 15.0
    fire_rate: float = 5.0
    projectile_speed: float = 500.0
    projectile_size: float = 0.3
    projectile_color: str = "#ffff00"


@dataclass
class WaveConfig:
    """Wave system configuration."""
    start_budget: float = 5.0
    budget_per_wave: float = 3.0
    max_waves: int = 15
    wave_delay: float = 3.0
    spawn_delay: float = 0.5
    boss_every_n_waves: int = 5


@dataclass
class ArenaConfig:
    """Arena configuration."""
    width: int = 800
    height: int = 600
    background_color: str = "black"
    border_color: str = "#444444"
    grid_color: str = "#222222"
    grid_size: int = 50


@dataclass
class GameConfig:
    """
    Main game configuration.
    
    Usage:
        config = GameConfig()
        # Override defaults
        config.player.max_hp = 150
        config.arena.width = 1024
    """
    # Window settings
    title: str = "Robo-Arena"
    target_fps: int = 60
    
    # Sub-configurations
    player: PlayerConfig = field(default_factory=PlayerConfig)
    weapon: WeaponConfig = field(default_factory=WeaponConfig)
    wave: WaveConfig = field(default_factory=WaveConfig)
    arena: ArenaConfig = field(default_factory=ArenaConfig)
    
    # Gameplay settings
    i_frame_duration: float = 0.5
    show_health_bars: bool = True
    show_debug_info: bool = False
    
    # Difficulty modifiers
    enemy_hp_multiplier: float = 1.0
    enemy_damage_multiplier: float = 1.0
    enemy_speed_multiplier: float = 1.0


# Upgrade definitions
UPGRADES = {
    "max_hp": {
        "name": "Health Boost",
        "description": "+25 Max HP",
        "apply": lambda player_hp: setattr(player_hp, "max_hp", player_hp.max_hp + 25),
    },
    "fire_rate": {
        "name": "Rapid Fire",
        "description": "+20% Fire Rate",
        "apply": lambda weapon: setattr(weapon, "fire_rate", weapon.fire_rate * 1.2),
    },
    "move_speed": {
        "name": "Speed Boost",
        "description": "+15% Movement Speed",
        "apply": lambda physics: setattr(physics, "max_speed", physics.max_speed * 1.15),
    },
    "damage": {
        "name": "Damage Boost",
        "description": "+20% Damage",
        "apply": lambda weapon: setattr(weapon, "damage", weapon.damage * 1.2),
    },
    "shield": {
        "name": "Shield Boost",
        "description": "+25 Max Shield",
        "apply": lambda shield: setattr(shield, "max_hp", shield.max_hp + 25),
    },
    "armor": {
        "name": "Armor Plating",
        "description": "+10% Damage Reduction",
        "apply": lambda health: setattr(health, "armor", min(0.8, health.armor + 0.1)),
    },
}


# Default configuration instance
DEFAULT_CONFIG = GameConfig()
