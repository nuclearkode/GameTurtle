# Advanced Turtle Arena Game Engine

A modern, ECS-based 2D top-down arena shooter game engine built on Python's turtle library. This engine demonstrates professional game architecture patterns including Entity-Component-System (ECS), data-oriented design, and system-driven behavior.

## Features

- **Modern ECS Architecture**: Composable entities built from pure data components
- **System-Driven Behavior**: All game logic lives in focused, independent systems
- **Multiple Enemy Types**: Chasers, turrets, and swarm bots with unique AI behaviors
- **Weapon System**: Configurable weapons with different firing patterns
- **Wave-Based Progression**: Increasingly difficult waves with scaling difficulty
- **Collision System**: Broad-phase and narrow-phase collision detection
- **Health & Shields**: Damage system with shield absorption and regeneration
- **Status Effects**: Slow, stun, and burn effects (extensible)

## Architecture

The engine is organized into clear layers:

### Core ECS Layer (`game_engine/core/`)
- **Entity**: Just an ID with component references
- **Components**: Pure data classes (Transform, Renderable, Collider, Physics, Health, Weapon, etc.)
- **EntityManager**: Creates/destroys entities, manages components
- **ComponentRegistry**: Fast component lookups and queries
- **GameSystem**: Base class for all systems
- **SystemManager**: Manages system update order

### Systems Layer (`game_engine/systems/`)
- **PhysicsSystem**: Movement, velocity, friction, acceleration
- **CollisionSystem**: Collision detection and resolution
- **RenderSystem**: Turtle-based rendering with object pooling
- **AISystem**: Enemy AI (chaser, turret, swarm, boss)
- **WeaponSystem**: Weapon cooldowns and projectile spawning
- **HealthSystem**: Damage application, death handling, status effects
- **WaveSystem**: Wave spawning and difficulty scaling
- **PlayerControllerSystem**: Player input and movement

### Input Layer (`game_engine/input/`)
- **InputHandler**: Maps keyboard events to game actions
- **InputState**: Tracks current frame input state

### Game Layer (`game_engine/game/`)
- **GameLoop**: Main game loop with timing and orchestration

## Installation

Requires Python 3.7+ with the `turtle` module (included in standard library).

**Note**: The `turtle` module requires `tkinter`, which may need to be installed separately on some Linux distributions:
- Ubuntu/Debian: `sudo apt-get install python3-tk`
- Fedora: `sudo dnf install python3-tkinter`
- Arch: `sudo pacman -S tk`

```bash
# Run the game
python3 main.py

# Or test the ECS core without graphics
python3 test_ecs.py
```

## Controls

- **W/A/S/D**: Move forward/backward/left/right
- **Q/E**: Rotate left/right
- **Space**: Fire weapon
- **Escape**: Quit game

## Gameplay

You control a robot in an arena. Waves of enemies spawn from the edges:
- **Chasers** (red triangles): Rush toward you
- **Turrets** (orange squares): Stationary, rotate to face and shoot
- **Swarm bots** (pink circles): Flocking behavior, move in groups

Survive as long as you can! Each wave increases in difficulty.

## Design Principles

1. **Composition over Inheritance**: Entities are bags of components, not deep class hierarchies
2. **Data-Oriented**: Components are pure data; systems operate on arrays for cache-friendly iteration
3. **System-Driven**: Behavior lives in systems, not entities
4. **Separation of Concerns**: Each system has one clear responsibility
5. **Extensibility**: Easy to add new components/systems without modifying existing code

## Extending the Engine

### Adding a New Component

1. Create a dataclass in `game_engine/core/component.py`:
```python
@dataclass
class MyComponent(Component):
    my_field: float = 0.0
```

2. Register it in the component registry when adding to entities

### Adding a New System

1. Create a class inheriting from `GameSystem`:
```python
class MySystem(GameSystem):
    def update(self, dt: float):
        # Your logic here
        pass
```

2. Register it in `GameLoop`:
```python
my_system = MySystem(self.entity_manager, self.component_registry)
self.system_manager.register_system(my_system)
```

### Adding a New Enemy Type

1. Add behavior type to `AIBrain.behavior_type`
2. Implement behavior in `AISystem._update_<type>()`
3. Add spawn logic in `WaveSystem._create_<type>()`
4. Update difficulty costs in `WaveSystem._spawn_enemy()`

## Performance Considerations

The current implementation prioritizes clarity and extensibility. For optimization opportunities:

1. **Spatial Partitioning**: Replace O(n²) collision checks with grid-based broad-phase
2. **Component Arrays**: Store components in arrays indexed by entity ID for better cache locality
3. **Batch Operations**: Process similar entities together (e.g., all projectiles in one pass)
4. **Turtle Pooling**: Already implemented in RenderSystem

## File Structure

```
game_engine/
├── core/              # ECS primitives
├── systems/           # Game systems
├── input/             # Input handling
└── game/              # Game loop

main.py                # Entry point
ARCHITECTURE.md        # Detailed architecture documentation
```

## License

This is a demonstration project. Feel free to use and modify as needed.

## Credits

Built as a demonstration of modern game engine architecture patterns using Python's turtle library.
