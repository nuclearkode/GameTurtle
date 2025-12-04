"""WaveSystem: manages wave spawning and difficulty scaling."""

import random
from typing import List, Tuple
from ..core.system import GameSystem
from ..core.component import WaveInfo, Transform, Renderable, Collider, Physics, Health, Weapon, AIBrain


class WaveSystem(GameSystem):
    """Manages wave progression and enemy spawning."""
    
    def __init__(self, entity_manager, component_registry, arena_size: float = 800):
        super().__init__(entity_manager, component_registry)
        self.priority = 0  # Run first
        self.arena_size = arena_size
        self.wave_info_id: str = None
        self.spawn_timer: float = 0.0
        self.spawn_delay: float = 2.0  # Delay between spawns
        self.wave_active: bool = False
    
    def initialize(self):
        """Initialize wave system with a WaveInfo component."""
        if not self.wave_info_id:
            self.wave_info_id = self.entity_manager.create_entity()
            wave_info = WaveInfo(current_wave=0, enemies_remaining=0, difficulty_budget=0.0)
            self.entity_manager.add_component(self.wave_info_id, wave_info)
            self.component_registry.register_component(self.wave_info_id, "WaveInfo")
    
    def start_next_wave(self):
        """Start the next wave."""
        if not self.wave_info_id:
            self.initialize()
        
        wave_info = self.entity_manager.get_component(self.wave_info_id, "WaveInfo")
        if wave_info:
            wave_info.current_wave += 1
            # Scale difficulty budget: base + wave * multiplier
            wave_info.difficulty_budget = 10.0 + wave_info.current_wave * 5.0
            wave_info.enemies_remaining = 0
            self.wave_active = True
            self.spawn_timer = 0.0
    
    def update(self, dt: float):
        """Update wave spawning."""
        if not self.wave_info_id:
            self.initialize()
        
        wave_info = self.entity_manager.get_component(self.wave_info_id, "WaveInfo")
        if not wave_info:
            return
        
        # Count remaining enemies
        enemy_ids = self.component_registry.get_entities_with("AIBrain", "Health")
        wave_info.enemies_remaining = len(enemy_ids)
        
        # Spawn enemies if wave is active and budget remains
        if self.wave_active and wave_info.difficulty_budget > 0:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_delay:
                self.spawn_timer = 0.0
                self._spawn_enemy(wave_info)
        
        # Check if wave is complete
        if self.wave_active and wave_info.enemies_remaining == 0 and wave_info.difficulty_budget <= 0:
            self.wave_active = False
    
    def _spawn_enemy(self, wave_info: WaveInfo):
        """Spawn an enemy based on difficulty budget."""
        # Enemy types with costs
        enemy_types: List[Tuple[str, float]] = [
            ("chaser", 1.0),
            ("turret", 3.0),
            ("swarm", 0.5),
        ]
        
        # Filter available enemy types
        available = [et for et in enemy_types if et[1] <= wave_info.difficulty_budget]
        if not available:
            wave_info.difficulty_budget = 0
            return
        
        # Choose random enemy type
        enemy_type, cost = random.choice(available)
        wave_info.difficulty_budget -= cost
        
        # Spawn position (random edge of arena)
        side = random.randint(0, 3)
        if side == 0:  # Top
            x = random.uniform(-self.arena_size // 2, self.arena_size // 2)
            y = self.arena_size // 2
        elif side == 1:  # Bottom
            x = random.uniform(-self.arena_size // 2, self.arena_size // 2)
            y = -self.arena_size // 2
        elif side == 2:  # Left
            x = -self.arena_size // 2
            y = random.uniform(-self.arena_size // 2, self.arena_size // 2)
        else:  # Right
            x = self.arena_size // 2
            y = random.uniform(-self.arena_size // 2, self.arena_size // 2)
        
        # Create enemy based on type
        if enemy_type == "chaser":
            self._create_chaser(x, y)
        elif enemy_type == "turret":
            self._create_turret(x, y)
        elif enemy_type == "swarm":
            self._create_swarm(x, y)
    
    def _create_chaser(self, x: float, y: float):
        """Create a chaser enemy."""
        enemy_id = self.entity_manager.create_entity()
        
        transform = Transform(x=x, y=y, angle=0.0)
        self.entity_manager.add_component(enemy_id, transform)
        self.component_registry.register_component(enemy_id, "Transform")
        
        renderable = Renderable(shape="triangle", color="red", size=1.0)
        self.entity_manager.add_component(enemy_id, renderable)
        self.component_registry.register_component(enemy_id, "Renderable")
        
        collider = Collider(radius=15.0, mask=0x0002, tags={"enemy"})
        self.entity_manager.add_component(enemy_id, collider)
        self.component_registry.register_component(enemy_id, "Collider")
        
        physics = Physics(mass=1.0, friction=0.95, max_speed=150.0, acceleration=80.0)
        self.entity_manager.add_component(enemy_id, physics)
        self.component_registry.register_component(enemy_id, "Physics")
        
        health = Health(hp=30.0, max_hp=30.0)
        self.entity_manager.add_component(enemy_id, health)
        self.component_registry.register_component(enemy_id, "Health")
        
        ai_brain = AIBrain(
            behavior_type="chaser",
            awareness_range=400.0,
            attack_range=50.0
        )
        self.entity_manager.add_component(enemy_id, ai_brain)
        self.component_registry.register_component(enemy_id, "AIBrain")
    
    def _create_turret(self, x: float, y: float):
        """Create a turret enemy."""
        enemy_id = self.entity_manager.create_entity()
        
        transform = Transform(x=x, y=y, angle=0.0)
        self.entity_manager.add_component(enemy_id, transform)
        self.component_registry.register_component(enemy_id, "Transform")
        
        renderable = Renderable(shape="square", color="orange", size=1.2)
        self.entity_manager.add_component(enemy_id, renderable)
        self.component_registry.register_component(enemy_id, "Renderable")
        
        collider = Collider(radius=20.0, mask=0x0002, tags={"enemy"})
        self.entity_manager.add_component(enemy_id, collider)
        self.component_registry.register_component(enemy_id, "Collider")
        
        physics = Physics(mass=10.0, friction=1.0, max_speed=0.0, acceleration=0.0)  # Stationary
        self.entity_manager.add_component(enemy_id, physics)
        self.component_registry.register_component(enemy_id, "Physics")
        
        health = Health(hp=60.0, max_hp=60.0)
        self.entity_manager.add_component(enemy_id, health)
        self.component_registry.register_component(enemy_id, "Health")
        
        weapon = Weapon(
            fire_rate=1.5,
            damage=15.0,
            projectile_speed=250.0,
            weapon_type="single"
        )
        self.entity_manager.add_component(enemy_id, weapon)
        self.component_registry.register_component(enemy_id, "Weapon")
        
        ai_brain = AIBrain(
            behavior_type="turret",
            awareness_range=500.0,
            attack_range=400.0
        )
        self.entity_manager.add_component(enemy_id, ai_brain)
        self.component_registry.register_component(enemy_id, "AIBrain")
    
    def _create_swarm(self, x: float, y: float):
        """Create a swarm enemy."""
        enemy_id = self.entity_manager.create_entity()
        
        transform = Transform(x=x, y=y, angle=0.0)
        self.entity_manager.add_component(enemy_id, transform)
        self.component_registry.register_component(enemy_id, "Transform")
        
        renderable = Renderable(shape="circle", color="pink", size=0.7)
        self.entity_manager.add_component(enemy_id, renderable)
        self.component_registry.register_component(enemy_id, "Renderable")
        
        collider = Collider(radius=10.0, mask=0x0002, tags={"enemy"})
        self.entity_manager.add_component(enemy_id, collider)
        self.component_registry.register_component(enemy_id, "Collider")
        
        physics = Physics(mass=0.5, friction=0.97, max_speed=120.0, acceleration=100.0)
        self.entity_manager.add_component(enemy_id, physics)
        self.component_registry.register_component(enemy_id, "Physics")
        
        health = Health(hp=15.0, max_hp=15.0)
        self.entity_manager.add_component(enemy_id, health)
        self.component_registry.register_component(enemy_id, "Health")
        
        ai_brain = AIBrain(
            behavior_type="swarm",
            awareness_range=300.0,
            attack_range=30.0
        )
        self.entity_manager.add_component(enemy_id, ai_brain)
        self.component_registry.register_component(enemy_id, "AIBrain")
