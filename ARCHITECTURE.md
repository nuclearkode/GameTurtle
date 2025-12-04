# Advanced Turtle Arena Game Engine - Architecture Design

## Module Structure

```
game_engine/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── entity.py          # Entity ID and EntityManager
│   ├── component.py       # Component base class and all component dataclasses
│   ├── system.py          # System base class and SystemManager
│   └── registry.py        # ComponentRegistry for fast lookups
├── systems/
│   ├── __init__.py
│   ├── physics.py         # PhysicsSystem
│   ├── collision.py       # CollisionSystem
│   ├── render.py          # RenderSystem
│   ├── ai.py              # AISystem
│   ├── weapon.py          # WeaponSystem
│   ├── health.py          # HealthSystem
│   ├── wave.py            # WaveSystem
│   ├── pathfinding.py     # PathfindingSystem (optional)
│   └── particle.py        # ParticleSystem (optional)
├── input/
│   ├── __init__.py
│   └── input_handler.py   # InputState and key mapping
├── game/
│   ├── __init__.py
│   ├── game_loop.py       # Main game loop with timing
│   └── game_state.py      # Game state management
└── utils/
    ├── __init__.py
    └── math_utils.py      # Vector math, distance, angle utilities
```

## Core Concepts

### Entities
- Entities are UUIDs (strings)
- No behavior, just identity
- Managed by EntityManager

### Components (Pure Data)
All components are dataclasses with no methods:

1. **Transform**: x, y, vx, vy, angle, angular_velocity
2. **Renderable**: shape, color, size, turtle_ref
3. **Collider**: radius, mask, tags
4. **Physics**: mass, friction, max_speed, acceleration
5. **Health**: hp, max_hp, armor
6. **Weapon**: fire_rate, damage, projectile_speed, spread, bullet_count, cooldown
7. **Projectile**: owner_id, damage, lifetime, time_alive, pierce_count
8. **AIBrain**: behavior_type, state, target_id, awareness_range, attack_range, cooldowns, phase
9. **Shield**: hp, max_hp, recharge_rate, last_damage_time
10. **StatusEffects**: slow_timer, stun_timer, burn_timer, slow_magnitude, burn_dps
11. **WaveInfo**: current_wave, enemies_remaining (for player/global)

### Systems (Behavior)
Each system operates on entities with specific component signatures:

1. **PhysicsSystem**: Updates Transform based on Physics
2. **CollisionSystem**: Broad-phase + narrow-phase collision detection
3. **RenderSystem**: Draws entities via turtle
4. **AISystem**: Updates AIBrain, moves enemies, makes decisions
5. **WeaponSystem**: Handles firing, cooldowns, projectile creation
6. **HealthSystem**: Applies damage, handles death, shield regeneration
7. **WaveSystem**: Spawns waves, manages difficulty
8. **PathfindingSystem**: Grid-based A* for navigation
9. **ParticleSystem**: Visual effects

### Managers

**EntityManager**:
- create_entity() -> entity_id
- destroy_entity(entity_id)
- add_component(entity_id, component)
- remove_component(entity_id, component_type)
- get_component(entity_id, component_type)
- defer_destruction(entity_id) - queue for end of frame

**ComponentRegistry**:
- register(entity_id, component)
- unregister(entity_id, component_type)
- get_all(component_type) -> List[entity_id]
- get_entities_with(*component_types) -> Set[entity_id]

**SystemManager**:
- register_system(system, priority)
- update_all(dt) - calls systems in priority order

## Data Flow

1. **Input** → Updates InputState
2. **Systems** → Read components, update components, create/destroy entities
3. **Render** → Draws current state
4. **Cleanup** → Processes deferred destruction

## Performance Considerations

- ComponentRegistry uses dicts for O(1) lookups
- Systems iterate over component arrays (cache-friendly)
- Deferred destruction prevents mid-frame entity removal
- Batch operations where possible (e.g., collision broad-phase)
