"""
Game Configuration - Constants and tunable parameters.

Centralizes all game configuration for easy tweaking.
Includes support for different arena themes and visual styles.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from enum import Enum, auto


class ArenaTheme(Enum):
    """Available arena visual themes."""
    GRID = "grid"              # Digital/Minimalist - Cyan, black, white
    VOID = "void"              # Cosmic/Empty - Deep purple, stars
    CRYSTAL = "crystal"        # Organic/Crystalline - Teal, glowing
    CORRUPTED = "corrupted"    # Nature/Decay - Sickly green, brown
    FORGE = "forge"            # Industrial - Orange, gray, dark metal
    NEXUS = "nexus"            # Convergence - All colors (rainbow)


@dataclass
class ThemeColors:
    """Color palette for an arena theme."""
    background: str = "#000000"
    grid_primary: str = "#222222"
    grid_secondary: str = "#111111"
    border: str = "#444444"
    accent: str = "#00ffff"
    hazard: str = "#ff0000"
    safe_zone: str = "#00ff00"


# Theme color definitions
THEME_PALETTES = {
    ArenaTheme.GRID: ThemeColors(
        background="#000000",
        grid_primary="#004444",
        grid_secondary="#002222",
        border="#00ffff",
        accent="#00ffff",
        hazard="#ff4444",
        safe_zone="#44ff44"
    ),
    ArenaTheme.VOID: ThemeColors(
        background="#0a0014",
        grid_primary="#1a0033",
        grid_secondary="#0d001a",
        border="#6600aa",
        accent="#aa44ff",
        hazard="#ff00ff",
        safe_zone="#00ffaa"
    ),
    ArenaTheme.CRYSTAL: ThemeColors(
        background="#001a1a",
        grid_primary="#003333",
        grid_secondary="#001a1a",
        border="#00aaaa",
        accent="#44ffff",
        hazard="#ff8844",
        safe_zone="#88ffff"
    ),
    ArenaTheme.CORRUPTED: ThemeColors(
        background="#0a0800",
        grid_primary="#1a1000",
        grid_secondary="#0d0800",
        border="#446600",
        accent="#88aa00",
        hazard="#ff0044",
        safe_zone="#00ff44"
    ),
    ArenaTheme.FORGE: ThemeColors(
        background="#0a0500",
        grid_primary="#1a0a00",
        grid_secondary="#0d0500",
        border="#ff6600",
        accent="#ffaa44",
        hazard="#ff0000",
        safe_zone="#ffff44"
    ),
    ArenaTheme.NEXUS: ThemeColors(
        background="#0a0a0a",
        grid_primary="#1a1a1a",
        grid_secondary="#0d0d0d",
        border="#ffffff",
        accent="#ff00ff",
        hazard="#ff4444",
        safe_zone="#44ff44"
    ),
}


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
    budget_per_wave: float = 3.5
    max_waves: int = 20  # Extended to 20 waves
    wave_delay: float = 3.0
    spawn_delay: float = 0.4
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
    theme: ArenaTheme = ArenaTheme.GRID
    
    def get_theme_colors(self) -> ThemeColors:
        """Get the color palette for the current theme."""
        return THEME_PALETTES.get(self.theme, THEME_PALETTES[ArenaTheme.GRID])


@dataclass
class DifficultyConfig:
    """Dynamic difficulty configuration."""
    enabled: bool = True
    min_modifier: float = 0.7
    max_modifier: float = 1.5
    adaptation_rate: float = 0.1  # How fast difficulty changes


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
    difficulty: DifficultyConfig = field(default_factory=DifficultyConfig)
    
    # Gameplay settings
    i_frame_duration: float = 0.5
    show_health_bars: bool = True
    show_debug_info: bool = False
    
    # Difficulty modifiers
    enemy_hp_multiplier: float = 1.0
    enemy_damage_multiplier: float = 1.0
    enemy_speed_multiplier: float = 1.0
    
    # Visual settings
    enable_screen_shake: bool = True
    enable_particles: bool = True
    enable_glow_effects: bool = True


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
