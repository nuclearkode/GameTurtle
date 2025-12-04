# Robo-Arena: Advanced ECS Game Engine

A sophisticated 2D top-down arena shooter built with Python's turtle library, featuring a modern Entity-Component-System (ECS) architecture inspired by professional game engines like Unity, Unreal, and Godot.

## Overview

Robo-Arena is not just a game—it's a **mini game engine** built from scratch with:
- ✅ **ECS Architecture**: Composable entities built from components, not inheritance
- ✅ **Data-Oriented Design**: Components are pure data, systems operate on arrays
- ✅ **System-Driven Logic**: Behavior lives in systems, not entities
- ✅ **Professional Structure**: Clear separation of concerns, extensible design
- ✅ **Advanced Features**: AI behaviors, pathfinding, wave spawning, particle effects

## Game Features

### Combat
- **Player**: Top-down robot with movement, rotation, and shooting
- **Weapons**: Customizable fire rate, damage, spread, and bullet count
- **Projectiles**: Lifetime-limited, with support for piercing

### Enemies
- **Chaser Bots**: Rush toward the player aggressively
- **Turret Bots**: Stationary, track and shoot at range
- **Swarm Bots**: Flocking behavior using boids-like algorithms
- **Boss Enemies**: Multi-phase battles with increasing difficulty

### Systems
- **Wave System**: Progressive difficulty scaling with enemy budgets
- **Health & Shields**: Damage mitigation, invulnerability frames, shield recharge
- **Collision**: Spatial hashing for performance, circle-circle detection
- **Pathfinding**: A* algorithm with grid-based navigation
- **Particles**: Visual effects for explosions and trails
- **Power-Ups**: Pickups for health, shields, and upgrades

## Architecture

### Core ECS Components

**Entity**: Just an ID with a bag of components
```python
entity = entity_manager.create_entity()
entity_manager.add_component(entity.id, Transform(x=0, y=0))
entity_manager.add_component(entity.id, Health(hp=100))
```

**Components**: Pure data structures (no methods)
- `Transform`: position, velocity, angle
- `Physics`: mass, friction, max_speed
- `Health`: hp, armor, invulnerability
- `AIBrain`: behavior type, state, target
- `Weapon`: fire_rate, damage, projectile properties
- And 15+ more...

**Systems**: Behavior logic that operates on components
```python
class PhysicsSystem(GameSystem):
    def update(self, dt: float):
        entities = self.entity_manager.query_entities(Transform, Physics)
        for entity in entities:
            transform = entity.get_component(Transform)
            physics = entity.get_component(Physics)
            # Apply physics...
```

### System Execution Order
1. **PlayerSystem** (0): Process input
2. **AISystem** (5): Enemy decision-making
3. **PhysicsSystem** (10): Apply velocities, friction
4. **WeaponSystem** (15): Fire projectiles, cooldowns
5. **CollisionSystem** (20): Detect collisions, spatial hashing
6. **HealthSystem** (30): Apply damage, death logic
7. **WaveSystem** (40): Spawn enemies, track progress
8. **PathfindingSystem** (50): A* pathfinding
9. **PowerUpSystem** (60): Handle pickups
10. **ParticleSystem** (80): Visual effects
11. **RenderSystem** (90): Draw everything

### Module Structure
```
workspace/
├── main.py                 # Entry point
├── engine/
│   ├── core/
│   │   ├── entity.py       # Entity, EntityManager, ComponentRegistry
│   │   ├── component.py    # All component definitions
│   │   ├── system.py       # GameSystem base, SystemManager
│   │   └── game_engine.py  # Main game loop orchestrator
│   ├── systems/
│   │   ├── physics_system.py
│   │   ├── collision_system.py
│   │   ├── render_system.py
│   │   ├── ai_system.py
│   │   ├── weapon_system.py
│   │   ├── health_system.py
│   │   ├── wave_system.py
│   │   ├── pathfinding_system.py
│   │   ├── powerup_system.py
│   │   ├── particle_system.py
│   │   └── player_system.py
│   └── utils/
│       ├── input_manager.py
│       ├── math_utils.py
│       └── pathfinding.py
└── game/
    ├── config.py           # Game constants
    └── factory.py          # Entity creation functions
```

## Controls

- **WASD / Arrow Keys**: Move player
- **Q / E**: Rotate left/right
- **SPACE**: Fire weapon
- **ESC**: Pause game
- **Q** (when paused): Quit

## Installation & Running

### Requirements
- Python 3.7+
- turtle (included in standard library)

### Run the Game
```bash
python main.py
```

No external dependencies needed! Everything uses Python's built-in libraries.

## Design Principles

### 1. Composability
Entities are built from components, not deep inheritance hierarchies:
```python
# Create a new enemy type by composing components
entity = create_entity()
add_component(entity, Transform(...))
add_component(entity, Health(...))
add_component(entity, AIBrain(behavior_type=AIBehavior.SWARM))
add_component(entity, Weapon(...))
```

