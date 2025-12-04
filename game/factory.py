"""
Entity factory functions for creating game entities.
"""

from engine.core.entity import EntityManager
from engine.core.component import *
from game.config import *


def create_player(entity_manager: EntityManager, x: float = 0, y: float = 0):
    """Create the player entity."""
    player = entity_manager.create_entity()
    
    # Transform
    entity_manager.add_component(player.id, Transform(
        x=x, y=y, angle=0
    ))
    
    # Physics
    entity_manager.add_component(player.id, Physics(
        max_speed=PLAYER_SPEED,
        friction=5.0,
        acceleration=1000.0,
        rotation_speed=PLAYER_ROTATION_SPEED
    ))
    
    # Renderable
    entity_manager.add_component(player.id, Renderable(
        shape="triangle",
        color="cyan",
        size=PLAYER_SIZE,
        layer=1
    ))
    
    # Collider
    entity_manager.add_component(player.id, Collider(
        radius=15,
        tags=COLLISION_TAGS['player'],
        mask=COLLISION_MASKS['player']
    ))
    
    # Health
    entity_manager.add_component(player.id, Health(
        hp=PLAYER_HP,
        max_hp=PLAYER_HP,
        armor=0.0,
        invulnerable_duration=1.0
    ))
    
    # Shield
    entity_manager.add_component(player.id, Shield(
        hp=PLAYER_SHIELD,
        max_hp=PLAYER_SHIELD,
        recharge_rate=10.0,
        recharge_delay=3.0
    ))
    
    # Weapon
    entity_manager.add_component(player.id, Weapon(
        fire_rate=PLAYER_FIRE_RATE,
        damage=PLAYER_DAMAGE,
        projectile_speed=PROJECTILE_SPEED,
        bullet_color="cyan",
        bullet_size=PROJECTILE_SIZE,
        bullet_lifetime=PROJECTILE_LIFETIME
    ))
    
    # Player tag
    entity_manager.add_component(player.id, Player(
        score=0,
        lives=3
    ))
    
    return player


def create_chaser(entity_manager: EntityManager, x: float, y: float):
    """Create a chaser enemy."""
    settings = ENEMY_SETTINGS['chaser']
    
    enemy = entity_manager.create_entity()
    
    entity_manager.add_component(enemy.id, Transform(x=x, y=y))
    
    entity_manager.add_component(enemy.id, Physics(
        max_speed=settings['speed'],
        friction=3.0,
        acceleration=800.0,
        rotation_speed=240.0
    ))
    
    entity_manager.add_component(enemy.id, Renderable(
        shape="circle",
        color=settings['color'],
        size=settings['size'],
        layer=2
    ))
    
    entity_manager.add_component(enemy.id, Collider(
        radius=12,
        tags=COLLISION_TAGS['enemy'],
        mask=COLLISION_MASKS['enemy']
    ))
    
    entity_manager.add_component(enemy.id, Health(
        hp=settings['hp'],
        max_hp=settings['hp']
    ))
    
    entity_manager.add_component(enemy.id, AIBrain(
        behavior_type=AIBehavior.CHASER,
        awareness_range=settings['awareness_range'],
        attack_range=settings['attack_range'],
        personal_space=settings['personal_space']
    ))
    
    entity_manager.add_component(enemy.id, Enemy(
        type='chaser',
        threat_level=1,
        points=settings['points']
    ))
    
    return enemy


def create_turret(entity_manager: EntityManager, x: float, y: float):
    """Create a turret enemy."""
    settings = ENEMY_SETTINGS['turret']
    
    enemy = entity_manager.create_entity()
    
    entity_manager.add_component(enemy.id, Transform(x=x, y=y))
    
    entity_manager.add_component(enemy.id, Physics(
        max_speed=0.0,  # Stationary
        friction=0.0,
        rotation_speed=180.0
    ))
    
    entity_manager.add_component(enemy.id, Renderable(
        shape="square",
        color=settings['color'],
        size=settings['size'],
        layer=2
    ))
    
    entity_manager.add_component(enemy.id, Collider(
        radius=15,
        tags=COLLISION_TAGS['enemy'],
        mask=COLLISION_MASKS['enemy']
    ))
    
    entity_manager.add_component(enemy.id, Health(
        hp=settings['hp'],
        max_hp=settings['hp'],
        armor=0.2  # Turrets have some armor
    ))
    
    entity_manager.add_component(enemy.id, Weapon(
        fire_rate=settings['fire_rate'],
        damage=settings['damage'],
        projectile_speed=PROJECTILE_SPEED * 0.8,
        bullet_color="orange",
        bullet_size=6,
        bullet_lifetime=PROJECTILE_LIFETIME
    ))
    
    entity_manager.add_component(enemy.id, AIBrain(
        behavior_type=AIBehavior.TURRET,
        awareness_range=settings['awareness_range'],
        attack_range=settings['attack_range']
    ))
    
    entity_manager.add_component(enemy.id, Enemy(
        type='turret',
        threat_level=2,
        points=settings['points']
    ))
    
    return enemy


