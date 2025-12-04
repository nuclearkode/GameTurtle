"""
Wave System

Manages enemy waves, difficulty scaling, and upgrades between waves.
"""

import random
from engine.core.system import GameSystem
from engine.core.component import WaveInfo, Enemy, Player
from typing import Dict, List, Callable


class WaveSystem(GameSystem):
    """
    Manages wave-based gameplay.
    
    Responsibilities:
    - Spawn enemies in waves
    - Track wave progress
    - Scale difficulty
    - Handle wave completion
    - Present upgrade choices between waves
    """
    
    def __init__(self, entity_manager, priority: int = 40):
        super().__init__(entity_manager, priority)
        self.wave_info_entity = None
        self.spawn_functions: Dict[str, Callable] = {}  # enemy_type -> spawn_function
        self.upgrade_callback = None  # Called when offering upgrades
        self.wave_active = False
        self.time_until_next_wave = 0.0
    
    def set_spawn_function(self, enemy_type: str, spawn_func: Callable) -> None:
        """
        Register a spawn function for an enemy type.
        
        spawn_func should take (entity_manager, x, y) and create the enemy.
        """
        self.spawn_functions[enemy_type] = spawn_func
    
    def set_upgrade_callback(self, callback: Callable) -> None:
        """Set callback for when upgrades should be offered."""
        self.upgrade_callback = callback
    
    def start_wave(self, wave_number: int) -> None:
        """Start a specific wave."""
        # Get or create wave info entity
        if not self.wave_info_entity:
            wave_entities = self.entity_manager.query_entities(WaveInfo)
            if wave_entities:
                self.wave_info_entity = wave_entities[0]
            else:
                self.wave_info_entity = self.entity_manager.create_entity()
                self.entity_manager.add_component(
                    self.wave_info_entity.id,
                    WaveInfo(current_wave=0)
                )
        
        wave_info = self.wave_info_entity.get_component(WaveInfo)
        wave_info.current_wave = wave_number
        wave_info.wave_active = True
        wave_info.wave_complete = False
        wave_info.enemies_spawned = 0
        wave_info.enemies_alive = 0
        
        # Spawn enemies for this wave
        self._spawn_wave(wave_number)
        self.wave_active = True
    
    def update(self, dt: float) -> None:
        """Update wave state."""
        if not self.wave_info_entity:
            # Initialize first wave
            self.start_wave(1)
            return
        
        wave_info = self.wave_info_entity.get_component(WaveInfo)
        
        # Count alive enemies
        enemy_count = len(self.entity_manager.query_entities(Enemy))
        wave_info.enemies_alive = enemy_count
        
        # Check if wave is complete
        if wave_info.wave_active and wave_info.enemies_alive == 0:
            self._complete_wave()
            wave_info.wave_active = False
            wave_info.wave_complete = True
            self.wave_active = False
            self.time_until_next_wave = wave_info.time_between_waves
        
        # Handle time between waves
        if not wave_info.wave_active and wave_info.wave_complete:
            self.time_until_next_wave -= dt
            if self.time_until_next_wave <= 0:
                # Start next wave
                self.start_wave(wave_info.current_wave + 1)
    
    def _spawn_wave(self, wave_number: int) -> None:
        """Spawn enemies for the current wave."""
        # Calculate difficulty budget
        budget = self._calculate_wave_budget(wave_number)
        
        # Define enemy costs and types
        enemy_pool = self._get_enemy_pool(wave_number)
        
        # Spawn enemies until budget is exhausted
        spawned = 0
        max_spawns = 50  # Safety limit
        
        while budget > 0 and spawned < max_spawns:
            # Choose random enemy type that fits budget
            available = [e for e in enemy_pool if e['cost'] <= budget]
            if not available:
                break
            
            enemy_def = random.choice(available)
            
            # Spawn enemy at random position
            spawn_x, spawn_y = self._get_spawn_position()
            
            if enemy_def['type'] in self.spawn_functions:
                self.spawn_functions[enemy_def['type']](
                    self.entity_manager, spawn_x, spawn_y
                )
                budget -= enemy_def['cost']
                spawned += 1
        
        wave_info = self.wave_info_entity.get_component(WaveInfo)
        wave_info.enemies_spawned = spawned
        wave_info.enemies_alive = spawned
    
    def _calculate_wave_budget(self, wave_number: int) -> float:
        """Calculate difficulty budget for a wave."""
        # Exponential scaling with diminishing returns
        base_budget = 10.0
        scaling = 1.5
        return base_budget * (wave_number ** 0.7) * scaling
    
    def _get_enemy_pool(self, wave_number: int) -> List[Dict]:
        """Get available enemy types for this wave."""
        pool = [
            {'type': 'chaser', 'cost': 1.0},
        ]
        
        # Unlock new enemy types as waves progress
        if wave_number >= 3:
            pool.append({'type': 'turret', 'cost': 2.0})
        
        if wave_number >= 5:
            pool.append({'type': 'swarm', 'cost': 0.5})
        
        if wave_number >= 10:
            pool.append({'type': 'boss', 'cost': 10.0})
        
        return pool
    
    def _get_spawn_position(self) -> tuple:
        """Get a random spawn position at the edge of the arena."""
        import random
        
        # Spawn at edges of arena
        side = random.choice(['top', 'bottom', 'left', 'right'])
        
        if side == 'top':
            return (random.uniform(-350, 350), 280)
        elif side == 'bottom':
            return (random.uniform(-350, 350), -280)
        elif side == 'left':
            return (-380, random.uniform(-250, 250))
        else:  # right
            return (380, random.uniform(-250, 250))
    
    def _complete_wave(self) -> None:
        """Handle wave completion."""
        wave_info = self.wave_info_entity.get_component(WaveInfo)
        
        # Offer upgrades every few waves
        if wave_info.current_wave % 3 == 0 and self.upgrade_callback:
            self.upgrade_callback()
    
    def get_current_wave(self) -> int:
        """Get current wave number."""
        if self.wave_info_entity:
            wave_info = self.wave_info_entity.get_component(WaveInfo)
            return wave_info.current_wave
        return 0
    
    def is_wave_active(self) -> bool:
        """Check if a wave is currently active."""
        return self.wave_active
