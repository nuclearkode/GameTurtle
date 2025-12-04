# Robo-Arena Game Engine Architecture

## Overview
A hybrid ECS (Entity-Component-System) + Data-Oriented game engine built on Python's turtle library.

## Design Principles
1. **Composability**: Entities built from components, not inheritance
2. **Data-Oriented**: Components are pure data, systems operate on arrays
3. **System-Driven**: Behavior lives in systems, not entities
4. **Extensible**: Easy to add new components, systems, and behaviors
5. **Debuggable**: Clear separation of data and logic

## Module Structure

```
workspace/
├── ARCHITECTURE.md          # This file
├── README.md               # User documentation
├── main.py                 # Entry point
├── engine/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── entity.py       # Entity, EntityManager, ComponentRegistry
│   │   ├── component.py    # Base Component class and all component types
│   │   ├── system.py       # GameSystem base class, SystemManager
│   │   └── game_engine.py  # Main game loop orchestrator
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── physics_system.py
│   │   ├── collision_system.py
│   │   ├── render_system.py
│   │   ├── ai_system.py
│   │   ├── weapon_system.py
│   │   ├── health_system.py
│   │   ├── wave_system.py
│   │   ├── pathfinding_system.py
│   │   ├── powerup_system.py
│   │   └── particle_system.py
│   └── utils/
│       ├── __init__.py
│       ├── input_manager.py
│       ├── math_utils.py
│       └── pathfinding.py
└── game/
    ├── __init__.py
    ├── config.py           # Game constants and configuration
    ├── factory.py          # Entity creation functions
    └── upgrades.py         # Upgrade definitions
```

## Core ECS Architecture

### Entity
- Simple ID (UUID) with component dictionary
- No behavior, just a container for components
- Managed by EntityManager

### Components (Pure Data)
All components are dataclasses with no methods:

1. **Transform**: position, velocity, angle, angular_velocity
2. **Physics**: mass, friction, max_speed, acceleration
3. **Renderable**: shape, color, size, layer, visible, turtle_ref
4. **Collider**: radius (circle), aabb (box), tags, mask
5. **Health**: hp, max_hp, armor, invulnerable_time
6. **Shield**: hp, max_hp, recharge_rate, recharge_delay, last_damage_time
7. **Weapon**: fire_rate, cooldown, damage, projectile_speed, spread, bullet_count
8. **Projectile**: owner_id, damage, lifetime, time_alive, piercing
9. **AIBrain**: behavior_type, state, target_id, awareness_range, attack_range, cooldowns, custom_data
10. **Player**: score, lives
11. **Enemy**: type, threat_level, points
12. **StatusEffect**: effects (dict of effect_name -> (duration, magnitude))
13. **WaveInfo**: current_wave, enemies_spawned, enemies_remaining
14. **PowerUp**: type, value, lifetime
15. **Particle**: lifetime, fade_rate

### Systems (Behavior Logic)
Systems query entities by component signature and process them:

1. **PhysicsSystem**: 
   - Apply velocity to position
   - Apply friction and acceleration
   - Clamp to max speed
   - Handle rotation

2. **CollisionSystem**:
   - Broad phase: spatial hashing or simple grid
   - Narrow phase: circle-circle, circle-AABB, AABB-AABB
   - Generate collision events
   - Handle collision response (bounce, stop, etc.)

3. **RenderSystem**:
   - Sort by layer
   - Update turtle positions and headings
   - Draw shapes
   - Handle visibility
   - Object pooling for turtles

4. **AISystem**:
   - Query entities with AIBrain + Transform
   - Dispatch to behavior handlers:
     - **Chaser**: Move toward player, optionally pathfind
     - **Turret**: Rotate to face player, shoot when in range
     - **Swarm**: Boids-like flocking (cohesion, separation, alignment)
     - **Boss**: State machine with multiple phases
   - Update cooldowns
   - Set velocities/accelerations in Physics component

5. **WeaponSystem**:
   - Update cooldowns
   - Handle firing (create projectile entities)
   - Support multiple fire patterns (single, spread, burst)
   - Update projectile lifetimes
   - Destroy expired projectiles

6. **HealthSystem**:
   - Process damage events from collision system
   - Apply armor reduction
   - Update shield before health
   - Handle invulnerability frames
   - Mark entities for death
   - Trigger death effects (spawn particles, loot)

7. **WaveSystem**:
   - Track current wave and enemy count
   - Spawn enemies based on difficulty budget
   - Scale difficulty (enemy stats, count)
   - Handle wave completion
   - Present upgrade choices

8. **PathfindingSystem** (Advanced):
   - Maintain grid representation of arena
   - A* or BFS pathfinding
   - Cache paths for performance
   - Update when obstacles change

9. **PowerUpSystem**:
   - Update power-up lifetimes
   - Check player collision with power-ups
   - Apply buffs/upgrades
   - Visual feedback

10. **ParticleSystem**:
    - Update particle lifetimes
    - Fade/shrink particles
    - Remove dead particles

### Entity Manager
- Create/destroy entities
- Add/remove components
- Query entities by component signature
- Deferred destruction (entities marked for death, removed at end of frame)

### Component Registry
- Index: Dict[component_type, Set[entity_id]]
- Fast queries: "Get all entities with Transform + AIBrain"
- Update indices when components added/removed

### System Manager
- Store list of systems
- Sort by priority
- Call update(dt) on each system in order

## Game Loop Flow

