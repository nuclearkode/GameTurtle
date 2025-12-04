"""
Game configuration and constants.
"""

# Arena settings
ARENA_WIDTH = 800
ARENA_HEIGHT = 600
ARENA_MIN_X = -400
ARENA_MAX_X = 400
ARENA_MIN_Y = -300
ARENA_MAX_Y = 300

# Game settings
TARGET_FPS = 60

# Player settings
PLAYER_SPEED = 200.0
PLAYER_HP = 100.0
PLAYER_SHIELD = 50.0
PLAYER_FIRE_RATE = 3.0
PLAYER_DAMAGE = 15.0
PLAYER_SIZE = 1.5
PLAYER_ROTATION_SPEED = 360.0

# Enemy settings
ENEMY_SETTINGS = {
    'chaser': {
        'hp': 30.0,
        'speed': 120.0,
        'size': 1.2,
        'color': 'red',
        'damage': 10.0,
        'points': 10,
        'awareness_range': 400.0,
        'attack_range': 150.0,
        'personal_space': 40.0,
    },
    'turret': {
        'hp': 50.0,
        'speed': 0.0,  # Stationary
        'size': 1.5,
        'color': 'orange',
        'fire_rate': 1.0,
        'damage': 12.0,
        'points': 20,
        'awareness_range': 500.0,
        'attack_range': 300.0,
    },
    'swarm': {
        'hp': 15.0,
        'speed': 100.0,
        'size': 0.8,
        'color': 'yellow',
        'damage': 5.0,
        'points': 5,
        'awareness_range': 300.0,
        'attack_range': 100.0,
        'personal_space': 30.0,
        'flock_radius': 80.0,
    },
    'boss': {
        'hp': 300.0,
        'speed': 80.0,
        'size': 3.0,
        'color': 'purple',
        'fire_rate': 0.5,
        'damage': 25.0,
        'points': 100,
        'awareness_range': 600.0,
        'attack_range': 250.0,
        'personal_space': 100.0,
    }
}

# Projectile settings
PROJECTILE_SPEED = 400.0
PROJECTILE_LIFETIME = 2.0
PROJECTILE_SIZE = 5.0

# Collision tags
COLLISION_TAGS = {
    'player': {'player'},
    'enemy': {'enemy'},
    'player_projectile': {'player_projectile'},
    'enemy_projectile': {'enemy_projectile'},
    'wall': {'wall'},
    'powerup': {'powerup'},
}

# Collision masks (what each tag collides with)
COLLISION_MASKS = {
    'player': {'enemy', 'enemy_projectile', 'wall', 'powerup'},
    'enemy': {'player', 'player_projectile', 'wall'},
    'player_projectile': {'enemy', 'wall'},
    'enemy_projectile': {'player', 'wall'},
    'wall': {'player', 'enemy', 'player_projectile', 'enemy_projectile'},
    'powerup': {'player'},
}

# Wave settings
WAVE_TIME_BETWEEN = 5.0
WAVE_DIFFICULTY_SCALING = 1.5

# Upgrade options
UPGRADES = [
    {'name': 'Max Health +20', 'type': 'health', 'value': 20},
    {'name': 'Fire Rate +20%', 'type': 'fire_rate', 'value': 0.2},
    {'name': 'Movement Speed +15%', 'type': 'speed', 'value': 0.15},
    {'name': 'Damage +25%', 'type': 'damage', 'value': 0.25},
    {'name': 'Shield Capacity +30', 'type': 'shield', 'value': 30},
    {'name': 'Bullet Piercing +1', 'type': 'piercing', 'value': 1},
    {'name': 'Shield Recharge +50%', 'type': 'shield_recharge', 'value': 0.5},
]
