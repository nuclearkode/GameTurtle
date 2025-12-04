"""
ComponentRegistry - fast lookups of entities by component type.
Data-oriented: stores arrays of entity IDs per component type.
"""

from typing import Dict, Type, Set, List, Any
from collections import defaultdict


class ComponentRegistry:
    """
    Registry for fast component lookups.
    Maintains indices: component_type -> set of entity_ids
    """
    
    def __init__(self):
        # component_type -> set of entity_ids
        self._indices: Dict[Type, Set[str]] = defaultdict(set)
    
    def register(self, entity_id: str, component: Any) -> None:
        """Register an entity-component pair"""
        component_type = type(component)
        self._indices[component_type].add(entity_id)
    
    def unregister(self, entity_id: str, component_type: Type) -> None:
        """Unregister an entity-component pair"""
        if component_type in self._indices:
            self._indices[component_type].discard(entity_id)
    
    def get_all(self, component_type: Type) -> Set[str]:
        """Get all entity IDs with a given component type"""
        return self._indices[component_type].copy()
    
    def get_entities_with(self, *component_types: Type) -> Set[str]:
        """
        Get entities that have ALL of the specified component types.
        Returns intersection of all component type sets.
        """
        if not component_types:
            return set()
        
        # Start with first component type
        result = self._indices[component_types[0]].copy()
        
        # Intersect with remaining types
        for comp_type in component_types[1:]:
            result &= self._indices[comp_type]
        
        return result
    
    def clear(self) -> None:
        """Clear all registrations"""
        self._indices.clear()
    
    def remove_entity(self, entity_id: str) -> None:
        """Remove entity from all indices"""
        for entity_set in self._indices.values():
            entity_set.discard(entity_id)
