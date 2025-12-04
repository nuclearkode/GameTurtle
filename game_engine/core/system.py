"""Base GameSystem class that all systems inherit from."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entity_manager import EntityManager
    from .component_registry import ComponentRegistry


class GameSystem(ABC):
    """Base class for all game systems."""
    
    def __init__(
        self,
        entity_manager: 'EntityManager',
        component_registry: 'ComponentRegistry'
    ):
        self.entity_manager = entity_manager
        self.component_registry = component_registry
        self.enabled = True
        self.priority = 0  # Lower priority runs first
    
    @abstractmethod
    def update(self, dt: float):
        """
        Update the system.
        
        Args:
            dt: Delta time in seconds since last update
        """
        pass
    
    def on_entity_added(self, entity_id: str):
        """Called when an entity is added (optional override)."""
        pass
    
    def on_entity_removed(self, entity_id: str):
        """Called when an entity is removed (optional override)."""
        pass
