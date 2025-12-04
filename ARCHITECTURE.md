# Advanced Turtle Arena Game Engine - Architecture Design

## Module Structure

```
game_engine/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── entity.py          # Entity ID and basic entity concept
│   ├── component.py       # Base Component class and all component dataclasses
│   ├── system.py          # Base GameSystem class
│   ├── entity_manager.py  # EntityManager: create/destroy entities, component management
│   ├── component_registry.py  # ComponentRegistry: fast component lookups
│   └── system_manager.py  # SystemManager: system registration and update ordering
├── systems/
│   ├── __init__.py
│   ├── physics_system.py  # Movement, velocity, friction, acceleration
│   ├── collision_system.py  # Broad-phase & narrow-phase collision detection
│   ├── render_system.py   # Turtle-based rendering
│   ├── ai_system.py       # AI decision-making (chase, turret, swarm, boss)
│   ├── weapon_system.py   # Weapon cooldowns, firing projectiles
│   ├── health_system.py   # Damage application, death/despawn
│   ├── wave_system.py     # Wave spawning, difficulty scaling
│   ├── pathfinding_system.py  # Grid-based A* pathfinding (optional)
│   ├── particle_system.py  # Visual effects (optional)
│   └── powerup_system.py  # Pickups and buffs (optional)
├── input/
│   ├── __init__.py
│   └── input_handler.py   # Input state management, key mapping
├── game/
│   ├── __init__.py
│   └── game_loop.py       # Main game loop, timing, orchestration
└── main.py                # Entry point

```

## Core Components (Data Classes)

### Transform
- `x, y`: Position
- `vx, vy`: Velocity
- `angle`: Rotation angle in degrees
- `angular_velocity`: Rotation speed

### Renderable
- `shape`: turtle shape name ("circle", "triangle", etc.)
- `color`: Color string or tuple
- `size`: Size multiplier
- `turtle_ref`: Reference to turtle object (managed by render system)

### Collider
- `radius`: Circular collision radius
- `mask`: Collision layer mask (what can collide with this)
- `tags`: Set of tags for filtering

### Physics
- `mass`: Mass value
- `friction`: Friction coefficient (0-1)
- `max_speed`: Maximum velocity magnitude
- `acceleration`: Acceleration rate

### Health
- `hp`: Current health points
- `max_hp`: Maximum health points
- `armor`: Damage reduction (0-1)

### Weapon
- `fire_rate`: Shots per second
- `damage`: Base damage per projectile
- `projectile_speed`: Speed of projectiles
- `spread`: Spread angle in degrees
- `bullet_count`: Number of bullets per shot
- `cooldown_remaining`: Time until next shot available
- `weapon_type`: "single", "shotgun", "burst", "beam"

### Projectile
- `owner_id`: Entity ID that fired this
- `damage`: Damage value
- `lifetime`: Total lifetime in seconds
- `time_alive`: Current age
- `piercing`: Can pierce through enemies
- `bounce`: Can bounce off walls

### AIBrain
- `behavior_type`: "chaser", "turret", "swarm", "boss"
- `state`: Current AI state string
- `target_id`: Entity ID to target (usually player)
- `awareness_range`: Detection range
- `attack_range`: Attack range
- `cooldowns`: Dict of cooldown timers
- `phase`: For boss enemies (phase number)

### Shield
- `hp`: Current shield points
- `max_hp`: Maximum shield points
- `recharge_rate`: HP per second when not taking damage
- `recharge_delay`: Seconds before recharge starts after taking damage
- `time_since_damage`: Timer for recharge delay

### StatusEffects
- `slow`: Slow multiplier (0-1)
- `slow_duration`: Remaining slow time
- `stun`: Stun timer
- `burn`: Burn damage per second
- `burn_duration`: Remaining burn time

### WaveInfo
- `current_wave`: Wave number
- `enemies_remaining`: Count of enemies left
- `difficulty_budget`: Current difficulty points available

## Systems

### PhysicsSystem
- Updates Transform based on velocity
- Applies friction
- Enforces max_speed
- Updates angular velocity

### CollisionSystem
- Broad-phase: spatial grid or simple distance checks
- Narrow-phase: circle-circle collision detection
- Resolves collisions (push apart, trigger events)
- Handles projectile collisions

### RenderSystem
- Manages turtle objects (pooling/reuse)
- Draws all Renderable entities
- Handles screen clearing and updates
- Draws static elements (arena, grid)

### AISystem
- Chaser: moves toward target
- Turret: rotates to face target, fires when in range
- Swarm: boids behavior (cohesion, separation, alignment)
- Boss: multi-phase state machine

### WeaponSystem
- Updates weapon cooldowns
- Handles firing logic
- Spawns projectiles
- Manages projectile lifetime

### HealthSystem
- Applies damage from collisions
- Handles shield absorption
- Manages death/despawn
- Applies status effects

### WaveSystem
- Tracks wave progression
- Spawns enemies based on difficulty budget
- Scales difficulty
- Triggers wave completion events

### PathfindingSystem (Optional)
- Grid-based A* pathfinding
- Precomputes paths
- Updates entity movement targets

## Managers

### EntityManager
- Creates entities (returns UUID)
- Destroys entities (deferred to end of frame)
- Adds/removes components
- Queries entities by component signature

### ComponentRegistry
- Indexes entities by component type
- Fast lookups: "get all entities with Transform and Health"
- Maintains component arrays for cache-friendly iteration

### SystemManager
- Registers systems with priorities
- Calls update(dt) in priority order
- Manages system lifecycle

## Input Handling

### InputState
- Maps raw keys to actions
- Tracks current frame input state
- Provides action queries (is_pressed, was_pressed_this_frame)

## Game Loop

1. Initialize turtle screen
2. Create managers and systems
3. Spawn initial entities (player, arena)
4. Main loop:
   - Poll input
   - Update systems in order
   - Flush entity destruction
   - Render frame
   - Sleep for FPS cap

## Design Principles

1. **Composition over Inheritance**: Entities are bags of components
2. **Data-Oriented**: Components are pure data, systems operate on arrays
3. **System-Driven**: Behavior lives in systems, not entities
4. **Separation of Concerns**: Each system has one responsibility
5. **Extensibility**: Easy to add new components/systems without modifying existing code
