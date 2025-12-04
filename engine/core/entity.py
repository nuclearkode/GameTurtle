"""
Entity-Component-System (ECS) core primitives.

Entity: Just an ID with a bag of components.
EntityManager: Creates, destroys, and queries entities.
ComponentRegistry: Indexes entities by component type for fast queries.
"""

from typing import Dict, Set, Type, Any, List, Tuple, Optional
from uuid import uuid4
from collections import defaultdict


class Entity:
    """
    An entity is simply a unique ID with a collection of components.
    No behavior - just a container.
    """
    
    def __init__(self, entity_id: str):
        self.id: str = entity_id
        self.components: Dict[Type, Any] = {}
        self.active: bool = True
    
    def add_component(self, component: Any) -> None:
        """Add a component to this entity."""
        self.components[type(component)] = component
    
    def remove_component(self, component_type: Type) -> None:
        """Remove a component from this entity."""
        if component_type in self.components:
            del self.components[component_type]
    
    def get_component(self, component_type: Type) -> Optional[Any]:
        """Get a component of the specified type."""
        return self.components.get(component_type)
    
    def has_component(self, component_type: Type) -> bool:
        """Check if entity has a component of the specified type."""
        return component_type in self.components
    
    def has_components(self, *component_types: Type) -> bool:
        """Check if entity has all specified component types."""
        return all(ct in self.components for ct in component_types)
    
    def __repr__(self) -> str:
        comp_names = [ct.__name__ for ct in self.components.keys()]
        return f"Entity({self.id[:8]}..., components={comp_names})"


class ComponentRegistry:
    """
    Indexes entities by component type for fast queries.
    
    Maintains: component_type -> Set[entity_id]
    """
    
    def __init__(self):
        # Maps component type to set of entity IDs that have that component
        self.index: Dict[Type, Set[str]] = defaultdict(set)
    
    def register_component(self, entity_id: str, component_type: Type) -> None:
        """Register that an entity has a component of the given type."""
        self.index[component_type].add(entity_id)
    
    def unregister_component(self, entity_id: str, component_type: Type) -> None:
        """Unregister a component from an entity."""
        if component_type in self.index:
            self.index[component_type].discard(entity_id)
    
    def unregister_entity(self, entity_id: str) -> None:
        """Remove an entity from all component indices."""
        for entity_set in self.index.values():
            entity_set.discard(entity_id)
    
    def get_entities_with_component(self, component_type: Type) -> Set[str]:
        """Get all entity IDs that have the specified component type."""
        return self.index.get(component_type, set())
    
    def get_entities_with_components(self, *component_types: Type) -> Set[str]:
        """Get all entity IDs that have ALL of the specified component types."""
        if not component_types:
            return set()
        
        # Start with entities that have the first component
        result = self.index.get(component_types[0], set()).copy()
        
        # Intersect with entities that have each subsequent component
        for component_type in component_types[1:]:
            result &= self.index.get(component_type, set())
        
        return result
    
    def clear(self) -> None:
        """Clear all indices."""
        self.index.clear()


class EntityManager:
    """
    Manages entity lifecycle: creation, destruction, component management, and queries.
    
    Uses deferred destruction to avoid modifying collections during iteration.
    """
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.registry: ComponentRegistry = ComponentRegistry()
        self.destruction_queue: Set[str] = set()
    
    def create_entity(self, entity_id: Optional[str] = None) -> Entity:
        """
        Create a new entity with a unique ID.
        
        Args:
            entity_id: Optional custom ID. If None, generates UUID.
        
        Returns:
            The created entity.
        """
        if entity_id is None:
            entity_id = str(uuid4())
        
        entity = Entity(entity_id)
        self.entities[entity_id] = entity
        return entity
    
    def destroy_entity(self, entity_id: str) -> None:
        """
        Mark an entity for destruction.
        Actual destruction happens in process_destruction_queue().
        """
        self.destruction_queue.add(entity_id)
    
    def destroy_entity_immediate(self, entity_id: str) -> None:
        """
        Immediately destroy an entity.
        WARNING: Use only when not iterating over entities.
        """
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            entity.active = False
            self.registry.unregister_entity(entity_id)
            del self.entities[entity_id]
    
    def process_destruction_queue(self) -> None:
        """
        Process all entities marked for destruction.
        Call this at the end of each frame.
        """
        for entity_id in self.destruction_queue:
            self.destroy_entity_immediate(entity_id)
        self.destruction_queue.clear()
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        return self.entities.get(entity_id)
    
    def add_component(self, entity_id: str, component: Any) -> None:
        """Add a component to an entity."""
        entity = self.entities.get(entity_id)
        if entity:
            entity.add_component(component)
            self.registry.register_component(entity_id, type(component))
    
    def remove_component(self, entity_id: str, component_type: Type) -> None:
        """Remove a component from an entity."""
        entity = self.entities.get(entity_id)
        if entity:
            entity.remove_component(component_type)
            self.registry.unregister_component(entity_id, component_type)
    
    def get_component(self, entity_id: str, component_type: Type) -> Optional[Any]:
        """Get a component from an entity."""
        entity = self.entities.get(entity_id)
        return entity.get_component(component_type) if entity else None
    
    def query_entities(self, *component_types: Type) -> List[Entity]:
        """
        Query all active entities that have ALL of the specified component types.
        
        Returns:
            List of entities matching the query.
        """
        entity_ids = self.registry.get_entities_with_components(*component_types)
        return [
            self.entities[eid] 
            for eid in entity_ids 
            if eid in self.entities and self.entities[eid].active
        ]
    
    def query_entity_ids(self, *component_types: Type) -> List[str]:
        """
        Query all active entity IDs that have ALL of the specified component types.
        
        Returns:
            List of entity IDs matching the query.
        """
        entity_ids = self.registry.get_entities_with_components(*component_types)
        return [
            eid 
            for eid in entity_ids 
            if eid in self.entities and self.entities[eid].active
        ]
    
    def get_all_entities(self) -> List[Entity]:
        """Get all active entities."""
        return [e for e in self.entities.values() if e.active]
    
    def entity_count(self) -> int:
        """Get the number of active entities."""
        return sum(1 for e in self.entities.values() if e.active)
    
    def clear(self) -> None:
        """Remove all entities."""
        self.entities.clear()
        self.registry.clear()
        self.destruction_queue.clear()