### 2. Data-Oriented Design
Components store only data. Systems operate on that data:
```python
@dataclass
class Transform:
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    angle: float = 0.0
```

### 3. System-Driven Behavior
Logic lives in systems, not scattered across entity classes:
```python
# All physics logic in one place
class PhysicsSystem:
    def update(self, dt):
        for entity in query(Transform, Physics):
            # Update positions, apply friction, clamp velocities...
```

### 4. Extensibility
Adding new features is straightforward:

**New Component**:
```python
@dataclass
class Stealth:
    visibility: float = 1.0
    detection_range_modifier: float = 1.0
```

**New System**:
```python
class StealthSystem(GameSystem):
    def update(self, dt):
        # Implement stealth logic...
```

**New Enemy**:
```python
def create_ninja_enemy(em, x, y):
    entity = em.create_entity()
    em.add_component(entity.id, Transform(x=x, y=y))
    em.add_component(entity.id, AIBrain(behavior_type=AIBehavior.STEALTH))
    em.add_component(entity.id, Stealth(visibility=0.5))
    return entity
```

## Advanced Features

### AI System
- **Chaser**: Direct pursuit with optional pathfinding
- **Turret**: Stationary tracking with line-of-sight checks
- **Swarm**: Boids algorithm (cohesion, separation, alignment)
- **Boss**: Multi-phase state machine

### Collision System
- Spatial hashing for broad-phase optimization
- Circle-circle collision detection
- Tag-based collision filtering (player vs. enemy projectiles)
- Trigger vs. solid collisions

### Pathfinding
- Grid-based A* algorithm
- Path caching for performance
- Path simplification to reduce waypoints
- Dynamic obstacle updates

### Wave System
- Budget-based difficulty scaling
- Enemy type unlocking (turrets at wave 3, swarm at wave 5, boss at wave 10)
- Configurable spawn positions
- Wave completion callbacks for upgrades

## Performance Optimizations

### Current Optimizations
1. **Object Pooling**: Turtle objects reused instead of recreated
2. **Spatial Hashing**: O(n) collision detection instead of O(n²)
3. **Deferred Destruction**: Entities destroyed at end of frame, not during iteration
4. **Static Background**: Arena drawn once, not every frame
5. **Component Registry**: Fast entity queries by component type

### Future Optimizations (v2)
1. **Component Arrays**: Contiguous memory layout
2. **Structure of Arrays (SoA)**: Vectorized operations
3. **Archetype Storage**: Group entities by component signature
4. **Dirty Flags**: Skip unchanged entities
5. **NumPy Integration**: SIMD operations for physics

## Extending the Engine

### Add a New Weapon Type
```python
# In game/factory.py
def create_shotgun_weapon():
    return Weapon(
        fire_rate=1.0,
        damage=8.0,
        bullet_count=5,      # Multiple bullets
        spread=30.0,         # Wide spread
        projectile_speed=300.0
    )
```

### Add a New AI Behavior
```python
# In engine/systems/ai_system.py
def _update_assassin(self, entity, ai, transform, player_pos, dt):
    """Assassin: Teleport behind player and attack"""
    # Implementation...
```

### Add Status Effects
```python
# Already supported! Use StatusEffect component:
status = entity.get_component(StatusEffect)
status.add_effect("poison", duration=5.0, magnitude=2.0)
status.add_effect("slow", duration=3.0, magnitude=0.5)
```

## Code Quality

- **Clear Separation**: Data (components) vs. Logic (systems) vs. Orchestration (engine)
- **Single Responsibility**: Each system has one job
- **No God Objects**: Entity is just an ID, minimal coupling
- **Type Hints**: Full type annotations throughout
- **Documentation**: Extensive docstrings and comments

## Lessons Learned

1. **ECS vs. OOP**: ECS wins for flexibility and composition
2. **Data Locality**: Keep related data together (components)
3. **System Order Matters**: Dependencies require careful prioritization
4. **Turtle Limitations**: 100-200 entities max before slowdown
5. **Deferred Operations**: Never modify collections during iteration

## Future Enhancements

- [ ] Boss telegraphed attacks with visual indicators
- [ ] More power-up types (multishot, homing missiles)
- [ ] Upgrade tree between waves
- [ ] Persistent high scores
- [ ] Sound effects (using winsound or pygame.mixer)
- [ ] Mini-map display
- [ ] Screen shake on impacts
- [ ] Better particle effects (trails, smoke)

## Contributing

This is a reference implementation demonstrating modern game architecture. Feel free to:
- Study the code for learning purposes
- Extend it with new features
- Optimize performance further
- Port to other rendering backends (pygame, pyglet, arcade)

## License

MIT License - Feel free to learn from and build upon this code.

## Acknowledgments

Built as a demonstration of:
- Entity-Component-System architecture
- Data-oriented design principles
- Professional game engine patterns
- Python best practices

Inspired by Unity, Unreal Engine, Godot, and Bevy.

---

**Robo-Arena**: Where turtles meet modern game engine architecture! 🐢🎮🤖
