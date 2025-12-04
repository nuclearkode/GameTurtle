"""
Component Registry - Additional indexing and component type utilities.

Design Philosophy:
- Components are pure data (defined using @dataclass)
- The registry provides type information and validation
- Enables reflection-like capabilities for editor/debug tools
"""

from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from typing import Dict, Type, Any, List, Set, Optional, Callable
import copy


class ComponentMeta:
    """
    Metadata about a component type.
    
    Stores information for debugging, serialization, and editor tools.
    """
    def __init__(
        self,
        component_type: Type,
        name: Optional[str] = None,
        description: str = "",
        pooled: bool = False,
        max_pool_size: int = 100
    ):
        self.component_type = component_type
        self.name = name or component_type.__name__
        self.description = description
        self.pooled = pooled
        self.max_pool_size = max_pool_size
        
        # Extract field info if it's a dataclass
        self.fields: List[str] = []
        self.field_types: Dict[str, Type] = {}
        self.field_defaults: Dict[str, Any] = {}
        
        if is_dataclass(component_type):
            for f in fields(component_type):
                self.fields.append(f.name)
                self.field_types[f.name] = f.type
                if f.default is not f.default_factory:
                    self.field_defaults[f.name] = f.default


class ComponentRegistry:
    """
    Central registry for component types and pooling.
    
    Responsibilities:
    - Register component types with metadata
    - Provide component pooling for frequently created/destroyed components
    - Enable component introspection
    
    Component Pooling:
    For components that are frequently created and destroyed (like projectiles),
    pooling reduces allocation overhead. When an entity is destroyed, its pooled
    components are returned to the pool for reuse.
    """
    
    def __init__(self):
        self._registered: Dict[Type, ComponentMeta] = {}
        self._pools: Dict[Type, List[Any]] = {}
        self._pool_reset_fns: Dict[Type, Callable[[Any], None]] = {}
    
    def register(
        self,
        component_type: Type,
        name: Optional[str] = None,
        description: str = "",
        pooled: bool = False,
        max_pool_size: int = 100,
        reset_fn: Optional[Callable[[Any], None]] = None
    ) -> ComponentMeta:
        """
        Register a component type.
        
        Args:
            component_type: The component class (should be a dataclass)
            name: Display name for debugging/editors
            description: Human-readable description
            pooled: Whether to pool instances of this component
            max_pool_size: Maximum pool size if pooled
            reset_fn: Function to reset component to default state for reuse
            
        Returns:
            ComponentMeta with type information
        """
        meta = ComponentMeta(
            component_type=component_type,
            name=name,
            description=description,
            pooled=pooled,
            max_pool_size=max_pool_size
        )
        self._registered[component_type] = meta
        
        if pooled:
            self._pools[component_type] = []
            if reset_fn:
                self._pool_reset_fns[component_type] = reset_fn
        
        return meta
    
    def get_meta(self, component_type: Type) -> Optional[ComponentMeta]:
        """Get metadata for a registered component type."""
        return self._registered.get(component_type)
    
    def is_registered(self, component_type: Type) -> bool:
        """Check if a component type is registered."""
        return component_type in self._registered
    
    def acquire(self, component_type: Type, **kwargs) -> Any:
        """
        Get a component instance, from pool if available.
        
        Args:
            component_type: The component class
            **kwargs: Arguments to initialize the component
            
        Returns:
            A component instance (new or recycled from pool)
        """
        meta = self._registered.get(component_type)
        
        # If pooled and pool has instances, reuse one
        if meta and meta.pooled and self._pools.get(component_type):
            instance = self._pools[component_type].pop()
            # Reset and update with new values
            if component_type in self._pool_reset_fns:
                self._pool_reset_fns[component_type](instance)
            for key, value in kwargs.items():
                setattr(instance, key, value)
            return instance
        
        # Create new instance
        return component_type(**kwargs)
    
    def release(self, component: Any) -> bool:
        """
        Return a component to the pool for reuse.
        
        Args:
            component: The component instance to return
            
        Returns:
            True if component was pooled, False otherwise
        """
        component_type = type(component)
        meta = self._registered.get(component_type)
        
        if not meta or not meta.pooled:
            return False
        
        pool = self._pools.get(component_type, [])
        if len(pool) < meta.max_pool_size:
            pool.append(component)
            return True
        
        return False
    
    def get_all_registered(self) -> List[ComponentMeta]:
        """Get metadata for all registered component types."""
        return list(self._registered.values())
    
    def get_pool_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics about component pools."""
        stats = {}
        for comp_type, pool in self._pools.items():
            meta = self._registered.get(comp_type)
            if meta:
                stats[meta.name] = {
                    "available": len(pool),
                    "max_size": meta.max_pool_size
                }
        return stats
    
    def clear_pools(self) -> None:
        """Clear all component pools."""
        for pool in self._pools.values():
            pool.clear()


# Global registry instance (can be replaced with dependency injection if needed)
_global_registry = ComponentRegistry()


def get_component_registry() -> ComponentRegistry:
    """Get the global component registry."""
    return _global_registry


def register_component(
    name: Optional[str] = None,
    description: str = "",
    pooled: bool = False,
    max_pool_size: int = 100,
    reset_fn: Optional[Callable[[Any], None]] = None
):
    """
    Decorator to register a component class.
    
    Usage:
        @register_component(pooled=True)
        @dataclass
        class Projectile:
            damage: float
            lifetime: float
    """
    def decorator(cls):
        _global_registry.register(
            cls,
            name=name,
            description=description,
            pooled=pooled,
            max_pool_size=max_pool_size,
            reset_fn=reset_fn
        )
        return cls
    return decorator
