"""
Wave System - Enemy wave management and difficulty scaling.

Handles spawning waves of enemies with increasing difficulty,
and manages wave-based progression.

Enemy Design Philosophy:
- Each enemy teaches the player something different
- Archetypes: Near (melee), Far (ranged), Swarmer (fast/fragile), Heavy (slow/tanky), Specialist (unique mechanic)
- Color coded by type: blue=swarmer, green=scout, red=heavy, purple=specialist, orange=elite
"""

from __future__ import annotations
import math
import random
from typing import TYPE_CHECKING, Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum, auto

from ..core.system import GameSystem, SystemPriority
from ..core.events import WaveStartEvent, WaveCompleteEvent, DeathEvent, GameStateEvent
from ..components.transform import Transform
from ..components.physics import Physics, Velocity
from ..components.renderable import Renderable, RenderShape, RenderLayer
from ..components.collider import Collider, ColliderType, CollisionMask
from ..components.health import Health, Shield
from ..components.weapon import Weapon, WeaponType
from ..components.ai import AIBrain, AIBehavior, AIState
from ..components.tags import EnemyTag, BossTag

if TYPE_CHECKING:
    from ..core.entity import Entity


class WaveState(Enum):
    """Current state of the wave system."""
    WAITING = auto()      # Before first wave
    SPAWNING = auto()     # Spawning enemies
    ACTIVE = auto()       # Wave in progress
    COMPLETE = auto()     # Wave cleared, awaiting next
    BOSS_WAVE = auto()    # Boss wave active
    GAME_OVER = auto()    # Player died
    VICTORY = auto()      # All waves completed


class EnemyTier(Enum):
    """Enemy difficulty tier."""
    STARTER = 1      # Waves 1-3
    INTERMEDIATE = 2  # Waves 4-7
    ADVANCED = 3     # Waves 8-12
    ELITE = 4        # Waves 13+


@dataclass
class EnemySpawnConfig:
    """Configuration for spawning an enemy type."""
    name: str
    cost: float  # Budget cost
    spawn_fn: Callable[["WaveSystem", float, float], "Entity"]
    min_wave: int = 1  # First wave this enemy can appear
    max_per_wave: int = 10  # Maximum of this type per wave
    weight: float = 1.0  # Spawn probability weight
    tier: EnemyTier = EnemyTier.STARTER


@dataclass 
class WaveConfig:
    """Configuration for a specific wave."""
    wave_number: int
    budget: float
    spawn_delay: float = 0.5  # Delay between spawns
    is_boss_wave: bool = False
    boss_type: Optional[str] = None
    special_rules: Dict = None


