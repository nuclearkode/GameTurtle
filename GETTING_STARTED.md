# Getting Started with Robo-Arena

## Quick Start

### Prerequisites
- Python 3.7 or higher
- tkinter (usually included with Python)

### Installation
No installation needed! All dependencies are part of Python's standard library.

```bash
# Clone or download the project
cd workspace

# Run the game
python3 main.py
```

### First Time Setup
The game will automatically:
1. Initialize the ECS engine
2. Create the player at center (0, 0)
3. Spawn some walls for cover
4. Start wave 1 with basic enemies

## Controls

| Key | Action |
|-----|--------|
| W / ↑ | Move up |
| S / ↓ | Move down |
| A / ← | Move left |
| D / → | Move right |
| Q | Rotate left |
| E | Rotate right |
| SPACE | Fire weapon |
| ESC | Pause game |

## Game Mechanics

### Player
- **Health**: 100 HP
- **Shield**: 50 HP (regenerates after 3 seconds)
- **Weapon**: Fires 3 shots per second
- **Movement**: Free 8-directional movement

### Enemies

#### Chaser Bots (Red)
- Rush toward you
- 30 HP
- 10 points
- Appear from wave 1

#### Turret Bots (Orange)
- Stationary shooters
- 50 HP, armored
- 20 points
- Appear from wave 3

#### Swarm Bots (Yellow)
- Flocking behavior
- 15 HP, fast
- 5 points
- Appear from wave 5

#### Boss (Purple)
- Multi-phase attacks
- 300 HP, heavily armored
- 100 points
- Appears from wave 10

### Waves
- Waves spawn automatically
- 5 second break between waves
- Difficulty increases each wave
- New enemy types unlock as you progress

## Testing the ECS Engine

Want to see the engine without turtle/graphics?

```bash
python3 test_ecs.py
```

This runs unit tests demonstrating:
- Entity creation and management
- Component queries
- System updates
- Performance benchmarks

**Example output:**
```
✓ Created 1000 entities with components in 3.96ms
✓ Queried Transform+Health in 0.11ms (500 entities)
✅ All ECS tests passed!
```

## Project Structure

```
workspace/
├── main.py              # Start here!
├── test_ecs.py          # Test the engine
│
├── Documentation/
│   ├── README.md                    # Overview
│   ├── ARCHITECTURE.md              # Deep dive
│   ├── IMPLEMENTATION_SUMMARY.md    # What was built
│   └── GETTING_STARTED.md           # This file
│
├── engine/              # Reusable game engine
│   ├── core/
│   │   ├── entity.py        # ECS foundation
│   │   ├── component.py     # All components
│   │   ├── system.py        # System base class
│   │   └── game_engine.py   # Main game loop
│   │
│   ├── systems/         # Game systems
│   │   ├── physics_system.py
│   │   ├── collision_system.py
│   │   ├── render_system.py
│   │   ├── ai_system.py
│   │   ├── weapon_system.py
│   │   ├── health_system.py
│   │   └── ... (11 systems total)
│   │
│   └── utils/           # Helper utilities
│       ├── input_manager.py
│       ├── math_utils.py
│       └── pathfinding.py
│
└── game/                # Game-specific code
    ├── config.py        # Constants
    └── factory.py       # Entity creation
```

## Understanding the Code

### 1. Entities are Simple
```python
# Just an ID with components
player = entity_manager.create_entity()
```

### 2. Components are Data
```python
@dataclass
class Transform:
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0
```

### 3. Systems are Logic
```python
class PhysicsSystem(GameSystem):
    def update(self, dt):
        # Get all entities with Transform + Physics
        entities = query_entities(Transform, Physics)
        
        # Update their positions
        for entity in entities:
            transform.x += transform.vx * dt
```

### 4. Manager Orchestrates
```python
# Game loop
while running:
    input.update()
    systems.update_all(dt)  # All systems run in order
    entities.cleanup()
    screen.update()
```

## Common Tasks

### Add a New Enemy Type

1. **Define stats in config.py:**
```python
ENEMY_SETTINGS = {
    'ninja': {
        'hp': 40.0,
        'speed': 180.0,
        'color': 'purple',
        # ...
    }
}
```

