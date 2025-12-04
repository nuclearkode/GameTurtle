# Design Summary: Advanced Turtle Arena Game Engine

## Architecture Overview

This game engine implements a hybrid ECS (Entity-Component-System) + data-oriented design with light OOP principles, similar to modern game engines like Unity, Unreal, and Godot.

## Core Design Principles

### 1. Entity-Component-System (ECS)

**Entities**: Just UUIDs - no behavior, only identity
- Created via `EntityManager.create_entity()`
- Destroyed via `EntityManager.destroy_entity()` (deferred)

**Components**: Pure data structures (dataclasses)
- No methods, only data fields
- Examples: `Transform`, `Health`, `Weapon`, `AIBrain`
- Attached to entities via `EntityManager.add_component()`

**Systems**: Contain all behavior/logic
- Operate on entities with specific component signatures
- Examples: `PhysicsSystem`, `AISystem`, `WeaponSystem`
- Updated each frame in priority order

### 2. Data-Oriented Design

- **ComponentRegistry**: Fast O(1) lookups by component type
- Components stored in arrays/sets for cache-friendly iteration
- Systems iterate over component arrays, not entity hierarchies
- Batch operations where possible

### 3. System-Driven Architecture

- Behavior lives in systems, not entities
- Systems are independent (no direct dependencies)
- Communication via shared component data
- Clear separation of concerns

## Module Structure

```
game_engine/
├── core/                    # ECS primitives
│   ├── entity.py           # EntityManager
│   ├── component.py        # All component dataclasses
│   ├── system.py           # GameSystem base, SystemManager
│   └── registry.py         # ComponentRegistry
├── systems/                 # Game systems
│   ├── physics.py          # Movement, velocity, friction
│   ├── collision.py        # Collision detection
│   ├── render.py           # Turtle rendering
│   ├── ai.py               # Enemy AI behaviors
│   ├── weapon.py           # Weapon firing, projectiles
│   ├── health.py           # Health, shields, death
│   └── wave.py             # Wave spawning
├── input/                   # Input handling
│   └── input_handler.py    # InputState, key mapping
├── game/                    # Game orchestration
│   ├── game_loop.py        # Main loop, timing
│   └── game_state.py       # Game state management
└── utils/                   # Utilities
    └── math_utils.py       # Vector math, distance, angles
```

## Component Types

### Core Components
- **Transform**: Position (x, y), velocity (vx, vy), rotation (angle)
- **Renderable**: Shape, color, size, turtle reference
- **Collider**: Radius, collision mask, tags
- **Physics**: Mass, friction, max speed, acceleration

### Gameplay Components
- **Health**: HP, max HP, armor
- **Weapon**: Fire rate, damage, projectile speed, spread
- **Projectile**: Owner ID, damage, lifetime, pierce count
- **AIBrain**: Behavior type, state, target, ranges, cooldowns
- **Shield**: HP, recharge rate, recharge delay
- **StatusEffects**: Slow, stun, burn timers and magnitudes
- **WaveInfo**: Current wave, enemies remaining

## System Execution Order

Systems run in priority order (lower = earlier):

1. **PhysicsSystem** (10): Updates positions/velocities
2. **AISystem** (20): Updates enemy AI behavior
3. **WeaponSystem** (30): Handles firing, projectile creation
4. **CollisionSystem** (40): Detects collisions, applies damage
5. **HealthSystem** (50): Updates health, shields, status effects, death
6. **WaveSystem** (60): Spawns waves, manages difficulty
7. **RenderSystem** (100): Draws everything (runs last)

## Game Loop Flow

```
1. Calculate delta time (dt)
2. Handle input → Update InputState
3. Update systems in priority order:
   - PhysicsSystem: Move entities
   - AISystem: Update enemy behavior
   - WeaponSystem: Fire weapons, create projectiles
   - CollisionSystem: Check collisions, apply damage
   - HealthSystem: Update health, check death
   - WaveSystem: Spawn enemies
   - RenderSystem: Draw entities
4. Flush entity destruction (cleanup)
5. Update screen (turtle.update())
6. Sleep to cap FPS
```

## Adding New Features

### Adding a New Enemy Type

1. Add to `AIBehaviorType` enum in `component.py`:
```python
class AIBehaviorType(Enum):
    NEW_ENEMY = "new_enemy"
```

2. Implement behavior in `AISystem`:
```python
def _update_new_enemy(self, entity_id, transform, brain, physics, player_transform, dt):
    # Your AI logic here
    pass
```

3. Add to `AISystem.update()`:
```python
elif brain.behavior_type == AIBehaviorType.NEW_ENEMY:
    self._update_new_enemy(...)
```

4. Configure in `WaveSystem._spawn_enemy()`:
```python
colors = {
    AIBehaviorType.NEW_ENEMY: "green",
    # ...
}
```

### Adding a New Component

1. Create dataclass in `component.py`:
```python
@dataclass
class MyComponent(Component):
    field1: float = 0.0
    field2: str = ""
```

2. Add to imports in `core/__init__.py`

3. Systems can now query for it:
```python
entities = self.registry.get_entities_with(Transform, MyComponent)
```

### Adding a New System

1. Create system class:
```python
class MySystem(GameSystem):
    def update(self, dt: float):
        entities = self.registry.get_entities_with(RequiredComponent)
        for entity_id in entities:
            # Your logic here
            pass
```

2. Register in `GameLoop._setup_systems()`:
```python
self.system_manager.register_system(
    MySystem(self.entity_manager, self.registry),
    priority=45  # Choose appropriate priority
)
```

## Performance Considerations

### Current Optimizations
- ComponentRegistry uses dicts for O(1) lookups
- Systems iterate over component sets (cache-friendly)
- Deferred entity destruction prevents mid-frame issues
- Object pooling for turtle objects in RenderSystem

### Potential Future Optimizations
- Store components in arrays instead of dicts (SoA - Structure of Arrays)
- Batch collision checks using spatial partitioning
- Component archetypes for faster iteration
- Parallel system execution (threading)

## Design Decisions Explained

### Why ECS?
- **Composability**: Entities built from components, not inheritance
- **Flexibility**: Easy to add new behaviors without changing existing code
- **Performance**: Data-oriented iteration is cache-friendly
- **Debugging**: Clear separation of data and logic

### Why Data-Oriented?
- **Cache Efficiency**: Iterating over arrays of same type is faster
- **Scalability**: Better performance with many entities
- **Predictability**: Easier to optimize hot paths

### Why System-Driven?
- **Separation of Concerns**: Each system has one responsibility
- **Testability**: Systems can be tested independently
- **Maintainability**: Easy to understand and modify

## Testing Strategy

1. **Unit Tests**: Test individual systems in isolation
2. **Integration Tests**: Test system interactions
3. **Component Tests**: Verify component data integrity
4. **Gameplay Tests**: Manual testing of game mechanics

Example test structure:
```python
def test_physics_system():
    # Create test entities
    # Run physics system
    # Verify positions updated correctly
```

## Extension Points

The engine is designed to be extended:

1. **New Enemy Types**: Add to AIBehaviorType, implement in AISystem
2. **New Weapons**: Extend Weapon component, modify WeaponSystem
3. **New Systems**: Create new GameSystem subclass, register in GameLoop
4. **New Components**: Add dataclass, systems can use it
5. **New Game Modes**: Extend GameState, modify GameLoop

## Code Quality

- Type hints throughout
- Clear naming conventions
- Comprehensive docstrings
- Modular design
- No circular dependencies
- Minimal global state
