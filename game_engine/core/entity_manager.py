"""EntityManager: creates, destroys, and manages entities and components."""

from typing import Dict, Set, Optional, Type, List, Any
from .entity import Entity
from .component import Component


class EntityManager:
    """Manages entity lifecycle and component attachment."""
    
    def __init__(self):
        self._entities: Dict[str, Entity] = {}
        self._to_destroy: Set[str] = set()
    
    def create_entity(self, entity_id: Optional[str] = None) -> str:
        """Create a new entity and return its ID."""
        entity = Entity(entity_id)
        self._entities[entity.id] = entity
        return entity.id
    
    def destroy_entity(self, entity_id: str):
        """Mark entity for destruction (deferred to end of frame)."""
        if entity_id in self._entities:
            self._to_destroy.add(entity_id)
    
    def flush_destruction(self):
        """Actually destroy all entities marked for destruction."""
        for entity_id in self._to_destroy:
            if entity_id in self._entities:
                del self._entities[entity_id]
        self._to_destroy.clear()
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self._entities.get(entity_id)
    
    def has_entity(self, entity_id: str) -> bool:
        """Check if entity exists."""
        return entity_id in self._entities
    
    def add_component(self, entity_id: str, component: Component):
        """Add a component to an entity."""
        entity = self._entities.get(entity_id)
        if entity:
            component_type = type(component).__name__
            entity.components[component_type] = component
    
    def remove_component(self, entity_id: str, component_type: str):
        """Remove a component from an entity."""
        entity = self._entities.get(entity_id)
        if entity:
            entity.components.pop(component_type, None)
    
    def get_component(self, entity_id: str, component_type: str) -> Optional[Component]:
        """Get a component from an entity."""
        entity = self._entities.get(entity_id)
        if entity:
            return entity.components.get(component_type)
        return None
    
    def has_component(self, entity_id: str, component_type: str) -> bool:
        """Check if entity has a component."""
        entity = self._entities.get(entity_id)
        if entity:
            return component_type in entity.components
        return False
    
    def get_all_entities(self) -> List[str]:
        """Get all entity IDs."""
        return list(self._entities.keys())
    
    def query_entities(self, *component_types: str) -> List[str]:
        """Query entities that have all specified components."""
        result = []
        for entity_id, entity in self._entities.items():
            if all(ct in entity.components for ct in component_types):
                result.append(entity_id)
        return result
    
    def get_entity_count(self) -> int:
        """Get total number of entities."""
        return len(self._entities)
