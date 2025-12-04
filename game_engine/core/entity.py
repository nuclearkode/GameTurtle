"""
Entity and EntityManager
Entities are just IDs with component bags.
"""

import uuid
from typing import Dict, Type, Optional, Set, Any
from dataclasses import dataclass


class Entity:
    """Entity is just an ID (UUID string)"""
    
    @staticmethod
    def create() -> str:
        """Create a new entity ID"""
        return str(uuid.uuid4())


@dataclass
class ComponentBag:
    """Bag of components for an entity"""
    components: Dict[Type, Any]


class EntityManager:
    """
    Manages entity lifecycle and component attachment.
    Uses deferred destruction for safety.
    """
    
    def __init__(self):
        self._entities: Dict[str, ComponentBag] = {}
        self._pending_destruction: Set[str] = set()
    
    def create_entity(self) -> str:
        """Create a new entity and return its ID"""
        entity_id = Entity.create()
        self._entities[entity_id] = ComponentBag(components={})
        return entity_id
    
    def destroy_entity(self, entity_id: str) -> None:
        """Mark entity for destruction (deferred)"""
        if entity_id in self._entities:
            self._pending_destruction.add(entity_id)
    
    def add_component(self, entity_id: str, component: Any) -> None:
        """Add a component to an entity"""
        if entity_id not in self._entities:
            raise ValueError(f"Entity {entity_id} does not exist")
        component_type = type(component)
        self._entities[entity_id].components[component_type] = component
    
    def remove_component(self, entity_id: str, component_type: Type) -> None:
        """Remove a component from an entity"""
        if entity_id in self._entities:
            bag = self._entities[entity_id]
            if component_type in bag.components:
                del bag.components[component_type]
    
    def get_component(self, entity_id: str, component_type: Type) -> Optional[Any]:
        """Get a component from an entity"""
        if entity_id not in self._entities:
            return None
        return self._entities[entity_id].components.get(component_type)
    
    def has_component(self, entity_id: str, component_type: Type) -> bool:
        """Check if entity has a component"""
        if entity_id not in self._entities:
            return False
        return component_type in self._entities[entity_id].components
    
    def get_all_entities(self) -> Set[str]:
        """Get all active entity IDs"""
        return set(self._entities.keys())
    
    def flush_destruction(self, registry=None) -> None:
        """Destroy all entities marked for destruction"""
        for entity_id in self._pending_destruction:
            if entity_id in self._entities:
                # Remove from registry if provided
                if registry:
                    registry.remove_entity(entity_id)
                del self._entities[entity_id]
        self._pending_destruction.clear()
    
    def is_alive(self, entity_id: str) -> bool:
        """Check if entity is alive (not pending destruction)"""
        return entity_id in self._entities and entity_id not in self._pending_destruction