2. **Create factory function in factory.py:**
```python
def create_ninja(entity_manager, x, y):
    enemy = entity_manager.create_entity()
    entity_manager.add_component(enemy.id, Transform(x=x, y=y))
    entity_manager.add_component(enemy.id, Health(hp=40))
    entity_manager.add_component(enemy.id, AIBrain(behavior_type=AIBehavior.CHASER))
    return enemy
```

3. **Register with wave system:**
```python
wave_system.set_spawn_function('ninja', create_ninja)
```

### Add a New Weapon

```python
# In factory.py or wherever you create the weapon component
weapon = Weapon(
    fire_rate=5.0,        # 5 shots per second
    damage=20.0,          # 20 damage per shot
    bullet_count=3,       # 3 bullets per shot
    spread=15.0,          # 15 degree spread
    projectile_speed=500.0,
    bullet_color="red",
    bullet_lifetime=2.0
)
```

### Add a New System

1. **Create the system file:**
```python
# engine/systems/my_system.py
from engine.core.system import GameSystem

class MySystem(GameSystem):
    def update(self, dt: float):
        # Your logic here
        entities = self.entity_manager.query_entities(Component1, Component2)
        for entity in entities:
            # Process entity
            pass
```

2. **Register in main.py:**
```python
my_system = MySystem(engine.entity_manager, priority=25)
engine.add_system(my_system)
```

Priority determines execution order (lower = earlier).

## Debugging Tips

### Print Entity Count
```python
print(f"Entities: {entity_manager.entity_count()}")
```

### Query Entities
```python
enemies = entity_manager.query_entities(Enemy)
print(f"Enemies alive: {len(enemies)}")
```

### Check Component Values
```python
player = entity_manager.query_entities(Player)[0]
health = player.get_component(Health)
print(f"Player HP: {health.hp}/{health.max_hp}")
```

### Enable System Logging
Add print statements in system update methods:
```python
def update(self, dt):
    entities = self.entity_manager.query_entities(Transform)
    print(f"PhysicsSystem updating {len(entities)} entities")
```

## Performance Tips

### Current Performance
- **Target**: 60 FPS
- **Capacity**: 100-200 entities comfortably
- **Bottleneck**: Turtle rendering

### Optimization Strategies
1. **Reduce entity count**: Despawn off-screen entities
2. **Limit particles**: Cap particle system spawns
3. **Throttle expensive systems**: Run pathfinding every N frames
4. **Use spatial hashing**: Already implemented in collision system

### If You Hit Performance Issues
```python
# In main.py, reduce target FPS
game_engine = GameEngine(target_fps=30)  # Instead of 60

# Or reduce enemy count
# In wave_system.py, adjust budget scaling
def _calculate_wave_budget(self, wave_number):
    return base_budget * (wave_number ** 0.5)  # Slower growth
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'tkinter'"
Install tkinter:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS
# Usually included, reinstall Python if missing

# Windows
# Reinstall Python with "tcl/tk" option checked
```

### Game Runs Slowly
- Reduce target FPS in config.py
- Limit enemy spawns in wave system
- Disable particle effects (comment out particle_system creation)

### No Window Appears
- Check that turtle is installed: `python3 -c "import turtle"`
- Ensure you have a GUI environment (not SSH/headless)

### Entities Not Colliding
- Check collision tags and masks in config.py
- Verify both entities have Collider components
- Ensure CollisionSystem is registered and running

## Next Steps

1. **Play the game**: `python3 main.py`
2. **Read ARCHITECTURE.md**: Understand the design
3. **Run tests**: `python3 test_ecs.py`
4. **Modify config.py**: Tweak game parameters
5. **Add new enemies**: Follow the guide above
6. **Create new systems**: Extend the engine

## Learning Resources

### Understand ECS
- Read `ARCHITECTURE.md` for detailed explanation
- Study `engine/core/entity.py` for ECS implementation
- Look at `test_ecs.py` for usage examples

### Understand Systems
- Each system file in `engine/systems/` is self-contained
- Start with `physics_system.py` (simplest)
- Move to `ai_system.py` (more complex)

### Understand Components
- All defined in `engine/core/component.py`
- Just data, no methods
- Use dataclasses for simplicity

## Community & Support

This is a reference implementation for educational purposes. Feel free to:
- Study the code
- Modify and extend it
- Use it as a foundation for your own projects
- Share improvements and ideas

## License

MIT License - Free to use, modify, and distribute.

---

**Happy coding!** 🎮🤖

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md)

For implementation details, see [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
