# Robo-Arena: Advanced Turtle Arena Game Engine

A modern 2D top-down arena shooter built on Python's turtle graphics library, featuring a full Entity-Component-System (ECS) architecture with data-oriented design principles.

## 🎮 Quick Start

```bash
python run_game.py
```

### Controls

| Key | Action |
|-----|--------|
| W | Move Up |
| A | Move Left |
| S | Move Down |
| D | Move Right |
| Arrow Keys | Aim Direction |
| Mouse | Aim Direction (alternative) |
| Space / Click | Fire |
| R | Reload |
| Escape | Pause Menu |
| Q | Quit |

### Movement System
- **WASD**: Omnidirectional movement - move in any direction regardless of facing
- **Arrow Keys or Mouse**: Controls aim/facing direction independently from movement
- This twin-stick style control allows strafing while shooting in any direction!

## 🏗️ Architecture Overview

This project implements a **mini game engine** on top of Python's turtle library, following modern game engine architecture patterns similar to Unity, Unreal, and Godot.

### Core Design Principles

1. **Entity-Component-System (ECS)**: Entities are lightweight IDs, components are pure data, systems contain all logic
2. **Data-Oriented Design**: Components stored in centralized registries for cache-friendly iteration
3. **Composition over Inheritance**: Entities built from components, not class hierarchies
4. **System-Driven Behavior**: All game logic lives in systems, not in entity classes
5. **Event-Driven Communication**: Systems communicate via events, not direct calls

## 📁 Project Structure

```
/workspace/
├── engine/                    # Core game engine
│   ├── core/                  # ECS primitives
│   │   ├── entity.py         # Entity & EntityManager
│   │   ├── component.py      # ComponentRegistry
│   │   ├── system.py         # GameSystem & SystemManager
│   │   └── events.py         # EventBus & built-in events
│   ├── components/           # Component definitions (pure data)
│   │   ├── transform.py      # Position, rotation, scale
│   │   ├── physics.py        # Velocity, mass, friction
│   │   ├── renderable.py     # Visual representation
│   │   ├── collider.py       # Collision shapes and masks
│   │   ├── health.py         # HP, shields
│   │   ├── weapon.py         # Weapons, projectiles
│   │   ├── ai.py             # AI behavior configuration
│   │   ├── status.py         # Status effects (buffs/debuffs)
│   │   ├── tags.py           # Marker components
│   │   └── upgrades.py       # Permanent upgrade system (NEW)
│   ├── systems/              # Game logic systems
│   │   ├── physics_system.py    # Movement, forces, bounds
│   │   ├── collision_system.py  # Spatial partitioning, detection
│   │   ├── render_system.py     # Turtle graphics rendering
│   │   ├── input_system.py      # Keyboard/mouse input + aiming
│   │   ├── ai_system.py         # Enemy AI behaviors
│   │   ├── weapon_system.py     # Firing, projectiles
│   │   ├── health_system.py     # Damage, death, shields, evasion
│   │   ├── wave_system.py       # Wave spawning, difficulty
│   │   ├── status_system.py     # Status effect processing
│   │   ├── pathfinding_system.py # A* grid pathfinding
│   │   └── upgrade_system.py    # Upgrade processing (NEW)
│   ├── input/                # Input handling module
│   ├── menu.py               # Advanced menu system (NEW)
│   └── game_loop.py          # Main engine orchestrator
├── game/                     # Game implementation
│   ├── config.py             # Game configuration
│   ├── prefabs.py            # Entity factory functions
│   └── main.py               # Game entry point
└── run_game.py               # Launcher script
```

## 🧩 Engine Components

### Core ECS

#### Entity
```python
from engine.core import Entity, EntityManager

# Entities are lightweight IDs
entity = entity_manager.create_entity(name="player")

# Add components to build entity behavior
entity_manager.add_component(entity, Transform(x=0, y=0))
entity_manager.add_component(entity, Velocity())
entity_manager.add_component(entity, Health(hp=100))
```

#### Components
Components are pure data structures using `@dataclass`:

```python
@dataclass
class Transform:
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0
    scale: float = 1.0
```

#### Systems
Systems process entities with specific component signatures:

```python
class PhysicsSystem(GameSystem):
    def __init__(self):
        super().__init__(priority=SystemPriority.PHYSICS)
    
    def update(self, dt: float):
        for entity in self.entities.get_entities_with(Transform, Velocity):
            transform = self.entities.get_component(entity, Transform)
            velocity = self.entities.get_component(entity, Velocity)
            
            transform.x += velocity.vx * dt
            transform.y += velocity.vy * dt
```

### Systems Overview

| System | Priority | Description |
|--------|----------|-------------|
| InputSystem | 0 | Keyboard/mouse input, WASD movement + aim |
| UpgradeSystem | 50 | Upgrade effects, pickups, degradation |
| PathfindingSystem | 99 | A* pathfinding grid |
| AISystem | 100 | Enemy behavior logic |
| PhysicsSystem | 200 | Movement, forces, bounds |
| WeaponSystem | 300 | Firing, cooldowns, multishot |
| CollisionSystem | 400 | Spatial partitioning, detection |
| HealthSystem | 600 | Damage, shields, death, evasion, lifesteal |
| WaveSystem | 700 | Enemy wave spawning |
| StatusEffectSystem | 800 | Buff/debuff processing |
| RenderSystem | 1000 | Turtle graphics rendering |

### Event System

Systems communicate via events without direct dependencies:

