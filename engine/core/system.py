"""
GameSystem and SystemManager - Behavior execution framework.

Design Philosophy:
- Systems contain ALL game logic (behavior lives in systems, not entities)
- Systems operate on component data, not on entity classes
- Systems are called in a deterministic order each frame
- Systems should be stateless where possible (state lives in components)
- Systems communicate via shared component data or events, not direct calls
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type, TYPE_CHECKING
from enum import IntEnum
from dataclasses import dataclass

if TYPE_CHECKING:
    from .entity import EntityManager
    from .events import EventBus


class SystemPriority(IntEnum):
    """
    Standard priority levels for system execution order.
    
    Lower values execute first. Systems at the same priority
    execute in registration order.
    """
    INPUT = 0          # Read input first
    AI = 100           # AI decisions before physics
    PHYSICS = 200      # Movement and forces
    WEAPON = 300       # Weapon firing (after physics positions updated)
    COLLISION = 400    # Collision detection and response
    DAMAGE = 500       # Apply damage from collisions
    HEALTH = 600       # Process health changes, death
    WAVE = 700         # Wave management, spawning
    STATUS_EFFECT = 800  # Status effect ticking
    CLEANUP = 900      # Cleanup operations
    RENDER = 1000      # Render last


class GameSystem(ABC):
    """
    Base class for all game systems.
    
    A system processes entities that have specific component signatures.
    Systems should:
    - Be mostly stateless (cache rarely, derive from components)
    - Not directly call other systems (use events or component flags)
    - Iterate over relevant entities each frame
    - Batch similar operations where possible
    
    Lifecycle:
    - initialize(): Called once when the system is added to the manager
    - update(dt): Called every frame
    - cleanup(): Called when system is removed or game ends
    """
    
    def __init__(self, priority: int = SystemPriority.PHYSICS):
        self.priority = priority
        self.enabled = True
        self._entity_manager: Optional[EntityManager] = None
        self._event_bus: Optional[EventBus] = None
        self._initialized = False
    
    def inject_dependencies(
        self,
        entity_manager: EntityManager,
        event_bus: EventBus
    ) -> None:
        """
        Inject required dependencies.
        Called by SystemManager when the system is registered.
        """
        self._entity_manager = entity_manager
        self._event_bus = event_bus
    
    @property
    def entities(self) -> EntityManager:
        """Access the entity manager."""
        if self._entity_manager is None:
            raise RuntimeError("System not initialized - no entity manager")
        return self._entity_manager
    
    @property
    def events(self) -> EventBus:
        """Access the event bus."""
        if self._event_bus is None:
            raise RuntimeError("System not initialized - no event bus")
        return self._event_bus
    
    def initialize(self) -> None:
        """
        Called once when the system is added to the manager.
        Override to perform one-time setup.
        """
        pass
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Process entities for this frame.
        
        Args:
            dt: Delta time in seconds since last frame
            
        This is called every frame for enabled systems.
        Implement your game logic here by:
        1. Querying entities with required components
        2. Iterating and updating component data
        """
        pass
    
    def cleanup(self) -> None:
        """
        Called when the system is removed or game ends.
        Override to clean up resources.
        """
        pass


class SystemManager:
    """
    Orchestrates system execution.
    
    Responsibilities:
    - Store registered systems
    - Sort systems by priority
    - Call update(dt) in correct order
    - Manage system lifecycle (init, update, cleanup)
    - Allow enabling/disabling systems at runtime
    """
    
    def __init__(
        self,
        entity_manager: EntityManager,
        event_bus: EventBus
    ):
        self._entity_manager = entity_manager
        self._event_bus = event_bus
        self._systems: List[GameSystem] = []
        self._systems_by_type: Dict[Type[GameSystem], GameSystem] = {}
        self._sorted = False
    
    def add_system(self, system: GameSystem) -> GameSystem:
        """
        Register a system.
        
        Args:
            system: The system instance to add
            
        Returns:
            The system (for chaining)
        """
        # Inject dependencies
        system.inject_dependencies(self._entity_manager, self._event_bus)
        
        # Store by type for retrieval
        self._systems_by_type[type(system)] = system
        
        # Add to list and mark for re-sorting
        self._systems.append(system)
        self._sorted = False
        
        # Initialize
        system.initialize()
        system._initialized = True
        
        return system
    
    def remove_system(self, system_type: Type[GameSystem]) -> Optional[GameSystem]:
        """
        Remove a system by type.
        
        Args:
            system_type: The type of system to remove
            
        Returns:
            The removed system, or None if not found
        """
        system = self._systems_by_type.pop(system_type, None)
        if system:
            system.cleanup()
            self._systems.remove(system)
        return system
    
    def get_system(self, system_type: Type[GameSystem]) -> Optional[GameSystem]:
        """Get a system by type."""
        return self._systems_by_type.get(system_type)
    
    def update(self, dt: float) -> None:
        """
        Update all enabled systems in priority order.
        
        Args:
            dt: Delta time in seconds
        """
        # Sort by priority if needed
        if not self._sorted:
            self._systems.sort(key=lambda s: s.priority)
            self._sorted = True
        
        # Update enabled systems
        for system in self._systems:
            if system.enabled:
                system.update(dt)
    
    def cleanup(self) -> None:
        """Clean up all systems."""
        for system in self._systems:
            if system._initialized:
                system.cleanup()
        self._systems.clear()
        self._systems_by_type.clear()
    
    def enable_system(self, system_type: Type[GameSystem]) -> bool:
        """Enable a system by type. Returns True if found."""
        system = self._systems_by_type.get(system_type)
        if system:
            system.enabled = True
            return True
        return False
    
    def disable_system(self, system_type: Type[GameSystem]) -> bool:
        """Disable a system by type. Returns True if found."""
        system = self._systems_by_type.get(system_type)
        if system:
            system.enabled = False
            return True
        return False
    
    @property
    def system_count(self) -> int:
        """Number of registered systems."""
        return len(self._systems)
    
    def get_all_systems(self) -> List[GameSystem]:
        """Get all systems in priority order."""
        if not self._sorted:
            self._systems.sort(key=lambda s: s.priority)
            self._sorted = True
        return list(self._systems)
