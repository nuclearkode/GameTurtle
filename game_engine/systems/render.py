"""
RenderSystem - handles all rendering via turtle.
Minimal state, mostly pure drawing operations.
"""

import turtle
from typing import Optional
from game_engine.core.system import GameSystem
from game_engine.core.component import Transform, Renderable


class RenderSystem(GameSystem):
    """
    Renders all entities with Transform and Renderable components.
    Creates/reuses turtle objects for each entity.
    """
    
    def __init__(self, entity_manager, component_registry, screen: turtle.Screen):
        super().__init__(entity_manager, component_registry)
        self.screen = screen
        self._turtle_cache: dict = {}  # entity_id -> turtle object
    
    def update(self, dt: float) -> None:
        """Render all renderable entities"""
        # Clear screen (or use tracer for double buffering)
        entities = self.registry.get_entities_with(Transform, Renderable)
        
        for entity_id in entities:
            transform = self.entity_manager.get_component(entity_id, Transform)
            renderable = self.entity_manager.get_component(entity_id, Renderable)
            
            if not transform or not renderable:
                continue
            
            # Get or create turtle
            t = self._get_turtle(entity_id, renderable)
            
            # Update position and rotation
            t.goto(transform.x, transform.y)
            t.setheading(transform.angle)
    
    def _get_turtle(self, entity_id: str, renderable: Renderable) -> turtle.Turtle:
        """Get or create turtle for entity"""
        if entity_id not in self._turtle_cache:
            t = turtle.Turtle()
            t.hideturtle()
            t.penup()
            t.speed(0)  # Fastest
            self._turtle_cache[entity_id] = t
            renderable.turtle_ref = t
        
        t = self._turtle_cache[entity_id]
        
        # Update turtle properties
        t.shape(renderable.shape)
        t.color(renderable.color)
        t.shapesize(renderable.size)
        t.showturtle()
        
        return t
    
    def cleanup_entity(self, entity_id: str) -> None:
        """Clean up turtle when entity is destroyed"""
        if entity_id in self._turtle_cache:
            t = self._turtle_cache[entity_id]
            t.hideturtle()
            t.clear()
            del self._turtle_cache[entity_id]