```python
# Subscribe to events
event_bus.subscribe(CollisionEvent, self.on_collision)

# Emit events
event_bus.emit(DamageEvent(
    target_id=entity.id,
    source_id=attacker.id,
    amount=25.0
))
```

Built-in events:
- `CollisionEvent` - Two entities collided
- `DamageEvent` - Damage should be applied
- `DeathEvent` - Entity died
- `WaveStartEvent` / `WaveCompleteEvent` - Wave lifecycle
- `GameStateEvent` - State changes (pause, game over, victory)

## 🎯 Game Features

### Enemy Types

| Enemy | Behavior | Description |
|-------|----------|-------------|
| Chaser | CHASER | Rushes directly at player |
| Turret | TURRET | Stationary, rotates and shoots |
| Swarm | SWARM | Flocking behavior (boids) |
| Orbiter | ORBIT | Circles player while shooting |
| Boss | BOSS | Multi-phase state machine |

### Combat System

- **Weapons**: Single shot, shotgun, burst, rapid fire, rocket
- **Projectiles**: Lifetime, piercing, bouncing, explosive
- **Health/Shields**: Shield absorbs damage, regenerates after delay
- **Status Effects**: Slow, stun, burn, poison, freeze, buffs

### 🆙 Permanent Active Upgrade System

A comprehensive upgrade system inspired by modern roguelite games:

#### Design Philosophy
- **Always Active**: Every upgrade affects gameplay every frame
- **Stackable**: Pick up 5 "Damage+" upgrades = 5 stacks with cumulative effects
- **Degradation**: Take damage → 50% chance to lose 1 random upgrade stack
- **Risk/Reward**: Powerful upgrades encourage careful play to maintain stacks

#### Upgrade Tiers

| Tier | Rarity | Examples |
|------|--------|----------|
| **Tier 1** | Very Common (1-2 kills) | Damage+, Fire Rate+, Speed+, HP+ |
| **Tier 2** | Common (3-5 kills) | Critical Chance, Armor, Multishot, Shield Regen |
| **Tier 3** | Uncommon (8-15 kills) | Piercing, Ricochet, Lifesteal, Regeneration |
| **Tier 4** | Rare (Boss/Special) | Dash, Slow Aura, Crit Multiplier, Homing |
| **Tier 5** | Epic (Boss Only) | Berserk Mode, Time Dilation, Ally Drone |

#### 31 Unique Upgrades Including:
- **Offensive**: Damage+, Fire Rate+, Critical Chance, Multishot, Piercing, Explosive Impact
- **Defensive**: HP+, Armor, Shield Regen, Evasion, Mana Shield
- **Utility**: Speed+, Dash, Lifesteal, Regeneration, Probability Field
- **Special**: Berserk Mode, Time Dilation, Ally Drone, Feedback Loop

#### Synergy Examples
- Damage+ × 5 + Crit Mult × 3 = Massive burst damage
- Fire Rate+ × 8 + Multishot × 4 = Bullet hell fantasy
- Piercing × 5 + Ricochet × 4 = Screen-clearing projectiles
- Armor × 8 + Regen × 5 = Unkillable tank build

### Wave System

- Budget-based enemy spawning
- Difficulty scaling per wave
- Boss waves every 5 waves
- Upgrade drops scale with wave number
- Configurable enemy costs and weights

### Menu System

- **Main Menu**: Start Game, Quit buttons with keyboard/mouse navigation
- **Pause Menu**: Resume, Restart, Quit (press ESC during gameplay)
- **Game Over**: Shows score, wave reached, and kill count
- **Victory Screen**: Final stats and replay option
- **Proper Quit**: X button and Quit button properly close the game

## 🔧 Extending the Engine

### Adding a New Component

```python
# engine/components/my_component.py
from dataclasses import dataclass

@dataclass
class MyComponent:
    value: float = 0.0
    enabled: bool = True
```

### Adding a New System

```python
# engine/systems/my_system.py
from engine.core.system import GameSystem, SystemPriority

class MySystem(GameSystem):
    def __init__(self):
        super().__init__(priority=SystemPriority.PHYSICS + 50)
    
    def initialize(self):
        # One-time setup
        pass
    
    def update(self, dt: float):
        for entity in self.entities.get_entities_with(MyComponent):
            component = self.entities.get_component(entity, MyComponent)
            # Process component
```

### Adding a New Enemy Type

```python
# In wave_system.py or custom file
self.register_enemy_type(EnemySpawnConfig(
    name="my_enemy",
    cost=2.0,
    spawn_fn=self._spawn_my_enemy,
    min_wave=3,
    weight=1.0
))
```

## 🚀 Performance Considerations

### Current Optimizations

1. **Spatial Partitioning**: CollisionSystem uses a grid for broad-phase
2. **Component Indexing**: EntityManager maintains reverse indices for fast queries
3. **Object Pooling**: Turtle objects are recycled for projectiles
4. **Deferred Destruction**: Entities destroyed at frame end to prevent iterator invalidation

### Potential Improvements

For larger games, consider:

1. **Structure of Arrays (SoA)**: Store component data in contiguous arrays
2. **Archetypes**: Group entities by component signature for better cache locality  
3. **Spatial Hashing**: Replace grid with hash-based spatial partitioning
4. **Component Pooling**: Expand pooling to all frequently-created components
5. **Batch Rendering**: Group similar entities for batch draw calls

## 📋 Requirements

- Python 3.10+
- turtle (built-in)

No external dependencies required!

## 📄 License

MIT License - Feel free to use, modify, and extend!

---

Built with ❤️ as a demonstration of modern game architecture in Python.
