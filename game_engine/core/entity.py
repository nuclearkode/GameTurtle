"""Entity representation - just an ID with component references."""

from typing import Dict, Any
from uuid import uuid4


class Entity:
    """An entity is just an ID with a bag of components."""
    
    def __init__(self, entity_id: str = None):
        self.id = entity_id or str(uuid4())
        self.components: Dict[str, Any] = {}
    
    def __repr__(self):
        comp_names = ", ".join(self.components.keys())
        return f"Entity({self.id[:8]}... [{comp_names}])"
