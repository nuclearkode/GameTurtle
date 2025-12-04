"""
GameSystem base class and SystemManager.
Systems contain behavior, operate on components.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
from dataclasses import dataclass


class GameSystem(ABC):
    """
    Base class for all game systems.
    Systems contain behavior/logic, operate on components.
    """
    
    def __init__(self, entity_manager, component_registry):
        self.entity_manager = entity_manager
        self.registry = component_registry
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Update system logic.
        dt: delta time in seconds
        """
        pass
    
    def on_entity_added(self, entity_id: str) -> None:
        """Called when an entity with relevant components is added"""
        pass
    
    def on_entity_removed(self, entity_id: str) -> None:
        """Called when an entity with relevant components is removed"""
        pass


@dataclass
class SystemEntry:
    """System with priority for ordering"""
    system: GameSystem
    priority: int


class SystemManager:
    """
    Manages systems and calls them in priority order.
    Lower priority = runs first (e.g., input=0, physics=10, render=100)
    """
    
    def __init__(self):
        self._systems: List[SystemEntry] = []
    
    def register_system(self, system: GameSystem, priority: int = 50) -> None:
        """Register a system with a priority"""
        self._systems.append(SystemEntry(system=system, priority=priority))
        # Sort by priority (lower = earlier)
        self._systems.sort(key=lambda e: e.priority)
    
    def update_all(self, dt: float) -> None:
        """Update all systems in priority order"""
        for entry in self._systems:
            entry.system.update(dt)
    
    def get_system(self, system_type: type) -> GameSystem:
        """Get a system by type"""
        for entry in self._systems:
            if isinstance(entry.system, system_type):
                return entry.system
        raise ValueError(f"System {system_type} not found")