```
1. Initialize Engine
   - Create screen, set up turtle
   - Create EntityManager, SystemManager
   - Register all systems
   - Create player, arena, initial enemies

2. Main Loop (target 60 FPS)
   while running:
       dt = calculate_delta_time()
       
       # Input
       input_manager.update()
       
       # Systems (in order)
       ai_system.update(dt)
       weapon_system.update(dt)
       physics_system.update(dt)
       collision_system.update(dt)
       health_system.update(dt)
       wave_system.update(dt)
       pathfinding_system.update(dt)
       powerup_system.update(dt)
       particle_system.update(dt)
       render_system.update(dt)
       
       # Cleanup
       entity_manager.process_destruction_queue()
       
       # Display
       screen.update()
       sleep_to_cap_fps(dt)

3. Shutdown
   - Clean up turtles
   - Save stats
```

## System Execution Order & Dependencies
1. **AISystem**: Read game state, set desired velocities
2. **WeaponSystem**: Spawn projectiles, update cooldowns
3. **PhysicsSystem**: Apply velocities, update positions
4. **CollisionSystem**: Detect collisions, generate events
5. **HealthSystem**: Apply damage from collision events
6. **WaveSystem**: Spawn new enemies if needed
7. **PathfindingSystem**: Update paths (can be throttled)
8. **PowerUpSystem**: Apply pickups
9. **ParticleSystem**: Update visual effects
10. **RenderSystem**: Draw everything (last!)

## Data-Oriented Optimizations

### Current Approach (v1)
- Components stored in entity's dict: `entity.components[Transform]`
- Systems iterate entity IDs, fetch components as needed
- Simple, flexible, good for prototyping

### Future Optimizations (v2+)
1. **Component Arrays**: Store all Transform components in a contiguous array
   - Better cache locality
   - SIMD potential (NumPy)
   
2. **Structure of Arrays (SoA)**: Instead of `Transform(x, y, vx, vy)`, use:
   - `transforms.x = [x1, x2, x3, ...]`
   - `transforms.y = [y1, y2, y3, ...]`
   - Vectorize operations
   
3. **Archetype Storage**: Group entities by component signature
   - All entities with (Transform, Physics, Collider) in one array
   - Iterate without branching
   
4. **Dirty Flags**: Only process changed entities
   - Mark components dirty when modified
   - Skip unchanged entities in expensive systems

## Performance Budget (Turtle Limitations)
- Target: 60 FPS
- Max entities on screen: ~100-200 (turtle is slow)
- Optimization strategies:
  1. Object pooling for turtles
  2. Pre-draw static elements
  3. Spatial partitioning for collisions
  4. Limit particle count
  5. Throttle expensive systems (pathfinding every N frames)

## AI Behavior Details

### Chaser Bot
- State: IDLE, CHASE, ATTACK
- Awareness range: Start chasing when player nearby
- Direct movement or pathfinding around walls
- Attack: Ram player or melee

### Turret Bot
- State: IDLE, TRACKING, FIRING
- Stationary (no Physics component)
- Rotate to face player
- Line-of-sight check before firing
- Cooldown between shots

### Swarm Bot
- Lightweight, many instances
- Boids behavior:
  - Cohesion: Move toward center of neighbors
  - Separation: Avoid crowding
  - Alignment: Match velocity of neighbors
  - Target: Bias toward player
- Limit neighbor checks (nearest N)

### Boss (Optional)
- Multi-phase state machine
- Phase 1: Single projectiles
- Phase 2: Spread/burst fire
- Phase 3: Summon minions
- Telegraph attacks (color change, pause)
- More HP, larger, slower

## Weapon Types
1. **Pistol**: Single bullet, medium fire rate
2. **Shotgun**: Multiple bullets, spread, slow fire rate
3. **Machine Gun**: Fast fire rate, low damage
4. **Laser**: Instant raycast, high damage, very slow
5. **Rocket**: Slow projectile, AoE on impact

## Upgrade System
Between waves, player chooses 1 of 3 random upgrades:
- Health +20
- Fire rate +20%
- Movement speed +15%
- Bullet damage +5
- Shield capacity +30
- New weapon unlock
- Projectile piercing
- Status effect on hit (slow, burn)

## Collision Layers & Masks
- Layer 0: Player
- Layer 1: Enemies
- Layer 2: Projectiles (player)
- Layer 3: Projectiles (enemy)
- Layer 4: Walls
- Layer 5: Power-ups

Masks define what collides with what:
- Player collides with: Enemies, Enemy projectiles, Walls, Power-ups
- Enemies collide with: Player projectiles, Walls
- etc.

## Event System (Simple)
For decoupling systems:
- Collision events: (entity_a, entity_b, collision_data)
- Damage events: (entity, damage, source)
- Death events: (entity)
- Wave complete events
- Systems can subscribe/publish events

## Testing Strategy
1. **Unit tests**: Test individual systems with mock entities
2. **Integration tests**: Test system interactions
3. **Visual tests**: Run game, verify rendering
4. **Performance tests**: Spawn 100 entities, measure FPS

## Extensibility Examples
Adding a new enemy type:
1. Create factory function in `factory.py`
2. Add behavior type to AISystem
3. Define stats in `config.py`
4. Add to wave spawn pool

Adding a new component:
1. Define dataclass in `component.py`
2. Update relevant systems to query/process it
3. Add to entities via factory

Adding a new system:
1. Subclass GameSystem
2. Implement update(dt)
3. Register in game engine with appropriate priority

## Notes
- Turtle is single-threaded, so no concurrency needed
- All coordinates in turtle space (-400 to 400 default)
- Angles in degrees (turtle convention)
- Keep it simple first, optimize later
