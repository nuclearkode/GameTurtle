"""
Prefabs - Factory functions for creating common entities.

Prefabs encapsulate the component composition for common entity types,
making it easy to create consistent game objects.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import random

from engine.core.entity import Entity, EntityManager
from engine.components.transform import Transform
from engine.components.physics import Physics, Velocity
from engine.components.renderable import Renderable, RenderShape, RenderLayer
from engine.components.collider import Collider, ColliderType, CollisionMask
from engine.components.health import Health, Shield
from engine.components.weapon import Weapon, WeaponType
from engine.components.ai import AIBrain, AIBehavior
from engine.components.status import StatusEffects
from engine.components.tags import PlayerTag, EnemyTag, ObstacleTag, PowerupTag

from .config import GameConfig, DEFAULT_CONFIG


def create_player(
    entities: EntityManager,
    x: float = 0.0,
    y: float = 0.0,
    config: Optional[GameConfig] = None
) -> Entity:
    """
    Create the player entity.
    
    Args:
        entities: Entity manager
        x, y: Starting position
        config: Game configuration (uses defaults if None)
        
    Returns:
        The player entity
    """
    config = config or DEFAULT_CONFIG
    pc = config.player
    wc = config.weapon
    
    entity = entities.create_entity(name="player")
    
    # Transform
    entities.add_component(entity, Transform(x=x, y=y, angle=90))
    
    # Physics
    entities.add_component(entity, Velocity())
    entities.add_component(entity, Physics(
        max_speed=pc.move_speed,
        acceleration=pc.acceleration,
        angular_acceleration=pc.turn_speed,
        friction=pc.friction,
        drag=pc.drag
    ))
    
    # Rendering
    entities.add_component(entity, Renderable(
        shape=RenderShape.TRIANGLE,
        color=pc.color,
        outline_color=pc.outline_color,
        size=pc.size,
        layer=RenderLayer.PLAYER
    ))
    
    # Collision
    entities.add_component(entity, Collider(
        collider_type=ColliderType.CIRCLE,
        radius=15.0 * pc.size,
        layer=CollisionMask.PLAYER,
        mask=CollisionMask.ENEMY | CollisionMask.OBSTACLE | CollisionMask.ENEMY_PROJECTILE | CollisionMask.POWERUP
    ))
    
    # Health & Shield
    entities.add_component(entity, Health(
        hp=pc.max_hp,
        max_hp=pc.max_hp
    ))
    entities.add_component(entity, Shield(
        hp=pc.max_shield,
        max_hp=pc.max_shield,
        recharge_rate=pc.shield_recharge,
        recharge_delay=pc.shield_delay
    ))
    
    # Weapon
    entities.add_component(entity, Weapon(
        weapon_type=WeaponType.SINGLE,
        damage=wc.damage,
        fire_rate=wc.fire_rate,
        projectile_speed=wc.projectile_speed,
        projectile_size=wc.projectile_size,
        projectile_color=wc.projectile_color
    ))
    
    # Status effects container
    entities.add_component(entity, StatusEffects())
    
    # Tag
    entities.add_component(entity, PlayerTag())
    entities.add_tag(entity, "player")
    
    return entity


def create_obstacle(
    entities: EntityManager,
    x: float,
    y: float,
    width: float = 50.0,
    height: float = 50.0,
    destructible: bool = False,
    hp: float = 100.0
) -> Entity:
    """
    Create an obstacle/wall entity.
    
    Args:
        entities: Entity manager
        x, y: Position
        width, height: Obstacle dimensions
        destructible: Whether it can be destroyed
        hp: Health if destructible
        
    Returns:
        The obstacle entity
    """
    entity = entities.create_entity()
    
    # Transform
    entities.add_component(entity, Transform(x=x, y=y))
    
    # Static physics
    entities.add_component(entity, Velocity())
    entities.add_component(entity, Physics(is_kinematic=True))
    
    # Rendering
    entities.add_component(entity, Renderable(
        shape=RenderShape.SQUARE,
        color="#666666",
        outline_color="#888888",
        size=max(width, height) / 20,  # Scale based on size
        layer=RenderLayer.OBSTACLE
    ))
    
    # Collision
    entities.add_component(entity, Collider(
        collider_type=ColliderType.AABB,
        width=width,
        height=height,
        layer=CollisionMask.OBSTACLE,
        mask=CollisionMask.ALL,
        is_static=True
    ))
    
    # Health (if destructible)
    if destructible:
        entities.add_component(entity, Health(hp=hp, max_hp=hp))
    
    # Tag
    entities.add_component(entity, ObstacleTag(
        blocks_movement=True,
        blocks_projectiles=True,
        destructible=destructible
    ))
    entities.add_tag(entity, "obstacle")
    
    return entity


def create_powerup(
    entities: EntityManager,
    x: float,
    y: float,
    powerup_type: str = "health",
    value: float = 25.0
) -> Entity:
    """
    Create a power-up pickup entity.
    
    Args:
        entities: Entity manager
        x, y: Position
        powerup_type: Type of powerup ("health", "shield", "damage", "speed")
        value: Effect magnitude
        
    Returns:
        The powerup entity
    """
    entity = entities.create_entity()
    
    # Determine color based on type
    colors = {
        "health": ("#ff4444", "#aa0000"),
        "shield": ("#4444ff", "#0000aa"),
        "damage": ("#ffaa00", "#aa7700"),
        "speed": ("#00ffff", "#00aaaa"),
    }
    color, outline = colors.get(powerup_type, ("#ffffff", "#aaaaaa"))
    
    # Transform
    entities.add_component(entity, Transform(x=x, y=y))
    
    # Slight floating animation via velocity
    entities.add_component(entity, Velocity(angular=45))
    
    # Rendering
    entities.add_component(entity, Renderable(
        shape=RenderShape.CIRCLE,
        color=color,
        outline_color=outline,
        size=0.6,
        layer=RenderLayer.POWERUP
    ))
    
    # Collision (trigger only)
    entities.add_component(entity, Collider(
        collider_type=ColliderType.CIRCLE,
        radius=12.0,
        layer=CollisionMask.POWERUP,
        mask=CollisionMask.PLAYER,
        is_trigger=True
    ))
    
    # Tag
    entities.add_component(entity, PowerupTag(
        powerup_type=powerup_type,
        value=value
    ))
    entities.add_tag(entity, "powerup")
    
    return entity


def create_arena_obstacles(
    entities: EntityManager,
    arena_width: float,
    arena_height: float,
    obstacle_count: int = 5
) -> list[Entity]:
    """
    Create random obstacles in the arena.
    
    Avoids placing obstacles too close to the center (player spawn).
    
    Returns:
        List of created obstacle entities
    """
    obstacles = []
    hw = arena_width / 2 - 50
    hh = arena_height / 2 - 50
    min_dist_from_center = 100
    
    for _ in range(obstacle_count):
        # Random position avoiding center
        for _ in range(10):  # Max attempts
            x = random.uniform(-hw, hw)
            y = random.uniform(-hh, hh)
            
            if (x**2 + y**2) > min_dist_from_center**2:
                break
        
        # Random size
        size = random.uniform(30, 60)
        
        obstacle = create_obstacle(
            entities, x, y,
            width=size,
            height=size,
            destructible=random.random() < 0.3  # 30% chance destructible
        )
        obstacles.append(obstacle)
    
    return obstacles