class WaveSystem(GameSystem):
    """
    Manages enemy waves and difficulty progression.
    
    Features:
    - Budget-based enemy spawning with procedural variety
    - Difficulty scaling per wave
    - 16+ enemy types organized by tier
    - Multiple boss types with phase mechanics
    - Wave completion detection
    - Dynamic difficulty adaptation
    - Special events
    """
    
    def __init__(
        self,
        arena_width: float = 800,
        arena_height: float = 600,
        start_budget: float = 5.0,
        budget_per_wave: float = 3.0,
        max_waves: int = 20  # Extended to 20 waves
    ):
        super().__init__(priority=SystemPriority.WAVE)
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.start_budget = start_budget
        self.budget_per_wave = budget_per_wave
        self.max_waves = max_waves
        
        # Wave state
        self.current_wave = 0
        self.state = WaveState.WAITING
        self.enemies_remaining = 0
        self.wave_timer = 0.0
        self.spawn_timer = 0.0
        self.spawn_queue: List[EnemySpawnConfig] = []
        
        # Timing
        self.wave_delay = 3.0  # Delay between waves
        self.spawn_delay = 0.5  # Delay between spawns
        
        # Enemy configurations
        self.enemy_configs: Dict[str, EnemySpawnConfig] = {}
        self._register_all_enemies()
        
        # Score tracking
        self.score = 0
        self.kills = 0
        
        # Dynamic difficulty
        self.difficulty_modifier = 1.0
        self.player_performance_score = 0.0  # Track how well player is doing
        
        # Special events
        self.event_active = False
        self.event_type = ""
        self.event_timer = 0.0
    
    def initialize(self) -> None:
        """Set up wave system."""
        # Subscribe to death events to track enemy kills
        self.events.subscribe(DeathEvent, self._on_enemy_death)
    
    def _register_all_enemies(self) -> None:
        """Register all enemy types organized by tier."""
        # ========== TIER 1: STARTER ENEMIES (Waves 1-3) ==========
        
        # Drone - Basic swarmer, fast, direct rush
        self.register_enemy_type(EnemySpawnConfig(
            name="drone",
            cost=1.0,
            spawn_fn=self._spawn_drone,
            min_wave=1,
            max_per_wave=12,
            weight=2.5,
            tier=EnemyTier.STARTER
        ))
        
        # Scout - Ranged, strafes while shooting
        self.register_enemy_type(EnemySpawnConfig(
            name="scout",
            cost=1.5,
            spawn_fn=self._spawn_scout,
            min_wave=1,
            max_per_wave=6,
            weight=1.5,
            tier=EnemyTier.STARTER
        ))
        
        # Bruiser - Slow, tanky, rams player
        self.register_enemy_type(EnemySpawnConfig(
            name="bruiser",
            cost=2.5,
            spawn_fn=self._spawn_bruiser,
            min_wave=2,
            max_per_wave=4,
            weight=1.0,
            tier=EnemyTier.STARTER
        ))
        
        # Turret - Stationary, rotates and shoots
        self.register_enemy_type(EnemySpawnConfig(
            name="turret",
            cost=2.0,
            spawn_fn=self._spawn_turret,
            min_wave=2,
            max_per_wave=3,
            weight=1.0,
            tier=EnemyTier.STARTER
        ))
        
        # ========== TIER 2: INTERMEDIATE ENEMIES (Waves 4-7) ==========
        
        # Ricochet - Fires bouncing projectiles
        self.register_enemy_type(EnemySpawnConfig(
            name="ricochet",
            cost=2.5,
            spawn_fn=self._spawn_ricochet,
            min_wave=4,
            max_per_wave=4,
            weight=1.0,
            tier=EnemyTier.INTERMEDIATE
        ))
        
        # Orbiter - Circles player, periodic burst shots
        self.register_enemy_type(EnemySpawnConfig(
            name="orbiter",
            cost=2.5,
            spawn_fn=self._spawn_orbiter,
            min_wave=4,
            max_per_wave=5,
            weight=1.2,
            tier=EnemyTier.INTERMEDIATE
        ))
        
        # Shielder - Has front shield, regenerates
        self.register_enemy_type(EnemySpawnConfig(
            name="shielder",
            cost=3.5,
            spawn_fn=self._spawn_shielder,
            min_wave=5,
            max_per_wave=3,
            weight=0.8,
            tier=EnemyTier.INTERMEDIATE
        ))
        
        # Divider - Splits into smaller versions when killed
        self.register_enemy_type(EnemySpawnConfig(
            name="divider",
            cost=2.0,
            spawn_fn=self._spawn_divider,
            min_wave=5,
            max_per_wave=4,
            weight=1.0,
            tier=EnemyTier.INTERMEDIATE
        ))
        
        # Charger - Fast charge in straight line
        self.register_enemy_type(EnemySpawnConfig(
            name="charger",
            cost=2.0,
            spawn_fn=self._spawn_charger,
            min_wave=4,
            max_per_wave=4,
            weight=1.2,
            tier=EnemyTier.INTERMEDIATE
        ))
        
        # Phantom - Becomes invisible, shoots from hidden
        self.register_enemy_type(EnemySpawnConfig(
            name="phantom",
            cost=3.0,
            spawn_fn=self._spawn_phantom,
            min_wave=6,
            max_per_wave=3,
            weight=0.8,
            tier=EnemyTier.INTERMEDIATE
        ))
        
        # ========== TIER 3: ADVANCED ENEMIES (Waves 8-12) ==========
        
        # Mimic - Copies player's weapon
        self.register_enemy_type(EnemySpawnConfig(
            name="mimic",
            cost=4.0,
            spawn_fn=self._spawn_mimic,
            min_wave=8,
            max_per_wave=2,
            weight=0.7,
            tier=EnemyTier.ADVANCED
        ))
        
        # Hive - Spawns small drones
        self.register_enemy_type(EnemySpawnConfig(
            name="hive",
            cost=5.0,
            spawn_fn=self._spawn_hive,
            min_wave=8,
            max_per_wave=2,
            weight=0.6,
            tier=EnemyTier.ADVANCED
        ))
        
        # Stalker - Teleports when player gets close
        self.register_enemy_type(EnemySpawnConfig(
            name="stalker",
            cost=3.5,
            spawn_fn=self._spawn_stalker,
            min_wave=9,
            max_per_wave=3,
            weight=0.8,
            tier=EnemyTier.ADVANCED
        ))
        
        # Splicer - Projectiles split mid-flight
        self.register_enemy_type(EnemySpawnConfig(
            name="splicer",
            cost=3.0,
            spawn_fn=self._spawn_splicer,
            min_wave=9,
            max_per_wave=3,
            weight=0.9,
            tier=EnemyTier.ADVANCED
        ))
        
        # ========== TIER 4: ELITE/BOSS-ADJACENT (Waves 13+) ==========
        
        # Sentinel - 3-phase enemy (slow march → burst fire → fast + AoE)
        self.register_enemy_type(EnemySpawnConfig(
            name="sentinel",
            cost=6.0,
            spawn_fn=self._spawn_sentinel,
            min_wave=13,
            max_per_wave=2,
            weight=0.5,
            tier=EnemyTier.ELITE
        ))
        
        # Sovereign - Commands and buffs nearby enemies
        self.register_enemy_type(EnemySpawnConfig(
            name="sovereign",
            cost=5.0,
            spawn_fn=self._spawn_sovereign,
            min_wave=13,
            max_per_wave=1,
            weight=0.4,
            tier=EnemyTier.ELITE
        ))
        
        # Executor - Ultra-fast, stuns on hit
        self.register_enemy_type(EnemySpawnConfig(
            name="executor",
            cost=4.5,
            spawn_fn=self._spawn_executor,
            min_wave=14,
            max_per_wave=2,
            weight=0.6,
            tier=EnemyTier.ELITE
        ))
        
        # Legacy enemy names for compatibility
        self.register_enemy_type(EnemySpawnConfig(
            name="chaser",
            cost=1.0,
            spawn_fn=self._spawn_drone,  # Alias to drone
            min_wave=1,
            weight=2.0,
            tier=EnemyTier.STARTER
        ))
        
        self.register_enemy_type(EnemySpawnConfig(
            name="swarm",
            cost=0.5,
            spawn_fn=self._spawn_swarm,
            min_wave=3,
            max_per_wave=15,
            weight=1.5,
            tier=EnemyTier.STARTER
        ))
    
    def register_enemy_type(self, config: EnemySpawnConfig) -> None:
        """Register an enemy type for spawning."""
        self.enemy_configs[config.name] = config
    
    def _on_enemy_death(self, event: DeathEvent) -> None:
        """Handle enemy death."""
        if not event or not event.entity_id:
            return
            
        # Use safe entity lookup
        entity = self.entities.get_entity_by_id(event.entity_id)
        if not entity:
            return
        
        enemy_tag = self.entities.get_component(entity, EnemyTag)
        if enemy_tag:
            self.enemies_remaining = max(0, self.enemies_remaining - 1)
            self.kills += 1
            # Validate point value
            if isinstance(enemy_tag.point_value, (int, float)) and enemy_tag.point_value > 0:
                self.score += int(enemy_tag.point_value)
    
    def update(self, dt: float) -> None:
        """Update wave state."""
        # Update special events
        self._update_special_events(dt)
        
        # Update spawner enemies (hives)
        self._update_spawner_enemies(dt)
        
        if self.state == WaveState.WAITING:
            # Start first wave after delay
            self.wave_timer += dt
            if self.wave_timer >= self.wave_delay:
                self._start_next_wave()
        
        elif self.state == WaveState.SPAWNING:
            self._process_spawning(dt)
        
        elif self.state == WaveState.ACTIVE or self.state == WaveState.BOSS_WAVE:
            # Check if wave is complete
            if self.enemies_remaining <= 0:
                self._complete_wave()
        
        elif self.state == WaveState.COMPLETE:
            self.wave_timer += dt
            if self.wave_timer >= self.wave_delay:
                if self.current_wave >= self.max_waves:
                    self.state = WaveState.VICTORY
                    self.events.emit(GameStateEvent(state="victory"))
                else:
                    self._start_next_wave()
    
    def _update_special_events(self, dt: float) -> None:
        """Update special event state."""
        if self.event_active:
            self.event_timer -= dt
            if self.event_timer <= 0:
                self._end_special_event()
        
        # Chance to trigger event every few waves
        if self.state == WaveState.ACTIVE and not self.event_active:
            if self.current_wave >= 3 and self.current_wave % 2 == 0:
                if random.random() < 0.15:  # 15% chance per applicable wave
                    self._trigger_special_event()
    
    def _trigger_special_event(self) -> None:
        """Trigger a random special event."""
        events = [
            ("energy_surge", 15.0),    # All upgrades +50% effectiveness
            ("gold_rush", 20.0),       # 3x drop rate
            ("enemy_mutation", 25.0),  # Random enemy becomes corrupted
        ]
        
        event_type, duration = random.choice(events)
        self.event_active = True
        self.event_type = event_type
        self.event_timer = duration
        
        # Apply event effects
        if event_type == "enemy_mutation":
            self._mutate_random_enemy()
    
    def _end_special_event(self) -> None:
        """End the current special event."""
        self.event_active = False
        self.event_type = ""
    
    def _mutate_random_enemy(self) -> None:
        """Make a random enemy into a 'corrupted' variant with 2x stats."""
        try:
            enemies = list(self.entities.get_entities_with(EnemyTag))
            if enemies:
                target = random.choice(enemies)
                health = self.entities.get_component(target, Health)
                renderable = self.entities.get_component(target, Renderable)
                
                if health:
                    health.hp *= 2
                    health.max_hp *= 2
                
                if renderable:
                    renderable.color = "#ff0044"  # Red corruption
                    renderable.outline_color = "#880022"
                    renderable.glow = True
                    renderable.pulse_speed = 3.0
        except Exception:
            pass
    
    def _update_spawner_enemies(self, dt: float) -> None:
        """Update hive/spawner enemies to spawn drones."""
        try:
            for entity in self.entities.get_entities_with(EnemyTag):
                if not self.entities.is_alive(entity):
                    continue
                
                if not self.entities.has_tag(entity, "spawner"):
                    continue
                
                # Get AI brain for timer
                brain = self.entities.get_component(entity, AIBrain)
                transform = self.entities.get_component(entity, Transform)
                
                if not brain or not transform:
                    continue
                
                # Use state_timer as spawn timer
                brain.state_timer += dt
                
                # Spawn every 3 seconds
                if brain.state_timer >= 3.0:
                    brain.state_timer = 0.0
                    
                    # Spawn 2-3 small drones near the hive
                    spawn_count = random.randint(2, 3)
                    for _ in range(spawn_count):
                        offset_x = random.uniform(-30, 30)
                        offset_y = random.uniform(-30, 30)
                        self._spawn_swarm(transform.x + offset_x, transform.y + offset_y)
                        self.enemies_remaining += 1
        except Exception:
            pass
    
    def _adapt_difficulty(self) -> None:
        """Adapt difficulty based on player performance."""
        # Track performance metrics
        # If player is winning easily: increase difficulty
        # If player is struggling: decrease difficulty
        
        # Simple implementation: based on health percentage
        player = self.entities.get_named("player")
        if player:
            health = self.entities.get_component(player, Health)
            if health:
                hp_percent = health.health_percent
                
                if hp_percent > 0.8:  # Player is doing great
                    self.difficulty_modifier = min(1.5, self.difficulty_modifier + 0.05)
                elif hp_percent < 0.3:  # Player is struggling
                    self.difficulty_modifier = max(0.7, self.difficulty_modifier - 0.05)
    
    def get_difficulty_modifier(self) -> float:
        """Get current difficulty modifier for scaling."""
        return self.difficulty_modifier
    
    def _start_next_wave(self) -> None:
        """Start the next wave."""
        self.current_wave += 1
        self.wave_timer = 0.0
        self.spawn_timer = 0.0
        
        # Check for boss wave (every 5 waves)
        is_boss = self.current_wave % 5 == 0
        
        # Calculate budget
        budget = self.start_budget + (self.current_wave - 1) * self.budget_per_wave
        
        if is_boss:
            self.state = WaveState.BOSS_WAVE
            self._spawn_boss()
        else:
            self.state = WaveState.SPAWNING
            self._generate_spawn_queue(budget)
        
        self.events.emit(WaveStartEvent(
            wave_number=self.current_wave,
            enemy_count=len(self.spawn_queue)
        ))
    
    def _generate_spawn_queue(self, budget: float) -> None:
        """Generate the spawn queue for a wave."""
        self.spawn_queue.clear()
        remaining_budget = budget
        spawn_counts: Dict[str, int] = {}
        
        # Get eligible enemies for this wave
        eligible = [
            config for config in self.enemy_configs.values()
            if config.min_wave <= self.current_wave
        ]
        
        if not eligible:
            return
        
        # Fill spawn queue
        while remaining_budget > 0:
            # Weight-based random selection
            total_weight = sum(c.weight for c in eligible 
                             if spawn_counts.get(c.name, 0) < c.max_per_wave
                             and c.cost <= remaining_budget)
            
            if total_weight <= 0:
                break
            
            roll = random.uniform(0, total_weight)
            cumulative = 0
            selected = None
            
            for config in eligible:
                if (spawn_counts.get(config.name, 0) >= config.max_per_wave or
                    config.cost > remaining_budget):
                    continue
                cumulative += config.weight
                if roll <= cumulative:
                    selected = config
                    break
            
            if selected:
                self.spawn_queue.append(selected)
                remaining_budget -= selected.cost
                spawn_counts[selected.name] = spawn_counts.get(selected.name, 0) + 1
            else:
                break
        
        self.enemies_remaining = len(self.spawn_queue)
    
    def _process_spawning(self, dt: float) -> None:
        """Spawn enemies from queue."""
        self.spawn_timer += dt
        
        if self.spawn_timer >= self.spawn_delay and self.spawn_queue:
            self.spawn_timer = 0.0
            config = self.spawn_queue.pop(0)
            
            try:
                # Find spawn position
                x, y = self._get_spawn_position()
                
                # Validate spawn position
                import math
                if not math.isfinite(x) or not math.isfinite(y):
                    x, y = 0.0, self.arena_height / 2 - 50
                
                # Spawn enemy (spawn_fn is already a bound method, so don't pass self)
                if config.spawn_fn:
                    config.spawn_fn(x, y)
            except Exception as e:
                # Log error but continue spawning
                import sys
                print(f"[WaveSystem] Error spawning enemy: {e}", file=sys.stderr)
        
        if not self.spawn_queue:
            self.state = WaveState.ACTIVE
    
    def _get_spawn_position(self) -> tuple[float, float]:
        """Get a random spawn position on the arena edge."""
        hw = self.arena_width / 2 - 30
        hh = self.arena_height / 2 - 30
        
        side = random.randint(0, 3)
        if side == 0:  # Top
            return (random.uniform(-hw, hw), hh)
        elif side == 1:  # Bottom
            return (random.uniform(-hw, hw), -hh)
        elif side == 2:  # Left
            return (-hw, random.uniform(-hh, hh))
        else:  # Right
            return (hw, random.uniform(-hh, hh))
    
    def _complete_wave(self) -> None:
        """Handle wave completion."""
        self.state = WaveState.COMPLETE
        self.wave_timer = 0.0
        
        self.events.emit(WaveCompleteEvent(wave_number=self.current_wave))
        self.events.emit(GameStateEvent(state="wave_complete"))
    
    # ========== ENEMY SPAWN FUNCTIONS ==========
    
    # ----- TIER 1: STARTER ENEMIES -----
    
    def _spawn_drone(self, x: float, y: float) -> Entity:
        """Spawn a Drone enemy - basic swarmer, fast, direct rush toward player."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.05
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=180.0 * wave_scale,
            acceleration=400.0,
            friction=0.1,
            drag=0.95
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.TRIANGLE,
            color="#4488ff",  # Blue = swarmer
            outline_color="#2266cc",
            size=0.6,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=10.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=5.0 + self.current_wave * 3,
            max_hp=5.0 + self.current_wave * 3
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.CHASER,
            awareness_range=500.0,
            attack_range=25.0,
            speed_multiplier=wave_scale
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="drone",
            wave_spawned=self.current_wave,
            point_value=50
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    def _spawn_scout(self, x: float, y: float) -> Entity:
        """Spawn a Scout enemy - strafes while shooting, medium distance."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.04
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=150.0 * wave_scale,
            acceleration=300.0,
            friction=0.08,
            drag=0.96
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.TRIANGLE,
            color="#44ff44",  # Green = scout/ranged
            outline_color="#22aa22",
            size=0.7,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=11.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=8.0 + self.current_wave * 4,
            max_hp=8.0 + self.current_wave * 4
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SINGLE,
            damage=5.0,
            fire_rate=1.5,
            projectile_speed=280.0,
            projectile_color="#66ff66"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.ORBIT,
            awareness_range=400.0,
            attack_range=300.0,
            preferred_range=200.0,
            attack_cooldown=0.7,
            turn_speed=150.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="scout",
            wave_spawned=self.current_wave,
            point_value=100
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    def _spawn_bruiser(self, x: float, y: float) -> Entity:
        """Spawn a Bruiser enemy - slow, tanky, rams player for high damage."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.06
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=80.0 * wave_scale,
            acceleration=150.0,
            friction=0.15,
            drag=0.92
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.SQUARE,
            color="#ff4444",  # Red = heavy/bruiser
            outline_color="#aa0000",
            size=1.2,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=18.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=15.0 + self.current_wave * 8,
            max_hp=15.0 + self.current_wave * 8,
            armor=0.2
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.CHASER,
            awareness_range=400.0,
            attack_range=35.0,
            speed_multiplier=wave_scale * 0.8,
            turn_speed=60.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="bruiser",
            wave_spawned=self.current_wave,
            point_value=150
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    def _spawn_turret(self, x: float, y: float) -> Entity:
        """Spawn a Turret enemy - stationary, rotates to track, high fire rate."""
        entity = self.entities.create_entity()
        
        self.entities.add_component(entity, Transform(x=x, y=y))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(is_kinematic=True))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.SQUARE,
            color="#44ffff",  # Cyan = turret
            outline_color="#00aaaa",
            size=0.9,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=14.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.PLAYER_PROJECTILE,
            is_static=True
        ))
        self.entities.add_component(entity, Health(
            hp=12.0 + self.current_wave * 6,
            max_hp=12.0 + self.current_wave * 6,
            armor=0.1
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SINGLE,
            damage=4.0,
            fire_rate=2.5 + self.current_wave * 0.15,
            projectile_speed=350.0,
            projectile_color="#88ffff"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.TURRET,
            awareness_range=350.0,
            attack_range=320.0,
            attack_cooldown=0.4,
            turn_speed=120.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="turret",
            wave_spawned=self.current_wave,
            point_value=120
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    def _spawn_swarm(self, x: float, y: float) -> Entity:
        """Spawn a swarm enemy - small, fast, uses boids behavior."""
        entity = self.entities.create_entity()
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=200.0,
            acceleration=450.0,
            friction=0.05,
            drag=0.98
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.CIRCLE,
            color="#88ff88",
            outline_color="#44aa44",
            size=0.4,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=6.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=3.0 + self.current_wave * 1.5,
            max_hp=3.0 + self.current_wave * 1.5
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.SWARM,
            awareness_range=400.0,
            attack_range=20.0,
            separation_distance=25.0,
            neighbor_distance=70.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="swarm",
            wave_spawned=self.current_wave,
            point_value=30
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    # ----- TIER 2: INTERMEDIATE ENEMIES -----
    
    def _spawn_ricochet(self, x: float, y: float) -> Entity:
        """Spawn a Ricochet enemy - fires bouncing projectiles."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.04
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=120.0 * wave_scale,
            acceleration=250.0,
            friction=0.1,
            drag=0.95
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.DIAMOND,
            color="#ff8800",  # Orange = special
            outline_color="#cc6600",
            size=0.8,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=12.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=10.0 + self.current_wave * 5,
            max_hp=10.0 + self.current_wave * 5
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SINGLE,
            damage=4.0,
            fire_rate=1.2,
            projectile_speed=250.0,
            projectile_color="#ffaa44"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.ORBIT,
            awareness_range=400.0,
            attack_range=350.0,
            preferred_range=250.0,
            attack_cooldown=0.8,
            turn_speed=100.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="ricochet",
            wave_spawned=self.current_wave,
            point_value=180
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    def _spawn_orbiter(self, x: float, y: float) -> Entity:
        """Spawn an Orbiter enemy - circles player, periodic burst shots."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.04
        
        self.entities.add_component(entity, Transform(x=x, y=y))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=180.0 * wave_scale,
            acceleration=350.0,
            friction=0.08,
            drag=0.96
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.CIRCLE,
            color="#ff44ff",  # Purple = specialist
            outline_color="#aa00aa",
            size=0.7,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=10.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=6.0 + self.current_wave * 4,
            max_hp=6.0 + self.current_wave * 4
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.BURST,
            damage=3.0,
            fire_rate=2.5,
            projectile_speed=300.0,
            projectile_color="#ff88ff",
            burst_count=3,
            burst_delay=0.08
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.ORBIT,
            awareness_range=450.0,
            attack_range=300.0,
            preferred_range=150.0,
            attack_cooldown=1.5,
            turn_speed=180.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="orbiter",
            wave_spawned=self.current_wave,
            point_value=200
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    def _spawn_shielder(self, x: float, y: float) -> Entity:
        """Spawn a Shielder enemy - has shield that regenerates, must break or flank."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.05
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=70.0 * wave_scale,
            acceleration=150.0,
            friction=0.12,
            drag=0.93
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.SQUARE,
            color="#8888ff",  # Blue-purple = shielded
            outline_color="#4444cc",
            size=1.0,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=16.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=20.0 + self.current_wave * 8,
            max_hp=20.0 + self.current_wave * 8,
            armor=0.3
        ))
        self.entities.add_component(entity, Shield(
            hp=25.0 + self.current_wave * 5,
            max_hp=25.0 + self.current_wave * 5,
            recharge_rate=5.0,
            recharge_delay=2.0
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SINGLE,
            damage=6.0,
            fire_rate=1.0,
            projectile_speed=280.0,
            projectile_color="#aaaaff"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.CHASER,
            awareness_range=350.0,
            attack_range=200.0,
            attack_cooldown=1.0,
            turn_speed=60.0,
            speed_multiplier=wave_scale * 0.7
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="shielder",
            wave_spawned=self.current_wave,
            point_value=250
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    def _spawn_divider(self, x: float, y: float, size_tier: int = 0) -> Entity:
        """Spawn a Divider enemy - splits into smaller versions when killed."""
        entity = self.entities.create_entity()
        
        # Size decreases with tier (0 = big, 1 = medium, 2 = small)
        size_mult = [1.0, 0.6, 0.35][min(size_tier, 2)]
        hp_mult = [1.0, 0.5, 0.25][min(size_tier, 2)]
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=160.0 + size_tier * 30,  # Smaller = faster
            acceleration=350.0,
            friction=0.08,
            drag=0.96
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.HEXAGON,
            color="#ffff44",  # Yellow
            outline_color="#aaaa00",
            size=0.9 * size_mult,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=14.0 * size_mult,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=(8.0 + self.current_wave * 3) * hp_mult,
            max_hp=(8.0 + self.current_wave * 3) * hp_mult
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.CHASER,
            awareness_range=400.0,
            attack_range=25.0,
            speed_multiplier=1.0 + size_tier * 0.3
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type=f"divider_{size_tier}",
            wave_spawned=self.current_wave,
            point_value=80 - size_tier * 20
        ))
        self.entities.add_tag(entity, "enemy")
        self.entities.add_tag(entity, f"divider_{size_tier}")
        return entity
    
    def _spawn_charger(self, x: float, y: float) -> Entity:
        """Spawn a Charger enemy - charges in straight lines, vulnerable when turning."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.05
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=300.0 * wave_scale,  # Very fast
            acceleration=600.0,
            friction=0.05,
            drag=0.98
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.TRIANGLE,
            color="#ff6644",  # Orange-red
            outline_color="#cc4422",
            size=0.9,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=13.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=12.0 + self.current_wave * 5,
            max_hp=12.0 + self.current_wave * 5
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.CHASER,
            awareness_range=500.0,
            attack_range=30.0,
            speed_multiplier=wave_scale * 1.5,
            turn_speed=45.0  # Slow turning = predictable
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="charger",
            wave_spawned=self.current_wave,
            point_value=160
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    def _spawn_phantom(self, x: float, y: float) -> Entity:
        """Spawn a Phantom enemy - becomes invisible, shoots from hidden position."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.04
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=140.0 * wave_scale,
            acceleration=280.0,
            friction=0.1,
            drag=0.95
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.DIAMOND,
            color="#aa88ff",  # Light purple
            outline_color="#6644aa",
            size=0.7,
            layer=RenderLayer.ENEMY,
            glow=True,
            pulse_speed=1.5
        ))
        self.entities.add_component(entity, Collider(
            radius=11.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=9.0 + self.current_wave * 4,
            max_hp=9.0 + self.current_wave * 4
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SINGLE,
            damage=5.0,
            fire_rate=0.8,
            projectile_speed=320.0,
            projectile_color="#cc88ff"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.ORBIT,
            awareness_range=400.0,
            attack_range=280.0,
            preferred_range=200.0,
            attack_cooldown=2.5,  # Long cooldown (shoots from stealth)
            turn_speed=150.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="phantom",
            wave_spawned=self.current_wave,
            point_value=220
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    # ----- TIER 3: ADVANCED ENEMIES -----
    
    def _spawn_mimic(self, x: float, y: float) -> Entity:
        """Spawn a Mimic enemy - copies player's weapon style."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.04
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=150.0 * wave_scale,
            acceleration=300.0,
            friction=0.1,
            drag=0.95
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.TRIANGLE,
            color="#00ff88",  # Similar to player
            outline_color="#00aa55",
            size=0.85,
            layer=RenderLayer.ENEMY,
            glow=True
        ))
        self.entities.add_component(entity, Collider(
            radius=13.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=11.0 + self.current_wave * 5,
            max_hp=11.0 + self.current_wave * 5
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SINGLE,
            damage=6.0,
            fire_rate=3.0,  # Same as player
            projectile_speed=400.0,
            projectile_color="#88ffaa"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.ORBIT,
            awareness_range=450.0,
            attack_range=350.0,
            preferred_range=200.0,
            attack_cooldown=0.5,
            turn_speed=200.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="mimic",
            wave_spawned=self.current_wave,
            point_value=300
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    def _spawn_hive(self, x: float, y: float) -> Entity:
        """Spawn a Hive enemy - spawns small drones periodically."""
        entity = self.entities.create_entity()
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=0))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=40.0,  # Very slow
            acceleration=80.0,
            friction=0.15,
            drag=0.9
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.HEXAGON,
            color="#ffaa00",  # Orange
            outline_color="#cc8800",
            size=1.3,
            layer=RenderLayer.ENEMY,
            glow=True,
            pulse_speed=0.5
        ))
        self.entities.add_component(entity, Collider(
            radius=20.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=25.0 + self.current_wave * 10,
            max_hp=25.0 + self.current_wave * 10,
            armor=0.2
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.WANDER,
            awareness_range=500.0,
            attack_range=400.0,
            speed_multiplier=0.5
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="hive",
            wave_spawned=self.current_wave,
            point_value=350
        ))
        self.entities.add_tag(entity, "enemy")
        self.entities.add_tag(entity, "spawner")
        return entity
    
    def _spawn_stalker(self, x: float, y: float) -> Entity:
        """Spawn a Stalker enemy - teleports if player gets too close."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.04
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=130.0 * wave_scale,
            acceleration=260.0,
            friction=0.1,
            drag=0.95
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.DIAMOND,
            color="#ff00ff",  # Magenta
            outline_color="#aa00aa",
            size=0.75,
            layer=RenderLayer.ENEMY,
            glow=True,
            pulse_speed=2.0
        ))
        self.entities.add_component(entity, Collider(
            radius=11.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=12.0 + self.current_wave * 5,
            max_hp=12.0 + self.current_wave * 5
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SINGLE,
            damage=5.0,
            fire_rate=1.5,
            projectile_speed=320.0,
            projectile_color="#ff88ff"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.ORBIT,
            awareness_range=500.0,
            attack_range=280.0,
            preferred_range=180.0,
            attack_cooldown=0.7,
            turn_speed=200.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="stalker",
            wave_spawned=self.current_wave,
            point_value=280
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    def _spawn_splicer(self, x: float, y: float) -> Entity:
        """Spawn a Splicer enemy - projectiles split mid-flight."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.04
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=110.0 * wave_scale,
            acceleration=220.0,
            friction=0.1,
            drag=0.95
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.HEXAGON,
            color="#ff4488",  # Pink-red
            outline_color="#cc2266",
            size=0.8,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=12.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=10.0 + self.current_wave * 4,
            max_hp=10.0 + self.current_wave * 4
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SINGLE,
            damage=4.0,
            fire_rate=0.8,
            projectile_speed=220.0,  # Slower projectiles
            projectile_color="#ff88aa"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.ORBIT,
            awareness_range=400.0,
            attack_range=300.0,
            preferred_range=220.0,
            attack_cooldown=1.2,
            turn_speed=120.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="splicer",
            wave_spawned=self.current_wave,
            point_value=260
        ))
        self.entities.add_tag(entity, "enemy")
        return entity
    
    # ----- TIER 4: ELITE ENEMIES -----
    
    def _spawn_sentinel(self, x: float, y: float) -> Entity:
        """Spawn a Sentinel enemy - 3-phase enemy that escalates through combat."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.05
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=100.0 * wave_scale,
            acceleration=200.0,
            friction=0.1,
            drag=0.94
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.SQUARE,
            color="#ff8800",  # Orange = elite
            outline_color="#cc6600",
            size=1.4,
            layer=RenderLayer.ENEMY,
            glow=True,
            pulse_speed=1.0
        ))
        self.entities.add_component(entity, Collider(
            radius=22.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=40.0 + self.current_wave * 15,
            max_hp=40.0 + self.current_wave * 15,
            armor=0.25
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.BURST,
            damage=8.0,
            fire_rate=1.5,
            projectile_speed=300.0,
            projectile_color="#ffaa44",
            burst_count=4,
            burst_delay=0.1
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.BOSS,  # Uses phase-based behavior
            awareness_range=600.0,
            attack_range=400.0,
            preferred_range=200.0,
            attack_cooldown=2.0,
            turn_speed=80.0,
            phase_hp_thresholds=[0.66, 0.33, 0.0]
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="sentinel",
            wave_spawned=self.current_wave,
            point_value=500
        ))
        self.entities.add_tag(entity, "enemy")
        self.entities.add_tag(entity, "elite")
        return entity
    
    def _spawn_sovereign(self, x: float, y: float) -> Entity:
        """Spawn a Sovereign enemy - buffs and commands nearby enemies."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.04
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=80.0 * wave_scale,
            acceleration=160.0,
            friction=0.12,
            drag=0.93
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.HEXAGON,
            color="#ffff00",  # Gold = commander
            outline_color="#cccc00",
            size=1.2,
            layer=RenderLayer.ENEMY,
            glow=True,
            pulse_speed=0.8
        ))
        self.entities.add_component(entity, Collider(
            radius=18.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=30.0 + self.current_wave * 12,
            max_hp=30.0 + self.current_wave * 12,
            armor=0.15
        ))
        self.entities.add_component(entity, Shield(
            hp=20.0 + self.current_wave * 5,
            max_hp=20.0 + self.current_wave * 5,
            recharge_rate=8.0,
            recharge_delay=3.0
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SINGLE,
            damage=6.0,
            fire_rate=1.0,
            projectile_speed=280.0,
            projectile_color="#ffff88"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.FLEE,  # Stays back, commands others
            awareness_range=500.0,
            attack_range=300.0,
            preferred_range=250.0,
            attack_cooldown=1.0,
            turn_speed=120.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="sovereign",
            wave_spawned=self.current_wave,
            point_value=450
        ))
        self.entities.add_tag(entity, "enemy")
        self.entities.add_tag(entity, "elite")
        self.entities.add_tag(entity, "commander")
        return entity
    
    def _spawn_executor(self, x: float, y: float) -> Entity:
        """Spawn an Executor enemy - ultra-fast, stuns player on hit."""
        entity = self.entities.create_entity()
        wave_scale = 1.0 + self.current_wave * 0.05
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=280.0 * wave_scale,  # Very fast
            acceleration=550.0,
            friction=0.06,
            drag=0.97
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.TRIANGLE,
            color="#ff0044",  # Deep red
            outline_color="#aa0022",
            size=0.95,
            layer=RenderLayer.ENEMY,
            glow=True,
            pulse_speed=3.0
        ))
        self.entities.add_component(entity, Collider(
            radius=14.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=18.0 + self.current_wave * 6,
            max_hp=18.0 + self.current_wave * 6
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.CHASER,
            awareness_range=600.0,
            attack_range=30.0,
            speed_multiplier=wave_scale * 1.4,
            turn_speed=150.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="executor",
            wave_spawned=self.current_wave,
            point_value=400
        ))
        self.entities.add_tag(entity, "enemy")
        self.entities.add_tag(entity, "elite")
        return entity
    
    # Legacy compatibility alias
    def _spawn_chaser(self, x: float, y: float) -> Entity:
        """Legacy spawn function - redirects to drone."""
        return self._spawn_drone(x, y)
    
    def _spawn_boss(self) -> None:
        """Spawn a boss enemy based on current wave."""
        x, y = 0, self.arena_height / 2 - 60  # Top center
        
        # Determine which boss to spawn based on wave number
        boss_type = (self.current_wave // 5) % 4  # Cycles through 4 boss types
        
        if boss_type == 0:
            self._spawn_boss_constructor(x, y)
        elif boss_type == 1:
            self._spawn_boss_shadow(x, y)
        elif boss_type == 2:
            self._spawn_boss_architect(x, y)
        else:
            self._spawn_boss_final_trial(x, y)
        
        self.enemies_remaining = 1
    
    def _spawn_boss_constructor(self, x: float, y: float) -> None:
        """
        THE CONSTRUCTOR - Wave 5 Boss
        Theme: Methodical, building. Emphasizes positioning.
        Phase 1: Cannon Barrage, Wall Slam, Repair
        Phase 2: Enraged Barrage, Deploy Drones
        """
        entity = self.entities.create_entity()
        wave_scale = 1.0 + (self.current_wave - 5) * 0.1
        
        self.entities.add_component(entity, Transform(x=x, y=y))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=80.0 * wave_scale,
            acceleration=160.0,
            friction=0.12,
            drag=0.94
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.SQUARE,
            color="#ff4400",  # Orange-red
            outline_color="#aa2200",
            size=2.2,
            layer=RenderLayer.ENEMY,
            glow=True,
            pulse_speed=0.5
        ))
        self.entities.add_component(entity, Collider(
            radius=35.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.PLAYER_PROJECTILE
        ))
        
        boss_hp = 150.0 * wave_scale
        self.entities.add_component(entity, Health(
            hp=boss_hp,
            max_hp=boss_hp,
            armor=0.25
        ))
        self.entities.add_component(entity, Shield(
            hp=boss_hp * 0.3,
            max_hp=boss_hp * 0.3,
            recharge_rate=5.0,
            recharge_delay=4.0
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SHOTGUN,
            damage=12.0,
            fire_rate=0.6,
            projectile_speed=280.0,
            bullet_count=5,
            spread=45.0,
            projectile_color="#ff6644"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.BOSS,
            awareness_range=600.0,
            attack_range=400.0,
            attack_cooldown=1.5,
            turn_speed=50.0,
            phase_hp_thresholds=[0.6, 0.0]
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="boss_constructor",
            wave_spawned=self.current_wave,
            point_value=1000
        ))
        self.entities.add_component(entity, BossTag(
            boss_name="THE CONSTRUCTOR"
        ))
        self.entities.add_tag(entity, "enemy")
        self.entities.add_tag(entity, "boss")
    
    def _spawn_boss_shadow(self, x: float, y: float) -> None:
        """
        THE SHADOW - Wave 10 Boss
        Theme: Evasive, prediction-based. Teaches tracking.
        Phase 1: Teleport Strike, Homing Projectiles, Stealth Phase
        Phase 2: Spiral Attack, Double Teleport, Duplicate
        """
        entity = self.entities.create_entity()
        wave_scale = 1.0 + (self.current_wave - 10) * 0.1
        
        self.entities.add_component(entity, Transform(x=x, y=y))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=180.0 * wave_scale,
            acceleration=400.0,
            friction=0.06,
            drag=0.97
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.DIAMOND,
            color="#8800ff",  # Purple
            outline_color="#5500aa",
            size=1.8,
            layer=RenderLayer.ENEMY,
            glow=True,
            pulse_speed=2.0
        ))
        self.entities.add_component(entity, Collider(
            radius=28.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.PLAYER_PROJECTILE
        ))
        
        boss_hp = 120.0 * wave_scale
        self.entities.add_component(entity, Health(
            hp=boss_hp,
            max_hp=boss_hp,
            armor=0.1
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.BURST,
            damage=8.0,
            fire_rate=1.0,
            projectile_speed=350.0,
            projectile_color="#aa44ff",
            burst_count=3,
            burst_delay=0.1
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.BOSS,
            awareness_range=700.0,
            attack_range=500.0,
            preferred_range=200.0,
            attack_cooldown=1.0,
            turn_speed=200.0,
            phase_hp_thresholds=[0.5, 0.0]
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="boss_shadow",
            wave_spawned=self.current_wave,
            point_value=1500
        ))
        self.entities.add_component(entity, BossTag(
            boss_name="THE SHADOW"
        ))
        self.entities.add_tag(entity, "enemy")
        self.entities.add_tag(entity, "boss")
    
    def _spawn_boss_architect(self, x: float, y: float) -> None:
        """
        THE ARCHITECT - Wave 15 Boss
        Theme: Complex, multi-mechanic. Teaches adaptation.
        3 Phases with different attack patterns
        """
        entity = self.entities.create_entity()
        wave_scale = 1.0 + (self.current_wave - 15) * 0.1
        
        self.entities.add_component(entity, Transform(x=x, y=y))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=100.0 * wave_scale,
            acceleration=200.0,
            friction=0.1,
            drag=0.95
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.HEXAGON,
            color="#ff8800",  # Orange
            outline_color="#cc6600",
            size=2.5,
            layer=RenderLayer.ENEMY,
            glow=True,
            pulse_speed=0.8
        ))
        self.entities.add_component(entity, Collider(
            radius=40.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.PLAYER_PROJECTILE
        ))
        
        boss_hp = 200.0 * wave_scale
        self.entities.add_component(entity, Health(
            hp=boss_hp,
            max_hp=boss_hp,
            armor=0.3
        ))
        self.entities.add_component(entity, Shield(
            hp=boss_hp * 0.4,
            max_hp=boss_hp * 0.4,
            recharge_rate=8.0,
            recharge_delay=3.0
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SHOTGUN,
            damage=15.0,
            fire_rate=0.5,
            projectile_speed=300.0,
            bullet_count=7,
            spread=80.0,
            projectile_color="#ffaa44"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.BOSS,
            awareness_range=700.0,
            attack_range=500.0,
            attack_cooldown=2.0,
            turn_speed=70.0,
            phase_hp_thresholds=[0.65, 0.3, 0.0]
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="boss_architect",
            wave_spawned=self.current_wave,
            point_value=2000
        ))
        self.entities.add_component(entity, BossTag(
            boss_name="THE ARCHITECT"
        ))
        self.entities.add_tag(entity, "enemy")
        self.entities.add_tag(entity, "boss")
    
    def _spawn_boss_final_trial(self, x: float, y: float) -> None:
        """
        THE FINAL TRIAL - Wave 20 Boss
        Theme: Amalgamation. Tests everything learned.
        Combines all previous boss mechanics
        """
        entity = self.entities.create_entity()
        wave_scale = 1.0 + (self.current_wave - 20) * 0.1
        
        self.entities.add_component(entity, Transform(x=x, y=y))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=150.0 * wave_scale,
            acceleration=300.0,
            friction=0.08,
            drag=0.96
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.HEXAGON,
            color="#ffffff",  # White/rainbow
            outline_color="#ffff00",
            size=3.0,
            layer=RenderLayer.ENEMY,
            glow=True,
            pulse_speed=1.5
        ))
        self.entities.add_component(entity, Collider(
            radius=50.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.PLAYER_PROJECTILE
        ))
        
        boss_hp = 300.0 * wave_scale
        self.entities.add_component(entity, Health(
            hp=boss_hp,
            max_hp=boss_hp,
            armor=0.35
        ))
        self.entities.add_component(entity, Shield(
            hp=boss_hp * 0.5,
            max_hp=boss_hp * 0.5,
            recharge_rate=15.0,
            recharge_delay=2.0
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SHOTGUN,
            damage=20.0,
            fire_rate=0.8,
            projectile_speed=350.0,
            bullet_count=9,
            spread=120.0,
            projectile_color="#ffffff"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.BOSS,
            awareness_range=800.0,
            attack_range=600.0,
            attack_cooldown=1.5,
            turn_speed=100.0,
            phase_hp_thresholds=[0.7, 0.4, 0.0]
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="boss_final",
            wave_spawned=self.current_wave,
            point_value=5000
        ))
        self.entities.add_component(entity, BossTag(
            boss_name="THE FINAL TRIAL"
        ))
        self.entities.add_tag(entity, "enemy")
        self.entities.add_tag(entity, "boss")
    
    def start_game(self) -> None:
        """Start the game (begin wave spawning)."""
        self.current_wave = 0
        self.state = WaveState.WAITING
        self.wave_timer = 0.0
        self.score = 0
        self.kills = 0
        self.enemies_remaining = 0
        self.spawn_queue.clear()
    
    def set_arena_size(self, width: float, height: float) -> None:
        """Update arena dimensions."""
        self.arena_width = width
        self.arena_height = height
