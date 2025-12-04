"""
Wave System - Enemy wave management and difficulty scaling.

Handles spawning waves of enemies with increasing difficulty,
and manages wave-based progression.
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


@dataclass
class EnemySpawnConfig:
    """Configuration for spawning an enemy type."""
    name: str
    cost: float  # Budget cost
    spawn_fn: Callable[["WaveSystem", float, float], "Entity"]
    min_wave: int = 1  # First wave this enemy can appear
    max_per_wave: int = 10  # Maximum of this type per wave
    weight: float = 1.0  # Spawn probability weight


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
    - Budget-based enemy spawning
    - Difficulty scaling per wave
    - Multiple enemy types with costs
    - Boss waves
    - Wave completion detection
    - Upgrade opportunities between waves
    """
    
    def __init__(
        self,
        arena_width: float = 800,
        arena_height: float = 600,
        start_budget: float = 5.0,
        budget_per_wave: float = 3.0,
        max_waves: int = 10
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
        self._register_default_enemies()
        
        # Score tracking
        self.score = 0
        self.kills = 0
    
    def initialize(self) -> None:
        """Set up wave system."""
        # Subscribe to death events to track enemy kills
        self.events.subscribe(DeathEvent, self._on_enemy_death)
    
    def _register_default_enemies(self) -> None:
        """Register default enemy types."""
        self.register_enemy_type(EnemySpawnConfig(
            name="chaser",
            cost=1.0,
            spawn_fn=self._spawn_chaser,
            min_wave=1,
            weight=2.0
        ))
        
        self.register_enemy_type(EnemySpawnConfig(
            name="turret",
            cost=2.0,
            spawn_fn=self._spawn_turret,
            min_wave=2,
            weight=1.0
        ))
        
        self.register_enemy_type(EnemySpawnConfig(
            name="swarm",
            cost=0.5,
            spawn_fn=self._spawn_swarm,
            min_wave=3,
            max_per_wave=15,
            weight=1.5
        ))
        
        self.register_enemy_type(EnemySpawnConfig(
            name="orbiter",
            cost=2.5,
            spawn_fn=self._spawn_orbiter,
            min_wave=4,
            weight=0.8
        ))
    
    def register_enemy_type(self, config: EnemySpawnConfig) -> None:
        """Register an enemy type for spawning."""
        self.enemy_configs[config.name] = config
    
    def _on_enemy_death(self, event: DeathEvent) -> None:
        """Handle enemy death."""
        entity = next((e for e in self.entities if e.id == event.entity_id), None)
        if not entity:
            return
        
        enemy_tag = self.entities.get_component(entity, EnemyTag)
        if enemy_tag:
            self.enemies_remaining -= 1
            self.kills += 1
            self.score += enemy_tag.point_value
    
    def update(self, dt: float) -> None:
        """Update wave state."""
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
            
            # Find spawn position
            x, y = self._get_spawn_position()
            
            # Spawn enemy (spawn_fn is already a bound method, so don't pass self)
            config.spawn_fn(x, y)
        
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
    
    # Enemy spawn functions
    
    def _spawn_chaser(self, x: float, y: float) -> Entity:
        """Spawn a chaser enemy."""
        entity = self.entities.create_entity()
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=150.0,
            acceleration=300.0,
            friction=0.1,
            drag=0.95
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.TRIANGLE,
            color="#ff4444",
            outline_color="#aa0000",
            size=0.8,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=12.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=30.0 + self.current_wave * 5,
            max_hp=30.0 + self.current_wave * 5
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.CHASER,
            awareness_range=500.0,
            attack_range=30.0,
            speed_multiplier=1.0 + self.current_wave * 0.05
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="chaser",
            wave_spawned=self.current_wave,
            point_value=100
        ))
        self.entities.add_tag(entity, "enemy")
        
        return entity
    
    def _spawn_turret(self, x: float, y: float) -> Entity:
        """Spawn a turret enemy."""
        entity = self.entities.create_entity()
        
        self.entities.add_component(entity, Transform(x=x, y=y))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(is_kinematic=True))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.SQUARE,
            color="#4444ff",
            outline_color="#0000aa",
            size=1.0,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=15.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.PLAYER_PROJECTILE,
            is_static=True
        ))
        self.entities.add_component(entity, Health(
            hp=50.0 + self.current_wave * 10,
            max_hp=50.0 + self.current_wave * 10,
            armor=0.2
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SINGLE,
            damage=15.0,
            fire_rate=1.0 + self.current_wave * 0.1,
            projectile_speed=300.0,
            projectile_color="#6666ff"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.TURRET,
            awareness_range=350.0,
            attack_range=300.0,
            attack_cooldown=1.0,
            turn_speed=90.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="turret",
            wave_spawned=self.current_wave,
            point_value=200
        ))
        self.entities.add_tag(entity, "enemy")
        
        return entity
    
    def _spawn_swarm(self, x: float, y: float) -> Entity:
        """Spawn a swarm enemy."""
        entity = self.entities.create_entity()
        
        self.entities.add_component(entity, Transform(x=x, y=y, angle=random.uniform(0, 360)))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=180.0,
            acceleration=400.0,
            friction=0.05,
            drag=0.98
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.CIRCLE,
            color="#44ff44",
            outline_color="#00aa00",
            size=0.5,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=8.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.OBSTACLE | CollisionMask.PLAYER_PROJECTILE
        ))
        self.entities.add_component(entity, Health(
            hp=15.0 + self.current_wave * 2,
            max_hp=15.0 + self.current_wave * 2
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.SWARM,
            awareness_range=400.0,
            attack_range=25.0,
            separation_distance=30.0,
            neighbor_distance=80.0
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="swarm",
            wave_spawned=self.current_wave,
            point_value=50
        ))
        self.entities.add_tag(entity, "enemy")
        
        return entity
    
    def _spawn_orbiter(self, x: float, y: float) -> Entity:
        """Spawn an orbiter enemy."""
        entity = self.entities.create_entity()
        
        self.entities.add_component(entity, Transform(x=x, y=y))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=200.0,
            acceleration=350.0,
            friction=0.08,
            drag=0.96
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.CIRCLE,
            color="#ff44ff",
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
            hp=40.0 + self.current_wave * 8,
            max_hp=40.0 + self.current_wave * 8
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SINGLE,
            damage=10.0,
            fire_rate=2.0,
            projectile_speed=350.0,
            projectile_color="#ff88ff"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.ORBIT,
            awareness_range=400.0,
            attack_range=250.0,
            preferred_range=150.0,
            attack_cooldown=0.5
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="orbiter",
            wave_spawned=self.current_wave,
            point_value=250
        ))
        self.entities.add_tag(entity, "enemy")
        
        return entity
    
    def _spawn_boss(self) -> None:
        """Spawn a boss enemy."""
        x, y = 0, self.arena_height / 2 - 50  # Top center
        
        entity = self.entities.create_entity()
        
        self.entities.add_component(entity, Transform(x=x, y=y))
        self.entities.add_component(entity, Velocity())
        self.entities.add_component(entity, Physics(
            max_speed=100.0,
            acceleration=200.0,
            friction=0.1,
            drag=0.95
        ))
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.SQUARE,
            color="#ff0000",
            outline_color="#880000",
            size=2.5,
            layer=RenderLayer.ENEMY
        ))
        self.entities.add_component(entity, Collider(
            radius=40.0,
            layer=CollisionMask.ENEMY,
            mask=CollisionMask.PLAYER | CollisionMask.PLAYER_PROJECTILE
        ))
        
        boss_hp = 200.0 + self.current_wave * 50
        self.entities.add_component(entity, Health(
            hp=boss_hp,
            max_hp=boss_hp,
            armor=0.3
        ))
        self.entities.add_component(entity, Shield(
            hp=boss_hp * 0.5,
            max_hp=boss_hp * 0.5,
            recharge_rate=10.0,
            recharge_delay=3.0
        ))
        self.entities.add_component(entity, Weapon(
            weapon_type=WeaponType.SHOTGUN,
            damage=20.0,
            fire_rate=0.5,
            projectile_speed=250.0,
            bullet_count=5,
            spread=60.0,
            projectile_color="#ff8800"
        ))
        self.entities.add_component(entity, AIBrain(
            behavior=AIBehavior.BOSS,
            awareness_range=600.0,
            attack_range=400.0,
            attack_cooldown=2.0,
            turn_speed=60.0,
            phase_hp_thresholds=[0.66, 0.33, 0.0]
        ))
        self.entities.add_component(entity, EnemyTag(
            enemy_type="boss",
            wave_spawned=self.current_wave,
            point_value=1000
        ))
        self.entities.add_component(entity, BossTag(
            boss_name=f"Boss Wave {self.current_wave}"
        ))
        self.entities.add_tag(entity, "enemy")
        self.entities.add_tag(entity, "boss")
        
        self.enemies_remaining = 1
    
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
