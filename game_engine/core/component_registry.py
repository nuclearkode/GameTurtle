"""ComponentRegistry: fast component lookups and cache-friendly iteration."""

from typing import Dict, List, Set, Type, Optional
from .component import Component


class ComponentRegistry:
    """Indexes entities by component type for fast lookups."""
    
    def __init__(self):
        # Map component type name -> set of entity IDs
        self._component_index: Dict[str, Set[str]] = {}
        # Map entity ID -> component type names
        self._entity_components: Dict[str, Set[str]] = {}
    
    def register_component(self, entity_id: str, component_type: str):
        """Register that an entity has a component."""
        if component_type not in self._component_index:
            self._component_index[component_type] = set()
        
        self._component_index[component_type].add(entity_id)
        
        if entity_id not in self._entity_components:
            self._entity_components[entity_id] = set()
        self._entity_components[entity_id].add(component_type)
    
    def unregister_component(self, entity_id: str, component_type: str):
        """Unregister a component from an entity."""
        if component_type in self._component_index:
            self._component_index[component_type].discard(entity_id)
        
        if entity_id in self._entity_components:
            self._entity_components[entity_id].discard(component_type)
    
    def unregister_entity(self, entity_id: str):
        """Unregister all components for an entity."""
        if entity_id in self._entity_components:
            component_types = self._entity_components[entity_id].copy()
            for component_type in component_types:
                self.unregister_component(entity_id, component_type)
            del self._entity_components[entity_id]
    
    def get_entities_with(self, *component_types: str) -> Set[str]:
        """Get entities that have all specified components (intersection)."""
        if not component_types:
            return set()
        
        # Start with entities that have the first component type
        result = self._component_index.get(component_types[0], set()).copy()
        
        # Intersect with entities that have each subsequent component type
        for component_type in component_types[1:]:
            result &= self._component_index.get(component_type, set())
        
        return result
    
    def get_entities_with_any(self, *component_types: str) -> Set[str]:
        """Get entities that have any of the specified components (union)."""
        result = set()
        for component_type in component_types:
            result |= self._component_index.get(component_type, set())
        return result
    
    def has_component(self, entity_id: str, component_type: str) -> bool:
        """Check if entity has a component registered."""
        return (
            entity_id in self._entity_components and
            component_type in self._entity_components[entity_id]
        )
    
    def get_component_types(self, entity_id: str) -> Set[str]:
        """Get all component types for an entity."""
        return self._entity_components.get(entity_id, set()).copy()
