"""
WaveSystem - manages wave spawning, difficulty scaling, enemy placement.
"""

import random
from game_engine.core.system import GameSystem
from game_engine.core.component import (
    Transform, Renderable, Collider, Physics, Health, Weapon, AIBrain, WaveInfo
)
from game_engine.core.component import AIBehaviorType


class WaveSystem(GameSystem):
    """
    Spawns waves of enemies with increasing difficulty.
    """
    
    def __init__(self, entity_manager, component_registry, player_id: str, arena_bounds=None):
        super().__init__(entity_manager, component_registry)
        self.player_id = player_id
        self.arena_bounds = arena_bounds or (-400, -400, 400, 400)
        self.current_wave = 0
        self.enemies_remaining = 0
        self.wave_active = False
        self.time_since_wave_end = 0.0
        self.wave_cooldown = 3.0  # Seconds between waves
    
    def update(self, dt: float) -> None:
        """Update wave system"""
        # Count remaining enemies
        enemy_entities = self.registry.get_entities_with(Transform, AIBrain)
        self.enemies_remaining = len(enemy_entities)
        
        # Check if wave is complete
        if self.wave_active and self.enemies_remaining == 0:
            self.wave_active = False
            self.time_since_wave_end = 0.0
            # Wave complete! Could trigger upgrade screen here
        
        # Spawn next wave if ready
        if not self.wave_active:
            self.time_since_wave_end += dt
            if self.time_since_wave_end >= self.wave_cooldown:
                self._spawn_wave()
    
    def _spawn_wave(self) -> None:
        """Spawn a new wave"""
        self.current_wave += 1
        self.wave_active = True
        
        # Calculate difficulty budget
        base_budget = 5.0
        budget = base_budget + self.current_wave * 2.0
        
        # Enemy costs
        costs = {
            AIBehaviorType.CHASER: 1.0,
            AIBehaviorType.TURRET: 3.0,
            AIBehaviorType.SWARM: 0.5,
            AIBehaviorType.BOSS: 10.0,
        }
        
        # Spawn enemies until budget is used
        min_x, min_y, max_x, max_y = self.arena_bounds
        used_budget = 0.0
        
        while used_budget < budget:
            # Choose enemy type (weighted by cost)
            enemy_types = [
                AIBehaviorType.CHASER,
                AIBehaviorType.CHASER,  # More common
                AIBehaviorType.TURRET,
                AIBehaviorType.SWARM,
            ]
            
            # Add boss every 5 waves
            if self.current_wave % 5 == 0 and used_budget + costs[AIBehaviorType.BOSS] <= budget:
                enemy_type = AIBehaviorType.BOSS
            else:
                enemy_type = random.choice(enemy_types)
            
            cost = costs[enemy_type]
            if used_budget + cost > budget:
                break
            
            # Spawn enemy
            self._spawn_enemy(enemy_type, min_x, min_y, max_x, max_y)
            used_budget += cost
    
    def _spawn_enemy(self, behavior_type: AIBehaviorType, min_x: float, min_y: float,
                    max_x: float, max_y: float) -> None:
        """Spawn a single enemy"""
        # Spawn at edge of arena, away from player
        player_transform = self.entity_manager.get_component(self.player_id, Transform)
        if not player_transform:
            return
        
        # Choose spawn side
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            x = random.uniform(min_x, max_x)
            y = max_y - 50
        elif side == "bottom":
            x = random.uniform(min_x, max_x)
            y = min_y + 50
        elif side == "left":
            x = min_x + 50
            y = random.uniform(min_y, max_y)
        else:  # right
            x = max_x - 50
            y = random.uniform(min_y, max_y)
        
        # Create entity
        enemy_id = self.entity_manager.create_entity()
        
        # Transform
        transform = Transform(x=x, y=y, angle=0.0)
        self.entity_manager.add_component(enemy_id, transform)
        self.registry.register(enemy_id, transform)
        
        # Renderable
        colors = {
            AIBehaviorType.CHASER: "red",
            AIBehaviorType.TURRET: "orange",
            AIBehaviorType.SWARM: "pink",
            AIBehaviorType.BOSS: "purple",
        }
        renderable = Renderable(
            shape="square" if behavior_type == AIBehaviorType.TURRET else "circle",
            color=colors.get(behavior_type, "red"),
            size=1.5 if behavior_type == AIBehaviorType.BOSS else 1.0
        )
        self.entity_manager.add_component(enemy_id, renderable)
        self.registry.register(enemy_id, renderable)
        
        # Collider
        collider = Collider(
            radius=15.0 if behavior_type == AIBehaviorType.BOSS else 10.0,
            mask=0x0002,  # Enemy mask
            tags={"enemy"}
        )
        self.entity_manager.add_component(enemy_id, collider)
        self.registry.register(enemy_id, collider)
        
        # Physics (turrets don't move)
        if behavior_type != AIBehaviorType.TURRET:
            physics = Physics(
                mass=1.0,
                friction=0.95,
                max_speed=100.0 if behavior_type == AIBehaviorType.SWARM else 150.0,
                acceleration=200.0
            )
            self.entity_manager.add_component(enemy_id, physics)
            self.registry.register(enemy_id, physics)
        
        # Health
        max_hp = {
            AIBehaviorType.CHASER: 30.0,
            AIBehaviorType.TURRET: 50.0,
            AIBehaviorType.SWARM: 15.0,
            AIBehaviorType.BOSS: 200.0,
        }
        health = Health(hp=max_hp.get(behavior_type, 30.0), max_hp=max_hp.get(behavior_type, 30.0))
        self.entity_manager.add_component(enemy_id, health)
        self.registry.register(enemy_id, health)
        
        # Weapon
        weapon = Weapon(
            fire_rate=1.0 if behavior_type == AIBehaviorType.TURRET else 0.5,
            damage=10.0,
            projectile_speed=250.0,
            spread=5.0,
            bullet_count=1,
            range=500.0
        )
        self.entity_manager.add_component(enemy_id, weapon)
        self.registry.register(enemy_id, weapon)
        
        # AIBrain
        brain = AIBrain(
            behavior_type=behavior_type,
            state="idle",
            awareness_range=300.0,
            attack_range=250.0,
            cooldowns={}
        )
        self.entity_manager.add_component(enemy_id, brain)
        self.registry.register(enemy_id, brain)
