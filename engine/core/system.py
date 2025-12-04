"""
System base class and system manager.

Systems contain behavior logic that operates on entity components.
Each system queries for entities with specific components and updates them.
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class GameSystem(ABC):
    """
    Base class for all game systems.
    
    Systems should:
    - Query entities through EntityManager
    - Read and modify component data
    - Never store entity state (only transient computation)
    - Be order-independent where possible
    """
    
    def __init__(self, entity_manager, priority: int = 0):
        """
        Initialize the system.
        
        Args:
            entity_manager: Reference to the EntityManager
            priority: Execution order (lower = earlier). Default 0.
        """
        self.entity_manager = entity_manager
        self.priority = priority
        self.enabled = True
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Update system logic.
        
        Args:
            dt: Delta time in seconds since last update.
        """
        pass
    
    def enable(self) -> None:
        """Enable this system."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable this system (won't update)."""
        self.enabled = False
    
    def on_entity_created(self, entity_id: str) -> None:
        """
        Optional callback when an entity is created.
        Override if the system needs to react to entity creation.
        """
        pass
    
    def on_entity_destroyed(self, entity_id: str) -> None:
        """
        Optional callback when an entity is destroyed.
        Override if the system needs cleanup on entity destruction.
        """
        pass


class SystemManager:
    """
    Manages all game systems and their execution order.
    
    Systems are updated in priority order (lowest first).
    """
    
    def __init__(self):
        self.systems: List[GameSystem] = []
        self._sorted = False
    
    def add_system(self, system: GameSystem) -> None:
        """
        Add a system to the manager.
        
        Args:
            system: The system to add.
        """
        self.systems.append(system)
        self._sorted = False
    
    def remove_system(self, system: GameSystem) -> None:
        """Remove a system from the manager."""
        if system in self.systems:
            self.systems.remove(system)
    
    def get_system(self, system_type: type) -> Optional[GameSystem]:
        """Get a system by type."""
        for system in self.systems:
            if isinstance(system, system_type):
                return system
        return None
    
    def update_all(self, dt: float) -> None:
        """
        Update all enabled systems in priority order.
        
        Args:
            dt: Delta time in seconds.
        """
        # Sort systems by priority if needed
        if not self._sorted:
            self.systems.sort(key=lambda s: s.priority)
            self._sorted = True
        
        # Update each enabled system
        for system in self.systems:
            if system.enabled:
                system.update(dt)
    
    def enable_all(self) -> None:
        """Enable all systems."""
        for system in self.systems:
            system.enable()
    
    def disable_all(self) -> None:
        """Disable all systems."""
        for system in self.systems:
            system.disable()
    
    def clear(self) -> None:
        """Remove all systems."""
        self.systems.clear()
        self._sorted = False
