# Advanced Turtle Arena Game Engine

A modern 2D top-down arena shooter built with Python's turtle library, featuring an ECS (Entity-Component-System) architecture with data-oriented design principles.

## Architecture

This game engine demonstrates:

- **ECS Architecture**: Entities are IDs, Components are pure data, Systems contain behavior
- **Data-Oriented Design**: Components stored in registries for cache-friendly iteration
- **System-Driven Logic**: Behavior lives in systems, not entities
- **Composable Design**: Easy to add new enemy types, weapons, and features

## Features

### Core Systems
- **PhysicsSystem**: Movement, velocity, friction, acceleration
- **CollisionSystem**: Broad-phase and narrow-phase collision detection
- **RenderSystem**: Efficient turtle-based rendering with object pooling
- **AISystem**: Multiple AI behaviors (Chaser, Turret, Swarm, Boss)
- **WeaponSystem**: Firing, cooldowns, projectile management
- **HealthSystem**: Health, shields, status effects, death handling
- **WaveSystem**: Wave spawning with difficulty scaling

### Enemy Types
- **Chaser**: Rushes directly toward the player
- **Turret**: Stationary, rotates to face player, fires when in range
- **Swarm**: Boids-like flocking behavior (cohesion, separation, alignment)
- **Boss**: Multi-phase behavior with increasing difficulty

### Game Mechanics
- Player movement with WASD
- Rotation with Q/E
- Shooting with Spacebar
- Waves of enemies with increasing difficulty
- Health and damage system
- Projectile physics

## Installation

Requires Python 3.7+

```bash
# No external dependencies - uses only Python standard library
python main.py
```

## Controls

- **W/A/S/D**: Move player
- **Q/E**: Rotate left/right
- **Spacebar**: Fire weapon
- **P**: Pause/Unpause
- **Escape**: Quit game

## Project Structure

```
game_engine/
├── core/              # ECS primitives (Entity, Component, System, Registry)
├── systems/           # Game systems (Physics, Collision, AI, etc.)
├── input/             # Input handling
├── game/              # Game loop and state management
└── utils/             # Math utilities

main.py                # Entry point
ARCHITECTURE.md        # Detailed architecture documentation
```

## Design Principles

### Components (Pure Data)
All components are dataclasses with no methods. Examples:
- `Transform`: Position, velocity, rotation
- `Health`: HP, max HP, armor
- `Weapon`: Fire rate, damage, projectile properties
- `AIBrain`: Behavior type, state, target

### Systems (Behavior)
Systems operate on entities with specific component signatures:
- Read components
- Update components
- Create/destroy entities
- No direct dependencies between systems

### Entities
Entities are just UUIDs. They have no behavior, only identity.

### Managers
- **EntityManager**: Creates/destroys entities, manages component bags
- **ComponentRegistry**: Fast lookups by component type
- **SystemManager**: Executes systems in priority order

## Extending the Engine

### Adding a New Enemy Type

1. Add behavior type to `AIBehaviorType` enum in `component.py`
2. Implement behavior logic in `AISystem._update_*` method
3. Configure stats in `WaveSystem._spawn_enemy`

### Adding a New Component

1. Create dataclass inheriting from `Component`
2. Add to component imports
3. Systems can now query for this component

### Adding a New System

1. Create class inheriting from `GameSystem`
2. Implement `update(dt)` method
3. Register in `GameLoop._setup_systems` with priority

## Performance Optimizations

- ComponentRegistry uses dicts for O(1) lookups
- Systems iterate over component arrays (cache-friendly)
- Deferred entity destruction prevents mid-frame removal
- Object pooling for turtle objects in RenderSystem

## Future Enhancements

- Pathfinding system (A* grid-based)
- Particle system for visual effects
- Upgrade system between waves
- Status effects (slow, stun, burn)
- More weapon types (shotgun, beam, etc.)
- Sound effects and music
- Save/load system

## License

This is an educational project demonstrating game engine architecture principles.