def create_swarm(entity_manager: EntityManager, x: float, y: float):
    """Create a swarm enemy."""
    settings = ENEMY_SETTINGS['swarm']
    
    enemy = entity_manager.create_entity()
    
    entity_manager.add_component(enemy.id, Transform(x=x, y=y))
    
    entity_manager.add_component(enemy.id, Physics(
        max_speed=settings['speed'],
        friction=2.0,
        acceleration=600.0,
        rotation_speed=300.0
    ))
    
    entity_manager.add_component(enemy.id, Renderable(
        shape="circle",
        color=settings['color'],
        size=settings['size'],
        layer=2
    ))
    
    entity_manager.add_component(enemy.id, Collider(
        radius=8,
        tags=COLLISION_TAGS['enemy'],
        mask=COLLISION_MASKS['enemy']
    ))
    
    entity_manager.add_component(enemy.id, Health(
        hp=settings['hp'],
        max_hp=settings['hp']
    ))
    
    entity_manager.add_component(enemy.id, AIBrain(
        behavior_type=AIBehavior.SWARM,
        awareness_range=settings['awareness_range'],
        attack_range=settings['attack_range'],
        personal_space=settings['personal_space'],
        flock_radius=settings['flock_radius']
    ))
    
    entity_manager.add_component(enemy.id, Enemy(
        type='swarm',
        threat_level=1,
        points=settings['points']
    ))
    
    return enemy


def create_boss(entity_manager: EntityManager, x: float, y: float):
    """Create a boss enemy."""
    settings = ENEMY_SETTINGS['boss']
    
    enemy = entity_manager.create_entity()
    
    entity_manager.add_component(enemy.id, Transform(x=x, y=y))
    
    entity_manager.add_component(enemy.id, Physics(
        max_speed=settings['speed'],
        friction=4.0,
        acceleration=500.0,
        rotation_speed=120.0
    ))
    
    entity_manager.add_component(enemy.id, Renderable(
        shape="circle",
        color=settings['color'],
        size=settings['size'],
        layer=3
    ))
    
    entity_manager.add_component(enemy.id, Collider(
        radius=30,
        tags=COLLISION_TAGS['enemy'],
        mask=COLLISION_MASKS['enemy']
    ))
    
    entity_manager.add_component(enemy.id, Health(
        hp=settings['hp'],
        max_hp=settings['hp'],
        armor=0.3
    ))
    
    entity_manager.add_component(enemy.id, Weapon(
        fire_rate=settings['fire_rate'],
        damage=settings['damage'],
        projectile_speed=PROJECTILE_SPEED,
        bullet_color="purple",
        bullet_size=8,
        bullet_lifetime=PROJECTILE_LIFETIME
    ))
    
    entity_manager.add_component(enemy.id, AIBrain(
        behavior_type=AIBehavior.BOSS,
        awareness_range=settings['awareness_range'],
        attack_range=settings['attack_range'],
        personal_space=settings['personal_space'],
        custom_data={'phase': 1}
    ))
    
    entity_manager.add_component(enemy.id, Enemy(
        type='boss',
        threat_level=10,
        points=settings['points']
    ))
    
    return enemy


def create_wall(entity_manager: EntityManager, x: float, y: float, width: float = 20, height: float = 20):
    """Create a wall obstacle."""
    wall = entity_manager.create_entity()
    
    entity_manager.add_component(wall.id, Transform(x=x, y=y))
    
    entity_manager.add_component(wall.id, Renderable(
        shape="square",
        color="gray",
        size=1.5,
        layer=0
    ))
    
    entity_manager.add_component(wall.id, Collider(
        radius=width / 2,
        tags=COLLISION_TAGS['wall'],
        mask=COLLISION_MASKS['wall']
    ))
    
    entity_manager.add_component(wall.id, Wall(
        blocks_movement=True,
        blocks_los=True
    ))
    
    return wall


def create_arena(entity_manager: EntityManager):
    """Create arena boundaries."""
    arena_entity = entity_manager.create_entity()
    
    entity_manager.add_component(arena_entity.id, Arena(
        min_x=ARENA_MIN_X,
        max_x=ARENA_MAX_X,
        min_y=ARENA_MIN_Y,
        max_y=ARENA_MAX_Y
    ))
    
    return arena_entity
