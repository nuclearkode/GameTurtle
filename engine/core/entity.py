"""
Entity and EntityManager - Core ECS identity and lifecycle management.

Design Philosophy:
- Entities are just unique IDs (lightweight)
- Components are stored in the EntityManager, indexed by entity ID
- This allows for data-oriented iteration over components
- Deferred destruction prevents iterator invalidation
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Set, Type, TypeVar, Optional, Iterator, List, Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Entity:
    """
    A lightweight entity identifier.
    
    Entities are immutable IDs that reference a collection of components.
    The actual component data lives in the EntityManager, not here.
    
    Using frozen=True makes entities hashable for use in sets/dicts.
    Using slots=True reduces memory overhead.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Entity):
            return self.id == other.id
        return False


# Type variable for component types
C = TypeVar('C')


class EntityManager:
    """
    Central registry for all entities and their components.
    
    Responsibilities:
    - Create and destroy entities
    - Add/remove components from entities
    - Query entities by component signature
    - Defer destruction to end of frame for safe iteration
    
    Data Layout:
    - _entities: Set of all active entity IDs
    - _components: Dict[entity_id, Dict[component_type, component_instance]]
    - _by_component: Dict[component_type, Set[entity_id]] for fast queries
    - _pending_destroy: Entities marked for destruction this frame
    
    This design allows:
    1. O(1) component access by entity
    2. O(1) entity lookup by component type
    3. Safe iteration (destruction is deferred)
    """
    
    def __init__(self):
        # All active entities
        self._entities: Set[Entity] = set()
        
        # Component storage: entity_id -> {component_type -> component}
        self._components: Dict[str, Dict[Type, Any]] = {}
        
        # Reverse index: component_type -> set of entity_ids
        self._by_component: Dict[Type, Set[str]] = {}
        
        # Deferred destruction queue
        self._pending_destroy: List[Entity] = []
        
        # Tag system for quick entity categorization
        self._tags: Dict[str, Set[Entity]] = {}
        
        # Named entity lookup (e.g., "player")
        self._named: Dict[str, Entity] = {}
    
    def create_entity(self, name: Optional[str] = None) -> Entity:
        """
        Create a new entity and return it.
        
        Args:
            name: Optional unique name for quick lookup (e.g., "player")
        
        Returns:
            The newly created Entity
        """
        entity = Entity()
        self._entities.add(entity)
        self._components[entity.id] = {}
        
        if name:
            self._named[name] = entity
        
        return entity
    
    def destroy_entity(self, entity: Entity, immediate: bool = False) -> None:
        """
        Mark an entity for destruction.
        
        By default, destruction is deferred to flush_destroyed() call,
        which should happen at the end of each frame. This prevents
        iterator invalidation during system updates.
        
        Args:
            entity: The entity to destroy
            immediate: If True, destroy immediately (use with caution!)
        """
        if entity not in self._entities:
            return
            
        if immediate:
            self._do_destroy(entity)
        else:
            if entity not in self._pending_destroy:
                self._pending_destroy.append(entity)
    
    def _do_destroy(self, entity: Entity) -> None:
        """Internal: Actually destroy an entity and clean up all references."""
        if entity not in self._entities:
            return
            
        # Remove from component indices
        if entity.id in self._components:
            for comp_type in self._components[entity.id]:
                if comp_type in self._by_component:
                    self._by_component[comp_type].discard(entity.id)
            del self._components[entity.id]
        
        # Remove from tags
        for tag_set in self._tags.values():
            tag_set.discard(entity)
        
        # Remove from named lookup
        names_to_remove = [n for n, e in self._named.items() if e == entity]
        for name in names_to_remove:
            del self._named[name]
        
        # Finally remove from active set
        self._entities.discard(entity)
    
    def flush_destroyed(self) -> int:
        """
        Destroy all entities pending destruction.
        
        Call this at the end of each frame after all systems have run.
        
        Returns:
            Number of entities destroyed
        """
        count = len(self._pending_destroy)
        for entity in self._pending_destroy:
            self._do_destroy(entity)
        self._pending_destroy.clear()
        return count
    
    def is_alive(self, entity: Entity) -> bool:
        """Check if an entity is still active (not destroyed)."""
        return entity in self._entities and entity not in self._pending_destroy
    
    def add_component(self, entity: Entity, component: C) -> C:
        """
        Add a component to an entity.
        
        Args:
            entity: The entity to add the component to
            component: The component instance
            
        Returns:
            The component (for chaining)
            
        Note: If a component of this type already exists, it's replaced.
        """
        if entity.id not in self._components:
            raise ValueError(f"Entity {entity.id} does not exist")
        
        comp_type = type(component)
        self._components[entity.id][comp_type] = component
        
        # Update reverse index
        if comp_type not in self._by_component:
            self._by_component[comp_type] = set()
        self._by_component[comp_type].add(entity.id)
        
        return component
    
    def remove_component(self, entity: Entity, component_type: Type[C]) -> Optional[C]:
        """
        Remove a component from an entity.
        
        Args:
            entity: The entity
            component_type: The type of component to remove
            
        Returns:
            The removed component, or None if not found
        """
        if entity.id not in self._components:
            return None
            
        component = self._components[entity.id].pop(component_type, None)
        
        if component is not None and component_type in self._by_component:
            self._by_component[component_type].discard(entity.id)
        
        return component
    
    def get_component(self, entity: Optional[Entity], component_type: Type[C]) -> Optional[C]:
        """
        Get a component from an entity.
        
        Args:
            entity: The entity (can be None for safety)
            component_type: The type of component to get
            
        Returns:
            The component instance, or None if not found or entity is None
        """
        if entity is None:
            return None
        if entity.id not in self._components:
            return None
        return self._components[entity.id].get(component_type)
    
    def has_component(self, entity: Optional[Entity], component_type: Type) -> bool:
        """Check if an entity has a specific component type."""
        if entity is None:
            return False
        if entity.id not in self._components:
            return False
        return component_type in self._components[entity.id]
    
    def has_components(self, entity: Optional[Entity], *component_types: Type) -> bool:
        """Check if an entity has ALL specified component types."""
        if entity is None:
            return False
        if entity.id not in self._components:
            return False
        entity_components = self._components[entity.id]
        return all(ct in entity_components for ct in component_types)
    
    def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        """
        Safely get an entity by its ID.
        
        Args:
            entity_id: The entity's ID string
            
        Returns:
            The Entity if found and alive, None otherwise
        """
        if not entity_id:
            return None
        for entity in self._entities:
            if entity.id == entity_id and entity not in self._pending_destroy:
                return entity
        return None
    
    def get_entities_with(self, *component_types: Type) -> Iterator[Entity]:
        """
        Get all entities that have ALL specified component types.
        
        This is the primary query method for systems.
        Uses set intersection on reverse indices for efficiency.
        
        Args:
            *component_types: The component types to filter by
            
        Yields:
            Entities that have all specified components
        """
        if not component_types:
            # Iterate over a copy to prevent RuntimeError if set changes during iteration
            yield from list(self._entities)
            return
        
        # Start with the smallest set for efficiency
        sets = []
        for ct in component_types:
            if ct not in self._by_component:
                return  # No entities have this component
            sets.append(self._by_component[ct])
        
        # Sort by size and intersect
        sets.sort(key=len)
        result = sets[0].copy()
        for s in sets[1:]:
            result &= s
        
        # Convert IDs back to entities
        # Iterate over a copy to prevent RuntimeError if set changes during iteration
        for entity in list(self._entities):
            if entity.id in result:
                yield entity
    
    def get_components(self, entity: Entity) -> Dict[Type, Any]:
        """Get all components for an entity as a dict."""
        return self._components.get(entity.id, {}).copy()
    
    # Tag system for quick categorization
    def add_tag(self, entity: Entity, tag: str) -> None:
        """Add a tag to an entity (e.g., 'enemy', 'projectile')."""
        if tag not in self._tags:
            self._tags[tag] = set()
        self._tags[tag].add(entity)
    
    def remove_tag(self, entity: Entity, tag: str) -> None:
        """Remove a tag from an entity."""
        if tag in self._tags:
            self._tags[tag].discard(entity)
    
    def has_tag(self, entity: Entity, tag: str) -> bool:
        """Check if an entity has a specific tag."""
        return tag in self._tags and entity in self._tags[tag]
    
    def get_entities_with_tag(self, tag: str) -> Iterator[Entity]:
        """Get all entities with a specific tag."""
        if tag in self._tags:
            # Iterate over a copy to prevent RuntimeError if set changes during iteration
            for entity in list(self._tags[tag]):
                if entity in self._entities:
                    yield entity
    
    # Named entity lookup
    def get_named(self, name: str) -> Optional[Entity]:
        """Get an entity by its unique name."""
        return self._named.get(name)
    
    def set_name(self, entity: Entity, name: str) -> None:
        """Set or update an entity's name."""
        # Remove old name if exists
        old_names = [n for n, e in self._named.items() if e == entity]
        for old in old_names:
            del self._named[old]
        self._named[name] = entity
    
    @property
    def entity_count(self) -> int:
        """Number of active entities."""
        return len(self._entities)
    
    def __iter__(self) -> Iterator[Entity]:
        """Iterate over all active entities."""
        # Return iterator over a copy to prevent RuntimeError if set changes during iteration
        return iter(list(self._entities))
    
    def __contains__(self, entity: Entity) -> bool:
        """Check if entity is managed by this manager."""
        return entity in self._entities
